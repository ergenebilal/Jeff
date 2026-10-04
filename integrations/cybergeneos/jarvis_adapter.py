"""Only infrastructure status. Business workflows and approvals are untouched."""
import json
import sys
from pathlib import Path

TRUTH_RULES=(' Güncel altyapı/onay/Pablo durumu için untrusted_panel_data içindeki jarvis_snapshot kaydını kullan. '
             'known false veya kısmi listeyi başarı sayma. Onay ve iş sonucu ayrıdır. Güncel kaydın yoksa tahmin etme. '
             'Ses, aynı panel yanıtının okunmasıdır; Telegram ile ayrı sohbet geçmişi kullanabilir, ortak altyapı kaydı aynıdır.')
STATUS_REQUESTS={'/durum','jarvis durumu','altyapı durumu','pablo ve onay durumu'}


def patch(source):
    marker='    install_approval_adapter(sys.modules[__name__])\n'
    if 'install_jarvis_adapter(sys.modules[__name__])' in source:return source
    if source.count(marker)!=1:raise ValueError('Panel source anchor changed')
    return source.replace(marker,marker+'    from .jarvis_adapter import install as install_jarvis_adapter\n    install_jarvis_adapter(sys.modules[__name__])\n')


def patch_front(source):
    old="D.jeff === 'hermes' ? 'Jeff çevrimiçi'"
    new="D.jeff === 'hermes' ? 'Jeff bağlantısı ayarlı'"
    if new in source:return source
    if source.count(old)!=1:raise ValueError('Panel label anchor changed')
    source=source.replace(old,new)
    anchor="  $('#sys').classList.toggle('off', state.error || D.jeff !== 'hermes');"
    if source.count(anchor)!=1:raise ValueError('Panel status anchor changed')
    return source.replace(anchor,anchor+"\n  $('#sys').title = D.jarvis?.work?.known && D.jarvis?.approvals?.known ? `${D.jarvis.work.open} açık iş; ${D.jarvis.approvals.pending} güncel onay` : 'Görev ve onay durumu okunamadı';")


def install(app,reader=None,renderer=None):
    if getattr(app,'_jarvis_installed',False):return
    if reader is None:
        sys.path.insert(0,'/home/hermes/jeff_repo')
        from scripts.jarvis_snapshot import snapshot,render,read_work
        def panel_work():
            # The panel already has this agent credential; never needs sudo.
            config=json.loads((Path(app.DATA)/'approval-gateway.json').read_text())
            key=config.get('auth_token')
            if not isinstance(key,str) or not key:raise ValueError('Panel work credential unavailable')
            return read_work(key=key)
        reader=lambda:snapshot(work_reader=panel_work)
        renderer=render
    state_original=app.build_state;context_original=app.briefing.jeff_context;reply_original=app.jeff.stream_reply
    def state():return {**state_original(),'jarvis':reader()}
    def context(store):
        return context_original(store)+'\n\n'+json.dumps({'jarvis_snapshot':reader()},ensure_ascii=False)
    def reply(text,context):
        if text.strip().casefold() in STATUS_REQUESTS:
            yield renderer(reader())
        else:yield from reply_original(text,context)
    app.build_state=state;app.briefing.jeff_context=context;app.jeff.stream_reply=reply
    app.jeff.VOICE_RULES+=TRUTH_RULES;app.jeff.FALLBACK_SYSTEM+=TRUTH_RULES
    app._jarvis_installed=True
