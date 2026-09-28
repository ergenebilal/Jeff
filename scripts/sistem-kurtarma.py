#!/usr/bin/env python3
"""Sistem Kurtarma — Gateway, Mem0, API, Disk sağlık kontrolü + oto-onarım.
Eski Faz 14 (Miras)'ın çalışan versiyonu. Hiçbir dış API'ye bağımlı değil."""
import subprocess, os, sys, json, datetime

HOME = os.path.expanduser("~")
LOG = os.path.join(HOME, ".hermes", "logs", "recovery.log")

def log_yaz(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG, "a") as f:
        f.write(f"[{ts}] {msg}\n")
    print(msg)

def kontrol_et(ad, komut, basari_str):
    """Bir servisi kontrol et, çalışmıyorsa düzelt."""
    r = subprocess.run(komut, shell=True, capture_output=True, text=True)
    if basari_str in r.stdout or basari_str in r.stderr:
        log_yaz(f"  ✅ {ad} çalışıyor")
        return True
    else:
        log_yaz(f"  ❌ {ad} çalışmıyor — onarılıyor...")
        return False

def onar(ad, komut):
    """Servisi onarmaya çalış."""
    log_yaz(f"  🔧 {ad} onarılıyor: {komut}")
    r = subprocess.run(komut, shell=True, capture_output=True, text=True, timeout=30)
    if r.returncode == 0:
        log_yaz(f"  ✅ {ad} onarıldı")
        return True
    else:
        log_yaz(f"  ❌ {ad} onarılamadı: {r.stderr[:200]}")
        return False

def disk_kontrol():
    """Disk doluluğunu kontrol et, kritikse uyar."""
    r = subprocess.run("df -h / | tail -1", shell=True, capture_output=True, text=True)
    parts = r.stdout.strip().split()
    if len(parts) >= 5:
        kullanim = parts[4].replace("%", "")
        try:
            kullanim = int(kullanim)
            if kullanim > 90:
                log_yaz(f"  ⚠️ Disk %{kullanim} dolu! Kritik seviye.")
                # Eski logları temizle
                subprocess.run("find ~/.hermes/logs -name '*.log.*' -mtime +3 -delete 2>/dev/null", shell=True)
                subprocess.run("find ~/.hermes/logs -name 'errors.log.*' -mtime +1 -delete 2>/dev/null", shell=True)
                log_yaz(f"  🧹 Eski loglar temizlendi")
                return False
            elif kullanim > 80:
                log_yaz(f"  ⚠️ Disk %{kullanim} dolu — takipte")
            else:
                log_yaz(f"  ✅ Disk %{kullanim} — sağlıklı")
            return True
        except:
            pass
    return True

def mem0_kontrol():
    """Mem0 çalışıyor mu kontrol et."""
    # Mem0'ın çalıştığını pid'den kontrol et
    r = subprocess.run("pgrep -f 'mem0' 2>/dev/null", shell=True, capture_output=True, text=True)
    if r.stdout.strip():
        log_yaz(f"  ✅ Mem0 süreci var")
    else:
        log_yaz(f"  ⚠️ Mem0 süreci yok (plugin bazlı, restart gerekmez)")
    # Qdrant kilit kontrolü
    qdrant_lock = os.path.expanduser("~/.mem0/gateway-data/.lock")
    if os.path.exists(qdrant_lock):
        # Lock dosyası 1 saatten eskiyse sorun olabilir
        age = datetime.datetime.now().timestamp() - os.path.getmtime(qdrant_lock)
        if age > 3600:
            log_yaz(f"  ⚠️ Qdrant lock dosyası eski ({age/60:.0f} dk) — yetki kontrolü yapılamadı, elle temizlik gerekebilir")
    return True

def gateway_kontrol():
    """Gateway'i kontrol et, çökmüşse restart et."""
    r = subprocess.run("systemctl is-active hermes-gateway 2>/dev/null", shell=True, capture_output=True, text=True)
    if "active" in r.stdout:
        log_yaz(f"  ✅ Gateway aktif")
        
        # Gateway'in child process'lerini kontrol et
        childs = subprocess.run("pgrep -f 'python3 server.py' 2>/dev/null | wc -l", shell=True, capture_output=True, text=True)
        # Normalde en az 1 tane olmalı (HQ server)
        
        return True
    else:
        log_yaz(f"  ❌ Gateway down!")
        onar("Gateway", "systemctl restart hermes-gateway")
        # Restart sonrası bekle ve kontrol et
        import time
        time.sleep(5)
        r2 = subprocess.run("systemctl is-active hermes-gateway 2>/dev/null", shell=True, capture_output=True, text=True)
        return "active" in r2.stdout

def api_kontrol():
    """Jeff Web API'yi kontrol et (port 8892)."""
    r = subprocess.run("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8892/health 2>/dev/null", shell=True, capture_output=True, text=True, timeout=5)
    if r.stdout.strip() == "200":
        log_yaz(f"  ✅ Jeff API (8892) çalışıyor")
        return True
    else:
        log_yaz(f"  ❌ Jeff API (8892) çalışmıyor")
        # Watchdog'u tetikle (arka planda başlatır)
        watchdog = os.path.join(HOME, ".hermes", "skills", "hermes-self", "otonom-karar-motoru", "scripts", "jeff-api-watchdog.sh")
        if os.path.exists(watchdog):
            onar("Jeff API", f"bash {watchdog}")
        return False

def kanban_kontrol():
    """Kanban board'u kontrol et (port 8889)."""
    r = subprocess.run("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8889 2>/dev/null", shell=True, capture_output=True, text=True, timeout=5)
    if r.stdout.strip() and r.stdout.strip() != "000":
        log_yaz(f"  ✅ Kanban (8889) çalışıyor")
        return True
    else:
        log_yaz(f"  ⚠️ Kanban (8889) yanıt vermiyor — kritik değil")
        return True  # Kritik değil, devam

if __name__ == "__main__":
    print(f"\n🔧 SİSTEM KURTARMA — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 45)
    
    sorun_sayisi = 0
    
    # 1. Disk kontrolü
    if not disk_kontrol(): sorun_sayisi += 1
    
    # 2. Gateway kontrolü
    if not gateway_kontrol(): sorun_sayisi += 1
    
    # 3. Mem0 kontrolü
    mem0_kontrol()
    
    # 4. Jeff API kontrolü
    if not api_kontrol(): sorun_sayisi += 1
    
    # 5. Kanban kontrolü
    kanban_kontrol()
    
    print(f"\n{'=' * 45}")
    if sorun_sayisi == 0:
        print(f"✅ TÜM SİSTEMLER SAĞLIKLI — müdahale gerekmiyor")
    else:
        print(f"⚠️ {sorun_sayisi} sorun onarıldı (veya onarılamadı)")
    
    # Özet log
    log_yaz(f"🔚 Tarama tamam — {sorun_sayisi} sorun")
