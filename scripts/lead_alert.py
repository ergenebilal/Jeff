"""Tells Bilal on Telegram, within minutes, when a website visitor looks like a real opportunity.

Run from cron every 2 minutes. It reads new visitor messages from the site chat database
(read-only; the chat app's own columns are never touched), ignores test messages, and sends one
alert per conversation when the visitor asks about price/appointment/offer, plus one more when
they leave a phone number or e-mail. The first run only records where the chat stands, so old
conversations never flood Telegram.

    python scripts/lead_alert.py --chat-db ... --state ... --env-file ... [--dry-run]
"""
import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:  # imported as a package (tests) or run from the scripts folder (server)
    from scripts import morning_report as mr
    from scripts import system_watchdog as wd
except ImportError:  # pragma: no cover
    import morning_report as mr
    import system_watchdog as wd

MAX_ALERTS_PER_RUN = 5


def contacts_in(text):
    phones = [' '.join(m.split()) for m in mr.PHONE_RE.findall(text)]
    return phones + mr.EMAIL_RE.findall(text)


def format_alert(kind, ts_local, question, sid, contacts):
    quote = ' '.join(question.split())[:160]
    if kind == 'contact':
        head = 'Ziyaretçi iletişim bilgisi bıraktı'
    else:
        head = 'Sitede sıcak bir fırsat var'
    lines = [head, f'Saat: {ts_local:%H:%M}', f'Yazdığı: "{quote}"']
    if contacts:
        lines.append('Bıraktığı bilgi: ' + ', '.join(contacts))
    lines.append(f'Konuşma: #{sid[-6:]}')
    lines.append('Fırsat sıcakken dönüş yapmak en iyisi.')
    return '\n'.join(lines)


def load_state(path):
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(path, state):
    tmp = Path(str(path) + '.tmp')
    tmp.write_text(json.dumps(state, ensure_ascii=False), encoding='utf-8')
    os.replace(tmp, path)


def run(chat_db, state_path, send, tz):
    try:
        db = sqlite3.connect(f'file:{chat_db}?mode=ro', uri=True, timeout=10)
    except sqlite3.Error:
        return 'db-unavailable'
    try:
        state = load_state(state_path)
        if 'last_id' not in state:   # first run: remember where we are, alert about nothing old
            top = db.execute('SELECT COALESCE(MAX(id),0) FROM messages').fetchone()[0]
            save_state(state_path, {'last_id': top, 'sessions': {}})
            return f'initialized at {top}'
        rows = db.execute("SELECT id, session_id, text, timestamp FROM messages "
                          "WHERE id>? AND sender='visitor' ORDER BY id", (state['last_id'],)).fetchall()
        top = db.execute('SELECT COALESCE(MAX(id),0) FROM messages').fetchone()[0]
    except sqlite3.Error:
        return 'db-unavailable'
    finally:
        db.close()

    sessions, sent, held = state.get('sessions', {}), 0, 0
    last_id = state['last_id']
    for mid, sid, text, stamp in rows:
        question = mr.visitor_question(text or '')
        kind = None
        if mr.classify(question) != 'test':
            found = contacts_in(question)
            seen = sessions.get(sid, {})
            if found and not seen.get('contact'):
                kind = 'contact'
            elif mr.classify(question) == 'warm' and not seen.get('warm'):
                kind = 'warm'
        if kind:
            if sent >= MAX_ALERTS_PER_RUN:   # a burst: pick the rest up on the next run
                held += 1
                break
            ts = mr._parse_ts(stamp) or datetime.now(timezone.utc)
            if not send(format_alert(kind, ts.astimezone(tz), question, sid, found if kind == 'contact' else [])):
                break   # keep last_id before this message so it is retried
            seen = sessions.setdefault(sid, {})
            seen[kind] = True
            if kind == 'contact':
                seen['warm'] = True   # leaving contact details already says everything the first alert would
            sent += 1
        last_id = mid
    # trim bookkeeping so the file cannot grow forever
    if len(sessions) > 500:
        sessions = dict(list(sessions.items())[-300:])
    save_state(state_path, {'last_id': last_id, 'sessions': sessions})
    return f'{sent} bildirim, {len(rows)} yeni mesaj'


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--chat-db', default='/home/hermes/cybergene-chat/data/support_chat.db')
    ap.add_argument('--state', default='/home/hermes/logs/lead_alert_state.json')
    ap.add_argument('--env-file')
    ap.add_argument('--tz', default='Europe/Istanbul')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args(argv)
    tz = mr._zone(args.tz)
    if args.dry_run:
        def send(text):
            enc = sys.stdout.encoding or 'utf-8'
            print(('--- MESAJ ---\n' + text).encode(enc, 'replace').decode(enc, 'replace'))
            return True
    else:
        env = dict(os.environ)
        if args.env_file:
            env.update(wd.load_env_file(args.env_file))
        token, chat = env.get('ALERT_BOT_TOKEN'), env.get('ALERT_CHAT_ID')
        if not token or not chat:
            print('[firsat] ALERT_BOT_TOKEN / ALERT_CHAT_ID yok', file=sys.stderr)
            return 2
        send = wd.telegram_sender(token, chat)
    print('[firsat]', run(args.chat_db, args.state, send, tz))
    return 0


if __name__ == '__main__':
    sys.exit(main())
