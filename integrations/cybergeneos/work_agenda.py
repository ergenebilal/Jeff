"""Fast owner agenda from existing panel steps and the recorded Jarvis plan.

No new business rules, worker request, model call or store initialization.
"""
from contextlib import closing
from pathlib import Path
import re
import sqlite3
import threading
import time

PLAN = Path('/home/hermes/raporlar/JEFF_TO_JARVIS.md')


def clip(value, size):
    return re.sub(r'\s+', ' ', str(value or '')).strip()[:size]


def spoken_step(step):
    text=clip(step['text'],160)
    lowered=text.replace('İ','i').casefold()
    # A legacy panel button label is neither a current authorization nor a
    # customer delivery. Only the presentation changes; panel rules stay intact.
    if 'gönder' in lowered or 'onaylı' in lowered:
        return 'Mesaj kaydını ve taslağı incele; gönderim için ayrı geçerli onay gerekir'
    return text


def read(store, steps, plan=PLAN):
    result = {'observed_at': time.time(), 'read_only': True,
              'scope': 'panel_next_steps_and_recorded_jarvis_plan',
              'panel': {'known': False}, 'plan': {'known': False}}
    try:
        # Reuse installed read methods without running Store.__init__, which
        # performs migrations and changes interrupted jobs on startup.
        with closing(sqlite3.connect(Path(store.path).resolve().as_uri()+'?mode=ro', uri=True, timeout=1)) as db:
            db.row_factory = sqlite3.Row
            db.execute('PRAGMA query_only=ON')
            db.execute('BEGIN')
            view = object.__new__(type(store))
            view.path, view.db, view.lock = store.path, db, threading.RLock()
            leads = view.leads()
            next_steps = steps(view, leads)
            mine = [(lead, next_steps[lead['id']]) for lead in leads
                    if next_steps[lead['id']]['list'] == 'sira']
            mine.sort(key=lambda pair: pair[1].get('rank', 9))
            jobs = view.q("SELECT title,status FROM jobs WHERE status IN ('queued','running') ORDER BY created_at DESC,rowid DESC")
            result['panel'] = {'known': True, 'actionable_count': len(mine),
                'items': [{'name': clip(lead['name'], 80), 'next_step': spoken_step(step)} for lead, step in mine[:3]],
                'active_job_count': len(jobs),
                'active_jobs': [{'title': clip(job['title'], 100), 'recorded_status': job['status']} for job in jobs[:2]],
                'ranking': 'unchanged_panel_step_rank', 'worker_completion_verified': False}
    except Exception as exc:
        result['panel'] = {'known': False, 'failure_class': type(exc).__name__}
    try:
        if plan.is_symlink() or plan.stat().st_size > 400000:
            raise ValueError('Invalid plan source')
        text = plan.read_text(encoding='utf-8')
        line = next(line for line in text.splitlines() if line.startswith('**Sıradaki adım:**'))
        result['plan'] = {'known': True, 'source': 'JEFF_TO_JARVIS.md',
                          'next_step': clip(line.split('**Sıradaki adım:**', 1)[1], 550),
                          'execution_verified': False}
    except Exception as exc:
        result['plan'] = {'known': False, 'failure_class': type(exc).__name__}
    return result


def render(data):
    panel, plan = data['panel'], data['plan']
    parts = []
    if panel['known']:
        if panel['actionable_count']:
            parts.append(f"Panelde senden bir adım bekleyen {panel['actionable_count']} kayıt var.")
            parts.extend(f"{item['name']}: {item['next_step']}." for item in panel['items'])
        else:
            parts.append('Panelde senden bir adım bekleyen kayıt görünmüyor.')
        if panel['active_job_count']:
            labels = {'queued': 'sırada', 'running': 'çalışıyor'}
            parts.append('Ayrıca panel görev kaydında: '+ '; '.join(
                f"{item['title']}, {labels[item['recorded_status']]}" for item in panel['active_jobs'])+'.')
            parts.append('Bu kayıt, işin tamamlandığını doğrulamaz.')
    else:
        parts.append('Panelin yapılacak iş listesine şu anda erişemiyorum.')
    # An explicit work question gets the owner's concrete next steps. Routine
    # infrastructure maintenance must not crowd them out or become a new task.
    if plan['known'] and (not panel['known'] or not panel['actionable_count']):
        parts.append('Jarvis planında sıradaki adım: '+plan['next_step'])
    elif not panel['known'] or not panel['actionable_count']:
        parts.append('Jarvis planını da okuyamadım; sana iş yok diyemem.')
    return ' '.join(parts)
