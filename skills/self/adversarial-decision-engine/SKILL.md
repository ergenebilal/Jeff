---
name: adversarial-decision-engine
author: Jeff
description: Stratejik kararda tek LLM gorusune guvenme, debate calistir.
---

# Adversarial Decision Engine — Kullanim Protokolu

Hermes onemli kararlari yalnizca tek LLM gorusune dayanarak vermez. Motor: `/opt/hermes/jeff_v2/adversarial_engine.py` (board_deliberation.py'nin YANINA additive eklendi — mevcut sistemlerin davranisi DEGISMEZ).

## Ne Zaman Tetikle (Decision Gate)

Su trigger'lardan biri varsa DEBATE CALISTIR (L1 light yeterli):
- `niche_selection`, `product_decision`, `pricing`, `customer_segment`
- `resource_allocation` (>₺5K), `architecture_change`, `critical_sales`
- `research_strategic`, `assumption_validation` (mevcut varsayimi dogrulama)
- Geri donusu zor VEYA ekonomik etki >₺5K VEYA belirsizlik yuksek

Yoksa: NORMAL EXECUTION — debate maliyet/latency israfi.

## Nasil Calistir

```python
from adversarial_engine import AdversarialDecisionEngine
engine = AdversarialDecisionEngine(model='deepseek/deepseek-v4-flash')  # HIZLI backend — nemotron cok yavas (tek cagri 270s olabiliyor)
result = engine.run(question="...", context={...}, trigger="niche_selection",
                    economic_impact=150000, uncertainty="high")
```

- **L1_LIGHT** (3 cagri): thesis → anti-thesis → judge. Orta onemli kararlar.
- **L2_FULL** (5 cagri): + cross-exam/rebuttal/customer-sim/economic → judge. Niche/urun/fiyat/kaynak.
- **force_level='L2_FULL'** ile zorla.
- Kararlar `~/.hermes/decisions/dec_*.json` altina yazilir, `~/.hermes/logs/ade-decisions.log`'a loglanir.

## Ciktiyi Okuma

```json
{"verdict": "SCALE|TEST|ITERATE|HOLD|KILL|RESEARCH", "confidence": 0-100,
 "judge_scores": {...}, "next_experiment": {"experiment": "...", "cost": "Low|Medium|High",
 "time": "...", "success_criteria": "...", "failure_criteria": "..."}}
```

**ANAHTAR ADI TUZAĞI (11.09.2026, iki kez yasandi):** `eng.run()` ciktisinda oneri
**`next_experiment`** anahtarindadir. `next_best_experiment` runtime'da YOKTUR — o ad
hakemin ham JSON semasindaki anahtardir (`adversarial_engine.py` satir 480:
`record.next_experiment = judge.get("next_best_experiment", {})`) ve yalnizca `raw_outputs`
icinde bulunur. Raporlama script'i `next_best_experiment` basarsa sessizce `{}` yazar ve
oneri kaybolmus gibi gorunur.

- SCALE → uygula; TEST → next_best_experiment'i calistir; ITERATE → offer degismeli;
  KILL → birak; RESEARCH → once veri topla; HOLD → bekle.
- Confidence asla "LLM kendini ne kadar emin hissediyor" degil — kanit kalitesine gore.

## Kurallar

1. **Debate sonucu otomatik dis aksiyon izni DEGILDIR.** SCALE ciktiysa bile para harcama/mesaj gonderme/dis sistem degisikligi mevcut approval kurallarina tabi (madde 25).
2. Kanit katmanlari AYRI: VERIFIED/OBSERVED/INFERENCE/ESTIMATE/HYPOTHESIS/UNKNOWN. UNKNOWN'u gercek gibi kullanma.
3. **Cost control:** Ayni argumani tekrar uretme. Anti-tez guclu curutmeyle yeni bilgi uretilemiyorsa debate'i erken bitir.
4. Her verdict sonrasi NEXT BEST EXPERIMENT uret — en ucuz testle en kritik belirsizligi oldur.
5. Gercek sonuc geldiginde `record_real_world_result(decision_id, {"success": bool})` ile kalibrasyon dersi cikar (learning loop).
6. Bu motoru board_deliberation'a TERCIH ETME — ikisi farkli amac: board kural-bazli 5-director simule eder (LLM'siz), ADE gercek LLM adversarial akis. Board SCALE/HOLD derse kritik kararda ADE ile dogrula.

## Testler

`cd /opt/hermes/jeff_v2 && python3 test_adversarial_engine.py` — 18 test (gate, verdict, fallback, izolasyon, Turkce kesme isareti JSON fix'i).

## Pitfall'lar (gercek calismadan ogrenildi)

1. **Model secimi kritik**: nemotron-3.5-lightning:free cok yavas (tek LLM cagrisi 270s'ye kadar cikabiliyor — fallback zinciri 3 model × 60s). `deepseek/deepseek-v4-flash` ~8-20s/cagri, tum debate 5dk'da biter. Varsayilan modeli deepseek yap.
2. **LLM ciktisi kesilebilir** (finish_reason=length): llm_call otomatik 4000 token ile retry eder; judge stage'i `max_tokens=2400` ister (en uzun cikti).
3. **Turkce kesme isaretleri**: LLM'ler metinde `TR\'de` gibi gecersiz `\'` kacisi uretir → _parse_json bunu temizler (test_turkish_apostrophe_json_fix).
4. **Paralel demo calistirma YASAK**: iki emlak_demo sureci ayni sonuc dosyasina yazar, birbirini ezer. Calistirmadan once `pgrep -af emlak_demo` ile temizle.
5. **Demo 5-8 dk surer** (4 LLM cagrisi × 20-150s). Foreground 400s timeout YETERSIZ kalir; background=true + notify kullan, sonucu `emlak-demo-sonuc.json`'dan oku.
6. **Tam debate ciktisi karar dosyasinda**: `~/.hermes/decisions/dec_*.json` → `thesis`, `anti_thesis.evidence_audit` (kanit katmanlari), `debate_body` (cross_examination/customer_simulation/economic_analysis/rebuttal), `raw_outputs`.

7. **`failure_scenario` motorun en somut ciktisi**: `anti_thesis` icindeki
   `failure_scenario` stratejinin NASIL olecegini anlatir, `assumption_attacked` ise
   hangi varsayimin kanitsiz oldugunu. Rapor ederken ikisini de aktar — sadece skor
   tablosu vermek muhakemeyi gizler.
8. **Motorun onerdigi deney hacmi sahaya inmez**: motor genelde 10 hedef / 4 hafta gibi
   agir deney onerir. Bilal'in KILL FAST kurali 7 gun. Olcutu koru, hacmi dusur
   (ornek: 3 hedef / 7 gun) ve bu duzeltmeyi raporda acikca belirt.

## Gercek Calisma Ornegi (2026-09-09)

Emlak hipotezi L2_FULL: VERDICT=RESEARCH, conf=20. Judge: evidence=15, customer_problem=20, payment=50, capability=70, economic=25, uncertainty=85. Motor kendi tezine karsi cikti: 188K TL 'kayip' iddiasi HYPOTHESIS'e dustu, reklam butcesi 200K TL ESTIMATE, odeme istegi 15/100. Next experiment: 5-10 Bursa ofisine ucretsiz mini audit + odeme istegi olcumu.

## Gercek Calisma Ornegi (2026-09-11) — Teklif mimarisi, AYNI dikeyde zafere gecis

Ayni gun iki ADE kosusu, ayni dikey (Bursa veteriner), iki farkli soru:

- **Kirik-site stratejisi** ("12 hedefe mesaj atilmali mi?"): VERDICT=RESEARCH, conf=50.
  Skorlar: evidence=30, problem=20, odeme=30, rekabet=10, yetkinlik=50, ekonomik=20, belirsizlik=80.
- **Katmanli teklif mimarisi** ("ucretsiz audit → ucretsiz demo → 10-15K kurulum → 4-7K/ay"):
  VERDICT=**TEST**, conf=55. Skorlar: evidence=60, problem=55, **odeme=58**, **rekabet=50**,
  yetkinlik=60, ekonomik=45, belirsizlik=70.

**Ders:** Motorun en sert elestirdigi sey `competitive_advantage` idi (10). Teklif "site yapmak"
olarak ifade edildiginde emtia skoru aliyor; "kapatilan delik + olculen sonuc" olarak ifade
edildiginde 50'ye cikiyor. **Ayni is, farkli ifade = verdikt degisimi.** Bu, teklif cumlesinin
muhakeme kadar onemli oldugunu gosterir.

**Motorun gordugu kor nokta:** Antitez, retainer'i ICERIK uzerine kurulu varsayip "musteri zaten
icerik uretiyor, reddeder" dedi. Teklif metni icerigi destek bileseni yapiyordu. Ders: motora
verilen context'teki siralama bile antitezi yonlendirir — hangi bilesenin ana, hangisinin destek
oldugunu context'te acikca yaz.

## Referans

- Motor: `/opt/hermes/jeff_v2/adversarial_engine.py`
- Master prompt: `/opt/hermes/adversarial-engine/MASTER-PROMPT-v1.md`
- Demo ornegi: `/opt/hermes/adversarial-engine/emlak_demo.py`
