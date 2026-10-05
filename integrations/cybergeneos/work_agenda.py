"""Fast owner agenda from existing panel steps and the recorded Jarvis plan.

No new business rules, worker request, model call or store initialization.
"""
from contextlib import closing
from pathlib import Path
import json
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
            parts.append('İş listende öne çıkan adımlar şunlar:')
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


def read_radar(store):
    """Read saved news/results only. Never start or retry a scan."""
    data={'known':False,'observed_at':time.time(),'read_only':True}
    try:
        with closing(sqlite3.connect(Path(store.path).resolve().as_uri()+'?mode=ro',uri=True,timeout=1)) as db:
            db.row_factory=sqlite3.Row;db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
            row=db.execute("SELECT status,finished_at,result FROM jobs WHERE kind='radar' ORDER BY created_at DESC,rowid DESC LIMIT 1").fetchone()
            latest={'known':row is not None}
            if row:
                latest.update(recorded_status=row['status'],finished_at=row['finished_at'],result_known=False)
                if row['status']=='done':
                    try:
                        result=json.loads(row['result'] or 'null')
                        fields=('news','opps','sources_ok','sources_down')
                        if isinstance(result,dict) and all(type(result.get(k)) is int and result[k]>=0 for k in fields) and row['finished_at']:
                            latest.update(result_known=True,counts={k:result[k] for k in fields})
                    except (ValueError,TypeError):pass
            rows=db.execute('SELECT title,why,src,published_at FROM news WHERE published_at>? ORDER BY IFNULL(stars,0) DESC,published_at DESC LIMIT 3',(time.time()-72*3600,)).fetchall()
            data.update(known=True,last_scan=latest,news=[{'title':clip(r['title'],140),'why':clip(r['why'],180),'source':clip(r['src'],60),'published_at':r['published_at']} for r in rows],
                        news_scope='saved_panel_news_last_72h_existing_rank',new_scan_started=False)
    except Exception as exc:data['failure_class']=type(exc).__name__
    return data


def render_radar(data):
    if not data['known']:return 'Kayıtlı haber ve tarama sonuçlarına şu anda erişemiyorum. Yeni tarama başlatmadım; sonuç yok diyemem.'
    scan=data['last_scan'];parts=['Mevcut haber kayıtlarını okuyorum; yeni tarama başlatmadım.']
    if not scan['known']:parts.append('Kayıtlı bir haber taraması bulunamadı.')
    elif scan['recorded_status']=='done' and scan['result_known']:
        c=scan['counts'];parts.append(f"Son tarama kaydında tamamlandı: {c['news']} haber, {c['opps']} fırsat eklendi. {c['sources_ok']} kaynak okundu; {c['sources_down']} kaynağa erişilemedi.")
        if data['observed_at']-scan['finished_at']>3*3600:parts.append('Bu tarama üç saatten eski; şu an yapılmış tarama gibi sunmuyorum.')
    elif scan['recorded_status'] in ('queued','running'):parts.append('Son tarama kayıtta hâlâ sürüyor; bitmiş saymıyorum. Aşağıdaki haberler daha önce kaydedilenlerden.')
    elif scan['recorded_status']=='done':parts.append('Son tarama tamamlandı diye işaretli ama sonuç sayıları doğrulanamadı.')
    else:parts.append('Son tarama kaydı başarılı tamamlanma göstermiyor.')
    if data['news']:
        parts.append('Panelde son yetmiş iki saatte kaydedilmiş öne çıkan haberler:')
        parts.extend(item['title']+(': '+item['why'] if item['why'] else '')+'.' for item in data['news'])
    else:parts.append('Panelde son yetmiş iki saat kapsamında haber kaydı görünmüyor; bu dünyada yeni haber yok demek değildir.')
    return ' '.join(parts)
