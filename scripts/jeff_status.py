"""One-screen "how is Jeff right now" report in plain Turkish, built only from live measurements.

Meant to be run by the Telegram command /durum (a Hermes quick command) or from a shell:

    python scripts/jeff_status.py

Every line is measured now; a source that cannot be read says "veri alinamadi" instead of guessing.
"""
import json
import math
from contextlib import closing
import re
import subprocess
import sqlite3
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


def model_route_line(db_path=HOME / '.hermes/state.db', now_ts=None):
    """Only actual call receipts establish a used route; probes never do."""
    now_ts=time.time() if now_ts is None else now_ts
    try:
        path=Path(db_path).resolve()
        db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
        try:
            row=db.execute('SELECT requested_route,actual_route,status,fallback_used,fallback_reason,started_at,ended_at '
                           'FROM model_route_receipts ORDER BY rowid DESC LIMIT 1').fetchone()
        finally:
            db.close()
        if row is None:
            return 'Son model çağrısı: bilinmiyor (makbuz yok)'
        requested,actual,status,fallback,reason,started,ended=row
        def valid_time(value):
            return (type(value) in (int,float) and math.isfinite(value) and
                    0 <= value <= now_ts+5)
        if (not valid_time(started) or status not in ('running','succeeded','failed','unknown') or
                (ended is not None and (not valid_time(ended) or ended < started)) or
                (status != 'running' and ended is None) or
                (status == 'running' and ended is not None)):
            return 'Son model çağrısı: bilinmiyor (makbuz tutarsız)'
        # A failed write makes a cached result historical until a later completed
        # call is recorded. Keep the marker as history; never print its contents.
        marker=path.parent/'model-route-receipt-error.json'
        try:
            error=json.loads(marker.read_text(encoding='utf-8'))
        except FileNotFoundError:
            pass
        except (OSError,ValueError):
            return 'Son model çağrısı: bilinmiyor (kayıt güvenilirliği doğrulanamadı)'
        else:
            if (not isinstance(error,dict) or error.get('status') != 'unknown' or
                    not valid_time(error.get('observed_at'))):
                return 'Son model çağrısı: bilinmiyor (kayıt güvenilirliği doğrulanamadı)'
            if ended is None or ended <= error['observed_at']:
                return 'Son model çağrısı: bilinmiyor (makbuz kaydı başarısız; önceki sonuç geçmişte kaldı)'
        text=f'Son model çağrısı: {actual}; sonuç: {status}; tercih: {requested}'
        if fallback:
            text+=f'; fallback nedeni: {reason or "bilinmiyor"}'
        if ended is None or now_ts-ended>1800:
            text+='; geçmiş/bitmemiş makbuz, güncel sağlık değildir'
        return text
    except (OSError,sqlite3.Error):
        return 'Son model çağrısı: bilinmiyor (makbuz okunamadı)'


def model_success_line(db_path=HOME / '.hermes/state.db', now_ts=None):
    """Historical successful calls come only from completed physical receipts."""
    now_ts=time.time() if now_ts is None else now_ts
    try:
        with closing(sqlite3.connect(Path(db_path).resolve().as_uri()+'?mode=ro',uri=True)) as db:
            row=db.execute("SELECT actual_route,ended_at FROM model_route_receipts WHERE status='succeeded' "
                           "AND actual_route NOT IN ('','unknown') AND typeof(started_at) IN ('integer','real') "
                           "AND typeof(ended_at) IN ('integer','real') AND started_at>=0 AND ended_at>=started_at "
                           "AND ended_at<=? ORDER BY ended_at DESC,rowid DESC LIMIT 1",(now_ts+5,)).fetchone()
        if row is None:
            return 'Son kayıtlı başarılı çağrı: bilinmiyor (başarı makbuzu yok)'
        when=datetime.fromtimestamp(row[1],timezone.utc).strftime('%d.%m.%Y %H:%M:%S UTC')
        return f'Son kayıtlı başarılı çağrı: {row[0]}; {when} (geçmiş kayıt)'
    except (OSError,sqlite3.Error,ValueError,OverflowError):
        return 'Son kayıtlı başarılı çağrı: bilinmiyor (makbuz okunamadı)'


def model_probe_line(path=HOME / 'logs/model_health.json', now_ts=None):
    """Read probe availability without inferring a real session route or success."""
    now_ts=time.time() if now_ts is None else now_ts
    try:
        try:
            from scripts.model_health import health_snapshot
        except ImportError:  # direct script execution on the server
            from model_health import health_snapshot
        report=json.loads(Path(path).read_text(encoding='utf-8'))
        view=health_snapshot(report,now=lambda:now_ts)
        if view['health_status']=='unknown':
            return 'Model yoklaması: bilinmiyor (kayıt eski, eksik veya tutarsız)'
        preferred=view['preferred_route']
        verdict='yanıt verdi' if view['preferred_status']=='healthy' else 'yanıt vermedi'
        others=', '.join(route for route in view['available_routes'] if route!=preferred) or 'yok'
        when=datetime.fromtimestamp(view['observed_at'],timezone.utc).strftime('%d.%m.%Y %H:%M:%S UTC')
        return f'Model yoklaması: tercih {preferred} {verdict}; yanıt veren diğer yollar: {others}; ölçüm: {when}'
    except (OSError,ValueError,OverflowError):
        return 'Model yoklaması: bilinmiyor (kontrol kaydı okunamadı)'


def hermes_jobs_line(jobs_path=HOME / '.hermes/cron/jobs.json'):
    """Jeff's own scheduled jobs: how many run, how many are paused, how many last failed."""
    try:
        data = json.loads(Path(jobs_path).read_text(encoding='utf-8'))
        jobs = data.get('jobs', data) if isinstance(data, dict) else data
        if not isinstance(jobs,list) or any(not isinstance(j,dict) for j in jobs):
            raise ValueError('Invalid job inventory')
        active = [j for j in jobs if j.get('enabled', True) and not j.get('paused_at')]
        paused = len(jobs) - len(active)
        groups = {key: [] for key in ('error','delivery_failed','timeout','interrupted','unknown')}
        for job in active:
            raw = str(job.get('last_status') or 'unknown')
            status = raw.strip().lower().replace(' ','_')
            if status == 'ok':
                continue
            category = status if status in groups else 'unknown'
            name = job.get('name') or job.get('id') or 'kimlik bilinmiyor'
            when = job.get('last_run_at') or job.get('last_run') or 'çalışma zamanı bilinmiyor'
            detail = f'{name} [son çalışma: {when}]'
            if category == 'unknown':
                detail += f' [ham sonuç: {raw}]'
            groups[category].append(detail)
    except (OSError, ValueError, AttributeError):
        return f"Jeff'in kendi zamanlanmış işleri: {UNAVAILABLE}"
    text = f"Jeff'in kendi zamanlanmış işleri: {len(active)} aktif, {paused} duraklatılmış"
    labels={'error':'son çalışmada hata veren','delivery_failed':'çalıştı; teslim başarısız',
            'timeout':'zaman aşımı','interrupted':'kesilen','unknown':'sonucu bilinmeyen'}
    for category,items in groups.items():
        if items:
            text += f"; {labels[category]}: {', '.join(items)}"
    return text


def reports_line(sent_state=HOME / 'logs/morning_report_state.json', now=None):
    if (Path(sent_state).parent/'reports').is_dir():
        files=sorted((Path(sent_state).parent/'reports').glob('*.txt'),key=lambda p:p.stat().st_mtime)
        return 'Rutin raporlar: yerel arşiv; bildirim sessiz; son kayıt: '+(files[-1].name if files else 'henüz yok')
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


def attention_line(path=HOME/'logs/attention.db'):
    try:
        with sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True) as db:
            counts=dict(db.execute('SELECT status,count(*) FROM attention_outbox GROUP BY status'))
        return f"Karar bildirimleri: teslim {counts.get('sent',0)}, teslimi belirsiz {counts.get('delivery_unknown',0)}, bitmemiş {counts.get('sending',0)}"
    except sqlite3.Error:return 'Karar bildirimleri: veri alınamadı'


def build_status(now=None, gateway=gateway_line, jobs=hermes_jobs_line, reports=reports_line, dog=watchdog_lines,
                 model=model_route_line, model_success=model_success_line, model_probe=model_probe_line):
    now = now or datetime.now(timezone.utc)
    lines = [f"Jeff durumu, {now.astimezone().strftime('%d.%m.%Y %H:%M')}", '']
    lines.append(gateway())
    lines.append(model())
    lines.append(model_success())
    lines.append(model_probe())
    lines.extend(dog())
    lines.append(jobs())
    lines.append(reports())
    lines.append(attention_line())
    lines.append('')
    lines.append('Bu ekrandaki her satır az önce ölçüldü; ölçülemeyen "veri alinamadi" der.')
    return '\n'.join(lines)


if __name__ == '__main__':
    out = build_status()
    enc = sys.stdout.encoding or 'utf-8'
    print(out.encode(enc, 'replace').decode(enc, 'replace'))
