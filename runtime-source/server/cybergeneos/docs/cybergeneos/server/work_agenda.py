"""Read-only panel agenda, distinct Windows candidate records and recorded plan.

A recorded business stage is neither verified need, current work nor permission.
"""
from contextlib import closing
from pathlib import Path
import json
import math
import re
import sqlite3
import threading
import time
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler

PLAN = Path('/home/hermes/raporlar/JEFF_TO_JARVIS.md')
NODE_HOST = 'http://100.89.26.86:7788'
AGENDA_PATH = '/marketing/agenda?offset=0&limit=20'
MAX_RESPONSE_BYTES = 65536
AGENDA_CONTACT_MODES = ('direct_link', 'phone_only', 'instagram_link_only')
AGENDA_FIELDS = {'schema_version','status','observed_at','total_records','offset','next_offset','items'}
ALLOWED_CONTRACT_FIELDS = {'id','company_name','district','stage','source_url','source_observed_at','contact_mode','loss_verified'}


def clip(value, size):
    return re.sub(r'\s+', ' ', str(value or '')).strip()[:size]


def spoken_step(step):
    text = clip(step['text'], 160)
    lowered = text.replace('İ', 'i').casefold()
    if 'gönder' in lowered or 'onaylı' in lowered:
        return 'Mesaj kaydını ve taslağı incele; gönderim için ayrı geçerli onay gerekir'
    return text


def candidate_next_step(stage):
    """Presentation of a recorded stage, not new business or authorization rules."""
    if not stage or not isinstance(stage,str):return 'kayıt durumu bilinmiyor; bağımsız doğrulama gerekir'
    st=stage.casefold().strip()
    labels={'radar':'kaynak ve ilk sinyal doğrulaması bekliyor',
            'yeni':'ilk inceleme bekliyor','kesif':'ilk inceleme bekliyor','keşif':'ilk inceleme bekliyor',
            'incelendi':'iletişim kanalı kararı bekliyor','nitelikli':'iletişim kanalı kararı bekliyor',
            'taslak_hazir':'taslağın incelenmesi bekliyor; gönderim için ayrı geçerli onay gerekir',
            'taslak hazır':'taslağın incelenmesi bekliyor; gönderim için ayrı geçerli onay gerekir',
            'onay_bekliyor':'onay bekliyor; gönderim için ayrı geçerli onay gerekir',
            'onay bekliyor':'onay bekliyor; gönderim için ayrı geçerli onay gerekir',
            'gonderildi':'takip zamanı bekleniyor','gönderildi':'takip zamanı bekleniyor',
            'yanit_geldi':'yanıtın okunması bekliyor','yanıt geldi':'yanıtın okunması bekliyor',
            'gorusme':'görüşme sonucunun işaretlenmesi bekliyor','görüşme':'görüşme sonucunun işaretlenmesi bekliyor'}
    return labels.get(st,'kayıt durumu bilinmiyor; bağımsız doğrulama gerekir')


def unknown_marketing(reason='AgendaUnavailable'):
    return {'known':False,'failure_class':reason,'status':'unavailable','observed_at':None,
            'total_records':None,'candidate_count':None,'items':[],'next_offset':None,
            'complete_list':False,'counts_scope':'current_page_only','outcome_verified':False,
            'semantic_goal_verified':False,'execution_authorized':False,'read_only':True,
            'source_instruction_authority':'none','current_truth_verified':False}


def _finite(value):
    return type(value) in (int,float) and math.isfinite(value) and value>0


def _text(value,bound,nullable=False):
    return nullable and value is None or isinstance(value,str) and len(value)<=bound and all(ord(c)>=32 for c in value)


def validate_marketing_agenda(data, *, now):
    if (not isinstance(data,dict) or set(data)!=AGENDA_FIELDS or type(data['schema_version']) is not int
            or data['schema_version']!=1 or data['status'] not in ('observed','observed_partial','unavailable')
            or type(data['offset']) is not int or data['offset']!=0):raise ValueError('Invalid agenda contract')
    if data['status']=='unavailable':
        if data['observed_at'] is not None or data['total_records'] is not None or data['next_offset'] is not None or data['items']!=[]:
            raise ValueError('Invalid unavailable projection')
        return unknown_marketing('SourceUnavailable')
    stamp=data['observed_at'];total=data['total_records'];items=data['items'];cursor=data['next_offset']
    if not _finite(now) or not _finite(stamp) or now-stamp>60 or stamp>now+5:raise ValueError('Invalid observation time')
    if type(total) is not int or not 0<=total<=1000000 or not isinstance(items,list) or len(items)>min(total,20):
        raise ValueError('Invalid count or page')
    partial=data['status']=='observed_partial';slots=min(total,20)
    if (not partial and len(items)!=slots or partial and total==0
            or total<=20 and cursor is not None
            or total>20 and (type(cursor) is not int or cursor!=20)):
        raise ValueError('Invalid page cursor')
    clean=[];seen=set()
    for row in items:
        if not isinstance(row,dict) or set(row)!=ALLOWED_CONTRACT_FIELDS:raise ValueError('Invalid record fields')
        rid=row['id'];source_time=row['source_observed_at'];url=row['source_url']
        if (type(rid) is not int or not 0<rid<=9223372036854775807 or rid in seen
                or not _text(row['company_name'],120) or not _text(row['district'],60,True)
                or not _text(row['stage'],40,True) or not _text(url,300,True)
                or source_time is not None and (not _finite(source_time) or source_time>now+5)
                or row['contact_mode'] is not None and row['contact_mode'] not in AGENDA_CONTACT_MODES
                or row['loss_verified'] is not None and row['loss_verified'] is not False):
            raise ValueError('Invalid record value')
        if url:
            parsed=urlsplit(url)
            if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username is not None or parsed.password is not None:
                raise ValueError('Invalid source URL')
        seen.add(rid);clean.append(dict(row))
    return {'known':True,'source':'windows_marketing_agenda','status':data['status'],'observed_at':stamp,
            'total_records':total,'candidate_count':len(clean),'items':clean,'next_offset':cursor,
            'complete_list':not partial and cursor is None and len(clean)==total,
            'counts_scope':'current_page_only','total_count_scope':'reported_candidate_ledger_count',
            'outcome_verified':False,'semantic_goal_verified':False,'execution_authorized':False,
            'read_only':True,'source_instruction_authority':'none','current_truth_verified':False}


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


def read_marketing_agenda(key=None, endpoint=None, timeout=3, *, clock=time.time):
    """The production caller passes its existing app.DATA credential in memory.

    endpoint is private fixture injection, never model/body input. No key helper,
    sudo, relative config, proxy, redirect, mutation or second-page request.
    """
    if not isinstance(key,str) or not key or any(ord(c)<32 for c in key):return unknown_marketing('CredentialUnavailable')
    try:
        request=Request(endpoint or NODE_HOST+AGENDA_PATH,headers={'X-Bridge-Key':key},method='GET')
        opener=build_opener(ProxyHandler({}),_NoRedirect())
        with opener.open(request,timeout=timeout) as response:raw=response.read(MAX_RESPONSE_BYTES+1)
        if len(raw)>MAX_RESPONSE_BYTES:raise ValueError('Response exceeds maximum size')
        def unique(pairs):
            result={}
            for name,value in pairs:
                if name in result:raise ValueError('Duplicate field')
                result[name]=value
            return result
        def invalid(_):raise ValueError('Invalid JSON number')
        data=json.loads(raw.decode('utf-8'),object_pairs_hook=unique,parse_constant=invalid)
        return validate_marketing_agenda(data,now=clock())
    except Exception as exc:
        return unknown_marketing(type(exc).__name__)


def read(store, steps, plan=PLAN, marketing_reader=None):
    result={'observed_at':time.time(),'read_only':True,'source_instruction_authority':'none',
            'scope':'panel_next_steps_windows_candidate_records_and_recorded_plan',
            'panel':{'known':False},'marketing':unknown_marketing(),'plan':{'known':False}}
    try:
        with closing(sqlite3.connect(Path(store.path).resolve().as_uri()+'?mode=ro',uri=True,timeout=1)) as db:
            db.row_factory=sqlite3.Row;db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
            view=object.__new__(type(store));view.path,view.db,view.lock=store.path,db,threading.RLock()
            leads=view.leads();next_steps=steps(view,leads)
            mine=[(lead,next_steps[lead['id']]) for lead in leads if next_steps[lead['id']]['list']=='sira']
            mine.sort(key=lambda pair:pair[1].get('rank',9))
            jobs=view.q("SELECT title,status FROM jobs WHERE status IN ('queued','running') ORDER BY created_at DESC,rowid DESC")
            result['panel']={'known':True,'actionable_count':len(mine),
                'items':[{'name':clip(lead['name'],80),'next_step':spoken_step(step)} for lead,step in mine[:3]],
                'active_job_count':len(jobs),'active_jobs':[{'title':clip(job['title'],100),'recorded_status':job['status']} for job in jobs[:2]],
                'ranking':'unchanged_panel_step_rank','worker_completion_verified':False}
    except Exception as exc:result['panel']={'known':False,'failure_class':type(exc).__name__}
    if marketing_reader is not None:
        try:
            marketing=marketing_reader()
            if not isinstance(marketing,dict) or type(marketing.get('known')) is not bool:raise ValueError('Invalid reader output')
            if marketing['known']:
                # Revalidate consumer metadata rather than trusting an injected count.
                raw={k:marketing.get(k) for k in ('status','observed_at','total_records','next_offset','items')}
                raw.update(schema_version=1,offset=0)
                marketing=validate_marketing_agenda(raw,now=time.time())
            result['marketing']=marketing if marketing['known'] else unknown_marketing(marketing.get('failure_class','AgendaUnavailable'))
        except Exception as exc:result['marketing']=unknown_marketing(type(exc).__name__)
    # No implicit credential discovery or Windows access in voice/other callers.
    try:
        path=Path(plan)
        if path.is_symlink():raise ValueError('Invalid plan source')
        with path.open('rb') as handle:head=handle.read(16384)
        # A truncated final line is not a complete current-header field.
        if len(head)==16384 and not head.endswith(b'\n'):head=head.rsplit(b'\n',1)[0]
        text=head.decode('utf-8')
        lines=[]
        for current in text.splitlines():
            if current.strip()=='---':break
            lines.append(current)
        line=next(line for line in lines if line.startswith('**Sıradaki adım:**'))
        result['plan']={'known':True,'source':'JEFF_TO_JARVIS.md','next_step':clip(line.split('**Sıradaki adım:**',1)[1],550),
                        'scope':'current_source_header_only','execution_verified':False}
    except Exception as exc:result['plan']={'known':False,'failure_class':type(exc).__name__}
    return result


def render(data):
    panel=data.get('panel',{'known':False});marketing=data.get('marketing',unknown_marketing());plan=data.get('plan',{'known':False});parts=[]
    if panel.get('known') is True:
        if panel.get('actionable_count'):
            parts.append('Panel iş listende öne çıkan kayıtlı adımlar:')
            parts.extend(f"{item['name']}: {item['next_step']}." for item in panel['items'])
        else:parts.append('Panelde senden bir adım bekleyen kayıt görünmüyor; diğer kaynaklar bundan çıkarılamaz.')
        if panel.get('active_job_count'):
            labels={'queued':'sırada','running':'çalışıyor'}
            parts.append('Panel görev kaydında: '+'; '.join(f"{item['title']}, {labels[item['recorded_status']]}" for item in panel['active_jobs'])+'.')
            parts.append('Bu kayıt, işin tamamlandığını doğrulamaz.')
    else:parts.append('Panelin yapılacak iş listesine şu anda erişemiyorum.')
    count=marketing.get('total_records')
    if marketing.get('known') is True and type(count) is int and count>=0:
        parts.append(f'Windows aday defterinde kayıtlı toplam {count} aday var.' if count else 'Windows aday defterinde kayıtlı aday görünmüyor; bu şirketin hiç işi olmadığı anlamına gelmez.')
        for item in marketing.get('items',[])[:3]:
            stage=item.get('stage');parts.append(f"{item.get('company_name') or 'İsimsiz aday'} (kayıtlı aşama: {stage or 'bilinmiyor'}): {candidate_next_step(stage)}.")
        parts.append('Bu kayıtlar aktif icra işi değildir; ihtiyaç, satın alma niyeti ve sonuç doğrulanmadı. Kayıtlı aşama yeni gönderim onayı değildir.')
        if marketing.get('complete_list') is not True:
            parts.append(f"Yalnız bu sayfada {marketing.get('candidate_count')} kayıt okundu; liste kısmidir ve eksik gözlemler bilinmiyor.")
    else:parts.append('Windows aday defterine şu anda erişemiyorum; aday yok diyemem.')
    if plan.get('known') is True and (panel.get('known') is not True or not panel.get('actionable_count')):
        parts.append('Jarvis planının güncel üst kaydında sıradaki adım: '+plan['next_step'])
    elif panel.get('known') is not True or not panel.get('actionable_count'):
        parts.append('Jarvis planının güncel üst kaydını da okuyamadım; sana genel olarak iş yok diyemem.')
    return ' '.join(parts)


def read_radar(store):
    """Read saved news/results only. Never start or retry a scan."""
    data = {'known': False, 'observed_at': time.time(), 'read_only': True}
    try:
        with closing(sqlite3.connect(Path(store.path).resolve().as_uri() + '?mode=ro', uri=True, timeout=1)) as db:
            db.row_factory = sqlite3.Row
            db.execute('PRAGMA query_only=ON')
            db.execute('BEGIN')
            row = db.execute("SELECT status,finished_at,result FROM jobs WHERE kind='radar' ORDER BY created_at DESC,rowid DESC LIMIT 1").fetchone()
            latest = {'known': row is not None}
            if row:
                latest.update(recorded_status=row['status'], finished_at=row['finished_at'], result_known=False)
                if row['status'] == 'done':
                    try:
                        result = json.loads(row['result'] or 'null')
                        fields = ('news', 'opps', 'sources_ok', 'sources_down')
                        if isinstance(result, dict) and all(type(result.get(k)) is int and result[k] >= 0 for k in fields) and row['finished_at']:
                            latest.update(result_known=True, counts={k: result[k] for k in fields})
                    except (ValueError, TypeError):
                        pass
            rows = db.execute('SELECT title,why,src,published_at FROM news WHERE published_at>? ORDER BY IFNULL(stars,0) DESC,published_at DESC LIMIT 3', (time.time() - 72 * 3600,)).fetchall()
            data.update(known=True, last_scan=latest, news=[{'title': clip(r['title'], 140), 'why': clip(r['why'], 180), 'source': clip(r['src'], 60), 'published_at': r['published_at']} for r in rows],
                        news_scope='saved_panel_news_last_72h_existing_rank', new_scan_started=False)
    except Exception as exc:
        data['failure_class'] = type(exc).__name__
    return data


def render_radar(data):
    if not data['known']:
        return 'Kayıtlı haber ve tarama sonuçlarına şu anda erişemiyorum. Yeni tarama başlatmadım; sonuç yok diyemem.'
    scan = data['last_scan']
    parts = ['Mevcut haber kayıtlarını okuyorum; yeni tarama başlatmadım.']
    if not scan['known']:
        parts.append('Kayıtlı bir haber taraması bulunamadı.')
    elif scan['recorded_status'] == 'done' and scan['result_known']:
        c = scan['counts']
        parts.append(f"Son tarama kaydında tamamlandı: {c['news']} haber, {c['opps']} fırsat eklendi. {c['sources_ok']} kaynak okundu; {c['sources_down']} kaynağa erişilemedi.")
        if data['observed_at'] - scan['finished_at'] > 3 * 3600:
            parts.append('Bu tarama üç saatten eski; şu an yapılmış tarama gibi sunmuyorum.')
    elif scan['recorded_status'] in ('queued', 'running'):
        parts.append('Son tarama kayıtta hâlâ sürüyor; bitmiş saymıyorum. Aşağıdaki haberler daha önce kaydedilenlerden.')
    elif scan['recorded_status'] == 'done':
        parts.append('Son tarama tamamlandı diye işaretli ama sonuç sayıları doğrulanamadı.')
    else:
        parts.append('Son tarama kaydı başarılı tamamlanma göstermiyor.')
    if data['news']:
        parts.append('Panelde son yetmiş iki saatte kaydedilmiş öne çıkan haberler:')
        parts.extend(item['title'] + (': ' + item['why'] if item['why'] else '') + '.' for item in data['news'])
    else:
        parts.append('Panelde son yetmiş iki saat kapsamında haber kaydı görünmüyor; bu dünyada yeni haber yok demek değildir.')
    return ' '.join(parts)
