#!/usr/bin/env python3
"""
ErgeneAI Günlük Instagram Carousel Pipeline (v3.0)
Teslimat: önce 5 slide (captionsız), sonra caption ayrı mesaj
"""
import sys, json, os, time, requests, logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/opt/hermes/instagram-pipeline')
from orchestrator import InstagramPipeline

BASE_DIR = Path('/opt/hermes/instagram-pipeline')
STATE_FILE = BASE_DIR / 'output' / 'state' / 'post_tracker.json'
TOKEN = open(os.path.expanduser('~/.hermes/secrets/ig_bot_token.txt')).read().strip()
CHAT_ID = "5506784207"
BOT_API = f"https://api.telegram.org/bot{TOKEN}"

LOG_DIR = BASE_DIR / 'output' / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename=str(LOG_DIR / 'daily_pipeline.log'), level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger('daily_pipeline')


# ============================================================
# CONTENT PLAN — 12 Post
# ============================================================

CONTENT_PLAN = [
    # ─── Post 1: AI Farkındalık ───
    {
        "id": 1, "theme": "AI Farkındalık — Nedir Bu AI?",
        "caption": "<b>Herkes AI Diyor</b>\n\nAI dedikleri şey aslında ne? Koca koca şirketlerin size sattığı gibi bir sihir değil.\n\nSadece: veri → desen → karar. İşte bu kadar.\n\nPeki senin işletmen bu döngüyü kullanıyor mu?\n\nergeneai.com\n\n#ErgeneAI #YapayZeka #DijitalDonusum #KucukIsletme",
        "slides": [
            {"hook": "Herkes AI Diyor", "desc": "Peki kimse ne olduğunu anlatmıyor.", "hl": "AI", "metrics": None, "seed": 42, "scene": "Professional small business owner's desk, wooden table, coffee cup, notebook and pen, warm natural lighting, soft shadows, cozy atmosphere, realistic photograph style, no text, 8k quality"},
            {"hook": "AI Sandığın Gibi Değil", "desc": "Terminatör değil. Matrix değil. Sadece daha akıllı bir yardımcı.", "hl": "Sandığın Gibi Değil", "metrics": None, "seed": 101, "scene": "Relaxed home office corner, comfortable chair, bookshelf in background, warm sunlight streaming through window, plants on desk, calm peaceful atmosphere, realistic photograph, no text"},
            {"hook": "Aslında Çok Basit", "desc": "AI = veriyi al → deseni bul → kararı ver. Hepsi bu.", "hl": "Basit", "metrics": [("%87", "İşletme", "AI kullanıyor"), ("3x", "Daha fazla", "üretim"), ("7/24", "Kesintisiz", "çalışır")], "seed": 202, "scene": "Minimalist modern meeting room, clean white table, two empty chairs, natural light from large windows, simple plant decor, professional calm atmosphere, realistic photo, no text"},
            {"hook": "Rakibin Çoktan Başladı", "desc": "Sen hâlâ her şeye manuel mi yetişiyorsun?", "hl": "Rakibin", "metrics": [("%40", "Maliyet", "düşüş"), ("%60", "Cevapsız", "kayıp"), ("24/7", "Hizmet", "mümkün")], "seed": 303, "scene": "Busy workshop or storefront counter, stacks of papers, phone ringing, slightly messy organized chaos, warm fluorescent lighting, small business atmosphere, realistic photography, no text"},
            {"hook": "Bugün Başla", "desc": "AI karmaşık değil. Sana özel, çok kolay.", "hl": "Başla", "metrics": None, "seed": 404, "scene": "Peaceful morning coffee shop table, laptop closed, coffee cup steam rising, sunlight on wooden surface, calm and inviting atmosphere, realistic photograph style, no text"},
        ]
    },
    # ─── Post 2: FOMO ───
    {
        "id": 2, "theme": "FOMO — Ya Herkes Kullanıyorsa?",
        "caption": "<b>Ya Herkes Kullanıyorsa?</b>\n\nRakiplerin AI ile çalışırken sen hâlâ manuel mi devam ediyorsun?\n\nFarkı görmek için çok geç değil.\n\nergeneai.com\n\n#ErgeneAI #YapayZeka #DijitalDonusum #KucukIsletme",
        "slides": [
            {"hook": "Ya Herkes Kullanıyorsa?", "desc": "Sen daha başlamamışken rakiplerin çoktan geçti.", "hl": "Herkes", "metrics": None, "seed": 501, "scene": "Competing storefronts on a busy street, one shop closed and dark, the next one bright and full of customers, contrast of success vs stagnation, realistic street photography, natural daylight, no text"},
            {"hook": "Rekabet Uyumuyor", "desc": "Rakibin AI ile 7/24 hizmet verirken sen 9-5 çalışıyorsun.", "hl": "Rekabet", "metrics": [("%65", "Rakip", "AI kullanıyor"), ("%40", "Daha hızlı", "cevap süresi"), ("%30", "Daha fazla", "müşteri")], "seed": 502, "scene": "Two barbershops side by side, one has a line of customers waiting, the other empty, natural daylight, authentic street view photography, candid moment, no text"},
            {"hook": "Farkı Anla", "desc": "AI kullanan işletme: 7/24 açık, anında cevap, düşük maliyet.\nKullanmayan: kaçıran, yetişemeyen, kaybeden.", "hl": "Farkı", "metrics": None, "seed": 503, "scene": "Modern open sign glowing on a shop window at dusk, warm light inside, inviting atmosphere, street photography style, realistic evening lighting, no text"},
            {"hook": "Geç Kalmadan", "desc": "Pazar hızla değişiyor. Geç kalanın yerini doldurmak zor.", "hl": "Geç Kalmadan", "metrics": [("2x", "Daha hızlı", "büyüme"), ("%50", "Daha az", "iş yükü"), ("%90", "Müşteri", "memnun")], "seed": 504, "scene": "Sunset over a small town main street, peaceful evening, shopkeepers closing up, nostalgic American small business vibe, warm golden hour lighting, realistic photograph, no text"},
            {"hook": "Bugün Başla", "desc": "Rakibin bugün başladı. Sen ne zaman başlayacaksın?", "hl": "Bugün", "metrics": None, "seed": 505, "scene": "Early morning sunrise over a quiet neighborhood street, fresh start feeling, a single jogger on empty road, hopeful and motivating atmosphere, realistic photography, warm golden tones, no text"},
        ]
    },
    # ─── Post 3: Korkuyu Giderme ───
    {
        "id": 3, "theme": "AI Korkusu — Robot Değil",
        "caption": "<b>AI = Robot Değil</b>\n\nAI denince akla gelen o bilim kurgu filmlerini boşver.\n\nAI bir araç. Tıpkı telefon gibi, bilgisayar gibi.\n\nİşini kolaylaştırmak için var.\n\nergeneai.com\n\n#ErgeneAI #YapayZeka #DijitalDonusum #KucukIsletme",
        "slides": [
            {"hook": "AI = Robot Değil", "desc": "Filmlerdeki gibi değil. İşini kolaylaştıran bir araç.", "hl": "Robot Değil", "metrics": None, "seed": 601, "scene": "Friendly local coffee shop barista making coffee, warm smile, authentic small business atmosphere, natural morning light, realistic photography, no text"},
            {"hook": "Korkmana Gerek Yok", "desc": "AI senin işini ALMAZ. Senin işini KOLAYLAŞTIRIR.", "hl": "Korkmana Gerek Yok", "metrics": [("%92", "Kullanıcı", "memnun"), ("%70", "Zaman", "tasarrufu"), ("%0", "İş kaybı", "sektörde")], "seed": 602, "scene": "Relaxed small business owner smiling at their laptop, comfortable home office, plants and personal photos on desk, warm inviting atmosphere, natural window light, realistic portrait, no text"},
            {"hook": "Tıpkı Telefon Gibi", "desc": "Telefon hayatımızı kolaylaştırdı. AI da aynı.", "hl": "Telefon Gibi", "metrics": None, "seed": 603, "scene": "Hand holding a smartphone in a cozy living room, coffee table, magazine, warm lamp light, everyday life scene, realistic photography, no text"},
            {"hook": "Sen Hâlâ Kontroldesin", "desc": "AI karar vermez. Sen verirsin. AI sadece senin asistanın.", "hl": "Kontroldesin", "metrics": [("7/24", "Asistan", "hazır"), ("%100", "Senin", "kontrolünde"), ("0", "Karmaşa", "yok")], "seed": 604, "scene": "Confident business owner standing in their shop, arms crossed, looking assured, natural daylight from storefront window, authentic portrait, realistic photography, no text"},
            {"hook": "Küçük Adım, Büyük Fark", "desc": "Bugün 1 saat kazandıran bir araç düşün. Bir haftada 5 saat.", "hl": "Küçük Adım", "metrics": None, "seed": 605, "scene": "Peaceful evening desk scene, warm desk lamp, notebook open, coffee mug, personal workspace, calm atmosphere, realistic photography, no text"},
        ]
    },
    # ─── Post 4: Erişilebilirlik ───
    {
        "id": 4, "theme": "Erişilebilirlik — Küçük İşletmeye Fazla Mı?",
        "caption": "<b>Küçük İşletmeye Fazla Mı?</b>\n\nAI sadece büyük şirketler için değil.\n\nTam tersi: küçük işletmeler AI ile büyük şirketlerle rekabet edebilir.\n\nDüşük maliyet, büyük etki.\n\nergeneai.com\n\n#ErgeneAI #YapayZeka #DijitalDonusum #KucukIsletme",
        "slides": [
            {"hook": "Küçük İşletmeye Fazla Mı?", "desc": "Hiç değil. Tam tersi: küçük işletmeler için biçilmiş kaftan.", "hl": "Fazla Mı", "metrics": None, "seed": 701, "scene": "Small boutique shop interior, carefully arranged products on wooden shelves, warm lighting, cozy and inviting atmosphere, independent business feel, realistic photography, no text"},
            {"hook": "Büyük Şirketlerin Sırrı", "desc": "Büyüklerin kullandığı araçlar artık herkese açık.", "hl": "Sırrı", "metrics": [("%80", "Daha ucuz", "5 yıl öncesine göre"), ("%60", "Küçük işletme", "AI kullanıyor"), ("15dk", "Kurulum", "ortalama")], "seed": 702, "scene": "Open laptop on a small cafe table, outdoor seating, sunlight through trees, relaxed work atmosphere, realistic photography, no text"},
            {"hook": "Rekabet Eşitleniyor", "desc": "AI ile küçük işletme = büyük şirket gibi çalışır.", "hl": "Eşitleniyor", "metrics": None, "seed": 703, "scene": "Two small shop owners chatting in a doorway, friendly neighborhood vibe, brick storefront, morning sunlight, authentic street scene, realistic photography, no text"},
            {"hook": "Düşük Maliyet, Büyük Etki", "desc": "Bir çalışan maaşının çok altında. Ama bir çalışandan daha hızlı.", "hl": "Düşük Maliyet", "metrics": [("%90", "Daha az", "maliyet"), ("7/24", "Kesintisiz", "çalışır"), ("%40", "Daha fazla", "müşteri")], "seed": 704, "scene": "Happy shopkeeper counting morning earnings at the counter, small retail store, natural storefront light, authentic candid moment, realistic photography, no text"},
            {"hook": "Her İşletmeye Özel", "desc": "Hazır kalıp yok. Sana, işletmene, sektörüne özel çözüm.", "hl": "Her İşletmeye Özel", "metrics": None, "seed": 705, "scene": "Custom tailor shop, sewing machine, fabric rolls, personal workspace, warm indoor lighting, handmade craft atmosphere, realistic photography, no text"},
        ]
    },
    # ─── Post 5: Faydalar ───
    {
        "id": 5, "theme": "Faydalar — İşletmene Ne Katar?",
        "caption": "<b>İşletmene Ne Katar?</b>\n\nZaman kazandırır. Müşteri memnuniyetini artırır. Maliyeti düşürür.\n\nAI bir lüks değil, işletmenin yeni olmazsa olmazı.\n\nKazandığın zamanı asıl işine harca.\n\nergeneai.com\n\n#ErgeneAI #YapayZeka #DijitalDonusum #KucukIsletme",
        "slides": [
            {"hook": "İşletmene Ne Katar?", "desc": "Zaman, para, müşteri memnuniyeti. Üçü birden.", "hl": "Ne Katar", "metrics": None, "seed": 801, "scene": "Thriving local restaurant interior, happy customers, warm ambient lighting, busy but organized atmosphere, successful small business vibe, realistic photography, no text"},
            {"hook": "Zaman = Para", "desc": "Her gün saatlerce tekrar eden işlere veda et.", "hl": "Zaman = Para", "metrics": [("%70", "Zaman", "tasarrufu"), ("Haftada 15", "Saat", "kazanç"), ("%50", "Daha az", "iş yükü")], "seed": 802, "scene": "Watchmaker's bench with tools neatly arranged, careful craftsperson at work, warm focused atmosphere, detail-oriented workspace, realistic photography, no text"},
            {"hook": "Müşterin Memnun", "desc": "Hızlı cevap, 7/24 hizmet, unutulan randevu yok.", "hl": "Memnun", "metrics": None, "seed": 803, "scene": "Welcome desk at a small hotel or clinic, friendly reception area, flowers on counter, warm lighting, inviting atmosphere, realistic photography, no text"},
            {"hook": "Rakibin Önüne Geç", "desc": "Rakibin AI kullanıyorsa sen kullanmamak kaybettirir.", "hl": "Rakibin Önüne Geç", "metrics": [("2x", "Daha hızlı", "büyüme"), ("%40", "Daha fazla", "müşteri"), ("%90", "Memnuniyet", "oranı")], "seed": 804, "scene": "Bustling local market street, successful vendors with queues of customers, energetic atmosphere, golden afternoon light, authentic street photography, no text"},
            {"hook": "Haydi Başla", "desc": "Bugün başla. Bir hafta sonra farkı gör.", "hl": "Haydi Başla", "metrics": None, "seed": 805, "scene": "Open door of a small shop with a welcome mat, warm light spilling onto the sidewalk, inviting entrance, morning atmosphere, realistic photography, no text"},
        ]
    },
    # ─── Post 6: Acı ───
    {
        "id": 6, "theme": "Acı — AI'sız Geçen Her Gün",
        "caption": "<b>AI'sız Geçen Her Gün</b>\n\nHer gün cevapsız mesajlar, kaçan müşteriler, yetişmeyen işler.\n\nAI'sız geçen her gün = kayıp.\n\nDaha fazla bekleme.\n\nergeneai.com\n\n#ErgeneAI #YapayZeka #DijitalDonusum #KucukIsletme",
        "slides": [
            {"hook": "AI'sız Geçen Her Gün", "desc": "Her gün kayıp müşteri, kaçan fırsat, yetişmeyen iş.", "hl": "AI'sız", "metrics": None, "seed": 901, "scene": "Overwhelmed shopkeeper surrounded by papers, multiple phones ringing, stressed expression, messy desk, chaotic atmosphere, realistic photography, no text"},
            {"hook": "Kaçan Müşteriler", "desc": "Müşterin mesaj atıyor. Sen 2 saat sonra görüyorsun. O çoktan rakibine gitti.", "hl": "Kaçan", "metrics": [("%60", "Müşteri", "cevapsız kalıyor"), ("5dk", "İçinde", "rakibe gidiyor"), ("%30", "Kayıp", "gelir")], "seed": 902, "scene": "Empty waiting area in a clinic or shop, clock on wall showing late hour, dim lighting, missed opportunity atmosphere, realistic photography, no text"},
            {"hook": "Yetişemiyorsun", "desc": "Randevular, mesajlar, aramalar, siparişler... Bir yetişebilene kadar.", "hl": "Yetişemiyorsun", "metrics": None, "seed": 903, "scene": "Busy kitchen during rush hour, chef overwhelmed with multiple orders, steam and movement, chaotic but authentic restaurant atmosphere, realistic photography, no text"},
            {"hook": "Rakibin Uyumuyor", "desc": "Rakibin 7/24 hizmet veriyor. Sen uyurken o kazanıyor.", "hl": "Rakibin Uyumuyor", "metrics": [("7/24", "Rakip hizmet", "veriyor"), ("%40", "Daha hızlı", "cevap"), ("%50", "Daha fazla", "müşteri")], "seed": 904, "scene": "Night view of two competing stores side by side, one brightly lit with customers, the other dark and closed, moonlight atmosphere, realistic night photography, no text"},
            {"hook": "Bugün Değiştir", "desc": "Bu döngüyü kırmak için bir adım yeter.", "hl": "Bugün Değiştir", "metrics": None, "seed": 905, "scene": "First light of dawn over a quiet town, new day beginning, hopeful atmosphere, fresh start feeling, warm golden sunrise, realistic landscape photography, no text"},
        ]
    },
    # ─── Post 7: Saç Ekimi ───
    {
        "id": 7, "theme": "Saç Ekimi — Hasta Kaybı",
        "caption": "<b>Saç Ekimi Randevuları Kaçıyor</b>\n\nHasta mesaj atıyor, 2 saat sonra görüyorsun. O çoktan başka kliniğe gitmiş.\n\n7/24 cevap veren bir sistemle hasta kaybını sıfırla.\n\nergeneai.com\n\n#ErgeneAI #SacEkimi #Klinik #HastaMemnuniyeti #DijitalDonusum",
        "slides": [
            {"hook": "Hasta Nerede?", "desc": "Mesaj atıyor. Cevap bekliyor. 5 dk içinde rakibine gidiyor.", "hl": "Nerede", "metrics": None, "seed": 1001, "scene": "Modern hair transplant clinic reception desk, clean white interior, comfortable waiting area with leather sofas, professional atmosphere, natural daylight through large windows, realistic photography, no text"},
            {"hook": "Kaçan Hasta, Kaçan Para", "desc": "Her cevapsız mesaj = kayıp hasta. Her kayıp hasta = boş randevu.", "hl": "Kaçan Para", "metrics": [("%60", "Hasta", "cevapsız kalıyor"), ("%40", "Randevu", "boşa gidiyor"), ("30bin TL", "Aylık", "kayıp")], "seed": 1002, "scene": "Hair transplant consultation room, empty examination chair, medical equipment in background, professional clean atmosphere, soft medical lighting, realistic photo, no text"},
            {"hook": "Rakip Klinik Uyumuyor", "desc": "Rakip klinik 7/24 cevap veriyor. Sen 9-5 çalışıyorsun.", "hl": "Rakip Klinik", "metrics": [("7/24", "Cevap süresi", "rakipte hazır"), ("%90", "Hasta", "hızlı cevap bekler"), ("%50", "Daha fazla", "randevu rakibe")], "seed": 1003, "scene": "Two hair transplant clinics side by side on a main street, one with patients entering, modern facade, professional signage, daylight, realistic street photography, no text"},
            {"hook": "Hasta Unutmaz", "desc": "Randevu hatırlatma, takip mesajı, anında bilgilendirme. Hasta memnun, sen rahat.", "hl": "Unutmaz", "metrics": None, "seed": 1004, "scene": "Patient smiling while looking at phone, comfortable clinic environment, reassuring atmosphere, warm lighting, realistic portrait photography, no text"},
            {"hook": "Farkı Gör", "desc": "Haftaya 5 hasta daha kazanmak için bir adım yeter.", "hl": "Farkı Gör", "metrics": None, "seed": 1005, "scene": "Before and after hair transplant results board in clinic hallway, successful results, professional presentation, warm lighting, realistic clinical photography, no text"},
        ]
    },
    # ─── Post 8: Estetik ───
    {
        "id": 8, "theme": "Estetik — Danışan Takibi",
        "caption": "<b>Estetik Danışanların Nerede?</b>\n\nDanışan soru soruyor, sen cevaplayana kadar beklemekten vazgeçiyor.\n\nHızlı cevap = yüksek dönüşüm.\n\nergeneai.com\n\n#ErgeneAI #Estetik #DanisanMemnuniyeti #KlinikYonetimi #DijitalDonusum",
        "slides": [
            {"hook": "Danışan Beklemez", "desc": "Estetik kararı anlıktır. Bekleyen danışan vazgeçer.", "hl": "Beklemez", "metrics": None, "seed": 1101, "scene": "Luxury aesthetic clinic lobby, modern white interior, comfortable seating, elegant decor, fresh flowers on reception desk, premium atmosphere, natural lighting, realistic photography, no text"},
            {"hook": "Soru Sormak İster", "desc": "Aklında 10 soru var. Cevaplayan olmazsa başka kliniğe gider.", "hl": "Soru Sormak", "metrics": [("%70", "Danışan", "önce soru sorar"), ("%50", "Cevapsız kalınca", "vazgeçer"), ("24 saat", "İçinde", "karar verir")], "seed": 1102, "scene": "Aesthetic consultation room, treatment bed, modern medical equipment, soft lighting, professional calm atmosphere, realistic medical photography, no text"},
            {"hook": "7/24 Hazır Ol", "desc": "Danışan gece 2'de araştırır. O anda cevap alan kazanır.", "hl": "Hazır Ol", "metrics": None, "seed": 1103, "scene": "Smartphone on a nightstand showing message notification, moonlight through window, late night atmosphere, realistic photography, no text"},
            {"hook": "Kişisel Yaklaş", "desc": "Her danışana özel mesaj, kişisel teklif, hatırlatma. İnsan dokunuşu.", "hl": "Kişisel Yaklaş", "metrics": [("%80", "Danışan", "kişisel iletişim bekler"), ("%60", "Daha yüksek", "dönüşüm oranı"), ("%90", "Memnuniyet", "oranı")], "seed": 1104, "scene": "Aesthetic doctor consulting with patient in modern office, warm professional interaction, medical diplomas on wall, natural light, realistic portrait photography, no text"},
            {"hook": "Farkı Hisset", "desc": "Haftaya danışan kaybını unut. Sadece kazananları gör.", "hl": "Farkı Hisset", "metrics": None, "seed": 1105, "scene": "Happy aesthetic clinic team gathering, smiling staff in white uniforms, modern clinic background, team spirit atmosphere, realistic group photography, no text"},
        ]
    },
    # ─── Post 9: Güzellik ───
    {
        "id": 9, "theme": "Güzellik — Randevu Kaosu",
        "caption": "<b>Güzellik Merkezinde Randevu Kaosu</b>\n\nTelefon susmuyor. Mesajlar yetişmiyor. Randevular karışıyor.\n\nDijital düzene geç, hayatı kolaylaştır.\n\nergeneai.com\n\n#ErgeneAI #GuzellikMerkezi #RandevuSistemi #MusteriMemnuniyeti #DijitalDonusum",
        "slides": [
            {"hook": "Randevu Kaosu", "desc": "Telefon, mesaj, Instagram DM... Hepsi aynı anda. Yetişemiyorsun.", "hl": "Kaosu", "metrics": None, "seed": 1201, "scene": "Busy beauty salon reception desk, phone ringing, appointment book open, nail polish bottles, slightly chaotic but creative atmosphere, warm lighting, realistic photography, no text"},
            {"hook": "Müşterin Bekler mi?", "desc": "Cevap alamayan müşteri bir sonraki salona gider.", "hl": "Bekler mi", "metrics": [("%65", "Müşteri", "hızlı cevap bekler"), ("%40", "Cevapsız", "randevu kaybı"), ("Haftada 10+", "Kayıp", "müşteri")], "seed": 1202, "scene": "Elegant beauty salon interior, empty styling chair, mirror with lights, professional atmosphere, natural daylight, realistic interior photography, no text"},
            {"hook": "7/24 Açık Salon", "desc": "Sen uyurken müşterin randevu alsın. Sabah gelince hazır gör.", "hl": "7/24 Açık", "metrics": None, "seed": 1203, "scene": "Beauty salon at night, neon open sign glowing, empty chairs neatly arranged, calm atmosphere after hours, moody lighting, realistic night photography, no text"},
            {"hook": "Düzen = Kazanç", "desc": "Dijital randevu sistemiyle doluluk oranın artsın, iptaller azalsın.", "hl": "Düzen = Kazanç", "metrics": [("%90", "Doluluk", "oranına kadar"), ("%70", "Daha az", "iptal"), ("%50", "Daha fazla", "müşteri")], "seed": 1204, "scene": "Well-organized beauty salon desk, digital tablet showing schedule, organized product shelves, clean and professional atmosphere, realistic photography, no text"},
            {"hook": "Haydi Düzene Gir", "desc": "Bu hafta randevu kaosuna son ver.", "hl": "Düzene Gir", "metrics": None, "seed": 1205, "scene": "Successful beauty salon owner smiling, welcoming atmosphere, full salon in background, happy team, confident professional portrait, realistic photography, no text"},
        ]
    },
    # ─── Post 10: Diş ───
    {
        "id": 10, "theme": "Diş — Hasta Sadakati",
        "caption": "<b>Diş Hekiminde Hasta Sadakati</b>\n\nHasta randevuyu unutur. Sonra başka kliniğe gider.\n\nHatırlatma ve takiple hasta sadakatini artır.\n\nergeneai.com\n\n#ErgeneAI #DisHekimi #KlinikYonetimi #HastaTakibi #DijitalDonusum",
        "slides": [
            {"hook": "Hasta Unutur", "desc": "Randevu hatırlatma yok = boş koltuk. Boş koltuk = kayıp.", "hl": "Unutur", "metrics": None, "seed": 1301, "scene": "Modern dental clinic reception, clean white interior, dental equipment visible, professional atmosphere, soft clinical lighting, welcoming environment, realistic photography, no text"},
            {"hook": "Takip = Sadakat", "desc": "Randevu hatırlatma, kontrol mesajı, doğum günü kutlaması. Unutmazlar.", "hl": "Takip = Sadakat", "metrics": [("%30", "Randevu", "unutuluyor"), ("%80", "Hatırlatma", "ile geliyor"), ("%60", "Daha sadık", "hasta")], "seed": 1302, "scene": "Dental examination room, modern dental chair, equipment ready, clean professional environment, soft lighting, realistic clinical photography, no text"},
            {"hook": "Ağızdan Ağıza", "desc": "Mutlu hasta = ücretsiz reklam. Her memnun hasta 3 kişi getirir.", "hl": "Ağızdan Ağıza", "metrics": None, "seed": 1303, "scene": "Dentist consulting with happy patient in modern clinic, friendly interaction, professional atmosphere, warm natural light, realistic portrait photography, no text"},
            {"hook": "7/24 Danışma", "desc": "Hasta gece diş ağrısıyla mesaj atar. Anında cevap alırsa seni arar.", "hl": "7/24 Danışma", "metrics": [("7/24", "Hasta danışma", "hazır"), ("%50", "Gece mesajı", "acil vaka"), ("%70", "Dönüşüm", "oranı")], "seed": 1304, "scene": "Dental clinic facade at night, warm light from window, emergency sign visible, professional building, realistic night photography, no text"},
            {"hook": "Farkı Yaşa", "desc": "Haftaya boş koltuğun kalmasın.", "hl": "Farkı Yaşa", "metrics": None, "seed": 1305, "scene": "Full dental clinic waiting room, patients seated comfortably, modern interior, lively professional atmosphere, realistic photography, no text"},
        ]
    },
    # ─── Post 11: Avukat ───
    {
        "id": 11, "theme": "Avukat — Müvekkil İletişimi",
        "caption": "<b>Avukat Müvekkil İlişkisi</b>\n\nMüvekkil mesaj atar, cevap bekler. Bekleyen müvekkil güven kaybeder.\n\nHızlı iletişim, güçlü güven.\n\nergeneai.com\n\n#ErgeneAI #Avukat #Hukuk #MuvekkilIletisimi #DijitalDonusum",
        "slides": [
            {"hook": "Müvekkil Beklemez", "desc": "Acil bir dava mesajı. Cevap geç kalırsa müvekkil başka avukata gider.", "hl": "Beklemez", "metrics": None, "seed": 1401, "scene": "Professional law office, wooden desk, leather chair, law books on shelves, classical decor, serious professional atmosphere, natural light from window, realistic photography, no text"},
            {"hook": "Güven = Hız", "desc": "Hızlı cevap = güven. Güven = sadakat. Sadakat = referans.", "hl": "Güven = Hız", "metrics": [("%70", "Müvekkil", "hızlı cevap bekler"), ("%80", "İlk mesaj", "kritik"), ("%50", "Geç cevap", "kayıp")], "seed": 1402, "scene": "Lawyer reviewing documents in elegant office, focused expression, professional attire, bookshelf background, serious atmosphere, realistic portrait photography, no text"},
            {"hook": "7/24 Hazır Avukat", "desc": "Müvekkil gece 11'de mesaj atar. Sen sabah 9'da görürsün. Çok geç.", "hl": "7/24 Hazır", "metrics": None, "seed": 1403, "scene": "Law office building at dusk, warm lights on, professional sign, street view, calm evening atmosphere, realistic night photography, no text"},
            {"hook": "Düzenli Takip", "desc": "Dava takibi, duruşma hatırlatma, bilgilendirme. Müvekkil hep haberdar.", "hl": "Düzenli Takip", "metrics": [("%90", "Müvekkil", "bilgilendirme ister"), ("%60", "Daha memnun", "düzenli takiple"), ("%40", "Daha fazla", "referans")], "seed": 1404, "scene": "Legal documents neatly organized on desk, tablet showing calendar, professional organization, law office atmosphere, realistic photography, no text"},
            {"hook": "Bugün Başla", "desc": "Müvekkil iletişiminde farkı yaratan sen ol.", "hl": "Bugün Başla", "metrics": None, "seed": 1405, "scene": "Confident lawyer standing in front of law books, professional portrait, successful atmosphere, warm lighting, realistic photography, no text"},
        ]
    },
    # ─── Post 12: Emlak ───
    {
        "id": 12, "theme": "Emlak — Müşteri Takibi",
        "caption": "<b>Emlakçı Müşteri Kaybediyor</b>\n\nMüşteri ilanı görür, mesaj atar. Cevap yoksa başka emlakçıya gider.\n\nHızlı dönüş = satılık ilan.\n\nergeneai.com\n\n#ErgeneAI #Emlak #Emlakci #MusteriTakibi #DijitalDonusum",
        "slides": [
            {"hook": "Müşteri Kaçıyor", "desc": "İlanı görüp mesaj atan müşteri 5 dk içinde cevap bekler. Geç kalma.", "hl": "Kaçıyor", "metrics": None, "seed": 1501, "scene": "Real estate agency office, desk with property brochures, dual monitors, modern professional atmosphere, warm lighting, street view from window, realistic photography, no text"},
            {"hook": "Hız = Satış", "desc": "Hızlı cevap veren emlakçı = çok satan emlakçı.", "hl": "Hız = Satış", "metrics": [("%70", "Müşteri", "hızlı cevap bekler"), ("%80", "İlk iletişim", "kritik"), ("%50", "Daha fazla", "satış")], "seed": 1502, "scene": "Estate agent showing property keys to happy couple, new home atmosphere, smiling faces, professional yet warm interaction, realistic portrait photography, no text"},
            {"hook": "Gece Sorusu", "desc": "Müşteri gece 2'de ilan görür, mesaj atar. Sabah çok geç.", "hl": "Gece Sorusu", "metrics": None, "seed": 1503, "scene": "Smartphone showing property listing at night, warm bed lamp, cozy bedroom atmosphere, late night house hunting, realistic photography, no text"},
            {"hook": "Takip = Satış", "desc": "İlan gezen müşteriyi takip et. Unutma, hatırlat, buluştur.", "hl": "Takip = Satış", "metrics": [("%60", "Müşteri", "takip ister"), ("%40", "Daha fazla", "görüntüleme"), ("%30", "Daha yüksek", "kapanış")], "seed": 1504, "scene": "Property viewing, estate agent showing house to family, natural daylight through windows, warm home atmosphere, realistic photography, no text"},
            {"hook": "Haydi Başla", "desc": "Bu hafta kaybettiğin müşterileri geri kazan.", "hl": "Haydi Başla", "metrics": None, "seed": 1505, "scene": "Sold sign in front of beautiful house, successful real estate transaction, sunset lighting, achievement atmosphere, realistic photography, no text"},
        ]
    },
]


# ============================================================
# STATE MANAGEMENT
# ============================================================
def load_state():
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_post_id": 0, "last_date": "", "total_sent": 0}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_next_post():
    state = load_state()
    today = datetime.now().strftime("%Y-%m-%d")
    if state.get("last_date") == today:
        log.info(f"Already sent post today ({today}), skipping")
        return None, state
    next_id = state.get("last_post_id", 0) + 1
    for post in CONTENT_PLAN:
        if post["id"] == next_id:
            return post, state
    log.info("All posts completed, looping back to post 1")
    return CONTENT_PLAN[0], state


# ============================================================
# TELEGRAM SEND
# ============================================================
def send_photo(img_path, caption=""):
    with open(img_path, 'rb') as f:
        r = requests.post(
            f"{BOT_API}/sendPhoto",
            data={"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"},
            files={"photo": f},
            timeout=30
        )
    result = r.json()
    if result.get("ok"):
        log.info(f"Sent: {os.path.basename(img_path)}")
        return True
    else:
        log.error(f"Send failed: {result.get('description', 'unknown')}")
        return False

def send_message(text):
    r = requests.post(
        f"{BOT_API}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
        timeout=30
    )
    result = r.json()
    if result.get("ok"):
        log.info(f"Caption sent: {text[:50]}...")
        return True
    else:
        log.error(f"Message failed: {result.get('description', 'unknown')}")
        return False


# ============================================================
# SINGLE POST GENERATION + DELIVERY
# ============================================================
def generate_and_deliver(post, pipe):
    """Generate 5 slides and deliver them + caption separately."""
    post_id = post["id"]
    print(f"\n  📸 Generating {len(post['slides'])} slides...")
    
    generated = []
    for i, slide in enumerate(post["slides"]):
        scene = slide.get("scene", "Warm inviting business environment, natural lighting, realistic photograph style, brand-safe, no text")
        print(f"    Slide {i+1}/5: \"{slide['hook']}\"")
        
        result = pipe.run(
            scene_description=scene,
            hook=slide["hook"],
            description=slide.get("desc", ""),
            badge="", cta="",
            format="portrait",
            highlight_word=slide.get("hl", ""),
            niche="default",
            metrics=slide.get("metrics") or [],
            label=f"post{post_id}-slide{i+1}",
            seed=slide.get("seed", 42),
            max_revisions=1,
        )
        
        paths = result.get("paths", {})
        overlay = paths.get("overlay") or paths.get("rejected", "")
        final = paths.get("final") or overlay
        
        if final and os.path.exists(final):
            generated.append(final)
            print(f"      ✅ {os.path.basename(final)}")
        else:
            import glob
            outputs = sorted(glob.glob("/opt/hermes/instagram-pipeline/output/layouts/post_*_portrait.png"), key=os.path.getmtime)
            if outputs:
                generated.append(outputs[-1])
                print(f"      ⚠️ Fallback")
            else:
                print(f"      ❌ FAILED!")
    
    if len(generated) != 5:
        print(f"    ❌ Only {len(generated)}/5 slides generated, aborting delivery")
        return False
    
    # DELIVERY: önce 5 slide captionsız
    print(f"    📤 Sending 5 slides (no captions)...")
    for slide_path in generated:
        ok = send_photo(slide_path, "")
        if not ok:
            print(f"      ❌ Send failed")
        time.sleep(1.5)
    
    # DELIVERY: sonra caption ayrı mesaj
    caption = post.get("caption", "")
    if caption:
        print(f"    📤 Sending caption...")
        send_message(caption)
    
    print(f"    ✅ Post #{post_id} delivered!")
    return True


# ============================================================
# MAIN — Daily Single Post
# ============================================================
def main():
    print("=" * 60)
    today = datetime.now().strftime("%d.%m.%Y")
    print(f"📅 ErgeneAI Daily Pipeline — {today}")
    print("=" * 60)
    
    post, state = get_next_post()
    if post is None:
        print("✅ Already sent today, nothing to do.")
        return
    
    pipe = InstagramPipeline(base_dir='/opt/hermes/instagram-pipeline')
    success = generate_and_deliver(post, pipe)
    
    if success:
        state["last_post_id"] = post["id"]
        state["last_date"] = datetime.now().strftime("%Y-%m-%d")
        state["total_sent"] = state.get("total_sent", 0) + 1
        save_state(state)
        print(f"\n✅ Post #{post['id']} completed and state saved!")
    else:
        print(f"\n⚠️ Post #{post['id']} delivery failed, state NOT updated")


# ============================================================
# BATCH MODE — Generate Multiple Posts (for backlog fill)
# ============================================================
def batch_mode(post_ids):
    """Generate and deliver specific posts by ID (for filling the feed)."""
    print("=" * 60)
    print(f"📦 BATCH MODE — Posts: {post_ids}")
    print("=" * 60)
    
    pipe = InstagramPipeline(base_dir='/opt/hermes/instagram-pipeline')
    
    for pid in post_ids:
        post = None
        for p in CONTENT_PLAN:
            if p["id"] == pid:
                post = p
                break
        if not post:
            print(f"\n❌ Post #{pid} not found in CONTENT_PLAN")
            continue
        
        print(f"\n{'─' * 50}")
        print(f"📸 Post #{post['id']}: {post['theme']}")
        success = generate_and_deliver(post, pipe)
        
        if success:
            print(f"  ✅ Done!")
        else:
            print(f"  ❌ Failed!")
        
        # 10s pause between posts to avoid flooding
        if pid != post_ids[-1]:
            print(f"  ⏳ Waiting 10s before next post...")
            time.sleep(10)
    
    print(f"\n{'=' * 60}")
    print(f"✅ BATCH COMPLETE: {len(post_ids)} posts delivered")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=str, help="Post IDs to generate (comma-separated, e.g. '2,3,4,5,6')")
    args = parser.parse_args()
    
    if args.batch:
        ids = [int(x.strip()) for x in args.batch.split(",")]
        batch_mode(ids)
    else:
        main()
