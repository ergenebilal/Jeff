"""Staged ephemeral one-use handoff. No provider, execution or storage."""
from copy import deepcopy
import math,secrets,threading,time
from .scoped_advice import prepare_scoped_advice

def reply(status):
    return dict(status=status,packet=None,provider_called=False,
        execution_authorized=False,reexecution_authorized=False,
        permanent_memory_write_authorized=False,customer_contact_authorized=False)

class SingleUseAdvice:
    def __init__(self,workflow,*,excerpt_read,clock=time.time,ttl=30,capacity=256):
        if type(ttl) is not int or not 1<=ttl<=60 or type(capacity) is not int or not 1<=capacity<=256:
            raise ValueError('bounded ephemeral state required')
        self.workflow=workflow;self.excerpt_read=excerpt_read;self.clock=clock
        self.ttl=ttl;self.capacity=capacity;self._states={};self._lock=threading.RLock()
    def _key(self,channel):
        if not {'platform','session_id'}<=set(channel) or set(channel)-{'platform','session_id','sender_id'}:
            raise ValueError('transport channel only')
        key=(channel.get('platform'),channel.get('session_id'),channel.get('sender_id',''))
        if not all(type(s) is str for s in key) or not key[1]:raise ValueError()
        if self.workflow.owner_check(*key) is not True:raise PermissionError()
        return key
    def _now(self):
        now=self.clock()
        if type(now) not in (int,float) or not math.isfinite(now) or now<=0:raise ValueError()
        return now
    def _purge(self,now):
        for key,value in list(self._states.items()):
            if not value['created']<=now<value['expires']:self._states.pop(key)
    def _active(self,key,state,epoch):
        try:
            if self.workflow.owner_check(*key) is not True:return False
            with self._lock:
                now=self._now()
                active=(self._states.get(key) is state and state['epoch']==epoch
                        and state['created']<=now<state['expires'])
            return active and self.workflow.owner_check(*key) is True
        except Exception:return False
    def _prepare(self,candidate,key,literal,question,task,source,state,epoch):
        return prepare_scoped_advice(candidate,platform=key[0],session_id=key[1],sender_id=key[2],
            confirmed_owner_correction=literal,user_question=question,task_id=task,source=source,
            owner_check=lambda *identity:identity==key and self._active(key,state,epoch),decision_read=self.workflow.decision_read,
            memory_read=self.workflow.memory_read,redact=self.workflow.redact,
            excerpt_read=self.excerpt_read,clock=self.clock)
    def select(self,*,task_id,source,**channel):
        try:
            key=self._key(channel)
            with self._lock:
                self._states.pop(key,None);now=self._now();self._purge(now)
                if len(self._states)>=self.capacity:return reply('context_capacity_reached')
                state=dict(epoch=0,created=now,expires=now+300,selection=None,candidate=None,grant=None)
                self._states[key]=state
            value=self.workflow.select(**channel,task_id=task_id,source=source)
            with self._lock:
                if self._states.get(key) is not state:return reply('context_changed')
                self._key(channel)
                if value.get('context_ticket'):state['selection']=value['context_ticket']
                else:self._states.pop(key,None)
            return value
        except PermissionError:return reply('not_owner')
        except Exception:return reply('unavailable')
    def close(self,**channel):
        try:
            key=self._key(channel)
            with self._lock:self._states.pop(key,None)
            return self.workflow.close(**channel)
        except PermissionError:return reply('not_owner')
        except Exception:return reply('unavailable')
    def correct(self,*,context_ticket,user_message,**channel):
        try:
            key=self._key(channel)
            with self._lock:
                self._purge(self._now());state=self._states.get(key)
                if not state or type(context_ticket) is not str or not secrets.compare_digest(context_ticket,state['selection'] or ''):
                    return reply('context_missing_or_changed')
                state['epoch']+=1;epoch=state['epoch'];state['candidate']=None;state['grant']=None
            value=self.workflow.correct(**channel,context_ticket=context_ticket,user_message=user_message)
            with self._lock:
                if self._states.get(key) is not state or state['epoch']!=epoch:return reply('context_changed')
                self._key(channel)
                if value.get('candidate'):state['candidate']=deepcopy(value['candidate'])
            return value
        except PermissionError:return reply('not_owner')
        except Exception:return reply('unavailable')
    def issue(self,*,context_ticket,confirmed_owner_correction,user_question,
              requested_task_id,source,explicit_scope,**channel):
        try:
            key=self._key(channel)
            with self._lock:
                self._purge(self._now());state=self._states.get(key)
                if not state or type(context_ticket) is not str or not secrets.compare_digest(context_ticket,state['selection'] or ''):
                    return reply('context_missing_or_changed')
                state['epoch']+=1;epoch=state['epoch'];state['grant']=None
                candidate=deepcopy(state['candidate'])
                if candidate is None:return reply('fresh_correction_required')
                if explicit_scope!='selected_task_only':return reply('explicit_selected_task_required')
                if requested_task_id!=candidate['task_binding']['request_id'] or source!=candidate['source']:
                    return reply('other_task_or_source_requires_new_selection')
            prepared=self._prepare(candidate,key,confirmed_owner_correction,user_question,requested_task_id,source,state,epoch)
            if prepared.get('packet') is None:return prepared
            with self._lock:
                now=self._now();self._purge(now);self._key(channel)
                if self._states.get(key) is not state or state['epoch']!=epoch:return reply('context_changed')
                ticket=secrets.token_urlsafe(32)
                state['grant']=dict(ticket=ticket,created=now,expires=now+self.ttl,candidate=candidate,
                    literal=confirmed_owner_correction,question=user_question,task=requested_task_id,source=source)
            value=reply('one_use_advice_ready');value.update(advice_ticket=ticket,expires_in=self.ttl)
            return value
        except PermissionError:return reply('not_owner')
        except Exception:return reply('unavailable')
    def consume(self,*,advice_ticket,requested_task_id,source,**channel):
        """Atomic consume BEFORE evidence read. Failed read never makes it reusable.

        The eventual dispatcher still requires a fresh authenticated channel and
        a read-only model path. This prepared handoff does not implement those.
        """
        try:
            key=self._key(channel)
            with self._lock:
                now=self._now();self._purge(now);state=self._states.get(key)
                grant=state.get('grant') if state else None
                if not grant or type(advice_ticket) is not str or not secrets.compare_digest(advice_ticket,grant['ticket']):
                    return reply('advice_missing_or_consumed')
                state['grant']=None;state['epoch']+=1;epoch=state['epoch']
                if not grant['created']<=now<grant['expires']:return reply('advice_expired')
                if requested_task_id!=grant['task'] or source!=grant['source']:
                    return reply('other_task_or_source_requires_new_selection')
            prepared=self._prepare(grant['candidate'],key,grant['literal'],grant['question'],grant['task'],grant['source'],state,epoch)
            with self._lock:
                self._purge(self._now());self._key(channel)
                if self._states.get(key) is not state or state['epoch']!=epoch:return reply('context_changed')
            if prepared.get('packet') is not None:
                prepared.update(transport_consumed=True,read_only_advice_only=True,
                    _dispatch_current=lambda:self._active(key,state,epoch),
                    _dispatch_revalidate=lambda:self._prepare(grant['candidate'],key,grant['literal'],grant['question'],grant['task'],grant['source'],state,epoch))
            return prepared
        except PermissionError:return reply('not_owner')
        except Exception:return reply('unavailable')
