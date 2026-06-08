"""First mission: scan for Hermes/Jeff/Bilal references across the filesystem.

Scans .txt, .md, .py files for keywords "hermes", "jeff", "bilal"
and writes a structured report to ~/.hermes/reports/first_mission.json.
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPORTS_DIR = Path.home() / ".hermes" / "reports"
REPORT_FILE = REPORTS_DIR / "first_mission.json"

# Scan targets — user's home and common document locations
SCAN_ROOTS = [
    Path.home(),
    Path("C:/Users"),
]

EXCLUDE_DIRS = {
    "AppData", "__pycache__", ".git", ".venv", "venv", "node_modules",
    ".claude", ".hermes", ".cache", ".npm", ".m2",
}

KEYWORDS = ["hermes", "jeff", "bilal"]
EXTENSIONS = (".txt", ".md", ".py")


def _should_scan(path: Path) -> bool:
    """Check if a directory should be scanned."""
    name = path.name
    if name.startswith(".") and name not in (".config", ".local"):
        return False
    if name in EXCLUDE_DIRS:
        return False
    return True


def scan() -> dict:
    """Scan filesystem for keyword matches.

    Returns structured report with per-file details and summary stats.
    """
    results: list[dict] = []
    files_scanned = 0
    files_matched = 0
    keyword_counts: dict[str, int] = {k: 0 for k in KEYWORDS}
    errors: list[str] = []

    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root, topdown=True):
            current = Path(dirpath)

            # Prune excluded dirs in-place (affects os.walk)
            dirnames[:] = [d for d in dirnames if _should_scan(current / d)]

            # Limit depth — don't go too deep
            rel = current.relative_to(root) if root in current.parents else current
            if len(rel.parts) > 6:
                dirnames.clear()
                continue

            for fname in filenames:
                if not fname.lower().endswith(EXTENSIONS):
                    continue
                fpath = current / fname
                files_scanned += 1

                try:
                    text = fpath.read_text(encoding="utf-8", errors="ignore")
                except (OSError, PermissionError):
                    continue

                line_matches: list[dict] = []
                for i, line in enumerate(text.split("\n"), 1):
                    lower = line.lower()
                    for kw in KEYWORDS:
                        if kw in lower:
                            line_matches.append({
                                "line": i,
                                "keyword": kw,
                                "snippet": line.strip()[:120],
                            })
                            keyword_counts[kw] += 1

                if line_matches:
                    files_matched += 1
                    results.append({
                        "file": str(fpath),
                        "matches": len(line_matches),
                        "lines": line_matches[:20],  # cap per-file
                    })

    # Sort by most matches first
    results.sort(key=lambda x: x["matches"], reverse=True)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mission": "first_mission",
        "summary": {
            "files_scanned": files_scanned,
            "files_matched": files_matched,
            "total_matches": sum(keyword_counts.values()),
            "keyword_breakdown": keyword_counts,
        },
        "top_results": results[:50],
        "total_result_files": len(results),
    }

    # Write report
    try:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        REPORT_FILE.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Rapor yazildi: {REPORT_FILE}")
    except OSError as e:
        errors.append(f"Rapor yazma hatasi: {e}")

    if errors:
        report["errors"] = errors

    return report


def print_summary(report: dict) -> None:
    """Print a human-readable summary."""
    s = report["summary"]
    print(f"\n{'='*50}")
    print(f"ILK GOREV RAPORU")
    print(f"{'='*50}")
    print(f"Taranan dosya: {s['files_scanned']}")
    print(f"Eslesen dosya: {s['files_matched']}")
    print(f"Toplam eslesme: {s['total_matches']}")
    print(f"\nKelime dagilimi:")
    for kw, count in s["keyword_breakdown"].items():
        print(f"  {kw}: {count}")
    print(f"\nEn cok eslesen dosyalar:")
    for r in report["top_results"][:10]:
        print(f"  {r['matches']}x {r['file']}")


if __name__ == "__main__":
    report = scan()
    print_summary(report)
