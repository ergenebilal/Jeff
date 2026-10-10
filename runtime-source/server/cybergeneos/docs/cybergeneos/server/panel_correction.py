"""Owner-only panel workflow adapter. No model routing or business operations.

The caller selects an existing supported task and a verified knowledge source.
Their relationship is an explicit owner choice, never inferred from page data.
Dependencies use existing actual readers; this adapter is staged, not installed.
"""
from contextvars import ContextVar
import hashlib
from http.cookies import SimpleCookie
from urllib.parse import urlsplit

from .correction_context import CorrectionContext
from .advice_gate import SingleUseAdvice
from .advice_dispatch import dispatch


def patch_app(source):
    addition='    from .panel_correction import install as install_panel_correction\n    install_panel_correction(sys.modules[__name__])\n'
    anchor='    install_opportunity_context(sys.modules[__name__])\n'
    if addition in source:
        return source
    if source.count(anchor) != 1:
        raise ValueError('Changed install boundary')
    return source.replace(anchor,anchor+addition)


def install(app, *, decision_read=None, memory_read=None, redact=None, clock=None, choices_read=None, excerpt_read=None, invoke=None):
    """Dependencies supplied by supported installation; no caller credentials.

    The authenticated HTTP boundary below provides current owner identity. It is
    not based on a body field or a boolean returned by a cached proposal.
    """
    if getattr(app,'_panel_correction_installed',False):
        return app._panel_correction_workflow
    if (not callable(getattr(getattr(app,'H',None),'route',None))
            or not callable(getattr(app,'valid_token',None))):
        raise ValueError('Verified owner HTTP boundary required')
    if invoke is None:
        from .worker_invoke import invoke
    if excerpt_read is None:
        from .correction_readers import production_excerpt_reader
        excerpt_read=production_excerpt_reader()
    if all(dep is None for dep in (decision_read,memory_read,redact,choices_read)):
        from .correction_readers import production_dependencies
        decision_read,memory_read,redact,choices_read=production_dependencies(app)
    elif any(dep is None for dep in (decision_read,memory_read,redact)):
        raise ValueError('Verified installation dependencies required')
    current=ContextVar('authenticated_panel_correction_channel',default=None)
    def owner_check(platform,session_id,sender_id):
        active=current.get()
        return (active is not None and active[0] == (platform,session_id,sender_id)
                and app.valid_token(active[1]) is True)
    def require_current():
        active=current.get()
        if active is None or app.valid_token(active[1]) is not True:
            raise ValueError('Owner session unavailable')
    def guarded(reader):
        def call(*args,**kwargs):
            require_current()
            result=reader(*args,**kwargs)
            require_current()
            return result
        return call
    dependencies=dict(owner_check=owner_check,decision_read=guarded(decision_read),memory_read=guarded(memory_read),redact=guarded(redact))
    if clock is not None:
        dependencies['clock']=clock
    workflow=CorrectionContext(**dependencies)
    workflow=SingleUseAdvice(workflow,excerpt_read=guarded(excerpt_read),**({"clock":clock} if clock is not None else {}))
    original=app.H.route
    def route(handler,parts,body):
        if parts[:2] != ['api','correction']:
            return original(handler,parts,body)
        # This private operation always requires a signed owner browser session,
        # including when the base panel permits anonymous localhost access.
        if handler.command != 'POST' or handler.by != 'bilal' or not handler._authed():
            return 403, {'error':'sahip_gerekiyor'}
        try:
            origin=urlsplit(handler.headers.get('Origin',''))
            host=handler.headers.get('Host','').lower()
            if (origin.scheme != ('https' if handler._https() else 'http')
                    or origin.netloc.lower()!=host or origin.path not in ('','/')
                    or origin.query or origin.fragment or origin.username or origin.password):
                return 403, {'error':'kaynak'}
            raw_cookie=handler.headers.get('Cookie','')
            if sum(p.strip().partition('=')[0]=='cgos' for p in raw_cookie.split(';')) != 1:
                return 403, {'error':'sahip_gerekiyor'}
            cookie=SimpleCookie(raw_cookie)
            if 'cgos' not in cookie or app.valid_token(cookie['cgos'].value) is not True:
                return 403, {'error':'sahip_gerekiyor'}
            owner=hashlib.sha256(cookie['cgos'].value.encode()).hexdigest()
            contracts={'select':{'task_id','source'},'correct':{'context_ticket','user_message'},'close':set(),'choices':{'query','offset'},'advice-issue':{'context_ticket','confirmed_owner_correction','user_question','requested_task_id','source','explicit_scope'},'advice-answer':{'advice_ticket','requested_task_id','source'}}
            if len(parts)!=3 or parts[2] not in contracts:
                return 404, {'error':'yok'}
            if not isinstance(body,dict) or set(body)!=contracts[parts[2]]:
                return 400, {'error':'gecersiz'}
            channel=dict(platform='panel',session_id=owner,sender_id='')
            token=current.set((('panel',owner,''),cookie['cgos'].value))
            try:
                if parts[2]=='choices':
                    if (not isinstance(body['query'],str) or not 1<=len(body['query'].strip())<=2000
                            or type(body['offset']) is not int or not 0<=body['offset']<=100000):
                        return 400, {'error':'gecersiz'}
                    if choices_read is None:
                        return 503, {'error':'secim_okuyucusu_yok'}
                    result=guarded(choices_read)(body['query'],body['offset'])
                else:
                    if parts[2]=='advice-answer':
                        result=dispatch(workflow.consume(**channel,**body),invoke=invoke,redact=guarded(redact))
                    else:
                        method={'select':workflow.select,'correct':workflow.correct,'close':workflow.close,'advice-issue':workflow.issue}[parts[2]]
                        result=method(**channel,**body)
            finally:
                current.reset(token)
            # Ticket exists only in this private response and is never forwarded
            # to a model, customer-facing text, telemetry or permanent memory.
            return 200,result
        except Exception:
            return 502, {'error':'duzeltme_baglantisi_kurulamadi'}
    app.H.route=route
    app._panel_correction_workflow=workflow
    app._panel_correction_installed=True
    return workflow
