# Delege Edilmiş Araştırmayı Doğrulama — Tarif

Paralel alt ajanlarla araştırma yaptırıldığında (fan-out), dönen her rapor **özbeyandır**.
Sentezden önce çalıştırılacak somut adımlar:

## 1) Artefakt kontrolü

Alt ajanlar dosyayı diske yazar ve yolunu bildirir. Önce gerçekten yazıldığını gör:

```bash
ls -la /path/rapor1.md /path/rapor2.md
wc -l  /path/rapor1.md /path/rapor2.md
```

Beyandaki boyut (ör. "21,7 KB") ile gerçek boyut uyuşmuyorsa rapora güvenme.

## 2) Başlık rakamlarını raporda ara

Beyanda öne çıkan sayıları dosyanın içinde `grep` ile ara. Bulunamayan sayı = uydurma ya da karışmış.

```bash
grep -inE 'cochrane|%67|%78|no-?show' rapor.md | head -12
grep -oiE '(₺|\$|TL)\s?[0-9][0-9.,]*' rapor.md | sort | uniq -c | sort -rn | head -20
```

Not: para birimi/isim listesi çıkarmak hem doğrulama hem sentez için tek hamlede işe yarar.

## 3) Kaynak sayımı — atıfsız rapor kanıt değildir

```bash
for f in rapor*.md; do echo -n "$f -> "; grep -oE 'https?://[^ )]+' "$f" | sort -u | wc -l; done
```

## 4) Kritik sayıyı kendi verinden yeniden hesapla

Alt ajanın iddiası kendi veritabanındaki bir dağılıma dayanıyorsa (ör. "nişlerin medyan yorumu"),
aynı hesabı yerel veriyle bir kez daha koştur ve karşılaştır. Uyuşmazlık varsa rapordaki sayıyı düşür.

```python
import json, statistics as st
from collections import defaultdict
d = json.load(open('veri.json', encoding='utf-8'))
g = defaultdict(list)
for r in d: g[(r.get('niche') or '').lower()].append(r.get('reviews') or 0)
for n, v in sorted(g.items(), key=lambda x: -st.median(x[1])):
    print(f"{n:14s} n={len(v):3d} medyan={int(st.median(v))}")
```

Bu adım, beyandaki bir sıralama/üstünlük iddiasını çürütebilir (ör. "en yüksek hacimli niş" denilen niş
aslında üçüncü çıkabilir). **Doğrulama, anlatıyı bozuyorsa anlatıyı düzelt — sayıyı değil.**

## 5) Hedef-çıktı eşleştirme (çok URL'li okuma tuzağı)

Tek çağrıda birden fazla profil/URL okunduğunda araç katmanı **önbellekten başka bir hedefin
metnini** döndürebilir. Kural: dönen `title`/içerik, istediğin hedefi (`(@handle)`, alan adı,
işletme adı) içermiyorsa o satır **çöpe** gider.

- Aynı anda 5 URL veriyorsan 5 sonucun **her birini** ayrı ayrı eşleştir; sırayla geldiğini varsayma.
- `Failed to fetch` / `Error fetching content` dönen hedefler için "doğrulanamadı" yaz; sessizce boş bırakma.
- Karışan satırları raporun tablosuna **koyma** — tek yanlış eşleşme bütün tabloyu güvenilmez yapar.

## 6) Rapor dilinde sonuç

- Doğrulanan bulgu: `VERIFIED` + kaynak satırı.
- Doğrulanamayan: `UNKNOWN` / "doğrulanamadı" — uydurma ile doldurma.
- Satıcı/pazarlama kaynaklı iddialar ayrı etiketlenir (ör. bir firmanın "%40 artış" iddiası), bağımsız
  çalışmalar (meta-analiz, hakemli yayın) ayrı satırda gösterilir.
