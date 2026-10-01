"""Phase 9 testleri (prompt'taki Instagram ornegi dahil)."""

import pytest

from jeff_cognitive.learning import build_lesson


def test_instagram_lesson():
    les = build_lesson(
        believed="Instagram yorumlari anlamli inbound talep gosterir",
        happened="Gozlenen yorumlar yanitsiz musteri talebi degildi",
        why_matters="Yorum yoklugu yanit basarisizligi sayildi",
        failed_assumption="'Yorum yok' = 'yanitsiz musteri' yanlis okundu",
        change="Yorum yoklugunu yanit basarisizligi kaniti sayma",
        apply_where="social-listening/*",
        confidence=0.7,
    )
    assert les.lesson_id
    enf = les.to_enforcer_format()
    assert "yorum yoklugunu" in enf["rule"].lower() or "Yorum" in enf["rule"]


def test_missing_field_rejected():
    with pytest.raises(ValueError):
        build_lesson(believed="x", happened="y", why_matters="z",
                     failed_assumption="", change="c", apply_where="w")
