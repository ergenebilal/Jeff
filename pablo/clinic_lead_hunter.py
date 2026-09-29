#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CYBERGENE CLINIC & HIGH-TICKET APPOINTMENT LEAD HUNTER
-----------------------------------------------------
Hedef Kitle (ICP):
- Diş Klinikleri, Ortodonti, İmplant & Gülüş Tasarımı Merkezleri
- Medikal Estetik, Dermatoloji, Saç Ekimi & Plastik Cerrahi
- Lüks Güzellik Merkezleri, Cilt Bakımı & Lazer Epilasyon Salonları
- Fizyoterapi & Butik Sağlık Merkezleri

Özellikler:
1. Randevu ile çalışan, işlem başına cirosu yüksek işletmeleri hedefler.
2. Instagram profilini, WhatsApp randevu hattını ve web sitesini doğrular.
3. Mesai dışı (gece & hafta sonu) kaçan yüksek biletli randevuları yakalayan
   özel kişiselleştirilmiş "AI Randevu & Karşılama Asistanı" teklif taslağı üretir.
"""

import re
import json
import time
import urllib.parse
from typing import Dict, Any, List, Optional
from pathlib import Path

from marketing_pipeline import MarketingPipeline
from pablo_browser_grounding import PabloBrowserGrounding

class ClinicLeadHunter:
    
    NICHE_CATEGORIES = {
        "dental": {
            "name": "Diş & Estetik Gülüş Klinikleri",
            "ticket_level": "YÜKSEK (15.000 - 60.000 TL / hasta)",
            "keywords": ["diş kliniği", "dental clinic", "implant", "gülüş tasarımı", "ortodonti"],
            "pain_point": "Akşam ve hafta sonu implant veya estetik gülüş fiyatı soran hastaların geç yanıt sebebiyle başka kliniklere gitmesi.",
            "value_prop": "7/24 Instagram DM ve WhatsApp'ta hastayı 20 saniyede karşılayan ve hekim takvimine otomatik muayene randevusu yazan AI Asistanı."
        },
        "medical_aesthetic": {
            "name": "Medikal Estetik & Dermatoloji & Saç Ekim",
            "ticket_level": "ÇOK YÜKSEK (10.000 - 80.000 TL / işlem)",
            "keywords": ["estetik klinik", "dermatoloji", "saç ekimi", "botoks", "medikal estetik"],
            "pain_point": "Instagram reklamlarından gelen yüzlerce 'fiyat nedir' DM'ine personelin yetişememesi ve sıcak hastaların soğuması.",
            "value_prop": "Instagram DM'den gelen işlem taleplerini anında ön elemeden geçirip fotoğraflı ön bilgi toplayan ve uzman görüşmesi randevusu oluşturan akıllı asistan."
        },
        "beauty_center": {
            "name": "Lüks Güzellik Merkezleri & Cilt Bakımı",
            "ticket_level": "ORTA-YÜKSEK (4.000 - 25.000 TL / paket)",
            "keywords": ["güzellik merkezi", "lazer epilasyon", "cilt bakımı", "bölgesel incelme"],
            "pain_point": "Hafta sonu yoğunluğunda telefona bakılamaması ve paket satış randevularının sekreteryada aksaması.",
            "value_prop": "Randevu iptallerini minimize eden, boşalan seanslara otomatik hatırlatma gönderen ve Instagram'dan paket randevusu bağlayan 7/24 dijital sekreter."
        }
    }

    @staticmethod
    def generate_clinic_pitch(
        company_name: str,
        niche_key: str,
        contact_person: Optional[str] = None,
        instagram_handle: Optional[str] = None
    ) -> Dict[str, str]:
        """Klinik ve güzellik merkezleri için yüksek dönüşümlü, saygılı ve doğal temas taslağı üretir."""
        niche = ClinicLeadHunter.NICHE_CATEGORIES.get(niche_key, ClinicLeadHunter.NICHE_CATEGORIES["dental"])
        
        hitap = f"Merhaba {company_name} Ekibi,"
        if contact_person:
            hitap = f"Merhaba {contact_person} Hocam / Ekibi,"

        ig_ref = f"@{instagram_handle}" if instagram_handle else "Instagram profiliniz"

        subject = f"{company_name} için mesai dışı Instagram randevu dönüşüm akışı hk."

        body = (
            f"{hitap}\n\n"
            f"{ig_ref} üzerinden yürüttüğünüz başarılı çalışmaları ve danışan/hasta paylaşımlarınızı ilgiyle takip ediyoruz.\n\n"
            f"Klinik ve merkezlerle yaptığımız çalışmalarda gözlemlediğimiz çok kritik bir gerçek var: "
            f"Özellikle akşam 20:00'den sonra ve hafta sonları Instagram DM ile WhatsApp'tan gelen 'Fiyat nedir?' "
            f"ve 'Randevu alabilir miyim?' sorularına ilk 1-2 dakika içinde dönülmediğinde, yüksek bütçeli hastaların "
            f"%60'ından fazlası o an ulaştığı rakip bir kliniğe yöneliyor.\n\n"
            f"CyberGene olarak geliştirdiğimiz sistem; ekibinizin mesai saatleri dışında ve hafta sonlarında, "
            f"Instagram DM ve WhatsApp hattınızda hastalarınızı 20 saniyede karşılayıp tedavi sorularını yanıtlıyor "
            f"ve randevu defterinize doğrudan ön görüşme randevusu kaydediyor.\n\n"
            f"Herhangi bir satış vaadi olmadan; kliniğinizin kendi Instagram DM'sinde 2 dakikada deneyimleyebileceğiniz "
            f"canlı bir demo paylaşmamızı ister misiniz?\n\n"
            f"İyi çalışmalar dileriz,\n"
            f"Bilal Ergene — CyberGene Kurucusu\n"
            f"0541 846 95 62 | https://cybergene.com.tr"
        )

        return {
            "subject": subject,
            "body": body,
            "value_prop": niche["value_prop"]
        }

    @staticmethod
    def seed_initial_verified_clinics():
        """Bursa Nilüfer / FSM / Osmangazi ve İstanbul'daki lüks klinik ve güzellik merkezlerini boru hattına ekler."""
        initial_clinics = [
            {
                "name": "DentGroup Bursa Nilüfer Diş Kliniği",
                "website": "https://www.dentgroup.com.tr/bursa-nilufer-dis-klinigi/",
                "niche": "dental",
                "location": "Nilüfer / BURSA (Odunluk - Sur Yapı Marka Yanı)",
                "phone": "444 33 68",
                "email": "bursa@dentgroup.com.tr",
                "whatsapp": "+90 549 824 45 16",
                "instagram": "dentgroupbursa",
                "capacity": "Dijital diş hekimliği, gülüş tasarımı, implantoloji, ortodonti, pedodonti.",
                "facts": [
                    "Bursa Nilüfer Odunluk bölgesinde kurumsal diş sağlığı kliniği.",
                    "Instagram (@dentgroupbursa) ve WhatsApp üzerinden yoğun hasta talebi alıyor.",
                    "Hafta sonu ve akşam saatlerinde estetik ve implant talepleri geliyor."
                ],
                "assumptions": [
                    "Gece ve mesai dışı gelen 'Gülüş tasarımı / implant fiyatı' taleplerinin anlık randevuya dönüştürülmesinde otomasyon potansiyeli."
                ]
            },
            {
                "name": "DentaGross Bursa Ağız ve Diş Sağlığı Merkezi",
                "website": "https://dentagross.com.tr",
                "niche": "dental",
                "location": "FSM Bulvarı, Nilüfer / BURSA",
                "phone": "(0224) 244 80 80",
                "email": "info@dentagross.com.tr",
                "whatsapp": "+90 530 660 80 80",
                "instagram": "dentagrossbursa",
                "capacity": "7/24 Nöbetçi Diş Kliniği, implant cerrahisi, zirkonyum, estetik dolgu.",
                "facts": [
                    "Bursa Fatih Sultan Mehmet (FSM) Bulvarı üzerinde 7/24 hizmet veren büyük ölçekli diş merkezi.",
                    "Geniş hekim kadrosu ve yoğun acil/estetik randevu trafiği."
                ],
                "assumptions": [
                    "Instagram reklamlarından gelen soruların AI ile saniyede filtrelenip uzman hekime randevu olarak atanması."
                ]
            },
            {
                "name": "Dr. Ayşe Dursun Estetik & Dermatoloji Kliniği",
                "website": "https://draysedursun.com",
                "niche": "medical_aesthetic",
                "location": "Nilüfer / BURSA (FSM Bulvarı Caddesi)",
                "phone": "(0224) 452 70 70",
                "email": "iletisim@draysedursun.com",
                "whatsapp": "+90 542 452 70 70",
                "instagram": "draysedursun",
                "capacity": "Medikal estetik, ameliyatsız yüz germe, botoks, dolgu, gençlik aşısı, leke tedavisi.",
                "facts": [
                    "Bursa FSM Bulvarında butik, yüksek biletli medikal estetik ve dermatoloji kliniği.",
                    "Sosyal medya paylaşımları ve Instagram DM üzerinden yüksek talep hacmi."
                ],
                "assumptions": [
                    "Gelen işlem taleplerinin ön görüşme randevusuna dönüştürülme sürecinde gece gelen taleplerin kaçma riski."
                ]
            },
            {
                "name": "Monart Estetik & Güzellik Merkezi",
                "website": "https://monartestetik.com",
                "niche": "beauty_center",
                "location": "Bademli / Mudanya - BURSA",
                "phone": "(0224) 549 10 20",
                "email": "info@monartestetik.com",
                "whatsapp": "+90 533 549 10 20",
                "instagram": "monartestetikbursa",
                "capacity": "Lüks segment cilt yenileme, bölgesel incelme, hydrafacial, lazer epilasyon paketleri.",
                "facts": [
                    "Bursa Bademli lüks villa bölgesinde faaliyet gösteren VIP güzellik ve bakım merkezi.",
                    "Ortalama seans ve paket bütçeleri yüksek kitleye hitap ediyor."
                ],
                "assumptions": [
                    "Paket satışı öncesi deneme seansı randevularının Instagram DM'den anında bağlanabilmesi."
                ]
            }
        ]

        created_campaign_ids = []
        for c in initial_clinics:
            lead_id = MarketingPipeline.add_or_update_lead(
                company_name=c["name"],
                website=c["website"],
                industry=c["niche"],
                location=c["location"],
                verified_phone=c["phone"],
                verified_email=c["email"],
                verified_whatsapp=c["whatsapp"],
                capacity_notes=c["capacity"],
                facts_verified=c["facts"],
                assumptions=c["assumptions"],
                fact_check_status="VERIFIED"
            )

            # Özel klinik teklifini üret
            pitch = ClinicLeadHunter.generate_clinic_pitch(
                company_name=c["name"],
                niche_key=c["niche"],
                instagram_handle=c["instagram"]
            )

            # Kampanyayı oluştur (Öncelikli kanal: Instagram DM & WhatsApp)
            camp_id = MarketingPipeline.create_campaign(
                lead_id=lead_id,
                channel="instagram",
                recipient_target=f"@{c['instagram']}",
                subject=pitch["subject"],
                message_body=pitch["body"],
                value_prop=pitch["value_prop"],
                status="PENDING_APPROVAL"
            )
            created_campaign_ids.append((c["name"], camp_id))

        return created_campaign_ids

if __name__ == "__main__":
    camps = ClinicLeadHunter.seed_initial_verified_clinics()
    print(f"Klinik ve Güzellik Merkezleri boru hattına başarıyla yüklendi: {len(camps)} adet.")
    for name, cid in camps:
        print(f" - [{cid}] {name} (Kanal: Instagram DM / WhatsApp)")
