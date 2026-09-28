#!/usr/bin/env python3
"""Produce the sourced executive briefing; delivery requires --send."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path

from executive_briefing import BriefingStore, TelegramDelivery


DEFAULT_DB = Path(__file__).resolve().parents[1] / 'jeff2' / 'bridge' / 'bridge.db'


def main(argv=None):
    parser = argparse.ArgumentParser(description='Create a verified executive briefing')
    parser.add_argument('--db', type=Path, default=Path(os.environ.get('JEFF_LEDGER_DB', DEFAULT_DB)))
    parser.add_argument('--dry-run', type=Path, help='Write the report to this local file')
    parser.add_argument('--send', action='store_true', help='Send to the configured admin chat')
    args = parser.parse_args(argv)
    if not args.dry_run and not args.send:
        parser.error('Specify --dry-run or --send')
    store = BriefingStore(args.db)
    report = store.snapshot(datetime.now(timezone.utc))
    if args.dry_run:
        args.dry_run.parent.mkdir(parents=True, exist_ok=True)
        args.dry_run.write_text(report.text + '\n', encoding='utf-8')
        print(f'DRY_RUN: {args.dry_run}')
    if args.send:
        if not args.db.exists():
            parser.error('Canonical database unavailable; refusing delivery')
        token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('ADMIN_CHAT_ID')
        if not token or not chat_id:
            parser.error('TELEGRAM_BOT_TOKEN and ADMIN_CHAT_ID are required')
        store.initialize()
        result = TelegramDelivery(store, token=token, chat_id=chat_id).send(
            report.report_id, report.text)
        print(f"Delivery: {result['status']}; chunks: {result['chunks']}")
    return report


if __name__ == '__main__':
    main()
