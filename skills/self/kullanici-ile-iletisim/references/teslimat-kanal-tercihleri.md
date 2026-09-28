# Teslimat Kanal Tercihleri
> Kullanıcının dosya/çıktı teslimatı için kanal tercihleri.
> Son güncelleme: 2026-07-10

## Ana Kural

**Bilal'e dosya/çıktı teslim ederken önce BULUNDUĞUN KANALI dene.**
Dış servis (Google Drive, HTTP, e-posta) ANCAK kullanıcı açıkça belirtirse kullanılır.

## Türkçe Sinyal Sözlüğü

| Kullanıcı Dediği | Anlamı | Aksiyon |
|-----------------|--------|---------|
| "koy" | Bu kanala gönder / teslim et | Dosyayı mevcut kanala (Telegram) gönder |
| "at" | Bu kanala at / gönder | Dosyayı mevcut kanala gönder |
| "yaz" | Google Doc'a yaz / oluştur | Google Docs Create yap, link ver |
| "drive'a yükle" | Google Drive'a upload et | Drive upload yap |
| "indir" / "download et" | Dosyayı al, içeriğini ver | read_file ile içeriği göster veya indirilebilir yap |
| "link ver" | HTTP/URL ile erişilebilir yap | HTTP server başlat, URL ver |
| "gönder" | Bu kanala gönder | Mevcut kanala teslim et |

## Öncelik Sırası (Teslimat için)

1. **Mevcut kanal (Telegram DM)** — cron deliver=origin, veya direkt terminal çıktısı
2. **Google Drive** — sadece "drive'a yükle" dendiğinde
3. **HTTP server** — sadece "link ver" dendiğinde
4. **E-posta** — sadece "mail at / e-posta gönder" dendiğinde

## Önemli Nüanslar

- "koy" dedikten sonra "yaz" derse → yaz (her cümle kendi başına)
- "koy" + "yaz" aynı cümledeyse → "yaz" öncelikli (içerik oluşturma eylemi)
- Kullanıcı önce "drive'a yükle" dediyse sonra "koy" derse → "koy" BU KANALDA teslim et demektir. Önceki tercih artık geçersiz.Sadece kullanıcı aynı cümlede ikisini birden söylerse Drive'a yükle.
- Kullanıcı "bekliyorum" dediğinde bir aktivite bekliyordur — output göndermeyi bekleme, HEMEN yap ve gönder.
