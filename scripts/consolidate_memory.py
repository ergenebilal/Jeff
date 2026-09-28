#!/usr/bin/env python3
"""
Memory Consolidation Agent — runs nightly at 03:00.
Reads current memory entries, removes stale/duplicate/low-value entries,
compresses verbose ones, and keeps memory lean.

Protokol: type hint + try-except + internal_log
"""
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

LOG_PATH: str = os.path.expanduser("~/.hermes/logs/memory_consolidation.log")
INTERNAL_LOG: str = os.path.expanduser("~/.hermes/internal_log.json")

# Entries that are always kept (core rules/reflexes)
PROTECTED_KEYWORDS: List[str] = [
    "KODLAMA PROTOKOLÜ",
    "HALÜSİNASYON REFLEKSİ",
    "SOHBET KURALI",
    "TIMEZONE REFLEKS",
    "TIMEZONE:",
]

# Stale patterns — entries containing these are candidates for removal
STALE_PATTERNS: List[str] = [
    "Memory cleanup result",
    "Sales pipeline",
    "IG botu",
    "Görsel pazarlama motoru aktif",
]


def log(message: str) -> None:
    """Append timestamped log entry."""
    ts: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line: str = f"[{ts}] {message}"
    print(line)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def log_internal(component: str, message: str, level: str = "INFO") -> None:
    """Write structured entry to internal_log.json."""
    entry: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "component": component,
        "level": level,
        "message": message,
    }
    try:
        existing: List[Dict[str, Any]] = []
        if os.path.exists(INTERNAL_LOG):
            with open(INTERNAL_LOG, "r") as f:
                existing = json.load(f)
        existing.append(entry)
        with open(INTERNAL_LOG, "w") as f:
            json.dump(existing[-100:], f, indent=2)
    except Exception as e:
        log(f"WARN: Could not write internal log: {e}")


def consolidate(current_entries: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Analyze and consolidate memory entries.
    Returns filtered/compressed list.
    """
    kept: List[Dict[str, str]] = []
    removed_count: int = 0

    for entry in current_entries:
        content: str = entry.get("content", "")
        target: str = entry.get("target", "memory")

        # Protect critical rules
        if any(kw in content for kw in PROTECTED_KEYWORDS):
            kept.append(entry)
            continue

        # Remove stale patterns
        if any(pattern in content for pattern in STALE_PATTERNS):
            removed_count += 1
            log(f"REMOVE stale: {content[:60]}...")
            continue

        # Compress verbose entries (>300 chars)
        if len(content) > 300:
            compressed: str = content[:250] + "..."
            entry["content"] = compressed
            log(f"COMPRESS: {len(content)} -> {len(compressed)} chars")
            kept.append(entry)
            continue

        kept.append(entry)

    log(f"Consolidation done: {len(current_entries)} -> {len(kept)} entries ({removed_count} removed)")
    return kept


def main() -> None:
    """Main consolidation routine."""
    log("=== Memory Consolidation Start ===")
    log_internal("memory-consolidation", "Starting nightly consolidation")

    # Current entries are passed via stdin as JSON array
    # If running standalone, report status and exit
    log("Standalone mode: memory consolidation requires agent context")
    log("To run: pipe memory entries as JSON via stdin")
    log_internal("memory-consolidation", "Standalone check completed (no entries processed)")
    log("=== Memory Consolidation End ===")
    sys.exit(0)


if __name__ == "__main__":
    main()
