"""Jeff system watchdog: tells Bilal on Telegram when something breaks, and when it recovers.

Run from cron every 5 minutes on the server. It only *observes and notifies*; it never
restarts anything. State lives in a small JSON file so a problem is announced once, repeated
as a reminder every few hours while it lasts, and closed with a "fixed" message.

    python scripts/system_watchdog.py --state /home/hermes/logs/watchdog_state.json [--dry-run]

Telegram credentials come from the environment (ALERT_BOT_TOKEN, ALERT_CHAT_ID) or from
the file named by --env-file (KEY=VALUE lines). Nothing secret is written to logs.
"""
import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

REMIND_EVERY_SECONDS = 6 * 3600
BACKUP_MAX_AGE_HOURS = 30
DISK_MAX_PERCENT = 90


@dataclass
class Check:
    key: str
    label: str            # plain-language name shown to Bilal
    impact: str           # what it means for him if this is down
    run: object           # callable -> (ok: bool, detail: str)
    grace_seconds: int = 0  # how long it may fail before we bother him


# ---------------------------------------------------------------- probes

def unit_active(unit, runner=subprocess.run):
    def probe():
        try:
            out = runner(['systemctl', 'is-active', unit], capture_output=True, text=True, timeout=10)
            state = (out.stdout or '').strip() or 'unknown'
        except Exception as exc:
            return False, f'kontrol edilemedi ({type(exc).__name__})'
        return state == 'active', state
    return probe


def http_reachable(url, ok_statuses=None, timeout=6, opener=urllib.request.urlopen):
    """Reachable means the server answered. 4xx from a locked door still proves it is up."""
    def probe():
        try:
            with opener(url, timeout=timeout) as resp:
                status = resp.status
        except urllib.error.HTTPError as err:
            status = err.code
        except Exception as exc:
            return False, f'yanit yok ({type(exc).__name__})'
        good = ok_statuses(status) if ok_statuses else 200 <= status < 300
        return good, f'HTTP {status}'
    return probe


def any_answer(status):
    return status < 500


def backup_fresh(directory, max_age_hours=BACKUP_MAX_AGE_HOURS, now=time.time):
    def probe():
        files = sorted(Path(directory).glob('jeff-backup-*.tar.gz'), key=lambda p: p.stat().st_mtime) \
            if Path(directory).is_dir() else []
        if not files:
            return False, 'hic yedek yok'
        age_h = (now() - files[-1].stat().st_mtime) / 3600
        return age_h <= max_age_hours, f'son yedek {age_h:.0f} saat once'
    return probe


def marker_fresh(path, max_age_days=9, now=time.time):
    """The PC touches this marker after every verified off-server copy of the backup."""
    def probe():
        marker = Path(path)
        if not marker.exists():
            return False, 'bilgisayara hic kopya alinmamis'
        age_days = (now() - marker.stat().st_mtime) / 86400
        return age_days <= max_age_days, f'son bilgisayar kopyasi {age_days:.0f} gun once'
    return probe


def disk_ok(path='/', max_percent=DISK_MAX_PERCENT, usage=shutil.disk_usage):
    def probe():
        u = usage(path)
        pct = u.used * 100 / u.total
        return pct < max_percent, f'%{pct:.0f} dolu'
    return probe


def telegram_not_fighting(unit='hermes-gateway.service', limit=3, runner=subprocess.run):
    """Two Jeffs polling the same bot show up as repeated 'polling conflict' lines."""
    def probe():
        try:
            out = runner(['journalctl', '-u', unit, '--since', '-10min', '--no-pager'],
                         capture_output=True, text=True, timeout=15)
        except Exception as exc:
            return True, f'gunluk okunamadi ({type(exc).__name__})'  # do not cry wolf on a read failure
        n = (out.stdout or '').lower().count('polling conflict')
        return n < limit, f'{n} cakisma (son 10 dk)'
    return probe


def _model_probe(path):
    """Reads the report written by model_health.py; imported lazily so the two scripts stay independent."""
    try:
        from scripts.model_health import watchdog_probe
    except ImportError:  # pragma: no cover - running from the scripts folder on the server
        from model_health import watchdog_probe
    return watchdog_probe(path)


def default_checks(backup_dir='/home/hermes/backups', model_report='/home/hermes/logs/model_health.json'):
    def unit(u, label, impact, grace=0):
        return Check(f'unit:{u}', label, impact, unit_active(u), grace)
    return [
        unit('hermes-gateway', 'Jeff (Telegram)', 'Jeff Telegram mesajlarina cevap vermez'),
        unit('jeff-bridge', 'Gorev panosu', 'Jeff ile Pablo arasinda is devri durur'),
        unit('cybergene-chat', 'Site sohbet servisi', 'Sitedeki canli destek cevap vermez'),
        unit('nginx', 'Web sunucusu', 'Site acilmaz'),
        unit('hermes-hq', 'Komuta merkezi', 'Komuta paneli acilmaz', 300),
        unit('jeff-mobile', 'Mobil baglanti', 'Telefon baglantisi calismaz', 300),
        Check('http:site', 'cybergene.co sitesi', 'Musteriler siteyi goremez',
              http_reachable('https://cybergene.co/'), 120),
        Check('http:chat', 'Sohbet sagligi', 'Sitedeki sohbet cevap vermez',
              http_reachable('http://127.0.0.1:8774/health'), 120),
        Check('http:proxy', 'Yapay zeka koprusu', 'Jeff dusunemez, cevap uretemez',
              http_reachable('http://127.0.0.1:8999/v1/models'), 120),
        Check('http:bridge', 'Gorev panosu (ag)', 'Pablo ile baglanti kopar',
              http_reachable('http://100.80.122.74:7700/health', any_answer), 300),
        # The PC may be asleep at night; only worth a message if it stays gone.
        Check('http:pablo', "Pablo (Bilal'in bilgisayari)", 'Bilgisayardaki isler (WhatsApp, tarayici) yapilamaz',
              http_reachable('http://100.89.26.86:7788/ping', any_answer), 3600),
        Check('model', "Jeff'in dusunme yolu", 'Jeff cevap uretemez ya da yedek yolla calisiyor', _model_probe(model_report), 600),
        Check('telegram', 'Telegram baglantisi', 'Jeff iki yerde birden dinliyor olabilir, mesajlar kacabilir',
              telegram_not_fighting(), 0),
        Check('backup', 'Gece yedegi', 'Bir sey bozulursa geri donecek guncel yedek yok',
              backup_fresh(backup_dir), 0),
        Check('offsite', 'Yedegin bilgisayara kopyasi', 'Sunucu bozulursa yedekler de onunla birlikte gider',
              marker_fresh(f'{backup_dir}/.offsite-copy-ok'), 0),
        Check('disk', 'Disk alani', 'Disk dolarsa her sey durur', disk_ok(), 0),
    ]


# ---------------------------------------------------------------- state machine

def evaluate(checks, state, now):
    """Return (new_state, events). Events are ('down'|'remind'|'up', check, detail, since)."""
    events = []
    new_state = {}
    for chk in checks:
        try:
            ok, detail = chk.run()
        except Exception as exc:  # a broken probe must not silence the others
            ok, detail = False, f'kontrol hatasi ({type(exc).__name__})'
        prev = state.get(chk.key, {'ok': True})
        cur = dict(prev)
        if ok:
            if prev.get('alerted'):
                # Keep the old record until the "fixed" message is really delivered, so a failed
                # send is retried on the next run (apply_events clears it on success).
                events.append(('up', chk, detail, prev.get('since', now)))
            else:
                cur = {'ok': True}
        else:
            if prev.get('ok', True):
                cur = {'ok': False, 'since': now, 'alerted': False, 'last_alert': 0}
            since = cur.get('since', now)
            if not cur.get('alerted') and now - since >= chk.grace_seconds:
                events.append(('down', chk, detail, since))
            elif cur.get('alerted') and now - cur.get('last_alert', 0) >= REMIND_EVERY_SECONDS:
                events.append(('remind', chk, detail, since))
            cur['detail'] = detail
        new_state[chk.key] = cur
    return new_state, events


def _duration(seconds):
    m = int(seconds // 60)
    if m < 60:
        return f'{max(m, 1)} dakika'
    h, m = divmod(m, 60)
    return f'{h} saat {m} dakika' if m else f'{h} saat'


def format_event(kind, chk, detail, since, now):
    if kind == 'up':
        return f'✅ Duzeldi: {chk.label}\n{_duration(now - since)} sorunluydu, simdi normal.'
    head = '⚠️ Sorun var' if kind == 'down' else '⏰ Hala duzelmedi'
    extra = f'\n{_duration(now - since)}dir sorunlu.' if kind == 'remind' else ''
    return (f'{head}: {chk.label}\nNe anlama geliyor: {chk.impact}.{extra}\n'
            f'Son durum: {detail}\nJeff bunu kendiliginden yeniden baslatmaz; bakilmasi gerekiyor.')


def apply_events(events, state, now, send):
    """Send messages; only mark as announced when Telegram accepted it, so a failed send retries."""
    for kind, chk, detail, since in events:
        if not send(format_event(kind, chk, detail, since, now)):
            continue
        if kind in ('down', 'remind'):
            state[chk.key]['alerted'] = True
            state[chk.key]['last_alert'] = now
        elif kind == 'up':
            state[chk.key] = {'ok': True}
    return state


# ---------------------------------------------------------------- io

def load_env_file(path):
    values = {}
    try:
        for line in Path(path).read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                values[k.strip()] = v.strip().strip('"\'')
    except OSError:
        pass
    return values


def telegram_sender(token, chat_id, opener=urllib.request.urlopen):
    def send(text):
        body = json.dumps({'chat_id': chat_id, 'text': text}).encode()
        req = urllib.request.Request(f'https://api.telegram.org/bot{token}/sendMessage', data=body,
                                     headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with opener(req, timeout=10) as resp:
                return resp.status == 200
        except Exception as exc:
            print(f'[watchdog] telegram gonderilemedi ({type(exc).__name__})', file=sys.stderr)
            return False
    return send


def load_state(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def save_state(path, state):
    tmp = Path(str(path) + '.tmp')
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding='utf-8')
    os.replace(tmp, path)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--state', required=True)
    ap.add_argument('--env-file')
    ap.add_argument('--backup-dir', default='/home/hermes/backups')
    ap.add_argument('--dry-run', action='store_true', help='print messages instead of sending')
    args = ap.parse_args(argv)

    env = dict(os.environ)
    if args.env_file:
        env.update(load_env_file(args.env_file))
    if args.dry_run:
        def send(text):
            enc = sys.stdout.encoding or 'utf-8'
            print(('--- MESAJ ---\n' + text).encode(enc, 'replace').decode(enc, 'replace'))
            return True
    else:
        token, chat = env.get('ALERT_BOT_TOKEN'), env.get('ALERT_CHAT_ID')
        if not token or not chat:
            print('[watchdog] ALERT_BOT_TOKEN / ALERT_CHAT_ID yok', file=sys.stderr)
            return 2
        send = telegram_sender(token, chat)

    now = time.time()
    state = load_state(args.state)
    new_state, events = evaluate(default_checks(args.backup_dir), state, now)
    new_state = apply_events(events, new_state, now, send)
    if not args.dry_run:   # a rehearsal must never mark problems as announced
        save_state(args.state, new_state)
    bad = [k for k, v in new_state.items() if not v.get('ok', True)]
    print(f'[watchdog] {len(new_state)} kontrol, sorunlu: {bad or "yok"}, mesaj: {len(events)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
