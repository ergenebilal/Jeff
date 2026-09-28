#!/usr/bin/env python3
"""
Jeff Approval Queue — Command Handler
======================================
Reads commands from stdin (one per line) and processes them.

Commands (via stdin — one per line):
    approve <id>    — mark item as onaylandi + create outcome-ledger entry
    reject  <id>    — mark item as reddedildi + add to jeff-feedback
    snooze  <id>    — mark item as ertelendi + append to watch-list

Usage:
    echo "approve abc123" | python3 approval-command-handler.py
    python3 approval-command-handler.py --dry-run approve abc123

Files under /opt/hermes/trend-watcher/:
    approval-queue.md       — main queue (read + update durum)
    outcome-ledger.md       — approved items
    jeff-feedback.md        — rejected items
    watch-list.md           — snoozed items
    processed-commands.md   — Telegram update_id idempotency log
"""

import re
import uuid
import datetime
import pathlib
import sys

# ── File locking ────────────────────────────────────────────────────────────
sys.path.insert(0, "/opt/hermes/trend-watcher")
from lock_utils import file_lock

# ── Constants ──────────────────────────────────────────────────────────────
TREND_DIR = pathlib.Path("/opt/hermes/trend-watcher")

QUEUE_FILE            = TREND_DIR / "approval-queue.md"
OUTCOME_FILE          = TREND_DIR / "outcome-ledger.md"
FEEDBACK_FILE         = TREND_DIR / "jeff-feedback.md"
WATCH_FILE            = TREND_DIR / "watch-list.md"
PROCESSED_COMMANDS    = TREND_DIR / "processed-commands.md"

DRY_RUN = False
UPDATE_ID = None  # optional Telegram update_id for idempotency

# ── Terminal states (cannot be re-processed) ───────────────────────────────
TERMINAL_STATES = ("onaylandi", "reddedildi", "arsivlendi")

# ── Header templates ───────────────────────────────────────────────────────

QUEUE_HEADER = """# Jeff Onay Kuyruğu — Approval Queue

<!-- queue-description -->
Sıradaki MCP araç trendleri ve değerlendirmeler.
-->

<!-- queue-entries buraya eklenir -->
"""

OUTCOME_HEADER = """# Outcome Ledger — Kayıtlı Kazanımlar

<!-- outcome-description -->
Onaylanan araçların dağıtım ve etki takibi.
-->

<!-- outcome-entries buraya eklenir -->
"""

FEEDBACK_HEADER = """# Jeff Feedback — Geri Bildirim Günlüğü

<!-- feedback-description -->
Reddedilen veya pas geçilen sinyallerin nedenleri.
-->

<!-- feedback-entries buraya eklenir -->
"""

WATCH_HEADER = """# Watch List — İzleme Listesi

<!-- watch-description -->
Ertelenen veya takip edilmesi gereken sinyaller.
-->

<!-- watch-entries buraya eklenir -->
"""


# ── Helpers ────────────────────────────────────────────────────────────────

def today_str() -> str:
    """YYYY-MM-DD"""
    return datetime.date.today().isoformat()


def now_str() -> str:
    """YYYY-MM-DD HH:MM"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def ensure_dir():
    """Create TREND_DIR if it doesn't exist."""
    TREND_DIR.mkdir(parents=True, exist_ok=True)


def ensure_file(file: pathlib.Path, header: str):
    """Create file with header if it doesn't exist."""
    if not file.exists():
        if not DRY_RUN:
            file.write_text(header.lstrip("\n"))
        sys.stderr.write(f"[{'DRY-RUN' if DRY_RUN else 'INFO'}] Created {file}\n")


def parse_queue_item(block: str) -> dict | None:
    """
    Parse a single markdown list item block from approval-queue into a dict.
    Expected format (relaxed — lines can be contiguous or multi-line):

    - id: <uuid>
      baslik: "..."
      kategori: mcp
      kaynak: trend-report|github-gems
      sinyal: ★★★★★
      jeff_guveni: yuksek
      zaman_maliyeti: 1-3 saat
      ozet_tek_satir: "..."
      durum: bekliyor|onaylandi|reddedildi|ertelendi
      olusturulma: YYYY-MM-DD HH:MM
    """
    lines = block.strip().splitlines()
    if not lines:
        return None

    item = {}
    # Check that the block starts with a list item
    first = lines[0].strip()
    if not first.startswith("- id:"):
        return None

    for line in lines:
        line_stripped = line.strip()
        # Skip empty / bullet-only lines
        if not line_stripped:
            continue

        # Remove leading "- " if present (start of list item)
        if line_stripped.startswith("- "):
            line_stripped = line_stripped[2:]

        match = re.match(r"^(\w[\w_]*)\s*:(.*)", line_stripped)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip().strip('"')
            item[key] = value

    # Normalise keys — yaml-style 'olusturulma' might arrive as 'olusturulma'
    if "olusturulma" not in item and "olusturulma" in item:
        item["olusturulma"] = item.pop("olusturulma")

    return item


def find_item_in_queue(item_id: str) -> tuple[str, str, int] | None:
    """
    Search approval-queue.md for item with given ID.

    Returns (full_block, durum, line_offset_of_block_start) or None.
    We do a simple scan — find the line "- id: <item_id>", then collect
    subsequent indented lines as the block.
    """
    if not QUEUE_FILE.exists():
        return None

    text = QUEUE_FILE.read_text()
    lines = text.splitlines(keepends=True)

    for i, line in enumerate(lines):
        stripped = line.strip()
        # Look for "- id: <item_id>"
        id_match = re.match(r"^- id:\s*(\S+)", stripped)
        if id_match and id_match.group(1) == item_id:
            # Collect the block starting at i
            block_lines = [lines[i].rstrip("\n")]
            j = i + 1
            while j < len(lines):
                next_stripped = lines[j].strip()
                # A new list item at same level breaks the block
                if next_stripped.startswith("- ") and not next_stripped.startswith("- id:"):
                    # Could be a sub-item like "- id: ..." is the only opener;
                    # otherwise a top-level "- something" breaks.
                    # For safety, check if it's a dashed field (continuation style)
                    # Actually in our format, fields are indented after "- id:"
                    # so a line at column 0 starting with "- " is a new item.
                    if not lines[j].startswith(" ") and not lines[j].startswith("\t"):
                        break
                if not next_stripped:
                    j += 1
                    continue
                if re.match(r"^\s*\w[\w_]*\s*:", next_stripped):
                    block_lines.append(lines[j].rstrip("\n"))
                    j += 1
                else:
                    # Non-field line — could be continuation or block end
                    # Our format has all fields on separate indented lines.
                    # If the line is not a field line and is not indented, stop.
                    if not lines[j].startswith(" ") and not lines[j].startswith("\t"):
                        break
                    # Indented but not a known field — treat as continuation of previous value? No, our format has simple key: value lines.
                    # Break to be safe.
                    break
            else:
                # j reached end without breaking — that's fine
                pass

            block = "\n".join(block_lines)
            item = parse_queue_item(block)
            durum = item.get("durum", "") if item else ""
            return (block, durum, i)

    return None


def update_queue_item(item_id: str, new_durum: str) -> tuple[bool, str]:
    """
    Update the durum field of an item in approval-queue.md.
    Returns (success, message).
    """
    if not QUEUE_FILE.exists():
        return (False, f"HATA: {QUEUE_FILE} bulunamadi")

    with file_lock(QUEUE_FILE):
        text = QUEUE_FILE.read_text()
        lines = text.splitlines(keepends=True)

        # Find the line "- id: <item_id>"
        found_idx = -1
        for i, line in enumerate(lines):
            stripped = line.strip()
            id_match = re.match(r"^- id:\s*(\S+)", stripped)
            if id_match and id_match.group(1) == item_id:
                found_idx = i
                break

        if found_idx == -1:
            return (False, f"HATA: '{item_id}' approval-queue'da bulunamadi")

        # Now find the "durum:" line within the item's block
        updated = False
        for j in range(found_idx, len(lines)):
            stripped = lines[j].strip()
            if re.match(r"^- id:", stripped) and j != found_idx:
                # Reached a new item — stop
                break
            if re.match(r"durum\s*:", stripped):
                old_line = lines[j]
                # Preserve exact indentation
                indent = old_line[:len(old_line) - len(old_line.lstrip())]
                lines[j] = f"{indent}durum: {new_durum}\n"
                updated = True
                break

        if not updated:
            return (False, f"HATA: '{item_id}' icin durum alani bulunamadi")

        new_text = "".join(lines)
        if not DRY_RUN:
            QUEUE_FILE.write_text(new_text)
    return (True, f"✅ {item_id} → durum: {new_durum}")


def update_queue_item_field(item_id: str, field: str, value: str) -> tuple[bool, str]:
    """
    Update (or add) a specific field in an item block in approval-queue.md.
    Returns (success, message).
    """
    if not QUEUE_FILE.exists():
        return (False, f"HATA: {QUEUE_FILE} bulunamadi")

    with file_lock(QUEUE_FILE):
        text = QUEUE_FILE.read_text()
        lines = text.splitlines(keepends=True)

        # Find the line "- id: <item_id>"
        found_idx = -1
        for i, line in enumerate(lines):
            stripped = line.strip()
            id_match = re.match(r"^- id:\s*(\S+)", stripped)
            if id_match and id_match.group(1) == item_id:
                found_idx = i
                break

        if found_idx == -1:
            return (False, f"HATA: '{item_id}' approval-queue'da bulunamadi")

        # Find the block end
        block_end = len(lines)
        for j in range(found_idx + 1, len(lines)):
            stripped = lines[j].strip()
            if stripped.startswith("- ") and re.match(r"^- id:", stripped) is None:
                if not lines[j].startswith(" ") and not lines[j].startswith("\t"):
                    block_end = j
                    break
            # Stop at a new top-level "- id:" item
            if re.match(r"^- id:", stripped):
                block_end = j
                break
            # Empty line followed by a non-field line at column 0
            if not stripped:
                # Look ahead for a non-indented, non-field line
                k = j + 1
                while k < len(lines) and not lines[k].strip():
                    k += 1
                if k < len(lines) and not lines[k].startswith(" ") and not lines[k].startswith("\t"):
                    block_end = j
                    break

        # Try to find existing field line
        field_found = False
        for j in range(found_idx, block_end):
            stripped = lines[j].strip()
            # Remove leading "- " if present
            if stripped.startswith("- "):
                stripped_check = stripped[2:]
            else:
                stripped_check = stripped
            if re.match(rf"^{field}\s*:", stripped_check):
                old_line = lines[j]
                indent = old_line[:len(old_line) - len(old_line.lstrip())]
                lines[j] = f"{indent}{field}: {value}\n"
                field_found = True
                break

        if not field_found:
            # Add field after the last field line in the block (before block end)
            # Find the indentation of an existing field
            indent = "  "  # default 2-space indent
            for j in range(found_idx, block_end):
                if lines[j].strip() and not lines[j].strip().startswith("- id:"):
                    indent = lines[j][:len(lines[j]) - len(lines[j].lstrip())]
                    break
            new_line = f"{indent}{field}: {value}\n"
            lines.insert(block_end, new_line)

        new_text = "".join(lines)
        if not DRY_RUN:
            QUEUE_FILE.write_text(new_text)
    return (True, f"✅ {item_id} → {field}: {value}")


def parse_time_cost(raw: str) -> float:
    """Convert zaman_maliyeti string to float hours.

    "1-3 saat"  → 2.0
    "<1 saat"   → 0.5
    "3+ saat"   → 4.0
    "2 saat"    → 2.0
    default     → 2.0
    """
    raw = raw.strip().lower()
    # Pattern: "<1 saat" or "<1"
    if re.match(r"<\s*1", raw):
        return 0.5
    # Pattern: "3+ saat" or "3+"
    if re.match(r"3\s*\+", raw):
        return 4.0
    # Pattern: "1-3 saat" → 2.0
    range_match = re.search(r"(\d+)\s*-\s*(\d+)", raw)
    if range_match:
        a = float(range_match.group(1))
        b = float(range_match.group(2))
        return (a + b) / 2.0
    # Pattern: plain number, "2 saat" → 2.0
    num_match = re.search(r"(\d+\.?\d*)", raw)
    if num_match:
        return float(num_match.group(1))
    return 2.0


def get_item_field(item_block: str, field: str) -> str:
    """Extract a field value from an item block."""
    for line in item_block.splitlines():
        stripped = line.strip()
        if re.match(rf"^{field}\s*:", stripped):
            # Remove leading "- " if present
            if stripped.startswith("- "):
                stripped = stripped[2:]
            match = re.match(rf"^{field}\s*:\s*(.*)", stripped)
            if match:
                return match.group(1).strip().strip('"')
    return ""


def generate_uuid() -> str:
    """Generate a short-ish UUID (first 8 hex chars of uuid4)."""
    return uuid.uuid4().hex[:8]


def check_terminal_state(item_id: str, block: str, durum: str) -> bool:
    """
    Check if item is in a terminal state.
    If it is, print rejection message and return True.
    Returns False if item can be processed.
    """
    if durum in TERMINAL_STATES:
        print(f"⏭️  Bu madde zaten {durum} olarak islendi")
        return True
    return False


def is_command_processed(update_id: str) -> bool:
    """
    Check if a Telegram update_id has already been processed.
    Returns True if found in processed-commands.md.
    """
    if not update_id:
        return False
    if not PROCESSED_COMMANDS.exists():
        return False
    for line in PROCESSED_COMMANDS.read_text().splitlines():
        if line.strip() == update_id.strip():
            return True
    return False


def mark_command_processed(update_id: str):
    """Append an update_id to processed-commands.md."""
    if not update_id:
        return
    if DRY_RUN:
        return
    with file_lock(PROCESSED_COMMANDS):
        if not PROCESSED_COMMANDS.exists():
            PROCESSED_COMMANDS.write_text(f"# Processed Telegram update_ids\n\n{update_id}\n")
        else:
            with PROCESSED_COMMANDS.open("a") as f:
                f.write(f"{update_id}\n")


# ── Action handlers ────────────────────────────────────────────────────────

def cmd_approve(item_id: str):
    """Approve an item → update queue + create outcome-ledger entry."""
    result = find_item_in_queue(item_id)
    if result is None:
        print(f"❌ {item_id} bulunamadi")
        return

    block, durum, line_no = result

    # Terminal state check
    if check_terminal_state(item_id, block, durum):
        return

    if durum and durum not in ("bekliyor", "pending_notified"):
        print(f"⏭️  {item_id} zaten {durum}")
        return

    # Update queue — wrap with file_lock
    ok, msg = update_queue_item(item_id, "onaylandi")
    if not ok:
        print(msg)
        return
    print(msg)

    # Update son_kullanici_aksiyonu and son_bildirim fields
    now = now_str()
    update_queue_item_field(item_id, "son_kullanici_aksiyonu", now)
    update_queue_item_field(item_id, "son_bildirim", now)

    # Gather fields from original block
    baslik      = get_item_field(block, "baslik")
    kategori    = get_item_field(block, "kategori") or "mcp"
    kaynak      = get_item_field(block, "kaynak") or "trend-report"
    raw_cost    = get_item_field(block, "zaman_maliyeti") or "2 saat"
    fingerprint = get_item_field(block, "fingerprint")
    cost_hours  = parse_time_cost(raw_cost)
    new_id      = generate_uuid()

    entry_lines = [
        f"- id: {new_id}",
        f"  tarih: {today_str()}",
        f"  baslik: \"{baslik}\"",
        f"  kategori: {kategori}",
        f"  kaynak: {kaynak}",
        f"  karar: kurulacak",
        f"  durum: testte",
        f"  zaman_maliyeti_saat: {cost_hours}",
        f"  teknik_risk: dusuk",
        f"  cikti_tipi: yeni_kabiliyet",
    ]
    if fingerprint:
        entry_lines.append(f"  fingerprint: {fingerprint}")
    entry_lines.extend([
        f"  net_etki: ",
        f"  not: \"Approval Queue'dan\"",
    ])

    outcome_entry = "\n".join(entry_lines) + "\n"

    # Append to outcome-ledger.md — with file locking
    if not DRY_RUN:
        with file_lock(OUTCOME_FILE):
            append_after_comment(OUTCOME_FILE, "outcome-entries", outcome_entry)
    print(f"📋 {item_id} → outcome-ledger.md eklendi (id: {new_id})")


def cmd_reject(item_id: str):
    """Reject an item → update queue + add to jeff-feedback."""
    result = find_item_in_queue(item_id)
    if result is None:
        print(f"❌ {item_id} bulunamadi")
        return

    block, durum, line_no = result

    # Terminal state check
    if check_terminal_state(item_id, block, durum):
        return

    if durum and durum not in ("bekliyor", "pending_notified"):
        print(f"⏭️  {item_id} zaten {durum}")
        return

    # Update queue — wrapped with file_lock inside update_queue_item
    ok, msg = update_queue_item(item_id, "reddedildi")
    if not ok:
        print(msg)
        return
    print(msg)

    # Update son_kullanici_aksiyonu and son_bildirim fields
    now = now_str()
    update_queue_item_field(item_id, "son_kullanici_aksiyonu", now)
    update_queue_item_field(item_id, "son_bildirim", now)

    # Gather fields
    baslik      = get_item_field(block, "baslik")
    kategori    = get_item_field(block, "kategori") or "mcp"
    fingerprint = get_item_field(block, "fingerprint")

    entry_lines = [
        f"- id: {item_id}",
        f"  tarih: {now_str()}",
        f"  kaynak: approval-queue",
        f"  baslik: \"{baslik}\"",
        f"  karar: pas",
        f"  skor: 0",
        f"  kategori: {kategori}",
    ]
    if fingerprint:
        entry_lines.append(f"  fingerprint: {fingerprint}")
    entry_lines.append(f"  not: \"Approval Queue'da reddedildi\"")

    feedback_entry = "\n".join(entry_lines) + "\n"

    if not DRY_RUN:
        with file_lock(FEEDBACK_FILE):
            append_after_comment(FEEDBACK_FILE, "feedback-entries", feedback_entry)
    print(f"📋 {item_id} → jeff-feedback.md eklendi")


def cmd_snooze(item_id: str):
    """Snooze an item → update queue + append to watch-list."""
    result = find_item_in_queue(item_id)
    if result is None:
        print(f"❌ {item_id} bulunamadi")
        return

    block, durum, line_no = result

    # Terminal state check
    if check_terminal_state(item_id, block, durum):
        return

    if durum and durum not in ("bekliyor", "pending_notified"):
        print(f"⏭️  {item_id} zaten {durum}")
        return

    # Update queue — wrapped with file_lock inside update_queue_item
    ok, msg = update_queue_item(item_id, "ertelendi")
    if not ok:
        print(msg)
        return
    print(msg)

    # Update son_kullanici_aksiyonu, son_bildirim, and otomatik_erteleme_tarihi
    now = now_str()
    # now + 48 hours for otomatik_erteleme_tarihi
    delay_iso = (datetime.datetime.now() + datetime.timedelta(hours=48)).strftime("%Y-%m-%d %H:%M")
    update_queue_item_field(item_id, "son_kullanici_aksiyonu", now)
    update_queue_item_field(item_id, "son_bildirim", now)
    update_queue_item_field(item_id, "otomatik_erteleme_tarihi", delay_iso)

    # Gather fields
    baslik   = get_item_field(block, "baslik")
    kategori = get_item_field(block, "kategori") or "mcp"

    watch_entry = (
        f"- id: {item_id}\n"
        f"  baslik: \"{baslik}\"\n"
        f"  kategori: {kategori}\n"
        f"  izleme_nedeni: \"Approval Queue'dan ertelendi\"\n"
        f"  ilk_eklenme: {today_str()}\n"
        f"  son_kontrol: {today_str()}\n"
        f"  tetik_kriteri: manuel_erteleme\n"
        f"  durum: acik\n"
    )

    if not DRY_RUN:
        with file_lock(WATCH_FILE):
            append_after_comment(WATCH_FILE, "watch-entries", watch_entry)
    print(f"🔔 {item_id} → watch-list.md eklendi")


# ── File helpers ───────────────────────────────────────────────────────────

def append_after_comment(file: pathlib.Path, comment_hint: str, entry: str):
    """
    Append `entry` right after the line containing `comment_hint` in `file`.
    If the file doesn't exist or the comment isn't found, append at the end
    (with a blank line separator).

    NOTE: This function expects the caller to handle file locking.
    """
    if not file.exists():
        # Create with appropriate header
        header_map = {
            OUTCOME_FILE: OUTCOME_HEADER,
            FEEDBACK_FILE: FEEDBACK_HEADER,
            WATCH_FILE: WATCH_HEADER,
        }
        header = header_map.get(file, "")
        # Write header + entry
        file.write_text(header.lstrip("\n") + "\n" + entry)
        return

    text = file.read_text()
    lines = text.splitlines(keepends=True)

    insert_idx = None
    for i, line in enumerate(lines):
        if comment_hint in line:
            insert_idx = i + 1  # insert after this line
            break

    if insert_idx is not None:
        # Insert the entry at insert_idx
        new_lines = lines[:insert_idx] + [entry] + lines[insert_idx:]
        file.write_text("".join(new_lines))
    else:
        # Comment marker not found — just append
        with file.open("a") as f:
            f.write("\n" + entry)


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    global DRY_RUN, UPDATE_ID

    # Parse arguments — check for --dry-run and --update-id
    args = sys.argv[1:]

    # Extract --update-id <value>
    if "--update-id" in args:
        idx = args.index("--update-id")
        if idx + 1 < len(args):
            UPDATE_ID = args[idx + 1]
            # Remove both --update-id and its value
            args = args[:idx] + args[idx + 2:]

    if "--dry-run" in args:
        DRY_RUN = True
        args.remove("--dry-run")

    # Ensure directories and files
    ensure_dir()
    ensure_file(QUEUE_FILE, QUEUE_HEADER)

    # Ensure processed-commands.md exists (idempotency log)
    if not PROCESSED_COMMANDS.exists():
        if not DRY_RUN:
            PROCESSED_COMMANDS.write_text("# Processed Telegram update_ids\n\n")
        sys.stderr.write(f"[{'DRY-RUN' if DRY_RUN else 'INFO'}] Created {PROCESSED_COMMANDS}\n")

    # Determine input sources
    commands = []

    if args:
        # Command-line args: e.g. "approve abc123"
        # Accept either "approve abc123" as positional or ["approve", "abc123"]
        if len(args) >= 2:
            cmd = args[0].lower()
            rest = args[1:]
            for item_id in rest:
                commands.append((cmd, item_id))
        elif len(args) == 1 and " " in args[0]:
            cmd, item_id = args[0].split(None, 1)
            commands.append((cmd.lower(), item_id))
    else:
        # Read from stdin (one command per line)
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) < 2:
                sys.stderr.write(f"UYARI: Gecersiz komut: {line!r}\n")
                continue
            cmd = parts[0].lower()
            item_id = parts[1]
            commands.append((cmd, item_id))

    if not commands:
        sys.stderr.write("Kullanim: echo \"approve <id>\" | python3 approval-command-handler.py\n")
        sys.stderr.write("Kullanim: python3 approval-command-handler.py --dry-run approve <test-id>\n")
        sys.exit(1)

    if DRY_RUN:
        sys.stderr.write("🧪 DRY-RUN MODE — hicbir dosya degistirilmeyecek\n\n")

    # Process each command
    for cmd, item_id in commands:
        cmd = cmd.lstrip("/")  # Allow /approve, /reject, /snooze

        # Idempotency check: if update_id is set, skip if already processed
        if UPDATE_ID and is_command_processed(UPDATE_ID):
            sys.stderr.write(f"[SKIP] update_id {UPDATE_ID} already processed\n")
            continue

        if cmd == "approve":
            cmd_approve(item_id)
        elif cmd == "reject":
            cmd_reject(item_id)
        elif cmd == "snooze":
            cmd_snooze(item_id)
        else:
            sys.stderr.write(f"UYARI: Bilinmeyen komut: {cmd!r} (approve|reject|snooze)\n")

        # Mark as processed after successful handling
        if UPDATE_ID:
            mark_command_processed(UPDATE_ID)


if __name__ == "__main__":
    main()
