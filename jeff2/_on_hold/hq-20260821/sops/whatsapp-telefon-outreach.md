# SOP: WhatsApp / Telefon Outreach v2
**Oluşturan:** Jeff (Patronus)
**Tarih:** 2026-07-09 (v2)
**Geçerlilik:** 2026-10-07 (+90 gün)
**Durum:** ✅ Onay bekliyor

## 1. Amaç

Email'i olmayan lead'leri bloke etmek yerine, **telefon ve WhatsApp üzerinden outreach** yaparak pipeline'ı canlı tutmak. Email yoksa iş durmasın. Ama agresif satışa da dönüşmesin.

## 2. Hangi Lead'lere Uygulanır

Bu SOP sadece şu lead'lere uygulanır:

| Durum | Uygulanır mı? |
|:------|:-------------|
| Email'i yok + Telefonu var | ✅ **Uygulanır** |
| Email'i yok + Telefonu yok | ❌ Uygulanmaz (beklemeye alınır) |
| Email'i var | ❌ Email outreach kullanılır |
| Email yok + Telefon var + Contacted statüsünde | ❌ Zaten iletişim kurulmuş |

**Mevcut durum:** 31 emailsiz lead'in ~29'unda telefon var (%95). Kalan ~2'sinde telefon da yok — bunlar beklemeye alınır.

**Öncelik sırası:**
1. 🥇 Diş klinikleri (en yüksek dönüşüm potansiyeli)
2. 🥇 Oteller (sezon açık, acil ihtiyaç olabilir)
3. 🥈 Saç ekimi merkezleri (yüksek bütçeli müşteri)
4. 🥉 Diğer

## 2b. Kanal Geçişi Meşruiyet Kuralları

**Email → WhatsApp/Telefon geçişi sadece şu durumda meşrudur:**
1. Email yok (veya enriched edilemedi)
2. **VE** Telefon/WhatsApp bilgisi var
3. **VE** Lead daha önce email ile denenmedi (veya denendi ama yanıtsız kaldı ve üzerinden 7+ gün geçti)
4. **VE** Lead'in sektörü WhatsApp/Telefon kanalına uygun (otel/hizmet/sektör: uygun; kurumsal/yazılım: önce email denenmeli)

**Şu durumda geçiş MEŞRU DEĞİLDİR:**
- Lead'de email var ama enrichment atlanıp direkt WhatsApp çıkıldıysa (tembellik)
- Lead'de email yok, telefon da yok, ama yine de "whatsapp çıkıldı" deniyorsa (veri tutarsızlığı)
- Lead daha önce email ile denenmiş ve yanıt almışsa, aynı lead'i WhatsApp'tan tekrar rahatsız etmek

**Her kanal geçişi feed'e yazılır ve gerekçesi belirtilir:**
```
📞 KANAL GEÇİŞİ: lead-xxx → email yok, telefon var, sektör otel → WhatsApp kanalına geçildi
```

**Çapraz kontrol (Bilge→Hırslı) bu geçişlerin meşruiyetini haftalık denetler.** Gerekçesiz veya kural dışı geçiş ihlal sayılır.

## 3. Outreach Sırası

Her lead için aynı sıra uygulanır. Atlama yok.

```
Adım 1 — Lead'i Hazırla
─────────────────────────
Ne yap: Lead'in adını, sektörünü, websitesini kontrol et
Süre: 2 dk

Adım 2 — İlk Temas (WhatsApp)
───────────────────────────────
Ne yap: Kısa, tanıtıcı mesaj gönder (bkz. Bölüm 4 — Mesaj Kuralları)
Kanal: WhatsApp (telefon numarası varsa)
Hedef: Lead'in ihtiyacını anlamak, satış yapmak değil

Adım 3 — Bekle (3 gün)
───────────────────────
Ne yap: Cevap bekle. Sabırlı ol.
Süre: 3 iş günü

Adım 4 — Cevap Yoksa Telefon Ara
─────────────────────────────────
Ne yap: Kısa bir telefon görüşmesi yap
Kanal: Doğrudan ara (WhatsApp değil)
Hedef: Lead'i konuşturmak, ihtiyacını anlamak
Süre: Max 3 dk

Adım 5 — Bekle (2 gün)
───────────────────────
Cevap yoksa veya meşgulse → 2 gün bekle

Adım 6 — WhatsApp Takip
────────────────────────
Kısa bir hatırlatma mesajı (bkz. Bölüm 4)

Adım 7 — Bekle (7 gün)
───────────────────────
Cevap yoksa → lead "soğudu" statüsüne al

Adım 8 — Soğuk Lead Havuzu
───────────────────────────
7 gün + ulaşılamadı → soğuk havuza al
Ayda 1 kez tekrar dene (sadece WhatsApp)
```

## 4. Mesaj Kuralları

### İlk WhatsApp Mesajı (Template — KESİNLİKLE birebir kopyalanmayacak, lead'e göre uyarlanacak)

```
Merhaba [isim/ünvan],

Ben Bilal Ergene, ErgeneAI kurucusu. [Sektör/şehir]'deki işletmelere 
dijital operasyon yönetimi konusunda destek veriyoruz.

[Lead'in sektörüne özel 1 cümle: örn. "Otel rezervasyon yönetimini"]
[veya "Diş kliniği hasta takibini"] otomatikleştiren bir sistem 
üzerinde çalışıyoruz.

Şu an sizin gibi [sayı] işletme ile görüşüyor, ihtiyaçları haritalıyoruz.
5 dakikanız varsa çok değerli olur.

Teşekkürler,
Bilal
```

### Mesaj Kuralları (Uyulmazsa iptal)

| Kural | Açıklama |
|:------|:---------|
| **Kısa** | 3 cümleyi geçme. İlk mesaj max 200 karakter |
| **Satış baskısı yok** | "Fırsat", "kaçırma", "sınırlı" gibi kelimeler yasak |
| **Değer ver** | Lead'in ihtiyacını sor, kendini satma |
| **Kişisel** | Her mesaj lead'e özel uyarlanır. Kopyala-yapıştır yasak |
| **Saat** | WhatsApp: 10:00-12:00 veya 14:00-17:00 arası. Hafta sonu yasak |
| **Arama** | 10:00-11:30 veya 14:00-16:00 arası. Öğle tatilinde arama yasak |
| **Israr yok** | 2 cevapsız denemeden sonra 7 gün bekle |

### Takip Mesajı (3 gün sonra, cevap yoksa)

```
Merhaba [isim], bir önceki mesajımı gördünüz mü? 
Çok kısa bir görüşme için uygun bir zamanınız var mı?
```

### İkinci Takip (5 gün sonra, hâlâ cevap yoksa)

```
[isim] merhaba, şu an uygun değilseniz başka bir zaman 
iletişime geçeyim. Bana uygun bir zaman söyler misiniz?
```

**3. denemeden sonra 7 gün bekle.** Sonra soğuk havuza al.

## 5. Lead Durum Güncelleme

Her adımda lead'in CRM statüsü güncellenir.

| Adım | CRM Statüsü | Açıklama |
|:-----|:------------|:---------|
| WhatsApp mesajı gönderildi | `contacted_whatsapp` | İlk temas yapıldı, kanal WhatsApp |
| Telefon arandı | `contacted_phone` | Telefonla arandı |
| Cevap geldi | `replied` | Lead cevap verdi (kanaldan bağımsız) |
| Görüşme planlandı | `booked` | Randevu alındı |
| Cevap yok (7 gün) | `cold` | Soğuk havuza alındı |
| Email sonradan bulundu | `email_enriched` | Email bulundu, outreach kanalı değişti |
| Lead kaydı güncellendi | — | Telefon/email/not bilgisi güncellendi |

**Not:** Statüler CRM'de manuel veya subagent aracılığıyla güncellenir. AgencyOS'de lead statü alanı varsa oraya yazılır. Yoksa feed'de kayıt tutulur.

## 6. Cevap Gelirse Ne Olur?

| Cevap Türü | Ne Yapılır? |
|:-----------|:------------|
| **"Ne yapıyorsunuz?" / "Anlatın"** | Kısa bir ErgeneAI tanıtımı yap (2 dk). Lead'in ihtiyacını sor. Randevu al. |
| **"İlgilenmiyorum"** | "Teşekkürler, zaman ayırdığınız için. İlerde ihtiyaç olursa ulaşın." Lead'i "replied_not_interested" statüsüne al. 90 gün sonra tekrar dene. |
| **"Şu an müsait değilim"** | "Ne zaman uygun olursunuz?" Alınan saati CRM'e not et. O tarihte tekrar dene. |
| **"Fiyat nedir?"** | Erken fiyat sorusu. "Öncelikle ihtiyacınızı anlamak isterim. Kısa bir görüşme ayarlayabilir miyiz?" Fiyatı görüşmeye bırak. |
| **"Detaylı bilgi gönderin"** | Kısa bir broşür/döküman hazırla (Estetik'ten destek al). PDF olarak WhatsApp'tan gönder. 3 gün sonra takip et. |

**Cevap gelirse lead'in durumu `replied` olarak güncellenir ve sıradaki adıma geçilir.**

## 7. Cevap Gelmezse Ne Olur?

| Aşama | Süre | Ne Yapılır? |
|:------|:-----|:------------|
| İlk WhatsApp | 0. gün | Mesaj gönder |
| Takip 1 | 3. gün | Kısa hatırlatma (bkz. Bölüm 4) |
| Telefon ara | 5. gün | Doğrudan ara (WhatsApp değil) |
| Takip 2 | 7. gün | Son WhatsApp mesajı |
| Soğuk havuz | 14. gün | Lead "cold" statüsüne al |
| Aylık deneme | 30 gün sonra | 1 WhatsApp mesajı daha dene |

**Toplam 3 WhatsApp + 1 telefon = 4 deneme.** Sonra soğuk havuz.

**Soğuk havuza alınan lead'ler ayda 1 kez tekrar denenir.** Max 6 ay (toplam 6 deneme). 6 ay sonra tamamen arşivlenir.

## 8. Email Sonradan Bulunursa

Email sonradan bulunursa akış şöyle değişir:

```
Email bulunduğu an:
1. Lead CRM'de güncellenir (email alanı doldurulur)
2. Lead'in outreach kanalı WhatsApp/Telefon → Email olarak değiştirilir
3. WhatsApp/Telefon kuyruğundan çıkarılır
4. Email outreach kuyruğuna eklenir

İstisna:
- Eğer lead zaten WhatsApp'ta cevap verdiyse → Email'e geçilmez, 
  mevcut kanaldan devam edilir (lead'in tercihine saygı)
- Eğer lead hiç cevap vermediyse → Email'e geçilir (yeni bir kanal denenmiş olur)
```

**Email bulma yöntemleri:**
- Manuel website tarama (SOP: lead-enrichment-pipeline.md)
- Hunter.io domain search (API key varsa)
- Lead'in kendisi WhatsApp'ta email'ini paylaşırsa (cevap gelince)

## 9. AgentMemory Kaydı

Şu olaylar AgentMemory'ye otomatik kaydedilir:

| Olay | Kaydedilecek Ders |
|:-----|:-----------------|
| WhatsApp outreach başlatıldı | "WhatsApp outreach: [lead sayısı] lead'e mesaj gönderildi. Tarih: [tarih]" |
| Telefon görüşmesi yapıldı | "Telefon görüşmesi: [lead adı] — [kısa not]. Tarih: [tarih]" |
| Lead cevap verdi | "Lead cevap verdi: [lead adı] — [cevap türü]. Tarih: [tarih]" |
| Lead soğuk havuza alındı | "Lead soğudu: [lead adı] — [sebep]. Tarih: [tarih]" |
| Email sonradan bulundu | "Email bulundu: [lead adı] — [email]. Kanal WhatsApp → Email değişti. Tarih: [tarih]" |

**Kaydedilmez:**
- Her mesaj gönderimi (gürültü)
- "Cevap yok" durumu (soğuk havuza alınınca kaydedilir)
- Rutin durum güncellemeleri

## 10. Uygulama Notu

| Alan | Değer |
|:-----|:------|
| **Kapsam** | 31 emailsiz lead. Telefonu olan ~29 lead |
| **İlk adım** | Diş klinikleri ve otellerle başla (en sıcak sektörler) |
| **Kanal önceliği** | WhatsApp > Telefon > Email (sonradan bulunursa) |
| **Mesaj sayısı/lead** | Max 3 WhatsApp + 1 telefon = 4 deneme |
| **Soğuk havuz süresi** | 14 gün sonra. Ayda 1 deneme, max 6 ay |
| **Başarı kriteri** | 31 lead'den ≥5 replied (%15) + ≥1 booked (%3) |
| **Hata durumu** | Telefon yanlışsa lead "ulaşılamaz" statüsüne alınır |
| **CRM** | AgencyOS'de statü güncellemesi manuel yapılır |
| **İlgili SOP** | lead-enrichment-pipeline.md (email bulunursa devreye girer) |
| **Risk** | Düşük. WhatsApp outreach agresif satışa dönmezse sorun yok. |

---

Bu SOP onaylanırsa uygulama aşamasına geçebilirim.
