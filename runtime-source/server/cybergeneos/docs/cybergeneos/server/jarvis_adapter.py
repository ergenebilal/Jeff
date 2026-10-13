"""Only infrastructure status and fast owner agenda. Business workflows and approvals are untouched."""
from contextlib import closing
from pathlib import Path
import json
import sqlite3
import sys
import hashlib
import math
import time
from contextvars import ContextVar
from http.cookies import SimpleCookie
from threading import RLock
from copy import deepcopy

TRUTH_RULES = (' Güncel altyapı/onay/Pablo durumu için untrusted_panel_data içindeki jarvis_snapshot kaydını kullan. '
               'known false veya kısmi listeyi başarı sayma. Onay ve iş sonucu ayrıdır. Güncel kaydın yoksa tahmin etme. '
               'Ses, aynı panel yanıtının okunmasıdır; Telegram ile ayrı sohbet geçmişi kullanabilir, ortak altyapı kaydı aynıdır.')
STATUS_REQUESTS = {'/durum', 'jarvis durumu', 'altyapı durumu', 'pablo ve onay durumu'}
AGENDA_REQUESTS = {
    '/gundem', '/gündem', 'gündem', 'gündem nedir', 'gündem durumu', 'gündem özeti',
    'ne iş var', 'ne iş var jeff', 'jeff ne iş var', 'bugün ne var', 'işler nedir',
    'iş listesi', 'yapılacaklar', 'sıradaki işler', 'sıradaki adımlar'
}


def patch(source):
    marker = '    install_approval_adapter(sys.modules[__name__])\n'
    if 'install_jarvis_adapter(sys.modules[__name__])' in source:
        return source
    if source.count(marker) != 1:
        raise ValueError('Panel source anchor changed')
    return source.replace(marker, marker + '    from .jarvis_adapter import install as install_jarvis_adapter\n    install_jarvis_adapter(sys.modules[__name__])\n')


def patch_front(source):
    old = "D.jeff === 'hermes' ? 'Jeff çevrimiçi'"
    new = "D.jeff === 'hermes' ? 'Jeff bağlantısı ayarlı'"
    if new in source:
        return source
    if source.count(old) != 1:
        raise ValueError('Panel label anchor changed')
    source = source.replace(old, new)
    anchor = "  $('#sys').classList.toggle('off', state.error || D.jeff !== 'hermes');"
    if source.count(anchor) != 1:
        raise ValueError('Panel status anchor changed')
    return source.replace(anchor, anchor + "\n  $('#sys').title = D.jarvis?.work?.known && D.jarvis?.approvals?.known ? `${D.jarvis.work.open} açık iş; ${D.jarvis.approvals.pending} güncel onay` : 'Görev ve onay durumu okunamadı';")


def install(app, reader=None, renderer=None, agenda_reader=None, agenda_renderer=None):
    if getattr(app, '_jarvis_installed', False):return
    if reader is None:
        sys.path.insert(0, '/home/hermes/jeff_repo')
        from scripts.jarvis_snapshot import snapshot, render, read_work
        def panel_work():
            config=json.loads((Path(app.DATA)/'approval-gateway.json').read_text())
            key=config.get('auth_token')
            if not isinstance(key,str) or not key:raise ValueError('Panel work credential unavailable')
            return read_work(key=key)
        reader=lambda:snapshot(work_reader=panel_work)
        renderer=render
    from . import work_agenda
    if agenda_reader is None:
        def marketing():
            # Only this already-used private panel configuration; never helper/sudo/fallback.
            try:
                path=Path(app.DATA)/'approval-gateway.json'
                if path.is_symlink():raise ValueError('Credential source unavailable')
                with path.open('rb') as handle:raw=handle.read(16385)
                if len(raw)>16384:raise ValueError('Credential source exceeds bound')
                def unique(pairs):
                    result={}
                    for name,value in pairs:
                        if name in result:raise ValueError('Duplicate configuration field')
                        result[name]=value
                    return result
                def invalid(_):raise ValueError('Invalid configuration number')
                config=json.loads(raw.decode('utf-8'),object_pairs_hook=unique,parse_constant=invalid)
                key=config.get('auth_token') if isinstance(config,dict) else None
                return work_agenda.read_marketing_agenda(key=key)
            except Exception:return work_agenda.unknown_marketing('CredentialUnavailable')
        agenda_reader=lambda:work_agenda.read(app.store,app.briefing.steps,marketing_reader=marketing)
    if agenda_renderer is None:agenda_renderer=work_agenda.render
    state_original=app.build_state;context_original=app.briefing.jeff_context;reply_original=app.jeff.stream_reply
    stream_original=app.H.stream if callable(getattr(getattr(app,'H',None),'stream',None)) else None
    request_scope=ContextVar('owner_agenda_request',default=None)
    cache={};cache_lock=RLock();cache_epoch=[0]
    def normalize(text):
        return ' '.join(str(text).replace('İ','i').casefold().strip().rstrip('.!?').split())
    def unavailable():
        return {'observed_at':None,'read_only':True,'source_instruction_authority':'none',
                'panel':{'known':False},'marketing':work_agenda.unknown_marketing(),'plan':{'known':False}}
    def fresh_enough(data,now):
        stamp=data.get('marketing',{}).get('observed_at') if isinstance(data,dict) else None
        return (data.get('marketing',{}).get('known') is True and type(stamp) in (int,float)
                and math.isfinite(stamp) and stamp>0 and -5<=now-stamp<=30)
    def owner_cache_identity(handler):
        # A permissive localhost _authed() does not create a persistent private cache owner.
        try:
            raw=handler.headers.get('Cookie','')
            if sum(part.strip().partition('=')[0]=='cgos' for part in raw.split(';'))!=1:return None
            cookies=SimpleCookie(raw);value=cookies['cgos'].value
            if not callable(getattr(app,'valid_token',None)) or app.valid_token(value) is not True:return None
            return hashlib.sha256(value.encode()).hexdigest()
        except Exception:return None
    def snapshot_read():
        try:return reader()
        except Exception:return {'work':{'known':False},'approvals':{'known':False}}
    def current_agenda():
        active=request_scope.get()
        if active is None or active['owner_authorized'] is not True:return unavailable()
        with cache_lock:
            if active['cache_epoch']!=cache_epoch[0]:return unavailable()
        if active['agenda'] is not None:return active['agenda']
        identity=active['cache_identity'];now=time.time()
        if active['fresh_requested']:
            try:
                result=agenda_reader()
                if not isinstance(result,dict):raise ValueError('Invalid agenda reader output')
            except Exception:result=unavailable()
            result=deepcopy(result)
            result['context_observation']={'cached':False,'fresh_requested':True,
                'source_only':True,'current_truth_verified':False,'execution_authorized':False}
            with cache_lock:
                if active['cache_epoch']!=cache_epoch[0]:result=unavailable()
            if identity:
                with cache_lock:
                    if active['cache_epoch']!=cache_epoch[0]:
                        active['agenda']=unavailable();return active['agenda']
                    for key in [key for key,value in cache.items() if not fresh_enough(value,now)]:del cache[key]
                    if fresh_enough(result,time.time()) and len(cache)<64:cache[identity]=deepcopy(result)
                    else:cache.pop(identity,None)
        else:
            result=unavailable()
            if identity:
                with cache_lock:
                    cached=cache.get(identity)
                    if cached is not None and fresh_enough(cached,now):result=deepcopy(cached)
                    elif cached is not None:cache.pop(identity,None)
            result['context_observation']={'cached':result.get('marketing',{}).get('known') is True,
                'fresh_requested':False,'cache_max_age_seconds':30,'source_only':True,
                'current_truth_verified':False,'execution_authorized':False}
        active['agenda']=result
        return result
    def state():return {**state_original(),'jarvis':snapshot_read()}
    def context(store):
        base=context_original(store)
        return base+'\n\n'+json.dumps({'jarvis_snapshot':snapshot_read(),'work_agenda':current_agenda()},ensure_ascii=False,allow_nan=False)
    def reply(text,context):
        clean=normalize(text)
        if clean in STATUS_REQUESTS:yield renderer(snapshot_read())
        elif clean in AGENDA_REQUESTS:yield agenda_renderer(current_agenda())
        else:yield from reply_original(text,context)
    if stream_original is not None:
        def stream(handler,kind,body):
            if kind!='jeff':return stream_original(handler,kind,body)
            owner=handler.by=='bilal' and handler._authed() is True
            text=body.get('text','') if isinstance(body,dict) else ''
            with cache_lock:epoch=cache_epoch[0]
            active={'owner_authorized':owner,'cache_identity':owner_cache_identity(handler) if owner else None,
                    'fresh_requested':normalize(text) in AGENDA_REQUESTS,'agenda':None,'cache_epoch':epoch}
            marker=request_scope.set(active)
            try:return stream_original(handler,kind,body)
            finally:request_scope.reset(marker)
        app.H.stream=stream
    reset_original=getattr(app.jeff,'reset',None)
    if callable(reset_original):
        def reset(*args,**kwargs):
            with cache_lock:cache.clear();cache_epoch[0]+=1
            return reset_original(*args,**kwargs)
        app.jeff.reset=reset
    app.build_state=state;app.briefing.jeff_context=context;app.jeff.stream_reply=reply
    app._jarvis_panel_context=context_original;app._jarvis_snapshot=reader
    app._jarvis_agenda_reader=agenda_reader;app._jarvis_agenda_renderer=agenda_renderer
    app.jeff.VOICE_RULES+=TRUTH_RULES;app.jeff.FALLBACK_SYSTEM+=TRUTH_RULES
    app._jarvis_installed=True
