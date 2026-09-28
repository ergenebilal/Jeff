# Eş Ajan Arayüzü — sunucudan okuma ve uç doğrulama

Ne zaman: eş ajanın (yerel makinedeki oda/panel) arayüzünü sunucudan okumak, canlılığını ölçmek ya da
hangi yolların gerçekten var olduğunu bulmak gerektiğinde. Bu bir **ölçüm** işidir; arayüzden
konuşma başlatmak işi değildir (bkz. §3).

## 1. Ağ kapısı — kim açabilir
- Yerel arayüz `127.0.0.1:<port>`'a bağlıysa sunucudan erişilemez. Çözüm iki tanedir ve **ikisi de
  karşı tarafın/Bilal'in onayına bağlı bir ağ ayarıdır**: arayüzü `0.0.0.0`'a bind etmek ya da
  `tailscale serve --bg <port>` çalıştırmak. Sunucudan bunları sen yapamazsın; isteği net komutla ve
  tek maddede ver.
- Kapı açıldı iddiasını ölçümle karşıla: `curl -s -m 8 -o /tmp/room.html -w '%{http_code} %{size_download} %{time_total}\n' http://<tailscale-ip>:<port>/`
  → `200` + makul süre (ör. <1 sn) kanıt; zaman aşımı/hata, kapının hâlâ kapalı olduğunun kanıtıdır.
- Adresi IP'den yaz, düğüm adından değil: `tailscale status` ile karşı uç düğümün adını + IP'sini
  birlikte göster, hangi tarafın hangisi olduğunu tek cümlede sabitle (isim kuralı: SKILL.md §1).

## 2. Gerçek uç bulma — 200 kanıt DEĞİLDİR
Tek sayfa uygulamaları bilinmeyen yollara **index.html** döner ve **200** verir. Yani aynı boyutta
dönen 200 = "o yol yok".
- Doğru ölçüt: **yanıt boyutu + içerik**. `index.html` boyutunda (birkaç KB, `<html` ile başlayan)
  yanıt = yol yok. JSON dönen ve farklı boyutta yanıt = gerçek uç.
- Sıra: önce sağlık ucu (`/health` ya da eşdeğeri; genelde küçük JSON ve hızlı) → sonra `/api/*`
  adaylarını sırayla dene. Her aday için `%{http_code}` + `%{size_download}` + ilk ~30 karakteri yazdır.
  Yalnız durum koduna bakan tarama, "her yol çalışıyor" gibi yanlış bir tablo üretir.
- GET ile bulunan yolun POST'u olmayabilir; yazma yolu ayrı aranır (POST denemesinde de boyut kontrolü
  şart).
- Tarama aday listesini skorla, kalanını "uç yok" diye değil "index.html döndü" diye yaz.

## 3. Yazma yolu ve kimlik sınırı
- Arayüzün tarayıcı yolu (genelde WebSocket `/ws`) **insan kullanıcı** kimliğiyle yazar. Uygulama JS'i
  ayrı dosyada olabilir (ör. `/app.jsx`); gövde şeklini ve adresi oradan oku.
- Ajan kimliğiyle yazmak ayrı yoldur: arayüz seni çağırır, cevabını kendi imzanla postalar. Yani
  **kendi başına sohbet başlatamıyorsun** — bu bir arıza değil, tasarım sınırı.
- İnsan yolundan yazmanın bedeli: satır **geri alınamaz** ve panelde **kullanıcı (Bilal)** olarak
  görünür — imza taşımaz. Tek yazma yolu bu olduğu için kullanmak yasak değil, **koşullu**: yalnız
  Bilal'in istediği satırı yaz, metnin başına `[jeff·sunucu]` koy ve Bilal'e "panelde senin adınla
  görünecek" diye söyle. Kendi kararını Bilal'in ağzından yazma — o karar artık ona ait görünür.

## 4. Arayüzün kendi durum ölçümü
- Durum ucu (ör. `/api/status`) genelde "eş ajan online mı", son ölçüm gecikmesi ve son hata metnini
  taşır. Kök sebep aramaya buradan başla: hata metni (ör. çağrı `aborted`) hangi yolun tıkandığını
  söyler.
- Ajanın kendi beyanı ile arayüzün ölçtüğü durum çelişebilir. İkisini yan yana yaz ve **hangisinin
  ölçüm, hangisinin beyan** olduğunu açıkça belirt (SKILL.md §2).
- Durum ucundaki "offline" yazısı tek başına "karşı ajan ölü" demek değildir; çağrı yolu kesilmiş
  olabilir (bekleme süresi, yol/port, kimlik). Kesin konuşmadan önce ikinci bir ölçüm yap.

## 5. Rapor şekli
Tek ekranda: (a) ağ kapısı ölçümü (kod + süre), (b) bulunan gerçek uçlar ve olamayanlar
("index.html döndü"), (c) yazma yolunun sınırı, (d) engelin ne olduğu ve kimin açacağı. Uzun anlatım
yerine ölçüm tablosu; her satırda kanıt komutu.

## 6. Gövde keşfi ve ölçüm komut düzeni
- **Gövdeyi nereden okuyacaksın:** kök HTML genelde boş bir kabuktur; adresler ve gövde alanları JS
  paketinde olur. `curl -s http://<ip>:<port>/app.jsx -o /tmp/app.jsx` →
  `grep -nE "fetch\(|method: 'POST'|new WebSocket" /tmp/app.jsx`. Böylece hem yazma yolunun adresi
  hem gövde şekli (ör. `{"type":"chat","text":...}`) tek turda çıkar; arayüzü tarayıcıda açıp
  tahmin etmeye gerek kalmaz.
- **Yanıtı dosyaya indir, script ile ayrıştır:** `curl -s -m 10 <url> -o /tmp/x.json` + ayrı bir
  `python3 /tmp/ayristir.py`. Doğrudan boru (`curl ... | python3`) güvenlik taramasında reddedilir;
  dosya + script düzeni her yüzeyde çalışır. İndirdiğin tek JSON'u birden fazla soru için kullan
  (kayıt sayısı, son N olay, `id` eşleşmesi) — her soru için yeniden indirme.
- Her prob satırında `%{http_code}` + `%{size_download}` + `%{time_total}` yazdır; 200 tek başına
  kanıt değildir (§2).
