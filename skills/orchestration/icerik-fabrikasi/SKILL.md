---
name: icerik-fabrikasi
version: 1.1.0
author: Jeff
description: Multi-agent içerik üretim pipeline'ı — delegate_task ile paralel görsel içerik fabrikası. Orkestra şefi modeli.
---

# İçerik Fabrikası

## Trigger
- Instagram/LinkedIn/Twitter için görsel içerik üretilecekse
- Birden fazla sektöre aynı anda içerik lazımsa
- "Bana içerik üret" dendiğinde

## Mimari (Orkestra Şefi Modeli)

Jeff kod yazmaz, işi dağıtır:

```
Jeff → delegate_task(tasks=[Agent1, Agent2])
  ├─ Agent 1: Görsel motoru (HF Space tarama + en iyi aracı bul)
  └─ Agent 2: İçerik üretici (sektör konsepti + görsel + overlay + Telegram)
```

## Batch 1: Görsel Motoru

```python
goal = "En kaliteli ÜCRETSİZ görsel üretim aracını bul ve endpoint yap"
context = """
- HF API server: /opt/hermes/scripts/hf_tools/, port 8767
- HF_TOKEN ~/.hermes/.env'de
- Pollinations.ai çalışıyor ama düşük kalite (fallback)
- gradio_client ile HF Space'leri dene
- En iyi 2-3 Space'i seç, fallback zinciri kur
- /hf/image-gen-smart endpoint'i ekle
"""
toolsets = ["terminal", "file", "web"]
```

## Batch 2: İçerik Üretici

```python
goal = "X sektör için 5 slidelık carousel üret"
context = """
- Format: 1080x1350, 5 slide
- Yapı: kapak → problem → çözüm → değer → CTA
- Görsel: Pollinations.ai (https://image.pollinations.ai/prompt/{encoded})
- Overlay: HTML+CSS, Playwright screenshot
- Çıktı: /tmp/ergeneai_carousels/slides_output/
- Sektörler: her biri ayrı, öncekilerden farklı
"""
toolsets = ["terminal", "file", "web"]
```

## Başarılı Format (Bilal Onaylı) — Track 1: Sorun→Çözüm

| Slide | Tür | Örnek |
|-------|-----|-------|
| 1 | Kapak | "Hastalarınız Randevuyu Unutuyor mu?" + %25 istatistik |
| 2 | Problem | Her unutulan randevu = kayıp gelir |
| 3 | Çözüm | Otomatik hatırlatma sistemi |
| 4 | Değer | Ayda X TL kazanç artışı |
| 5 | CTA | "Hemen ücretsiz demo alın" |

Renk paleti: Yeşil-Beyaz-Siyah. Kurumsal, modern, okunaklı.

## Başarılı Format — Track 2: Araç/Ajan Tanıtımı

| Slide | Tür | Örnek |
|-------|-----|-------|
| 1 | Kapak | "Telefonla Konuşan Asistan: Sesi Var, Sabrı Sonsuz" |
| 2 | Hikaye/Sorun | "Hayal et: telefon çalıyor, sen meşgulsün" |
| 3 | Göster | 3 adımda kurulum / nasıl çalıştığı |
| 4 | Değer | 7/24 çalışır, maaş istemez, asla yorulmaz |
| 5 | CTA | ergeneai.com |

⚠️ **Track seçimi:** İçerik tekrarladığında Track değiştir. İkisini aynı anda kullanma. |

Renk paleti: Yeşil-Beyaz-Siyah. Kurumsal, modern, okunaklı.

## Sektör Rotasyonu

Aynı sektörü tekrar etme. Sırayla:
Güzellik → Klinik → Restoran → Diş → Oto Kuaför → Otel → Okul → Spor → Emlak → Hukuk → ...

## Kalite Standardı (Bilal Onaylı Minimum Bar)

**Kalite kontrol artık 3 katmanlı sistemle çalışır.**
Detay: `product/visual-quality-surgery` -> `references/kalite-kontrol-pipeline.md`

5 sektör pilot seti (diş, oto kuaför, otel, okul, spor) = **TABAN**. Altı geçemez.

| Kriter | Standart |
|--------|----------|
| Arka plan | Profesyonel stok/üretim + koyu overlay |
| Renk | Yeşil-beyaz-siyah |
| Tipografi | Sans-serif, mobil okunaklı, Türkçe |
| Formül | Pain point + istatistik (%'li kutu) |
| Yapı | kapak → problem → çözüm → değer → CTA |
| Boyut | 1080×1350px |
| Dil | Temiz Türkçe, yazım hatası yok |

Bu standardın ALTINDAKİ hiçbir iş Bilal'in önüne düşmez. Sessizce tekrar yaptır.

Bilal'in önüne sadece onaylanmış iş düşer. Akış:

```
Subagent işi bitirir
  → Jeff sonuçları denetler
    → vision_analyze ile görsel kalite kontrolü
    → Metinler Türkçe, okunaklı, yazım hatası yok mu?
    → Renk paleti, tasarım, profesyonellik
  → BAŞARILI: Bilal'e sun
  → BAŞARISIZ: Subagent'a geri gönder, düzelt
```

Asla: "Subagent yaptı" diye Bilal'e ham sonuç iletme.

## Referanslar
- `references/ai-araclari-icerik-plani.md` — Track 2 (Araç/Ajan tanıtımı) içerik planı, daily_ig.py'deki WEEKLY_THEMES ile senkronize

## Direkt Yürütme Modu (Subagent'sız)

Subagent scaling (delegate_task) büyük batch'ler için idealdir. Tek bir post veya carousel üretirken **doğrudan kod yaz** — daha hızlı, daha kontrollü, daha az context harcar.

| Özellik | Subagent Modu | Direkt Mod |
|----------|--------------|------------|
| Ne zaman | Batch 3+ post, paralel sektör | Tek post, carousel, revizyon |
| Hız | Yavaş (delegasyon overhead) | Hızlı (tek script) |
| Kontrol | Subagent çıktısını denetle | Render'ı direkt doğrula |

**Direkt mod akışı:**
1. Render script'i yaz (Pillow compositing)
2. Terminal'de çalıştır
3. vision_analyze veya pixel check ile doğrula
4. Gerekirse patch ile düzelt
5. Onay sonrası cron job'a ekle

## Carousel Üretimi (Post 1+2 Onaylı)

### İçerik Rotasyonu
| Sıra | Track | Format | Örnek |
|------|-------|--------|-------|
| Post 1 | **Track 1** — Sorun→Çözüm | Cover → KAYIP → ÇÖZÜM → SONUÇ → CTA | "Sisteminiz Sizi Yavaşlatıyor" |
| Post 2 | **Track 2** — Eğitim/Rehber | Cover → KURAL 1 → KURAL 2 → KURAL 3 → CTA | "Dijital Dönüşümün 3 Temel Kuralı" |
| Post 3+ | Rotasyon | Track 1 ↔ Track 2 değiş, asla üst üste aynı | |

Track değiştirirken badge ve hook yapısı da değişir: Track 1 badge'leri (OPERASYON/KAYIP/ÇÖZÜM) ticari tension taşır, Track 2 badge'leri (EĞİTİM/KURAL 1/KURAL 2/KURAL 3) eğitim tonundadır.

### Arka Plan Kuralı (06.07.2026)
**Her post'un arka planı konuyla tematik olarak bağdaşmalı.** Başka post için üretilmiş bg'yi farklı konuda kullanma.

| Post Konusu | Background Prompt | Kullanılmaz |
|-------------|------------------|-------------|
| Operasyon/işletme | Dark office, iş masası, moody | Dental klinik ⛔ |
| Dijital dönüşüm | abstract corporate, gradient | Klinik/salon ⛔ |
| Sektörel (diş) | Sakin klinik, doğal ışık | Ofis ⛔ |

Test: Background'u görünce "bu post ne hakkında?" sorusuna cevap veriyor mu? Vermiyorsa alakasız.

### Mobil Ölçekleme (1024×1024 canvas)
Carousel postlarında telefon ekranında (375-430 CSS px) okunurluk için minimum boyutlar:

| Element | Minimum | Post 1 Onaylı |
|---------|---------|---------------|
| Card genişlik | ≥%90 | %90 (922px) |
| Hook font | ≥100px | **105px** |
| Liste metni | ≥28px | **28px** |
| Badge | ≥20px | **20px** |
| Title | ≥50px | **50px** |
| Hook line spacing | ≥110px | **115px** |
| URL font | ≥20px | **22px** |
| Logo | ≥100px | **110px** |

%78 card + 88px hook telefon ekranında çok küçük kalır. İlk sürümde her zaman büyüt.

### Layout Freeze Kuralı (06.07.2026)
**Approved layout = frozen during polish.** "Final polish" = α/overlay/glow/spacing ince ayarı, layout değil.

| İzinli (polish) | Yasak (layout change) |
|-----------------|----------------------|
| Card opacity (α) | Logo position |
| Overlay gücü | Badge text içeriği |
| Shadow alpha | Card alignment |
| Inner glow | Top border presence |
| Font size (±10%) | Accent color |

Layout değişikliği gerekiyorsa: **"Layout değişikliği öneriyorum"** de ve ayrı onay al.

### URL Pill Text Ortalama (Kritik)
Padding-based positioning (`(ux0 + pp, uy0 + pp)`) text'i round corner'dan taşmış gösterir. Exact centering kullan:

```python
ub = d.textbbox((0, 0), url, font=fu)
uw = ub[2] - ub[0]
text_h = ub[3] - ub[1]
tx = ux0 + (pw - uw) // 2
ty = uy0 + (pill_h - text_h) // 2 - ub[1]   # - ub[1] ZORUNLU
d.text((tx, ty), url, font=fu, fill=WHITE)
```

`- ub[1]` olmadan text görsel olarak kutunun altına kayar.

## Günlük Teslimat (Cron)

Her sabah 08:00'de tüm postlar @ergeneaiicerik_Bot'a otomatik gönderilir.

### Akış
```
08:00 — Cron tetiklenir → delivery script render eder → agent MEDIA+caption gönderir
```

### Setup
- Script: `~/.hermes/scripts/post1_daily_delivery.sh`
- Render script'leri: `render_carousel_v3.py` (Post 1), `render_post2_v3.py` (Post 2)
- Cron: `0 8 * * *`, deliver=all
- Caption ve etiketler delivery script içinde gömülü
- Yeni post üretildikçe delivery script + cron prompt güncellenir

## Referanslar
- `references/ai-araclari-icerik-plani.md` — Track 2 (Araç/Ajan tanıtımı) içerik planı, daily_ig.py'deki WEEKLY_THEMES ile senkronize
- `references/post1-post2-production-params.md` — Post 1+2 onaylı parametreler ve render script referansları
- `references/pipeline-health-check.md` — Teslimat teşhis referansı: token/credential varlığı, cron kaydı, delivery vs generation gap tespiti, content plan exhaustion diagnosis, batch kurtarma

## Pitfalls
- Subagent "interrupted" dönebilir ama işi yapmış olabilir — dosyaları kontrol et
- Görselleri vision_analyze ile doğrula (kalite kontrol)
- Kalite filtresinden geçmeyen içeriği Bilal'e gösterme — sessizce tekrar yaptır
- Max 3 paralel task, 4+ ise chunk'la
- **İçerik tekrarı tuzağı (20.06.2026):** Kullanıcı "içerik konuları kendini tekrar ediyor" dedi. Sebep: WEEKLY_THEMES hep aynı Track 1 (Sorun→Çözüm) formatını döndürüyordu. Çözüm: Track 2 (Araç/Ajan tanıtımı) eklendi. **Bir track'te 1 haftadan fazla kalma.**
- **Güncellenmeyen içerik planı (20.06.2026):** Eski temaları sil, yenilerini ekle. Sadece bg_keyword değiştirmek yetmez.
- **Layout değişikliği tuzağı (06.07.2026):** "Final polish" adı altında logo position/badge text/ border presence değiştirme — kullanıcı "bunu onaylamama rağmen bozdun" dedi. Layout = frozen approval.
- **Arka plan uyumsuzluğu (06.07.2026):** İşletme postunda dental klinik bg kullanma. Kullanıcı: "Arkaplan konuyla bağdaşmalı."
- **Mobil ölçek (06.07.2026):** 1024 canvas'ta %78 card + 88px hook telefondan küçük. %90 card + 100+px hook ile başla.
- **URL pill taşması (06.07.2026):** Padding ile konumlandırma text'i round corner'dan taşırmış gösterir. Exact centering + `-ub[1]` kullan.
