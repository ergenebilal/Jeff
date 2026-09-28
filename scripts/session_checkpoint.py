#!/usr/bin/env python3
"""Session Checkpoint — Uzun konuşmalarda otomatik özet çıkarır ve kaydeder.
Her 50 mesajda bir çalışır.
"""
import json, os, subprocess
from datetime import datetime

CHECKPOINT_DIR = os.path.expanduser("~/.hermes/checkpoints/")
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

def save_checkpoint(summary, session_id="auto"):
    filename = f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M')}_{session_id[:8]}.json"
    path = os.path.join(CHECKPOINT_DIR, filename)
    with open(path, "w") as f:
        json.dump({
            "time": datetime.now().isoformat(),
            "session": session_id,
            "summary": summary
        }, f, indent=2)
    print(f"💾 Checkpoint kaydedildi: {filename}")

def get_checkpoints(limit=5):
    files = sorted(os.listdir(CHECKPOINT_DIR))[-limit:]
    return [os.path.join(CHECKPOINT_DIR, f) for f in files]

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        save_checkpoint(sys.argv[1])
    else:
        print("Kullanım: session_checkpoint.py \"<özet>\"")
