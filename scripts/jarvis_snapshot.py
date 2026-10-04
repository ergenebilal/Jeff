"""One read-only source for Jarvis status in chat, panel and voice."""
import json
from pathlib import Path
import sqlite3
import time
from urllib.request import Request,urlopen


def read_work(key=None):
    if key is None:
        from scripts.pablo_dispatch import bridge_key
        key=bridge_key()
    if not key:raise RuntimeError('Work credential unavailable')
    with urlopen(Request('http://100.89.26.86:7788/work',headers={'X-Bridge-Key':key}),timeout=3) as response:
        return json.load(response)


def snapshot(bridge='/home/hermes/jeff2/bridge/bridge.db',work_reader=read_work,now=None):
    now=time.time() if now is None else now
    result={'version':1,'observed_at':now,'read_only':True,'atomic_across_sources':False}
    try:
        with sqlite3.connect(Path(bridge).resolve().as_uri()+'?mode=ro',uri=True) as db:
            rows=db.execute("SELECT approval_id,status,expires_at FROM approval_records WHERE status IN ('pending','approved','claimed') AND archived_at IS NULL ORDER BY created_at").fetchall()
        items=[{'id':rid,'status':status,'expires_at':expires,'expired':expires<=now} for rid,status,expires in rows]
        result['approvals']={'known':True,'source':'canonical_approval_ledger','items':items,
                             'pending':sum(i['status']=='pending' and not i['expired'] for i in items),
                             'expired_visible':sum(i['expired'] and i['status'] in ('pending','approved') for i in items)}
    except Exception as exc:result['approvals']={'known':False,'pending':None,'failure_class':type(exc).__name__}
    try:
        work=work_reader()
        if type(work.get('open_count')) is not int or work['open_count']<0 or not isinstance(work.get('items'),list):raise ValueError('Invalid work source')
        items=[]
        for item in work['items']:
            if not isinstance(item.get('request_id'),str) or not isinstance(item.get('status'),str):raise ValueError('Invalid work item')
            items.append({'id':item['request_id'],'status':item['status'],
                          'outcome_verified':item.get('outcome_verified') is True})
        result['work']={'known':True,'source':'pablo_durable_work','open':work['open_count'],'items':items,
                        'complete_list':work.get('next_offset') is None and len(items)==work['open_count'],
                        'automatic_replay':work.get('automatic_replay') is True}
    except Exception as exc:result['work']={'known':False,'open':None,'failure_class':type(exc).__name__}
    return result


def render(data):
    approvals=data['approvals'];work=data['work']
    onay=f"Karar bekleyen güncel onay {approvals['pending']}" if approvals['known'] else 'Onay durumu okunamadı'
    isler=f"Pablo’da {work['open']} açık iş var" if work['known'] else 'Pablo iş durumu okunamadı'
    if work['known']:
        uncertain=sum(i['status'] in ('OUTCOME_UNKNOWN','UNKNOWN','IN_PROGRESS','PENDING_VERIFICATION') and not i['outcome_verified'] for i in work['items'])
        if uncertain:isler+=f'; görünen işlerin {uncertain} tanesinin sonucu henüz doğrulanmadı'
        if not work['complete_list']:isler+='; liste kısmi'
    return onay+'. '+isler+'. Onay verilmesi işin bittiğini kanıtlamaz.'


if __name__=='__main__':print(json.dumps(snapshot(),ensure_ascii=False))
