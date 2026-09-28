# Reverse Proxy Patterns — Coolify / Caddy / Traefik / Nginx

Hangi durumda hangi proxy? Bu dosya karar verme kılavuzu.

## Karar Matrisi

| Durum | Önerilen | Neden |
|---|---|---|
| Coolify self-hosted, sadece panel + 1-2 servis | **Coolify built-in nginx** | Ek container yok, sıfır config |
| Coolify + 5+ servis, otomatik routing istiyorsan | **Traefik companion** | Coolify'ın orijinal kurulumu bu, auto-SSL + labels |
| Coolify çöktü, hızlı kurtarma gerekiyor | **Caddy bypass** | 5dk'da çalışır, otomatik HTTPS |
| Çoklu domain, karışık routing, performans kritik | **Nginx external** | En esnek, en karmaşık config |
| Cloud-native, k8s/Docker Swarm, dynamic services | **Traefik** | Service discovery native |

## Coolify Standart Mimarisi

```
Internet (443)
   ↓
coolify-proxy container (Traefik v2)
   ↓ labels ile route
   ├─→ coolify:8080 (panel)
   ├─→ n8n-xyz:5678
   ├─→ esgrupmetal-app:80
   └─→ ...
```

**Kurulum:** Coolify'ın install script'i `coolify-proxy` adında Traefik container'ı oluşturur.
**Config:** Coolify panelden domain eklenince `/data/coolify/proxy/` altında dynamic config dosyası oluşur.
**Sorun:** Bu container kaybolursa/ölürse tüm public servisler offline.

### Coolify proxy container'ı yeniden oluştur

```bash
# Mevcut coolify data
ls -la /data/coolify/proxy/ 2>/dev/null

# Eğer boşsa, coolify-proxy'i sıfırdan oluştur
docker run -d \
  --name coolify-proxy \
  --restart always \
  --network coolify \
  -p 80:80 -p 443:443 \
  -v /data/coolify/proxy:/traefik \
  traefik:v2.10 \
  --providers.file.directory=/traefik \
  --providers.file.watch=true \
  --entrypoints.web.address=:80 \
  --entrypoints.websecure.address=:443 \
  --certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web \
  --certificatesresolvers.letsencrypt.acme.email=admin@DOMAIN.com \
  --certificatesresolvers.letsencrypt.acme.storage=/traefik/acme.json
```

> **NOT:** Coolify 4.x ile bu adımlar değişebilir. Güncel komutlar için: https://coolify.io/docs/installation

## Caddy Bypass — Hızlı Kurtarma

Coolify proxy tamir edilemiyorsa veya uzun sürecekse, Caddy ile köprü:

### Avantajlar
- 5 dakikada kurulur
- Otomatik HTTPS (Let's Encrypt)
- Caddyfile basit, okunabilir
- Zero-downtime reload

### Dezavantajlar
- Coolify'ın auto-routing özelliği devre dışı
- Yeni deploy edilen servisleri Caddyfile'a **manuel** eklemen gerekir
- İki katmanlı yönetim (coolify panel + Caddy config)

### Curl ile test

```bash
# Coolify internal network'teki servis IP'lerini bul
docker network inspect coolify_default | jq '.[0].Containers | to_entries[] | {name: .value.Name, ip: .value.IPv4Address}'

# Caddy'den önce direkt test
docker run --rm --network coolify_default curlimages/curl -sI http://n8n:5678
```

Caddyfile şablonu: `templates/caddy-minimal-Caddyfile`

## Traefik vs Caddy — Ne Zaman Hangisi

| Kriter | Traefik | Caddy |
|---|---|---|
| Auto-SSL | ✓ (ACME) | ✓ (built-in, daha kolay) |
| Docker labels ile dynamic config | ✓ (native) | △ (file provider lazım) |
| Config syntax karmaşıklığı | Orta | Düşük |
| Performans (high traffic) | Yüksek | Orta |
| Hot reload | ✓ (watch mode) | ✓ (file watch) |
| Coolify native | ✓ (companion) | ✗ (manual) |
| Öğrenme eğrisi | Dik | Yumuşak |

**Soğuk cevap:** Coolify kullanıyorsan Traefik, hızlı kurtarma istiyorsan Caddy.

## Nginx External — Son Çare

Çoklu domain, path-based routing, custom auth, rate limiting gerekiyorsa:

```nginx
# /etc/nginx/sites-available/public-services
server {
  listen 443 ssl http2;
  server_name n8n.aiergene.xyz;
  
  ssl_certificate /etc/letsencrypt/live/n8n.aiergene.xyz/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/n8n.aiergene.xyz/privkey.pem;
  
  location / {
    proxy_pass http://10.0.30.21:5678;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # WebSocket (n8n için gerekli)
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
  }
}
```

**Nginx external'i Caddy/Traefik'in üzerine kurmak:** yalnızca çoklu reverse proxy katmanlarından kaçınmak istiyorsan.

## DNS Tarafı — Unutulan Katman

Reverse proxy mükemmel çalışsa bile DNS yanlışsa her şey 0.

```bash
# Apex domain
dig DOMAIN.com +short
# Subdomain
dig n8n.aiergene.xyz +short
# Wildcard (coolify için gerekli)
dig *.aiergene.xyz +short

# Doğru IP'yi gösteriyor mu?
dig DOMAIN.com @8.8.8.8 | grep -A1 "ANSWER SECTION"
```

**Yaygın hatalar:**
- Apex A kaydı eski IP'yi gösteriyor (sunucu taşındı)
- `www` çalışıyor, apex çalışmıyor (veya tersi) — CNAME/A karışıklığı
- Wildcard eksik → coolify yeni subdomain oluşturamıyor

**Cloudflare proxy aktifse:** DNS only (gri bulut) yap ki gerçek IP'yi gör, sorun olursa bypass et.
