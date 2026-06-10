#!/usr/bin/env python3
"""Strategy Planner — uzun vadeli hedefleri haftalık/günlük aksiyonlara böler.
Predictive Engine + Decision Engine kullanarak stratejik plan oluşturur."""

import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

PLANS_PATH = os.path.expanduser("~/.hermes/brain/strategy_plans.json")
TZ = timezone(timedelta(hours=3))


def _load_plans() -> List[Dict]:
    """Kayıtlı planları yükle."""
    if not os.path.exists(PLANS_PATH):
        return []
    try:
        with open(PLANS_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_plans(plans: List[Dict]) -> None:
    """Planları kaydet."""
    os.makedirs(os.path.dirname(PLANS_PATH), exist_ok=True)
    with open(PLANS_PATH, "w") as f:
        json.dump(plans, f, indent=2, ensure_ascii=False)


def create_plan(goal: str, deadline_days: int = 30,
                weekly_budget_usd: float = 5.0) -> Dict:
    """Uzun vadeli bir hedefi haftalık aksiyonlara böl.
    
    Args:
        goal: Hedef (örn: "Bu ay Gumroad'dan $500 kazan")
        deadline_days: Gün sayısı
        weekly_budget_usd: Haftalık token bütçesi
    
    Returns:
        Plan dict
    """
    now = datetime.now(TZ)
    deadline = now + timedelta(days=deadline_days)
    hafta_sayisi = max(1, deadline_days // 7)
    haftalik_hedef = 1.0 / hafta_sayisi

    # Predictive engine'den genel örüntüleri al
    try:
        from predictive_engine import analyze_patterns
        patterns = analyze_patterns()
    except ImportError:
        patterns = {}

    weekly_actions = []
    for i in range(hafta_sayisi):
        week_start = now + timedelta(weeks=i)
        week_end = now + timedelta(weeks=i + 1) - timedelta(seconds=1)

        # Her hafta için hedef yüzdesi
        progress_target = min(1.0, (i + 1) * haftalik_hedef)

        # Haftalık aksiyonlar (hedef türüne göre)
        actions = _generate_weekly_actions(goal, i + 1, hafta_sayisi)

        weekly_actions.append({
            "hafta": i + 1,
            "baslangic": week_start.isoformat(),
            "bitis": week_end.isoformat(),
            "hedef_yuzde": round(progress_target * 100),
            "aksiyonlar": actions,
            "butce": round(weekly_budget_usd, 2),
        })

    plan = {
        "id": f"plan_{now.strftime('%Y%m%d_%H%M%S')}",
        "hedef": goal,
        "olusturulma": now.isoformat(),
        "son_tarih": deadline.isoformat(),
        "gun_sayisi": deadline_days,
        "haftalik_butce": weekly_budget_usd,
        "haftalik_plan": weekly_actions,
        "tamamlanma_yuzde": 0,
        "aktif": True,
    }

    plans = _load_plans()
    plans.append(plan)
    _save_plans(plans)

    return plan


def _generate_weekly_actions(goal: str, week_num: int,
                              total_weeks: int) -> List[Dict]:
    """Hedefe göre haftalık aksiyonlar üret."""
    goal_lower = goal.lower()
    
    actions = []

    # Varsayılan aksiyonlar
    if "gumroad" in goal_lower or "sat" in goal_lower or "kazan" in goal_lower:
        if week_num == 1:
            actions = [
                {"aksiyon": "Mevcut ürünleri gözden geçir", "sure_dk": 30, "kritik": True},
                {"aksiyon": "1 yeni ürün konsepti oluştur", "sure_dk": 45, "kritik": True},
                {"aksiyon": "Landing page metni yaz", "sure_dk": 60, "kritik": False},
            ]
        elif week_num <= total_weeks // 2:
            actions = [
                {"aksiyon": "Ürünleri güncelle ve iyileştir", "sure_dk": 45, "kritik": True},
                {"aksiyon": "Sosyal medyada tanıtım yap", "sure_dk": 30, "kritik": False},
                {"aksiyon": "Outreach mesajları hazırla", "sure_dk": 40, "kritik": True},
            ]
        else:
            actions = [
                {"aksiyon": "Satış kanallarını optimize et", "sure_dk": 30, "kritik": True},
                {"aksiyon": "Müşteri yorumlarını topla", "sure_dk": 20, "kritik": False},
                {"aksiyon": "Fiyatlandırmayı güncelle", "sure_dk": 15, "kritik": False},
            ]
    
    elif "kod" in goal_lower or "yaz" in goal_lower or "geliştir" in goal_lower:
        if week_num == 1:
            actions = [
                {"aksiyon": "Proje planı oluştur", "sure_dk": 30, "kritik": True},
                {"aksiyon": "Temel yapıyı kur", "sure_dk": 60, "kritik": True},
            ]
        elif week_num <= total_weeks // 2:
            actions = [
                {"aksiyon": "Çekirdek modülleri yaz", "sure_dk": 60, "kritik": True},
                {"aksiyon": "Testleri yaz", "sure_dk": 30, "kritik": True},
            ]
        else:
            actions = [
                {"aksiyon": "Hata düzeltme ve optimizasyon", "sure_dk": 45, "kritik": True},
                {"aksiyon": "Deploy ve dokümantasyon", "sure_dk": 30, "kritik": False},
            ]

    elif "twitter" in goal_lower or "x" in goal_lower or "sosyal" in goal_lower:
        if week_num == 1:
            actions = [
                {"aksiyon": "Hesap ayarlarını yap", "sure_dk": 20, "kritik": True},
                {"aksiyon": "İlk 5 tweet taslağı yaz", "sure_dk": 30, "kritik": True},
            ]
        else:
            actions = [
                {"aksiyon": "Günlük paylaşım programı oluştur", "sure_dk": 15, "kritik": True},
                {"aksiyon": "Etkileşim analizi yap", "sure_dk": 20, "kritik": False},
            ]

    elif "instagram" in goal_lower or "ig" in goal_lower:
        if week_num == 1:
            actions = [
                {"aksiyon": "İçerik takvimi oluştur", "sure_dk": 30, "kritik": True},
                {"aksiyon": "İlk 3 post tasarla", "sure_dk": 60, "kritik": True},
            ]
        else:
            actions = [
                {"aksiyon": "Haftalık post planla", "sure_dk": 25, "kritik": True},
                {"aksiyon": "DM asistanını test et", "sure_dk": 20, "kritik": False},
            ]

    else:
        # Genel hedef
        actions = [
            {"aksiyon": f"Hedef analizi yap: {goal[:30]}", "sure_dk": 30, "kritik": True},
            {"aksiyon": "İlk adımı belirle ve uygula", "sure_dk": 45, "kritik": True},
            {"aksiyon": "İlerlemeyi değerlendir", "sure_dk": 15, "kritik": False},
        ]

    return actions


def get_weekly_plan() -> Optional[Dict]:
    """Bu hafta için aktif planı döndür."""
    plans = _load_plans()
    now = datetime.now(TZ)
    
    for plan in plans:
        if not plan.get("aktif"):
            continue
        for hafta in plan.get("haftalik_plan", []):
            try:
                baslangic = datetime.fromisoformat(hafta["baslangic"])
                bitis = datetime.fromisoformat(hafta["bitis"])
                if baslangic <= now <= bitis:
                    return {
                        "hedef": plan["hedef"],
                        "hafta": hafta["hafta"],
                        "toplam_hafta": len(plan["haftalik_plan"]),
                        "aksiyonlar": hafta["aksiyonlar"],
                        "butce": hafta["butce"],
                        "ilerleme": plan.get("tamamlanma_yuzde", 0),
                    }
            except (ValueError, KeyError):
                continue
    
    return None


def update_progress(plan_id: str, yuzde: int) -> bool:
    """Bir planın tamamlanma yüzdesini güncelle."""
    plans = _load_plans()
    for plan in plans:
        if plan.get("id") == plan_id:
            plan["tamamlanma_yuzde"] = min(100, max(0, yuzde))
            if yuzde >= 100:
                plan["aktif"] = False
            _save_plans(plans)
            return True
    return False


def list_active_plans() -> List[Dict]:
    """Aktif planları listele."""
    return [p for p in _load_plans() if p.get("aktif")]


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 2 and sys.argv[1] == "create":
        goal = " ".join(sys.argv[2:])
        plan = create_plan(goal)
        print(f"Plan oluşturuldu: {plan['id']}")
        print(f"Hedef: {plan['hedef']}")
        print(f"Süre: {plan['gun_sayisi']} gün, {len(plan['haftalik_plan'])} hafta")
        for h in plan['haftalik_plan'][:3]:  # İlk 3 hafta
            print(f"\n  Hafta {h['hafta']}:")
            for a in h['aksiyonlar']:
                print(f"    {'🔴' if a['kritik'] else '🟢'} {a['aksiyon']} ({a['sure_dk']}dk)")
    
    elif len(sys.argv) > 1 and sys.argv[1] == "current":
        w = get_weekly_plan()
        if w:
            print(f"Bu hafta: {w['hedef'][:50]}...")
            print(f"Hafta {w['hafta']}/{w['toplam_hafta']} | İlerleme: %{w['ilerleme']}")
            for a in w['aksiyonlar']:
                print(f"  {'🔴' if a['kritik'] else '🟢'} {a['aksiyon']} ({a['sure_dk']}dk)")
        else:
            print("Aktif plan yok.")
    
    else:
        print("Kullanım:")
        print("  create <hedef>   — Yeni stratejik plan oluştur")
        print("  current          — Bu haftanın planını göster")
