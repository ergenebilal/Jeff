#!/usr/bin/env python3
"""n8n Self-Healing Watchdog — Bilal'i rahatsız etmeden n8n'i ayakta tutar."""

import subprocess, requests, sys, time
from datetime import datetime

def log(msg):
    """Sadece hata durumunda yaz, sağlıklıyken sessiz."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", file=sys.stderr)

def check_health():
    """n8n sağlık kontrolü, 3 kademeli."""
    urls = [
        "http://localhost:5678/healthz",
        "https://n8n.aiergene.xyz/healthz",
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200 and r.json().get("status") == "ok":
                return True, url
        except:
            continue
    return False, None

def check_container():
    """n8n container çalışıyor mu?"""
    r = subprocess.run(
        ["docker", "ps", "--filter", "name=n8n-y10hlm1fr9avvxt3asz5p0bk", "--format", "{{.Status}}"],
        capture_output=True, text=True
    )
    return "Up" in r.stdout

def check_proxy():
    """n8n-proxy container çalışıyor mu?"""
    r = subprocess.run(
        ["docker", "ps", "--filter", "name=n8n-proxy", "--format", "{{.Status}}"],
        capture_output=True, text=True
    )
    return "Up" in r.stdout

def fix_proxy():
    """n8n-proxy container'ı yeniden başlat."""
    log("Proxy restart deneniyor...")
    subprocess.run(["docker", "restart", "n8n-proxy"], capture_output=True)
    time.sleep(5)
    ok, _ = check_health()
    return ok

def fix_container():
    """n8n container'ı yeniden başlat."""
    log("Container restart deneniyor...")
    subprocess.run(["docker", "restart", "n8n-y10hlm1fr9avvxt3asz5p0bk"], capture_output=True)
    time.sleep(10)
    
    # Container kalktıysa proxy'yi de restart et (IP değişebilir)
    subprocess.run(["docker", "restart", "n8n-proxy"], capture_output=True)
    time.sleep(5)
    
    ok, _ = check_health()
    return ok

def fix_full():
    """Sıfırdan proxy kur (container IP'si algıla + proxy oluştur)."""
    log("Full rebuild deneniyor...")
    
    # Container IP'sini al
    r = subprocess.run(
        ["docker", "inspect", "n8n-y10hlm1fr9avvxt3asz5p0bk", "--format", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}"],
        capture_output=True, text=True
    )
    ip = r.stdout.strip()
    
    if not ip:
        log("Container IP alınamadı, çıkış.")
        return False
    
    # Eski proxy'yi kaldır
    subprocess.run(["docker", "rm", "-f", "n8n-proxy"], capture_output=True)
    
    # Yeni proxy kur
    subprocess.run([
        "docker", "run", "-d", "--name", "n8n-proxy",
        "--restart", "unless-stopped",
        "-p", "5678:5678",
        "alpine/socat:latest",
        f"tcp-listen:5678,fork,reuseaddr", f"tcp-connect:{ip}:5678"
    ], capture_output=True)
    
    time.sleep(5)
    ok, _ = check_health()
    return ok

# ---- MAIN ----
ok, url = check_health()

if ok:
    log(f"OK ({url})")
    sys.exit(0)

log(f"❌ n8n erişilemez!")
log(f"Container: {'Up' if check_container() else 'DOWN'}")
log(f"Proxy: {'Up' if check_proxy() else 'DOWN'}")

# Tier 1: Proxy restart
if fix_proxy():
    log("✅ Tier 1 başarılı (proxy restart)")
    sys.exit(0)

# Tier 2: Container restart
if fix_container():
    log("✅ Tier 2 başarılı (container restart)")
    sys.exit(0)

# Tier 3: Full rebuild
if fix_full():
    log("✅ Tier 3 başarılı (full rebuild)")
    sys.exit(0)

# All failed — escalate to Jeff
log("🚨 TÜM TIER'LAR BAŞARISIZ! Jeff'e escalate.")
sys.exit(1)