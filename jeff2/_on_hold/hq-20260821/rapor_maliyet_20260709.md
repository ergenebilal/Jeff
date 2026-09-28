# 💰 HAZİNE RAPORU
**Dönem:** 08-09 Temmuz 2026 (son 24h)
**Hazırlayan:** Maliyetçi (Hazine Departmanı)
**Tarih:** 2026-07-09T10:41

---

## 1. Token & AI Maliyeti

| Kalem | Değer |
|-------|-------|
| **AI Maliyeti (24s)** | **~$0.00** |
| **AI Maliyeti (7g)** | **~$0.001** |
| **Tahmini Günlük (normal)** | ~150K token ≈ **~$0.04** |
| **Kullanılan Model** | DeepSeek V4 Flash ($0.14/M input, $0.55/M output) |

> ⚠️ Maliyetler Hermes aktivitesine dayalı tahmindir. Kesin tüketim DeepSeek dashboard'dan kontrol edilmelidir.
> AI maliyeti şu an ihmal edilebilir seviyede.

## 2. Enrichment Maliyeti

| Kalem | Değer |
|-------|-------|
| **ENRICHMENT_LOG kaydı** | **VERİ YOK** |
| **Toplam enrichment maliyeti** | **Hesaplanamadı** |
| **Lead başı maliyet** | **Hesaplanamadı** |

**🔴 SORUN:** feed.jsonl'de (139 satır taranmıştır) hiç `ENRICHMENT_LOG` satırı bulunamamıştır.
- Hırslı, enrichment log standardını (`SPEC_SOP_UYUM_COST_LOGGING.md`) henüz uygulamamıştır.
- Çapraz kontrol (09.07.2026): *"enrichment API kaydı yok 🟡 maliyet takipsiz"*
- Enrichment maliyeti hesaplanamadığı için ROI, lead başı maliyet, provider verimliliği raporlanamıyor.

## 3. Provider Verimliliği

| Provider | Call | Email Bulunan | Maliyet | Verim |
|----------|:----:|:-------------:|:-------:|:-----:|
| web_extract | — | — | — | **Veri yok** |
| hunter/apollo | — | — | — | **Veri yok** |

**🔴 Enrichment log'u olmadığı için provider verimliliği hesaplanamadı.**

## 4. Alarm Eşikleri

| Eşik | Limit | Gerçekleşen | Durum |
|:----|:----:|:-----------:|:-----:|
| Günlük enrichment $1 🟡 | $1.00/gün | Hesaplanamadı | 🟡 Veri yok |
| Haftalık enrichment $5 🔴 | $5.00/hafta | Hesaplanamadı | 🟡 Veri yok |
| Lead başı $0.50 🔴 | $0.50/lead | Hesaplanamadı | 🟡 Veri yok |
| **Haftalık hata oranı** 🟡 | %35 deseni | **%35** | **🟡 AKTİF** |
| Enrichment logsuz geçen süre | 0 gün | 1+ gün | **🟡 MALİYET KARA DELİĞİ** |

## 5. Veto Durumu

| Kriter | Durum |
|--------|-------|
| $10+ tek seferlik harcama | **Bulunamadı** — veto edilecek harcama yok |
| Tüm harcamalar | $0.00 seviyesinde (AI maliyeti ihmal edilebilir) |

## 6. Önceki Maliyetçi Raporu Özeti

Son Maliyetçi bildirimi (09.07.2026 01:16):
- AI Maliyeti (24s): ~$0.00
- AI Maliyeti (7g): ~$0.001
- Onay bekleyen: 2 task
- Alarm: 🟡 haftalık hata oranı %35

---

## 7. Özet ve Öneriler

| Alan | Durum | Not |
|:-----|:-----:|:----|
| AI Maliyeti | 🟢 | İhmal edilebilir ($0.00/gün) |
| Enrichment Maliyeti | 🔴 | **Enrichment log'u tutulmuyor** |
| Provider Verimliliği | 🔴 | Log olmadan hesaplanamaz |
| Hata Oranı | 🟡 | Haftalık hata deseni %35 |
| Onay Bekleyen | 🟡 | 2 task (dijital ürün fikri + gelir kanalı fizibilite) |

**Tasarruf Önerisi:**
1. **Hırslı'nın ENRICHMENT_LOG implementasyonu hızlandırılmalı** — spec (SPEC_SOP_UYUM_COST_LOGGING.md) yazıldı ama uygulanmadı. Maliyet denetimi için bu kritik.
2. **Haftalık hata %35 deseni araştırılmalı** — Bilge ile ortak desen, sebebi tespit edilip düzeltilmeli.
3. **Maliyet şu an sorun değil** — DeepSeek V4 Flash çok ucuz, günlük harcama ~$0.04 civarı.

> **Veto:** $10+ harcama bulunamadı, veto uygulanmadı.
> **Gizlilik:** Kasa/borç verisi feed'e yazılmadı, charter'da kaldı.
