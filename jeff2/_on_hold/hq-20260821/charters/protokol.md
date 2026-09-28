# ErgeneAI Kabinesi — Karar ve Onay Protokolü

## 1. Karar Hiyerarşisi

```
🔴 CEO (Bilal)
  Stratejik, geri dönüşü olmayan, maliyetli, marka riski taşıyan kararlar.
  
  🟡 Patronus (Ben)
    Operasyonel koordinasyon, kalite kapısı, risk yönetimi, bakanlar arası çakışma çözümü.
    
    🟢 Bakan (Hırslı/Estetik/Pragmatik/Maliyetçi/Bilge)
      Kendi alanında rutin kararlar, günlük işletme, raporlama.
      
        ⚪ İşçiler (OpenCode/subagent/n8n)
          Fiziksel icra, kod, scraping, render — karar yok, sadece yürütme.
```

## 2. Karar Türleri ve Geçiş Yolları

| Tür | Örnek | Yetki | Süreç |
|-----|-------|-------|-------|
| **Rutin** | Lead ekleme, post üretme, token raporu | 🟢 Bakan | Kendi başına, Patronus'a bilgi |
| **Taktik** | Email gönderme, deploy, segment açma | 🟡 Patronus | Bakan önerir → Patronus onaylar |
| **Stratejik** | Fiyat değişimi, ürün lansmanı, motor kapatma | 🔴 Bilal | Bakan analiz → Patronus değerlendir → Bilal karar verir |

## 3. Onay Gerektiren Durumlar (Gates)

Bir karar aşağıdaki kriterlerden birini taşıyorsa **gate** gerektirir:

| Kriter | Gate | Açıklama |
|--------|------|----------|
| Maliyet > $10 | 🟡 Patronus | Hazine raporu + Patronus onayı |
| Maliyet > $50 | 🔴 Bilal | Hazine + Patronus + Bilal |
| Marka riski | 🔴 Bilal | Sosyal medya paylaşımı, yayın |
| Veri kaybı riski | 🟡 Patronus | Silme, truncate, reset |
| Müşteri teması | 🟡 Patronus | Email, DM, telefon |
| Dış dünyaya açılım | 🔴 Bilal | Hesap açma, ödeme, üyelik |
| Bakanlar arası çakışma | 🟡 Patronus | İki bakan aynı kaynak için yarışıyorsa |

## 4. Acil Durum Protokolü

Eğer bir bakan "bu acil" derse:

```
1. Bakan durumu işaretler (Feed'de 🔴 etiketi)
2. Patronus 5dk içinde yanıt vermezse bakan kendi inisiyatifiyle hareket edebilir
3. Ancak aldığı aksiyonu derhal raporlamalıdır
4. Hatalı karar durumunda sorumluluk bakana aittir
```

Acil durum tanımı: Sistem kesintisi, müşteri şikayeti, güvenlik açığı, gelir kaybı.

---

# Action Ledger — Aksiyon Kaydı ve Sahiplik Mantığı

## 1. Her Aksiyonun Sahibi Olmalı

Bir aksiyon ya bir bakana ya Patronus'a aittir. Sahipsiz aksiyon = yapılmamış aksiyon.

## 2. Action Ledger Formatı

Tüm aksiyonlar feed.jsonl üzerinden kaydedilir. Format:

```json
{
  "timestamp": "2026-07-08T01:30:00",
  "sahip": "📈 Hırslı",
  "aksiyon": "Email enrichment başlattı",
  "hedef": "İbrahim Erayhan (lead-...q5jvco)",
  "durum": "tamam",
  "not": "info@ibrahimerayhansacekimi.com bulundu, CRM'e işlendi",
  "onay_gerekiyor": false,
  "motor_etkisi": "Hizmet Motoru"
}
```

## 3. Ledger Durum Kodları

| Kod | Anlamı |
|-----|--------|
| ✅ **tamam** | Aksiyon tamamlandı, sonuç alındı |
| ⏳ **beklemede** | Patronus/CEO onayı bekliyor |
| 🔄 **çalışıyor** | Devam eden aksiyon (subagent çalışıyor) |
| ❌ **başarısız** | Aksiyon denendi ama başarısız |
| ⛔ **red** | Onaylanmadı veya iptal edildi |
| 📋 **plan** | Henüz başlamadı, backlog'da |

## 4. Haftalık Ledger Review (Pazartesi)

Her pazartesi:
1. Bilge (Arşiv Bakanı) haftalık ledger'ı analiz eder
2. Tamamlanan aksiyonlardan ders çıkarır
3. Başarısız aksiyonları işaretler
4. Desen varsa SOP'laştırır
5. Patronus'a review raporu sunar

## 5. Sorumluluk Zinciri

```
Hata oluşursa:
1. İşçi hatası → Bakan sorumlu (denetim eksik)
2. Bakan hatası → Patronus sorumlu (yönlendirme eksik)
3. Patronus hatası → Bilal devreye girer

Hiçbir hata "AI yaptı" diye geçiştirilmez.
Her hatanın bir sahibi ve bir dersi vardır.
```
