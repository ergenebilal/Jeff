# JEFF RÖNTGEN — X-RAY Denetim Protokolü

**Tetikleyici:** Bilal "JEFF RÖNTGEN" yazar. Başka hiçbir açıklamaya gerek yoktur.

**Amaç:** Sistemin GERÇEKTEN ne durumda olduğunu, belgelerde/raporlarda iddia edilen durumdan
ayırarak ortaya koymak. Bu rapor Bilal'in mimari ve ticari kararlarının temel girdisidir.

---

## 1. Mutlak kurallar

- **Sıfır değişiklik.** Hiçbir kod, config, servis, cron, DB kaydı, dosya değiştirilmez. Hiçbir dış
  aksiyon alınmaz. Bulunan arıza raporlanır, onarılmaz (onarım ayrı iş + ayrı onay). Denetim
  sırasında üretilen geçici yardımcı dosyalar iş bitiminde silinir.
- **Kanıt hiyerarşisi zorunlu.** Her iddia şu sınıflardan biriyle etiketlenir:
  VERIFIED (canlı sistemden doğrulandı) · OBSERVED (gözlendi) · INFERRED (çıkarım) ·
  CLAIMED (eski rapor/doküman/araç kendi beyanı) · CONTRADICTED (tersi kanıtlı) · UNKNOWN (bilinmiyor) ·
  ESTIMATE (tahmin). Etiketsiz iddia yazılmaz.
- **Ölçülmeyen sayı yazılmaz.** "Muhtemelen", "tahminen" yalnız ESTIMATE etiketiyle.
- **"Test geçti" ≠ "production'da çalışıyor".** Hiçbir bölümde karıştırılmaz.
- **Eski iddiaları doğrula.** Önceki röntgen/audit bulguları canlı sistemle karşılaştırılır;
  "PASS" olduğu gibi aktarılmaz, kanıt zincirine bağlanır.
- **Kendini savunma yok.** "Önceki raporum fazla iddialıydı" demekten çekinilmez.
- **Kendi hatanı da yaz.** Denetim sırasında kendi verdiğin yanlış bir bilgi (ör. bir servisin
  erişim kapsamını olduğundan dar anlatmak) ortaya çıkarsa raporda açıkça düzeltilir.

## 2. Akış ve veri toplama

READ → INSPECT → TEST (yalnız okuma) → VERIFY → REPORT

**Toplama deseni:** 4–6 paralel, salt-okunur blok. Her blok tek bir tema; çıktı ekrana değil akla
sığacak kadar kısa tutulur (head/limit), ham yığın rapora taşınmaz. Bloklar:

| Blok | Ne toplar |
|---|---|
| Çekirdek | uptime/yük, disk, bellek, zombi, çalışan süreçler, konteynerler, sistem servisleri |
| Kod tabanları | boyut + son değişiklik yaşı + hangisinin canlı olduğu (süreç cwd/cmdline, import izi) |
| Görev katmanı | görev envanteri, durum dağılımı, teslim hedefleri, `last_error` kök nedenleri |
| Bilişsel katman | hook karar günlüğü kovaları, karar kayıtları, izin/kesme izleri, hedef tablosu |
| Hafıza & ölçüm | hafıza doluluk, konsolidasyon çıktısı, anlamsal bellek tazeliği, token/maliyet kaydı |
| Güvenlik & yedek | dinlenen portlar, ateş duvarı politikası, anahtar izinleri, son yedek + offsite kanıtı |

- Uzun çıktı üreten komutları **daralt** (`tail`, `head`, `awk`, sayımlar); ham log rapora girmez.
- Topladığın her bulguyu bulgu dosyasına **hemen** yaz; tur ortasında bağlam kesilirse kanıt kaybolmaz.
- Tek satırda çok uzun/çok parçalı komut guard'a takılır: parçala ya da `.py`/`.sh` dosyasına yaz,
  sonra dosyayı çalıştır.

## 3. Zorunlu bölüm listesi (25)

| # | Bölüm |
|---|-------|
| 0 | Executive X-RAY (özet karne) |
| 1 | System Map — kod tabanları, servisler, MCP'ler, veritabanları, çalışıyor görünen ölü süreçler |
| 2 | Production gerçekliği (alt bölüm: **önceki denetimin maddeleri — yapıldı/kısmi/hareket yok**) |
| 3 | Yetenek matrisi (çalışan / kağıt üzerinde olan) |
| 4 | Cognitive loop denetimi (faz faz + ham kova sayıları) |
| 5 | ADE (karar motoru) denetimi |
| 6 | Board denetimi |
| 7 | Governance (izin/kesme) denetimi |
| 8 | Model / routing röntgeni |
| 9 | Maliyet röntgeni |
| 10 | Otonomi denetimi (hangi seviyede, kanıtıyla) |
| 11 | Test röntgeni (istenen / yazılan / geçen / gerçekten koşan ayrımı) |
| 12 | Memory / learning röntgeni |
| 13 | Ekonomik ajan röntgeni (bul → doğrula → temas → kapanış sayıları) |
| 14 | Lead pipeline koruması (hangi veri sağlam, kişisel veri notu) |
| 15 | Güvenlik / yetki röntgeni |
| 16 | "Hayal edilen sistem" vs "gerçek sistem" |
| 17 | En büyük 10 gerçek problem |
| 18 | En büyük 10 güç (yalnızca gerçek runtime kabiliyetleri) |
| 19 | Redundancy / ölü kod denetimi |
| 20 | En önemli tek soru |
| 21 | AGI-benzeri davranış testi (yeni/tanımsız bir iş geldiğinde ne oluyor) |
| 22 | Ekonomik gerçeklik testi (bugünkü ciro/gider + geri dönüş için gereken tek adım) |
| 23 | Sonuç (executive tekrar) |
| 24 | Son karar: KEEP / FIX (öncelik sıralı) / IGNORE-KILL |

## 4. Önceki denetimin takibi (bu bölüm atlanmaz)

Önceki X-RAY raporunun **FIX listesini** satır satır al ve her maddeyi bugünkü kanıtla sınıflandır:

| # | Önceki istek | Bugünkü durum |
|---|---|---|
| 1 | <madde> | HAREKET YOK / KISMİ / YAPILDI — <bugünkü kanıt> |

- Kanıt **ölçülebilir** olmalı (kayıt sayacı, dosya içeriği, koşu kaydı) — "iyileşti" gibi izlenim değil.
- Sonuca tek cümle yaz: kaç maddede ilerleme var, kaçında yok. Bu tablo, öğrenme döngüsünün
  çalışmadığını gösteren **davranışsal kanıttır**; sayısal ders tartışmasından daha ağırdır.

## 5. Ölçüm tuzakları (her biri bir denetimde yanlış hüküm üretti)

- **"0" şüphelidir — ikinci bağımsız ölçüm şart.** Bir araç 0/sıfır küme döndürdüğünde önce ölçümü
  doğrula (yetki, limit, parse, hedef). İkinci yol (konteyner içi CLI, dosya sayımı, başka uç nokta)
  farklı sayı veriyorsa ilk ölçüm çöptür. Kanıt: aynı sistem için bir yol "0 iş akışı", diğer yol 7.
- **Sayacın etiketi ≠ olay.** "N başarısız" listesini rapora yazmadan gerekçe alanını oku; çoğu kayıt
  gerçek görev hatası değil defter artefaktı olabilir. Sayıyı adlandırmadan raporlama.
- **Üretici çıktının kendi "çalışıyor" beyanı CLAIMED'dır.** Günlük rapor "bekçi çalışıyor, sıradaki
  tarama şu saatte" diyorsa çıktının **beslemesini** ayrıca doğrula: bağımlı görev hâlâ var mı
  (görev listesinde ID/ad olarak duruyor mu), son koşusu ne zaman, boş girdiyle mi üretilmiş
  (`context_from` hedefi boşalmış olabilir). Beslemesi ölmüş bir rapor her gün güvenle yanlış bilgi verir.
- **Sistem üretimi turlar kullanıcı trafiği gibi görünür.** Karar günlüğünde cron çıktıları,
  hafıza-gözden-geçirme istemleri ve arka plan bildirimleri de sınıflanır; istatistiği okurken
  gerçek kullanıcı sinyalini `preview` alanından ayır.
- **Aynı gün içinde zamanlanmış arıza + elle başarı olabilir.** Hükmü **yeni kaydın saatinden** ver;
  eski başarısız satırlar tarihseldir. "Çalışıyor mu" sorusuna cevap, sonraki doğal koşudur.
- **Dosya adı/sayısı tek başına canlılık kanıtı değildir.** Uykuda duran kod tabanları (değişmeyen
  kopyalar) "var" görünür; hangisinin canlı sürece bağlı olduğunu import/process iziyle ayır.
- **Aynı betiğin/ayarın iki kopyası olabilir.** Farkı `cmp` ile ölç, hangisinin koştuğunu kanıtla;
  sessizce senkronlama, farkı raporla.

## 6. Teslim

- Kaynak metin MD olarak kalır (yeniden üretilebilirlik), PDF'e çevrilir → `rapor-pdf-teslimi` skill'i.
- **Emoji kullanma** (tablo hücrelerinde özellikle): PDF kapısındaki çift-boşluk denetimini tetikler;
  `OK / YOK / KISMİ / KORU / ONAR / BIRAK` gibi metin işaretleri kullan.
- Telegram'a `MEDIA:` ile gönderilir; üstüne **jargonsuz sade özet**: 3–5 kritik bulgu, sayı içeren
  tablo sohbete yapıştırılmaz, varsa kendi düzeltmen açıkça yazılır.
- Arşiv: `/home/hermes/raporlar/` (tarihli dosya adı). Referans uygulamalar: 12.09.2026 X-RAY v1.0 ve
  14.09.2026 X-RAY v2.0; `/home/hermes/audit/` altındaki eski full-stack denetimleri.
