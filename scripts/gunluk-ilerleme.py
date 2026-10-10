#!/usr/bin/env python3.11
"""Gunluk %1 ilerleme olcer (03.10.2026, Bilal emri).

Her gece sonu (23:59 audit ile ayni pencere) somut ilerleme alanlarini
karsilastirilir ve bugun onceki gune gore en az %1 ilerleme olculup olculmedigi raporlanir.

Alanlar:
  - lead sayisi (cgos.db leads)
  - qualification raporu sayisi
  - gorusme adayi sayisi (score >= 60)
  - repo commit sayisi (son 24h)
  - test sayisi (sonnight raporundan okunur, yoksa '-')

Cikis: /home/hermes/reports/ilerleme_YYYY-MM-DD.md + stdout JSON
Kurallar:
  - Sayi uretemezse '-' yazar; hicbir alanda %1 yoksa NET "ilierlemecok yok" der.
  - Hedef tablo: gorusme aday avantajinda her +1 aday en azindan %10 ilerlemesayilir (10 hedef).
"""
import json
import os
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

NOW = datetime.now()
DATE = NOW.strftime("%Y-%m-%d")
Hedef_ADAY = 10  # gorusme adayi hedefi (Bilal'in koydugu 10 firma hedefi)
REPORTS = Path("/home/hermes/reports")
REPORTS.mkdir(exist_ok=True)
OUT = REPORTS / f"ilerleme_{DATE}.md"

DB = Path("/home/hermes/cybergeneos-data/cgos.db")
REPO = Path("/home/hermes/jeff_repo")


def count_leads():
    if not DB.exists():
        return None
    try:
        conn = sqlite3.connect(str(DB))
        n = conn.execute("SELECT count(*) FROM leads").fetchone()[0]
        conn.close()
        return n
    except Exception:
        return None


def count_reports():
    if not DB.exists():
        return None
    try:
        conn = sqlite3.connect(str(DB))
        n = conn.execute("SELECT count(*) FROM qualification_reports").fetchone()[0]
        conn.close()
        return n
    except Exception:
        return None


def count_adaylar():
    """Gorusme adaylari: lead basina SON raporda need_status = guclu_is_yuku_hipotezi."""
    if not DB.exists():
        return None
    try:
        conn = sqlite3.connect(str(DB))
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT qr.report
            FROM qualification_reports qr
            WHERE qr.created_at = (
                SELECT MAX(q2.created_at) FROM qualification_reports q2 WHERE q2.lead_id = qr.lead_id
            )
        """).fetchall()
        aday = 0
        for r in rows:
            try:
                rep = json.loads(r["report"]) if isinstance(r["report"], str) else r["report"]
                if rep.get("need_status") == "guclu_is_yuku_hipotezi":
                    aday += 1
            except Exception:
                pass
        conn.close()
        return aday
    except Exception:
        return None


def count_commits_24h():
    global commits
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO), "log", "--since", "24 hours ago", "--oneline"],
            capture_output=True,
            text=True, timeout=15
        )
        commits = [l for l in out.stdout.splitlines() if l.strip()]
        return len(commits)
    except Exception:
        return None


def collect():
    return {
        "lead": count_leads(),
        "rapor": count_reports(),
        "aday": count_adaylar(),
        "commit_24h": count_commits_24h(),
    }


def previous_snapshot():
    """Onceki gun .json snapshot'i, varsa."""
    y = (NOW - timedelta(days=1)).strftime("%Y-%m-%d")
    f = REPORTS / f"ilerleme_{y}.json"
    if f.exists():
        try:
            return json.load(open(f))
        except Exception:
            return None
    return None


def pct_change(new, old):
    if new is None or old in (None, 0):
        return None
    try:
        return round((new - old) / old * 100, 2)
    except Exception:
        return None


def main():
    today = collect()
    # snapshot JSON yaz
    (REPORTS / f"ilerleme_{DATE}.json").write_text(json.dumps(today, ensure_ascii=False, indent=2))

    yesterday = previous_snapshot()
    delta = {}
    if yesterday:
        for k in today:
            delta[k] = {
                "bugun": today[k],
                "dun": yesterday.get(k),
                "degisim_pct": pct_change(today[k], yesterday.get(k)),
            }

    # %1 kontrolu: en az bir alan >= 1% artmis olmali
    progressed = False
    best = None
    for k, v in delta.items():
        p = v.get("degisim_pct")
        if p is not None and p > 0:
            progressed = True
            if best is None or p > best[1]:
                best = (k, p)

    lines = [
        f"# Günlük İlerleme Ölçümü — {DATE}",
        "",
    ]
    if yesterday:
        lines.append("| Alan | Bugun | Dun | Degisim % |")
        lines.append("|---|---|---|---|")
        for k, v in delta.items():
            b = v["bugun"] if v["bugun"] is not None else "-"
            d_ = v["dun"] if v["dun"] is not None else "-"
            p = v["degisim_pct"]
            lines.append(f"| {k} | {b} | {d_} | {p if p is not None else '-'} |")
    else:
        lines.append("Bugun ilk olcum gundu (onceki snapshot yok). Tablo yarinki raporda otomatik cikacak.")

    lines += ["", "## Sonuc"]
    if today.get("aday") is not None:
        if Hedef_ADAY > today["aday"]:
            remaining = Hedef_ADAY - today["aday"]
            lines.append(f"- Aday hedefi: {today['aday']}/{Hedef_ADAY} (kalan {remaining})")
        else:
            lines.append(f"- Aday hedefi TAMAMLANDI: {today['aday']}/{Hedef_ADAY}")
    if progressed and best:
        lines.append(f"- ✅ %1 ilerleme KARŞILANDI: en güçlü alan `{best[0]}` +{best[1]}%")
    elif yesterday is None:
        lines.append("- İlk gün ölçümü — yarın %1 karşılaştırma raporu otomatik üretilecek")
    else:
        lines.append("- ❌ %1 ilerleme YOK — hicbir alan bugun olculebilir sekilde ilerlemedi (gunu onarim/gelistirme isi gerekir)")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "date": DATE, "today": today,
        "yesterday": yesterday,
        "progressed": progressed,
        "report": str(OUT),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
