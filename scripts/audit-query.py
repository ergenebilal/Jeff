#!/usr/bin/env python3
import argparse, json, os, sys
from datetime import datetime, timezone

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audit", "audit.log")

def parse_args():
    parser = argparse.ArgumentParser(description="Audit log sorgulama araci")
    parser.add_argument("--action", help="Filtre: action_type")
    parser.add_argument("--since", help="ISO tarih/saat filtresi (ornek: 2026-06-19 veya 2026-06-19T10:00:00)")
    parser.add_argument("--status", choices=["error", "success", "all"], default="all", help="Durum filtresi")
    parser.add_argument("--limit", type=int, default=20, help="Kac satir gosterilecek (default: 20)")
    return parser.parse_args()

def filter_record(rec, args):
    if args.action and rec.get("action_type") != args.action:
        return False
    if args.since:
        try:
            since = datetime.fromisoformat(args.since)
            if since.tzinfo is None:
                since = since.replace(tzinfo=timezone.utc)
            ts = datetime.fromisoformat(rec["timestamp"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts < since:
                return False
        except (ValueError, KeyError):
            pass
    if args.status == "error" and rec.get("status") != "error":
        return False
    if args.status == "success" and rec.get("status") != "success":
        return False
    return True

def main():
    args = parse_args()

    if not os.path.exists(LOG_FILE):
        print(f"Log dosyasi bulunamadi: {LOG_FILE}", file=sys.stderr)
        sys.exit(1)

    records = []
    with open(LOG_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if filter_record(rec, args):
                    records.append(rec)
            except json.JSONDecodeError:
                continue

    records.sort(key=lambda r: r.get("timestamp", ""))

    display = records[-args.limit:] if args.limit > 0 else records

    if not display:
        print("Hata bulunamadi")
        return

    header = f"{'Timestamp':<30} {'Session':<20} {'Action':<20} {'Tool':<20} {'Status':<10} {'Dur(s)':<8} Error"
    try:
        cols = os.get_terminal_size().columns
    except OSError:
        cols = 120
    sep = "-" * min(cols, 120)
    print(header)
    print(sep)

    for rec in display:
        ts = rec.get("timestamp", "")[:26]
        sid = rec.get("session_id", "")[:18]
        act = rec.get("action_type", "")[:18]
        tool = rec.get("tool", "")[:18]
        st = rec.get("status", "")[:8]
        dur = rec.get("duration", 0)
        err = rec.get("error", "")
        print(f"{ts:<30} {sid:<20} {act:<20} {tool:<20} {st:<10} {dur:<8.3f} {err}")

    print(sep)
    total = len(records)
    errors = sum(1 for r in records if r.get("status") == "error")
    error_rate = (errors / total * 100) if total > 0 else 0
    print(f"Toplam: {total} kayit  |  Hata: {errors}  |  Hata orani: %{error_rate:.1f}")

    if errors == 0:
        print("Hata bulunamadi")

if __name__ == "__main__":
    main()
