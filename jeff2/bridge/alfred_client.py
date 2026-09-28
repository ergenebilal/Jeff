#!/usr/bin/env python3
"""Legacy Alfred presence adapter. Task execution belongs to Pablo TaskGuard."""
import os
import time

import requests

JEFF_API = os.environ.get('JEFF_API', 'http://127.0.0.1:7700')
BRIDGE_KEY = os.environ.get('BRIDGE_KEY')
TASK_WORKER_KEY = os.environ.get('TASK_WORKER_KEY')
PABLO_WORKER_ID = os.environ.get('PABLO_WORKER_ID')
HEARTBEAT_INTERVAL = 30


def main():
    if not BRIDGE_KEY or not TASK_WORKER_KEY or BRIDGE_KEY == TASK_WORKER_KEY or not PABLO_WORKER_ID:
        raise SystemExit('Separate BRIDGE_KEY, TASK_WORKER_KEY and PABLO_WORKER_ID are required')
    session = requests.Session()
    session.headers['X-Bridge-Key'] = BRIDGE_KEY
    session.headers['X-Task-Worker-Key'] = TASK_WORKER_KEY
    session.headers['X-Worker-ID'] = PABLO_WORKER_ID
    while True:
        response = session.post(
            f'{JEFF_API}/alfred/heartbeat',
            json={'agent': 'alfred-presence', 'status': 'ok', 'version': '2.0'},
            timeout=10,
        )
        response.raise_for_status()
        time.sleep(HEARTBEAT_INTERVAL)


if __name__ == '__main__':
    main()
