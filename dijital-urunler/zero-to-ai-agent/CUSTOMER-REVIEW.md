# Zero to AI Agent — Müşteri Gözüyle Analiz Raporu
**Tarih:** 8 Haziran 2026
**Analiz Yöntemi:** Ürünü satın alan teknik olmayan bir kullanıcının perspektifi

---

## 1️⃣ MÜŞTERİ GÖZÜYLE ÜRÜN DEĞERLENDİRMESİ

**Artılar:**
- 39 sayfa, 10 bölüm — ciddi duruyor
- Sade İngilizce, jargon patlaması yok
- Gerçek dünya tecrübesine dayalı (Chapter 10'daki "Nobody buys AI agents" samimi)
- 3 n8n workflow hediyesi

**Eksiler:**
- "Terminal familiarity" filtresi hedef kitleyi daraltıyor
- n8n workflow'larının PDF'deki isimleri ile ZIP'teki isimleri uyuşmuyor
- API key'ler dağınık anlatılmış, "nereden ne alacağım" diye bir liste yok
- Ekran görüntüsü sıfır — görmeyen inanmaz
- "Bunu kim yazdı?" sorusunun cevabı zayıf

---

## 2️⃣ İLK 3 TEKNİK ENGEL (ve çözümleri)

### ENGEL 1: Terminal Korkusu — Hermes Kurulumu
**Ne görüyor?** Chapter 2: `ssh`, `git clone`, `python3 -m venv`, `pip install`
**Ne düşünüyor?** "Ben bunları bilmiyorum. Kitap bana göre değil."
**Gerçek:** Bunlar 5 dk'lık işlemler ama developer olmayan için yabancı dil.

**ÇÖZÜM:** Şu 2 şey ürüne eklenmeli:

A. **One-Click Setup Script**
   Kullanıcının tek komutla her şeyi kurmasını sağlayan `install.sh`:
   ```bash
   curl -fsSL https://ergene.ai/install-agent.sh | bash
   ```
   (İçinde: apt paketleri, Hermes kurulumu, temel MCP server'lar, Telegram bot yapılandırması)

B. **Video: "Hermes Kurulumu 5 Dakikada"**
   - 5 dakikalık Loom/YouTube videosu
   - Ekranda her komutu göster + ne işe yaradığını açıkla
   - Linki PDF'in Chapter 2 başlığına koy

### ENGEL 2: Workflow İsim Uyuşmazlığı
**Ne görüyor?** PDF Chapter 5'te "Lead Scanner, Content Reporter, Error Handler" workflow'ları
**Ne alıyor?** daily-content-pipeline.json, content-generator.json, instagram-dm-assistant.json
**Ne düşünüyor?** "Yanlış dosya mı gönderildi?"

**ÇÖZÜM:**

A. **Workflow Mapping Tablosu — PDF'e eklenecek**
   | PDF'deki Adı | Dosya Adı | Ne İşe Yarar |
   | Lead Scanner | daily-content-pipeline.json | Her gün RSS + Twitter'dan lead topla |
   | Content Reporter | content-generator.json | 16 nişte otomatik içerik üret |
   | DM Assistant | instagram-dm-assistant.json | Instagram DM'lerine otomatik cevap ver |

B. **Veya daha basit:** Dosyaları PDF'deki isimlerle yeniden adlandır

### ENGEL 3: API Key Labirenti
**Ne görüyor?** Chapter 2'de DeepSeek/Anthropic/OpenAI key, Chapter 3'te Tavily, Telegram, belki GitHub
**Ne düşünüyor?** "5 farklı yerden key al, 5 farklı şeye yapıştır. Hangisi nereye?"

**ÇÖZÜM:**

A. **API Key Checklist — Tek Sayfa PDF'in en başına eklenecek**
   ```
   ⬜ Telegram Bot Token — @BotFather (5 dk, ücretsiz)
   ⬜ AI Provider Key — DeepSeek ($2/token) veya Anthropic/OpenAI
   ⬜ Tavily API Key — tavily.com (1000 sorgu/ay ücretsiz)
   ⬜ n8n API Key — n8n kurulumundan sonra Settings > API
   ⬜ Twitter API Key (opsiyonel) — developer.twitter.com
   ```

B. **Video: "API Key'ler Nasıl Alınır"**
   - 7 dakikalık video
   - Her key için: hangi site → hangi buton → nereye yapıştır
   - Link PDF'te

---

## 3️⃣ GOLDEN STANDARD

**Sorun:** PDF'de ürünün bir profesyonel tarafından hazırlandığını kanıtlayan somut delil yok.
Jeff'ten bahsediliyor ama "Bu adam gerçekten işini biliyor mu?" sorusu cevapsız.

**Önerilen Golden Standard (ürüne eklenecek 3 şey):**

### A. Canlı Demo Video (olmazsa olmaz)
- 3-5 dakikalık ekran videosu
- İçerik: Hermes agent çalışıyor, Telegram'dan komut alıyor, n8n workflow tetikleniyor, sonuç dönüyor
- "Bu ürünü ben kullanıyorum" ispatı
- YouTube'a yükle, PDF'e göm

### B. Production Screenshot Galerisi
- Kendi sunucundan 3 ekran görüntüsü:
  1. Hermes agent çalışırken (hermes status çıktısı)
  2. n8n workflow listesi (34 workflow görünüyor)
  3. Telegram'dan gelen otomatik rapor örneği
- PDF'de "Chapter 6" içinde ekran görüntüsü olarak

### C. Teknik Referanslar
- "Bu kitap /opt/hermes'te çalışan bir production sistem üzerine yazılmıştır"
- GitHub repo linki (public fork gösterebilir)
- Veya blog yazısı: "How I Built ErgeneAI" (medium/dev.to)

---

## 4️⃣ KARAR: GÜNCELLE

**Karar: GÜNCELLE — ÖNCELİKLİ**

Değişikliklerin toplam süresi: ~2 saat. Etkisi: Satış dönüşümünde tahmini 2-3x artış.

### Yapılacaklar (öncelik sırası):

| # | İş | Süre | Etki |
|---|-----|------|------|
| 1 | API Key Checklist → PDF başına ekle | 15 dk | Yüksek |
| 2 | Workflow isimlerini düzelt + mapping tablosu | 15 dk | Yüksek |
| 3 | One-Click Setup Script (install.sh) | 45 dk | Çok yüksek |
| 4 | Production screenshot çek + PDF'e koy | 30 dk | Yüksek |
| 5 | Demo video çek + YouTube yükle | 60 dk | Çok yüksek |
| 6 | Medium blog yaz | 60 dk | Orta |

Toplam: ~3.5 saat

### Güncelleme Yapılmazsa:
- Ürün satar mı? Evet, teknik kitleye satar.
- Kaç satar? Ayda 5-15.
- Potansiyel kayıp: Güncellenmiş hali ayda 30-50 satabilir.

---

## 5️⃣ KALİTE STANDARDI (Tüm Ürünler İçin Kural)

Bu analiz, **tüm dijital ürünler** için zorunlu kalite standardı haline gelmiştir.

Her ürün satışa çıkmadan önce:

1. **3-BARRIER TEST:** Bir müşterinin karşılaşacağı ilk 3 teknik engeli belirle.
   - Her engel için çözüm (doküman/video/link) ürüne eklenmeli.

2. **GOLDEN STANDARD:** Ürünün bir profesyonel tarafından hazırlandığını kanıtla.
   - Minimum 2 somut delil: demo video, screenshot, gerçek veri, referans.

3. **API-KEY CHECKLIST:** Tüm API key'leri tek sayfada göster.
   - Nereden alınır, nereye yapıştırılır, ücretsiz mi.

4. **COMMON-PITFALLS:** En sık yapılan 5 hatayı ve çözümünü ekle.

Bu standart dosyaya kaydedildi: `/opt/hermes/skills/product/digital-product-quality-standard`
