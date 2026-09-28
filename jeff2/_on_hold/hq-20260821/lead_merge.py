import json

# 22 Haziran lead'leri
leads_june22 = [
    {"company":"BLACK GYM","phone":"+90 530 078 95 00","email":"info@blackgym.com.tr","source":"Google Maps/Instagram","priority":"HIGH","website":"https://blackgym.com.tr","instagram":"@blackgymconcept","notes":"Nilüfer premium spor salonu"},
    {"company":"CaddePlus Coffee & Game Lounge","phone":"+90 534 244 72 76","email":None,"source":"Google Maps/Instagram","priority":"HIGH","website":"https://www.caddeplus16.com","instagram":"@caddeplus16","notes":"Nilüfer yeni nesil kafe"},
    {"company":"Hovarda Bursa (Delice Meyhane)","phone":"+90 532 781 12 33","email":None,"source":"Instagram","priority":"MEDIUM","website":"https://hovardabursa.com","instagram":"@hovardabursa","notes":"Bademli eğlence mekanı"},
    {"company":"İncir Cafe Mudanya","phone":"+90 224 544 91 95","email":None,"source":"Google Maps","priority":"HIGH","website":None,"instagram":"@incircafemudanya","notes":"Mudanya kafe, web sitesi yok"},
    {"company":"Nilüfer Burhan Balıkçılık","phone":"+90 545 368 22 00","email":None,"source":"Google Maps","priority":"CRITICAL","website":"https://www.niluferburhanbalikcilik.com","instagram":None,"notes":"Instagram yok, web zayıf"},
    {"company":"Mudanya Çiftliği (Gurme)","phone":"+90 544 665 16 16","email":None,"source":"Google Maps","priority":"HIGH","website":None,"instagram":"@mudanyaciftligigurme","notes":"Gurme market, web sitesi yok"},
    {"company":"Barber Plus","phone":"+90 537 449 26 35","email":None,"source":"Google Maps","priority":"CRITICAL","website":None,"instagram":None,"notes":"Sıfır dijital varlık"},
    {"company":"Mudanya Tarım Market","phone":"+90 532 156 39 99","email":None,"source":"Instagram","priority":"HIGH","website":None,"instagram":"@mudanya_tarim_market","notes":"Tarım market, web yok"},
    {"company":"Nilüfer Makina","phone":"+90 541 360 45 95","email":"c.ozdemir@nilufermakina.com","source":"Web","priority":"CRITICAL","website":"https://nilufermakina.com","instagram":None,"notes":"Google Maps kaydı yok"},
    {"company":"Özhan Market Nilüfer","phone":None,"email":None,"source":"Yerel Haber","priority":"MEDIUM","website":None,"instagram":None,"notes":"Zincir market yeni şube"},
    {"company":"Nilüfer Boğaz Cafe","phone":None,"email":None,"source":"Instagram","priority":"MEDIUM","website":None,"instagram":"@niluferbogaz","notes":"43K takipçi, web yok"},
    {"company":"Next Fitness Club","phone":None,"email":None,"source":"Web","priority":"HIGH","website":"https://nextfitnessclub.com","instagram":None,"notes":"Sosyal medya zayıf"},
]

# 29 Haziran lead'leri
leads_june29 = [
    {"company":"Beko Bayisi Mudanya","phone":None,"email":None,"source":"Yerel Haber","priority":"HIGH","website":None,"instagram":None,"notes":"18 Haziran'da açıldı"},
    {"company":"Nework Smart Working Cafe","phone":None,"email":None,"source":"Yerel Haber","priority":"CRITICAL","website":None,"instagram":None,"notes":"Yeni nesil kafe, web yok"},
    {"company":"Anaduyu Ergoterapi ve Dil Konuşma Merkezi","phone":None,"email":None,"source":"Yerel Haber","priority":"CRITICAL","website":None,"instagram":None,"notes":"Sağlık merkezi, sıfır dijital"},
    {"company":"Mudanya Petshop","phone":"0551 634 31 44","email":None,"source":"Google Maps","priority":"CRITICAL","website":"mudanyapetshop.com","instagram":None,"notes":"Web zayıf, Instagram yok"},
    {"company":"Mudanya Zeytin Kooperatifi Mağazası","phone":None,"email":None,"source":"Yerel Haber","priority":"CRITICAL","website":None,"instagram":None,"notes":"Dijital sıfır"},
    {"company":"MayKa - Bir Dilim Balkan","phone":None,"email":None,"source":"Yerel Haber","priority":"HIGH","website":None,"instagram":None,"notes":"Balkan mutfağı"},
    {"company":"Afize Restoran","phone":None,"email":None,"source":"Yerel Haber","priority":"HIGH","website":None,"instagram":None,"notes":"Downtown Bursa AVM"},
    {"company":"Çıtır Ekmek - Konya Etli Ekmek","phone":None,"email":None,"source":"Yerel Haber","priority":"HIGH","website":None,"instagram":None,"notes":"Yeni restoran"},
    {"company":"Minty 23 Nisan","phone":"+90 507 096 7051","email":None,"source":"Google Maps","priority":"MEDIUM","website":None,"instagram":None,"notes":"Kafe/nargile"},
    {"company":"Rokaru Kitchen","phone":"+90 505 757 2626","email":None,"source":"Google Maps","priority":"HIGH","website":None,"instagram":None,"notes":"Asya mutfağı"},
    {"company":"Evidea Ata Bulvarı","phone":None,"email":None,"source":"Yerel Haber","priority":"LOW","website":None,"instagram":None,"notes":"Kurumsal marka"},
    {"company":"Kantin Nilüfer","phone":None,"email":None,"source":"Web","priority":"MEDIUM","website":None,"instagram":None,"notes":"Belediye iştiraki"},
    {"company":"Taze Dükkan","phone":None,"email":None,"source":"Web","priority":"MEDIUM","website":None,"instagram":None,"notes":"Sağlıklı beslenme"},
    {"company":"Nilbel Kafe 29 Ekim","phone":None,"email":None,"source":"Web","priority":"LOW","website":None,"instagram":None,"notes":"Belediye iştiraki"},
    {"company":"Mudanya Kehribar","phone":None,"email":None,"source":"Google Maps","priority":"HIGH","website":"mudanyakehribar.com","instagram":None,"notes":"Doğal kehribar takı"},
]

all_leads = leads_june22 + leads_june29
priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
all_leads.sort(key=lambda x: priority_order.get(x["priority"], 99))

with open("/home/hermes/jeff2/hq/lead_pipeline_1.jsonl", "w") as f:
    for lead in all_leads:
        f.write(json.dumps(lead, ensure_ascii=False) + "\n")

print(f"✅ {len(all_leads)} lead CRM'e kaydedildi")
print(f"   🔴 CRITICAL: {sum(1 for l in all_leads if l['priority']=='CRITICAL')}")
print(f"   🟡 HIGH: {sum(1 for l in all_leads if l['priority']=='HIGH')}")
print(f"   🟢 MEDIUM: {sum(1 for l in all_leads if l['priority']=='MEDIUM')}")
print(f"   ⚪ LOW: {sum(1 for l in all_leads if l['priority']=='LOW')}")
print(f"   📧 Email var: {sum(1 for l in all_leads if l['email'])}")
print(f"   📞 Telefon var: {sum(1 for l in all_leads if l['phone'])}")
print(f"   ❌ Hiç iletişim yok: {sum(1 for l in all_leads if not l['email'] and not l['phone'])}")
