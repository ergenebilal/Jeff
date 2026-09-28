# ErgeneAI İçerik Üretim Stratejisi
## Dijital Yönetici Raporu — 9 Eylül 2026

---

## 1. HEDEF

- **12 Instagram carousel gönderisi** (4 hafta x 3 gönderi)
- **Aynı tasarım stili**: Koyu tema, minimal, profesyonel
- **Farklı konular**: Önceki gönderilerle çakışma yok

---

## 2. KULLANILACAK ARAÇLAR VE AKIŞ

### A. ARAŞTIRMA AŞAMASI (Her gönderi için)

#### 1. **web_search** — Güncel Veri ve İstatistik
- **Ne için**: Konuyla ilgili son veriler, raporlar, istatistikler
- **Örnek**: "AI kullanan işletmeler gelir artışı 2026 istatistikleri"
- **Nasıl**: Her gönderi öncesi 3-5 arama yapacağım
- **Çıktı**: Sayılar, yüzdeler, kaynaklar

#### 2. **web_extract** — Makale ve Rapor Analizi
- **Ne için**: Derinlemesine içerik okuma, vaka çalışmaları
- **Örnek**: McKinsey AI raporu, Gartner analizi
- **Nasıl**: web_search'den gelen linkleri çekeceğim
- **Çıktı**: Detaylı bilgi, alıntılar, veriler

#### 3. **notebooklm** — Derin Araştırma
- **Ne için**: Kapsamlı konu araştırması
- **Örnek**: "Restoranlarda AI kullanımı rehberi"
- **Nasıl**: Deep research modunda araştırma
- **Çıktı**: 10+ kaynak, sentezlenmiş bilgi

### B. İÇERİK ÜRETİM AŞAMASI

#### 4. **AI Modeli (mimo-v2.5)** — Metin Yazımı
- **Ne için**: Carousel metinleri, caption, hashtag'ler
- **Örnek**: "5 slide'lık carousel metni yaz"
- **Nasıl**: Araştırma çıktısını AI'a vereceğim
- **Çıktı**: 5-7 slide metni, caption, hashtag'ler

#### 5. **n8n Workflow** — Otomatik Pipeline
- **Ne için**: İçerik üretim otomasyonu
- **Örnek**: "ErgeneAI Content Pipeline" webhook'u
- **Nasıl**: POST isteği ile içerik talebi
- **Çıktı**: Formatlanmış içerik, JSON olarak

### C. GÖRSEL ÜRETİM AŞAMASI

#### 6. **fal** — AI ile Görsel Üretimi
- **Ne için**: Carousel görselleri
- **Örnek**: "Koyu tema, minimal, neon vurgulu görsel"
- **Nasıl**: Prompt ile görsel üreteceğim
- **Çıktı**: PNG/JPG görseller

#### 7. **browser (Playwright)** — Referans Görsel Analizi
- **Ne için**: Mevcut tasarım stilini anlama
- **Örnek**: @ergene.ai profilindeki görselleri inceleme
- **Nasıl**: Screenshot alma, vision_analyze ile analiz
- **Çıktı**: Tasarım referansları

### D. FORMATLAMA VE KAYIT AŞAMASI

#### 8. **write_file** — Markdown Olarak Kaydetme
- **Ne için**: İçerik dosyalarını kaydetme
- **Örnek**: "01-ai-kullanan-isletmeler.md"
- **Nasıl**: Markdown formatında dosya oluşturma
- **Çıktı**: Düzenli içerik dosyası

#### 9. **terminal** — Dosya Organizasyonu
- **Ne için**: Klasör yapısı, dosya taşıma
- **Örnek**: "mkdir -p content/week-1"
- **Nasıl**: Shell komutları ile dosya yönetimi
- **Çıktı**: Düzenli klasör yapısı

### E. PAYLAŞIM AŞAMASI

#### 10. **n8n** — Otomatik Planlama
- **Ne için**: İçerik takvimi planlama
- **Örnek**: "Bu içeriği Pazartesi 09:00'da paylaş"
- **Nasıl**: n8n workflow ile otomasyon
- **Çıktı**: Planlanmış gönderiler

#### 11. **browser (Playwright)** — Instagram Paylaşımı
- **Ne için**: Manuel paylaşım (şimdilik)
- **Örnek**: Instagram'a giriş yap, paylaş
- **Nasıl**: Manuel otomasyon
- **Çıktı**: Paylaşılmış gönderi

---

## 3. TEK BİR GÖNDERİ İÇİN AKIŞ

### Adım 1: Araştırma (5 dakika)
```
web_search("AI kullanan işletmeler gelir artışı 2026")
→ 3-5 kaynak bul
→ Verileri topla
```

### Adım 2: Derin Araştırma (10 dakika)
```
web_extract(linkler)
→ Makaleleri oku
→ Alıntıları çıkar
```

### Adım 3: İçerik Üretimi (10 dakika)
```
AI modeli ile metin yazımı
→ 5-7 slide metni
→ Caption ve hashtag'ler
```

### Adım 4: Görsel Üretimi (15 dakika)
```
fal ile görsel üretimi
→ Her slide için görsel
→ Koyu tema, minimal tasarım
```

### Adım 5: Formatlama (5 dakika)
```
write_file ile kaydetme
→ Markdown dosyası
→ Görseller ile birlikte
```

### Adım 6: Kontrol (5 dakika)
```
Tasarım kontrolü
→ Tutarlılık kontrolü
→ Son dokunuşlar
```

**Toplam Süre: 50 dakika/gönderi**

---

## 4. HAFTALIK PLAN

### 1. Hafta (3 gönderi)
- **Pazartesi**: "AI Kullanan İşletmeler %35 Daha Fazla Kazanıyor"
- **Çarşamba**: "Türkiye'de AI Kullanım Oranı: 2026 Raporu"
- **Cuma**: "2026'da İşletmeler İçin AI Trendleri"

### 2. Hafta (3 gönderi)
- **Pazartesi**: "Küçük Bir Kahve Dükkanının AI Yolculuğu"
- **Çarşamba**: "Restoranlarda AI Devrimi"
- **Cuma**: "Emlak Sektöründe AI"

### 3. Hafta (3 gönderi)
- **Pazartesi**: "Manuel vs AI Randevu: Zaman ve Maliyet Analizi"
- **Çarşamba**: "İşletmeniz İçin AI Seçerken 5 Altın Kural"
- **Cuma**: "AI Maliyetini 3 Ayda Çıkarma Rehberi"

### 4. Hafta (3 gönderi)
- **Pazartesi**: "AI Olmadan Önce ve Sonrası"
- **Çarşamba**: "Sizce AI İşletmenize Ne Katar?"
- **Cuma**: "AI Hakkında En Çok Sorulan 5 Soru"

---

## 5. BAŞARI KRİTERLERİ

| Metrik | Hedef |
|--------|-------|
| Gönderi Sayısı | 12 |
| Tasarım Tutarlılığı | %100 |
| İçerik Kalitesi | Yüksek |
| Veri Doğruluğu | %100 |
| Zamanında Paylaşım | %100 |

---

## 6. RİSKLER VE ÖNLEMLER

| Risk | Önlem |
|------|-------|
| Veri hatalısı | Her veriyi 2 kaynaktan doğrula |
| Tasarım tutarsızlığı | Referans görselleri her zaman incele |
| Gecikme | Haftalık plana sadık kal |
| Tekdüzelik | Her hafta farklı konu/şekil |

---

**Durum: Hazır. İlk gönderiye başlıyorum.** 🚀
