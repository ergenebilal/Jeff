#!/usr/bin/env bash
# NotebookLM (nlm) oturum teşhisi.
# Ağ mı, oturum mu? Ne zaman öldü? Kurtarma yolu ne?
# GÜVENLİK: cookie DEĞERLERİ asla yazdırılmaz — yalnız sayı/isim/zaman.
set -uo pipefail

BASE="${HOME}/.notebooklm-mcp-cli"

step() { printf '\n=== %s ===\n' "$1"; }

step "1. Ağ kontrolü (oturum mu, ağ mı?)"
for h in https://notebook.google.com https://accounts.google.com https://www.google.com; do
  printf '%-36s ' "$h"
  code=$(curl -s -o /dev/null -m 15 -w '%{http_code}' "$h" 2>/dev/null)
  if [ -n "$code" ] && [ "$code" != "000" ]; then
    echo "HTTP $code  (ağ SAĞLAM)"
  else
    echo "ERİŞİLEMEDİ  (ağ sorunu olabilir)"
  fi
done

step "2. nlm auth durumu"
if command -v nlm >/dev/null 2>&1; then
  timeout 40 nlm login --check 2>&1 | tail -4
else
  echo "nlm bulunamadı (PATH?)"
fi

step "3. Profil durumu (değerler gizli)"
python3 - "$BASE" <<'PY'
import glob, json, os, sys, time
base = sys.argv[1]

metas = sorted(glob.glob(os.path.join(base, "profiles", "*", "metadata.json")))
if not metas:
    print("  metadata.json bulunamadı:", os.path.join(base, "profiles"))
for p in metas:
    name = os.path.basename(os.path.dirname(p))
    try:
        d = json.load(open(p))
    except Exception as e:
        print(f"  {name}: okunamadı ({e})")
        continue
    lv = d.get("last_validated")
    if isinstance(lv, (int, float)) and lv > 1e9:
        when = time.strftime("%d.%m.%Y %H:%M", time.localtime(lv))
        age = (time.time() - lv) / 3600
        when += f"  ({age:.1f} saat önce)"
    else:
        when = str(lv)
    print(f"  [{name}] hesap: {d.get('email', '?')}")
    print(f"           son geçerli doğrulama: {when}")

for p in sorted(glob.glob(os.path.join(base, "profiles", "*", "cookies.json"))):
    try:
        c = json.load(open(p))
        if isinstance(c, dict):
            c = c.get("cookies", [])
        print(f"  {os.path.relpath(p, base)}: {len(c)} cookie")
    except Exception as e:
        print(f"  {p}: okunamadı ({e})")

for p in sorted(glob.glob(os.path.join(base, "profiles", "*", "backup_ha", "metadata-*.json")))[-3:]:
    try:
        d = json.load(open(p))
        lv = d.get("last_validated")
        if isinstance(lv, (int, float)) and lv > 1e9:
            lv = time.strftime("%d.%m.%Y %H:%M", time.localtime(lv))
        print(f"  yedek {os.path.basename(p)}: son doğrulama {lv}")
    except Exception:
        pass
PY

step "4. Kurtarma"
echo "  Kullanıcı cookie dosyası verirse:"
echo "      nlm login --manual -f /home/hermes/nlm-cookies.txt"
echo "  Kabul edilen formatlar: Copy as cURL | cookie header | JSON | Netscape cookies.txt"
echo "  UYARI: kullanıcının canlı cookie'lerini otomatik tarayıcıya enjekte ETME — oturum iptal olur."
