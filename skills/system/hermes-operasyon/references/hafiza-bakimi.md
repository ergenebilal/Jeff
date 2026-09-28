# Hafıza Bakımı — dolu depoyu taşıyarak açma

Tetikleyici: hafıza doluluk uyarısı, "%97 doluluk var bu ciddi problem" tipi bildirim, ya da
notların bir türlü eklenememesi.

## Doktrin (önce bunu oku)

- İki ayrı depo, iki ayrı sert limit: `~/.hermes/memories/MEMORY.md` (notlar) ve `USER.md` (profil).
  Güncel sayıyı oturum başındaki memory bloğundan oku; dosyaya sabit yazma.
- **Limiti YÜKSELTMEK çözüm değildir.** Hafıza her turda bağlama enjekte edilir: limiti büyütmek
  doluluğu erteler, her turda taşınan karakteri kalıcı büyütür. Çözüm **taşıma**dır.
  (16.06'da 50K'ya çekilmişti, depo yine tavana dayandı; 15.09'da taşıma ile %97 → %53 notlar / %73 profil.)
- Hedef: **her iki depo da %75 altı**. %80'i geçince taşımayı başlat.
- `hermes config set memory.*_char_limit` ile oynamak bu yüzden son adımdır, ilk adım değil.

## Ne nerede durur

| Depo | İçerik |
|---|---|
| MEMORY.md | kimlik/duruş, her oturumda geçerli değişmez kural, canlı durum ve proje özeti |
| USER.md | kullanıcı kimliği, tercihleri, iletişim tarzı, karar beklentileri |
| skill `references/` | prosedür, tuzak, şablon, niş kayıtları, ortam detayı (port, kimlik, adım adım tarif) |

Karar testi: "bu bilgi HER oturumda mı geçerli?" Hayır → skill referansı. Evet → hafızada tek satır.

## İş akışı

1. **Yedek al (atlanmaz):** `mkdir -p /opt/backups/memory-history/<tarih>_<saat>` +
   `cp -a ~/.hermes/memories/MEMORY.md ~/.hermes/memories/USER.md /opt/backups/memory-history/<tarih>_<saat>/`
2. **İki depoyu birden ölç:** `wc -m -l ~/.hermes/memories/*.md` — tavan genelde ikisinde aynı anda dolar.
3. **Sınıflandır** (kayıt kayıt): KALICI (kimlik, değişmez kural, canlı durum) · PROSEDÜR (skill'e
   taşınacak) · STALE (tarih olmuş faz/durum notu) → sil.
4. **Önce dosyayı yaz, sonra hafızadan sil.** Sıra ters olursa bilgi kaybolur. Hedef: ilgili skill'in
   `references/<konu>.md` dosyası — **konuya göre ad ver, oturum/tarih adı verme**.
5. **Sıkıştır:** aynı konudaki 3-7 kaydı tek kayda indir; uzun anlatım skill'de kalsın, hafızada tek
   satır özet + "detay: <skill>" işaretçisi.
6. **memory tool'u batch kullan:** silme + birleştirme + ekleme **tek çağrıda**. Atomiktir ve limit
   yalnız sonuç üzerinden ölçülür — ara durumda taşma hatası almazsın.
7. **Doğrula:** yeniden `wc -m`; iki depo %75 altında mı? Taşınan dosyalar gerçekten yerinde mi?

## Pitfall'lar

- **Taşıma hedefinin yolunu TAHMİN ETME, doğrula.** Skill dizinleri `~/.hermes/skills/<ad>/`
  (kategorisiz) ya da `~/.hermes/skills/<kategori>/<ad>/` olabilir. Tahminle kontrol edip "dosya yok"
  sonucu almak yanlış alarmdır; gerçek yeri `find ~/.hermes/skills -name <dosya>` ile bul.
- **Kendi skill'ine yazamayabilirsin:** kullanıcıya ait (curator-managed olmayan) skill'ler otomatik
  yazıma kapalıdır. Taşımayı o skill'e yapmayı planlıyorsan önce yazma hakkını gör; kapalıysa içeriği
  curator-managed bir skill'in referansına taşı ve kullanıcıya `hermes curator adopt <ad>` öner.
- **Prosedür hafızada kalmaz:** "şu komutla şunu yap" tipi içerik buraya değil skill'e aittir.
- **Tek ölçüme güvenme:** hafıza alarm log'u varsa oradan da teyit et.
