#!/usr/bin/env python3
"""Jeff Google Drive backup - no_agent cron script"""
import subprocess, sys
from pathlib import Path

BACKUP_SCRIPT = Path.home() / "backup-jeff.sh"
LOG = Path.home() / "logs" / "drive-backup.log"
LOG.parent.mkdir(exist_ok=True)

if not BACKUP_SCRIPT.exists():
    print("backup-jeff.sh not found")
    sys.exit(1)

result = subprocess.run(["bash", str(BACKUP_SCRIPT)], capture_output=True, text=True, timeout=600)
with open(LOG, "a") as f:
    f.write(result.stdout + "\n" + result.stderr + "\n")
print(f"exit={result.returncode}, output written to {LOG}")
sys.exit(result.returncode)
