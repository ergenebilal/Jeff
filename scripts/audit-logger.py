#!/usr/bin/env python3
import json, os, sys
from datetime import datetime, timezone

def main():
    if len(sys.argv) < 5:
        print(f"Kullanim: {sys.argv[0]} action_type tool status duration_sec [error_msg]", file=sys.stderr)
        sys.exit(1)

    action_type = sys.argv[1]
    tool = sys.argv[2]
    status = sys.argv[3]
    duration = float(sys.argv[4])
    error = sys.argv[5] if len(sys.argv) > 5 else ""

    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audit")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "audit.log")

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": os.environ.get("HERMES_SESSION_ID", "unknown"),
        "action_type": action_type,
        "tool": tool,
        "status": status,
        "duration": duration,
        "error": error,
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
