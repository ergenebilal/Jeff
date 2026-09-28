# Uzaktan İlk Temas — İcra Paketi Üretimi

Bu tarif, elde hazır mesaj listesi varken **gönderimin yapılmadığı** durumu kapatır. Amaç: insani adımı 5 saniyeye indirmek ve dönüşün ölçülebilmesini sağlamak. Ölçüt "paket hazırlandı" değil: **gönderim saatinin ve dönen yanıtın kayda girmesi**.

## Adımlar

1. Takip tablosunu doğru parse et: `cevap-log.csv` → **noktalı virgülle + `utf-8-sig`** oku (BOM'lu; düz `csv.DictReader` tek kolona düşer ve tüm alanlar `KeyError` verir).
2. Hedefleri aşamaya göre seç (ör. temas aşamasındaki satırlar).
3. **`hat` alanını kontrol et** — `mobil` → WhatsApp, `SABIT` → arama. Numaradan da çapraz doğrula: `(0xxx) xxx xx xx` biçimi sabit hattır. Alan boşsa numaradan çıkar, tahmin etme.
4. Onaylı metin dosyalarını birebir al (`mesajlar/*.txt`) — **yeniden yazma**.
5. Mobil için tek dokunuş linki üret:
   ```python
   import urllib.parse
   def intl(p):
       d = ''.join(c for c in p if c.isdigit())
       return '90' + d[1:] if d.startswith('0') else d
   link = 'https://wa.me/' + intl(tel) + '?text=' + urllib.parse.quote(metin)
   ```
6. Sabit hat için ayrı **arama metni** yaz (aynı gövde + "isterseniz 3 maddelik kısa özeti gönderebilirim") ve pakette "bu numara WhatsApp değil — ara" notu bırak.
7. Her hedef için kayıt satırı şablonu ver (alanlar dolu, **tarih boş**):
   ```
   <id>;<işletme>;<kategori>;hedef;<telefon>;<hat>;WhatsApp|ARAMA;1-GONDERILDI;<TARİH SAAT>;;;;;;;<not>
   ```
8. Tek dosyada teslim et: her hedefin metni kopyalanabilir blokta + link + kayıt satırı. Dosya adı sabit tutulur (ör. `ILK-TEMAS-PAKETI.md`), böylece bir sonraki parti aynı yere eklenir.

## Paketin içinde yazması gereken kurallar

- Metin **değiştirilmez**, kısaltılmaz, emoji eklenmez.
- Fiyat, paket adı, süre, garanti, "en iyi" ifadesi YOK (ticari doğrulama: ilgi testi aşamasında satış dili kullanılmaz).
- **Tam saat** not edilir — yanıt süresi bu saatten ölçülecek.
- Cevap gelmezse "yanıt yok" olarak yazılır; ikinci temas ayrı kararla yapılır.
- Kanıt: gönderim ekran görüntüsü veya mesaj kimliği.
- Gönderen kimliği kullanıcının kararıdır; numarası otomatik bir sisteme bağlanmaz.

## Pitfall'lar

- **Sabit hattı WhatsApp'a sokmaya çalışmak.** `(0xxx)` biçimli numara o teması sessizce öldürür; listede kanal tipi yoksa numara biçiminden çıkar.
- **Metni "iyileştirmek".** Onaylı metne yeni cümle eklemek ölçümü kirletir — hangi cümlenin işe yaradığı bilinemez.
- **Kayıt satırını pakete koymamak.** Şablonsuz devir, ölçümsüz icra üretir; cevap gelince kimin ne zaman ne gönderdiği bulunamaz.
- **Linki test etmeden teslim etmek.** Açılıp sohbeti ve yazılmış metni getirmiyorsa link ölüdür; teslimden önce birinde aç.
- **Gönderim tamamlanınca takip tablosunu güncellemeden "yapıldı" demek.** Başarı kayıtla birlikte gelir.
