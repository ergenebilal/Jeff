# Arastirma Fan-Out + Sentez — Brief Sablonu ve Dogrulama

Derin pazar/teknoloji arastirmasi icin 4 ortogonal kol, subagent brief'i, dogrulama komutlari ve sentez iskeleti.

## Kol secimi

Kollar **birbiriyle kesismeyecek** sorular olmali. Ayni soruyu iki kola sormak iki rapor dondurur, iki bilgi dondurmez.

| Kol | Soru | Cikti |
|---|---|---|
| 1 | Bu pazarda **ne satiliyor**, kim satiyor, kaca? | urun envanteri tablosu + fiyat + sikayetler |
| 2 | Dunyada **en iyisi** ne, standart ne oldu? | karsilastirma tablosu + ozellik checklist |
| 3 | Is **gercekte nasil yuruyor**, kanal maliyeti ne, kanit var mi? | mekanizma + maliyet tablosu + kanit katmanlari |
| 4 | **Resmi yukumluluk** ne, tarih ne, ceza ne? | zorunluluk tablosu (kim/ne/hangi tarihten) |

## Subagent brief sablonu

Her kola AYNEN yazilir (alt ajan bu oturumu gormez; baglami tam ver).

```
[Bu arastirmanin neden yapildigi — 2-3 cumle baglam]

KURALLAR:
- SADECE gercekten buldugun bilgiyi yaz. Bulamadigini 'BULUNAMADI' diye isaretle.
- ASLA uydurma isim, fiyat, ozellik, tarih, oran yazma.
- Her iddianin yanina kaynak URL koy.
- Satici/firma kendi sitesindeki iddialar 'SATICI IDDIASI' olarak etiketlenir; bagimsiz kanittan AYRI tutulur.
- Fiyat bulduysan para birimini ve tarihini yaz.

NELERI ARA:
1. ...
2. ...

CIKTI: Markdown rapor, su bolumlerle: (a) ... (b) ... (c) ... (d) BULUNAMAYANLAR.
Raporu su dosya yoluna yaz ve yolu bildir: <absolute path>
```

**`output_schema` DUZ tut** — ic ice `properties` sahasi "'string' is not of type object" ile reddedilir. Serbest markdown rapor + dosya yolu daha guvenilir.

## Dogrulama (sentezden ONCE, atlanmaz)

Alt ajan ozeti **kendi beyanidir**; "rapor yazildi" demesi dosyanin var oldugu anlamina gelmez.

```bash
# 1) Dosyalar gercekten var mi
ls -la <rapor1> <rapor2> <rapor3> <rapor4>
wc -l <rapor1> <rapor2> <rapor3> <rapor4>

# 2) Kaynak URL sayisi (dusukse rapor zayiftir)
for f in <raporlar>; do echo -n "$f -> "; grep -oE 'https?://[^ )]+' $f | sort -u | wc -l; done

# 3) Kritik rakamlari dosya icinde dogrula (ozetten degil, dosyadan)
grep -inE '<anahtar rakam|atif|urun adi>' <rapor>

# 4) 'BULUNAMADI' listesi var mi (durustluk sinyali)
grep -n 'BULUNAMADI\|DOGRULANAMADI' <rapor>
```

Bir rakam ozette var ama dosyada yoksa **ozete guvenme** — dosyayi bul ya da rakamı kullanma.

## Sentez iskeleti

```
TAM RAPOR — <konu>
0.  Yonetici ozeti            (sorulan soru + net cevap + en can alici bulgu)
1.  Mekanizma                 (is gercekte nasil yuruyor — adim adim)
2.  Envanter / karsilastirma  (tablolar; fiyat bantlari)
3.  Dunya standardi           (nerede geri kaliyoruz)
4.  Maliyet ekonomisi         (somut rakamlar; degisim varsa tarihiyle)
5.  Mevzuat yuku              (kim/ne/hangi tarihten tablosu)
6.  Kanit katmanlari          (SAGLAM vs SATICI IDDIASI — ayri basliklar)
7.  NEREDE ACIK VAR           (olumlu ADAYLAR + OLU / KAPSAM DISI basliklari)
8.  Bu arastirma ne degistirdi(degisen sorular, kapanan kapi)
9.  Bilinmeyenler             (uydurmadiklarimiz)
10. Sade dil ozeti
EKLER: kaynak raporlar (govdeye gomulmez)
```

**Bolum 7 en kritik olanidir.** "Her sey zaten cozulmus" ciktiysa bunu acikca yaz.

## Arz envanteri — teklif kurmadan once yapilir

Bir arastirma bir cozume yakinlastiginda **o isi yapan kac firma oldugunu say**: isim listesi, fiyat bandi, aralarinda **ucretsiz** olan var mi.

Bu, "nis normu" kontrolunden AYRI bir kapidir:
- **Nis normu** = *kusurun* yayginligi. Bir kusur o niste herkeste varsa satis argumani degildir (20 kliniğin 11'inde site olmamasi gibi).
- **Arz envanteri** = *cozumun* yayginligi. Cozum zaten 22 urunle satiliyorsa ve biri bedavaysa teklif olur.

Iki kapidan hangisinin kapali oldugunu karistirma. Arz envanteri sonucu olumsuzsa bunu raporda acikca yaz ve **fiyat/teklif cikarma** — arastirma belgesi teklif belgesi degildir.

## Sunum kurallari

- Her iddiayi `VERIFIED / STRONGLY LIKELY / HYPOTHESIS / UNKNOWN` etiketinden biriyle isaretle.
- Satici iddialarini bagimsiz kanit gibi sunma; ayni baslikta karistirma.
- Kaynak raporlari **ayri dosyalar** olarak gonder, sentezin icine gomme.
