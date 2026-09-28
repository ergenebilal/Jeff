#!/usr/bin/env python3
"""Sabah brifingi veri toplama script'i.
Evrim haritası durumu + sistem + lead özeti.
LLM cron tarafından okunur.
"""
import json, os, subprocess
from datetime import datetime

def main():
    report = []
    report.append(f"# ☀️ Günaydın Bilal — {datetime.now().strftime('%d %B %Y, %A')}")
    
    # Sistem
    uptime = os.popen("uptime -p").read().strip().replace("up ", "")
    disk = os.popen("df -h / | awk 'NR==2{print $3 \"/\" $2 \" (\" $5 \")\"}'").read().strip()
    ram = os.popen("free -h | grep Mem: | awk '{print $3}'").read().strip()
    report.append(f"\n## 💻 Sistem\n- Çalışma süresi: {uptime}\n- Disk: {disk}\n- RAM: {ram}")
    
    # Evrim haritası
    state_file = os.path.expanduser("~/.hermes/evrim_state.json")
    if os.path.exists(state_file):
        with open(state_file) as f:
            state = json.load(f)
        report.append(f"\n## 🗺️ Evrim Haritası\n- Gün: {state.get('gun', '?')}\n- Aktif Faz: {state.get('faz', '?')}")
    
    # Lead özeti
    lead_file = "/home/hermes/lead_listesi_hepsi.json"
    if os.path.exists(lead_file):
        with open(lead_file) as f:
            data = json.load(f)
            leads = data.get("leadler", data if isinstance(data, list) else [])
        toplam = len(leads)
        jeffte = sum(1 for l in leads if l.get("not") and "jeff" in l.get("not","").lower())
        report.append(f"\n## 📊 Lead Durumu\n- Toplam: {toplam if toplam > 0 else '0'}\n- Jeff'te bekleyen: {jeffte}")
    
    # Bugünün astronomisi (eğlence)
    report.append(f"\n## 🌌 Bugün Gökyüzünde\n- Jüpiter akşam güneydoğuda görünür durumda")
    
    print("\n".join(report))

if __name__ == "__main__":
    main()
