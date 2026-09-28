---
name: hedef-pazar-arastirmasi
category: product
author: Jeff
description: Nis seciminde kanita dayali karsilastir, tek oneri sun.
---

# Hedef Pazar / Nis Secimi Arastirmasi

Bilal icin B2B hedef nis secileceginde izlenecek yontem. "Nis sec", "pazari dogrula", "hangi sektore gidelim" tarzi isteklerde bu kural gecerlidir.

## Temel Kural: Tek Secenekli Onay YETMEZ

Bilal stratejik nis kararinda hizli "su olsun mu?" onayina hayir der. Istenen:

1. **5-10 aday nisi** ayni kriterlerle karsilastir (tek nis secip derine inme)
2. Her iddianin **kaynak gosterimi** sart (URL + tarih)
3. Bulunamayan veriyi "VERI YOK" diye isaretle — **uydurma yasak**
4. Sonunda **tek nis oner + kanitli gerekce** (puan tablosuyla)
5. 8 kriter: pazar buyuklugu, musteri basina ekonomik deger, lead yogunlugu, dijital acik, rekabet, ulasilabilir isletme sayisi, cozum satilabilirligi, bizim mevcut yeteneklerimiz

## Veri Kaynaklari Sirasi (once mevcut, sonra yeni)

1. **NotebookLM arastirma not defterleri** (onceki derin arastirmalar tekrar yapilmaz):
   - `db2fce0a-00a4-4fe7-8b33-327d3047adbf` — ErgeneAI Sektor Arastirmasi (69 kaynak: dental turizm fiyatlari, sac ekimi/estetik pazar, KOBİ AI benimseme)
   - `1308a34f-3a6c-4c8d-994c-dad5296024cc` — KOBI Yuksek Ciro Isletme Sahipleri Acilari (50 kaynak)
   - `mcp__notebooklm__notebook_query` ile citation'li ozet al
2. **Google Places (New)** ile lead yogunlugu olc (gercek tarama): `GOOGLE_API_KEY` → `~/.hermes/.env`. POST `places.googleapis.com/v1/places:searchText`, header `X-Goog-FieldMask` **zorunlu** (yoksa alanlar bos gelir): `places.displayName,places.rating,places.userRatingCount,places.websiteUri,places.formattedAddress,places.nationalPhoneNumber,places.businessStatus`. Query `"{sehir} {nis}"`, maxResultCount 20. Cikti: toplam, yorum ort, rating ort, website orani.
3. **Paralel subagent arastirmasi**: delegate_task 5'li fan-out, her biri 1-2 nis. `output_schema` DUZ tut — ic ice properties sahasi "'string' is not of type object" ile reddedilir.
4. Web aramasi (kaynak URL sart).

## Revenue Intelligence Pivotu

Master plan: `/opt/hermes/revenue-intelligence/PLAN-v1.md` — eski lead pipeline donduruldu, yeni sistem bu planla kuruluyor. Konum: "AI satmiyoruz; dijitalde nerede para kaybettigini bulup kapatıyoruz".

- Eksik bulmak degil **ticari etki** bulmak: "web siteniz kotu" yerine "yuksek niyetli ziyaretciyi teklife donusturecek CTA yok".
- Kanit katmanlari AYRI: Kanitlanmis (sayiyla) / Guclu cikarim / Senaryo. Dogrulanmis satis verisi yoksa "kesin ₺ kayip" iddiasi YASAK.
- Target Potential Score 0-100 (Customer Value 25 + Digital Dependency 20 + Digital Gap 20 + Competition 15 + Reachability 10 + Service Fit 10): ≥80 deep audit, 60-79 standard, <40 ELENIR.
- Mini Audit (3 bulgu + 1 rakip kiyasi + 1 quick win + 1 soru) ilk temas icin; 20 sayfalik deep audit YALNIZ yuksek potansiyelli/cevap veren lead'e.
- Code-first: skor/pattern/kontrol hesabi kodla; LLM sadece sentez ve stratejik oneride.

## Arastirma Fan-Out + Sentez Protokolu (derin pazar/teknoloji arastirmasi)

Bir pazar, teknoloji ya da tedarik zinciri derin arastirilacaksa **4 ORTOGONAL kol** kur (birbiriyle kesismeyen sorular) ve `delegate_task` ile paralel kostur:
1. **Yerel urun envanteri** — bu pazarda satilan urunler, fiyatlar, satici iddialari, kullanici sikayetleri
2. **Dunya standardi** — lider urunler, standart ozellik seti, yeni standartlar, entegrasyonlar
3. **Mekanik + maliyet** — is gercekte nasil yuruyor, kanal maliyetleri, etkinlik kanitlari
4. **Mevzuat/uyum** — resmi yukumlulukler, tarihler, ceza riskleri

**Subagent brief kurallari (her kola aynen yazilir):** SADECE bulunan bilgi yazilir · her iddiaya kaynak URL · bulunamayan "BULUNAMADI" diye isaretlenir · **uydurma yasak** · **satici iddiasi ile bagimsiz kanit AYRI etiketlenir** · cikti markdown rapor olarak dosyaya yazilir ve dosya yolu geri bildirilir.

**Dogrulama ZORUNLU — alt ajan ozeti kendi beyanidir, kanit degildir:**
- `ls -la` ile rapor dosyalari gercekten yazilmis mi (boyut > 0)
- iddia edilen kritik rakamlari `grep` ile rapor icinde dogrula (fiyat, atif, oran, urun adi)
- kaynak URL sayisini say: `grep -oE 'https?://[^ )]+' <rapor> | sort -u | wc -l` — dusukse rapor zayiftir
- basliklar/bolumler gercekten var mi; "BULUNAMADI" listesi var mi

**Sentez teslimi:** 4 raporu Bilal'e **dosya listesi olarak verme**. TEK karar belgesi yaz:
> yonetici ozeti → mekanizma (is gercekte nasil yuruyor) → envanter tablosu → dunya karsilastirmasi → maliyet ekonomisi → mevzuat → **hangi kanit saglam / hangisi satici iddiasi** → *nerede acik var* → **bu arastirma ne degistirdi** → bilinmeyenler → sade dil ozeti

Kaynak raporlar sentezin EKI olarak gonderilir, govdeye gomulmez.

**Olumsuz sonuc gecerli sonuctur.** "Bu is zaten cozulmus, teklif olu" demek basarisizlik degil; aylarca yanlis ise harcamayi onleyen sonuctur. Raporu bu sonuca gore egme ya da bulguyu satilabilir hale getirmeye calisma.

**Nis hacmi karsilastirmasi (hizli tarama):** kayitli isletme verisinde her nis icin **medyan yorum sayisini** hesapla (n>=3 olan nisler). Yuksek medyan = gercek musteri akisi. Tek basina nis secmez ama dusuk medyanli nislari hizla eler.

Brief sablonu, dogrulama komutlari ve sentez iskeleti: `references/arastirma-fanout-sentez.md`

## Kanitlanmis Nis Kararlari (09.09.2026 revizyonu — tam rapor: /opt/hermes/revenue-intelligence/nis-karari-raporu.md)

- **EMLAK OFISLERI — SECILDI (64/80)**: En olculebilir kayip (%4 komisyon = tek lead ~188K TL), portala 200K TL/yil odeme aliskanligi KANITLI, Bursa'da yuzlerce ofis (planin 100 isletme modeli calisir), EmlakDesk/sahibinden 'ilan+CRM' satiyor ama 'gelir kacagi audit' satan YOK. Ilk hedef: Bursa orta olcek ofisler, mini audit ₺7.5-15K → retainer ₺5-10K/ay. **— BU KARAR SONRADAN COKTU:** nis medyan yorumu **18** (11 nis icinde EN DUSUK) ve ofislerin **%32'si zaten sahibinden'de** calisiyor; masa-basi puanlama gercek saha sinyalini yakalamadi. Ders: puan tablosu tek basina nis secmez — **medyan musteri hacmi + dogrulanmis kusur kesisimi** secer. Daha sonra veteriner dikeyi bu kesisimle secildi (20 klinikte medyan 224 yorum, 3'unde canli dogrulanmis kusur).
- **Sac ekimi / medikal estetik — REVIZE (58/80, ikinci dalga)**: Pazar EN BUYUK (kuresel ~%60, 1.5M hasta/yil, bilet €1.8-5.5K) ama Bursa'da havuz DAR (~18-20 merkez) → planin 100 isletme taramasi calismaz; Istanbul devleri zaten dijitallesmis (13 klinik denetiminde 8'i cok dilli+widget). Bosluk: orta-kucuk + Istanbul disi klinikler + 'revenue audit satan yok'. Istanbul/Ankara/Izmir orta-kucuk kliniklere uzak audit ile test edilecek.
- **Mobilya (60) — ucuncu dalga**: Inegol 3.807 isletme (Bursa'ya 30dk) ama B2B inbound dusuk, %92 mikro firma butce kisitli.
- **Dis klinigi — REVIZE (57)**: 'Resepsiyonistim var' direnci suruyor; yazilim katmani DOYMUS (Macrodental/NovaSoft 5000+ klinik) — o katmana girme. Bosluk: 7/24 AI resepsiyonist + no-show/gelir-kacagi audit (kimse urunlestirmemis). ₺5-15K/ay mumkun.
- **ELENDI (kanitli)**: hukuk (KVKK + 1-2 kisilik buro + danisma ucretsiz), otel (personel krizi), insaat/tadilat (odeme kulturu yok), metal/CNC (muhendis dili, uzun dongu — 2. dalga), restoran (doymus POS + dusuk marj), guzellik (kucuk ciro — yedek kanal).
- **Istanbul devleri hedef DEGIL** (6K+ yorumlu global oyuncular — kendi pazarlama ekipleri var). Hedef: Bursa/orta olcek, 100-500 yorum, kurumsal olmayanlar.
- **VETERINER — SECILDI ama DOGRULANMADI (11.09.2026)**: secim gerekcesi pazar cazibesi degil **kesisim** — 20 klinikte medyan 224 yorum (kuafor 436 ve guzellik 233'un ALTINDA; yani en hacimli nis bile degil) + 3 klinikte canli dogrulanmis kusur (olu domain, gecersiz sertifika, puan dibi). Tek dikey secilmesinin sebebi: tek satis cumlesi + tek rakip seti + tek vaka calismasi (ADE'nin "nis daginikligi" itirazina cevap). **Yazilim katmani doymus (22 urun) — o katmana girme.** Bu nis de hala **sifir musteri temasi**; hicbir klinige mesaj gitmedi. Karsi-ornek: en hacimli iki nis (kuafor 436, guzellik 233) dijital kusur acisindan hic taranmadi — veteriner tutmazsa ilk bakilacak yer orasi.

- **Stratejik Onay**: Yuksek guvenli niş kararlari icin Adversarial Decision Engine (ADE) ile dogrulanir. L1_LIGHT debate (thesis/anti-thesis/judge) icin %50+ guven, L2_FULL icin %65+ guven hedeflenir. ADE output'u `~/.hermes/decisions/` ve `~/.hermes/logs/ade-decisions.log`'a kaydedilir.

Detay ve ornek olcum: `references/lead-yogunlugu-olcumu.md` (Google Places (New) tarif, websiteUri PORTAL_ONLY/OLU_SITE/IG_ONLY sınıflandırması — dijital açık oranını 'uri var' degil gerçek site sinifiyla oluic çünkü portala duesen bir lead kendi sitesiz sayılır)

#### ADE icin Kaynak

- Motor: `/opt/hermes/jeff_v2/adversarial_engine.py`
- Testler: `cd /opt/hermes/jeff_v2 && python3 test_adversarial_engine.py`
- Kullanim: `from adversarial_engine import AdversarialDecisionEngine`
- **Pitfall — `run()` imzasi:** `debate_level=...` ve sayisal `uncertainty=4` argumanlari DESTEKLENMEZ — `TypeError: run() got an unexpected keyword argument`. Dogrusu: `uncertainty="high"` (string) + `force_level="L2_FULL"` (degerini gate'in secmesine birak veya zorla). `irreversible=True` da L2'yi tetikler (gate skor >=5.0 veya irreversible/architecture trigger).

## 🔢 Kategori Dolgunluk Kontrolü — "Sistem Kuralım" Demeden Önce

Bir kategoriye *"size X sistemi kuralım"* demeden önce **o kategoride kaç hazır ürün olduğunu say.**
Ürün doluysa **ürün boşluğu yoktur**; geriye kalan tek meşru soru **benimseme** boşluğudur
("ürün var ama kullanmıyorlar") — o da ayrıca kanıt ister.

Ölçülmüş iki örnek:
- **Veteriner klinik yönetimi:** 22 yerli ürün (biri ücretsiz), fiyatlar ₺499–3.499/ay; ikisinde
  TARBİL/IDEXX entegrasyonu bile var → bu katman **kapalı**.
- **Kuaför/güzellik randevu:** 8+ ürün (kuaförandevu, salonrandevu, kolayrandevu, randevucun, nuvu,
  planlaapp, Booksy, Fresha) → "randevu sistemi kuralım" da **kapalı**.

**Ayrım kritik:** veterinerde 22 ürün vardı **ve klinikler kullanıyordu** (doygun); kuaförde ürün var
**ama bio'larda telefon/DM görülüyor** (benimseme açığı). İkisi farklı iştir: birincide ürün satılmaz,
ikincide ancak "kurulum/benimseme" hizmeti tartışılabilir.

Yanı sinyal: yerli ürünlerin çoğu fiyatını yayınlamıyorsa (22'nin 10'u) talep yüksektir — boşluk değil.

## 🧾 Tek Müşteri Sistem Değildir

İlk ödeme alındığında "sistem çalışıyor" denmez. Tek satış yalnızca **ilk adımın mümkün olduğunu**
kanıtlar (satış yapılabiliyor + teslim edilebiliyor); **tekrarlanabilirliği kanıtlamaz.**

- Ölçüt: aynı iş **ikinci ve üçüncü kez** satılabiliyor mu? Satılamıyorsa çerezlik iştir.
- İlk işten sonra sorulacak tek soru: *"bunu 10 kez satabilir miyim?"*
- Küçük tek seferlik işi küçümseme — referans + vaka çalışması + "satabiliyorum" kanıtı üretir.
  Ama onu sistem diye raporlamak, çerezlik işin aylar sonra da çerezlik kalmasına yol açar.

## 💰 Pazar Fiyat Çıpası ve Ortak/Platform Ölçümü

Fiyat yazmadan önce **aynı ihtiyaç için pazarda hâlihazırda ödenen** bedeli bul. En güçlü kanıt, hedef kitlenin satın aldığı **bitişik hizmetin canlı fiyat sayfasıdır** — kendi beyanın veya masa-başı tahmin değil, fiilen satılan fiyat. Bulunan çıpa teklifin **alt sınırıdır**: "görünür olmak" için ödenen bedelin üstünde konumlanan "dönüşüm" teklifi gerekçeli olur.

Çıpa, **o ihtiyaç için para döndüğünü** kanıtlar; "bu müşteri bize öder" demez. Ödeme sinyali yerine geçmez (`ticari-dogrulama` sırası atlanmaz).

Bir platform/potansiyel ortak değerlendirilecekse halka açık kaynaklardan ölç — sitemap envanteri (ürün sayısı = listelenen müşteri sayısı), fiyat sayfası, ödeme kuruluşu (PayTR/iyzico/Stripe varsa ürün fiilen satılıyor). Üç kural:
1. **Kayıtlı müşteri ≠ ciro.** Envanter sayısı gelir değildir; kaç tanesinin **ücretli abone** olduğu sorulmadan gelir hesabı yapılmaz.
2. **Ortağın doğrulanmamış iddiasını devralma** ("%20-50 artış" gibi) — kanıtlayamadığın acıyı satış argümanı yapmama ilkesi burada da geçerli.
3. **Ortaklık konuşmasıyla başlama → 5-10 müşterilik ölçülebilir pilot**; fiyat pilot sonucundan sonra konuşulur. Katman sınırını yaz ("görünürlük" platformun, "dönüşüm" bizim) — sınır bulanırsa ortaklık değil rekabet olur.

Sitemap sayım komutları, ham HTML'den fiyat çıkarma kalıpları, görüşmede sorulacak sorular ve rapor kalıbı: `references/ortak-ve-fiyat-cipasi.md`

## Saha Dogrulamasi — WhatsApp Cevap Hizi Testi (ADE RESEARCH sonrasi)

ADE `RESEARCH` (kanit masa-basi, satis verisi yok) verdiginde en ucuz saha dogrulamasi: hedef ofislere gercek musteri gibi WhatsApp mesaji at, cevap suresini olc. Uzun yanit = "lead kaciriyorsun" tezi kanitlanir.

### Oturum kurulumu — Playwright MCP (browser_exec degil)

`browser_exec` sunucuda Chrome baslatamaz ("chrome-not-running" fatal). Playwright MCP kendi tarayicisini yonetir:

```
1. mcp__playwright__browser_navigate -> https://web.whatsapp.com
2. mcp__playwright__browser_take_screenshot (filename: whatsapp-qr.png, scale: css)  # QR render edilir
3. Screenshot ~/.hermes/whatsapp-qr.png'e duser -> MEDIA: ile kullaniciya gonder
4. Kullanici telefonundan tarar (WhatsApp -> Bagli Cihazlar -> Cihaz Bagla)
```

QR ~20-30 sn gecerli — hizli gonder, kaybolursa yenisini cek. Mesaj gonderme: `browser_snapshot` + `browser_click` yeni sohbet; veya `browser_run_code_unsafe` ile `page` objesi.

### Test tasarimi

- Hedef (dijital zayif) + kontrol (site iyi) ofislere AYNI anda at — farki olc. **Kontrol grubu olmadan test GECERSIZDIR:** sehir/sektor genelinde zaten kimse yanit vermiyorsa bu bir "acik" degil NORMDUR; kontrol olmadan hedefteki yanitsizligi aciga yazmak sahte kanit uretir.
- **Mesaj metni hedef ve kontrolde BIREBIR AYNIDIR.** Farkli metin karsilastirmayi bozar.
- **Kohort kurali:** tum mesajlar tek bir 90 dk'lik pencerede gonderilir (Sali-Carsamba-Persembe, 10:30-12:00) — saat etkisi tum grupta esitlenir. Ogle arasi ve 17:00 sonrasi dislanir.
- **Tek mesaj, takip yok.** Hatirlatma mesaji "kac kez denedi" degiskenini kirletir.
- **Link/ek gonderme** — link spam filtresini tetikler ve yanitsizligi YAPAY sisirir.
- **Kanit sinifi ZORUNLU:** sonuc her zaman `EVIDENCE CLASS: RESPONSE FRICTION (VERIFIED | REFUTED | INCONCLUSIVE)` olarak etiketlenir — **asla** `REVENUE LOSS`.
- Mesaj gercek potansiyel musteri diliyle, spam degil; test oldugu itiraf edilmez. (Kucuk bir temsil icerdigini Bilal'e acikca bildir, karari ona birak.)
- Ucuncu tarafa mesaj = Bilal onayi sart. **Onay olmadan hicbir kanaldan hicbir mesaj gonderilmez** — numara dogrulama/"deneme" mesaji dahil.

Siniflama kodlari, zaman pencereleri, sonuc kriterleri ve blokaj listesi: `references/response-friction-test-protocol.md`
- **Bilal'in kendi numarasiyla test YASAK:** Whatsapp Web'i Bilal'in gercek telefonuyla baglamak, test mesajlarini o numaradan atmak demektir -> ofisler numarasini gorur ve kalici kayit altina alir. Bilal bunu kati reddetti ("Benim numaramdan ne yapacaksin"). Mystery-shopper testi için YA gizli/sanal numara YA kimligi aciga cikarmayan web-form testi kullan; gercek kullanici numarasi asla lead/e tarafa desifre edilmez.

## Instagram-Is Modeli Saha Analizi (IG DM/randevu ile is yapan isletmeler)

Bilal yon kurali: "Instagram DM uzerinden randevu/musteri alan isletmeler hedef olsun" (musterisi zaten orada). Guzellik merkezi gibi IG agirlikli nislerde saha dogrulamasinin ana olcumu **yorum-cevap orani** + bio CTA'dir.

- **Olcum birimi = bilgi isteyen yorumlara işletme public Reply veriyor mu.** Fiyat/randevu/urun/sube/"nasil" iceren yoruma cevap yok = provable leak: "musterin fiyat soriyor, sen cevapsiz birakiyorsun".
- **Pitfall — isletmeler yorumu gormezden gelir:** taramanan cogu son-postta yorum emoji/iltifat-cekili etiketi olur, bilgi sorusu az gorunur. Bu, isletmenin IG'yi vitrin yapip musteriyi DM/WhatsApp'e ittigini gosterir; yorum taramasi tek basina zayif kanit olabilir. Nerede satilacak acik varsa asil olcum **DM cevap suresi** (sanal numara/gizli hesap gerektirir — Bilal numarasi YASAK).
- **ADE uyarisi (payment_potential 10):** musteri IG'de kanitlanir AMA isletme "zaten elle yonuyorum" diyebilir; yorumlara cevap vermemesi bile "kanali onemsemiyor" diye okunur. Otomasyonu satmak icin olculmus kayip (cevap suresi) kaniti sart — masa-basi istegi yetmez.
- **Pitfall — "%0 cevap" sunumu yaniltici olabilir (saha verisi olumsuz cikti):** 895K takipci/29 profil taramasinda "17 soru, %0 cevap" diye satis kaniti sundum; ama veri cogunlukla "0 yorum"du — yani isletme cevapsiz birakiyor DIREKTE, kimse SORMUYORDU. Buyuk profillerde soru hic yok (163K Cicim, 213K Hairworld = 0 soru; sorular kucuk profillerde). Satis argumanina cevirme ONCESI kontrol: bilgi-isteyen soru sayisi gercekte >0 MI, yoksa yoklugun ustu mu orulen calisiyor? Takipci kalabaligi talep degildir. Bursa Suit ornegi: fiyat sorusu + cok sayida sikayet vardi ve sikayetlere sifir yanit — itibar kaybi acisi kazanc kaybinden daha satilabilir.
### Dijital Denetim Kanit Disiplini (site canliligi iddialari)

Dijital acik olcerken en pahali hata: **calismayan siteyi "olu site" saymak.**

- **HTTP hatasi ≠ olu site.** Cloudflare/bot korumasi, portal sayfalari ve yavas sunucular 403/timeout dondurur; bunlar sitenin olu oldugunu GOSTERMEZ. Denetim araclarinda 403/timeout goren bir site "olu" ilan edilirse acik orani SISIRILIR.
- **Iki katmanli dogrula:** (1) `socket.getaddrinfo(domain)` ile DNS cozumlenmesi — cozumlenmiyorsa domain GERCEKTEN oludur; (2) gercek tarayici render'i (Playwright) — DNS geciyor ama icerik gelmiyorsa bot-blok/hata ayrimini yapar. Sadece HTTP durum koduna bakarak "olu site" demek YASAK.
- **URL'yi ASLA tahmin etme.** Bir isletmenin "sitesi olu" iddiasi yalnizca kaynak verideki GERCEK `websiteUri` degeri uzerinden kurulur. Plausible gorunen bir alan adi uydurup test etmek sahte kanit uretir (uydurulan domain DNS'te cozumlenmez -> "olu" sanilir, oysa gercek kayitli domain calisiyordur).
- **Google Places `reviews` alani bos doner** (API kisitli; `searchText` ve Place Details ikisi de). Yorum metni icin Google Maps sayfasi Playwright ile acilabilir **ama oturum acilmamis tarayicida yer sayfasi yalnizca ilk ~3-6 yorumu render eder**: "Yorumlar" paneli ve "Yorumlarda arayin" kutusu **"Oturum açın"** durumunda kalir, `div[data-review-id]` sayisi 0 doner (arama kutusu sorguyu kabul edip "sonuclar gosteriliyor" der, liste yine bos kalir). **Yorum metnine dayali bir olcum tasarlamadan ONCE panelin gercekten yorum render ettigini dogrula** (`div[data-review-id]` sayisi > 0); bu dogrulamayi yapmadan saatler suren bir tarama kurma. Yorum metni zorunluysa once oturum/erisim sorusunu coz; cozulmuyorsa **yorum metnine bagimli olmayan** bir saha olcumune gec.
- **Portal profili = kendi sitesi DEGIL, ama acik da DEGILDIR.** `websiteUri` bir portal profilini (sahibinden.com vb.) veya bir sosyal medya sayfasini gosteriyorsa isletme kendi dijital varligina sahip degildir — ancak bu **rasyonel bir tercih** olabilir (alicilar/kiraci adaylari o portaldadir). "Portal kullaniyor" tek basina gelir kaybi kaniti degildir.
- **Yuksek yorum sayisi ≠ musteri kaciriyor.** Yorum sayisi TALEP gostergesidir, sizinti kaniti degildir. Ikisini karistirmak 09.09 manifestosunu ihlal eder.

- **Kayit (09.09, Bilal manifestosu): "Kanitlayamadigim ticari aciyi satis argumanina donusturmeyecegim."** Saha verisini satis metnine cevirme kapisi: (1) musteri bu aciyi gercekten yasiyor mu (gorulen talep/verideki kanit, cikarim degil), (2) para odemeye istekli mi (payment_willingness <40 ise RESEARCH — zorlama yok). Kanit tasiyamayan oneri rafa kaldirilir; "17 soru %0 cevap" gibi sayiyi abartip "hadi iletisime gecelim" demek aktivitedir, sonuc degildir.
- Orneklem 47 profile 3 paralel subagent ile tarandi; her subagent'a kanitlanmis Playwright protokol texte verildi. Tarif ve pitfall'lar: `references/instagram-is-saha-analizi.md`

