"""Thin authenticated transport. No local fallback grants owner authority."""
import hashlib
import json
from pathlib import Path
import time
from urllib.request import Request,urlopen

class ApprovalUnavailable(Exception):
    pass

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def action_binding(request_id,action,params,input_digest):
    recipient=next((str(params[k]) for k in ('recipient','recipient_target','phone','target','window_title','path','url') if params.get(k)), 'local:'+action)
    return {'task_id':str(params.get('user_task_id') or request_id),'action':action,'recipient':recipient,
            'channel':str(params.get('channel') or 'windows'),'input_digest':input_digest}

def review_binding(source,source_id,row):
    if source=='marketing_campaign':
        content={k:row.get(k) for k in ('lead_id','company_name','website','channel','recipient_target','subject','message_body','value_prop')}
        recipient=str(row.get('recipient_target') or '')
        channel=str(row.get('channel') or '')
        if not row.get('message_body'): raise ApprovalUnavailable('Campaign content missing')
        action='draft_review'
    elif source=='marketing_idea':
        content={k:v for k,v in row.items() if k not in ('status','approval_requested_at','approved_at','approved_by','created_at','updated_at')}
        recipient='local:art_direction'; channel='instagram'; action='art_direction_review'
        if not row.get('caption_draft'): raise ApprovalUnavailable('Idea content missing')
    else:
        content={k:row.get(k) for k in ('lead_id','opp_id','channel','target','text')}
        recipient=str(row.get('target') or ''); channel=str(row.get('channel') or ''); action='draft_review'
        if not row.get('text'): raise ApprovalUnavailable('Panel content missing')
    if not recipient or not channel: raise ApprovalUnavailable('Recipient or channel missing')
    return {'task_id':str(row.get('task_id') or source+':'+str(source_id)),
            'action':action,'recipient':recipient,'channel':channel,'input_digest':digest(content)}

class ApprovalClient:
    def __init__(self,config,opener=urlopen,clock=time.time):
        self.config=dict(config); self.opener=opener; self.clock=clock

    def call(self,method,path,body=None,owner=False):
        key=self.config.get('approval_decision_key' if owner else 'auth_token')
        if not key: raise ApprovalUnavailable('Canonical approval credential unavailable')
        headers={'Content-Type':'application/json','X-Approval-Key' if owner else 'X-Bridge-Key':key}
        req=Request(self.config.get('jeff_bridge_api_url','http://100.80.122.74:7700').rstrip('/')+path,
                    data=json.dumps(body).encode() if body is not None else None,headers=headers,method=method)
        try:
            with self.opener(req,timeout=8) as response: return json.load(response)
        except Exception as exc:
            raise ApprovalUnavailable(type(exc).__name__) from None

    def request(self,source,source_id,binding,expires_at,created_at=None):
        return self.call('POST','/decisions/request',{'source':source,'source_id':str(source_id),'binding':binding,
                                                   'expires_at':expires_at,'created_at':created_at})

    def decide(self,aid,binding,user_id,chat_id,approve=True):
        record=self.call('GET','/decisions/'+aid)
        if json.loads(record['binding_json'])!=binding: raise ApprovalUnavailable('Immutable binding changed')
        expected_owner=str(user_id)
        if approve and record['status']=='approved' and record.get('owner_id')==expected_owner:
            return record
        return self.call('POST','/decisions/'+aid+'/decision',{'user_id':str(user_id),'chat_id':str(chat_id),
                        'input_digest':binding['input_digest'],'decision':'approve' if approve else 'reject'},owner=True)

    def claim(self,aid,binding,worker):
        return self.call('POST','/decisions/'+aid+'/claim',{'binding':binding,'worker':worker})

    def complete(self,aid,claim,worker,outcome):
        return self.call('POST','/decisions/'+aid+'/complete',{'claim_id':claim,'worker':worker,'outcome':outcome})

def from_node_config():
    return ApprovalClient(json.loads(Path(r'C:\CyberGene\HermesNode\config.json').read_text(encoding='utf-8')))
