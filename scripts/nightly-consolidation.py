#!/usr/bin/env python3.11
"""Gece birleştirme (nightly consolidation) — cron no-agent script (14.09.2026 onarildi)."""
import json
import os
import sys

ROOT = "/home/hermes/.hermes/hermes-agent"
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from agent.consolidation import nightly_consolidation  # noqa: E402

if __name__ == "__main__":
    print(json.dumps(nightly_consolidation(), indent=2, default=str))
