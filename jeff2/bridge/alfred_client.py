#!/usr/bin/env python3
"""Legacy Alfred presence adapter. Task execution belongs to Pablo TaskGuard."""
import os
import time

import requests

JEFF_API = os.environ.get('JEFF_API', 'http://127.0.0.1:7700')
BRIDGE_KEY = os.environ.get('BRIDGE_KEY')
HEARTBEAT_INTERVAL = 30


def main():
    if not BRIDGE_KEY:
        raise SystemExit('BRIDGE_KEY is required')
    session = requests.Session()
    session.headers['X-Bridge-Key'] = BRIDGE_KEY
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
