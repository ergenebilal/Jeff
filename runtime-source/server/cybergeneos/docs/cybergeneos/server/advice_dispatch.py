"""One read-only reply; strict fields and fresh basis. No retries or actions."""
from copy import deepcopy
import json
import threading
_provider_slot=threading.BoundedSemaphore(1)

FIELDS=('answer_scope','task_outcome','source_current_truth_verified','permanent_rule_saved',
        'permanent_memory_write_authorized','execution_authorized','reexecution_authorized','customer_delivery_verified')

def expected_fields(packet):
    frame=packet['untrusted_panel_data']['scoped_advice']
    if frame['scope']!='this_task_only' or not isinstance(frame['current_task_outcome'],str):raise ValueError()
    return dict(answer_scope='selected_task_only',task_outcome=frame['current_task_outcome'],
        **{key:False for key in FIELDS[2:]})

def parse_answer(text,expected):
    def pairs(items):
        data={}
        for key,value in items:
            if key in data:raise ValueError()
            data[key]=value
        return data
    def invalid(value):raise ValueError()
    data=json.loads(text,object_pairs_hook=pairs,parse_constant=invalid)
    if type(data) is dict and set(data)=={'reply_field_observations','rationale'}:
        fields=data['reply_field_observations']
        if type(fields) is not dict or set(fields)!=set(expected):raise ValueError()
        data=fields|{'rationale':data['rationale']}
    if type(data) is not dict or set(data)!=set(expected)|{'rationale'}:raise ValueError()
    if any(type(data.get(k)) is not type(v) or data[k]!=v for k,v in expected.items()):raise ValueError()
    rationale=data['rationale']
    if type(rationale) is not str or not 1<=len(rationale.strip())<=1800 or any(ord(c)<32 for c in rationale):raise ValueError()
    return data

def basis(packet):
    data=deepcopy(packet)
    data['untrusted_panel_data']['scoped_advice'].pop('observed_at',None)
    return data

def dispatch(prepared,*,invoke,redact):
    """Caller passes private consume result; callbacks never come from HTTP body."""
    out=dict(status='advice_unavailable',reply=None,provider_called=False,model_completion_verified=False,
        execution_authorized=False,reexecution_authorized=False,permanent_memory_written=False,
        customer_contact_authorized=False,semantic_quality_verified=False)
    current=prepared.pop('_dispatch_current',None);revalidate=prepared.pop('_dispatch_revalidate',None)
    try:
        packet=prepared.get('packet')
        if prepared.get('transport_consumed') is not True or not callable(current) or not callable(revalidate) or current() is not True:
            out['status']='context_missing_or_changed';return out
        expected=expected_fields(packet)
        if current() is not True:out['status']='not_owner';return out
        if not _provider_slot.acquire(blocking=False):out['status']='provider_busy';return out
        try:
            if current() is not True:out['status']='context_changed_before_provider';return out
            out['invocation_started']=True;out['provider_called']=None
            response=invoke(deepcopy(packet),expected=deepcopy(expected))
        finally:_provider_slot.release()
        attempts=response.get('provider_request_attempts') if type(response) is dict else None
        if type(attempts) is int and attempts in (0,1):out['provider_called']=attempts==1
        if current() is not True:out['status']='context_changed_after_reply';return out
        if type(response) is not dict or response.get('status')!='completed':
            out['status']='provider_unavailable';return out
        if response.get('requested_tool_calls')!=0 or response.get('finish_reason') not in ('stop','end_turn'):
            out['status']='provider_reply_incomplete';return out
        data=parse_answer(response.get('raw_answer'),expected)
        safe,count=redact(data['rationale'])
        if type(count) is not int or count!=0 or safe!=data['rationale']:
            out['status']='private_reply_blocked';return out
        if current() is not True:out['status']='context_changed_after_reply';return out
        fresh=revalidate()
        if fresh.get('packet') is None or basis(fresh['packet'])!=basis(packet) or current() is not True:
            out['status']='evidence_changed_after_reply';return out
        frame=packet['untrusted_panel_data']['scoped_advice']
        outcome=frame['current_task_outcome']
        fact=('Taslak, son kontrolde ilk isteğin ölçütleriyle eşleşti; bu, işin dışarıda tamamlandığı anlamına gelmez.'
              if outcome=='matched_at_observation' else 'Taslak, son kontrolde ilk isteğin ölçütleriyle eşleşmedi.'
              if outcome=='mismatch' else 'Bu taslağın sonucu doğrulanamadı.')
        facts=[fact,'Kaynağın güncelliği yeniden incelenmeli.' if frame['source_review_required'] else
               'Kaynak seçimi korunuyor; içeriğin doğruluğu ayrıca kanıtlanmadı.']
        if current() is not True:out['status']='context_changed_after_reply';return out
        out.update(status='advice_reply_ready',reply=data['rationale'].strip(),verified_facts=facts,
                   model_completion_verified=True,structured_claims_checked=True)
        return out
    except (ValueError,TypeError,KeyError):out['status']='provider_reply_rejected';return out
    except Exception:out['status']='advice_unavailable';return out
