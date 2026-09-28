# Instagram Is-Saha Analizi — Taranan Tarif ve Pitfall'lar

IG'den is/musteri alan isletmeleri (guzellik merkezi, salon, freelance) dogrulanmis veriyle taramak icin. 09.09.2026'da 5 -> 47 handle'a 3 paralel subagent ile olceklenip calisti.

## On Kosul: Playwright MCP, browser_exec degil

`browser_exec` sunucuda Chrome baslatamaz ("chrome-not-running" fatal). Instagram profili/post okumak icin SADECE:
- `mcp__playwright__browser_navigate`
- `mcp__playwright__browser_run_code_unsafe` (async (page) => {...} gordu)

IG arama endpoint'leri (topsearch, explore/search/keyword) login duvari / ERR_HTTP_RESPONSE_CODE_FAILURE verir — onlari deneme. Dogrudan profil URL'i acilir, login gerekmez.

## Profil Verisi Cek (takipci + bio CTA + yorum)

```js
// 1. Profil: meta description takipci + bio CTA icerir ("X Followers" vb)
await page.goto('https://www.instagram.com/' + handle + '/');
await page.waitForTimeout(2500);
const meta = await page.evaluate(() =>
  document.querySelector('meta[name=description]')?.content ?? null);
const title = await page.evaluate(() => document.title);

// 2. Post linklerini topla
const links = await page.evaluate(() =>
  Array.from(document.querySelectorAll('a[href*="/p/"],a[href*="/reel/"]'))
    .slice(0,6).map(a => a.href));

// 3. Son posta git (link[0]), sonra body.innerText -> yorumlari gor
await page.goto(links[0]);
await page.waitForTimeout(3000);
const body = await page.evaluate(() => document.body.innerText);
```

Her profile 2-3sn bekle; hizli ol. ERR_HTTP_RESPONSE_CODE_FAILURE olan handle'i atla, digerine gec.

## Handle Bulma (web_search) — Rezerve Path Filtresi SART

```python
RESERVED = {'reel','p','explore','popular','search','accounts','web','direct',
            'stories','tv','help','about','terms','privacy','blog','press',
            'developers','api','logout','login','signup'}
# instagram.com/(...)/ URL'inden handle cikar, RESERVED'da değilse ve işletme adıyla
# alakaliysa (ad sozcukleri handle'a giriyorsa) kabul et.
```

Pitfall: govdesiz regex `instagram\.com/(\w+)` `reel/p/popular/explore` gibi IG path'lerini handle sanir — bunlar profil DEGIL. Handle'i profil URL'iyle dogrula (ac, title/meta'da isim gecmeli).

## Dogrulama Katmani

web_search ile bulunan handle'lar varsayimdir. Playwright ile ac, `document.title`/meta'da işletme adi gecmiyorsa PROFIL_YOK say — dogrulanmadan pazarlama hedefi yapma.

## Olcek: Paralel Subagent (47 handle, 3 grup)

- Handle listesini 3 esit gruba bol (subagent basina ~16).
- Her subagent'a AYNI kanitlanmis Playwright protokol metin olarak ver (browser_exec'i denememesi icin "SADECE mcp__playwright__* kullan" acikca yaz).
- `output_schema` DUZ tut: her isletme icin {handle, isletme_adi, takipci, cta_ozet, bilgi_isteyen_yorum_sayisi, isletme_cevap_verdi, not}. Uydurma YASAK — erisilemeyeni 'erişilmedi' isaretle.
- 5-10 dk icin tamamlanir; sonuclari tek rapora koy. 16 işletmede bilgi-isteyen soru=11, public Reply veren=0/16 gibi net sayilar satis hikayesinin omurgasidir.

## Yorum Siniflandirma

Bilgi isteyen yorum: fiyat, randevu, urun, "nasil", sorusu isareti, sube sorusu. Emoji/iltifat/cekilis etiketi bilgi isteyen DEGIL. Cevap = işletmenin "Reply" ile gorunur yaniti.

## Bilinen Ornek Veri Noktasi (referans)

BLOOM 20K + Emma 15K takipci, bio'da randevu CTA'si var ama tıklanabilir wa.me linki YOK (sadece telefon metni + "DM'e gel") — 35K takipcinin randevu akisi elle. IG'den is yapan işletmede bu, tam satilacak sorundur.
