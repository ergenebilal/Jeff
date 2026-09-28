#!/usr/bin/env python3
"""
Token Budget Watchdog — DeepSeek balance monitor + anormal tüketim alarmı.
Her çağrıda DeepSeek API'den balance sorgular, öncekiyle karşılaştırır,
anormal düşüş varsa stderr'e alarm basar (cron job bunu Bilal'e iletir).

Çıktı formatı (stdout):
  BALANCE:1.06 | DELTA:-0.42 | RATE:0.84/h | STATUS:SPIKE

Stderr'e sadece ALARM durumlarında yazar.
Exit code: 0=normal, 1=spike, 2=kritik bakiye
"""

import json, os, sys, urllib.request, time
from datetime import datetime, timedelta

STATE_FILE = os.path.expanduser("~/.hermes/state/token_watchdog.json")
LOG_FILE = os.path.expanduser("~/.hermes/logs/token_watchdog.log")
ENV_FILE = os.path.expanduser("~/.hermes/.env")

# Eşikler
CRITICAL_BALANCE = 0.99   # $0.99 altı kritik (Bilal onayı)
SPIKE_RATE_15MIN = 0.20   # 15 dk'da $0.20+ = spike
SPIKE_RATE_1H = 0.50      # 1 saatte $0.50+ = spike
ALREADY_ALERTED_FILE = os.path.expanduser("~/.hermes/state/token_watchdog_alerted.flag")

def get_api_key():
    with open(ENV_FILE) as f:
        for line in f:
            if line.startswith("DEEPSEEK_API_KEY="):
                return line.split("=", 1)[1].strip()
    return None

def get_balance(api_key):
    req = urllib.request.Request(
        "https://api.deepseek.com/user/balance",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    for info in data.get("balance_infos", []):
        if info["currency"] == "USD":
            return float(info["total_balance"])
    return None

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"history": []}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    # Sadece son 7 günü tut
    cutoff = (datetime.now() - timedelta(days=7)).isoformat()
    state["history"] = [h for h in state["history"] if h["ts"] > cutoff]
    # En fazla 1000 kayıt
    if len(state["history"]) > 1000:
        state["history"] = state["history"][-1000:]
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def log(msg, level="INFO"):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {level}: {msg}\n")

def alarm(msg, exit_code):
    """Stderr'e alarm bas, stdout'a da durum yaz"""
    print(f"ALARM: {msg}", file=sys.stderr)
    log(msg, "ALARM")
    sys.exit(exit_code)

def main():
    api_key = get_api_key()
    if not api_key:
        alarm("DEEPSEEK_API_KEY bulunamadı", 1)
        return
    
    balance = get_balance(api_key)
    if balance is None:
        alarm("Balance sorgulanamadı", 1)
        return
    
    now = datetime.now()
    state = load_state()
    history = state.get("history", [])
    
    # Önceki balance'ı bul
    prev = None
    if history:
        prev = history[-1]
    
    # Yeni kayıt
    record = {
        "ts": now.isoformat(),
        "balance": balance
    }
    
    # Delta hesapla
    delta = 0
    rate_1h = 0
    rate_24h = 0
    
    if prev:
        prev_balance = prev["balance"]
        delta = prev_balance - balance  # pozitif = harcandı
        
        # 1 saatlik rate
        hour_ago = (now - timedelta(hours=1)).isoformat()
        hour_records = [h for h in history if h["ts"] > hour_ago]
        if hour_records:
            oldest_in_hour = hour_records[0]["balance"]
            rate_1h = oldest_in_hour - balance
        
        # 24 saatlik rate
        day_ago = (now - timedelta(hours=24)).isoformat()
        day_records = [h for h in history if h["ts"] > day_ago]
        if day_records:
            oldest_in_day = day_records[0]["balance"]
            rate_24h = oldest_in_day - balance
    
    history.append(record)
    state["history"] = history
    state["last_balance"] = balance
    state["last_check"] = now.isoformat()
    save_state(state)
    
    # Durum belirleme
    status = "OK"
    exit_code = 0
    alarms = []
    
    # Sadece 1 kez alarm kontrolü
    already_alerted = os.path.exists(ALREADY_ALERTED_FILE)

    # Kritik bakiye kontrolü — sadece 1 kez
    if balance < CRITICAL_BALANCE:
        if not already_alerted:
            status = "CRITICAL"
            exit_code = 2
            alarms.append(f"KRİTİK BAKİYE: ${balance:.2f}")
    else:
        # Balance düzeldiyse flag'i temizle (tekrar alarm verebilir)
        if already_alerted:
            os.remove(ALREADY_ALERTED_FILE)
            log("Balance düzeldi, alarm flag'i temizlendi", "INFO")

    # Spike kontrolü
    if rate_1h > SPIKE_RATE_1H:
        status = "SPIKE"
        exit_code = max(exit_code, 1)
        alarms.append(f"Anormal tüketim: 1 saatte ${rate_1h:.2f}")
    
    # Stderr'e alarm
    for a in alarms:
        print(f"ALARM: {a}", file=sys.stderr)

    # İlk alarm basıldıysa flag oluştur (tekrarını önle)
    if alarms and (status == "CRITICAL" or "KRİTİK" in str(alarms)):
        with open(ALREADY_ALERTED_FILE, "w") as f:
            f.write(datetime.now().isoformat())
    
    # Log
    if alarms:
        log(" | ".join(alarms), "ALARM")
    else:
        log(f"Balance: ${balance:.2f} | Delta: ${delta:.4f} | 1h: ${rate_1h:.4f} | 24h: ${rate_24h:.4f}", "OK")
    
    # Stdout: SADECE anormal durumda yaz (no_agent cron ile 0 token)
    # Normal durumda sessiz kal, sadece log'a yaz
    if status == "OK":
        # Normal: hiç stdout yok → cron sessiz → Bilal'e mesaj gitmez
        pass
    else:  # CRITICAL veya SPIKE
        print(f"🚨 DeepSeek {'KRİTİK BAKİYE' if status == 'CRITICAL' else 'ANORMAL TÜKETİM'}")
        print(f"   Bakiye: ${balance:.2f}")
        print(f"   1 saatlik tüketim: ${rate_1h:.2f}")
        print(f"   24 saatlik tüketim: ${rate_24h:.2f}")
        if status == "CRITICAL":
            print(f"   ‼️ Acil yükleme yapılmalı!")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
