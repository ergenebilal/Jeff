#!/usr/bin/env bash
# Jeff 4.0 Health Monitor — saf script watchdog (LLM'siz)
# Sessiz çalışır: sorun yoksa boş çıktı (delivery yok), sorun varsa rapor.
set -uo pipefail

ISSUES=""

# 1. Supervisor — tüm Jeff worker'ları RUNNING mi?
SUP=$(sudo -n supervisorctl status 2>/dev/null || echo "SUPERVISOR_ERISIM_YOK")
DOWN=$(echo "$SUP" | grep -E "^jeff:" | grep -v "RUNNING" || true)
if echo "$SUP" | grep -q "SUPERVISOR_ERISIM_YOK"; then
  ISSUES+="⚠️ supervisorctl erişilemiyor (sudo izni kontrol et)\n"
elif [ -n "$DOWN" ]; then
  ISSUES+="⚠️ Duran Jeff worker'ları:\n$DOWN\n"
fi

# 2. Redis ayakta mı? (requirepass varsa supervisor conf'tan şifre çek, hardcode YOK)
REDIS_PW=$(sudo -n grep -oP 'REDIS_PASSWORD=\K[^,]+' /etc/supervisor/conf.d/jeff.conf 2>/dev/null | head -1)
if ! command -v redis-cli >/dev/null 2>&1; then
  ISSUES+="⚠️ redis-cli yok — Redis kontrol edilemiyor\n"
elif [ -n "$REDIS_PW" ]; then
  if ! REDISCLI_AUTH="$REDIS_PW" redis-cli ping 2>/dev/null | grep -q "PONG"; then
    ISSUES+="⚠️ Redis yanıt vermiyor (auth'lu ping FAILED)\n"
  fi
elif ! redis-cli ping 2>/dev/null | grep -q "PONG"; then
  ISSUES+="⚠️ Redis yanıt vermiyor (redis-cli ping FAILED)\n"
fi

# 3. Disk %85'i aşıyor mu?
DISK=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "${DISK:-0}" -gt 85 ]; then
  ISSUES+="⚠️ Disk %${DISK} — temizlik gerekli\n"
fi

# 4. RAM 500MB altına düşmüş mü?
MEM=$(free -m | awk '/^Mem:/{print $7}')
if [ "${MEM:-0}" -lt 500 ]; then
  ISSUES+="⚠️ Boş RAM ${MEM}MB — kritik seviye\n"
fi

if [ -n "$ISSUES" ]; then
  echo -e "🔴 Jeff 4.0 Health — SORUN TESPİTİ:\n\n${ISSUES}"
  exit 0
fi

# Her şey yolunda — sessiz kal (empty stdout = no delivery)
exit 0
