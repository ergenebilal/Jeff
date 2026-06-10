"""Yardimci fonksiyonlar: _as_text, _ascii_fold, normalize_memory_category, vs."""

from __future__ import annotations

import re
from typing import Any

_TURKISH_ASCII = str.maketrans({
    "ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
    "Ç": "c", "Ğ": "g", "İ": "i", "I": "i", "Ö": "o", "Ş": "s", "Ü": "u",
})

CANONICAL_MEMORY_CATEGORIES = {
    "kisisel", "is", "strateji", "teknik", "risk", "firsat",
    "operasyon", "genel",
}

_CATEGORY_ALIASES = {
    "personal_reminder": "kisisel", "kişisel": "kisisel", "kisisel": "kisisel",
    "hatirlatma": "kisisel", "hatırlatma": "kisisel",
    "business_strategy": "strateji", "strateji": "strateji", "strategy": "strateji",
    "tech_note": "teknik", "teknik": "teknik", "hata": "teknik",
    "risk": "risk", "borc": "risk", "borç": "risk",
    "firsat": "firsat", "fırsat": "firsat", "gelir": "firsat",
    "müşteri dışı operasyon": "operasyon", "musteri disi operasyon": "operasyon",
    "operasyon": "operasyon",
    "is": "is", "iş": "is",
    "genel": "genel", "test": "genel",
}


def _as_text(value: Any) -> str:
    return "" if value is None else str(value)


def normalize_memory_category(label: str | None) -> str:
    raw = _as_text(label).strip().casefold()
    if not raw:
        return "genel"
    if raw in CANONICAL_MEMORY_CATEGORIES:
        return raw
    if raw in _CATEGORY_ALIASES:
        return _CATEGORY_ALIASES[raw]
    for needle, category in _CATEGORY_ALIASES.items():
        if needle in raw:
            return category
    return "genel"


def _ascii_fold(text: Any) -> str:
    return _as_text(text).translate(_TURKISH_ASCII).casefold()


def _extract_day_window(text: str) -> int | None:
    match = re.search(r"\((\d+)\s*g[üu]n\)", text, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def _extract_money_amount(text: str) -> str | None:
    match = re.search(r"(\d[\d.]*\s*(?:₺|tl|try))", text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None


def _clamp_score(value: Any) -> int:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return 0
    return max(0, min(5, number))
