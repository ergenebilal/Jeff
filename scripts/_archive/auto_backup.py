#!/usr/bin/env python3
"""
Git Auto-Backup — Jeff reposunu otomatik commit + push.
Quality PASS sonrası veya gün sonunda çalışır.

Kullanım:
  python3 auto_backup.py                   # Tüm değişiklikleri commit + push
  python3 auto_backup.py --message "fix"   # Özel commit mesajı
  python3 auto_backup.py --check-only      # Sadece değişiklik var mı kontrol et

Sessiz çalışır (değişiklik yoksa output vermez).
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_PATH = Path.home() / "jeff-backup-repo"
BRANCH = "main"
TZ = "+03:00"


def run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command in the repo directory."""
    return subprocess.run(
        ["git"] + args,
        cwd=REPO_PATH,
        capture_output=True,
        text=True,
        timeout=30,
        check=check,
    )


def has_changes() -> bool:
    """Check if there are any uncommitted changes."""
    result = run_git(["status", "--porcelain"], check=False)
    return bool(result.stdout.strip())


def get_change_summary() -> str:
    """Get a summary of what changed."""
    result = run_git(["diff", "--stat"], check=False)
    return result.stdout.strip()[:500]


def auto_backup(custom_message: str | None = None, dry_run: bool = False) -> str:
    """Auto-commit and push if there are changes."""
    if not REPO_PATH.exists():
        return f"❌ Repo bulunamadı: {REPO_PATH}"

    # Check for changes
    result = run_git(["status", "--porcelain"], check=False)
    changed_files = result.stdout.strip()

    if not changed_files:
        return ""  # Silent — nothing to commit

    if dry_run:
        lines = changed_files.split("\n")
        count = len([l for l in lines if l.strip()])
        return f"📦 {count} dosyada değişiklik (dry-run, commit yapılmadı)"

    # Stage all
    run_git(["add", "-A"])

    # Count changes
    change_count = len([l for l in changed_files.split("\n") if l.strip()])

    # Build commit message
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    if custom_message:
        message = f"[{now}] {custom_message}"
    else:
        # Auto-generate from changed files
        files = [l[3:].strip() for l in changed_files.split("\n") if l.strip()]

        # Categorize
        dirs = set()
        for f in files:
            parts = f.split("/")
            if len(parts) > 1:
                dirs.add(parts[0])
            else:
                dirs.add(f)

        dir_summary = ", ".join(sorted(dirs)[:5])
        if len(dirs) > 5:
            dir_summary += f" +{len(dirs)-5} more"

        message = f"[{now}] auto-backup: {change_count} files ({dir_summary})"

    # Commit
    commit = run_git(["commit", "-m", message], check=False)
    if commit.returncode != 0:
        return f"⚠️ Commit başarısız: {commit.stderr.strip()[:200]}"

    # Push
    push = run_git(["push", "origin", BRANCH], check=False)
    if push.returncode != 0:
        return (
            f"✅ Commit yapıldı ama push başarısız: {push.stderr.strip()[:200]}"
        )

    return f"✅ {change_count} dosya commit'lendi + push'landı: _{message}_"


def main() -> None:
    parser = argparse.ArgumentParser(description="Git Auto-Backup for Jeff repo")
    parser.add_argument("--message", "-m", help="Custom commit message")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Sadece değişiklik var mı kontrol et",
    )
    args = parser.parse_args()

    result = auto_backup(
        custom_message=args.message, dry_run=args.check_only
    )
    if result:
        print(result)


if __name__ == "__main__":
    main()
