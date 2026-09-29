#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CYBERGENE INSTAGRAM EDİTORYAL KAPISI
-------------------------------------
Deterministik, LLM'siz yapısal ön-denetim. Kaynak kurallar:
- cybergene-web/docs/cybergene-instagram-master-v0.1.md (§2 editoryal ses, §5 tekrar denetimi)
- cybergene-web/docs/cybergene-instagram-quality-v1.0.md (Doğrudan ret listesi)
- cybergene-web/docs/cybergene-instagram-playbook-v1.0.md (§7 otomasyon sınır matrisi)

Bu kapı NİHAİ karar mercii DEĞİLDİR. Yalnız bariz, kod ile yakalanabilir
ihlalleri (eksik alan, yasaklı ifade, kaynaksız sayısal iddia, bariz tekrar)
süzer. GATE_PASSED = "bariz bir ihlal bulunamadı", yayın onayı veya estetik
onay anlamına gelmez. Gerçek editoryal/görsel karar her zaman insana veya
bir Claude Code sanat yönetimi oturumuna aittir.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from cybergene_site_taxonomy import SITE_PILLARS, RECENCY_WINDOW, RECENCY_DOMINANCE_THRESHOLD

VISUAL_FAMILIES = {"Dönüşüm", "Görev sınırı", "Karar sayfası", "İş dosyası", "İz sürme"}

EVIDENCE_TYPES = {
    "doğrulanmış marka ifadesi",
    "kaynaklı dış bilgi",
    "açıkça etiketli temsili senaryo",
    "doğrulanmış müşteri vakası",
}

REQUIRED_FIELDS = [
    "content_id", "visual_family", "site_pillar", "target_reader", "problem",
    "single_takeaway", "mechanism", "human_control_note",
    "evidence_type", "hook_text", "caption_draft",
]

# quality-v1.0.md "Doğrudan ret" + master-v0.1.md editoryal ses / kesin ret nedenleri
BANNED_PHRASES = [
    "uyumaz", "izin istemez", "hastalanmaz",
    "devrim", "rakiplerinizi geride bırak", "işinizi uçur",
    "personeliniz uyur", "kaybetmeyi bırak",
]

NUMERIC_CLAIM_PATTERN = re.compile(r"%\s?\d{1,3}|\d{1,3}\s?%|\d+\s*(kat|saat tasarruf|gün içinde)")


def _missing_fields(idea: Dict[str, Any]) -> List[str]:
    return [f for f in REQUIRED_FIELDS if not str(idea.get(f, "")).strip()]


def _norm(text: str) -> str:
    return re.sub(r"[^a-zçğıöşü0-9 ]", "", (text or "").lower()).strip()


def _duplicate_candidates(
    idea: Dict[str, Any], recent_ideas: List[Dict[str, Any]], limit: int = 30
) -> List[Dict[str, Any]]:
    """
    master-v0.1.md §5: tekrar denetimi başlığa değil problem + mekanizma + çıkarım
    üçlüsüne bakar. Burada kaba, normalize edilmiş bir metin örtüşmesi uygulanır —
    bu bir anlamsal (semantic) benzerlik kontrolü DEĞİLDİR, yalnız bariz tekrarları
    yakalamayı hedefler. Nihai "yeni mi değil mi" kararı her zaman insana aittir.
    """
    target = "|".join([
        _norm(idea.get("problem", "")),
        _norm(idea.get("mechanism", "")),
        _norm(idea.get("single_takeaway", "")),
    ])
    hits = []
    for other in recent_ideas[:limit]:
        if other.get("id") == idea.get("id"):
            continue
        other_key = "|".join([
            _norm(other.get("problem", "")),
            _norm(other.get("mechanism", "")),
            _norm(other.get("single_takeaway", "")),
        ])
        if not other_key.strip("|"):
            continue
        pairs = zip(target.split("|"), other_key.split("|"))
        overlap = sum(1 for a, b in pairs if a and b and (a in b or b in a))
        if overlap >= 2:
            hits.append(other)
    return hits


def _recency_dominance_notes(idea: Dict[str, Any], recent_ideas: List[Dict[str, Any]]) -> List[str]:
    """
    master-v0.1.md §5 / playbook-v1.0.md §3: son RECENCY_WINDOW gönderide tek
    sektörün/pillar'ın veya tek görsel ailenin baskınlaşması editoryal gözden
    geçirme sebebidir. REJECTED olanlar bu pencereye dahil edilmez — fiilen
    üretilmemiş/kabul edilmemiş içerik "tekrar" sayılmaz.
    """
    notes: List[str] = []
    window = [i for i in recent_ideas if i.get("status") != "REJECTED"][: RECENCY_WINDOW - 1]

    for axis, label in (("site_pillar", "konu (site pillar)"), ("visual_family", "görsel aile")):
        value = idea.get(axis)
        if not value:
            continue
        same = sum(1 for i in window if i.get(axis) == value)
        if same + 1 >= RECENCY_DOMINANCE_THRESHOLD:
            notes.append(
                f"Son {RECENCY_WINDOW} gönderide aynı {label} ('{value}') baskınlaşıyor "
                f"({same + 1}/{min(RECENCY_WINDOW, len(window) + 1)}). Çeşitlilik için editoryal "
                f"gözden geçirme önerilir; otomatik engellenmedi."
            )
    return notes


def run_editorial_gate(
    idea: Dict[str, Any], recent_ideas: Optional[List[Dict[str, Any]]] = None
) -> Tuple[bool, List[str], List[str]]:
    """
    idea: instagram_content_ideas satırıyla aynı alanları taşıyan dict.
    recent_ideas: tekrar denetimi için son N kayıt (en yeni önce).

    Returns: (passed, hard_reasons, soft_notes).

    hard_reasons niteliğindeki her ihlal yapısaldır (eksik alan, yasaklı
    ifade, kaynaksız iddia, geçersiz taksonomi) — bunlardan biri varsa
    passed=False olur, kayıt GATE_REJECTED işaretlenir ve Bilal'e onay
    kartı GÖNDERİLMEZ; önce düzeltilip tekrar gate'e girmesi gerekir.

    soft_notes ayrı tutulur (olası tekrar + konu/görsel aile baskınlığı):
    bunlar TEK BAŞINA passed'i False yapmaz. "Otomatik elenmez, insan
    gözden geçirmeli" ilkesi gereği, bu notları taşıyan bir fikir yine de
    onay kartına gider ama kartta uyarı olarak görünür — nihai karar
    insana kalır.
    """
    reasons: List[str] = []

    missing = _missing_fields(idea)
    if missing:
        reasons.append(f"Eksik zorunlu alan(lar): {', '.join(missing)}")

    vf = idea.get("visual_family", "")
    if vf and vf not in VISUAL_FAMILIES:
        reasons.append(f"Geçersiz görsel aile: '{vf}'. Beklenen: {', '.join(sorted(VISUAL_FAMILIES))}")

    sp = idea.get("site_pillar", "")
    if sp and sp not in SITE_PILLARS:
        reasons.append(f"Geçersiz site pillar: '{sp}'. Beklenen: {', '.join(sorted(SITE_PILLARS))}")

    et = idea.get("evidence_type", "")
    if et and et not in EVIDENCE_TYPES:
        reasons.append(f"Geçersiz kanıt türü: '{et}'. Beklenen: {', '.join(sorted(EVIDENCE_TYPES))}")

    if et == "kaynaklı dış bilgi" and not str(idea.get("evidence_source", "")).strip():
        reasons.append("Kanıt türü 'kaynaklı dış bilgi' ama evidence_source boş.")

    caption = f"{idea.get('caption_draft') or ''} {idea.get('hook_text') or ''}"
    caption_lower = caption.lower()

    for phrase in BANNED_PHRASES:
        if phrase in caption_lower:
            reasons.append(f"Yasaklı ifade tespit edildi: '{phrase}' (editoryal ses kuralına aykırı).")

    if NUMERIC_CLAIM_PATTERN.search(caption) and et not in ("kaynaklı dış bilgi", "doğrulanmış müşteri vakası"):
        reasons.append(
            "Kaynaksız sayısal/yüzde iddiası tespit edildi; evidence_type bunu desteklemiyor "
            "(quality-v1.0.md 'Doğrudan ret')."
        )

    if et == "açıkça etiketli temsili senaryo":
        if not any(tag in caption_lower for tag in ("temsili", "örnek akış", "örnek senaryo", "örnek karar")):
            reasons.append(
                "Kanıt türü 'temsili senaryo' ama metinde görünür bir "
                "'Temsili senaryo / örnek akış' etiketi yok."
            )

    soft_notes: List[str] = []
    if recent_ideas:
        dupes = _duplicate_candidates(idea, recent_ideas)
        if dupes:
            dupe_ids = ", ".join(str(d.get("content_id") or d.get("id")) for d in dupes)
            soft_notes.append(
                f"Olası tekrar: son kayıtlarda benzer problem+mekanizma+çıkarım üçlüsü var "
                f"({dupe_ids}). Otomatik elenmez, insan gözden geçirmeli."
            )
        soft_notes.extend(_recency_dominance_notes(idea, recent_ideas))

    return len(reasons) == 0, reasons, soft_notes
