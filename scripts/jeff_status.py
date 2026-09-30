"""One-screen "how is Jeff right now" report in plain Turkish, built only from live measurements.

Meant to be run by the Telegram command /durum (a Hermes quick command) or from a shell:

    python scripts/jeff_status.py

Every line is measured now; a source that cannot be read says "veri alinamadi" instead of guessing.
"""
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:  # imported as a package (tests) or run from the scripts folder (server)
    from scripts import system_watchdog as wd
except ImportError:  # pragma: no cover
    import system_watchdog as wd

UNAVAILABLE = 'veri alinamadi'
HOME = Path('/home/hermes')


def _ago(seconds):
    m = int(seconds // 60)
    if m < 1:
        return 'az önce'
    if m < 60:
        return f'{m} dakika önce'
    h = m // 60
    return f'{h} saat önce' if h < 48 else f'{h // 24} gün önce'


def gateway_line(runner=subprocess.run):
    """Is Jeff's Telegram gateway up, connected, and not fighting another instance?"""
    try:
        active = runner(['systemctl', 'is-active', 'hermes-gateway'], capture_output=True, text=True, timeout=10)
        if (active.stdout or '').strip() != 'active':
            return 'Jeff (Telegram): ÇALIŞMIYOR'
        log = runner(['journalctl', '-u', 'hermes-gateway', '--since', '-30min', '--no-pager'],
                     capture_output=True, text=True, timeout=20).stdout or ''
    except Exception:
        return f'Jeff (Telegram): {UNAVAILABLE}'
    conflicts = log.lower().count('polling conflict')
    if conflicts >= 3:
        return f'Jeff (Telegram): açık ama başka bir kopya aynı botu dinliyor ({conflicts} çakışma, son 30 dk)'
    return 'Jeff (Telegram): çalışıyor'


def hermes_jobs_line(jobs_path=HOME / '.hermes/cron/jobs.json'):
    """Jeff's own scheduled jobs: how many run, how many are paused, how many last failed."""
    try:
        data = json.loads(Path(jobs_path).read_text(encoding='utf-8'))
        jobs = data.get('jobs', data) if isinstance(data, dict) else data
        active = [j for j in jobs if j.get('enabled', True) and not j.get('paused_at')]
        paused = len(jobs) - len(active)
        failing = [j.get('name') for j in active if str(j.get('last_status')) == 'error']
    except (OSError, ValueError, AttributeError):
        return f"Jeff'in kendi zamanlanmış işleri: {UNAVAILABLE}"
    text = f"Jeff'in kendi zamanlanmış işleri: {len(active)} aktif, {paused} duraklatılmış"
    if failing:
        text += f"; son çalışmada hata veren: {', '.join(map(str, failing[:4]))}"
    return text


def reports_line(sent_state=HOME / 'logs/morning_report_state.json', now=None):
    try:
        data = json.loads(Path(sent_state).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return f'Raporlar: {UNAVAILABLE}'
    names = {'morning': 'sabah', 'evening': 'akşam', 'weekly': 'haftalık'}
    parts = []
    for kind, label in names.items():
        day = data.get(f'last_sent_{kind}') or (data.get('last_sent') if kind == 'morning' else None)
        parts.append(f'{label}: {day or "henüz gitmedi"}')
    return 'Son gönderilen raporlar: ' + ', '.join(parts)


def watchdog_lines(state_path=HOME / 'logs/watchdog_state.json', now_ts=None):
    now_ts = now_ts or time.time()
    try:
        state = json.loads(Path(state_path).read_text(encoding='utf-8'))
        age = now_ts - Path(state_path).stat().st_mtime
    except (OSError, ValueError):
        return [f'Bekçi: {UNAVAILABLE}']
    labels = {c.key: c.label for c in wd.default_checks()}
    bad = [labels.get(k, k) for k, v in state.items() if not v.get('ok', True)]
    lines = []
    if age > 20 * 60:
        lines.append(f'Bekçi: {_ago(age)} kayıt yazdı, güncel olmayabilir')
    if bad:
        lines.append(f'Sorunlu ({len(bad)}): ' + ', '.join(bad))
    elif age <= 20 * 60:
        lines.append(f'Bekçi: {len(state)} kontrolün hepsi sağlam ({_ago(age)} bakıldı)')
    return lines


def build_status(now=None, gateway=gateway_line, jobs=hermes_jobs_line, reports=reports_line, dog=watchdog_lines):
    now = now or datetime.now(timezone.utc)
    lines = [f"Jeff durumu, {now.astimezone().strftime('%d.%m.%Y %H:%M')}", '']
    lines.append(gateway())
    lines.extend(dog())
    lines.append(jobs())
    lines.append(reports())
    lines.append('')
    lines.append('Bu ekrandaki her satır az önce ölçüldü; ölçülemeyen "veri alinamadi" der.')
    return '\n'.join(lines)


if __name__ == '__main__':
    out = build_status()
    enc = sys.stdout.encoding or 'utf-8'
    print(out.encode(enc, 'replace').decode(enc, 'replace'))
