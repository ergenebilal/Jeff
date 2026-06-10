#!/usr/bin/env python3
"""Swarm Communicator — alt Jeff'ler arasında iletişim."""

import json, os
from datetime import datetime, timezone, timedelta
from typing import Dict, List

TZ = timezone(timedelta(hours=3))
SWARM_DIR = os.path.expanduser("~/.hermes/swarm")
COMMS_DIR = os.path.join(SWARM_DIR, "comms")
COMMS_LOG = os.path.join(SWARM_DIR, "comms_log.jsonl")


def send_message(from_agent: str, to_agent: str, message: str, message_type: str = "bilgi") -> Dict:
    os.makedirs(COMMS_DIR, exist_ok=True)
    comm = {"message_id": f"msg_{datetime.now(TZ).strftime('%H%M%S')}_{from_agent[-4:]}",
            "from": from_agent, "to": to_agent, "message": message, "type": message_type,
            "timestamp": datetime.now(TZ).isoformat(), "okundu": False}
    if to_agent == "tumu":
        for fname in os.listdir(COMMS_DIR):
            if fname.startswith("inbox_"):
                with open(os.path.join(COMMS_DIR, fname), "a") as f:
                    f.write(json.dumps(comm, ensure_ascii=False) + "\n")
    else:
        with open(os.path.join(COMMS_DIR, f"inbox_{to_agent}.jsonl"), "a") as f:
            f.write(json.dumps(comm, ensure_ascii=False) + "\n")
    return comm


def read_messages(agent_id: str, mark_read: bool = True) -> List[Dict]:
    inbox_path = os.path.join(COMMS_DIR, f"inbox_{agent_id}.jsonl")
    if not os.path.exists(inbox_path):
        return []
    msgs = []
    try:
        with open(inbox_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        msgs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except IOError:
        pass
    return msgs


def get_conversation_history() -> List[Dict]:
    if not os.path.exists(COMMS_LOG):
        return []
    history = []
    try:
        with open(COMMS_LOG) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        history.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except IOError:
        pass
    return history


def broadcast_status(agent_id: str, durum: str, mesaj: str) -> Dict:
    return send_message(from_agent=agent_id, to_agent="tumu",
                        message=f"[{durum.upper()}] {mesaj}", message_type="durum")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("send")
    p.add_argument("from_agent"); p.add_argument("to_agent"); p.add_argument("message")
    p2 = sub.add_parser("read")
    p2.add_argument("agent_id")
    sub.add_parser("history")
    p3 = sub.add_parser("broadcast")
    p3.add_argument("agent_id"); p3.add_argument("durum"); p3.add_argument("mesaj")
    args = parser.parse_args()
    if args.command == "send":
        r = send_message(args.from_agent, args.to_agent, args.message)
        print(f"Mesaj: {r['from']} -> {r['to']}")
    elif args.command == "read":
        msgs = read_messages(args.agent_id)
        print(f"{len(msgs)} mesaj")
    elif args.command == "history":
        print(f"{len(get_conversation_history())} kayit")
    elif args.command == "broadcast":
        broadcast_status(args.agent_id, args.durum, args.mesaj)
        print("Broadcast gonderildi")
