#!/usr/bin/env python3
"""Read official clinic pages and upsert at most ten sourced candidates."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from executive_briefing import BriefingStore, scan_sources


DEFAULT_DB = Path(__file__).resolve().parents[1] / 'jeff2' / 'bridge' / 'bridge.db'


def main(argv=None):
    parser = argparse.ArgumentParser(description='Read-only clinic opportunity radar')
    parser.add_argument('--sources', type=Path, required=True,
                        help='JSON list of official clinic website records')
    parser.add_argument('--db', type=Path, default=Path(os.environ.get('JEFF_LEDGER_DB', DEFAULT_DB)))
    args = parser.parse_args(argv)
    sources = json.loads(args.sources.read_text(encoding='utf-8'))
    if not isinstance(sources, list):
        parser.error('Sources must be a JSON list')
    now = datetime.now(timezone.utc)
    candidates = scan_sources(sources[:10], now)
    store = BriefingStore(args.db)
    store.initialize()
    counts = store.ingest(candidates, now)
    print(json.dumps({'observed_at': now.isoformat(), 'scanned': len(sources[:10]),
                      'sourced': len(candidates), **counts}, ensure_ascii=False))
    return counts


if __name__ == '__main__':
    main()
