#!/usr/bin/env python3
"""Self-Reset — sistem kararsız hale gelirse en son kararlı state'e dön."""
import json
import os
import shutil
import sys
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

BACKUP_DIR: str = os.path.expanduser("~/.hermes/backups/self-reset")
STATE_BACKUP: str = os.path.join(BACKUP_DIR, "brain-state.json")
SKILLS_BACKUP: str = os.path.join(BACKUP_DIR, "skills.txt")
TZ: timezone = timezone(timedelta(hours=3))


def checkpoint() -> dict[str, Any]:
    """Mevcut state'i yedekle. Her başarılı operasyon sonrası çağrılır."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    # State.json yedeği
    state_path: str = "/tmp/hermes-brain-state.json"
    if os.path.exists(state_path):
        shutil.copy2(state_path, STATE_BACKUP)

    # Skill listesi yedeği
    skills_dir: str = os.path.expanduser("~/.hermes/skills")
    skills: list[str] = []
    for root, dirs, files in os.walk(skills_dir):
        for f in files:
            if f == "SKILL.md":
                skills.append(os.path.basename(root))
    with open(SKILLS_BACKUP, "w") as f:
        f.write("\n".join(sorted(skills)))

    result: dict[str, Any] = {
        "tarih": datetime.now(TZ).isoformat(),
        "state_kaydedildi": os.path.exists(STATE_BACKUP),
        "skill_sayisi": len(skills),
    }
    return result


def restore() -> dict[str, Any]:
    """En son yedekten geri dön."""
    result: dict[str, Any] = {"restore_edildi": False, "mesaj": ""}

    if os.path.exists(STATE_BACKUP):
        try:
            shutil.copy2(STATE_BACKUP, "/tmp/hermes-brain-state.json")
            result["state_restore"] = True
        except (IOError, OSError) as e:
            result["state_restore"] = str(e)
    else:
        result["state_restore"] = "yedek yok"

    result["restore_edildi"] = True
    result["mesaj"] = "State.json geri yüklendi"
    return result


def health_check() -> dict[str, Any]:
    """Sistem sağlığını kontrol et. Problem varsa restore öner."""
    sorunlar: list[str] = []

    # State.json var mı?
    if not os.path.exists("/tmp/hermes-brain-state.json"):
        sorunlar.append("state.json yok")

    # Skills erişilebilir mi?
    skills_dir: str = os.path.expanduser("~/.hermes/skills")
    if not os.path.exists(skills_dir):
        sorunlar.append("skills/ dizini yok")

    # Son yedek ne kadar eski?
    if os.path.exists(STATE_BACKUP):
        age: float = datetime.now().timestamp() - os.path.getmtime(STATE_BACKUP)
        if age > 3600 * 24:  # 24 saatten eski
            sorunlar.append(f"son yedek {age/3600:.0f} saat eski")

    return {
        "sağlıklı": len(sorunlar) == 0,
        "sorunlar": sorunlar,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "checkpoint":
        r = checkpoint()
        print(f"✅ Yedek: {r['skill_sayisi']} skill")
    elif len(sys.argv) > 1 and sys.argv[1] == "restore":
        r = restore()
        print(f"{'✅' if r['restore_edildi'] else '❌'} {r['mesaj']}")
    elif len(sys.argv) > 1 and sys.argv[1] == "health":
        h = health_check()
        print(f"{'✅ Sağlıklı' if h['sağlıklı'] else '❌ Sorun var'}")
        for s in h['sorunlar']:
            print(f"  ⚠️  {s}")
    else:
        print(f"Kullanım: {sys.argv[0]} [checkpoint|restore|health]")
