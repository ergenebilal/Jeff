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
            "value_prop": "Gelen mesajları karşılayan, randevu talebini toparlayıp onayınıza sunan dijital çalışan."
        },
        "medical_aesthetic": {
            "name": "Medikal Estetik & Dermatoloji & Saç Ekim",
            "ticket_level": "ÇOK YÜKSEK (10.000 - 80.000 TL / işlem)",
            "keywords": ["estetik klinik", "dermatoloji", "saç ekimi", "botoks", "medikal estetik"],
            "pain_point": "Instagram reklamlarından gelen yüzlerce 'fiyat nedir' DM'ine personelin yetişememesi ve sıcak hastaların soğuması.",
            "value_prop": "Fiyat ve işlem sorularını karşılayıp ön bilgiyi toplayan, uzman görüşmesi talebini size sunan dijital çalışan."
        },
        "beauty_center": {
            "name": "Lüks Güzellik Merkezleri & Cilt Bakımı",
            "ticket_level": "ORTA-YÜKSEK (4.000 - 25.000 TL / paket)",
            "keywords": ["güzellik merkezi", "lazer epilasyon", "cilt bakımı", "bölgesel incelme"],
            "pain_point": "Hafta sonu yoğunluğunda telefona bakılamaması ve paket satış randevularının sekreteryada aksaması.",
            "value_prop": "Randevu taleplerini toparlayan, hatırlatmaları hazırlayıp onayınıza sunan dijital çalışan."
        }
    }

    SITE = "https://cybergene.co"
    DEFAULT_QUESTION = "Mesai dışı gelen randevu mesajlarını nasıl karşılarsınız?"

    @staticmethod
    def showroom_link(display_name: str, question: str = "") -> str:
        """Personal showroom link. The site itself sanitises `for` (40 chars) and `soru` (300 chars);
        we apply the same limits here so the link always renders as intended."""
        name = re.sub(r"[^\w .,'&-]", "", display_name or "", flags=re.UNICODE).strip()[:40]
        ask = " ".join((question or ClinicLeadHunter.DEFAULT_QUESTION).split())[:300]
        query = urllib.parse.urlencode({"for": name, "soru": ask}, quote_via=urllib.parse.quote)
        return f"{ClinicLeadHunter.SITE}/showroom/?{query}"

    @staticmethod
    def generate_clinic_pitch(
        company_name: str,
        niche_key: str,
        contact_person: Optional[str] = None,
        instagram_handle: Optional[str] = None,
        display_name: Optional[str] = None,
        question: str = "",
    ) -> Dict[str, str]:
        """First-contact draft. It only states what is true: no statistics, no invented past work,
        no speed promises. It always goes through human approval before anything is sent."""
        niche = ClinicLeadHunter.NICHE_CATEGORIES.get(niche_key, ClinicLeadHunter.NICHE_CATEGORIES["dental"])
        hitap = f"Merhaba {contact_person}," if contact_person else f"Merhaba {company_name} ekibi,"
        link = ClinicLeadHunter.showroom_link(display_name or company_name, question)
        subject = f"{company_name} için kısa bir örnek ekran"
        body = (
            f"{hitap}\n\n"
            f"Ben Bilal, CyberGene'den yazıyorum. İşletmelere özel dijital çalışanlar kuruyoruz: "
            f"gelen mesajları karşılayan, randevu talebini toparlayıp size sunan, işi mesai dışında da hazır tutan "
            f"yardımcılar. Son karar her zaman sizde kalır.\n\n"
            f"Sizin gibi bir işletmede nasıl çalışabileceğini gösteren bir örnek ekran hazırladık "
            f"(temsili bir örnektir, gerçek bir işlem yapmaz):\n{link}\n\n"
            f"Beğenirseniz, işinizde hangi işlerin devredilebileceğine birlikte bakacağımız ücretsiz bir ön görüşme "
            f"önerebiliriz. Yanıt vermeniz gerekmiyor; ilginizi çekmezse bu mesajı yok sayabilirsiniz.\n\n"
            f"İyi çalışmalar,\nBilal Ergene — CyberGene\n{ClinicLeadHunter.SITE}"
        )
        review=MarketingPipeline.review_message(body,company_name)
        return {"subject":subject,"body":review.get('suggested_body',body),"raw_body":body,
                "customer_review":review,"ready_for_founder_review":review.get('ready_for_founder_review') is True,
                "ready_for_send":False,"value_prop":niche["value_prop"]}


    @staticmethod
    def quick_radar(candidates: List[Dict[str, Any]], limit: int = 10) -> Dict[str, Any]:
        """One bounded public business-page check; no reviews/LLM/deep work."""
        import urllib.request
        import socket
        import ipaddress
        from html.parser import HTMLParser
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):return None
        class Links(HTMLParser):
            def __init__(self):super().__init__();self.links=[];self.text=[]
            def handle_starttag(self,tag,attrs):
                if tag=='a':
                    a=dict(attrs)
                    if a.get('href'):self.links.append(a['href'])
            def handle_data(self,data):self.text.append(data)
        def note_for(lead):
            raw=lead.get('capacity_notes') or ''
            try:
                val=json.loads(raw)
                return val if isinstance(val,dict) else {'previous_notes':raw}
            except (ValueError,TypeError):return {'previous_notes':raw} if raw else {}
        clean=[];skipped=[];seen=set();day=time.strftime('%Y-%m-%d');limit=max(1,min(int(limit),10))
        existing=MarketingPipeline.list_leads();used=sum(note_for(l).get('radar_day')==day for l in existing)
        remaining=max(0,limit-used);opener=urllib.request.build_opener(NoRedirect())
        for candidate in candidates[:50]:
            if len(clean)>=remaining:break
            start=time.monotonic();name=' '.join(str(candidate.get('company_name','')).split())[:120]
            website=str(candidate.get('website','')).strip();district=str(candidate.get('district','')).casefold().replace('i̇','i')
            if not name or district not in ('nilüfer','nilufer','mudanya') or website in seen:continue
            seen.add(website);parsed=urllib.parse.urlparse(website)
            prior=next((l for l in existing if l['company_name'].casefold()==name.casefold() or l.get('website','').rstrip('/')==website.rstrip('/')),None)
            if prior and note_for(prior).get('radar_day')==day:continue
            if prior:name=prior['company_name']
            try:
                if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password:raise ValueError('Public business source required')
                addresses=socket.getaddrinfo(parsed.hostname,parsed.port or (443 if parsed.scheme=='https' else 80),type=socket.SOCK_STREAM)
                if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):raise ValueError('Public business source required')
                if parsed.hostname.casefold().endswith(('instagram.com','facebook.com','google.com')):raise ValueError('Authorized platform feed required; no profile scraping')
                request=urllib.request.Request(website,headers={'User-Agent':'CyberGene business contact check','Accept':'text/html'})
                with opener.open(request,timeout=10) as response:
                    if 'html' not in response.headers.get('Content-Type','').lower():raise ValueError('Business HTML page required')
                    raw=response.read(512001)
                    if len(raw)>512000:raise ValueError('Page exceeds bounded contact check')
                    text=raw.decode('utf-8',errors='replace');source=response.geturl()
                parser=Links();parser.feed(text);visible=' '.join(parser.text).casefold().replace('i̇','i')
                district_words=('nilüfer','nilufer') if district in ('nilüfer','nilufer') else ('mudanya','bademli')
                name_words=[w.casefold() for w in name.split() if len(w)>3 and w.casefold() not in ('bursa','kliniği','güzellik','merkezi','estetik','clinic')]
                if not any(d in visible for d in district_words) or not name_words or not any(w in visible for w in name_words):raise ValueError('Business identity/location not observed on source page')
                links=[urllib.parse.urljoin(source,x) for x in parser.links]
                whatsapp=next((x for x in links if urllib.parse.urlparse(x).hostname in ('wa.me','api.whatsapp.com','web.whatsapp.com')),'')
                instagram=next((x for x in links if (urllib.parse.urlparse(x).hostname or '').casefold() in ('instagram.com','www.instagram.com')),'')
                phone=next((x[4:] for x in links if x.startswith('tel:')),'')
                appointment=next((x for x in links if any(k in x.casefold() for k in ('randevu','appointment','booking','booknow'))),'')
                direct=bool(whatsapp or appointment);contact='direct_link' if direct else 'phone_only' if phone else 'instagram_link_only'
                if not (whatsapp or phone or instagram):raise ValueError('No clean contact observed')
                elapsed=time.monotonic()-start
                if elapsed>=60:raise TimeoutError('Single contact check exceeded limit')
                meta={'stage':'radar','radar_day':day,'source':source,'observed_at':time.time(),'district':district,
                      'instagram':instagram,'whatsapp':whatsapp,'phone':phone,'appointment_link':appointment,
                      'contact_mode':contact,'single_check_seconds':round(elapsed,3),'model_calls':0,'loss_verified':False,
                      'dm_availability_verified':False,'source_presence_only':True}
                preserved=note_for(prior or {});preserved.update(meta)
                lead_id=MarketingPipeline.add_or_update_lead(company_name=name,website=source,
                    industry=(prior or {}).get('industry') or str(candidate.get('industry','beauty_or_clinic')),location=(prior or {}).get('location') or 'Bursa / '+district,
                    verified_phone=phone or (prior or {}).get('verified_phone') or '',verified_whatsapp=whatsapp or (prior or {}).get('verified_whatsapp') or '',verified_email=(prior or {}).get('verified_email') or '',
                    capacity_notes=json.dumps(preserved,ensure_ascii=False),
                    facts_verified=json.loads((prior or {}).get('facts_verified') or '[]')+[{'level':'OBSERVED','source':source,'claim':'Business identity, district and contact link observed','observed_at':meta['observed_at']}],
                    assumptions=json.loads((prior or {}).get('assumptions') or '[]'),fact_check_status=(prior or {}).get('fact_check_status') or 'CONTACT_OBSERVED')
                clean.append({'lead_id':lead_id,'company_name':name,**meta})
            except (OSError,ValueError,TimeoutError) as exc:skipped.append({'company_name':name,'reason':type(exc).__name__})
        return {'ok':True,'stage':'radar','candidates':clean,'clean_count':len(clean),'skipped':skipped,
                'daily_limit':limit,'already_observed_today':used,'model_calls':0,'deep_analysis_triggered':False}

    @staticmethod
    def seed_initial_verified_clinics():
        """Bursa Nilüfer / FSM / Osmangazi ve İstanbul'daki lüks klinik ve güzellik merkezlerini boru hattına ekler."""
        # 29.09.2026 kontrolü: bu örnek kayıtlar doğrulanamadı (iki alan adı hiç yok, biri başka şehirlerde,
        # biri sitesinde Bursa şubesi göstermiyor). Doğrulanmadan boru hattına konmaz; aday listesi resmî
        # kaynaklardan (radar) doğrulanarak üretilecek.
        return []

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
                fact_check_status="UNVERIFIED"
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
