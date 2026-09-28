# OpenCode Go — Kota Mekaniği ve Uygun Fiyatlı Model Seçimi

Ölçüm zamanı: **Eylül 2026**. Model listesi ve fiyatlar sağlayıcı tarafında değişir — karar öncesi resmi dokümandan (`/docs/go`) yeniden doğrula.

---

## 1. Kota mekaniği (asıl kısıt)

Go aboneliği sabit ücretli ama **dolar değeriyle** sınırlı:

| Pencere | Limit |
|---|---|
| 5 saat | 12 $ |
| Hafta | 30 $ |
| Ay | 60 $ |

- Limit dolunca istekler **429** döner, mesaj reset süresini verir; modeller SAĞLAMDIR.
- Her modelin kendi **aylık kullanım hakkı** da var (çoğu 15 $, bazıları 30–60 $, Omen Alpha 100 $).
- Pratik sonuç: doğru model seçimi para tasarrufu değil, **hizmetin kesilmemesi** meselesidir. Pahalı bir varsayılan, ayın ortasında tüm sistemi kilitler.
- Kesintisizlik sigortası: konsolda "balance fallback" (bakiye harcaması = kullanıcı onayı gereken ödeme işi).

## 2. Resmi fiyat + kapasite (OpenCode Go dokümanı)

| Model | Girdi $/M | Çıktı $/M | Hafıza okuma $/M | Aylık istek hakkı | Aylık kullanım |
|---|---|---|---|---|---|
| Muse Spark 1.2/1.3 Contributor | 0,10 | 0,20 | 0,002 | 226.600 | 60 $ |
| MiMo-V2.5 | 0,14 | 0,28 | 0,0028 | 150.400 | 60 $ |
| Omen Alpha | 0,20 | 0,66 | 0,04 | 57.900 | 100 $ |
| LongCat-2.0 | 0,30 | 1,20 | 0,006 | 57.200 | 60 $ |
| DeepSeek V4 Flash | 0,22 / 0,44 | 0,66 / 1,32 | 0,007 / 0,014 | 37.800 | 30 $ |
| Qwen3.8 Flash | 0,15 | 0,47 | 0,016 | 27.000 | 30 $ |
| Hy3 | 0,14 | 0,58 | 0,035 | 21.500 | 60 $ |
| Qwen3.7 Plus | 0,40 | 1,60 | 0,04 | 21.600 | 60 $ |
| MiMo-V2.5-Pro | 0,435 | 0,87 | 0,0036 | 16.300 | 15 $ |
| MiniMax M3 / M2.7 | 0,30 | 1,20 | 0,06 | 16.000 / 17.000 | 60 $ |
| GPT 5.6 Luna | 0,20 | 1,20 | 0,02 | 10.250 | 15 $ |
| GLM-5.3-Flash | 0,15 | 0,50 | 0,03 | 7.900 | 15 $ |
| Kimi K2.7 Code | 0,95 | 4,00 | 0,19 | 6.750 | 60 $ |
| GLM-5.2 / 5.1 | 1,40 | 4,40 | 0,26 | 4.300 | 60 $ |
| Kimi K3 | 3,00 | 15,00 | 0,30 | 490 | 15 $ |
| Qwen3.8 Max | 2,00 | 6,00 | 0,25 | 810 | 15 $ |
| Grok 4.6 | 2,00 | 6,00 | 0,50 | 845 | 15 $ |

## 3. Bu agent'ın gerçek profili ve çağrı-başı maliyet

Ölçülen profil (67 gün, 4.767 çağrı, `state.db → session_model_usage`):
**çağrı başına 5.452 girdi / 888 çıktı / 123.191 hafızadan okuma** → günde ~71 çağrı.

Hafıza okuması baskın olduğu için sıralama ilan edilen fiyattan **farklı** çıkar:

| Model | Çağrı başı | Aylık (71 çağrı/gün) | 60 $ limitinin | Not |
|---|---|---|---|---|
| MiMo-V2.5 | 0,00136 $ | 2,90 $ | %5 | En ucuz; Türkçede dil kayması riski |
| DeepSeek V4 Flash | 0,00265 $ | 5,65 $ | %9 | En ucuz sağlam; görsel sürümü var |
| Qwen3.8 Flash | 0,00321 $ | 6,84 $ | %11 | Doğru ama yavaş (≈6,7 sn) |
| LongCat-2.0 | 0,00344 $ | 7,34 $ | %12 | ≈28 sn |
| MiMo-V2.5-Pro | 0,00359 $ | 7,67 $ | %13 | ≈14 sn |
| GLM-5.3-Flash | 0,00496 $ | 10,58 $ | %18 | En iyi denge |
| Omen Alpha | 0,00660 $ | 14,10 $ | %23 | En hızlı, hak en büyük, bağımsız kıyas kanıtı yok |
| MiniMax M3 | 0,01009 $ | 21,54 $ | %36 | Düşüncesini metne döküyor |
| Kimi K2.7 Code | 0,03214 $ | 68,60 $ | %114 | Bütçeyi tek başına aşar |
| GLM-5.2 | 0,04357 $ | 93,00 $ | %155 | Bütçeyi aşar |
| Qwen3.8 Max / Kimi K3 / Grok 4.6 | 0,047–0,078 $ | 100–166 $ | %167–277 | Bütçeyi aşar |

Yeniden hesaplama: `SELECT model, SUM(api_call_count), SUM(input_tokens), SUM(output_tokens), SUM(cache_read_tokens) FROM session_model_usage GROUP BY model` → hafıza okuma kalemini atlamadan fiyatla.

## 4. Canlı probe sonuçları (4 görev)

| Model | Araç çağırma | Türkçe sade | Talimat | Uzun bağlam | Süre (1-2 cümle iş) |
|---|---|---|---|---|---|
| GLM-5.3-Flash | ✅ | ✅ doğal | ✅ | ✅ | **1,1–1,9 sn** |
| Omen Alpha | ✅ | ✅ doğal | ✅ | ✅ | **0,9–1,5 sn** |
| DeepSeek V4 Flash | ✅ | ✅ doğal | ✅ | ✅ | 1,5–3,3 sn |
| Qwen3.8 Flash | ✅ | ✅ | ✅ | ölçülmedi | 2,1–6,7 sn |
| MiniMax M3 | ⚠️ düşünce sızıyor | ⚠️ | ✅ | – | ≈1–5 sn |
| MiMo-V2.5-Pro | ✅ | ✅ | ✅ | – | 3,5–14 sn |
| MiMo-V2.5 | ✅ | ❌ Çince cevap | ✅ | – | 1,9–8,9 sn |
| Hy3 | ✅ | ❌ gizli düşünmede tükendi | ✅ | – | ≈20 sn |
| LongCat-2.0 | ✅ | ❌ gizli düşünmede tükendi | ✅ | – | ≈28 sn |
| GPT 5.6 Luna | ❌ 500 | ❌ | ❌ | – | – |

## 5. Eleme kuralları ve gerekçeleri

- **Bozuk/çökük:** `gpt-5.6-luna` (her görevde 500), `muse-spark-1.2/1.3-contributor` (500) → config'e hiç koyma.
- **Dil kayması:** Türkçe isteme yabancı dilde cevap veren modeller özet/sıkıştırma görevlerinde Çince/İngilizce kaçak üretir; yardımcı görevlerde kullanma (veya istemde dili sabitle).
- **Gizli düşünme oburu:** `content` boş dönüp 20 sn üstü süren modeller (uzun CoT) interaktif asistan için uygun değil — doğru cevap verseler bile.
- **Düşünce sızıntısı:** iç muhakemesini cevap metnine yazan modeller kullanıcıya giden metni kirletir.
- **Bütçe katili:** çağrı-başı maliyeti tek başına aylık limiti aşan modeller (hafıza okuma fiyatı yüksek olanlar) varsayılan olamaz; yalnız nadir premium işler için.
- **Boş cevap:** çıktı bütçesini gizli düşünmeye yakan modeller (§8) uzun çıktı görevlerinde sessizce başarısız olur — oran ölçülmeden varsayılan yapma.

## 6. Seçim config'de nereye yazılır

- Ana model: `model.default` + `model.provider`.
- Yardımcı işler ayrı ayrı: `auxiliary.vision`, `.web_extract`, `.compression`, `.approval`, `.mcp`, `.title_generation`, `.curator` (her biri kendi `provider`/`model` alanını taşır). Yalnız ana modeli değiştirmek yarım çözümdür.
- Görsel okuma için ayrı sürüm gerekir (ör. `…-vision-exp`); normal sürüm görsel okumaz.
- `config.yaml` düzenlemesi: `patch` aracı reddeder → python + yaml + yedek + `os.replace` (SKILL.md §4).

## 7. Kafa kafaya iki model kıyası (tek model taramasından farkı)

`scripts/model-bench.py` bir adayın "çalışıyor mu"sunu tarar. İki modeli **birbirine karşı** ölçmek ayrı bir iştir; protokol:

1. İki modeli katalogdan doğrula (`~/.hermes/cache/endpoint_model_metadata.json`, `/docs/go`) — aynı uç nokta, aynı anahtar, `temperature=0`.
2. Görev setini sabit tut: araç çağırma · Türkçe sade anlatım · talimat takibi · kod üretme · aritmetik akıl yürütme · uzun yazma · uzun bağlam iğnesi · görsel okuma.
3. Her koşuda kaydet: süre (ms), çıktı token, `finish_reason`, ham metin. **Süre tek başına yanıltıcı** — aynı işi yapan iki modelin çıktı token'ı 8 kata kadar fark eder (ölçüldü: ~190'a karşı ~1.627).
4. Hız ve kaliteyi ayrı satırlarda raporla; kalite puanını **elle doğrula** (aşağıdaki tuzaklar).
5. Boş cevap **oranını** ölç (§8) — tek koşu kanıt değil.
6. Bağlam merdiveni: ~17k → ~240k → ~440-500k token. Kısa işte yavaş olan model uzun bağlamda öne geçebilir (prefill farkı).
7. Görsel: küçük bir PNG'yi data-URL ile gönder, içindeki sayıyı sor.
8. Parametre uyumu: `reasoning_effort` / `enable_thinking` / `thinking.type` — hangisi 400 döner, hangisi etkisiz.
9. Raporu kanıt katmanıyla yaz: **ÖLÇÜLDÜ** (bu oturumda canlı) / **İLAN EDİLDİ** (resmi doküman) / **VARSAYIM** / **BİLİNMİYOR**.

**Tuzaklar (canlı kıyasta yaşandı):**
- Sonuç anahtarlarını **türetme** (`offset // 1000` → "0k") — çakışır ve sonuç sessizce ezilir; dönen sonuç sayısı görev sayısından azsa kayıp ara.
- Aritmetik görevde "model yanlış" hükmünü **kendin hesaplamadan** verme (kesirli doğru cevap yanlış sanılıyor: 164/3 = 54,67 tam doğruydu).
- Üretilen kodu gözle okuyup puanlama — **çalıştır**. Beklenen çıktıyı elle yazarken istemi tekrar oku; yanlış hatırlanan istem iki modeli de haksız suçlatır.
- Görev sürelerini `execute_code` hücresinde uzun sıralı koşularla ölçme → 300 sn limiti keser ve sonuçlar kaybolur; paralel koş (`ThreadPoolExecutor`) veya `terminal(background=True)` + sonuç dosyası (SKILL.md §9).

### Ölçülmüş sonuç (Eylül 2026): GLM-5.3-Flash vs DeepSeek V4.1 Flash

| Boyut | GLM-5.3-Flash | DeepSeek V4.1 Flash |
|---|---|---|
| Sade Türkçe (1-2 cümle) | **1,8 sn** | 6,5 sn |
| Kod üretme | **1,5 sn** | 4,9 sn |
| Zor görev (uzun yazma) | **3,0 sn** | 21,4 sn |
| ~237k token bağlam | 12,7 sn | **6,7 sn** |
| ~440k token bağlam | 25,9 sn | **9,8 sn** |
| Aynı yazma işinde çıktı | ~190 token | ~1.627 token |
| Boş cevap (3 limit × 3 tekrar) | **0/9** | 4/9 (1200'de 3/3) |
| Aritmetik akıl yürütme | küsurat hatası | **tam doğru** |
| Görsel okuma | ✅ 1,4 sn | ✅ 2,1 sn |
| Araç çağırma (tek + paralel) | ✅ | ✅ |
| Reasoning parametreleri | 400 (kabul etmiyor) | `reasoning_effort:low` hafif kazanç |
| Aylık kapasite (bu profille) | ~3.600 iş | **~8.300 iş** |

İlan edilen (resmi): GLM-5.3-Flash 320B-A18B MoE, 1M bağlam, native multimodal, Terminal-Bench 2.1 ≈ 84,3 · DeepSeek V4.1 Flash 552B MoE (girdi 8B / çıktı 16B aktif), 1M bağlam, native görsel anlama, hafıza okuma 0,007 $ (mesai dışı).

**Mesai saati fiyatı:** DeepSeek hafta içi 01-04 ve 06-10 UTC arasında (TR 04:00-07:00 ve 09:00-13:00) fiyatı **iki katına** çıkarır — tavan hesabını gündüz trafiğiyle yap.

**Karar kuralı:** ani kesinti istemiyorsan en çok çağrı kaldıran model; günlük akıcılık istiyorsan en hızlı model. Tek model tüm işleri taşımıyorsa ikinci modeli "yedek" değil **belirli görevlerin sahibi** yap (`auxiliary.*`) — yedek, test edilmemiş davranış demektir.

## 8. Boş cevap arızası — emniyet tabanı ve oran ölçümü

- Belirti: `content` boş/null, `finish_reason="length"`, süre normal, `usage` çıktı token'ı şişkin (gizli düşünme bütçeyi yiyor). Sohbette bir kez boş cevap gelmesi = aynı koşullarda ciddi bir oran demektir.
- **Taban 4000:** ölçülen boş cevap oranı 1200'de 3/3, 2500'de 1/3, 4000'de 0/9. "mt≥2000 ile tekrar dene" eşiği **yetmez**; uzun çıktı üreten tüm çağrılarda 4000 taban kabul et.
- **Parametrelerle çözülmez (ölçüldü):** `reasoning_effort:low` hafif hızlanma verir; `minimal` etkisiz, `enable_thinking:false` etkisiz, `thinking:{type:disabled}` hızlandırır ama talimat/format uyumunu bozar. Çözüm bütçe + model seçimidir.
- Bazı modeller bu parametreleri **400 ile reddeder** → "parametre desteği" model kıyasında ayrı bir boyuttur; istemci kodu bu 400'ü tolere etmeli (parametreyi düşür, isteği tekrarla).
- Sohbet asistanı için kalıcı ayar: ana model + `auxiliary.compression` gibi uzun çıktı üreten tüm yardımcılar aynı tabana uymalı.

## 9. Kota muhasebesi tuzakları

- **Test isteminden kapasite projeksiyonu yapma.** Test görevleri 50-200 token; gerçek çağrı ~94k hafıza okuması taşır. Küçük istemle hesaplanan projeksiyon yüz binlerce istek verir ve tamamen yanlıştır — kapasiteyi `session_model_usage` gerçek profiliyle hesapla.
- **`x-opencode-session` başlığı zorunlu:** eksikse 400 `MissingSessionID`. Anahtar bazında fark edebilir (biri başlıksız da çalışır) — "aynı istek neden bir anahtarda 400" sorusunu başlıkla cevapla.
- **Bu makinedeki kayıtlar FATURALAMA kaynağı değildir.** Aynı çalışma alanında Hermes dışı (CLI/panel) tüketim olabilir; yerel kayıt limitin çok altındayken 429 geldiyse farkı tahminle kapatma — "bilinmiyor" yaz ve konsoldan doğrulama iste.
- **Farklı anahtar = farklı çalışma alanı olabilir:** biri dolu, diğeri boş olabilir. 429 mesajı hem reset süresini hem çalışma alanı kimliğini verir — ikisini de kaydet.
- **Dosyadaki anahtar canlı olmayabilir:** `config.yaml` içinde kalmış, artık kullanılmayan bir anahtar 429 döndürürken canlı anahtar tüm modelleri sorunsuz sunabilir. Bu yüzden "kota doldu" hükmünü **canlı sürecin kullandığı** kimlikle ver; okuduğun dosyadaki değeri ölçüp kurulum hakkında genel hüküm çıkarma. Ayrıca 429 bir **anahtar/çalışma alanı** hükmüdür, modelin bozuk olduğu anlamına gelmez.
