---
name: instagram-public-okuma
description: Read public Instagram followers/posts without login.
---

# Instagram Public Profile Reading (logged-out)

Giriş yapmadan halka açık Instagram profillerinden **takipçi sayısı, gönderi sayısı ve son gönderi tarihleri** okunur. Login, cookie, API anahtarı GEREKMEZ.

## Neden gerekli
Instagram'ı `urllib`/`requests` ile sunucu tarafından çekmek **488KB'lık JS kabuğu** döndürür (bot duvarı) — veri yok. Gerçek tarayıcı gerekiyor.

## Hangi tarayıcı yolu
**Playwright MCP kullan** (`mcp__playwright__browser_navigate` + `browser_evaluate`). Hermes'in `browser_exec` (Browser Use CLI) daemon'ı ayrı çalışır ve bağlı olmayabilir; "Chrome yok" hatası verirse **Chrome gerçekten yok demek değildir** — önce `ps aux | grep -i chrom` ile Playwright'in headless Chrome'unu kontrol et. Çalışan bir tarayıcı varsa yenisini kurma.

## Tek profil okuma (en güvenilir)
1. `browser_navigate(url="https://www.instagram.com/<handle>/")`
2. `browser_evaluate` ile:

```js
() => {
  const md = document.querySelector('meta[name="description"]')?.content || '';
  const alts = [...document.querySelectorAll('img[alt]')]
    .map(i => i.alt).filter(a => a.includes('Photo by')).slice(0, 12);
  return JSON.stringify({md, alts}, null, 1);
}
```

**Çıktı:**
- `md` → `"22K Followers, 264 Following, 1,977 Posts - See Instagram photos and videos from ELFİ Gayrimenkul (@elfigayrimenkul)"`
- `alts` → `"Photo by BURSA KILIÇ EMLAK on August 14, 2026."` → **gönderi tarihleri** = recency kanıtı

Kısa yol: `document.querySelector('header')?.innerText` de takipçi/gönderi + bio linkini verir.

## Toplu okuma (aynı origin fetch)
Profil sayfasındayken aynı origin'e fetch atılır — tek tool çağrısında onlarca profil:

```js
async () => {
  const hs = ['handle1','handle2','handle3'];
  const out = [];
  for (const h of hs) {
    const r = await fetch('https://www.instagram.com/' + h + '/');
    const t = await r.text();
    const md = t.match(/<meta[^>]+name="description"[^>]+content="([^"]*)"/i);
    out.push({h, status: r.status, desc: md ? md[1] : null});
    await new Promise(s => setTimeout(s, 1500));
  }
  return JSON.stringify(out, null, 1);
}
```

**TUZAK:** Bu yol **kararsız**. Bazen dolu meta döner, bazen sadece `<title>` gelir (sayılar `null`).
Sayı iki kez `null` geldiyse o profil için **`browser_navigate` ile tam sayfa** aç ve DOM'dan oku. Fetch yolunu tek başına kesin kanıt sayma; tarih gerekiyorsa navigate şart.

## Hesap bulma (handle discovery)
- **IG kendi arama API'si ÇALIŞMAZ:** `/web/search/topsearch/?query=...` girişsiz **429** döner.
- Kullan: Google `site:instagram.com <işletme adı> <şehir>` → sonuç gürültülüdür.
- **ZORUNLU doğrulama:** bulunan handle'ı aç, `<title>` ve bio içindeki **marka adı + telefon/site** hedefle eşleşiyor mu bak. Eşleşmiyorsa BAĞLAMA. Tuzak örneği: "Nilüfer Gayrimenkul" arandığında `resitalnilufer` çıktı — marka adı "Resital Nilüfer Gayrimenkul", farklı işletme.
- Bulunamayan hesap için **"IG'si yok" DENMEZ** → "hesap tespit edilemedi" denir.

## Sınırlar / yapılmayanlar
- Takipçi listesi, DM, beğeni sayısı okunmaz (giriş gerektirir).
- **DM gönderme / otomasyon YASAK** — bu skill sadece okuma.
- Profil gridinde ~12 gönderi görünür; daha eskisi için scroll gerekir, genelde gereksiz.

## ⚠️ HIZ SINIRI (429) — OKUMAYI TEKRARLAMA (11.09.2026)

Aynı oturumda arka arkaya profil çekmek **429** döndürür ve o tur **tamamen kör** kalır. Bugün olan: 7 handle fetch (başarılı) → 5 dakika sonra 3 handle fetch → **429**, hepsi boş.

- **Tek turda bitecek şekilde planla:** okunacak tüm handle'ları TOPLA, aralarında ~2sn bekleyerek **tek** fetch turunda çek. İkinci tur genelde 429 yer.
- **401 = API yolu öldü:** `/api/v1/users/web_profile_info/?username=` artık `HTTP 401` dönüyor (x-ig-app-id header'ı ile bile). Bu yolu denemeyi bırak; `og:description` / `meta[name=description]` yolunu kullan.
- **Doğrudan `browser_navigate` de 429 yiyebilir:** `net::ERR_HTTP_RESPONSE_CODE_FAILURE`. Bu durumda `https://www.instagram.com/` (kök) aç, oradan **aynı-origin fetch** ile profilleri çek.
- **429 aldıysan iddia kurma.** Veriyi "sonra bakarım" diye not düş, rapora yazma. Uydurma yok, eksik veri açıkça "doğrulanamadı" etiketlenir.
- `curl` ile profil çekmek **login duvarı** döner (boş) — tarayıcı dışı yol çalışmaz.

## Doğrulama kuralı
Okunan sayıyı raporda **DOĞRULANDI** diye etiketlemeden önce iki farklı okumada (fetch + navigate)
aynı çıkmasını bekle. Tek fetch sonucuyla işletme hakkında iddia kurma.
