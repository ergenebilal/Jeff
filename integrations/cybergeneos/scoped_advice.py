"""Staged, one-question advisory envelope; no inference, actions or persistence.

The future transport must supply fresh authenticated owner confirmation. A
cached candidate, owner flag, chat classification or model cannot supply it.
"""
from copy import deepcopy
import math,time
from .owner_lesson import recheck_owner_lesson,source_record

def result(status):
    return dict(status=status,packet=None,prepared_only=True,provider_called=False,
        rule_applied=False,permanent_memory_write_authorized=False,
        execution_authorized=False,reexecution_authorized=False,
        customer_contact_authorized=False,general_rule_inferred=False,
        semantic_quality_verified=False)

def prepare_scoped_advice(candidate, *, platform,session_id,sender_id='',
                         task_id,source,confirmed_owner_correction,user_question,
                         owner_check,decision_read,memory_read,redact,excerpt_read,
                         clock=time.time,mode='explicit_task_advice'):
    """Fresh bindings and exact excerpt. Transport consumption is a later gate."""
    identity=(platform,session_id,sender_id)
    def require_owner():
        if owner_check(*identity) is not True:
            raise PermissionError()
    def guarded(callback):
        def call(*args):
            require_owner();value=callback(*args);require_owner();return value
        return call
    def now():
        value=clock()
        if type(value) not in (int,float) or not math.isfinite(value) or value<=0:
            raise ValueError()
        return value
    try:
        require_owner()
        if mode!='explicit_task_advice':return result('explicit_advice_required')
        if (not isinstance(user_question,str) or not 1<=len(user_question.strip())<=1200
                or any(ord(c)<32 for c in user_question)
                or user_question.lstrip().startswith(('{','['))):
            return result('invalid_question')
        if (not isinstance(confirmed_owner_correction,str) or not 1<=len(confirmed_owner_correction)<=600
                or any(ord(c)<32 for c in confirmed_owner_correction)
                or not isinstance(task_id,str) or not isinstance(source,str)):
            return result('invalid_confirmation')
        question=user_question.strip();safe,count=guarded(redact)(question)
        if safe!=question or type(count) is not int or count!=0:
            return result('private_content_blocked')
        # Caller supplies the fresh literal confirmation, not the cached text.
        message='Düzeltme: '+confirmed_owner_correction+'\ngörev:'+task_id+'\nkaynak:'+source
        checked=recheck_owner_lesson(candidate,platform=platform,session_id=session_id,sender_id=sender_id,
            user_message=message,scope='this_task_only',owner_check=owner_check,
            decision_read=guarded(decision_read),memory_read=guarded(memory_read),
            redact=guarded(redact),clock=clock)
        if checked.get('status') not in ('bindings_still_match','requires_source_review'):
            return result(checked.get('status','unavailable'))
        current=checked['candidate'];started=now()
        memory=guarded(memory_read)(source);record,review=source_record(memory,source)
        if record['source_sha256']!=current['source_sha256']:
            return result('source_changed')
        text=record.get('text')
        if not isinstance(text,str) or not text:return result('source_excerpt_unavailable')
        window=guarded(excerpt_read)(text,question+' '+confirmed_owner_correction)
        if not isinstance(window,dict):return result('source_excerpt_unavailable')
        begin,end=window.get('excerpt_start_char'),window.get('excerpt_end_char');excerpt=window.get('text')
        if (type(begin) is not int or type(end) is not int or not 0<=begin<end<=len(text)
                or not isinstance(excerpt,str) or not 1<=len(excerpt)<=650 or text[begin:end]!=excerpt):
            return result('source_excerpt_unbound')
        original_excerpt=excerpt;excerpt,count=guarded(redact)(excerpt)
        if (not isinstance(excerpt,str) or not 1<=len(excerpt)<=1000 or not excerpt.strip()
                or type(count) is not int or count<0 or count==0 and excerpt!=original_excerpt):
            return result('source_excerpt_unavailable')
        ended=now();observed=memory.get('observed_at')
        if (type(observed) not in (int,float) or not math.isfinite(observed)
                or not 0<observed<=ended or ended-observed>60 or ended-started>60
                or ended<started or ended-current['observed_at']>60):
            return result('evidence_expired')
        require_owner()
        packet=dict(trusted_user_request=(question+'\nBu seçili özel taslak için açık düzeltmem: '
            +confirmed_owner_correction+'\nYalnız bu iş için değerlendirme istiyorum; iş çalıştırma veya kalıcı hafızaya yazma.'),
            untrusted_panel_data=dict(scoped_advice=dict(
                scope='this_task_only',candidate_id=current['candidate_id'],
                task_binding=deepcopy(current['task_binding']),current_task_outcome=current['current_task_outcome'],
                execution_state=current['execution_state'],source=source,source_sha256=current['source_sha256'],
                source_date=deepcopy(record['declared_date']),source_review_required=review or current['source_review_required'],
                source_excerpt=excerpt,source_excerpt_redacted=count>0,excerpt_start_char=begin,excerpt_end_char=end,
                task_derived_from_source_verified=False,source_statement_truth_verified=False,
                general_rule_applied=False,permanent_memory_written=False,
                execution_outcome_verified=False,customer_delivery_verified=False,
                observed_at=ended,context_use='one_explicit_advisory_question')))
        out=result('advice_prepared_with_source_review' if review or current['source_review_required'] else 'advice_prepared')
        out['packet']=packet;return out
    except PermissionError:return result('not_owner')
    except Exception:return result('unavailable')
