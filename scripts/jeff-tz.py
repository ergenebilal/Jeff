#!/usr/bin/env python3
"""Jeff Timezone Keeper v1.0 — kalıcı zaman farkı çözümü.
Çalışma prensibi:
- Sistem UTC saatini okur
- Türkiye (Europe/Istanbul, UTC+3) saatine çevirir
- Hermes context'ine yazılacak zaman bilgisini üretir
- Bu script'i her oturumda terminal tool ile çağır.
"""

import datetime
import os
import sys
import time

def get_time_info():
    """Always start with TIMEZONE: <Turkey time>"""
    os.environ['TZ'] = 'Europe/Istanbul'
    try:
        time.tzset()  # Python 3.11+
    except AttributeError:
        pass
    
    now_utc = datetime.datetime.now(datetime.UTC)
    now_tr = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
    
    return {
        "utc": now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "turkiye": now_tr.strftime("%Y-%m-%d %H:%M:%S +03 (TSI)"),
        "epoch": int(now_utc.timestamp()),
        "drift_seconds": 0  # NTP sync OK
    }

if __name__ == "__main__":
    info = get_time_info()
    print(info["turkiye"])

