# Coolify Reverse Proxy Kurtarma Adımları

Coolify'ın `coolify-proxy` (veya Traefik companion) container'ı kaybolduğunda/ölü olduğunda.

## Senaryo A — Proxy hiç kurulmamış

**Belirti:** `/data/coolify/proxy/` boş, hiçbir reverse proxy container yok.

```bash
# Coolify'ın orijinal Traefik v2 companion'ını oluştur
docker run -d \
  --name coolify-proxy \
  --restart always \
  --label "traefik.enable=true" \
  --network coolify \
  -p 80:80 \
  -p 443:443 \
  -v /data/coolify/proxy:/traefik \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  traefik:v2.10 \
  --providers.docker=true \
  --providers.docker.exposedbydefault=false \
  --providers.docker.network=coolify \
  --entrypoints.web.address=:80 \
  --entrypoints.websecure.address=:443 \
  --entrypoints.web.http.redirections.entryPoint.to=websecure \
  --entrypoints.web.http.redirections.entryPoint.scheme=https \
  --certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web \
  --certificatesresolvers.letsencrypt.acme.email=admin@DOMAIN.com \
  --certificatesresolvers.letsencrypt.acme.storage=/traefik/acme.json
```

**Doğrula:**
```bash
docker logs coolify-proxy --tail 20
docker ps | grep coolify-proxy
curl -sI http://DOMAIN  # coolify panel çalışıyor olmalı
```

## Senaryo B — Proxy container ölmüş, volume sağlam

```bash
# Container'ı yeniden başlat
docker start coolify-proxy 2>/dev/null || echo "Container yok"

# Eğer container tamamen silinmişse, aynı imajla yeniden oluştur (Senaryo A komutları)
# Aynı volume (/data/coolify/proxy) bağlandığı için SSL sertifikaları korunur
```

## Senaryo C — Caddy ile bypass (kalıcı çözüm değil)

`templates/caddy-minimal-Caddyfile` şablonunu kullan.

```bash
# 1. Caddy'yi Coolify network'üne ekle
docker network connect coolify_default $(docker ps -qf name=caddy)

# 2. Container IP'lerini bul
docker network inspect coolify_default \
  | jq -r '.[0].Containers | to_entries[] | "\(.value.Name) \(.value.IPv4Address)"'

# 3. Caddyfile'ı güncelle ve reload
caddy reload --config /etc/caddy/Caddyfile
```

## Senaryo D — Coolify sıfırdan (son çare)

Tüm yapı bozuksa ve proxy de container de yoksa:

```bash
# 1. Coolify'ı durdur
docker stop coolify coolify-db coolify-redis

# 2. Volume'ları kontrol et (veri kaybı olmasın)
docker volume ls | grep coolify

# 3. Coolify'ı sıfırdan kur (data volume'lar bağlı kalır)
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash

# 4. Kurulum sonrası reverse proxy otomatik gelmeli
docker ps | grep -E "coolify|traefik"
```

**DİKKAT:** Eğer orijinal `APP_KEY` kaybolduysa, tüm encrypted alanlar (SSH keys, server keys) okunamaz olur. Yedekten geri yükle:

```bash
# Coolify yedekleri
ls -la /data/coolify/backups/ 2>/dev/null
ls -la /var/www/html/storage/app/backups/ 2>/dev/null  # container içi

# Manuel .env recovery
docker run --rm -v coolify-db:/var/lib/postgresql/data postgres:15 \
  pg_dumpall -U coolify > coolify-db-dump.sql
```

## Doğrulama

Her senaryo sonrası:

```bash
# Reverse proxy çalışıyor mu?
docker ps | grep -E "coolify-proxy|traefik|caddy"

# Dışarıdan erişim
curl -sI https://DOMAIN.com
curl -sI https://n8n.DOMAIN.com

# Coolify panel
curl -sI http://localhost:8000

# ACME sertifika (Let's Encrypt)
docker logs coolify-proxy 2>&1 | grep -iE "certificate|acme" | tail -5
```

**SSL sertifikası** Let's Encrypt'ten alındıysa 90 gün geçerli. Yenileme başarısızsa:
- DNS doğru çözümleniyor mu kontrol et
- Cloudflare proxy varsa DNS-only yap
- Traefik log'da `acme` hatası var mı bak
