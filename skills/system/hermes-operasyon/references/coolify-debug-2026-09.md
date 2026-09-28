# Coolify Debug Incident — 07.09.2026

**Belirti:** `https://n8n.aiergene.xyz/` ve `https://esgrupmetal.com/` açılmıyor.
**Yaklaşım:** 30+ dakika yanlış yol, sonra 10 saniyede doğru yol.
**Sonuç:** Sorun reverse proxy (Coolify'ın nginx'i host'ta değil, container içinde) — APP_KEY'e dokunmaya gerek yoktu.

## Zaman Çizgisi

| t | Aksiyon | Sonuç |
|---|---|---|
| 0:00 | Kullanıcı: "n8n.aiergene.xyz ve esgrupmetal.com açılmıyor" | — |
| 0:01 | Port 80/443 dinlemiyor tespit edildi | Reverse proxy eksik |
| 0:05 | Coolify `coolify-db` container'ı kayıp, sadece volume duruyor | DB volume sağlam |
| 0:10 | Coolify compose.prod.yml boş (eski kurulumdan kalmış) | Yeniden oluştur |
| 0:15 | Coolify container'ı oluşturuldu, dummy APP_KEY yazıldı | **GEREKSİZ** — .env'de orijinal vardı |
| 0:20 | Coolify "MAC is invalid" 500 dönüyor | APP_KEY yanlış sanıldı |
| 0:25 | DB encrypted alanları taramak için `db_check.py` yazıldı | Yanlış yol |
| 0:30 | `mac_test.py`, `check_appkey.py`, `scan_enc.py`, `db_dbg.py` × 5+ | Kör debug döngüsü |
| 0:45 | OpenCode aynı dosyayı (PrivateKey.php) okumaya başladı | Paralel keşif |
| 0:50 | `docker exec coolify cat /var/www/html/.env` | **BOMBA: APP_KEY orijinal** |
| 0:51 | Panel HTTP 302 dönüyor → APP_KEY doğru | MAC hatası başka şeyden |
| 0:55 | 80/443 hala dinlemiyor → reverse proxy ayrı konu | Coolify'ın proxy'si container içinde, host'ta değil |
| 1:00 | Caddy bypass planlandı | OpenCode'a bırakıldı |

## Kör Debug Döngüsü — Çöp Script'ler

Yazdığım ve **hiçbiri çözüme katkı sağlamamış** script'ler:

```
/tmp/db_check.py
/tmp/db_check2.py
/tmp/db_dbg.py
/tmp/db_dbg2.py
/tmp/db_dbg3.py
/tmp/scan_enc.py
/tmp/scan2.py
/tmp/scan3.py
/tmp/mac_test.py
/tmp/check_appkey.py
/tmp/check_cache.py
/tmp/check_key2.py
/tmp/restore_env.py
/tmp/diff_env.py
```

**Hepsi aynı hatanın tezahürü:** "APP_KEY kayıp olabilir" hipotezine saplanıp kalmak. Oysa 3. dakikada `cat /var/www/html/.env` ile doğrulanabilirdi.

## Gerçek Kök Sebep (ve Kanıtı)

### Kanıt 1 — APP_KEY orijinal `.env` içinde duruyor

```bash
$ docker exec coolify cat /var/www/html/.env | grep APP_KEY
APP_KEY=base64:2moJ3Zrr/XZQdtt6LcCF/mdF/tH1EMWEBU3T6CkX74c=
```

Bu key dummy **değil** — daha önce benim yazdığım 32-byte random'dan farklı (prefix `2moJ3Zrr` belirgin bir orijinal key). Yani coolify'ı yeniden oluştururken dummy key yazdığım `.env` dosyasına **yazılmamış** (volume mount başka bir dosyaya bağlı, ya da farklı yere yazıldı).

### Kanıt 2 — Coolify paneli sağlam

```bash
$ curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8000/
HTTP 302   # login'e redirect — panel çalışıyor
```

### Kanıt 3 — Laravel encrypted cast APP_KEY'e bağımlı, ama key doğru

```bash
$ docker exec coolify php artisan tinker --execute="echo config('app.key');"
base64:2moJ3Zrr/XZQdtt6LcCF/mdF/tH1EMWEBU3T6CkX74c=
$ docker exec coolify grep "protected \$casts" /var/www/html/app/Models/PrivateKey.php
protected $casts = [
    'private_key' => 'encrypted',  # ← Laravel'ın built-in encrypted cast
];
```

`encrypted` cast = `Crypt::encryptString` → APP_KEY ile HMAC + AES-256-CBC. Key doğruysa cast sorunsuz çalışır. Key değiştiyse tüm encrypted alanlar okunamaz.

### Kanıt 4 — Asıl sorun: Reverse proxy

```bash
$ ss -tlnp | grep -E ":80|:443"
(listen yok — host'ta 80/443 dinleyen bir şey yok)

$ docker ps --format "table {{.Names}}\t{{.Ports}}"
coolify    8080->8000    # paneli kendi nginx'iyle serve ediyor
n8n        (port yok)    # coolify internal network'te
```

**Coolify 4.x standart kurulumu:**
- Coolify container'ı **kendi nginx'ini** içinde barındırır (port 8080→8000)
- Reverse proxy Coolify'ın **kontrol paneli + deploy ettiği servislere** dışarıdan route eder
- Bu proxy normalde `/data/coolify/proxy/` volume'unda config tutar + coolify'ın `traefik` veya `nginx-proxy` companion container'ı çalışır
- **Bu container şu an mevcut değil** — belki kurulum sırasında oluşturulmadı, belki manuel silindi

## Dersler

### 1. Container state oku, DB'ye dalma

```bash
# İlk adım HER ZAMAN bu
docker exec CONTAINER cat /var/www/html/.env
docker exec CONTAINER php artisan tinker --execute="echo config('app.key');"
docker inspect CONTAINER --format '{{range .Config.Env}}{{println .}}{{end}}'
```

**Üçüncü adımdan sonra hâlâ kök sebep bulunmadıysa** → state'i baştan tara, hipotezini terk et.

### 2. "MAC is invalid" = semptom, sebep değil

Laravel'ın `Crypt::decryptString`'i HMAC doğrulaması başarısız olursa "MAC is invalid" döner. Bu **APP_KEY yanlış** demek **değildir**:
- Aynı key ile encrypt edilmiş veri, farklı key ile decrypt edilirse
- encrypted cast'i olan alan, manuel bir encrypt edilmiş string ise (key rotation yapılmamış)
- DB corruption olmuşsa

İlk adım: container env ve `.env` arasında key karşılaştır. İkisi aynıysa sorun başka yerde.

### 3. Coolify = 2 katmanlı proxy

```
Internet
  ↓
:443 (coolify-proxy veya Caddy — şu an YOK)
  ↓
coolify container içi nginx (port 8080)
  ↓
  ├─→ :8000 (coolify panel — çalışıyor)
  └─→ n8n/esgrupmetal container (coolify network içinde)
```

Eğer üst katman (coolify-proxy) yoksa, alt katmana dışarıdan ulaşmak **imkansız**. Kurtarma: Caddy ile bypass veya coolify-proxy companion'ı yeniden oluştur.

### 4. OpenCode paralel çalışma — izleme protokolü

Bilal "OpenCode'la yapıyorum" dediğinde ve ekran çıktısı yapıştırdığında:

| Bilal'in çıktısı | Benim doğru tepkim |
|---|---|
| `docker exec coolify sed -n 199,260p .../PrivateKey.php` | "OK, encrypted cast'i inceliyor" + **kendi tarafımda state oku** |
| OpenCode'un okuduğu dosyayı ben de oku | Aynı sonuca var, paylaş, **karşı çıkma** (görmüyorum) |
| "Şu işlemi yapıyor" (ekransız) | `who`, `ps aux`, `find -mmin` ile yan etki tara |

**Yanlış tepki:** "Göremiyorum, bilmiyorum" deyip durmak. **Doğru tepki:** "Göremiyorum ama X'i kendi başıma doğruladım, Y alternatif yol, seninkini izlemeye devam ediyorum."

### 5. /tmp'de debug script'i yığını = yanlış yoldayım sinyali

Kendi `/tmp`'ni kontrol et — son 30dk'da 5+ `check_*.py`, `scan_*.py`, `db_*.py` dosyası bıraktıysan **kör debug döngüsündesin**. Dur, state'i baştan tara.

## Quick Reference — Coolify "açılmıyor" triyaj

```bash
# 60 saniyede cevap
curl -sI https://DOMAIN  # dışarıdan ulaşılıyor mu?
ss -tlnp | grep -E ":80|:443"  # reverse proxy var mı?
docker ps  # container'lar ayakta mı?
docker exec coolify cat /var/www/html/.env | grep APP_KEY  # key sağlam mı?
docker exec coolify php artisan tinker --execute="echo config('app.key');"  # runtime key
```

Bu 5 komut 60 saniyede çalışır. **Üçünden sonra hâlâ cevap yoksa** → Caddy bypass'a geç, debug'ı bırak.
