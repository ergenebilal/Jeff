"""Jeff's morning, evening and weekly reports for Bilal: plain Turkish, built only from real data.

Sections: last 24h on the website (real conversations vs tests, warm opportunities), work waiting
for his approval, system health (from the watchdog), and one suggestion derived from those facts.
A source that cannot be read is reported as "veri alinamadi"; nothing is guessed or made up.

    python scripts/morning_report.py --chat-db ... --bridge-db ... --watchdog-state ... [--dry-run|--send]

--kind morning|evening|weekly picks the window and wording. --send needs ALERT_BOT_TOKEN / ALERT_CHAT_ID (env or --env-file), sends at most once per day and
not before --at (local time in --tz), so cron may call it every few minutes without duplicates.
"""
import argparse
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:  # imported as a package (tests) or run from the scripts folder (server)
    from scripts import system_watchdog as wd
    from scripts.approval_inventory import collect as approval_inventory
except ImportError:  # pragma: no cover
    import system_watchdog as wd
    from approval_inventory import collect as approval_inventory

QUESTION_MARKER = 'İşletme sahibinin sorusu:'
TEST_RE = re.compile(r'\b(test\w*|debug|verify|deneme\w*|doğrulama|migration|check)\b', re.I)
INTENT_RE = re.compile(r'\b(fiyat\w*|ücret\w*|randevu\w*|teklif\w*|demo\w*|görüşme\w*|görüşelim|arayın|'
                       r'whatsapp|price\w*|cost\w*|quote|appointment\w*|booking|call me)\b', re.I)
PHONE_RE = re.compile(r'(?<!\d)(\+?\d[\d\s().-]{8,}\d)(?!\d)')
EMAIL_RE = re.compile(r'[^\s@]+@[^\s@]+\.[^\s@]+')
WATCHDOG_STALE_SECONDS = 20 * 60
UNAVAILABLE = 'veri alinamadi'


def visitor_question(text):
    """Site messages carry a long system preamble; the real question follows the marker."""
    idx = text.rfind(QUESTION_MARKER)
    return (text[idx + len(QUESTION_MARKER):] if idx >= 0 else text).strip()


def classify(question):
    if TEST_RE.search(question):
        return 'test'
    if INTENT_RE.search(question) or PHONE_RE.search(question) or EMAIL_RE.search(question):
        return 'warm'
    return 'normal'


def _parse_ts(value):
    try:
        ts = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def _zone(name):
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        if name == 'Europe/Istanbul':  # fixed UTC+3 since 2016; keeps machines without tzdata working
            return timezone(timedelta(hours=3))
        raise


def _ro(path):
    return sqlite3.connect(f'file:{path}?mode=ro', uri=True, timeout=10)


def _traffic(chat_db, now, hours):
    """Anonymous website counters (one row per UTC day, event and page). None when the table does not exist yet."""
    try:
        db = _ro(chat_db)
        try:
            since = (now - timedelta(hours=hours)).strftime('%Y-%m-%d')
            rows = db.execute("SELECT name, SUM(n) FROM events WHERE day >= ? GROUP BY name", (since,)).fetchall()
        finally:
            db.close()
    except sqlite3.Error:
        return None
    return {name: int(n or 0) for name, n in rows}


def collect_site(chat_db, now, hours=24):
    """Site chat in the last `hours`. None when the database cannot be read."""
    try:
        db = _ro(chat_db)
        try:
            rows = db.execute("SELECT session_id, text, timestamp FROM messages "
                              "WHERE sender='visitor' ORDER BY id").fetchall()
        finally:
            db.close()
    except sqlite3.Error:
        return None
    since = now - timedelta(hours=hours)
    sessions = {}
    for sid, text, stamp in rows:
        ts = _parse_ts(stamp)
        if ts is None or ts < since:
            continue
        sessions.setdefault(sid, []).append((ts, visitor_question(text or '')))
    real = warm = test = 0
    warm_items = []
    for sid, msgs in sessions.items():
        kinds = [classify(q) for _, q in msgs]
        if str(sid).startswith('test_') or all(k == 'test' for k in kinds):   # our own probes and load tests never count as visitors
            test += 1
            continue
        real += 1
        for (ts, q), kind in zip(msgs, kinds):
            if kind == 'warm':
                warm += 1
                warm_items.append((ts, sid[-6:], q))
                break
    warm_items.sort(reverse=True)
    return {'real': real, 'warm': warm, 'test': test, 'warm_items': warm_items[:3], 'traffic': _traffic(chat_db, now, hours)}


def collect_approvals(bridge_db, now=None, stale_hours=48, panel_db=None):
    return approval_inventory(bridge_db, now, stale_hours, panel_db)


def collect_health(state_path, now_ts):
    try:
        state = json.loads(Path(state_path).read_text(encoding='utf-8'))
        age = now_ts - Path(state_path).stat().st_mtime
    except (OSError, ValueError):
        return None
    labels = {c.key: c.label for c in wd.default_checks()}
    bad = [(labels.get(k, k), v.get('detail', '')) for k, v in state.items() if not v.get('ok', True)]
    return {'total': len(state), 'bad': bad, 'stale': age > WATCHDOG_STALE_SECONDS,
            'age_min': int(age // 60)}


def collect_backup(backup_dir, now_ts):
    files = sorted(Path(backup_dir).glob('jeff-backup-*.tar.gz'), key=lambda p: p.stat().st_mtime) \
        if Path(backup_dir).is_dir() else []
    return None if not files else int((now_ts - files[-1].stat().st_mtime) // 3600)


def suggest(site, approvals, health):
    if approvals and approvals.get('unavailable') and not approvals['waiting']:
        return 'Bazı onay kaynakları okunamadı; bekleyen iş olmadığını henüz teyit edemiyorum.'
    if site and site['warm']:
        return f"{site['warm']} sıcak konuşma var; önce onlara dönüş yapmak en değerli iş görünüyor."
    if approvals and approvals.get('old'):
        return f"{approvals['old']} iş 2 günden uzun süredir onayını bekliyor; önce onlara karar vermek iyi olur."
    if approvals and approvals['waiting']:
        return f"Onayını bekleyen {approvals['waiting']} iş var; onları karara bağlamak akışı açar."
    if health and (health['bad'] or health['stale']):
        return 'Önce sistem tarafındaki uyarıya bakmak iyi olur; gerisi sakin.'
    if site is None and approvals is None and health is None:
        return 'Veriler okunamadı; önce raporun kaynaklarını kontrol etmek gerekiyor.'
    return 'Acil görünen bir şey yok. Yeni konuşma gelmesi için tanıtım ve içerik tarafına odaklanabilirsin.'


KINDS = {
    'morning': ('Günaydın Bilal. {d} sabah özeti', 'SİTEDE SON 24 SAAT', 'BUGÜN İÇİN ÖNERİM'),
    'evening': ('İyi akşamlar Bilal. {d} gün sonu özeti', 'SİTEDE BUGÜN', 'YARIN İÇİN ÖNERİM'),
    'weekly': ('Merhaba Bilal. {d} haftalık özet', 'SİTEDE SON 7 GÜN', 'ÖNÜMÜZDEKİ HAFTA İÇİN ÖNERİM'),
}
WINDOW_HOURS = {'morning': lambda ln: 24, 'evening': lambda ln: max(ln.hour + 1, 1), 'weekly': lambda ln: 168}


def build_report(site, approvals, health, backup_h, local_now, kind='morning'):
    title, site_head, advice_head = KINDS[kind]
    lines = [title.format(d=local_now.strftime('%d.%m.%Y')), '']
    lines.append(site_head)
    if site is None:
        lines.append(f'- {UNAVAILABLE} (sohbet kaydına ulaşılamadı)')
    else:
        lines.append(f"- Test görünmeyen ziyaretçi konuşması: {site['real']}")
        if site['test']:
            lines.append(f"- Deneme/test konuşması: {site['test']} (sayılmadı)")
        if site['warm']:
            lines.append(f"- Sıcak fırsat: {site['warm']}")
            for ts, sid, q in site['warm_items']:
                short = ' '.join(q.split())[:110]
                lines.append(f'   • {ts.astimezone(local_now.tzinfo).strftime("%H:%M")} #{sid}: "{short}"')
        elif site['real']:
            lines.append('- Sıcak fırsat işareti yok (fiyat, randevu, iletişim bilgisi gibi)')
        traffic = site.get('traffic')
        if traffic is not None:
            n = traffic.get
            if traffic:
                lines.append(f"- Siteyi gezen (tarayıcı oturumu): {n('visit', 0)}, showroom'a geçen: {n('showroom_link', 0)}")
                calls = n('whatsapp_click', 0) + n('pilot_call', 0)
                lines.append(f"- WhatsApp'a basan: {calls}" + (f" (pilot düğmesi: {n('pilot_call', 0)})" if n('pilot_call', 0) else ''))
                if n('faq_open', 0) or n('job_pick', 0):
                    lines.append(f"- İş örneği seçen: {n('job_pick', 0)}, sık sorulan soru açan: {n('faq_open', 0)}")
                lines.append('  (sayaçlar gün bazlıdır: dün ve bugün birlikte)')
            else:
                lines.append('- Site sayacında kayıt yok (henüz ziyaret gelmemiş ya da sayaç yeni açıldı)')
    lines += ['', 'SENDEN BEKLEYENLER']
    if approvals is None:
        lines.append(f'- {UNAVAILABLE} (görev panosuna ulaşılamadı)')
    else:
        lines.append(f"- Onay bekleyen iş: {approvals['waiting']}" if approvals['waiting'] else
                     '- Okunan kaynaklarda onay bekleyen iş yok' if approvals.get('unavailable') else
                     '- Onay bekleyen iş yok')
        if approvals.get('unavailable'):
            lines.append('- Onay verisi alınamadı: ' + ', '.join(approvals['unavailable']))
        if approvals.get('expired'):
            lines.append(f"- Süresi dolmuş onay: {approvals['expired']} (yeniden onaya sunulmalı)")
        if approvals.get('old'):
            lines.append(f"- Bunlardan {approvals['old']} tanesi 2 günden uzun süredir bekliyor")
        if approvals['stuck']:
            lines.append(f"- Takılan veya başarısız iş: {approvals['stuck']}")
    lines += ['', 'SİSTEM']
    if health is None:
        lines.append(f'- {UNAVAILABLE} (bekçi kaydı okunamadı)')
    else:
        if health['stale']:
            lines.append(f"- Dikkat: bekçi {health['age_min']} dakikadır kayıt yazmıyor; durum güncel olmayabilir")
        if health['bad']:
            lines.append(f"- {len(health['bad'])} sorun var:")
            lines.extend(f'   • {label}: {detail}' for label, detail in health['bad'])
        elif not health['stale']:
            lines.append(f"- Her şey normal ({health['total']}/{health['total']} kontrol sağlam)")
    if backup_h is not None:
        lines.append(f'- Son yedek: {backup_h} saat önce')
    lines += ['', advice_head, f'- {suggest(site, approvals, health)}']
    return '\n'.join(lines)


def split_message(text, limit=4000):
    parts, current = [], ''
    for line in text.split('\n'):
        if len(current) + len(line) + 1 > limit and current:
            parts.append(current)
            current = ''
        current += line + '\n'
    if current.strip():
        parts.append(current.rstrip())
    return parts


def _load_sent(state_file):
    try:
        data = json.loads(Path(state_file).read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def already_sent(state_file, day, kind='morning'):
    data = _load_sent(state_file)
    if data.get(f'last_sent_{kind}') == day:
        return True
    return kind == 'morning' and data.get('last_sent') == day   # written by the first version


def _mark(state_file, kind, day):
    data = _load_sent(state_file)
    data[f'last_sent_{kind}'] = day
    Path(state_file).write_text(json.dumps(data), encoding='utf-8')


def main(argv=None, now=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--chat-db', default='/home/hermes/cybergene-chat/data/support_chat.db')
    ap.add_argument('--bridge-db', default='/home/hermes/jeff_repo/jeff2/bridge/bridge.db')
    ap.add_argument('--panel-db', default='/home/hermes/cybergeneos-data/cgos.db')
    ap.add_argument('--watchdog-state', default='/home/hermes/logs/watchdog_state.json')
    ap.add_argument('--backup-dir', default='/home/hermes/backups')
    ap.add_argument('--sent-state', default='/home/hermes/logs/morning_report_state.json')
    ap.add_argument('--env-file')
    ap.add_argument('--tz', default='Europe/Istanbul')
    ap.add_argument('--kind', choices=sorted(KINDS), default='morning')
    ap.add_argument('--at', default='07:00', help='earliest local time to send (HH:MM)')
    ap.add_argument('--until', help='latest local time to send (HH:MM); later runs stay silent')
    ap.add_argument('--weekday', type=int, help='send only on this weekday (0=Monday .. 6=Sunday)')
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--send', action='store_true')
    args = ap.parse_args(argv)

    utc_now = now or datetime.now(timezone.utc)
    local_now = utc_now.astimezone(_zone(args.tz))
    day = local_now.strftime('%Y-%m-%d')
    if args.send:
        hh, mm = map(int, args.at.split(':'))
        if (local_now.hour, local_now.minute) < (hh, mm):
            print(f'[rapor] henuz erken ({local_now:%H:%M} < {args.at})')
            return 0
        if args.weekday is not None and local_now.weekday() != args.weekday:
            print('[rapor] bugun bu raporun gunu degil')
            return 0
        if args.until:
            uh, um = map(int, args.until.split(':'))
            if (local_now.hour, local_now.minute) > (uh, um):
                print(f'[rapor] zamani gecti ({local_now:%H:%M} > {args.until}), bugun atlandi')
                return 0
        if already_sent(args.sent_state, day, args.kind):
            print('[rapor] bugun zaten gonderildi')
            return 0

    ts = utc_now.timestamp()
    report = build_report(collect_site(args.chat_db, utc_now, WINDOW_HOURS[args.kind](local_now)),
                          collect_approvals(args.bridge_db, utc_now, panel_db=args.panel_db),
                          collect_health(args.watchdog_state, ts), collect_backup(args.backup_dir, ts),
                          local_now, args.kind)
    if args.dry_run:
        enc = sys.stdout.encoding or 'utf-8'
        print(report.encode(enc, 'replace').decode(enc, 'replace'))
        return 0

    # Routine reports remain available locally. They never wake the owner or
    # claim Telegram delivery; evidenced decisions use attention_policy only.
    report_dir=Path(args.sent_state).parent/'reports'
    report_dir.mkdir(parents=True,exist_ok=True)
    (report_dir/(args.kind+'-'+day+'.txt')).write_text(report,encoding='utf-8')
    print('[rapor] yerel rapor kaydedildi; rutin bildirim sessiz')
    return 0



if __name__ == '__main__':
    sys.exit(main())
