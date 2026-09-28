# Jeff 2.0 — Haftalık Durum Raporu
**Dönem:** 20-27 Temmuz 2026
**Hazırlayan:** Hermes (otonom cron)
**Tarih:** 27.07.2026 09:10 UTC

---

## 1. 🎯 Board Durumu (tasks.jsonl)

| Kategori | Adet | Detay |
|----------|------|-------|
| **Tamamlanan** | 7 | Hırslı(1), Estetik(2), Pragmatik(2), Maliyetçi(2), Bilge(2) — lead enrichment, post konsepti, test, SOP |
| **Aktif** | 7 | 5 kabine task'ı (lead tarama, enrichment, dijital ürün) + cron'lar |
| **Onay Bekleyen** | 2 | Dijital ürün fikri (Estetik), Yeni gelir kanalı fizibilite (Maliyetçi) |
| **Takıldı** | 4 | 09.07 batch'inde subagent timeout + provider hatası |
| **Toplam** | 21 | (1 lead data entry hariç) |

**Trend:** İlk batch %89 tamamlanma oranı yakalamıştı ancak 09.07'deki subagent timeout krizi 4 task'ı takılı bıraktı. Provider hatası (deepseek-v4-flash `ProviderModelNotFoundError`) çözüldü, o task'ların rerun'u gerekli.

---

## 2. ⚙️ Gelir Motorları

| Motor | Durum | Üretim | Detay |
|-------|-------|--------|-------|
| **Hizmet Motoru** | ✅ Charter hazır | 27 lead pipeline | Lead_pipeline_1.jsonl'de 27 kayıt, 4 email var, 12 telefon var. Yüksek öncelikli 12 lead. |
| **İçerik ve Talep Motoru** | ✅ Charter hazır | 2 post konsepti | Otel sektörü + KOBİ carousel konsepti hazır. Onay bekliyor. |
| **Dijital Ürün Motoru** | 🔴 Pasif | Fikir aşaması | Estetik'te onay bekleyen dijital ürün fikri task'ı var. |
| **Fırsat Deney Motoru** | 🔴 Pasif | Fizibilite aşaması | Maliyetçi'de onay bekleyen yeni gelir kanalı fizibilite task'ı. |

**Bu hafta eklenen yeni katmanlar (v3.1):**

| Katman | Durum | Açıklama |
|--------|-------|----------|
| goal_engine | ✅ Aktif | Hedef → task dönüşümü (goal_manager.py + goal_metrics.py) |
| decision_engine | ✅ Aktif | Structured karar pipeline (26 kayıt, decisions.db) |
| business_intelligence | ✅ Aktif | cost_analyzer.py + performance_dashboard.py |
| optimization_engine | ✅ Aktif | worker_optimizer.py — performans + token optimizasyonu |
| telemetry | ✅ Aktif | telemetry_logger.py — 9 olay kaydı, %88.9 başarı |
| hypothesis_engine | ✅ Aktif | hypothesis_manager.py — fikir → puanla → uygula |
| experience_engine | ✅ Aktif | experience_pipeline.py — hata → SOP |
| knowledge_graph | ✅ Seed | 26 node seed'li ilişkisel hafıza |

**Beklemede** (_on_hold/): prediction_engine, simulation_engine, multi_tenant, marketplace

---

## 3. 👷 Worker Profilleri

| Worker | Görev | Durum | Detay |
|--------|-------|-------|-------|
| **outreach** | Lead tarama, outbound | ✅ Cron aktif | Haftalık cron çalışıyor |
| **kodcu** | Kod, deploy, altyapı | ✅ Hizmet Motoru cron'u aktif | Sistem bakım görevleri |
| **analyst** | Token, maliyet, rapor | ✅ Token dashboard cron aktif | Maliyetçi raporu 09.07'de yayınlandı |
| **master** | Strateji, kalite, self-improvement | 🔄 Dijital Ürün task'inde | Telemetry: 1200ms task, 3400ms LLM call |
| **kesif** | Araştırma, fırsat keşfi | ⏸️ Boşta | Pazar araştırması yapabilir (cache hit: true) |
| **scraper** | Lead scraping | ⏸️ Boşta | Apify'da timeout sorunu yaşadı |

**Circuit Breaker Durumu (tümü closed):** buyume, icerik, teslimat, finans, hafiza, hunter, whatsapp — hepsi sağlıklı.

---

## 4. 💰 Token & Maliyet Özeti

| Kalem | Değer |
|-------|-------|
| **AI Maliyeti (bu hafta)** | ~$0.004 (tahmini) |
| **AI Maliyeti (tüm zamanlar - 23.07'den beri)** | ~$0.00364 (telemetry'den) |
| **Model** | DeepSeek V4 Flash ($0.14/M input) |
| **Worker Maliyeti** | $0.00 (opencode-go ücretsiz) |
| **Sunucu** | $0.00 (mevcut altyapı) |
| **Toplam İşletme Maliyeti** | **~$0.00/hafta** |

**Token Koruma:** Token guard sessiz (harcama limitinin çok altında). Bütçe kullanımı: %1 altı.

**Sunucu Sağlığı:**
- RAM: 31G toplam / 25G kullanım / 5.5G available
- Disk: 276G toplam / 141G kullanım (%54) — temizlik sonrası iyi durumda
- Uptime: 40 gün
- Servisler: agentmemory, xurl MCP (X API), HF API server — hepsi çalışıyor

---

## 5. 🧠 Kararlar & Dersler

**Alınan Kararlar (26 kayıt, decisions.jsonl):**
- Ameliyat Sistemi v1.0 kabul edildi — yapısal değişiklikler spec → onay → uygulama
- Gelir motorları pasife alındı — önce iç yapı kurulsun
- Onay sınırları belirlendi (yeşil/sarı/kırmızı)
- Maliyetçi'nin veto yetkisi sınırlandı
- Multi kazanç sistemi hedefi — en az 3 farklı kanal
- Bakan isimleri sade sıfata dönüştürüldü

**Aktif Dersler (lessons_registry.jsonl, 7 kayıt):**
| Ders | Durum | Özet |
|------|-------|------|
| web_extract verimsiz | 🔴 Active | Otel sitelerinde %0 başarı |
| email enrichment kıtlığı | 🔴 Active | 31/40 lead emailsiz |
| subagent timeout | ✅ Confirmed | 120sn 3+ kez, 1 retry yeterli |
| enrichment log kaydı | 🔴 Active | Log yoksa maliyet kara delik |
| feed format kuralı | 🔴 Active | Max 200 karakter, emoji+sonuç |
| hafıza birleştirme | ✅ Resolved | %95 → %58'e düşürüldü |
| buyume circuit breaker | 🔴 Active | 3 başarısız çağrıda açılır |

---

## 6. 📋 Pipeline Durumu

| Metrik | Değer | Hedef | Durum |
|--------|-------|-------|-------|
| Toplam Lead | 27 | 50+ | 🟡 Yolda |
| Email Sahibi | 4 | - | 🔴 Çoğu emailsiz |
| Telefon Sahibi | 12 | - | 🟡 |
| Yüksek Öncelikli | 12 | - | 🟢 |
| Ortalama Yanıt Süresi | 2.0sn | - | 🟢 |
| Telemetry Başarı | %88.9 | - | 🟡 |

---

## 7. 🔮 Önümüzdeki Hafta — Öneriler

1. **4 takılı task'ı rerun et** — Provider hatası çözüldü, subagent SOP fallback test edildi, yeniden dene.
2. **Email enrichment'e odaklan** — 27 lead'den sadece 4'ünde email var. Web_extract yetersiz, alternatif kanal gerek.
3. **Onay bekleyen 2 task'ı Bilal'e hatırlat** — Dijital ürün fikri + yeni gelir kanalı fizibilite bekliyor.
4. **Hizmet Motoru'nu ilk gelire taşı** — Pipeline hazır, 12 yüksek öncelikli lead var. Outbound başlatılabilir.
5. **Telemetry verisini düzenli topla** — 9 olay iyi başlangıç, haftada 50+ olaya çıkılmalı.
6. **Optimization engine'i devreye al** — worker_optimizer.py hazır, test edilmeyi bekliyor.
7. **Knowledge graph'i besle** — 26 node seed, ilişkisel hafıza için daha fazla veri gerekli.

---

## 8. ⚠️ Riskler

- **🔴 Enrichment log kara deliği** — Maliyetçi'nin raporladığı gibi, enrichment maliyeti hala takipsiz
- **🟡 Aktif task sayısı düşük** — 7 aktif task'ın çoğu idle/cron seviyesinde, yeni iş girişi gerekli
- **🟡 Post konseptleri onaysız** — 2 hazır konsept Bilal'in onayını bekliyor, içerik akışı tıkalı
- **🟢 AI maliyeti sıfır** — DeepSeek V4 Flash ile bu böyle devam eder
- **🟢 Sunucu sağlıklı** — 40 gün uptime, tüm servisler ayakta

---

*Rapor otomatik oluşturulmuştur. Telemetry, task, ledger ve pipeline verileri canlı okunmuştur.*
