#!/usr/bin/env python3
"""Decision Engine — çok kriterli karar ağacı + basit MCTS.
Mevcut autonomy_policy.py'yi tamamlar."""
import json
import math
import random
from typing import Any, Optional

__all__ = [
    "evaluate_action", "simulate_scenarios", "post_mortem",
    "get_decision_history", "MCTSScenario",
]


def evaluate_action(action: str, token_maliyeti: float = 0,
                    potansiyel_kazanc: float = 0,
                    acil_mi: bool = False,
                    tekrarlanabilir_mi: bool = False,
                    bilal_istedi_mi: bool = False) -> dict[str, Any]:
    """Bir aksiyonu çok kriterli değerlendir. 0-1 arası puan döndürür."""
    skor: float = 0.0
    gerekceler: list[str] = []

    # Fayda/Maliyet oranı
    if token_maliyeti > 0 and potansiyel_kazanc > 0:
        fm_oran: float = min(potansiyel_kazanc / token_maliyeti, 2.0) / 2.0
        skor += fm_oran * 0.3
        gerekceler.append(f"fayda/maliyet oranı: {fm_oran:.2f}")

    # Aciliyet
    if acil_mi:
        skor += 0.3
        gerekceler.append("acil: +0.3")

    # Tekrarlanabilirlik
    if tekrarlanabilir_mi:
        skor += 0.2
        gerekceler.append("tekrarlanabilir: +0.2")

    # Bilal isteği
    if bilal_istedi_mi:
        skor += 0.2
        gerekceler.append("Bilal istedi: +0.2")

    # Default minimum
    if skor == 0:
        skor = 0.3
        gerekceler.append("default: +0.3")

    return {"action": action, "skor": round(min(skor, 1.0), 2), "gerekceler": gerekceler}


class MCTSScenario:
    """Basit MCTS — bir problemi 3-4 senaryoyla simüle et."""

    def __init__(self, problem: str):
        self.problem: str = problem
        self.scenarios: list[dict[str, Any]] = []

    def add_scenario(self, ad: str, adimlar: list[str],
                     basari_orani: float, sure_dk: int,
                     risk_seviyesi: str = "düşük") -> None:
        """Senaryo ekle. basari_orani: 0-1 arası."""
        self.scenarios.append({
            "ad": ad,
            "adimlar": adimlar,
            "basari_orani": basari_orani,
            "sure_dk": sure_dk,
            "risk_seviyesi": risk_seviyesi,
            "maliyet_puani": round((1 - basari_orani) * sure_dk / 10, 2),
        })

    def recommend(self) -> dict[str, Any]:
        """En iyi senaryoyu öner (başarı/süre oranına göre)."""
        if not self.scenarios:
            return {"ad": "senaryo yok"}

        best: Optional[dict[str, Any]] = None
        best_score: float = -1

        for s in self.scenarios:
            # Başarı/süre oranı, risk cezası
            risk_cezasi: float = {"düşük": 0, "orta": 0.1, "yüksek": 0.3}.get(s["risk_seviyesi"], 0)
            score: float = (s["basari_orani"] * 10) / max(s["sure_dk"], 1) - risk_cezasi
            if score > best_score:
                best_score = score
                best = s

        return best or self.scenarios[0]

    def report(self) -> str:
        """Tüm senaryoları ve öneriyi içeren rapor."""
        lines: list[str] = [f"Problem: {self.problem}", ""]
        for i, s in enumerate(self.scenarios, 1):
            adim_str: str = " → ".join(s["adimlar"][:3])
            if len(s["adimlar"]) > 3:
                adim_str += f" → +{len(s['adimlar'])-3} adım"
            lines.append(f"{i}. {s['ad']}")
            lines.append(f"   Adımlar: {adim_str}")
            lines.append(f"   Başarı: %{s['basari_orani']*100:.0f} | Süre: {s['sure_dk']}dk | Risk: {s['risk_seviyesi']}")

        best = self.recommend()
        lines.append(f"\nÖneri: {best['ad']}")
        return "\n".join(lines)


_decision_log: list[dict[str, Any]] = []


def post_mortem(karar: str, beklenti: str, gerceklesen: str,
                dogru_muydu: bool, ders: str = "") -> dict[str, Any]:
    """Karar sonrası analiz kaydet."""
    entry: dict[str, Any] = {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "karar": karar,
        "beklenti": beklenti,
        "gerceklesen": gerceklesen,
        "dogru_muydu": dogru_muydu,
        "ders": ders,
    }
    _decision_log.append(entry)

    if not dogru_muydu and ders:
        # Yanlış kararı semantic memory'ye kaydet
        try:
            import sys
            sys.path.insert(0, __import__("os").path.expanduser("~/.hermes/scripts"))
            sm = __import__("semantic_memory")
            sm.learn(f"UYARI: {karar[:40]}", ders, kategori="hata", onem=9)
        except Exception:
            pass

    return entry


def get_decision_history(limit: int = 10) -> list[dict[str, Any]]:
    """Son karar analizlerini getir."""
    return _decision_log[-limit:]


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "evaluate" and len(sys.argv) > 2:
        r = evaluate_action(sys.argv[2])
        print(f"Skor: {r['skor']} | {', '.join(r['gerekceler'])}")
    elif len(sys.argv) > 1 and sys.argv[1] == "simulate" and len(sys.argv) > 2:
        m = MCTSScenario(sys.argv[2])
        m.add_scenario("Hızlı çözüm", ["dene", "kontrol et"], 0.6, 5, "orta")
        m.add_scenario("Güvenli çözüm", ["yedeği al", "dene", "test et", "aktifleştir"], 0.95, 15, "düşük")
        m.add_scenario("Sıfırla", ["dur", "yedekten dön"], 0.7, 30, "yüksek")
        print(m.report())
    else:
        print(f"Kullanım: {sys.argv[0]} [evaluate <action>|simulate <problem>]")
