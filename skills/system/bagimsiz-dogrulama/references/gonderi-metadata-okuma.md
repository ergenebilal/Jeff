# Gönderi/profile metadatası okuma (Instagram, girişsiz)

Amaç: bir gönderinin altyazısı, yazarı ve etkileşim sayılarına **tarayıcı açmadan veya tarayıcı bloke haldeyken** ulaşmak.

## Yollar

| Ne lazım | Yol |
|---|---|
| Gönderi altyazısı + yazar + beğeni/yorum sayısı | `web_extract(["https://www.instagram.com/p/<shortcode>/embed/captioned/"])` |
| Profil takipçi/gönderi sayısı + bio + site/telefon | `web_extract(["https://www.instagram.com/<handle>/"])` |
| Aynı veri, tarayıcıdan | gönderi/profil sayfası → `meta[property="og:description"].content` ya da `meta[name="description"].content` |
| Bio + link (tarayıcıdan) | `document.querySelector('header').innerText` |
| İlk yorumlar | embed/captioned çıktısı |
| Gönderi tarihi | DOM'daki `img[alt]` metni ("Photo by X on <tarih>.") |

`web_extract` yolu, tarayıcının 429 (`net::ERR_HTTP_RESPONSE_CODE_FAILURE`) yediği durumda birincil kaynaktır — 429 bloğu tarayıcıya aittir, bu yol o bloğa girmez.

## Zorunlu kontroller

- **Eşleşme kontrolü:** dönen sonucun `url`/`title` alanı istediğin gönderi/handle ile eşleşmiyorsa veriyi KULLANMA, tekrar çek. `web_extract` bazen **başka bir sayfanın** içeriğini döndürür (önbellek karışması). Yanlış hesabın verisiyle iddia kurmak, veri olmamasından kötüdür.
- **Çift okuma:** bir sayıyı (takipçi, gönderi adedi) iddiaya dayanak yapmadan önce iki farklı okumada aynı çıkmasını bekle.
- **Hız sınırı:** aynı turda arka arkaya çekim **429** yer. Okunacak tüm handle'ları topla, aralarında ~2 sn bekleyerek **tek** turda çek.
- **Okunamayan hesap için "yok" DENMEZ** → "hesap tespit edilemedi" denir. 429 yediysen iddia kurma, veriyi "doğrulanamadı" etiketle.
