# WhatsApp Business API — 2026 Politika Değişikliği

> Kaynak: Meta WhatsApp Business Solution Terms, güncelleme 15 Ocak 2026

## Ne Değişti?

Meta, 15 Ocak 2026'dan itibaren WhatsApp Business API'de **genel amaçlı AI chatbot'ları yasakladı.**

**Yasak olan:** AI model sağlayıcılarının WhatsApp'ı bir dağıtım kanalı olarak kullanması.
- ChatGPT'nin WhatsApp versiyonu ❌
- Genel amaçlı AI asistanlar ❌
- "Bir numara yaz, AI'la konuş" modeli ❌

**Serbest olan:** İşletmelerin kendi müşteri hizmetleri için AI kullanması.
- Klinik için randevu botu ✅
- Restoran için rezervasyon botu ✅
- Müşteri hizmetleri otomasyonu ✅

## ErgeneAI İçin Anlamı

Bizim modelimiz (işletmelere AI randevu/müşteri botu) **yasak kapsamında DEĞİL.** Çünkü:
1. Bot işletmenin kendi müşteri iletişimi için
2. Ana işlev işletmenin hizmeti, AI sadece araç
3. Genel amaçlı AI asistan değil, spesifik randevu/müşteri hizmeti

## Riskler

Meta tek taraflı kural değiştirebilir ("as determined by Meta in its sole discretion").

## Strateji

WhatsApp'ı **tek kanal** yapma. Ürünü "AI İşletme Asistanı" olarak konumlandır:

| Kanal | Maliyet | Risk | Öncelik |
|-------|---------|------|---------|
| 🌐 Web Widget (ergeneai.com) | Sıfır | Yok | 🥇 Birincil |
| 📱 Instagram DM | Sıfır | Düşük | 🥇 Birincil |
| 💬 WhatsApp | Var ($0.01-0.05/konuşma) | Orta | 🥈 İkincil |
| 📞 SMS | Düşük | Yok | 🥉 Alternatif |

Müşteri WhatsApp isterse kendi Business API hesabını açar, biz AI katmanını bağlarız.
