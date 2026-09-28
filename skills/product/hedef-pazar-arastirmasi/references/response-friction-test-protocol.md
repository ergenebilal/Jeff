# Response Friction Testi — Protokol Sablonu

Masa-basi analiz "musteri kaciriyor mu" sorusunu **asla** cevaplayamaz. Bu protokol, o soruyu gercek dunyada olcen en ucuz testin tekrar kullanilabilir iskeletidir. Amac **RESPONSE FRICTION** olcmek — gelir kaybi veya odeme istekliligi DEGIL.

---

## 0. Kabul edilen sinirlama (pazarlik konusu degil)

> "4 saatte yanit yok" = **yalnizca RESPONSE FRICTION kaniti.** Gelir kaybi kaniti olarak siniflandirilamaz.

Kopru (yanitsizlik → musteri rakibe gitti → ciro dustu) bu testle kurulmaz. Yanitsizligin en az 6 sebebi olabilir ve hicbiri tek basina "satis kacirdi" demek degildir:

1. Numara WhatsApp'ta degil (kanal hatasi)
2. Numara izlenmiyor / eski numara
3. Bilinmeyen numaradan gelen mesaj spam sayildi
4. Isletme o saatte kapaliydi
5. Mesaj goruldu ama onceliklendirilmedi
6. Personel yogundu

**Kabul edilen metodolojik kusur:** bilinmeyen numaradan gelen mesaj, isletme normalde hizli donse bile gorunmezden gelinmis olabilir. Kontrol grubu bunu KISMEN kontrol eder, tamamen ortadan kaldirmaz. Rapor bu kusuru acikca yazar.

---

## 1. Grup tasarimi

| Grup | Kriter | Amac |
|---|---|---|
| **Hedef** | Dijital acik VERIFIED (kendi calisan sitesi yok / domain olu) + talep kaniti (yorum esigi) + kullanilabilir iletisim kanali kayitli | Surtunme var mi? |
| **Kontrol** | Ayni nis + ayni sehir, **kendi CANLI sitesi var** (WhatsApp linki tasiyor) | Norm mu, acik mi? |

Ek kurallar: farkli marka (ayni ajansin iki ofisi girmez) · cografi yayilim · hedef ve kontrol **ayni mesaji** alir.

Kontrol grubu kucukse (n=1) istatistik zayiftir — rapora bu zayiflik yazilir, gizlenmez.

---

## 2. Mesaj kurallari

- Tek bir net soru. Fiyat yok, satis yok, link yok, ek yok, AI'dan bahis yok.
- Hedef ve kontrolde **birebir ayni metin** (nis bazinda ayni sablon).
- Gercek musteri dili. Test oldugu itiraf edilmez — ama temsil icerdigi Bilal'e acikca bildirilir.
- **Tek mesaj.** Hatirlatma/takip YOK ("kac kez denedi" degiskenini kirletir).

Ornek sablonlar:
```
Emlak   : "Merhaba, <ilce> bolgesinde 3+1 kiralik daire ariyorum. Elinizde uygun bir daire var mi? Bilgi verebilir misiniz?"
Veteriner: "Merhaba, kedimin yillik asisi icin randevu almak istiyorum. Bu hafta uygun bir gun var mi?"
```

---

## 3. Zamanlama standardi

| Alan | Kural |
|---|---|
| Gun | Sali / Carsamba / Persembe (Pazartesi hafta plani, Cuma erken kapanis → dislanir) |
| Pencere | 10:30-12:00 (ogle 12:00-13:30 ve 17:00 sonrasi dislanir) |
| Kohort | Tum mesajlar TEK 90 dk'lik pencerede — saat etkisi esitlenir |
| t0 | Saniye hassasiyetinde tek saat referansi |
| Gozlem | 48 saat |
| Birincil bitis noktasi | Ilk 4 saat |
| Tekrar | Yok — her isletme 1 kez |

---

## 4. Siniflandirma

| Kod | Sinif | Tanim |
|---|---|---|
| **R1** | Gercek insan yaniti | Gercek kisi, **soruya ozgu** icerik |
| **R2** | Otomatik yanit | WhatsApp Business karsilama/uzakta mesaji, sablon |
| **R3** | Yonlendirme | Baska kisiye/ajansa yonlendirme; insan devam ederse R1, etmezse R2 |
| **R4** | Yanit yok | Pencere icinde hicbir yanit gelmedi |
| **R5** | Ulasilamadi | Numara WhatsApp'ta degil / hat olu / mesaj iletilemedi → **R4'ten AYRI sayilir** |

R5'i R4'e karistirmak testi cokertir: ulasilamayan kanal, yanitsizlik kaniti degildir.

**Otomatik tespit kurallari (en az biri):** "otomatik", "su anda musait degiliz", "mesajiniz alindi", "en kisa surede" ifadeleri · 5 saniyeden kisa surede gelip sablon icerikli · soruya hic atif yapmiyor · birebir ayni metin birden fazla isletmeden.

**Sure kovalari:** ≤5dk · 5-15dk · 15-60dk · 1-4s · 4-24s · 24-48s · >48s/yok

**Kayit alanlari:** `id, nis, grup, kanal, t0, ilk yanit zamani, sure, sinif(R1-R5), yanit metni, okundu bilgisi`

---

## 5. Sonuc kriterleri (kanit sinifi korunarak)

| Sonuc | Kosul | Kanit sinifi | Siradaki adim |
|---|---|---|---|
| **BASARI** | Hedefin **≥%40'inda** ilk 4 saatte R1 YOK **VE** kontrolde **≤%20** | `RESPONSE FRICTION — VERIFIED (asymmetric)` | Surtunmenin ciroya etkisini olcen AYRI deney (isletmenin kendi verisini gerektirir; temas + ayri onay). **Satis degil.** |
| **BASARISIZ** | Hedefin **≥%80'i 15 dk icinde R1** | `REFUTED` | Nisi KILL |
| **SONUCSuz** | Hedef ≈ kontrol (fark <20 puan) | `INCONCLUSIVE` | HOLD — yanitsizlik norm, dijital acik temelli satis tezi desteklenmiyor |
| **TEST COKER** | **≥%50 R5** | Gecersiz | Kanallari duzelt, testi yeniden kur, sonucu raporlama |

### Bu test HICBIR kosulda uretemez
kaçirilan TL/ciro rakami · "odeme yaparlar" sonucu · satis argumani.

**BASARI ciktisi:** "surtunme var ve asimetrik" — "gelir kaybediliyor" DEGIL.

---

## 6. Blokajlar (cozulmeden test calismaz)

| # | Blokaj | Secenek |
|---|---|---|
| B1 | **Gonderen kimligi yok** — Bilal kendi numarasini kati reddediyor (test mesaji = numarasinin kalici kayit altina alinmasi) | asagidaki kanal tablosundan sec; onay sart |

### Gonderen kanal secenekleri (maliyet + teknik gereksinim + risk)

| Secenek | Maliyet | Teknik gereksinim | Otomasyon | Risk |
|---|---|---|---|---|
| **Faturasiz SIM + eski telefon + WhatsApp** | ₺258-1.050 (hat) + paket | TC kimlikle hat kaydi · WhatsApp kurulu bir cihaz · Wi-Fi yeterli | Elle (15 mesaj ~30 dk) veya WhatsApp Web + Playwright | Dusuk |
| **WhatsApp Business Cloud API** | ~$0.011/sohbet (TR marketing) + BSP $0-49/ay | Meta Business hesabi · isletme dogrulamasi · WhatsApp'ta kayitli OLMAYAN numara · onayli sablon | Tam otomatik | **YUKSEK — opt-in olmayan numaraya isletme mesaji Meta politikasina aykiri → numara bani** |
| **VoIP (Twilio/Netgsm) SMS** | ~₺0.10-0.30/SMS | Numara + BTK gonderen adi kaydi | Orta | Yuksek — SMS ≠ WhatsApp (kanal degisir, deney gecersiz olur), TR teslim orani dusuk |
| **eSIM (yurt disi numara)** | $4-20 | VoIP numarasi | — | Yuksek basarisizlik — **VoIP numaralari WhatsApp kaydinda cogu kez reddedilir** |
| **Telefon aramasi (insan)** | ₺0 (mevcut hat) | Biri arayacak (Bilal veya baska biri) | Yok | Dusuk ama emek yogun |
| **Hic mesaj yok — herkese acik sahip yanit taramasi** | ₺0 | **Oturum acmis** bir tarayici oturumu gerekir (yorum paneli misafirde render olmuyor) | Tam otomatik | Sifir risk — uygulanabilirligi oturum sorusuna bagli |

**Secim sirasi:** once kontak gerektirmeyen tarama (uygulanabilirse), sinyal cikarsa en ucuz hat + elle gonderim. **Cloud API ve VoIP elenir** — biri numarayi yakar, digeri kanali degistirip deneyi gecersiz kilar.
| B2 | **Kanal ulasilabilirligi dogrulanmadi** — numaralarin WhatsApp'ta olup olmadigi bilinmiyor; degilse R5 uretir ve test coker | Onaydan sonra, gonderim oncesi tek seferlik ulasilabilirlik kontrolu |
| B3 | **Etik temsil karari** — mesaj gercek alici izlenimi veriyor | Onayli metin veya alternatif ton; karar Bilal'in |
| B4 | **Kontrol grubu dengesi** — kontrol n=1 ise istatistik zayif | Kontrolu n>=2'ye cikar |

---

## 7. Onay kapisi

- Onay **tek seferlik ve kapsamli**: tarih + isletme listesi + metin.
- Onay oncesi hicbir on-mesaj, test aramasi, "deneme" veya numara dogrulama yapilmaz.
- Gonderilen mesaj onaylanmis metnin **birebir kopyasi** olur.
- Kapsam disina cikilirsa (yeni isletme eklemek vb.) **yeniden onay alinir**.

---

## 8. Raporlama formati

Protokol her zaman su sirayla raporlanir: (1) grup secim kriterleri, (2) isletme listesi + kanal + kaynak, (3) tam mesaj metinleri, (4) zamanlama standardi, (5) siniflandirma kurallari, (6) kabul edilen sinirlama + etiket zorunlulugu, (7) sonuc kriterleri, (8) onay kapisi.

Protokol yazilirken **hicbir mesaj gonderilmez**; sonunda yalnizca protokol raporlanir ve acik onay beklenir.
