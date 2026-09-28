#!/usr/bin/env bash
# reverse-proxy-diagnose.sh
# Tek seferde 80/443/upstream/container state taraması.
# 60 saniyede "ne yanlış" sorusuna cevap verir.
#
# Kullanım:
#   ./reverse-proxy-diagnose.sh DOMAIN.com [CONTAINER_NAME]
# Örnek:
#   ./reverse-proxy-diagnose.sh n8n.aiergene.xyz n8n
#   ./reverse-proxy-diagnose.sh esgrupmetal.com esgrupmetal-web

set -u

DOMAIN="${1:-}"
CONTAINER="${2:-}"

if [[ -z "$DOMAIN" ]]; then
  echo "Kullanım: $0 DOMAIN [CONTAINER]"
  echo "Örnek:    $0 n8n.aiergene.xyz n8n"
  exit 1
fi

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

section() { echo -e "\n${YELLOW}=== $1 ===${NC}"; }
ok()      { echo -e "${GREEN}✓${NC} $1"; }
fail()    { echo -e "${RED}✗${NC} $1"; }

section "1. Dışarıdan erişim (curl)"
HTTP_CODE=$(curl -sk -o /dev/null -w "%{http_code}" --max-time 10 "https://$DOMAIN/" 2>/dev/null)
if [[ "$HTTP_CODE" =~ ^(200|301|302)$ ]]; then
  ok "https://$DOMAIN → HTTP $HTTP_CODE"
else
  fail "https://$DOMAIN → HTTP $HTTP_CODE (timeout/refused/down)"
fi

section "2. Host'ta dinlenen portlar (80/443)"
if ss -tlnp 2>/dev/null | grep -qE "(:80|:443)\s"; then
  ss -tlnp 2>/dev/null | grep -E ":80\s|:443\s" | head -5
  ok "80/443 dinleniyor"
else
  fail "80/443 dinlemiyor → reverse proxy eksik veya ölü"
fi

section "3. Aktif container'lar"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | head -20

if [[ -n "$CONTAINER" ]]; then
  section "4. Hedef container: $CONTAINER"
  if docker ps --format "{{.Names}}" | grep -q "^${CONTAINER}$"; then
    ok "Container ayakta"
    docker inspect "$CONTAINER" --format 'IP: {{.NetworkSettings.IPAddress}}' 2>/dev/null
    docker inspect "$CONTAINER" --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null
  else
    fail "Container '$CONTAINER' bulunamadı veya ayakta değil"
    echo "Mevcut container'lar:"
    docker ps -a --format "{{.Names}}\t{{.Status}}"
  fi
fi

section "5. DNS çözümlemesi"
RESOLVED_IP=$(dig +short "$DOMAIN" 2>/dev/null | head -1)
if [[ -n "$RESOLVED_IP" ]]; then
  ok "$DOMAIN → $RESOLVED_IP"
  SERVER_IP=$(curl -s --max-time 5 https://api.ipify.org 2>/dev/null)
  if [[ "$RESOLVED_IP" == "$SERVER_IP" ]]; then
    ok "DNS sunucu IP'si ile eşleşiyor ($SERVER_IP)"
  else
    fail "DNS ($RESOLVED_IP) sunucu IP'sinden ($SERVER_IP) farklı"
  fi
else
  fail "DNS çözümlemesi başarısız"
fi

section "6. Coolify (varsa) state"
if docker ps --format "{{.Names}}" | grep -q "^coolify$"; then
  ok "Coolify container ayakta"
  APP_KEY=$(docker exec coolify grep "^APP_KEY" /var/www/html/.env 2>/dev/null | cut -d= -f2)
  if [[ -n "$APP_KEY" ]]; then
    ok "APP_KEY .env'de mevcut: ${APP_KEY:0:20}..."
  else
    fail "APP_KEY .env'de yok"
  fi
  PANEL_HTTP=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8000/ 2>/dev/null)
  echo "Coolify panel: HTTP $PANEL_HTTP"
fi

section "7. Özet"
echo "DOMAIN: $DOMAIN"
echo "CONTAINER: ${CONTAINER:-<belirtilmedi>}"
echo "Dış HTTP: ${HTTP_CODE:-unknown}"
echo "80/443: $(ss -tlnp 2>/dev/null | grep -cE '(:80|:443)\s') listener"
echo "DNS IP: ${RESOLVED_IP:-none}"
echo
echo "Yorum:"
if [[ "$HTTP_CODE" =~ ^(200|301|302)$ ]]; then
  ok "Site erişilebilir görünüyor — kullanıcı tarafı sorun olabilir (browser cache, CDN)"
elif ! ss -tlnp 2>/dev/null | grep -qE "(:80|:443)\s"; then
  fail "Reverse proxy eksik — Caddy bypass veya coolify-proxy oluştur"
elif [[ -n "$CONTAINER" ]] && ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER}$"; then
  fail "Container ölü — restart veya yeniden deploy gerekli"
fi
