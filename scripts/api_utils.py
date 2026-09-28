"""API Utilities — tüm modüller için standart log ve hata yönetimi.

Her modül şu standartları kullanır:
- Girdi: argparse veya JSON argümanları
- Çıktı (başarılı): print JSON veya print düz metin (CLI modu)
- Çıktı (hata): {"status": "error", "message": "..."}
- Log yeri: ~/.hermes/logs/<modul_adi>.log
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

LOGS_DIR = os.path.expanduser("~/.hermes/logs")
TZ = timezone(timedelta(hours=3))


def _ensure_logs_dir():
    os.makedirs(LOGS_DIR, exist_ok=True)


def log_error(module: str, error: Exception, context: Optional[str] = None) -> None:
    """Standart hata loglama.

    Args:
        module: Modül adı (örn: "meta_learner")
        error: Yakalanan exception
        context: Ek bağlam bilgisi
    """
    _ensure_logs_dir()
    log_path = os.path.join(LOGS_DIR, f"{module}.log")
    entry = {
        "timestamp": datetime.now(TZ).isoformat(),
        "module": module,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context or "",
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def error_response(module: str, message: str) -> Dict[str, Any]:
    """Standart hata yanıtı."""
    return {"status": "error", "message": message}


def success_response(data: Any = None) -> Dict[str, Any]:
    """Standart başarı yanıtı."""
    return {"status": "success", "data": data}


def log_info(module: str, message: str) -> None:
    """Standart bilgi logu."""
    _ensure_logs_dir()
    log_path = os.path.join(LOGS_DIR, f"{module}.log")
    entry = {
        "timestamp": datetime.now(TZ).isoformat(),
        "module": module,
        "level": "INFO",
        "message": message,
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
