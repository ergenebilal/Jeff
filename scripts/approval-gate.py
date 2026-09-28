#!/usr/bin/env python3
import argparse, subprocess, sys, os, time

YUKSEK_KEYWORDS = {"delete", "destroy", "remove", "reset", "--force"}
ORTA_KEYWORDS = {"write", "publish", "deploy", "send", "pay", "buy", "install"}
DUSUK_KEYWORDS = {"read", "list", "get", "search", "test", "check"}

def classify_risk(action):
    for kw in YUKSEK_KEYWORDS:
        if kw in action:
            return "YUKSEK"
    for kw in ORTA_KEYWORDS:
        if kw in action:
            return "ORTA"
    for kw in DUSUK_KEYWORDS:
        if kw in action:
            return "DUSUK"
    return "DUSUK"

def main():
    parser = argparse.ArgumentParser(description="Risk degerlendirme araci")
    parser.add_argument("action", help="Yapilacak aksiyon")
    parser.add_argument("target", help="Hedef nesne")
    parser.add_argument("--audit", action="store_true", help="Audit log'una kaydet")
    parser.add_argument("--timeout", type=int, default=0, help="Bekleme suresi (saniye, sadece YUKSEK'te anlamli)")
    args = parser.parse_args()

    risk = classify_risk(args.action.lower())

    if risk == "YUKSEK":
        msg = f"RISK: YUKSEK | Onay gerekli: Bu islem geri donulemez. Devam? (e/h)"
        print(msg)
        timeout = args.timeout if args.timeout > 0 else None
        try:
            import select
            if timeout:
                print(f"  [{timeout}s yanit bekleniyor...]")
            start = time.time()
            resp = ""
            while timeout and (time.time() - start) < timeout:
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    resp = sys.stdin.readline().strip()
                    break
            if not resp:
                resp = input() if not timeout else ""
            if resp.lower() not in ("e", "evet", "y", "yes"):
                print("ISLEM REDDEDILDI")
                if args.audit:
                    _audit_log(args, risk, "REDDEDILDI")
                sys.exit(1)
            _audit_log(args, risk, "ONAYLANDI")
        except KeyboardInterrupt:
            print("\nISLEM REDDEDILDI")
            sys.exit(1)
    elif risk == "ORTA":
        msg = "RISK: ORTA | Onerilen: once dogrula"
        print(msg)
        if args.audit:
            _audit_log(args, risk, "UYARI")
    else:
        msg = "RISK: DUSUK | Otomatik"
        print(msg)
        if args.audit:
            _audit_log(args, risk, "IZIN")

def _audit_log(args, risk, karar):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logger = os.path.join(script_dir, "audit-logger.py")
    action_str = f"{args.action} {args.target}"
    subprocess.run(
        [sys.executable, logger, action_str, "approval-gate", karar, "0"],
        capture_output=True
    )

if __name__ == "__main__":
    main()
