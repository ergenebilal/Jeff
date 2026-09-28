#!/usr/bin/env python3
"""
SQLite Database Optimizer — VACUUM + ANALYZE tüm .db dosyalarına.
Gece 03:00'te çalışır, sessizdir, sadece hata veya kayda değer kazanç varsa rapor verir.
Lean & Mean: sadece Python stdlib, harici bağımlılık yok.
"""

import json
import sqlite3
import time
from pathlib import Path

HERMES_HOME = Path.home() / ".hermes"

# Kritik DB'ler (büyükten küçüğe)
DB_PATHS = [
    HERMES_HOME / "state.db",                          # 329 MB — ana durum DB
    HERMES_HOME / "mnemosyne" / "data" / "mnemosyne.db",  # 572 KB — bellek
    HERMES_HOME / "mnemosyne" / "data" / "banks" / "cron" / "mnemosyne.db",  # 400 KB
    HERMES_HOME / "kanban.db",                         # 120 KB
    HERMES_HOME / "response_store.db",                 # 20 KB
]

# Profile DB'leri
PROFILE_DIR = HERMES_HOME / "profiles"
if PROFILE_DIR.exists():
    for pdir in sorted(PROFILE_DIR.iterdir()):
        if pdir.is_dir():
            db_path = pdir / "state.db"
            if db_path.exists():
                DB_PATHS.append(db_path)


def vacuum_db(db_path: Path) -> dict | None:
    """Run VACUUM and ANALYZE on a SQLite DB. Returns stats dict or None if error."""
    if not db_path.exists():
        return None

    size_before = db_path.stat().st_size
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA journal_mode=WAL;")
        
        # ANALYZE — update query planner statistics
        conn.execute("ANALYZE;")
        
        # VACUUM — rebuild database, reclaim space
        conn.execute("VACUUM;")
        
        conn.close()
    except sqlite3.Error as e:
        return {
            "path": str(db_path.relative_to(HERMES_HOME)),
            "error": str(e),
            "success": False,
        }

    size_after = db_path.stat().st_size
    saved = size_before - size_after
    saved_mb = saved / (1024 * 1024)

    result = {
        "path": str(db_path.relative_to(HERMES_HOME)),
        "size_before_mb": round(size_before / (1024 * 1024), 1),
        "size_after_mb": round(size_after / (1024 * 1024), 1),
        "saved_mb": round(saved_mb, 1),
        "success": True,
    }
    return result


def main() -> None:
    start = time.time()
    results = []
    total_saved = 0

    for db_path in DB_PATHS:
        result = vacuum_db(db_path)
        if result:
            results.append(result)
            if result.get("success") and result.get("saved_mb", 0) > 0:
                total_saved += result["saved_mb"]

    elapsed = time.time() - start

    # Sadece kayda değer kazanç varsa rapor ver
    significant = [r for r in results if r.get("success") and r.get("saved_mb", 0) >= 1.0]
    
    if significant:
        lines = ["🧹 **SQLite VACUUM Raporu**", f"⏱ {elapsed:.1f}s"]
        for r in significant:
            lines.append(f"  • {r['path']}: {r['size_before_mb']}MB → {r['size_after_mb']}MB (_{r['saved_mb']}MB kazanç_)")
        if total_saved > 0:
            lines.append(f"\n📊 Toplam kazanç: ~{total_saved:.1f} MB")
        print("\n".join(lines))
    else:
        # Sessiz — önemli kazanç yok
        pass

    # Hataları logla
    errors = [r for r in results if not r.get("success")]
    if errors:
        for err in errors:
            print(f"⚠️ VACUUM hatası: {err['path']}: {err['error']}")


if __name__ == "__main__":
    main()
