#!/usr/bin/env bash
# Dış erişilebilirlik testi: bir portun INTERNETTEN açık olup olmadığını ölçer.
#
# NEDEN GEREKLİ: kendi sunucundan kendi public IP'ne atılan curl dış erişimi KANITLAMAZ —
# o istek loopback yolundan geçer ve `ufw-before-input -i lo -j ACCEPT` gibi kurallar onu geçirir;
# erken sıradaki `DROP tcp dpt:<port>` kuralı olan port 000 verir. Yani yerel test iç filtreyi ölçer.
#
# Kullanim: ./disaridan-erisim-testi.sh <host|ip> <port> [port...]
#   KONTROL_PORT=22 (varsayilan) — ACIK oldugu bilinen port. Kontrol portu kapali cikarsa
#   olcum GECERSIZDIR (disaridan gelen istekler engelli/olcum yolu bozuk demektir).
set -uo pipefail

if [ $# -lt 2 ]; then
  echo "kullanim: $0 <host|ip> <port> [port...]" >&2
  exit 2
fi
HOST="$1"; shift
CONTROL_PORT="${KONTROL_PORT:-22}"
API="https://check-host.net"

probe() {
  local port="$1" rid
  rid=$(curl -s -m 20 -H "Accept: application/json" \
        "$API/check-tcp?host=$HOST:$port&max_nodes=3" \
        | python3 -c 'import sys,json;print(json.load(sys.stdin).get("request_id",""))' 2>/dev/null)
  if [ -z "$rid" ]; then echo "  port $port: olcum istegi acilamadi"; return; fi
  sleep 15
  curl -s -m 20 -H "Accept: application/json" "$API/check-result/$rid" | python3 -c '
import sys, json
port = sys.argv[1]
try:
    d = json.load(sys.stdin)
except Exception:
    print("  port %s: sonuc okunamadi" % port); raise SystemExit
acik = kapali = 0
for node, res in d.items():
    if not res:
        print("  port %s: %s sonuc yok" % (port, node)); continue
    for r in res:
        if r.get("error"):
            kapali += 1
        else:
            acik += 1
hukum = "ACIK" if acik > kapali else ("KAPALI" if kapali else "BELIRSIZ")
print("  port %s: acik dugum=%d kapali dugum=%d -> %s" % (port, acik, kapali, hukum))
' "$port"
}

echo "=== dis erisim testi: $HOST  (kontrol portu: $CONTROL_PORT) ==="
echo "-- kontrol portu (acik olmali; kapali cikarsa asagidaki hukumler GECERSIZ) --"
probe "$CONTROL_PORT"
for p in "$@"; do probe "$p"; done
echo "-- yerel INPUT kural sirasi (ipucu; hukmu dis olcum verir) --"
sudo -n iptables -S INPUT 2>/dev/null | grep -nE 'DROP|ACCEPT' | head -20 || echo "(iptables okunamadi)"
