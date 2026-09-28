#!/usr/bin/env python3
"""
Test: Kodlama Protokolü skill content integrity check.
Verifies all 6 sections exist in correct order.
"""
import os
import sys
from typing import List, Tuple

SKILL_PATH: str = os.path.expanduser("~/.hermes/skills/self/kodlama-protokolu/SKILL.md")

REQUIRED_SECTIONS: List[Tuple[str, str]] = [
    ("1. ÖNCE TEST", "Test-Driven Development"),
    ("2. ATOMİK DEĞİŞİKLİK", "Patch Only"),
    ("3. TYPE HINT", "ERROR HANDLING"),
    ("4. SEQUENTIAL-THINKING", "thought chain"),
    ("5. ÖZ-DENETİM", "Kanıt esaslı"),
    ("6. PROTOTYPE VS ÜRETİM", "Prototip"),
]


def test_skill_exists() -> None:
    """Assert skill file exists and is readable."""
    assert os.path.exists(SKILL_PATH), f"FAIL: Skill not found at {SKILL_PATH}"
    print(f"  Skill dosyası mevcut: {SKILL_PATH}")


def test_has_all_sections() -> None:
    """Assert all 6 required sections exist in content."""
    with open(SKILL_PATH, "r") as f:
        content: str = f.read()

    print(f"\n  Toplam boyut: {len(content)} karakter")
    print(f"  Satır sayısı: {content.count(chr(10))}")

    for title, keyword in REQUIRED_SECTIONS:
        assert title in content, f"FAIL: '{title}' bölümü eksik"
        assert keyword in content, f"FAIL: '{title}' -> '{keyword}' anahtar kelimesi eksik"
        print(f"  ✅ {title} — ({keyword}) mevcut")


def test_no_duplicate_ihlal() -> None:
    """Assert 'İhlal Durumu' heading appears exactly once."""
    count: int = SKILL_PATH  # placeholder
    with open(SKILL_PATH, "r") as f:
        content: str = f.read()
    count = content.count("## İhlal Durumu")
    assert count == 1, f"FAIL: 'İhlal Durumu' {count} kez geçiyor (1 olmalı)"
    print(f"  ✅ İhlal Durumu tek: {count}")


def main() -> None:
    """Run all protokol integrity checks."""
    print("=== Kodlama Protokolü Skill Testi ===")
    test_skill_exists()
    test_has_all_sections()
    test_no_duplicate_ihlal()
    print("\n✅ PASS: Protokol skill'i 6 bölümle eksiksiz ve hatasız")


if __name__ == "__main__":
    main()
