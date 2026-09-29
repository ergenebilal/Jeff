#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CYBERGENE 7/24 AUTONOMOUS MARKETING RUNNER
------------------------------------------
Arka planda otonom olarak:
1. Boru hattındaki müşteri adaylarının web sitelerini doğrular ve zenginleştirir.
2. Kişiselleştirilmiş B2B temas taslaklarını hazırlar.
3. Bilal'in Telegram kokpitine onay kartı gönderir.
4. Onaylanan kampanyaları Playbook üzerinden milisaniyelerde infaz eder.
5. Düzenli KPI durum raporu üretir.
"""

import time
import json
import logging
from pathlib import Path
from typing import Dict, Any

from marketing_pipeline import MarketingPipeline, init_marketing_db
from pablo_marketing_playbooks import MarketingPlaybooks
from marketing_telegram_gateway import send_campaign_approval_card, send_content_idea_approval_card

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
log = logging.getLogger("MarketingRunner")

class AutonomousMarketingRunner:
    def __init__(self, cycle_interval_sec: int = 300):
        init_marketing_db()
        self.interval = cycle_interval_sec
        self.running = True

    def run_single_cycle(self) -> Dict[str, Any]:
        """Tek bir otonom pazarlama döngüsü yürütür."""
        log.info("Otonom Pazarlama Döngüsü Başlatıldı...")
        report = {
            "timestamp": time.time(),
            "leads_enriched": 0,
            "campaigns_queued": 0,
            "approvals_sent": 0,
            "content_ideas_approvals_sent": 0
        }

        # 1. Bekleyen / zenginleştirilmemiş lead'leri bul
        leads = MarketingPipeline.list_leads()
        for lead in leads:
            if not lead["verified_phone"] or not lead["verified_email"]:
                try:
                    log.info(f"Lead zenginleştiriliyor: {lead['company_name']} ({lead['website']})")
                    res = MarketingPlaybooks.enrich_lead_website(lead["website"], lead_id=lead["id"])
                    if res.get("ok"):
                        report["leads_enriched"] += 1
                except Exception as e:
                    log.warning(f"Lead zenginleştirme hatası ({lead['company_name']}): {e}")

        # 2. DRAFTED durumundaki kampanyaları bul ve onay talebi gönder
        campaigns = MarketingPipeline.list_campaigns(status="DRAFTED")
        for camp in campaigns:
            try:
                log.info(f"Onay kartı gönderiliyor: Kampanya #{camp['id']} ({camp['company_name']})")
                card_res = send_campaign_approval_card(camp["id"])
                if card_res.get("ok"):
                    report["approvals_sent"] += 1
            except Exception as e:
                log.warning(f"Onay kartı gönderme hatası (Kampanya #{camp['id']}): {e}")

        # 3. Editoryal kapıyı geçmiş (GATE_PASSED), henüz onaya sunulmamış
        #    Instagram içerik önerilerini bul ve onay kartı gönder.
        #    Bu adım yalnız METİN taslağını Bilal'e iletir; hiçbir görsel
        #    üretmez veya yayınlamaz (bkz. docs/cybergene-instagram-playbook-v1.0.md §7).
        content_ideas = [
            idea for idea in MarketingPipeline.list_content_ideas(status="DRAFTED")
            if idea.get("gate_status") in ("GATE_PASSED", "GATE_PASSED_WITH_REVIEW_FLAG")
        ]
        for idea in content_ideas:
            try:
                log.info(f"Instagram içerik onay kartı gönderiliyor: #{idea['id']} ({idea.get('content_id')})")
                card_res = send_content_idea_approval_card(idea["id"])
                if card_res.get("ok"):
                    report["content_ideas_approvals_sent"] += 1
            except Exception as e:
                log.warning(f"İçerik onay kartı gönderme hatası (#{idea['id']}): {e}")

        log.info(f"Döngü Tamamlandı: {report}")
        return report

    def start_background_loop(self):
        """Sonsuz 7/24 döngü."""
        log.info(f"7/24 Otonom Pazarlama Nöbetçisi Devrede (Aralık: {self.interval} sn)")
        while self.running:
            try:
                self.run_single_cycle()
            except Exception as loop_err:
                log.error(f"Döngü hatası: {loop_err}")
            time.sleep(self.interval)

if __name__ == "__main__":
    runner = AutonomousMarketingRunner(cycle_interval_sec=60)
    # Tek döngü çalıştır ve test et
    runner.run_single_cycle()
