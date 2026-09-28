# Çok-Ajanlı Ortak Çalışma — Rol, Kanıt ve Devir Doktrini

**Ne zaman:** İş, sunucudaki ajan ile kullanıcının yerel makinesindeki başka bir ajan arasında bölünüyorsa (yerel icra + uzak beyin). Ortak sözleşme dosyası: `/home/hermes/fpc/EKIP-PROTOKOLU-jeff-alfred.md`.

## Roller

| Kim | Yapar | Yapmaz |
|---|---|---|
| Sunucu ajanı | Strateji, hedef doğrulama, metin, ölçüm, **tek doğru kaynak** (kayıt defteri), denetim | Kullanıcının makinesindeki fiziksel işlem |
| Yerel ajan | Gerçek oturumlu tarayıcı, yerel dosya/ofis işleri, ekran kanıtı, gönderim hazırlığı | Strateji kararı, kaydın son hali, onaysız üçüncü taraf teması |
| Devredilen işçi (subagent) | Toplu/ham iş (çoklu sayfa tarama, veri dönüştürme), paralel koşu | Karar, kaydın son hali; çıktısı denetimden geçmeden kullanılmaz |
| Kullanıcı | Kimin hangi kimlikle temas kuracağına karar verir | — |

## Değişmez kurallar

- Üçüncü tarafa **onaysız temas yok** (mesaj, arama, e-posta, DM).
- Kullanıcının numarası/hesabı otomatik bir sisteme bağlanmaz.
- **Bir ajanın kendi beyanı kanıt değildir.** Yanında artefakt olmadan (dosya yolu, ekran görüntüsü, mesaj kimliği, zaman damgası) "doğrulandı" olarak kayda geçmez; CLAIMED olarak durur.
- **Kayıt dışı dış aksiyon yok.** Temas aynı gün tek doğru kaynağa yazılır; gecikmiş kayıt kayıtsız aksiyondur.
- **Hedef sahipliği.** Aynı hedefe iki ajan aynı anda dokunmaz; kim dokunuyorsa kayıtta yazar.
- **Yetki kademeli genişler:** önce salt-okunur, çalıştığı kanıtlanınca yazma. Hassas/geri dönüşsüz işler (ödeme, hesap, silme) devredilmez.
- **Altyapı, taşıyacak iş olmadan kurulmaz.** Ajan sayısı artınca ortak kanal ihtiyacı gerçektir; ama kanal/platform üzerinden geçen **gerçek işle birlikte** açılır. Aksi hâlde ajanlar birbirine durum raporu yazar, hiçbir ölçüm üretilmez — bu tuzağın kanıtı iç raporlarda görüldü (beslemesi olmayan tarama "çalışıyor" diye raporlandı).

## Nerede konuşulur — kanal seçimi

- Kullanıcı "gruba yaz / tanışın" derse **yalnız o gruba yazılır**; postane/olay kanalı, DM bildirim, kayıt defteri olayı **devreye alınmaz**. Kanalı kullanıcı seçer, ajan kendi kendine genişletmez — her ek kanal kullanıcıya gürültü (bildirim) olarak döner.
- Ajanlar arası grup = tanışma ve karşılıklı görünürlük yüzeyi; postane = gerçek iş olayı (gönderim/yanıt) taşıyan hat. İkisi karıştırılmaz.
- Sessizce ek kanal açmak "hazırlıklı olmak" değil, kapsam ihlalidir.

## Olay kanalı (postane) — ajanlar arası tek hat

- Ajanlar birbirine dosya taşıtarak değil, **tek bir olay ucuna POST ederek** bildirir; kullanıcı mesaj otobüsü olmaktan çıkar.
- Olay gövdesi: `{kim, ne, hedef, kanit, not}`; `ne` ∈ `gonderildi | yanit | tamam | hata | not | durum`. `kim` whitelist'ten doğrulanır.
- Uç **token ile korunur**; token'sız/yanlış olay kayda girmez ve **sebebiyle** reddedilir. Sessiz yutma yok; gönderen yalnız `ok:true` görünce "bildirdim" sayar.
- `gonderildi` (gönderim anı) ve `yanit` (cevap anı → kaç dakikada döndü) olayları kayıt defterini **otomatik** günceller. **"Mesaj gitti" başarı değil; kayıt + dönen yanıt başarıdır.**
- Makineler aynı özel ağdaysa (Tailscale) **özel ağ yolu tercih edilir** — internete kapı açılmaz; genel yol yalnız yedektir.
- **Kanalın YÖNÜNÜ doğrula — tek yönlü kanal "iki ajan arasında hat" DEĞİLDİR.** Olay kanalı pratikte `gönderen ajan → n8n → kullanıcı bildirimi + kayıt` akışıdır: olayı geçen ajan karşı ajana **teslim etmez**. "Hat kuruldu / iki ajan konuşuyor" demeden önce şu soruyu kanıtla: benim olayım karşı ajanın OKUDUĞU bir yere düşüyor mu? Cevap hayırsa hat tek yönlüdür — karşı ajana giden yol ayrıca kurulmalı ya da açıkça "eksik halka" diye raporlanmalıdır.
- Kurulum mekaniği (iş akışı oluşturma, düğüm tuzakları, teslim kanıtı, sunucu tarafı toplayıcı): `references/n8n-olay-kanali.md`.

## Eş ajana ulaşma ve tanışma (handshake)

**Problem:** Olay kanalı senin → kullanıcı yönünde çalışır; **karşı ajana giden yol genelde yoktur.** "Tanışın" tipi bir istek geldiğinde mesaj yazmadan önce üç şeyi ölç:

1. **Ortak yüzey nerede?** İki ajanın birlikte bulunduğu sohbet/grup en ucuz iki yönlü yoldur. Sohbet kimliğini tahmin etme — Hermes kaydından oku: `~/.hermes/channel_directory.json` (grup/dm adı + id). Telegram tarafında doğrulama: `api.telegram.org/bot<token>/getChat | getChatMemberCount | getChatAdministrators` (token `~/.hermes/.env`), `getMe` ile hangi bot olduğunu teyit et.
2. **Bot üye listesini GÖREMEZ** — API'de üye dökümü yoktur; "grup N kişi" görüntüsü karşı ajanın orada olduğunu kanıtlamaz. Karşı ajanın mesajı aldığını yalnız **alıp yanıt vermesi** kanıtlar. Kendi botunun grubun TÜM mesajlarını gördüğünü log'dan doğrula (`inbound message: ... chat=<grup id>`) — gizlilik modu kapalıysa mesajlar sana düşer, o zaman yüzey gerçekten iki yönlüdür.
3. **Karşı makinede port taraması kesin cevap vermez:** açık port + her yola 404 dönen varsayılan sunucu (IIS vb.) "orada ajan servisi var" demek değildir. İki-üç port denemesi yeter; sonuç yoksa zorlamayı kes ve yüzeyi sohbete çevir.

**Tanışma mesajının iskeleti (tek mesaj, karşı ajanın hemen işine yarar halde):**
- nerede çalışıyorum · ne yaparım · bende olan (kayıt/veri/karar) · bende olmayan (karşı ajanın alanı)
- **kanal tarifi tam yazılır**: POST adresi + başlık + gövde alanları + "yalnız `ok:true` görürsen bildirdim say".
- **eksik halka açıkça söylenir**: "sen bana yazabiliyorsun, ben sana yazamıyorum; cevap yolum şimdilik şu yüzey" — bunu saklamak iki ajanı da yanlış varsayımla çalıştırır.
- iki değişmez kural (kendi beyanı kanıt değil · üçüncü tarafa onaysız temas yok)
- **karşı ajandan İSTENEN kanıt** net olur: kendini tanıt · kanallı gerçek bir olay geç · cevap yolunu bildir.
- **bekleyen iş paketi** eklenir (hazır hedef listesi + metin dosyası yolu): tanışma boş laf olmasın, ilk ortak iş tanışmanın içinde dursun.

## Yankı (echo) döngüsü — kanal kurulumunun en pahalı hatası

Köprü/panel ajan mesajlarını taşırken mesajı **yazarına geri** gönderirse kanal kendi kendini besler:
sen cevap verirsin → köprü cevabını "karşı tarafın mesajı" gibi sana geri düşürür → yeniden cevap
üretirsin. Ölçülen olay: verilen cevap **3 saniye sonra aynı metinle**, kendi ajan adı etiketiyle geri
düştü; aynı komut bir gecede 8 kez teslim edildi, 90 dakikada 16 oturum + 80 model çağrısı açıldı.

**Teşhis:**
- Gelen mesajın metni senin az önce gönderdiğin cevapla aynıysa (veya kendi ajan adınla etiketliyse)
  bu yankıdır — karşı tarafın sözü değil.
- Aynı talimatın birden çok kez teslimi ikinci işarettir (mesaj kimliğiyle tekilleştirme yok).
- Say, tahmin etme:
  `sqlite3 ~/.hermes/state.db "select s.source, count(*), sum(s.api_call_count) from sessions s where s.started_at > strftime('%s','now')-3600 group by s.source;"`;
  gelen/giden trafiği yüzeye göre listele (`messages` ⨝ `sessions.id`, `timestamp` unix epoch float).

**Kurallar:**
- **Yankıyı teslim kanıtı sayma.** "Cevabım karşı tarafa ulaştı" kanıtı, karşı tarafın **kendi
  ağzından, farklı metinle** gelen yeni olayıdır.
- **Kök neden ajan tarafında değil, köprüde.** İki kural: (a) mesajı **yazarına geri yollama** — her
  ajan yalnız başkalarının mesajlarını alır; (b) **aynı mesaj kimliğini iki kez teslim etme.**
- **Ajan tarafından bu döngü kesilemez:** gelen yankı sıradan bir sohbet mesajı gibi görünür, kaynağı
  ayırt edilemez. "Kanal çalışıyor" raporundan önce köprü filtresi istenir.
- **Yankı gelirken besle-me:** yeni içerik üretme, tek satırlık kısa cevapla ve döngüyü kullanıcıya
  bildir — uzun/araçlı cevap her turda maliyeti katlar.

## Kanal emekliliği ve yeni yüzeye geçiş

Kullanıcı bir kanalı bırakıp yerine yenisini koyduğunda eski kanal **kısmen kapatılmaz** — yarısı açık kalan kanal sessiz gürültü üretmeye devam eder. Sıra:

1. **Akışı pasife al, sonra sil.** Silme yanıtı `200` + silinen nesnenin gövdesini döndürür; gövde kesik/garbled gelebilir (JSON parse edilemez) — bu **başarısızlık kanıtı değildir ve başarı kanıtı da değildir**. Kanıt, iş akışı listesinin **yeniden okunmasıdır** (silinen ad listede görünmemeli).
2. **Besleyiciyi/zamanlanmış işi de sil:** toplayıcı, bekçi, poller. Kanalı silip besleyicisini bırakmak boş koşu + boş bildirim üretir (cron silme yolu ve yedekleme: `hermes-operasyon` §12b).
3. **Kayıt defterini arşiv olarak bırak, silme.** Geçmiş kanıttır; kanal kapanır, kayıt durur. Kullanıcıya "kanal kapandı, kayıt arşivde" diye söylenir.
4. **Tarif dosyasını "yürürlükte" bırakma.** Kanalı anlatan belge kaldırılır/arşive alınır; hafızaya **yeni yüzeyin adı + adresi + taşıma yolu** yazılır, eskisi silinir.
5. **Yeni yüzey erişilebilir mi — ölç, varsayma.** Karşı makinede çalışan arayüz `127.0.0.1:<port>`'a bağlıysa sunucudan **Tailscale üzerinden bile erişilemez** (özel ağ localhost bağını açmaz). Ölçüm iki adım: kendi tarafında `ss -ltn | grep <port>` (dinleyen yok) + karşı Tailscale IP'sine doğrudan probe (kapalı/erişilemez). Erişim yoksa çözüm ya uygulamayı `0.0.0.0`/Tailscale adresine bağlatmak + güvenlik duvarında porta izin vermek, ya da **zaten çalışan taşıma yolunu** kullanmaktır (ajan uç noktası / A2A). "Ben de odaya bağlanırım" demeden önce bu iki ölçümü yap; erişim yoksa eksik halkayı tek cümleyle kullanıcıya söyle ve mevcut yolla (karşı taraf sana yazar, sen cevap verirsin) çalışmaya devam et.

## Devir (handoff) disiplini

- Devredilen iş, **girdi + beklenen çıktı + kanıt biçimi + kayıt satırı şablonu** ile birlikte gider. Şablonsuz devir, ölçümsüz icra üretir.
- Devir paketi tek dokunuşa indirilir: hedef listesi, hazır mesaj metni, kanal (mobil → mesajlaşma uygulaması, sabit hat → **arama**; yanlış kanaldan denemek hiç denememekten iyi değildir), gönderim sonrası doldurulacak kayıt satırı.
- Başarı tanımı **kaydın yazılmasıdır**, "iş yapıldı" değil. Ölçüt: gönderim zamanı + dönen yanıt satırı.
- Devir öncesi karşı tarafın **kabiliyet listesi kanıtla** alınır (hangi oturumlar açık, ekran görüntüsü alabiliyor mu, dosya erişimi nerede, kendi zamanlanmış işi var mı). Tahminle iş bölümü yapılmaz.
- Devralacak ajanın **sürüm kontrolü + yedeği** yoksa, iş bölümünden önce bu sorulur: izsiz el, hattın yeni risk noktasıdır.

## Denetim dersleri

- **Başka bir ajanın senin işin hakkındaki iddiasını doğrulamadan kabul etme.** "Raporunda X var" diyen bir değerlendirme geldiğinde kendi artefaktında say: `grep -c "<iddia>" <rapor>`. 0 çıkarsa iddia CLAIMED'dır. (Bir dış değerlendirme, raporumda hiç geçmeyen bir bulguyu bana atfetmişti; sayım 0 verdi.)
- **Ajan değerlendirmesinde haklı bulguları da yaz.** Denetim raporlarında karşı tarafın isabetli eleştirisi ayrı satırda geçer; savunma refleksi kanıt değeri taşımaz.
- **Karşı tarafın "duvar" dediği engel çoğu zaman kullanıcının koyduğu kuraldır.** Yetenek yokluğu ile izin yokluğunu ayır: kural ise çözüm yeni bir araç değil, kullanıcının kararıdır (o kararı ona sor).
- Her ortak denetimde (X-RAY dahil) diğer ajanın katkısı **ne yaptı / kanıtı ne / sonucu ne** üçlüsüyle raporlanır.
