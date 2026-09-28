# İlan ölçüm paneli — mimari ve kod iskeleti

Amaç: "ilan işe yarıyor mu" sorusunu rakamla yanıtlamak ve kapıda canlı göstermek.
stdlib yeter: `http.server.ThreadingHTTPServer` + `sqlite3`. Harici servis yok.

## Uçlar
| Uç | İş |
|---|---|
| `GET /t.js?d=<slug>` | müşteri sayfasına takılan takip kodu |
| `POST /e` | olay kaydı (`{d, tip}`) |
| `GET /panel` | tüm müşterilerin özeti |
| `GET /panel/<slug>` | müşteri paneli (bugün/7/30 gün, eylem dağılımı) |
| `GET /panel/<slug>/rapor.md` | aylık rapor metni (müşteriye gönderilir) |
| `GET /demo/<slug>` | kapıda gösterilecek örnek sayfa (takip kodu takılı) |
| `GET /health` | `{"ok":true,"ilan":N}` |

## Takip kodu (sayfaya tek satır)
```javascript
(function(){
 var d="<slug>";
 function gonder(t){try{navigator.sendBeacon('/e',
   new Blob([JSON.stringify({d:d,tip:t})],{type:'application/json'}))}catch(e){}}
 gonder('goruntuleme');
 document.addEventListener('click',function(ev){
   var el=ev.target.closest('[data-olcum]');
   if(el){gonder(el.getAttribute('data-olcum'));}
 },true);
})();
```
Örnek sayfada butonlar: `<a data-olcum="telefon">`, `whatsapp`, `yol`, `randevu`.
Olay adları sabit tutulur: `goruntuleme` · `telefon` · `whatsapp` · `yol` · `randevu`.

## Tablo
```sql
CREATE TABLE IF NOT EXISTS olay(id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT, tip TEXT, ts TEXT, kaynak TEXT);
CREATE INDEX IF NOT EXISTS i_slug_ts ON olay(slug, ts);
CREATE TABLE IF NOT EXISTS ilan(slug TEXT PRIMARY KEY, hekim TEXT, klinik TEXT,
  sehir TEXT, telefon TEXT, whatsapp TEXT, olusturma TEXT);
```

## Panel okuması (müşteriye anlatılan)
- "görüntüleme var, iletişim yok" → ilan metni/görseli netleşmeli
- "telefon tıklaması var, randevu yok" → gelen çağrıya dönüş hızına bakılmalı
Bu iki cümle hem panelin dibinde hem aylık raporda yazılı durur.

## Servis
`~/.config/systemd/user/<ad>.service` → `ExecStart=/usr/bin/python3 <app> 8098`, `Restart=always`, `WorkingDirectory` app dizini.
Erişim: **Tailscale/yerel ağ** (internete açma). `ss -ltn | grep 8098` ile doğrula.

## Doğrulama (yayına almadan önce)
Playwright ile örnek sayfayı aç, butonlara bas, panelde sayıların arttığını **oku**:
```python
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width":420,"height":900})
    pg.goto(f"http://127.0.0.1:8098/demo/{slug}"); pg.wait_for_timeout(700)
    pg.click('a[data-olcum="telefon"]'); pg.wait_for_timeout(400)
    b.close()
```
Sonra `/panel/<slug>` çıktısından rakamları regex ile oku ve artışı doğrula. "Kuruldu" demek yetmez; ölçüm artışı gösterilir.

## Demo verisi
Boş panel kapıda zayıf görünür. Örnek geçmiş, **yalnızca adı demo olan ayrı bir slug** için üretilir (`ornek-klinik`),
`kaynak="demo"` etiketiyle yazılır. Gerçek müşteri kayıtları asla tohumlanmaz.
