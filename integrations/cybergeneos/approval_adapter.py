"""Infrastructure adapter for the existing panel; never sends a draft."""
import json
from pathlib import Path
import time
try:
    from .pablo_approval_client import ApprovalClient,ApprovalUnavailable,review_binding
except ImportError:
    from pablo_approval_client import ApprovalClient,ApprovalUnavailable,review_binding

class PanelApprovalAdapter:
    def __init__(self,store,client,owner,clock=time.time):
        self.store=store;self.client=client;self.owner=str(owner);self.clock=clock
        store.x('CREATE TABLE IF NOT EXISTS canonical_approval_links (local_id TEXT PRIMARY KEY, canonical_id TEXT, expires_at REAL NOT NULL, archived_at REAL, reason TEXT)')

    def register(self,aid):
        row=self.store.approval(aid)
        created=float(row['created_at']); expiry=created+172800
        try:
            record=self.client.request('panel',aid,review_binding('panel',aid,row),expiry,created)
            canonical_id=record['approval_id']; reason=record['status']
        except ApprovalUnavailable:
            canonical_id=None;reason='needs_revalidation'
        archived=self.clock() if expiry<=self.clock() or reason!='pending' else None
        self.store.x('INSERT OR REPLACE INTO canonical_approval_links VALUES(?,?,?,?,?)',(aid,canonical_id,expiry,archived,reason))
        if archived or not canonical_id:
            self.store.x("UPDATE approvals SET status='Yeniden doğrulama gerekiyor' WHERE id=?",(aid,))
        return aid

    def begin(self,aid,action,body,actor):
        if actor!='bilal': raise ApprovalUnavailable('Authenticated owner required')
        row=self.store.approval(aid)
        link=self.store.one('SELECT * FROM canonical_approval_links WHERE local_id=?',(aid,))
        if not row or not link or not link['canonical_id']: raise ApprovalUnavailable('Legacy approval requires revalidation')
        if self.clock()>=link['expires_at']: raise ApprovalUnavailable('Expired approval')
        if action=='edit':
            if row['status']!='Bekliyor':raise ApprovalUnavailable('Only pending draft can be edited')
            return None
        binding=review_binding('panel',aid,row)
        if action=='sent':
            record=self.client.call('GET','/decisions/'+link['canonical_id'])
            if row['status']!='Onaylandı' or record['status']!='consumed' or json.loads(record['binding_json'])!=binding:
                raise ApprovalUnavailable('Unreviewed or changed draft')
            return None
        if action not in ('approve','reject') or row['status']!='Bekliyor':raise ApprovalUnavailable('Not pending')
        self.client.decide(link['canonical_id'],binding,self.owner,self.owner,action=='approve')
        if action=='approve':
            claim=self.client.claim(link['canonical_id'],binding,'panel-review')
            return (link['canonical_id'],claim['claim_id'])

    def finish(self,aid,action,claim,result):
        if action=='edit':self.register(aid)
        if claim:
            try:self.client.complete(claim[0],claim[1],'panel-review','draft_review_only' if result[0]==200 else 'review_failed')
            except ApprovalUnavailable:result[1]['approval_reconciliation']='required'

    def decay(self):
        now=self.clock()
        for row in self.store.q("SELECT id,created_at FROM approvals WHERE status='Bekliyor' AND id NOT IN (SELECT local_id FROM canonical_approval_links)"):
            expiry=float(row['created_at'])+172800
            reason='expired' if expiry<=now else 'needs_revalidation'
            self.store.x('INSERT INTO canonical_approval_links VALUES(?,?,?,?,?)',(row['id'],None,expiry,now,reason))
            self.store.x("UPDATE approvals SET status=? WHERE id=?",('Süresi doldu' if reason=='expired' else 'Yeniden doğrulama gerekiyor',row['id']))
        self.store.x("UPDATE approvals SET status='Süresi doldu' WHERE status='Bekliyor' AND id IN (SELECT local_id FROM canonical_approval_links WHERE expires_at<=?)",(now,))
        self.store.x('UPDATE canonical_approval_links SET archived_at=?,reason=? WHERE expires_at<=? AND archived_at IS NULL',(now,'expired',now))

def install(app,client=None,owner=None):
    store=app.store
    if client is None:
        config=json.loads((Path(app.DATA)/'approval-gateway.json').read_text())
        client=ApprovalClient(config);owner=config['owner_id']
    adapter=PanelApprovalAdapter(store,client,owner)
    original_create=store.create_approval;original_list=store.approvals;original_act=app.act_approval
    def create(a):return adapter.register(original_create(a))
    def listing():adapter.decay();return original_list()
    def act(aid,action,body,actor=None):
        try:claim=adapter.begin(aid,action,body,actor)
        except ApprovalUnavailable:return (409,{'ok':False,'error':'approval_revalidation_required'})
        result=original_act(aid,action,body)
        adapter.finish(aid,action,claim,result)
        return result
    store.create_approval=create;store.approvals=listing;app.act_approval=act
    return adapter
