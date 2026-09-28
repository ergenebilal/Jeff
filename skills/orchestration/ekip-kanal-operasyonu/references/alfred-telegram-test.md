# Alfred Telegram Bot Doğrulama Testi

## Amaç
Alfred'in kendi bot token'ını kullanarak kullanıcıya doğrudan Telegram mesajı gönderebildiğini ve uçtan uca Alfred->kullanıcı iletişimini doğrulamak.

## Prosedür
1. Test mesajını hazırla: Kodlama sorunlarına yol açmayacak net metin kullan (ör. "Selam aldım, iletişim başarılı.")
2. Alfred'i tetikle: `~/.hermes/alfred_bridge/inbox/` dizininde `SEND_TELEGRAM: <mesaj>` dosyası oluştur (ör. `SEND_TELEGRAM: Selam aldım, iletişim başarılı.`)
3. Alfred işlemesini doğrula: `.cmd` dosyasının inbox'tan ~5 saniye içinde tüketildiğini (silindiğini/taşındığını) kontrol et
4. Bot çağrısını doğrula: Outbox'ta `"action": "send_telegram"` içeren görevi kontrol et
5. Kullanıcı alım doğrulaması: Telegram'da mesajın doğrudan Alfred'in botundan (Jeff/köprü aracılığıyla değil) geldiğini teyit et

## Pitfalls (Tuzaklar)
- **Bot kaynağını daima doğrula:** Mesaj doğrudan Alfred'in bot token'ından gelmeli; köprü üzerinden iletilen mesajlar bot yeteneğini doğrulamaz.
- **Sadece tetikleyiciyi değil botu test et:** Alfred'in inbox dosyasını işlemesi botun mesaj atabildiğini garanti etmez.
- **Birebir beklenen metni kullan:** Sapmalar testin geçerliliği konusunda kafa karışıklığı yaratır.
- **Karakter kodlamasına dikkat et:** Türkçe karakter sorunlarına karşı ASCII-güvenli metin tercih et.

## Başarı Kriterleri
- Kullanıcının Alfred botundan birebir test metnini içeren Telegram mesajını alması
- Alfred inbox tetikleyici dosyasının işlendikten sonra temizlenmesi
- Outbox'ta eşleşen `send_telegram` görevinin bulunması
