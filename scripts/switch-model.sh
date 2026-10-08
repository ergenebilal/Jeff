#!/bin/bash
# Reapply Bilal's selected Jeff routes; retired models are not selectable.
set -euo pipefail
case "${1:-primary}" in
  status)
    exec /home/hermes/.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
cfg=yaml.safe_load(Path('/home/hermes/.hermes/config.yaml').read_text()) or {}
primary=cfg.get('model',{})
print('Ana:',primary.get('provider'),primary.get('default'))
for fallback in cfg.get('fallback_providers',[]):
    print('Yedek:',fallback.get('provider'),fallback.get('model'))
PY
    ;;
  primary|go|flash|deepseek) ;;
  *) echo 'Kullanım: switch-model.sh {primary|go|flash|deepseek|status}' >&2; exit 1 ;;
esac
/home/hermes/.venv/bin/python - <<'PY'
from pathlib import Path
import os,shutil,tempfile,time,yaml
path=Path('/home/hermes/.hermes/config.yaml')
cfg=yaml.safe_load(path.read_text()) or {}
backup=Path('/home/hermes/backups')/('model-route-'+str(time.time_ns()))
backup.mkdir(mode=0o700)
shutil.copy2(path,backup/'config.yaml');(backup/'config.yaml').chmod(0o600)
cfg['model']={'provider':'opencode-go','default':'deepseek-v4.1-flash'}
cfg['fallback_providers']=[{'provider':'antigravity','model':'gemini-3.8-flash-high','base_url':'http://127.0.0.1:8999/v1'}]
cfg.pop('fallback_model',None)
fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.model-route-')
try:
    with os.fdopen(fd,'w') as handle:
        yaml.safe_dump(cfg,handle,allow_unicode=True,sort_keys=False)
        handle.flush();os.fsync(handle.fileno())
    os.replace(tmp,path)
finally:
    if os.path.exists(tmp):os.unlink(tmp)
print('Ana: OpenCode Go / DeepSeek 4.1 Flash; yedek: Antigravity / Gemini 3.8 Flash High')
PY
