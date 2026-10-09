"""Private correction choices and existing read-only evidence readers.

No model, dispatch, task replay, permanent correction or memory write.
Catalog entries are selection metadata, never independent outcome evidence.
"""
from copy import deepcopy
import json
import math
from pathlib import Path,PurePosixPath
import re
import sys
import time
from urllib.request import Request,urlopen

MAX_RESPONSE=262144

def checked_source(source):
    if not isinstance(source,str) or not 1<=len(source)<=400:
        raise ValueError('Invalid source selection')
    relative=PurePosixPath(source)
    if (relative.is_absolute() or '..' in relative.parts or '\\' in source or
            not relative.parts or relative.parts[0]!='knowledge' or relative.as_posix()!=source
            or any(ord(c)<32 for c in source)):
        raise ValueError('Invalid source selection')
    return source

def select_source(source, *, store, vault, examine, parse, redact, clock=time.time):
    """Use the actual eligibility gates and then recheck exact source bytes.

    Selection cannot silently use another search hit with a similar filename.
    Duplicate cache records are ambiguous; a source path is not truth authority.
    """
    checked_source(source)
    records,stale=store._eligible(audience='internal')
    selected=[deepcopy(record) for record in records if record.get('source')==source]
    if len(selected)!=1:
        selected=[]
    for record in selected:
        text=record.get('text')
        if not isinstance(text,str):
            raise ValueError('Invalid source text')
        if len(text)>32000:
            record['text']=text[:32000]+' [truncated]';record['text_truncated']=True
    value=examine(vault,{'records':selected,'stale_count':stale,'truncated':False},parse,redact,clock(),audience='internal')
    if any(row.get('source')!=source for row in value['records']):
        raise ValueError('Source binding changed')
    return value

def build_choices(query,offset, *, catalog_read,memory_read,redact):
    if not isinstance(query,str) or not 1<=len(query.strip())<=2000 or type(offset) is not int or not 0<=offset<=100000:
        raise ValueError('Invalid choices')
    catalog=catalog_read(offset)
    if (not isinstance(catalog,dict) or catalog.get('read_only') is not True or catalog.get('catalog_only') is not True
            or catalog.get('criterion_verified') is not False or catalog.get('current_outcome_verified') is not False
            or catalog.get('automatic_replay') is not False or not isinstance(catalog.get('items'),list)):
        raise ValueError('Unverified catalog boundary')
    tasks=[]
    for row in catalog['items']:
        if (not isinstance(row,dict) or set(row)!={'task_id','created_at','created_at_known'}
                or not isinstance(row['task_id'],str) or re.fullmatch(r'[A-Za-z0-9_-]{1,128}',row['task_id']) is None
                or type(row['created_at_known']) is not bool):
            raise ValueError('Invalid task catalog row')
        date=row['created_at']
        if row['created_at_known']:
            if type(date) not in (int,float) or not math.isfinite(date) or date<=0:
                raise ValueError('Invalid task catalog time')
        elif date is not None:
            raise ValueError('Unknown catalog time must remain unknown')
        tasks.append(dict(row))
    memory=memory_read(query);sources=[]
    if not isinstance(memory,dict) or memory.get('read_only') is not True or not isinstance(memory.get('records'),list):
        raise ValueError('Unverified memory boundary')
    for record in memory['records']:
        source=checked_source(record.get('source'))
        if record.get('source_hash_matched') is not True:
            continue
        text=record.get('text')
        if not isinstance(text,str) or not text.strip():
            continue
        # Real source excerpt as label, not an invented title or model summary.
        label=text.strip().splitlines()[0].lstrip('# ').strip()[:150]
        label,_=redact(label)
        source_safe,matches=redact(source)
        if source_safe!=source or matches!=0:
            continue
        date=record.get('declared_date')
        sources.append(dict(source=source,label=label,declared_date=date,
            assessment=record.get('assessment'),current_truth_verified=False))
    return dict(status='choices_ready',tasks=tasks,sources=sources,
        next_offset=catalog.get('next_offset'),omitted_in_page=catalog.get('omitted_in_page'),
        task_catalog_only=True,task_derived_from_source_verified=False,current_truth_verified=False,
        memory_list_partial=memory.get('retrieval_truncated') is True,read_only=True,
        memory_write_authorized=False,execution_authorized=False,reexecution_authorized=False)

def production_dependencies(app):
    sys.path.insert(0,'/home/hermes/jeff_repo')
    from scripts.pablo_decision_reader import read_decision
    from scripts.pablo_outcome_evidence import strict_json,valid_id
    from scripts.jeff_memory_context import VAULT,examine,read_context
    runtime=json.loads((VAULT/'.beyin-runtime.json').read_text())
    state=Path(runtime['state'])
    if not state.is_absolute() or state.resolve().is_relative_to(VAULT):
        raise ValueError('Invalid memory runtime')
    sys.path.insert(0,str(VAULT/'.claude/scripts'))
    from beyin_v3 import MemoryStore
    from beyin_v3_sync import parse
    from beyin_v3_secrets import redact as pure_redact
    store=MemoryStore(state,VAULT,read_only=True)
    safe=lambda text:pure_redact(text,state)
    def node(path):
        config=json.loads((Path(app.DATA)/'approval-gateway.json').read_text())
        key=config.get('auth_token')
        if not isinstance(key,str) or not key:
            raise ValueError('Node authentication unavailable')
        request=Request('http://100.89.26.86:7788'+path,headers={'X-Bridge-Key':key},method='GET')
        with urlopen(request,timeout=5) as response:
            raw=response.read(MAX_RESPONSE+1)
        if len(raw)>MAX_RESPONSE:
            raise ValueError('Evidence response exceeds bound')
        value=strict_json(raw)
        if not isinstance(value,dict):
            raise ValueError('Invalid evidence response')
        return value
    def load(task,suffix):
        if not valid_id(task) or suffix not in ('','/criterion','/observation'):
            raise ValueError('Invalid original evidence selection')
        value=node('/tasks/'+task+suffix)
        if value.get('request_id')!=task:
            raise ValueError('Evidence identity mismatch')
        return value
    decision=lambda task:read_decision(task,loader=load)
    selected=lambda source:select_source(source,store=store,vault=VAULT,examine=examine,parse=parse,redact=safe)
    choices=lambda query,offset:build_choices(query,offset,
        catalog_read=lambda offset:node('/draft-choices?limit=20&offset='+str(offset)),
        memory_read=read_context,redact=safe)
    return decision,selected,safe,choices


def production_excerpt_reader():
    """Existing cognition reader, source identity checked before private load."""
    import hashlib
    import importlib.util
    source=Path('/home/hermes/.hermes/plugins/jeff-reasoning/__init__.py')
    reference=Path('/home/hermes/jeff_repo/integrations/jeff-reasoning/__init__.py')
    try:
        actual=source.read_bytes();expected=reference.read_bytes()
    except OSError:
        raise ValueError('Verified excerpt reader unavailable') from None
    if hashlib.sha256(actual).digest()!=hashlib.sha256(expected).digest():
        raise ValueError('Cognition source changed')
    spec=importlib.util.spec_from_file_location('panel_advice_current_cognition',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    if not callable(getattr(module,'source_window',None)):
        raise ValueError('Verified excerpt reader unavailable')
    return module.source_window
