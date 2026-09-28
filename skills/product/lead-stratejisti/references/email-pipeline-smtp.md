# E-posta Pipeline — Gmail SMTP Implementasyonu (19.06.2026)

## Architecture Overview

```
index.html (frontend)
  → fetch POST /api/configure-email  (Gmail app password setup)
  → fetch POST /api/send-email/{id}  (single lead)
  → fetch POST /api/send-bulk        (batch with filters)
       ↓
main.py (FastAPI backend)
  → emailer.py module
       ↓
smtplib + Gmail SMTP (smtp.gmail.com:587)
  → STARTTLS + App Password auth
       ↓
Lead'in Gmail hesabına HTML e-posta
```

## File Locations

| File | Path | Purpose |
|------|------|---------|
| emailer.py | `/home/hermes/ergeneai-dashboard/emailer.py` | SMTP motoru: send, bulk, config, HTML build |
| main.py | `/home/hermes/ergeneai-dashboard/main.py` | FastAPI endpoints for email operations |
| index.html | `/home/hermes/ergeneai-dashboard/index.html` | Email config modal, send buttons, status bar |
| leads.json | `/home/hermes/ergeneai-dashboard/leads.json` | Lead data with `emails[]` tracking array |

## emailer.py — Key Functions

### `get_smtp_config()`
Reads from `~/.hermes/.env`:
- `GMAIL_EMAIL=ergenebilal@gmail.com`
- `GMAIL_APP_PASSWORD=<16-char-app-password>`

### `save_smtp_config(email, password)`
Writes to `~/.hermes/.env` with `chmod 0o600`.
Handles idempotent updates (replaces existing lines).

### `send_email(to_email, subject, body_html, body_text)`
Core SMTP send function:
1. Creates `MIMEMultipart("alternative")` with both HTML and plain text
2. Connects to `smtp.gmail.com:587` via `smtplib.SMTP`
3. STARTTLS with `ssl.create_default_context()`
4. `server.login(config["email"], config["password"])`
5. `server.sendmail(config["email"], to_email, msg.as_string())`
6. Returns `{"ok": True, "to": email, "subject": subject}` or error dict

Error handling:
- `SMTPAuthenticationError` → uygulama şifresi hatalı
- `SMTPRecipientsRefused` → alıcı adresi geçersiz
- Generic Exception → str(e)

### `build_email_html(lead, message)`
Generates:
- **Subject line** based on needs analysis:
  - "website" need → "Dijital Varlık Önerisi: [işletme]"
  - "seo" need → "Google'da Görünürlük Analizi: [işletme]"
  - default → "Dijital Çözüm Önerisi: [işletme]"
- **HTML body**: yeşil ErgeneAI branded template
  - Header: #198754 green bg, ErgeneAI logo/text
  - Body: personalized message paragraphs
  - Footer: company info

### `send_lead_email(lead, test_mode)`
- Requires `lead["email"]` field (skips if missing)
- If test_mode: returns preview only (no actual send)
- On success: appends to `lead["emails"]` array, sets status to "contacted"
- Returns result dict

### `send_bulk_emails(niches, max_count, test_mode)`
1. Filters leads by niche (optional)
2. Skips leads without email
3. Skips leads with existing `emails[]` array (no double-send)
4. Respects `max_count` cap
5. 1.5 second sleep between sends (Gmail rate limit)
6. Saves leads.json after batch completion
7. Returns `{total, sent, failed, errors[], by_niche{}}`

## API Endpoints

### POST /api/configure-email
```python
body = {"password": "xxxxxxxxxxxxxxxx"}
# email defaults to ergenebilal@gmail.com
# Saves to .env + sends test email to self
```

### POST /api/send-email/{lead_id}
```python
# No body needed — uses stored lead data
# Returns {"ok": True, "to": "...", "subject": "..."}
```

### POST /api/send-bulk
```python
body = {
    "test": true,        # Preview mode (no actual send)
    "max": 0,            # Max leads to send (0 = all)
    "niches": ["guzellik"]  # Optional niche filter
}
```

### GET /api/email-config-status
```python
# Returns {"configured": bool, "email": "...", "hint": "..."}
```

## Dashboard UI — Email Components

### Email Status Bar (Top of Page)
Shows green "✅ E-posta aktif: ergenebilal@gmail.com" or yellow "⚠️ Ayarlanmamış" with config link.

### Navbar Email Dropdown
```
📧 ▼
├── ⚙️ E-posta Ayarla
├── ─────────
├── 👁️ Test Önizleme
├── 📨 Tümüne Gönder
├── ─────────
├── 💅 Güzellik'e Gönder
├── ⚖️ Avukat'a Gönder
└── 🍽️ Restoran'a Gönder
```

### Email Config Modal
- Input field for 16-char app password (hidden type)
- Info box with link to google.com/apppasswords
- "Kaydet ve Test Et" button — sends test email to self
- Success/error message display

### Detail Panel Send Button
"E-posta Gönder" button next to "Kopyala" and "Sil"
- Confirmation dialog shows lead name and email (or warning if no email)
- On success: shows alert with recipient + subject
- On fail: shows error message

## JavaScript Functions

### `checkEmailStatus()`
Called on DOMContentLoaded + after config. Updates status bar.

### `openEmailConfig()`
Opens the config modal, clears previous state.

### `saveEmailConfig()`
Posts password to /api/configure-email. Shows spinner during test.

### `sendSingleEmail()`
Posts to /api/send-email/{currentLeadId}. Confirmation dialog first.

### `sendBulkTest()`
Posts test=true to /api/send-bulk. Shows stats: total/sent/failed.

### `sendBulkAll()`
Double confirmation, then posts to /api/send-bulk with no filters.

### `sendBulkNiche(niche)`
Single confirmation, then posts to /api/send-bulk with niches filter.

## Pitfalls Encountered

1. **Process management:** Old uvicorn process lingers after kill on the same port. Use `kill -9` + `lsof -i :8082` to verify port is free before restarting.

2. **email field in leads.json:** Google Places API doesn't return email addresses. Most leads will NOT have an email field. The system handles this gracefully (skips those leads silently during bulk send).

3. **Gmail daily limit:** 500 emails/day for free Gmail. With 32 leads, we're well within limit. But if scanning adds 50+ leads/day, need to be strategic about batch size.

4. **Background process lifecycle:** When starting uvicorn as a background task, need to ensure old process is fully dead first. `kill` alone may not suffice — use `kill -9`.

5. **Duplicate DOMContentLoaded handlers:** If multiple handlers are registered (original init + email check), they both fire. Merged into one handler for clarity.

## Batch Campaign Script (email-campaign.py)

A CLI tool at `/home/hermes/ergeneai-dashboard/email-campaign.py` for niche-filtered batch sends. See SKILL.md "Batch Campaign Script" section for full docs.

### Quick Reference

```bash
# Dry-run first
cd /home/hermes/ergeneai-dashboard
python3 email-campaign.py --niche avukat --dry-run

# Then send
python3 email-campaign.py --niche avukat --send
```

### Dependencies
- `emailer.py` — uses `get_smtp_config()` + `send_email()` from this module
- `marketing-content/{niche}.json` — requires `landing_page.body` to be populated
- `leads.json` — reads leads with email field
