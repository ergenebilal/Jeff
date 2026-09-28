#!/usr/bin/env python3.11
"""Sabah brifingi — cron no-agent script (14.09.2026 onarildi)."""
import os
import sys

ROOT = "/home/hermes/.hermes/hermes-agent"
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from agent.proactive import generate_morning_report  # noqa: E402

if __name__ == "__main__":
    print(generate_morning_report())
