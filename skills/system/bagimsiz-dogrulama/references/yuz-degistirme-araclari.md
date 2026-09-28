# Yüz değiştirme (face swap) — araç sınıfları

> **Durum: araştırma bulgusu adayları, sahada test EDİLMEMİŞTİR.** Kullanıcıya "öneri" olarak sunulur, "doğrulandı" diye etiketlenmez.

## Seçim ekseni

| Durum | Yol |
|---|---|
| Tek yüz, hızlı sonuç, arkadaş şakası | Telefon uygulaması (FaceMagic, Reface, Faceswapper.ai, Vidnoz, Magicam) — abonelik/filigran olabilir |
| Bedava deneme, tarayıcıdan | FaceFusion online; HuggingFace Spaces (FaceFusion Face Swap HYPERSWAP, Swap Face Video, InsightFace-FaceSwapper on Video) — kuyruk var |
| **Çoklu yüz** (her yüze ayrı kaynak) | FaceFusion, Roop-Unleashed, ReActor, DeepFaceLab — yerel, **GPU şart** |
| GPU yok | Web veya bulut API (fal.ai / Replicate) |

## Kritik ayrım

- **Çoklu yüz eşleme** isteyen işlerde telefon uygulamaları yetmez — her yüzü ayrı bir kaynak fotoğrafla eşleyen yerel araç sınıfı gerekir.
- Yerel boru hattı **GPU ister**. Hedef makinede GPU yoksa (sanal sunucu vb.) CPU'da çalıştırmak kısa bir klip için bile saatler sürer → bu yolu önerme, bulut/web öner.
- Bulut yolunda altyapı hazırsa (fal.ai gibi) en pratik teklif: videoyu + referans yüz fotoğraflarını kullanıcıdan al, sen çalıştır, sonucu gönder.

## "Bu video hangi araçla yapılmış?"

Pikselden ürün adı çıkarılamaz. İzlerden **sınıf** okunur:

- Boyun/kafa birleşiminde keskin kesim, pikselleşme, ten rengi ve ışık uyuşmazlığı → düşük ayarlı swap veya **elle kes-yapıştır** (kurgu yazılımı/Photoshop + takip)
- Eğitimli deepfake (DeepFaceLab sınıfı) bu izleri bırakmaz; kaynaşma daha temiz olur

Cevap kalıbı: "Kesin söyleyemem, ama kareler şunu gösteriyor…" + somut izler. Tek ürüne kesin atıf yapma.

## Kare çıkarma ile doğrulama

Medyanın gerçekte ne gösterdiğini öğrenmek için indir + kare çıkar + `vision_analyze` (bkz. SKILL.md). Altyazı/başlık yanıltıcıdır; medya esastır.
