#!/bin/sh
# Antigravity Ban Kalkanı — 8999 (LLM proxy) ve 7700 (Aider bridge) için
# internetten erişimi kapatır; localhost + Tailscale açık kalır.
# Idempotent. Root olarak çalışır. Geri alma: iptables -D ...
# Yazan: Dewey · 21.09.2026

PORTS="8999 7700"
LOG=/var/log/antigravity-shield.log
TS=$(date -Is)

if [ "$(id -u)" != "0" ]; then
  echo "$TS ERROR: root degil, cikiliyor" >> "$LOG" 2>/dev/null || true
  exit 1
fi

# IPv4 kurallari (dinleyiciler IPv4: 0.0.0.0)
for P in $PORTS; do
  iptables -C INPUT -i lo -p tcp --dport "$P" -j ACCEPT 2>/dev/null || \
    iptables -I INPUT 1 -i lo -p tcp --dport "$P" -j ACCEPT
  iptables -C INPUT -i tailscale0 -p tcp --dport "$P" -j ACCEPT 2>/dev/null || \
    iptables -I INPUT 2 -i tailscale0 -p tcp --dport "$P" -j ACCEPT
  iptables -C INPUT -p tcp --dport "$P" -j DROP 2>/dev/null || \
    iptables -I INPUT 3 -p tcp --dport "$P" -j DROP
done

# Kalicilik: reboot sonrasi kurallari geri koy
CRON=/etc/cron.d/antigravity-shield
if [ ! -f "$CRON" ]; then
  printf '# Antigravity ban kalkani — reboot kaliciligi (Dewey 21.09.2026)\n@reboot root /home/hermes/.hermes/scripts/antigravity_shield.sh >/dev/null 2>&1\n' > "$CRON"
  chmod 644 "$CRON"
fi

echo "$TS OK: 8999+7700 korundu (lo+tailscale ACCEPT, diger DROP)" >> "$LOG"
iptables -S INPUT | grep -E "dport (8999|7700)" >> "$LOG"
