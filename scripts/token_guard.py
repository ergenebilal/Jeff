#!/usr/bin/env python3
"""
Jeff Token Koruma Sistemi — DeepSeek fiyatlarıyla reel-time bütçe limiti.
06.06.2026 — Dün 5 doları 1 saatte yaktın, bir daha asla.

Nasıl çalışır:
1. Hermes API'den token kullanımını okur
2. Seans başına $0.50 bütçe limiti uygular
3. %75'te uyarı, %90'da Flash'a düşür, %100'de durdurur
"""

import os
import json
import time
import sys
from pathlib import Path

# === DEEPSEEK FİYATLARI (Resmi — 06.06.2026) ===
PRICING = {
    "deepseek-v4-pro": {
        "input_cache_hit": 0.003625,   # $/1M tokens
        "input_cache_miss": 0.435,     # $/1M tokens
        "output": 0.87,                # $/1M tokens
    },
    "deepseek-v4-flash": {
        "input_cache_hit": 0.0028,
        "input_cache_miss": 0.14,
        "output": 0.28,
    },
}

# === BÜTÇE LİMİTLERİ ===
SESSION_BUDGET_USD = 0.50      # Seans başına max $0.50
DAILY_BUDGET_USD = 1.00        # Günlük max $1.00
WARNING_THRESHOLD = 0.75       # %75'te uyarı
DOWNGRADE_THRESHOLD = 0.90     # %90'da Flash'a geç
STOP_THRESHOLD = 1.00          # %100'de dur

# === DOSYA YOLLARI ===
STATE_FILE = Path.home() / ".hermes" / "data" / "token_state.json"
LOG_FILE = Path.home() / "hermes_data" / "logs" / "token-guard.log"

def load_state():
    """Mevcut seans ve günlük harcamayı yükle."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, KeyError):
            pass
    return {
        "session_cost": 0.0,
        "daily_cost": 0.0,
        "date": time.strftime("%Y-%m-%d"),
        "session_start": time.time(),
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "warnings": 0,
        "downgraded": False,
    }

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))

def compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Token sayısına göre maliyet hesapla."""
    if model not in PRICING:
        model = "deepseek-v4-pro"  # fallback
    p = PRICING[model]
    # Basit hesaplama — cache hit/miss ayırt edemeyiz, cache miss varsay
    input_cost = (input_tokens / 1_000_000) * p["input_cache_miss"]
    output_cost = (output_tokens / 1_000_000) * p["output"]
    return round(input_cost + output_cost, 6)

def log(msg: str):
    """Log mesajı yaz."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[TOKEN-GUARD] {msg}", file=sys.stderr)

def check_budget(state: dict, estimated_input: int, estimated_output: int, model: str) -> dict:
    """
    Bütçe kontrolü yap. Dönüş:
    - action: "ok" | "warn" | "downgrade" | "stop"
    - message: durum mesajı
    """
    est_cost = compute_cost(model, estimated_input, estimated_output)
    new_session_cost = state["session_cost"] + est_cost
    new_daily_cost = state["daily_cost"] + est_cost

    # Gün değişmişse sıfırla
    today = time.strftime("%Y-%m-%d")
    if state.get("date") != today:
        state["daily_cost"] = 0.0
        state["date"] = today

    session_pct = new_session_cost / SESSION_BUDGET_USD if SESSION_BUDGET_USD > 0 else 1.0
    daily_pct = new_daily_cost / DAILY_BUDGET_USD if DAILY_BUDGET_USD > 0 else 1.0

    result = {"action": "ok", "message": "", "estimated_cost": est_cost}

    if session_pct >= STOP_THRESHOLD or daily_pct >= STOP_THRESHOLD:
        result["action"] = "stop"
        result["message"] = (
            f"⛔ BÜTÇE LİMİTİ AŞILDI! "
            f"Seans: ${new_session_cost:.4f}/{SESSION_BUDGET_USD:.2f} ({session_pct:.0%}), "
            f"Günlük: ${new_daily_cost:.4f}/{DAILY_BUDGET_USD:.2f} ({daily_pct:.0%})"
        )
    elif session_pct >= DOWNGRADE_THRESHOLD and model == "deepseek-v4-pro":
        result["action"] = "downgrade"
        result["message"] = (
            f"⬇️ Bütçe %90 — V4 Pro → Flash. "
            f"Seans: ${new_session_cost:.4f}/{SESSION_BUDGET_USD:.2f}, "
            f"Tahmini maliyet: ${est_cost:.4f}"
        )
    elif session_pct >= WARNING_THRESHOLD:
        result["action"] = "warn"
        result["message"] = (
            f"⚠️ Bütçe %75 aşıldı! "
            f"Seans: ${new_session_cost:.4f}/{SESSION_BUDGET_USD:.2f}, "
            f"Bu işlem: ~${est_cost:.4f}"
        )

    return result


if __name__ == "__main__":
    # CLI: token_guard.py [check|report|reset|update] [args...]
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"

    if cmd == "report":
        state = load_state()
        today = time.strftime("%Y-%m-%d")
        daily = state["daily_cost"] if state.get("date") == today else 0.0
        session_pct = state["session_cost"] / SESSION_BUDGET_USD if SESSION_BUDGET_USD > 0 else 0
        daily_pct = daily / DAILY_BUDGET_USD if DAILY_BUDGET_USD > 0 else 0
        
        log(f"📊 Rapor: Seans ${state['session_cost']:.4f} | Günlük ${daily:.4f} | "
            f"Input {state['total_input_tokens']:,} | Output {state['total_output_tokens']:,} | "
            f"Düşürüldü: {state['downgraded']}")
        
        # SADECE %50'nin üzerinde stdout'a yaz (cron sessiz kalsın)
        if session_pct >= 0.50 or daily_pct >= 0.50:
            print(json.dumps({
                "alert": True,
                "session_pct": round(session_pct * 100, 1),
                "daily_pct": round(daily_pct * 100, 1),
                "session_cost": state["session_cost"],
                "daily_cost": daily,
                "session_budget": SESSION_BUDGET_USD,
                "daily_budget": DAILY_BUDGET_USD,
            }))

    elif cmd == "check":
        model = sys.argv[2] if len(sys.argv) > 2 else "deepseek-v4-pro"
        est_input = int(sys.argv[3]) if len(sys.argv) > 3 else 10000
        est_output = int(sys.argv[4]) if len(sys.argv) > 4 else 5000

        state = load_state()
        result = check_budget(state, est_input, est_output, model)

        print(json.dumps(result))
        log(f"🔍 Check: {model}, ~{est_input:,}+{est_output:,} token → {result['action'].upper()}")
        if result["message"]:
            log(f"   {result['message']}")

        if result["action"] == "stop":
            sys.exit(1)  # Exit code 1 = dur

    elif cmd == "reset":
        today = time.strftime("%Y-%m-%d")
        state = {
            "session_cost": 0.0,
            "daily_cost": 0.0,
            "date": today,
            "session_start": time.time(),
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "warnings": 0,
            "downgraded": False,
        }
        save_state(state)
        log("🔄 Sıfırlandı")
        print(json.dumps({"status": "reset", "state": state}))

    elif cmd == "update":
        model = sys.argv[2] if len(sys.argv) > 2 else "deepseek-v4-pro"
        input_tokens = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        output_tokens = int(sys.argv[4]) if len(sys.argv) > 4 else 0

        state = load_state()
        cost = compute_cost(model, input_tokens, output_tokens)
        state["session_cost"] = round(state["session_cost"] + cost, 6)
        state["daily_cost"] = round(state["daily_cost"] + cost, 6)
        state["total_input_tokens"] += input_tokens
        state["total_output_tokens"] += output_tokens
        save_state(state)
        print(json.dumps({"status": "updated", "added_cost": cost, "state": state}))
        log(f"💰 +${cost:.6f}: {model} {input_tokens:,}→{output_tokens:,} | "
            f"Seans ${state['session_cost']:.4f}/{SESSION_BUDGET_USD:.2f}")
