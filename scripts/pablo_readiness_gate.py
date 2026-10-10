"""Fail-closed admission using the authenticated, current Windows observation."""
import json
import math
from pathlib import Path
import time

INBOX=Path('/home/hermes/.local/state/jeff-github-sync/windows-source.json')
READ_ACTIONS=frozenset(('read','read_file','file_read','file_read_content','file_list',
    'list_files','list_dir','dir_list','window_list','marketing_list','pilot_status','ping'))


def admission(action, *, inbox=INBOX, clock=time.time):
    out={'admitted':False,'status':'RECOVERY_UNAVAILABLE','ok':False,
         'outcome_verified':False,'completion_authority':False,'execution_authorized':False,
         'replayed':False,'reason':'Pablo için güncel çalışma kanıtı alınamadı.'}
    try:
        packet=json.loads(Path(inbox).read_text())
        health=packet.get('runtime_health',{})
        now=clock();stamp=packet.get('observed_at');checked=health.get('observed_at')
        valid_time=lambda x:type(x) in (int,float) and math.isfinite(x) and now-300 <= x <= now+5
        if packet.get('version')!=1 or health.get('schema_version')!=1 or not valid_time(stamp) or not valid_time(checked) or abs(stamp-checked)>30:
            return out
        checks=health.get('checks')
        required={'config.json','deployment.json','task-journal.sqlite3','intent_guard.sqlite3',
                  'configuration','release','running_sources','journal_schema','journal_integrity','intent_schema','intent_integrity'}
        if health.get('runtime_ready') is not True or not isinstance(checks,dict) or not required<=checks.keys() or not all(checks[k] is True for k in required):
            return out
        mode=health.get('mode');out['mode']=mode
        if mode=='read_only_recovery':
            if checks.get('recovery_write_lock') is not True or health.get('missing_interval_reconciled') is not False:
                return out
            if action not in READ_ACTIONS:
                out.update(status='RECOVERY_READ_ONLY',reason='Eksik iş geçmişi inceleniyor. Şimdilik yalnız okuma yapılabilir; bu iş başlatılmadı.')
                return out
        elif mode!='normal' or health.get('missing_interval_reconciled') is not True:
            return out
        out.update(admitted=True,status='ADMITTED',execution_authorized=True,
                   reason='Güncel çalışma durumu bu okuma işlemine izin veriyor.' if mode=='read_only_recovery' else 'Güncel çalışma kontrolleri geçti.')
    except (OSError,ValueError,TypeError,AttributeError):
        pass
    return out


def require(action):
    result=admission(action)
    if not result['admitted']:
        print(json.dumps(result,ensure_ascii=False));raise SystemExit(3)
    return result
