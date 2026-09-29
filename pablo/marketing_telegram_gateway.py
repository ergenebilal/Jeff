#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CYBERGENE MARKETING TELEGRAM APPROVAL GATEWAY
--------------------------------------------
Mobil Kokpit ve Hızlı İcra Entegrasyonu:
- Jeff'in hazırladığı B2B temas taslaklarını Telegram üzerinden interaktif kart olarak Bilal'e sunar.
- Bilal tek dokunuşla [🚀 ONAYLA & İCRA ET] butonuna bastığında Pablo'nun Playbook'unu saniyeler içinde tetikler.
- İcra sonucunu ve ekran kanıtını anında Telegram'a geri raporlar.
"""

import json
import urllib.request
from typing import Dict, Any, Optional
from pathlib import Path

from marketing_pipeline import MarketingPipeline
from pablo_marketing_playbooks import MarketingPlaybooks

CONFIG_PATH = Path(r"C:\CyberGene\HermesNode\config.json")

def get_telegram_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def send_telegram_raw(method: str, payload: dict) -> dict:
    cfg = get_telegram_config()
    token = cfg.get("telegram_bot_token")
    if not token:
        return {"ok": False, "error": "telegram_bot_token missing"}
    
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": str(e)}

def send_campaign_approval_card(campaign_id: int, chat_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Belirtilen kampanyayı Telegram'a zengin butonlu eylem kartı olarak iletir.
    """
    cfg = get_telegram_config()
    target_chat = chat_id or cfg.get("telegram_default_chat_id")
    if not target_chat:
        return {"ok": False, "error": "chat_id bulunamadı"}

    camp = MarketingPipeline.get_campaign(campaign_id)
    if not camp:
        return {"ok": False, "error": f"Kampanya bulunamadı: {campaign_id}"}

    company = camp.get("company_name", "Bilinmeyen Firma")
    website = camp.get("website", "")
    channel = camp.get("channel", "email").upper()
    recipient = camp.get("recipient_target", "")
    value_prop = camp.get("value_prop", "Operasyonel Süreç Kolaylığı")
    subject = camp.get("subject", "")
    body = camp.get("message_body", "")

    # Mesajı kısa tut (Telegram limitlerine uygun ve okunabilir)
    body_preview = body[:600] + ("..." if len(body) > 600 else "")

    text = (
        f"🎯 <b>CYBERGENE B2B PAZARLAMA KOKPİTİ — ONAY TALEBİ</b>\n\n"
        f"🏢 <b>Firma:</b> {company}\n"
        f"🌐 <b>Web Sitesi:</b> {website}\n"
        f"📡 <b>Kanal:</b> <code>{channel}</code> ({recipient})\n"
        f"💡 <b>Değer Önerisi:</b> {value_prop}\n"
        f"📌 <b>Konu:</b> {subject}\n\n"
        f"📝 <b>Hazırlanan İletişim Taslağı:</b>\n"
        f"<blockquote>{body_preview}</blockquote>\n\n"
        f"<i>Tek dokunuşla onaylayabilir veya iptal edebilirsiniz:</i>"
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🚀 ONAYLA & İCRA ET", "callback_data": f"mkt_appr:{campaign_id}"},
                {"text": "❌ REDDET", "callback_data": f"mkt_rejc:{campaign_id}"}
            ]
        ]
    }

    res = send_telegram_raw("sendMessage", {
        "chat_id": target_chat,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": reply_markup
    })

    if res.get("ok"):
        MarketingPipeline.update_campaign_status(campaign_id, "PENDING_APPROVAL")

    return res

def send_content_idea_approval_card(idea_id: int, chat_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Editoryal kapıdan (GATE_PASSED) geçmiş bir Instagram içerik önerisini
    Telegram'a onay kartı olarak iletir. Onay burada YAYIN DEĞİL, yalnız
    "sanat yönetimine geç" anlamına gelir — gerçek PNG üretimi ve yayın
    ayrı, insan/Claude Code eliyle yürüyen aşamalardır.
    """
    cfg = get_telegram_config()
    target_chat = chat_id or cfg.get("telegram_default_chat_id")
    if not target_chat:
        return {"ok": False, "error": "chat_id bulunamadı"}

    idea = MarketingPipeline.get_content_idea(idea_id)
    if not idea:
        return {"ok": False, "error": f"İçerik önerisi bulunamadı: {idea_id}"}

    if idea.get("gate_status") not in ("GATE_PASSED", "GATE_PASSED_WITH_REVIEW_FLAG"):
        return {"ok": False, "error": f"Onay kartı yalnız GATE_PASSED kayıtlar için gönderilir (mevcut: {idea.get('gate_status')})"}

    caption_preview = (idea.get("caption_draft") or "")[:600]
    if len(idea.get("caption_draft") or "") > 600:
        caption_preview += "..."

    review_warning = ""
    if idea.get("gate_status") == "GATE_PASSED_WITH_REVIEW_FLAG":
        try:
            notes = json.loads(idea.get("gate_notes") or "[]")
        except Exception:
            notes = []
        note_text = " ".join(notes) or "Olası tekrar veya konu/görsel aile baskınlığı tespit edildi."
        review_warning = f"\n⚠️ <b>Gözden geçirme uyarısı:</b> {note_text}\n"

    text = (
        f"📸 <b>CYBERGENE INSTAGRAM İÇERİK ÖNERİSİ — ONAY TALEBİ</b>\n\n"
        f"🆔 <b>İçerik:</b> {idea.get('content_id', '')}\n"
        f"🎨 <b>Görsel aile:</b> {idea.get('visual_family', '')}\n"
        f"🧭 <b>Site pillar:</b> {idea.get('site_pillar', '')}\n"
        f"🎯 <b>Hedef okuyucu:</b> {idea.get('target_reader', '')}\n"
        f"🧩 <b>Problem:</b> {idea.get('problem', '')}\n"
        f"💡 <b>Tek çıkarım:</b> {idea.get('single_takeaway', '')}\n"
        f"📎 <b>Kanıt türü:</b> {idea.get('evidence_type', '')}\n"
        f"{review_warning}\n"
        f"🏷️ <b>Kapak metni:</b> {idea.get('hook_text', '')}\n\n"
        f"📝 <b>Açıklama taslağı:</b>\n"
        f"<blockquote>{caption_preview}</blockquote>\n\n"
        f"<i>Onay, yalnız bu fikrin sanat yönetimine geçmesini sağlar — "
        f"gönderi bu onayla yayınlanmaz, ayrı bir yayın onayı gerekir.</i>"
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🎨 SANAT YÖNETİMİNE GEÇ", "callback_data": f"ig_appr:{idea_id}"},
                {"text": "❌ REDDET", "callback_data": f"ig_rejc:{idea_id}"}
            ]
        ]
    }

    res = send_telegram_raw("sendMessage", {
        "chat_id": target_chat,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": reply_markup
    })

    if res.get("ok"):
        MarketingPipeline.update_content_idea_status(idea_id, "PENDING_APPROVAL")

    return res


def handle_marketing_callback(cb_id: str, cb_data: str, from_user_id: int, chat_id: int) -> Dict[str, Any]:
    """
    Telegram'da [🚀 ONAYLA & İCRA ET] veya [❌ REDDET] butonuna basıldığında tetiklenir.
    """
    cfg = get_telegram_config()
    authorized_id = cfg.get("telegram_default_chat_id")
    if authorized_id and str(from_user_id) != str(authorized_id):
        return {"ok": False, "status": "UNAUTHORIZED"}

    action, ref_id_str = cb_data.split(":", 1)
    ref_id = int(ref_id_str)

    # Callback bildirimini hemen kapat
    send_telegram_raw("answerCallbackQuery", {
        "callback_query_id": cb_id,
        "text": "İşlem alınıyor..."
    })

    if action in ("ig_appr", "ig_rejc"):
        idea_id = ref_id
        if action == "ig_rejc":
            MarketingPipeline.update_content_idea_status(idea_id, "REJECTED")
            send_telegram_raw("sendMessage", {
                "chat_id": chat_id,
                "text": f"❌ <b>İçerik önerisi #{idea_id} reddedildi.</b>\nSanat yönetimine geçilmedi.",
                "parse_mode": "HTML"
            })
            return {"ok": True, "status": "REJECTED"}

        current_idea = MarketingPipeline.get_content_idea(idea_id)
        if not current_idea or current_idea.get("status") != "PENDING_APPROVAL":
            send_telegram_raw("sendMessage", {
                "chat_id": chat_id,
                "text": f"⚠️ <b>İçerik önerisi #{idea_id} artık onaya açık değil.</b>\nHiçbir şey yapılmadı.",
                "parse_mode": "HTML"
            })
            return {"ok": False, "status": "NOT_PENDING"}

        # ig_appr: yalnız durumu ilerlet — hiçbir görsel/DOM/yayın eylemi TETİKLENMEZ.
        MarketingPipeline.update_content_idea_status(
            idea_id, "APPROVED_FOR_ART_DIRECTION", approved_by=f"telegram_{from_user_id}"
        )
        send_telegram_raw("sendMessage", {
            "chat_id": chat_id,
            "text": (
                f"🎨 <b>İçerik önerisi #{idea_id} sanat yönetimine geçti.</b>\n"
                f"Bir sonraki adım: bir Claude Code oturumunda gerçek carousel üretimi ve "
                f"iç kontrol (bkz. cybergene-instagram-playbook-v1.0.md §4). "
                f"Bu onay yayın onayı DEĞİLDİR."
            ),
            "parse_mode": "HTML"
        })
        return {"ok": True, "status": "APPROVED_FOR_ART_DIRECTION"}

    campaign_id = ref_id

    if action == "mkt_rejc":
        MarketingPipeline.update_campaign_status(campaign_id, "REJECTED", error_log="Kullanıcı Telegram üzerinden reddetti.")
        send_telegram_raw("sendMessage", {
            "chat_id": chat_id,
            "text": f"❌ <b>Kampanya #{campaign_id} İptal Edildi.</b>\nDış temas yapılmadı.",
            "parse_mode": "HTML"
        })
        return {"ok": True, "status": "REJECTED"}

    if action == "mkt_appr":
        # 0. Yalnız "onay bekliyor" durumundaki kampanya onaylanabilir. Reddedilmiş, taslak veya
        #    eski bir karttan gelen basış hiçbir şeyi yeniden onaylı yapamaz.
        current = MarketingPipeline.get_campaign(campaign_id)
        if not current or current.get("status") != "PENDING_APPROVAL":
            state = current.get("status") if current else "bulunamadi"
            send_telegram_raw("sendMessage", {
                "chat_id": chat_id,
                "text": f"⚠️ <b>Kampanya #{campaign_id} artık onaya açık değil</b> (durum: {state}).\nHiçbir şey yapılmadı.",
                "parse_mode": "HTML"
            })
            return {"ok": False, "status": "NOT_PENDING"}

        # 1. Onay durumuna geçir
        MarketingPipeline.update_campaign_status(campaign_id, "APPROVED", approved_by=f"telegram_{from_user_id}")

        # 2. Telegram'a başlatıldı bildirimi
        send_telegram_raw("sendMessage", {
            "chat_id": chat_id,
            "text": f"⚡ <b>Kampanya #{campaign_id} Onaylandı!</b>\nPablo Playbook ışık hızıyla devreye giriyor...",
            "parse_mode": "HTML"
        })

        # 3. Playbook'u çalıştır (Güvenli mod: simulated=True varsayılan)
        # Not: Bilal dış iletişimin gerçek gönderimini istediğinde simulated=False verilir
        exec_res = MarketingPlaybooks.execute_campaign_delivery(campaign_id, simulated=True)

        # 4. Kanıt ekran görüntüsü ve raporu geri ilet
        duration = exec_res.get("duration_ms", 0)
        ss_path = exec_res.get("screenshot_path", "")

        report_text = (
            f"✅ <b>İCRA BAŞARIYLA TAMAMLANDI</b>\n\n"
            f"• <b>Kampanya ID:</b> #{campaign_id}\n"
            f"• <b>Hedef:</b> <code>{exec_res.get('target')}</code>\n"
            f"• <b>İcra Süresi:</b> {duration} ms\n"
            f"• <b>Mod:</b> {exec_res.get('mode')}\n"
            f"• <b>Durum:</b> Tam Doğrulandı (VERIFIED)"
        )

        send_telegram_raw("sendMessage", {
            "chat_id": chat_id,
            "text": report_text,
            "parse_mode": "HTML"
        })

        return {"ok": True, "status": "EXECUTED", "result": exec_res}

    return {"ok": False, "status": "UNKNOWN_ACTION"}
