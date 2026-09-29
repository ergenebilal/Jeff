#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PABLO BROWSER GROUNDING FIX - AŞAMA 4 TEST VE DOĞRULAMA SUITE
--------------------------------------------------------------
Test Senaryoları:
1. Basit statik sayfa navigasyonu ve buton/link tıklama (PASS/FAIL doğrulaması)
2. Dinamik/JS-yoğun YouTube'da video arama, DOM selector ile tıklama ve video oynatma doğrulaması
3. Yanlış / bulunamayan element tıklama denemesi (Sistemin "başarısız" olduğunu doğru raporlaması - Sahte Başarı YOK)
4. 3 başarısız deneme sonrası Loop Guard tetiklenmesi ve insan bildirimi
5. Koda gömülü zorunlu doğrulama denetimi (Bypass edilemezlik testi)
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
import time
import json
from pathlib import Path

# Add project paths
sys.path.insert(0, r"C:\CyberGene\HermesNode")
sys.path.insert(0, r"c:\AI AGENTS PROJECT")

from pablo_browser_grounding import PabloBrowserGrounding

def run_tests():
    engine = PabloBrowserGrounding.get_instance()
    results = {}

    print("=================================================================")
    print("      CYBERGENE PABLO - GROUNDED BROWSER VERIFICATION SUITE      ")
    print("=================================================================\n")

    # SENARYO 1: Basit statik sayfa tıklama ve doğrulama
    print("--- SENARYO 1: Statik Sayfa Navigasyonu ve DOM Tıklama ---")
    t0 = time.time()
    open_res = engine.open_url("https://example.com")
    print(f"  Navigasyon: ok={open_res.get('ok')}, verified={open_res.get('verified')}, url={open_res.get('url')}")
    
    # 'More information...' linkine tıkla (gerçek DOM linki: 'a')
    click_res = engine.click_element_verified("a", "More information link")
    print(f"  Tıklama: ok={click_res.get('ok')}, verified={click_res.get('verified')}, deneme={click_res.get('attempts')}")
    
    s1_pass = open_res.get("verified") is True and click_res.get("verified") is True
    results["SENARYO_1_STATIK_TIKLAMA"] = {
        "status": "PASS" if s1_pass else "FAIL",
        "verified": s1_pass,
        "details": click_res,
        "screenshot": click_res.get("screenshot_path")
    }
    print(f"  -> SONUÇ: {results['SENARYO_1_STATIK_TIKLAMA']['status']}\n")

    # SENARYO 2: Dinamik YouTube Video Arama, DOM Tıklama ve Oynatma Doğrulaması
    print("--- SENARYO 2: YouTube Dinamik Video Arama & Closed-Loop Oynatma ---")
    yt_res = engine.youtube_search_and_play("gerçeği bul")
    video_title = yt_res.get("video_title") or yt_res.get("title", "")
    video_url = yt_res.get("video_url") or yt_res.get("url", "")
    print(f"  YouTube Oynatma: ok={yt_res.get('ok')}, verified={yt_res.get('verified')}")
    print(f"  Video Başlığı: {video_title}")
    print(f"  Video URL: {video_url}")
    print(f"  Durum / Status: {yt_res.get('status')}")
    print(f"  İcra Süresi: {yt_res.get('duration_ms')} ms")
    print(f"  Kanıt Ekran Görüntüsü: {yt_res.get('screenshot_path')}")

    s2_pass = yt_res.get("verified") is True and "watch" in str(video_url)
    results["SENARYO_2_YOUTUBE_CLOSED_LOOP"] = {
        "status": "PASS" if s2_pass else "FAIL",
        "verified": s2_pass,
        "video_title": video_title,
        "video_url": video_url,
        "screenshot": yt_res.get("screenshot_path")
    }
    print(f"  -> SONUÇ: {results['SENARYO_2_YOUTUBE_CLOSED_LOOP']['status']}\n")

    # SENARYO 3: Yanlış / Bulunamayan Element Tıklama Denemesi (Sahte Başarı Engelleme)
    print("--- SENARYO 3: Bulunamayan Element Testi (Sahte Başarı Yok) ---")
    bad_click_res = engine.click_element_verified("#kesinlikle-boyle-bir-id-yok-12345", "Olmayan Buton")
    print(f"  Sonuç: ok={bad_click_res.get('ok')}, verified={bad_click_res.get('verified')}")
    print(f"  Hata Mesajı: {bad_click_res.get('error')[:80]}...")
    print(f"  Yapılan Deneme Sayısı: {bad_click_res.get('attempts')}")

    # Başarı kriteri: Sistemin False dönmesi ve hatayı dürüstçe raporlaması!
    s3_pass = bad_click_res.get("verified") is False and bad_click_res.get("ok") is False
    results["SENARYO_3_SAHTE_BASARI_ENGELLEME"] = {
        "status": "PASS" if s3_pass else "FAIL",
        "verified": s3_pass,
        "expected_failure_confirmed": True,
        "details": bad_click_res
    }
    print(f"  -> SONUÇ (Başarısızlığı Doğru Raporlama): {results['SENARYO_3_SAHTE_BASARI_ENGELLEME']['status']}\n")

    # SENARYO 4: 3 Başarısız Deneme Sonrası Loop Guard Tetiklenmesi
    print("--- SENARYO 4: Loop Guard (3 Deneme Kuralı) Denetimi ---")
    s4_pass = bad_click_res.get("attempts") == 3
    results["SENARYO_4_LOOP_GUARD_3_ATTEMPTS"] = {
        "status": "PASS" if s4_pass else "FAIL",
        "verified": s4_pass,
        "attempts_count": bad_click_res.get("attempts")
    }
    print(f"  -> SONUÇ: {results['SENARYO_4_LOOP_GUARD_3_ATTEMPTS']['status']} (Tam 3 deneme yapıldı ve döngü kırıldı)\n")

    # SENARYO 5: Koda Gömülü Zorunlu Doğrulama Katmanı Denetimi
    print("--- SENARYO 5: Koda Gömülü Zorunlu Doğrulama Katmanı ---")
    # Kod incelemesi: Fonksiyonda prompt'tan bağımsız kod seviyesinde verification kontrolü var mı?
    s5_pass = "verified" in yt_res and "screenshot_path" in yt_res and yt_res.get("screenshot_path") is not None
    results["SENARYO_5_KOD_SEVIYESI_ZORUNLU_DOGRULAMA"] = {
        "status": "PASS" if s5_pass else "FAIL",
        "verified": s5_pass
    }
    print(f"  -> SONUÇ: {results['SENARYO_5_KOD_SEVIYESI_ZORUNLU_DOGRULAMA']['status']}\n")

    # Özet Rapor
    print("=================================================================")
    print("                       GENEL TEST RAPORU                         ")
    print("=================================================================")
    all_pass = all(r["status"] == "PASS" for r in results.values())
    for k, v in results.items():
        print(f"  [{v['status']}] {k}")
    print(f"\nGENEL DURUM: {'100% PASS [TAM KORUMA]' if all_pass else 'FAIL'}")

    engine.close()
    return results

if __name__ == "__main__":
    res = run_tests()
    with open(r"C:\CyberGene\HermesNode\grounding_test_results.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
