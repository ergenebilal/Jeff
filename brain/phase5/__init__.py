"""Phase 5: Mode Ayrımı (Quick / Deep / Background)."""
from .mode_quick import QuickMode
from .mode_deep import DeepMode
from .mode_background import BackgroundMode
from .mode_router import ModeRouter, detect_mode, set_mode

__all__ = [
    "QuickMode",
    "DeepMode",
    "BackgroundMode",
    "ModeRouter",
    "detect_mode",
    "set_mode",
]
