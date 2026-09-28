"""Install reviewed sources only. Does not restart any service or execute agents."""
import hashlib
import json
import os
from pathlib import Path
import shutil

stage=Path(__file__).parent
manifest=json.loads((stage/'install_manifest.json').read_text())
backup=Path('/home/hermes/.hermes/change-backups/20260924-task-guard')
if backup.exists():
    raise SystemExit('Backup already exists; refusing accidental second installation')
for entry in manifest:
    source=stage/entry['source']; target=Path(entry['target'])
    assert hashlib.sha256(source.read_bytes()).hexdigest()==entry['sha256'], entry['source']
    if entry.get('original_sha256'):
        assert hashlib.sha256(target.read_bytes()).hexdigest()==entry['original_sha256'], 'Concurrent change: '+str(target)
    else:
        assert not target.exists(), 'Unexpected existing target: '+str(target)
    if source.suffix=='.py':
        compile(source.read_text(encoding='utf-8'),str(target),'exec')
backup.mkdir(parents=True,mode=0o700)
for index,entry in enumerate(manifest):
    source=stage/entry['source']; target=Path(entry['target'])
    if target.exists():
        shutil.copy2(target,backup/(str(index)+'-'+target.name))
    target.parent.mkdir(parents=True,exist_ok=True)
    temporary=target.with_name(target.name+'.cybergene-install')
    assert not temporary.exists()
    shutil.copyfile(source,temporary)
    os.chmod(temporary, target.stat().st_mode & 0o777 if target.exists() else 0o600)
    os.replace(temporary,target)
    assert hashlib.sha256(target.read_bytes()).hexdigest()==entry['sha256']
    print('SOURCE_INSTALLED',target)
shutil.copyfile(stage/'install_manifest.json',backup/'manifest.json')
print('NO_SERVICES_RESTARTED')
