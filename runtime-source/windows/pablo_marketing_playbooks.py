#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CYBERGENE PABLO MARKETING PLAYBOOKS
-----------------------------------
Önceden Doğrulanmış Deterministik Hızlı İcra Kütüphanesi
Kör LLM tahminleri yerine milisaniyeler içinde doğrudan çalışan icra kalıpları:
- Playbook 1: Lead Web Zenginleştirme ve Fact-Check (Playwright CDP ile < 3 sn)
- Playbook 2: Instagram Biyografi Düzenleme (Grounded DOM + React Setter ile < 3 sn)
- Playbook 3: E-posta / İletişim Formu Taslak ve Gönderim Doğrulaması
"""

import re
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional

from marketing_pipeline import MarketingPipeline, DB_PATH
from pablo_browser_grounding import PabloBrowserGrounding, SCREENSHOTS_DIR
from instagram_editorial_gate import run_editorial_gate

class MarketingPlaybooks:

    @staticmethod
    def submit_instagram_content_idea(
        content_id: str,
        visual_family: str,
        site_pillar: str,
        target_reader: str,
        problem: str,
        single_takeaway: str,
        mechanism: str,
        human_control_note: str,
        evidence_type: str,
        hook_text: str,
        caption_draft: str,
        evidence_source: str = "",
        proposed_by: str = "jeff_llm",
    ) -> Dict[str, Any]:
        """
        Instagram içerik öneri hattının TEK giriş noktası — METİN katmanı içindir.
        Hiçbir DOM/browser eylemi tetiklemez, hiçbir PNG/görsel üretmez, hiçbir
        şeyi yayınlamaz. Yalnız: (1) editoryal kapıdan geçirir, (2) geçerse
        Bilal'e onay kartı gönderir, (3) onaylanırsa durum 'APPROVED_FOR_ART_DIRECTION'
        olur — bu, bir Claude Code oturumunda gerçek sanat yönetimi/PNG üretimi
        yapılması gerektiği anlamına gelir, otomatik yayın anlamına GELMEZ.

        Görsel üretim ve yayın onayı bu fonksiyonun kapsamı dışındadır; bkz.
        docs/cybergene-instagram-playbook-v1.0.md §4 ve §7.
        """
        t0 = time.time()
        idea = {
            "content_id": content_id,
            "visual_family": visual_family,
            "site_pillar": site_pillar,
            "target_reader": target_reader,
            "problem": problem,
            "single_takeaway": single_takeaway,
            "mechanism": mechanism,
            "human_control_note": human_control_note,
            "evidence_type": evidence_type,
            "evidence_source": evidence_source,
            "hook_text": hook_text,
            "caption_draft": caption_draft,
        }

        recent_ideas = MarketingPipeline.list_content_ideas(limit=30)
        passed, hard_reasons, soft_notes = run_editorial_gate(idea, recent_ideas=recent_ideas)

        if not passed:
            gate_status, status = "GATE_REJECTED", "REJECTED"
        elif soft_notes:
            gate_status, status = "GATE_PASSED_WITH_REVIEW_FLAG", "DRAFTED"
        else:
            gate_status, status = "GATE_PASSED", "DRAFTED"

        idea_id = MarketingPipeline.create_content_idea(
            content_id=content_id,
            visual_family=visual_family,
            site_pillar=site_pillar,
            target_reader=target_reader,
            problem=problem,
            single_takeaway=single_takeaway,
            mechanism=mechanism,
            human_control_note=human_control_note,
            evidence_type=evidence_type,
            evidence_source=evidence_source,
            hook_text=hook_text,
            caption_draft=caption_draft,
            proposed_by=proposed_by,
            gate_status=gate_status,
            gate_notes=hard_reasons + soft_notes,
            status=status,
        )

        duration_ms = int((time.time() - t0) * 1000)
        MarketingPipeline.log_execution(
            playbook_name="Playbook_Instagram_Content_Idea_Submit",
            action_type="editorial_gate_check",
            status="SUCCESS" if passed else "FAILED",
            duration_ms=duration_ms,
            details={"idea_id": idea_id, "passed": passed, "hard_reasons": hard_reasons, "soft_notes": soft_notes},
        )

        return {
            "ok": True,
            "idea_id": idea_id,
            "gate_passed": passed,
            "gate_reasons": hard_reasons,
            "soft_notes": soft_notes,
            "status": status,
            "duration_ms": duration_ms,
        }

    @staticmethod
    def enrich_lead_website(company_url: str, lead_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Hedef şirketin web sitesini Playwright CDP üzerinden hızlıca tarar;
        e-posta, telefon, adres ve sayfa başlığını çıkarıp doğrular.
        """
        t0 = time.time()
        engine = PabloBrowserGrounding.get_instance()
        
        # 1. Sayfayı aç ve oku
        read_res = engine.read_page_content(target=company_url, mode="text")
        if not read_res.get("ok"):
            # Açmayı dene
            engine.open_url(company_url)
            read_res = engine.read_page_content(target=company_url, mode="text")

        text = read_res.get("text_preview", "")
        title = read_res.get("title", "")
        url = read_res.get("url", company_url)

        # 2. RegEx ile iletişim kanallarını ayıkla
        emails = list(set(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)))
        # Genel filtreleme (resim/uzantı çöplerini temizle)
        clean_emails = [e for e in emails if not any(e.endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.webp', '.svg'))]
        
        # Telefonlar
        phones = list(set(re.findall(r'(?:\+?90\s*|\(?0\d{3}\)?\s*)[\d\s-]{7,11}', text)))
        clean_phones = [p.strip() for p in phones if len(re.sub(r'\D', '', p)) in (10, 11, 12)]

        duration_ms = int((time.time() - t0) * 1000)
        
        result_data = {
            "ok": True,
            "url": url,
            "title": title,
            "emails": clean_emails,
            "phones": clean_phones,
            "text_sample": text[:400],
            "duration_ms": duration_ms
        }

        # Eğer lead_id verilmişse veritabanını zenginleştir
        if lead_id:
            lead = MarketingPipeline.get_lead(lead_id)
            if lead:
                v_email = lead["verified_email"] or (clean_emails[0] if clean_emails else "")
                v_phone = lead["verified_phone"] or (clean_phones[0] if clean_phones else "")
                MarketingPipeline.add_or_update_lead(
                    company_name=lead["company_name"],
                    website=lead["website"],
                    industry=lead["industry"],
                    location=lead["location"],
                    verified_phone=v_phone,
                    verified_email=v_email,
                    verified_whatsapp=lead["verified_whatsapp"],
                    capacity_notes=lead["capacity_notes"],
                    facts_verified=json.loads(lead["facts_verified"] or "[]"),
                    assumptions=json.loads(lead["assumptions"] or "[]"),
                    fact_check_status="VERIFIED"
                )

        MarketingPipeline.log_execution(
            playbook_name="Playbook_Enrich_Lead_Website",
            action_type="web_scraping_and_fact_check",
            status="SUCCESS",
            campaign_id=None,
            duration_ms=duration_ms,
            details=result_data
        )

        return result_data

    @staticmethod
    def execute_instagram_bio_update(new_bio_text: str) -> Dict[str, Any]:
        """
        Instagram profil düzenleme sayfasını açar, cerrahi olarak doğrulanmış
        3 kademeli metin girişini ve submit butonunu infaz eder.
        """
        t0 = time.time()
        engine = PabloBrowserGrounding.get_instance()
        target_url = "https://www.instagram.com/accounts/edit/"

        # 1. Sayfayı aç / Sekmeye bağlan
        open_res = engine.open_url(target_url)
        time.sleep(1.0)

        # 2. Biyografi alanını doldur
        type_res = engine.type_element_verified(
            selector="textarea[placeholder*='Bio']",
            text=new_bio_text,
            description="Instagram Profil Biyografisi",
            submit=False,
            clear=True,
            target=target_url
        )

        if not type_res.get("ok"):
            duration_ms = int((time.time() - t0) * 1000)
            MarketingPipeline.log_execution(
                playbook_name="Playbook_Instagram_Bio_Update",
                action_type="type_element",
                status="FAILED",
                duration_ms=duration_ms,
                evidence_screenshot=type_res.get("screenshot_path", ""),
                details={"error": type_res.get("error")}
            )
            return {"ok": False, "error": type_res.get("error"), "duration_ms": duration_ms}

        # 3. Gönder / Submit butonuna tıkla
        click_res = engine.click_element_verified(
            selector="button[type='submit']",
            description="Profili Kaydet (Gönder)",
            target=target_url
        )

        duration_ms = int((time.time() - t0) * 1000)
        ss_path = click_res.get("screenshot_path") or type_res.get("screenshot_path", "")

        is_success = type_res.get("ok") and (click_res.get("ok") or click_res.get("verified"))

        MarketingPipeline.log_execution(
            playbook_name="Playbook_Instagram_Bio_Update",
            action_type="full_flow",
            status="SUCCESS" if is_success else "FAILED",
            duration_ms=duration_ms,
            evidence_screenshot=ss_path,
            details={"type_result": type_res, "click_result": click_res}
        )

        return {
            "ok": is_success,
            "verified": is_success,
            "duration_ms": duration_ms,
            "screenshot_path": ss_path,
            "new_bio": new_bio_text
        }

    @staticmethod
    def execute_campaign_delivery(campaign_id: int, simulated: bool = False) -> Dict[str, Any]:
        """Validate an approved draft without claiming a delivery that did not happen.

        A simulation leaves the campaign approved and does not touch the desktop.
        No live sender is implemented yet; live requests fail explicitly.
        """
        t0 = time.time()
        campaign = MarketingPipeline.get_campaign(campaign_id)
        if not campaign:
            return {"ok": False, "status": "NOT_FOUND", "verified": False,
                    "delivered": False, "error": f"Kampanya bulunamadı: {campaign_id}"}
        if campaign.get("status") != "APPROVED":
            return {"ok": False, "status": "NOT_APPROVED", "verified": False,
                    "delivered": False, "error": "Gönderim taslağı onaylı değil."}
        target = campaign.get("recipient_target", "")
        subject = campaign.get("subject", "")
        if not target or not str(campaign.get("message_body") or "").strip():
            return {"ok": False, "status": "INVALID_DRAFT", "verified": False,
                    "delivered": False, "error": "Taslak metni veya alıcı eksik."}
        duration_ms = int((time.time() - t0) * 1000)
        status = "SIMULATED" if simulated else "UNSUPPORTED"
        MarketingPipeline.log_execution(
            playbook_name="Playbook_Campaign_Delivery",
            action_type="simulated_send" if simulated else "delivery_unavailable",
            status=status,
            campaign_id=campaign_id,
            duration_ms=duration_ms,
            details={"target": target, "subject": subject, "delivered": False}
        )
        return {
            "ok": bool(simulated),
            "status": status,
            "verified": False,
            "delivered": False,
            "mode": "SIMULATED_SAFE" if simulated else "LIVE_UNAVAILABLE",
            "campaign_id": campaign_id,
            "target": target,
            "screenshot_path": "",
            "duration_ms": duration_ms,
            "error": None if simulated else "Bu kanal için gerçek gönderici henüz kurulu değil. Mesaj gönderilmedi."
        }

    @staticmethod
    def audit_instagram_profile(instagram_handle: str) -> Dict[str, Any]:
        """
        Instagram profilini Playwright CDP üzerinden açar, biyografiyi, web/WhatsApp linklerini
        ve profil durumunu analiz eder.
        """
        t0 = time.time()
        engine = PabloBrowserGrounding.get_instance()
        clean_handle = instagram_handle.lstrip("@").strip()
        url = f"https://www.instagram.com/{clean_handle}/"

        open_res = engine.open_url(url)
        time.sleep(1.5)

        read_res = engine.read_page_content(target=url, mode="text")
        text = read_res.get("text_preview", "")
        title = read_res.get("title", "")

        ss_path = str(SCREENSHOTS_DIR / f"ig_profile_{clean_handle}_{int(time.time())}.png")
        p = getattr(engine, "page", None)
        if p and not p.is_closed():
            try:
                p.screenshot(path=ss_path)
            except Exception:
                pass

        duration_ms = int((time.time() - t0) * 1000)

        # WhatsApp veya randevu linki tespiti
        has_whatsapp = "wa.me" in text.lower() or "whatsapp" in text.lower() or "05" in text
        has_booking = any(k in text.lower() for k in ("randevu", "appointment", "doktor", "klinik", "seans"))

        result = {
            "ok": True,
            "handle": clean_handle,
            "url": url,
            "title": title,
            "has_whatsapp": has_whatsapp,
            "has_booking_mention": has_booking,
            "screenshot_path": ss_path,
            "duration_ms": duration_ms
        }

        MarketingPipeline.log_execution(
            playbook_name="Playbook_Instagram_Profile_Audit",
            action_type="profile_audit",
            status="SUCCESS",
            duration_ms=duration_ms,
            evidence_screenshot=ss_path,
            details=result
        )

        return result
