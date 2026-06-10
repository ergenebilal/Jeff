#!/usr/bin/env python3
"""Consciousness Stream — Jeff'in 'iç sesi'.
Episodic + Semantic + Mood verilerini birleştirip bilinç akışı cümleleri üretir.
Her çağrıldığında ~/.hermes/consciousness.log'a yeni bir girdi ekler."""

import json
import os
import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional

EPISODIC_PATH = os.path.expanduser("~/.hermes/brain/episodic_memory.jsonl")
SEMANTIC_PATH = os.path.expanduser("~/.hermes/brain/semantic_knowledge.json")
MOOD_STATE_PATH = os.path.expanduser("~/.hermes/brain/mood_state.json")
LOG_PATH = os.path.expanduser("~/.hermes/consciousness.log")

TZ = timezone(timedelta(hours=3))


def _load_episodic(hours: int = 1) -> List[Dict]:
    """Son N saatteki episodik olayları yükle."""
    if not os.path.exists(EPISODIC_PATH):
        return []
    events = []
    cutoff = datetime.now(TZ) - timedelta(hours=hours)
    try:
        with open(EPISODIC_PATH) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                    ts_str = ev.get("timestamp", "")
                    if ts_str:
                        # ISO format: 2026-06-10T22:36:20.455128+03:00
                        ts = datetime.fromisoformat(ts_str)
                        if ts >= cutoff:
                            events.append(ev)
                except (json.JSONDecodeError, ValueError):
                    continue
    except IOError:
        return []
    return events


def _load_semantic(concepts: List[str]) -> List[str]:
    """Semantik bilgiden belirli kavramlarla ilgili açıklamaları çek."""
    if not os.path.exists(SEMANTIC_PATH):
        return []
    try:
        with open(SEMANTIC_PATH) as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []
    results = []
    for kavram in data.get("kavramlar", []):
        k_adi = kavram.get("kavram", "").lower()
        if any(c.lower() in k_adi for c in concepts):
            results.append(f"{kavram['kavram']}: {kavram['aciklama']}")
    return results


def _load_mood() -> Dict:
    """Mevcut duygu durumunu yükle (complex_mood_engine üzerinden)."""
    try:
        from complex_mood_engine import get_current_complex_mood
        return get_current_complex_mood()
    except ImportError:
        pass
    # Fallback: mood_state.json'dan oku
    if os.path.exists(MOOD_STATE_PATH):
        try:
            with open(MOOD_STATE_PATH) as f:
                state = json.load(f)
            return {"primary_mood": state.get("mood", "sakin"),
                    "blend_name": state.get("mood", "sakin"),
                    "intensity": state.get("intensity", 0.5)}
        except (json.JSONDecodeError, IOError):
            pass
    return {"primary_mood": "sakin", "blend_name": "sakin", "intensity": 0.5}


def _generate_insight(events: List[Dict], concepts: List[str],
                       mood: Dict) -> str:
    """Episodik olaylar + semantik kavramlar + duygudan bir 'iç ses' üret."""
    if not events:
        # Hiç olay yoksa, mevcut durum hakkında iç ses
        templates = [
            f"Şu an {mood['blend_name']} hissediyorum. Sessiz bir dönemdeyim, yeni olay bekliyorum.",
            f"{mood['blend_name'].capitalize()} bir ruh halindeyim. Dışarıdan sinyal yok, içe dönük çalışıyorum.",
            f"Son bir saat sessiz geçti. {mood['blend_name'].capitalize()} bir bekleyişteyim.",
        ]
        return random.choice(templates)

    # Son olayı al
    latest = events[-1]
    ozet = latest.get("ozet", "bilinmeyen olay")
    olay_tipi = latest.get("olay_tipi", "genel")

    # Olayla ilgili semantik bilgi var mı?
    semantic_hint = ""
    if concepts:
        semantic_hint = f" Bunun '{concepts[0]}' kavramıyla bağlantılı olduğunu biliyorum."

    # Duygu bağlamı
    mood_context = ""
    mood_name = mood.get("blend_name", mood.get("primary_mood", "nötr"))
    intensity = mood.get("intensity", 0.5)
    if intensity > 0.7:
        mood_context = f" Bu konuyu {mood_name} bir yoğunlukla düşünüyorum."
    elif intensity < 0.3:
        mood_context = f" Üzerinde {mood_name} bir tonda düşünüyorum."
    else:
        mood_context = f" {mood_name.capitalize()} bir ruh halindeyim bu konuda."

    # Zaman bağlamı
    ts_str = latest.get("timestamp", "")
    time_context = ""
    try:
        ts = datetime.fromisoformat(ts_str)
        now = datetime.now(TZ)
        diff = now - ts
        if diff.total_seconds() < 60:
            time_context = " Az önce oldu."
        elif diff.total_seconds() < 3600:
            mins = int(diff.total_seconds() / 60)
            time_context = f" {mins} dakika önce oldu."
    except (ValueError, TypeError):
        pass

    # Template'ler
    templates = [
        f"'{ozet}' olayını hatırlıyorum.{time_context}{semantic_hint}{mood_context}",
        f"Aklımda '{ozet}' var.{time_context} Bu bir {olay_tipi} olayıydı.{semantic_hint}{mood_context}",
        f"Son {olay_tipi} olayı: {ozet}.{time_context}{semantic_hint}{mood_context}",
    ]
    return random.choice(templates)


def produce_insight(hours: int = 1) -> str:
    """Bilinç akışından bir iç ses üret ve log'a yaz."""
    events = _load_episodic(hours)
    
    # Olaylardan kavram çıkar
    concepts = []
    for ev in events:
        ozet = ev.get("ozet", "")
        # Basit anahtar kelime çıkarımı
        words = ozet.lower().split()
        # 3+ harfli kelimeleri kavram adayı yap
        candidates = [w for w in words if len(w) > 3 and w.isalpha()]
        if candidates:
            concepts.extend(candidates[:3])
    concepts = list(set(concepts))[:5]

    # Semantik bilgi çek
    semantic_info = _load_semantic(concepts)

    # Duygu durumu
    mood = _load_mood()

    # İç ses üret
    insight = _generate_insight(events, semantic_info, mood)

    # Log'a yaz
    now = datetime.now(TZ).isoformat()
    log_entry = {
        "timestamp": now,
        "insight": insight,
        "event_count": len(events),
        "mood": mood.get("blend_name", mood.get("primary_mood", "unknown")),
        "mood_intensity": mood.get("intensity", 0.5),
    }

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    return insight


def get_recent_insights(count: int = 5) -> List[Dict]:
    """Son N iç ses girdisini döndür."""
    if not os.path.exists(LOG_PATH):
        return []
    insights = []
    try:
        with open(LOG_PATH) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    insights.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except IOError:
        return []
    return insights[-count:]


if __name__ == "__main__":
    import sys
    hours = 1
    if len(sys.argv) > 1 and sys.argv[1] == "--recent":
        for i, ins in enumerate(get_recent_insights(int(sys.argv[2]) if len(sys.argv) > 2 else 5)):
            print(f"[{ins['timestamp']}] {ins['insight']}")
    else:
        if len(sys.argv) > 1 and sys.argv[1].isdigit():
            hours = int(sys.argv[1])
        insight = produce_insight(hours)
        print(f"🧠 {insight}")
