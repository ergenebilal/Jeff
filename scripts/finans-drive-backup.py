#!/usr/bin/env python3.11
"""Finans App → Google Drive yedekleme (her güncelleme sonrası)

data.json dosyasını "ErgeneAI Finans" Drive klasörüne yükler.
Version'lu isimle kaydeder, son 20 versiyonu tutar.

Çağrı: python3.11 finans-drive-backup.py <data_json_yolu>
"""
import json, os, sys, time
from pathlib import Path
from datetime import datetime, timezone

HOME = Path.home()
LOG = HOME / ".hermes" / "logs" / "finans-drive-backup.log"
DRIVE_FOLDER = "ErgeneAI Finans"
MAX_VERSIONS = 20

NOW = datetime.now(timezone.utc)
TS = NOW.strftime("%Y%m%d_%H%M%S")

def log(msg):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(f"[{NOW.isoformat()}] {msg}\n")

def google_drive_upload(file_path: Path) -> bool:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        token_path = HOME / ".google-workspace-mcp" / "tokens.json"
        creds_path = HOME / ".google-workspace-mcp" / "credentials.json"

        if not token_path.exists() or not creds_path.exists():
            log("Token/credentials bulunamadi")
            return False

        token_data = json.loads(token_path.read_text())
        # MCP formatı → SDK formatı dönüşümü
        if "token" in token_data and "access_token" not in token_data:
            token_data["access_token"] = token_data["token"]
            # Expiry zamanını kontrol et
            if "expiry" in token_data:
                from datetime import datetime
                expiry = token_data["expiry"]
                if isinstance(expiry, str):
                    token_data["expiry"] = expiry
            token_path.write_text(json.dumps(token_data, indent=2))
        creds_data = json.loads(creds_path.read_text())

        if "refresh_token" in token_data:
            creds = Credentials.from_authorized_user_info(token_data)
        else:
            log("Refresh token yok")
            return False

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.write_text(creds.to_json())

        service = build("drive", "v3", credentials=creds)

        # "ErgeneAI Finans" klasörünü bul/oluştur
        resp = service.files().list(
            q=f"name='{DRIVE_FOLDER}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces="drive", fields="files(id, name)"
        ).execute()

        folders = resp.get("files", [])
        if folders:
            folder_id = folders[0]["id"]
        else:
            folder = service.files().create(
                body={"name": DRIVE_FOLDER, "mimeType": "application/vnd.google-apps.folder"},
                fields="id"
            ).execute()
            folder_id = folder.get("id")

        # Dosyayı yükle — version'lu isim
        filename = f"data-{TS}.json"
        media = MediaFileUpload(str(file_path), mimetype="application/json", resumable=True)
        uploaded = service.files().create(
            body={"name": filename, "parents": [folder_id]},
            media_body=media,
            fields="id, name"
        ).execute()

        log(f"Drive'a yuklendi: {filename} (ID: {uploaded.get('id')})")
        print(f"✅ Finans yedek: {filename}")

        # Eski versiyonları temizle (son 20'yi tut)
        all_files = service.files().list(
            q=f"'{folder_id}' in parents and name starts with 'data-' and trashed=false",
            spaces="drive", fields="files(id, name, createdTime)",
            orderBy="createdTime desc"
        ).execute().get("files", [])

        if len(all_files) > MAX_VERSIONS:
            for old in all_files[MAX_VERSIONS:]:
                service.files().delete(fileId=old["id"]).execute()
                log(f"Eski versiyon silindi: {old['name']}")

        return True

    except Exception as e:
        log(f"Drive yukleme hatasi: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanim: finans-drive-backup.py <data_json_yolu>")
        sys.exit(1)

    data_path = Path(sys.argv[1])
    if not data_path.exists():
        print(f"Dosya bulunamadi: {data_path}")
        sys.exit(1)

    log("=== Finans yedek basliyor ===")
    success = google_drive_upload(data_path)
    if success:
        print("✅ Finans verisi Drive'a yedeklendi")
    else:
        print("❌ Drive yedekleme basarisiz")
        sys.exit(1)
