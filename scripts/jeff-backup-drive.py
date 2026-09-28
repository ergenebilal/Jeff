#!/usr/bin/env python3.11
"""Jeff → Google Drive Backup — gerçek Drive yedekleme

Ne yedekler:
- ~/.hermes/config.yaml
- ~/.hermes/.env (API key'ler)
- ~/.hermes/skills/ (tüm skill'ler)
- ~/.hermes/scripts/ (sadece cron'da kullanılanlar)
- ~/.hermes/manga_trajectory.json
- ~/.hermes/kanban.db
- /opt/hermes/brain/
- /home/hermes/hermes_data/hermes_tools/

Çalışma: no_agent cron script'i. Sadece sorun olursa çıktı verir.
"""

import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
HERMES = HOME / ".hermes"
SCRIPTS = HERMES / "scripts"
LOG = HERMES / "logs" / "drive-backup.log"
STATE_FILE = HERMES / "data" / "drive-backup-state.json"
BACKUP_DIR = HOME / "backups"
MAX_BACKUPS = 5

NOW = datetime.now(timezone.utc)
TS = NOW.strftime("%Y%m%d_%H%M%S")


def log(msg: str) -> None:
    with open(LOG, "a") as f:
        f.write(f"[{NOW.isoformat()}] {msg}\n")


def google_drive_upload(file_path: Path, mime_type: str = "application/gzip") -> bool:
    """Google Drive'a dosya yükler. Mevcut token'ları kullanır."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        token_path = HOME / ".google-workspace-mcp" / "tokens.json"
        creds_path = HOME / ".google-workspace-mcp" / "credentials.json"

        if not token_path.exists() or not creds_path.exists():
            log("Token veya credentials bulunamadi")
            return False

        token_data = json.loads(token_path.read_text())
        # MCP formatı → SDK formatı dönüşümü
        if "token" in token_data and "access_token" not in token_data:
            token_data["access_token"] = token_data["token"]
            token_path.write_text(json.dumps(token_data, indent=2))
        creds_data = json.loads(creds_path.read_text())

        # Refresh token varsa kullan
        if "refresh_token" in token_data:
            creds = Credentials.from_authorized_user_info(token_data)
        else:
            log("Refresh token yok — Drive'a yukleme yapilamaz")
            return False

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Guncel token'i kaydet
            token_path.write_text(creds.to_json())

        service = build("drive", "v3", credentials=creds)

        # "Jeff Backups" klasorunu bul veya olustur
        folder_name = "Jeff Backups"
        response = service.files().list(
            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces="drive",
            fields="files(id, name)",
        ).execute()

        folders = response.get("files", [])
        if folders:
            folder_id = folders[0]["id"]
        else:
            folder_meta = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            folder = service.files().create(body=folder_meta, fields="id").execute()
            folder_id = folder.get("id")

        # Dosyayi yukle
        file_metadata = {
            "name": file_path.name,
            "parents": [folder_id],
        }
        media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)
        uploaded = service.files().create(
            body=file_metadata, media_body=media, fields="id, name, webViewLink"
        ).execute()

        log(f"Drive'a yuklendi: {uploaded.get('name')} (ID: {uploaded.get('id')})")
        print(f"✅ Drive: {uploaded.get('name')}")
        return True

    except Exception as e:
        log(f"Drive yukleme hatasi: {e}")
        print(f"❌ Drive yukleme basarisiz: {e}")
        return False


def create_backup() -> Path | None:
    """Yedek tarball'i olusturur."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = BACKUP_DIR / f"jeff-backup-{TS}.tar.gz"

    try:
        with tarfile.open(archive_path, "w:gz") as tar:
            # Config
            if (HERMES / "config.yaml").exists():
                tar.add(HERMES / "config.yaml", arcname="config.yaml")
            if (HERMES / ".env").exists():
                tar.add(HERMES / ".env", arcname="env")

            # Skills
            if (HERMES / "skills").exists():
                tar.add(HERMES / "skills", arcname="skills")

            # Brain
            brain = Path("/opt/hermes/brain")
            if brain.exists():
                tar.add(brain, arcname="brain")

            # Custom tools
            tools = HOME / "hermes_data" / "hermes_tools"
            for f in ["_manga.py", "_kanban.py"]:
                p = tools / f
                if p.exists():
                    tar.add(p, arcname=f"tools/{f}")

            # State files
            for f in ["manga_trajectory.json", "kanban.db"]:
                p = HERMES / f
                if p.exists():
                    tar.add(p, arcname=f"state/{f}")

            # Active scripts
            active_scripts = [
                "probation_reminder.py", "vacuum_dbs.py", "n8n-mcp-watchdog.sh",
                "backup-to-drive.py", "hermes-update-watchdog.sh", "daily_ig.py",
                "jeff-watchdog.sh", "jeff-guardian.py", "closed_loop-kpi-cron.sh",
                "closed_loop-revenue-cron.sh", "kanban_zombie_check.py",
                "self-improvement-pulse.py", "jeff-backup-github.sh",
            ]
            for s in active_scripts:
                p = SCRIPTS / s
                if p.exists():
                    tar.add(p, arcname=f"scripts/{s}")

            # Version info
            info = f"""Backup: {TS}
Host: {os.uname().nodename}
Hermes: {subprocess.run(["hermes", "--version"], capture_output=True, text=True, timeout=5).stdout.strip() or "N/A"}
Commit: {subprocess.run(["git", "-C", "/opt/hermes", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5).stdout.strip()[:12] or "N/A"}
Skills: {len(list((HERMES / "skills").glob("*/SKILL.md"))) if (HERMES / "skills").exists() else 0}
"""
            info_path = BACKUP_DIR / f"info-{TS}.txt"
            info_path.write_text(info)
            tar.add(info_path, arcname="backup-info.txt")
            info_path.unlink()

        size_mb = archive_path.stat().st_size / 1024 / 1024
        log(f"Yedek olusturuldu: {archive_path.name} ({size_mb:.1f} MB)")
        return archive_path

    except Exception as e:
        log(f"Yedek olusturma hatasi: {e}")
        return None


def cleanup_old_backups(max_keep: int = MAX_BACKUPS):
    """Eski yedekleri temizle, son max_keep kadarini tut."""
    backups = sorted(BACKUP_DIR.glob("jeff-backup-*.tar.gz"), reverse=True)
    for old in backups[max_keep:]:
        old.unlink()
        log(f"Eski yedek silindi: {old.name}")


if __name__ == "__main__":
    log("=== Yedek basliyor ===")

    # 1. Yedek olustur
    archive = create_backup()
    if not archive:
        print("❌ Yedek olusturulamadi")
        sys.exit(1)

    print(f"📦 Yedek: {archive.name} ({archive.stat().st_size / 1024 / 1024:.1f} MB)")

    # 2. Drive'a yukle
    success = google_drive_upload(archive)

    # 3. Eski yedekleri temizle
    cleanup_old_backups()

    # 4. State kaydet
    HERMES / "data"
    (HERMES / "data").mkdir(parents=True, exist_ok=True)
    state = {
        "son_backup": TS,
        "dosya": archive.name,
        "boyut_mb": round(archive.stat().st_size / 1024 / 1024, 1),
        "drive_yukleme": "basarili" if success else "basarisiz",
        "tarih": NOW.isoformat(),
    }
    Path(STATE_FILE).write_text(json.dumps(state, indent=2))

    if success:
        print("✅ Jeff → Google Drive yedekleme tamam!")
    else:
        print("⚠️  Yerel yedek alindi ama Drive yukleme basarisiz")
        sys.exit(1)
