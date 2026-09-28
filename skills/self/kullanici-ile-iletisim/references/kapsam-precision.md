# Kapsam Precision Kuralı (29.07.2026)

## Sinyal

Bilal "sadece" / "sadece şunun" / "just X and Y" dediğinde:
**Tam olarak onu yap, genişletme, ekleme, yanına başka şey koyma.**

## Örnek: Session 29.07.2026

- **Bilal'in istediği:** "Opencode Subagent ile Jcode arasında kıyaslama yapmanı istedim sadece."
- **Benim yaptığım (hatalı):** jcode vs OpenCode (bütün) karşılaştırması yaptım.
- **Doğrusu:** jcode vs delegate_task — sadece o ikisi.

## Kural

1. Soruda belirtilmeyen hiçbir şeyi karşılaştırmaya/analize ekleme
2. "Sadece" gördüğünde scope'u daralt, genişletme
3. Tam emin değilsen: sorduğu şeyi aynen yap, tahmin edip genişletme
4. Fazladan bilgi sunmak istiyorsan: önce sadece istediğini ver, bitince "istersek şu da var" de

## Küçük istekte CEVAP ÖNCE, keşif sonra

**Sinyal:** kısa/sosyal istek ("tanışın", "selam ver", "şunu yaz", "ne diyorsun") ve kullanıcı ekranda bekliyor.

**Hata:** önce altyapı keşfine dalmak (log taraması, servis API'si, kimlik/üyelik sorgusu, port denemesi) — cevap gecikir, kullanıcı dürtmek zorunda kalır ("ee hadi", "hadi", "?").

**Kural:**
1. İstenen teslim, ≤2 araç çağrısıyla üretilebiliyorsa **ÖNCE onu üret ve gönder**; doğrulama/keşif cevaptan sonra ve yalnız gerekiyorsa yapılır.
2. Keşif gerçekten zorunluysa **tek turda topla** ve turu cevapla bitir — "araştırıyorum" mesajı teslim değildir.
3. İstek bir sosyal/koordinasyon isteğiyse (tanışma, duyuru, cevap metni) içerik **kendisidir**; altyapı detayı yalnız cevabın içindeki tek satırlık "nasıl ulaşırsın" notu kadar yer hak eder.
4. **Gecikme sinyali = hata sinyali:** kullanıcı aynı isteği ikinci kez dürtmek zorunda kaldıysa teslim gecikmiştir; bir sonraki turda keşfi kesip çıktıyı ver.
