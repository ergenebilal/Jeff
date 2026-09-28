"""
Jeff Strateji Motoru — v1.0
Haftalık: sunucu asset'lerini tara, fırsatları tespit et, öneri üret.

Token harcamaz — sadece terminal + brain katmanları.
"""

import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

STRATEJI_LOG = Path.home() / ".hermes" / "logs" / "strateji.jsonl"
STRATEJI_LOG.parent.mkdir(parents=True, exist_ok=True)


def _run(cmd: list, timeout: int = 15) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() or r.stderr.strip()
    except:
        return "?"


# ── ASSET TARAYICI ───────────────────────────────────────────────────────────

def docker_assetleri() -> list:
    """Tüm container'ları ve imajlarını listele."""
    r = _run(["sudo", "docker", "ps", "--format", "{{.Names}}|{{.Image}}|{{.Status}}"], timeout=15)
    lines = [l.strip() for l in r.split("\n") if l.strip()]
    assets = []
    for line in lines:
        parts = line.split("|")
        if len(parts) >= 3:
            assets.append({
                "name": parts[0],
                "image": parts[1],
                "status": "healthy" if "healthy" in parts[2] else ("up" if "Up" in parts[2] else "down"),
                "uptime": parts[2][:30],
            })
    return assets


def proje_assetleri() -> list:
    """/opt ve /home/hermes'teki projeler."""
    projeler = []
    for base in ["/opt", "/home/hermes"]:
        r = _run(["ls", "-d", f"{base}/*/"], timeout=5)
        for p in r.split("\n"):
            p = p.strip()
            if p and ".hermes" not in p and "snap" not in p:
                name = p.rstrip("/").split("/")[-1]
                projeler.append({"name": name, "path": p})
    return projeler


def disk_durumu() -> dict:
    r = _run(["df", "-h", "--output=used,avail,pcent,target"], timeout=5)
    lines = r.split("\n")
    disks = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 4 and "/" == parts[3]:
            disks.append({"used": parts[0], "avail": parts[1], "pcent": parts[2]})
    return disks[0] if disks else {"avail": "?", "pcent": "?"}


# ── FIRSAT TESPİTİ ───────────────────────────────────────────────────────────

def n8n_workflow_durumu() -> list:
    """n8n workflow'larını container log'larından tara."""
    try:
        r = subprocess.run(
            ["sudo", "docker", "logs", "n8n-y10hlm1fr9avvxt3asz5p0bk", "--tail", "100"],
            capture_output=True, text=True, timeout=10
        )
        lines = r.stdout.split("\n")
        workflows = []
        for line in lines:
            if "Activated workflow" in line:
                name = line.split('"')[1] if '"' in line else line
                workflows.append({"name": name.strip(), "active": True})
        return workflows
    except:
        return []


def _firsatlar(containers: list, projeler: list, disk: dict, workflows: list) -> list:
    """Mevcut duruma göre yapılabilecekleri öner."""
    oneriler = []

    container_names = [c["name"] for c in containers]

    # Eksik monitoring
    if "beszel" in container_names and "beszel-agent" not in container_names:
        pass  # beszel-agent da var

    # Odysseus aktif — not alma sistemi çalışıyor
    if "odysseus-odysseus-1" in container_names:
        oneriler.append({
            "konu": "Odysseus aktf",
            "detay": "Not alma sistemin çalışıyor. Bunu günlük iş akışına entegre edebiliriz.",
            "eylem": "Hermes + Odysseus entegrasyonu",
            "oncelik": "orta"
        })

    # Evolution API (WhatsApp) çalışıyor
    if "evolution-api" in [p["name"] for p in projeler]:
        oneriler.append({
            "konu": "Evolution API (WhatsApp) hazır",
            "detay": "WhatsApp bot altyapın çalışıyor. Müşteri iletişimi için kullanılabilir.",
            "eylem": "Müşteri destek botu için n8n workflow'u oluştur",
            "oncelik": "yuksek"
        })

    # Pilotdeck projesi var
    pilotdeck = [p for p in projeler if "pilot" in p["name"].lower()]
    if pilotdeck:
        oneriler.append({
            "konu": "Pilotdeck projesi duruyor",
            "detay": "/opt/pilotdeck mevcut. Ne durumda olduğunu kontrol edebilirim.",
            "eylem": "Pilotdeck durum kontrolü ve güncelleme",
            "oncelik": "orta"
        })

    # Disk alarmı
    disk_pcent = disk.get("pcent", "").replace("%", "")
    if disk_pcent and disk_pcent.isdigit() and int(disk_pcent) > 75:
        oneriler.append({
            "konu": "Disk doluyor",
            "detay": f"Disk %{disk_pcent} dolu. {disk.get('avail', '?')} boş.",
            "eylem": "Log temizleme, Docker prune, eski build'leri sil",
            "oncelik": "yuksek"
        })

    # SearXNG — özel arama motoru
    if "searxng" in container_names:
        oneriler.append({
            "konu": "SearXNG (özel arama) çalışıyor",
            "detay": "Kendi arama motorun var. Bunu Hermes'e entegre edebiliriz — daha özel ve sansürsüz arama.",
            "eylem": "SearXNG'i Hermes MCP olarak ekle",
            "oncelik": "dusuk"
        })

    return oneriler


# ── ÖZET ÜRETİCİ ─────────────────────────────────────────────────────────────

def generate() -> str:
    """Haftalık strateji özeti üret."""
    now = datetime.now(timezone.utc)

    containers = docker_assetleri()
    projeler = proje_assetleri()
    disk = disk_durumu()
    workflows = n8n_workflow_durumu()

    healthy = sum(1 for c in containers if c["status"] == "healthy")
    up = sum(1 for c in containers if c["status"] == "up")
    total = len(containers)

    oneriler = _firsatlar(containers, projeler, disk, workflows)

    # Kategorilere ayır
    yuksek = [o for o in oneriler if o["oncelik"] == "yuksek"]
    orta = [o for o in oneriler if o["oncelik"] == "orta"]
    dusuk = [o for o in oneriler if o["oncelik"] == "dusuk"]

    lines = [
        f"📊 **Haftalık Strateji Özeti** — {now.strftime('%d %B %Y')}",
        "",
        f"**🐳 Container'lar:** {total} çalışıyor ({healthy} sağlıklı, {up} ayakta)",
        f"**📁 Projeler:** {len(projeler)}",
        f"**💾 Disk:** {disk.get('avail','?')} boş, {disk.get('pcent','?')} dolu",
        "",
    ]

    if not oneriler:
        lines.append("✨ Her şey yolunda. Yeni bir öneri yok.")
    else:
        if yuksek:
            lines.append("**🔴 Yüksek Öncelik**")
            for o in yuksek:
                lines.append(f"  • **{o['konu']}** — {o['detay']}")
                lines.append(f"    → {o['eylem']}")
            lines.append("")

        if orta:
            lines.append("**🟡 Orta Öncelik**")
            for o in orta:
                lines.append(f"  • **{o['konu']}** — {o['detay']}")
                lines.append(f"    → {o['eylem']}")
            lines.append("")

        if dusuk:
            lines.append("**🟢 Düşük Öncelik**")
            for o in dusuk:
                lines.append(f"  • **{o['konu']}** — {o['detay']}")
                lines.append(f"    → {o['eylem']}")

    lines.append("")
    lines.append("---")
    lines.append("_Jeff Strateji Motoru — 0 token harcar_")

    # Log
    entry = {
        "timestamp": now.isoformat(),
        "containers": total,
        "healthy": healthy,
        "projeler": len(projeler),
        "disk": disk.get("pcent", "?"),
        "oneriler": len(oneriler),
        "yuksek": len(yuksek),
    }
    try:
        with STRATEJI_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass

    return "\n".join(lines)


if __name__ == "__main__":
    print(generate())
