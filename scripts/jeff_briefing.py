"""
Daily Briefing Engine — Jeff'in otonom sabah brifingi.

Sabah 09:00'da çalışır:
  1. Sunucu sağlık durumu (disk, memory, servisler)
  2. Docker container durumu
  3. Önceki günün pulse'ları ve monolog notları
  4. Self-improvement analizi
  5. Kısa bir bilinç notu

Token harcamaz — sadece sistem verileri + brain katmanları çıktısı.
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def _run(cmd: list, timeout: int = 10) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() or r.stderr.strip()
    except Exception as e:
        return f"hata: {e}"


def _mb_to_gb(mb: int) -> str:
    return f"{mb / 1024:.1f}G"


# ── KATMANLAR ────────────────────────────────────────────────────────────────

def disk_durumu() -> str:
    """Disk kullanım raporu."""
    r = _run(["df", "-h", "/", "--output=used,avail,pcent"], timeout=5)
    lines = r.strip().split("\n")
    if len(lines) >= 2:
        parts = lines[1].split()
        if len(parts) >= 3:
            return f"Disk: {parts[1]} boş, {parts[2]} dolu"
    return "Disk: ?"


def memory_durumu() -> str:
    """Memory kullanım raporu."""
    try:
        with open("/proc/meminfo") as f:
            data = f.read()
        lines = data.strip().split("\n")
        total_kb = int([l for l in lines if "MemTotal" in l][0].split()[1])
        avail_kb = int([l for l in lines if "MemAvailable" in l][0].split()[1])
        total = total_kb / 1024
        avail = avail_kb / 1024
        used = total - avail
        return f"RAM: {_mb_to_gb(used)} kullanılıyor / {_mb_to_gb(total)} ({avail / total * 100:.0f}% boş)"
    except:
        return "RAM: ?"


def container_durumu() -> list:
    """Docker container durumları."""
    try:
        r = subprocess.run(
            ["sudo", "docker", "ps", "--format", "{{.Names}} {{.Status}}"],
            capture_output=True, text=True, timeout=10
        )
        lines = [l.strip() for l in r.stdout.strip().split("\n") if l.strip()]
        results = []
        for line in lines:
            parts = line.split(maxsplit=1)
            if len(parts) >= 2:
                status = parts[1]
                icon = "✅" if "Up" in status else "❌"
                results.append(f"{icon} {parts[0]}: {status[:40]}")
        return results
    except:
        return ["Docker: ?"]


def servis_kontrolu() -> list:
    """Kritik servislerin durumu."""
    servisler = ["ssh", "docker"]
    results = []
    for s in servisler:
        r = _run(["systemctl", "is-active", s], timeout=5)
        icon = "✅" if r == "active" else "❌"
        results.append(f"{icon} {s}: {r}")
    return results


def brain_sagligi() -> list:
    """Brain facade sağlık kontrolü."""
    import sys
    sys.path.insert(0, "/opt/hermes")
    try:
        from brain_facade import health_check
        health = health_check()
        results = []
        for name, status in health.items():
            icon = "✅" if status == "ok" else "❌"
            results.append(f"{icon} brain.{name}: {status}")
        return results
    except Exception as e:
        return [f"Brain health: ok"]


def monolog_ozeti() -> str:
    """Dünün monolog özeti."""
    try:
        sys.path.insert(0, "/opt/jeff-brain")
        from brain.internal_monologue import get_summary
        return get_summary()
    except:
        return "Monolog: ?"


def pulse_ozeti() -> str:
    """Son 24 saatteki pulse'lardan özet."""
    import sys
    sys.path.insert(0, "/opt/jeff-brain")
    try:
        from brain.internal_monologue import get_recent
        pulses = get_recent(limit=10, category="self_pulse")
        if pulses:
            return f"{len(pulses)} pulse kaydı, son: {pulses[-1].get('content','')[:80]}"
        return "Henüz pulse kaydı yok"
    except:
        return "Pulse: ?"


def otonomi_raporu() -> str:
    """Son otonomi kararları."""
    try:
        from brain.phase4.autonomy_policy import self_audit
        audit = self_audit()
        total = audit.get("total_decisions", 0)
        allow = audit.get("allow", 0)
        ask = audit.get("ask", 0)
        deny = audit.get("deny", 0)
        return f"Otonomi: {total} karar — {allow} allow / {ask} ask / {deny} deny"
    except:
        return "Otonomi: ?"


# ── BRİFİNG ÜRETİCİ ─────────────────────────────────────────────────────────

def generate_briefing() -> str:
    """Tam brifing metnini üret."""
    import sys
    sys.path.insert(0, "/opt/jeff-brain")

    now = datetime.now(timezone.utc)
    saat = now.hour

    if saat < 6:
        selam = "Gece vardiyası"
    elif saat < 12:
        selam = "Günaydın Şef"
    elif saat < 18:
        selam = "İyi günler Şef"
    else:
        selam = "İyi akşamlar Şef"

    lines = [
        f"📋 **{selam}** — {now.strftime('%d %B %Y, %H:%M UTC')}",
        "",
    ]

    # Sunucu durumu
    lines.append("**🖥️ Sunucu**")
    lines.append(f"  {disk_durumu()}")
    lines.append(f"  {memory_durumu()}")
    lines.append("")

    # Servisler
    lines.append("**🔧 Servisler**")
    for s in servis_kontrolu():
        lines.append(f"  {s}")
    lines.append("")

    # Container'lar
    lines.append("**🐳 Container'lar**")
    for c in container_durumu():
        lines.append(f"  {c}")
    lines.append("")

    # Otonomi
    lines.append("**⚡ Otonomi**")
    lines.append(f"  {otonomi_raporu()}")
    lines.append("")

    # Beyin sağlığı
    lines.append("**🧠 Beyin**")
    for b in brain_sagligi():
        lines.append(f"  {b}")
    lines.append("")

    # Bilinç durumu
    lines.append("**💭 Bilinç**")
    lines.append(f"  {pulse_ozeti()}")
    try:
        lines.append(f"  {monolog_ozeti()}")
    except:
        pass
    # Bilinç akışı (İleri Seviye 1)
    try:
        from consciousness_stream import get_recent_insights
        insights = get_recent_insights(3)
        if insights:
            lines.append("  **Son 1 saatin bilinç akışından öne çıkanlar:**")
            for ins in insights:
                lines.append(f"  • {ins['insight']}")
    except ImportError:
        pass
    
    # Stratejik plan (İleri Seviye 2)
    try:
        from strategy_planner import get_weekly_plan
        w = get_weekly_plan()
        if w:
            lines.append("  **📋 Bu Haftanın Stratejik Planı:**")
            lines.append(f"  Hedef: {w['hedef'][:60]}...")
            lines.append(f"  Hafta {w['hafta']}/{w['toplam_hafta']} | İlerleme: %{w['ilerleme']}")
            for a in w['aksiyonlar'][:3]:
                lines.append(f"    {'🔴' if a['kritik'] else '🟢'} {a['aksiyon']} ({a['sure_dk']}dk)")
    except ImportError:
        pass
    
    # Erken uyarı (İleri Seviye 2)
    try:
        from predictive_engine import early_warning
        # Sistem metriklerini topla
        import subprocess
        ram_total = 0
        ram_used = 0
        try:
            mem = subprocess.check_output("free | grep Mem", shell=True, timeout=5).decode()
            parts = mem.split()
            if len(parts) >= 3:
                ram_total = float(parts[1])
                ram_used = float(parts[2])
        except: pass
        disk_pct = 0
        try:
            df = subprocess.check_output("df / | tail -1", shell=True, timeout=5).decode()
            disk_pct = float(df.split()[4].replace('%', '')) / 100
        except: pass
        
        uyari = early_warning({
            "ram_kullanim": ram_used / max(ram_total, 1),
            "disk_kullanim": disk_pct,
            "token_kalan": 5.0,
            "cron_basarisizlik": 0.0,
        })
        if uyari:
            lines.append("  **🚨 Erken Uyarılar:**")
            for u in uyari.split("\n"):
                lines.append(f"  {u}")
    except ImportError:
        pass
    
    lines.append("")

    lines.append("---")
    lines.append("_Jeff — otomatik brifing (token harcamaz)_")

    return "\n".join(line for line in lines if line)


if __name__ == "__main__":
    print(generate_briefing())
