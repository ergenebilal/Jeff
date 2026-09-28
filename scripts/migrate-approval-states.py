#!/usr/bin/env python3
"""
migrate-approval-states.py — One-time migration for approval-queue.md schema to v1.4.

Reads /opt/hermes/trend-watcher/approval-queue.md (and companion files
outcome-ledger.md, jeff-feedback.md) and upgrades entries that are missing
v1.4 schema fields.

Usage:
    python3 migrate-approval-states.py            # live run
    python3 migrate-approval-states.py --dry-run   # preview only
"""

import argparse
import hashlib
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, "/opt/hermes/trend-watcher")
from lock_utils import file_lock

# ── paths ──────────────────────────────────────────────────────────────────
APPROVAL_QUEUE = "/opt/hermes/trend-watcher/approval-queue.md"
OUTCOME_LEDGER = "/opt/hermes/trend-watcher/outcome-ledger.md"
JEFF_FEEDBACK = "/opt/hermes/trend-watcher/jeff-feedback.md"

# ── helpers ────────────────────────────────────────────────────────────────


def md5_of(text: str) -> str:
    """Return hex md5 digest of the given text."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _deadline_iso() -> str:
    """The digest-timestamp threshold for pending_notified promotion."""
    return "2026-07-01 18:00"


def _parse_timestamp(ts_str: str) -> datetime | None:
    """Attempt to parse a timestamp in YYYY-MM-DD HH:MM format."""
    ts_str = ts_str.strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    return None


def _today_iso() -> str:
    """Return today's date as YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


# ── YAML-like block parser ─────────────────────────────────────────────────


def parse_blocks(text: str, entry_prefix: str) -> list[dict]:
    """Parse YAML-like blocks from text.

    Each block starts with a line matching `entry_prefix` (e.g.
    ``  - id:`` or ``- id:``).  Key-value lines inside the block are
    recognised by leading whitespace + ``key: value``.

    Returns list of dicts ``{"raw": str, "fields": dict, "start": int, "end": int}``.
    """
    lines = text.splitlines(keepends=True)
    blocks: list[dict] = []
    current_block = None
    current_fields: dict[str, str] = {}

    for i, line in enumerate(lines):
        if re.match(entry_prefix, line):
            # flush previous block
            if current_block is not None:
                current_block["end"] = i
                current_block["fields"] = current_fields
                blocks.append(current_block)
            current_block = {"raw": "", "fields": {}, "start": i, "end": i}
            current_fields = {}
            current_block["raw"] += line
            # parse the id on the starter line
            m = re.match(r".*\- id:\s*(\S+)", line)
            if m:
                current_fields["id"] = m.group(1).strip("\"'")
        elif current_block is not None:
            current_block["raw"] += line
            # parse key: value pair (indented)
            m = re.match(r"^(\s+)([\w-]+):\s*(.*)", line)
            if m:
                key = m.group(2)
                val = m.group(3).rstrip()
                current_fields[key] = val

    # flush last block
    if current_block is not None:
        current_block["end"] = len(lines)
        current_block["fields"] = current_fields
        blocks.append(current_block)

    return blocks


def rebuild_entry_lines(block: dict, missing_fields: list[str],
                        computed_values: dict[str, str]) -> list[str]:
    """Return new lines for a single entry block.

    ``missing_fields`` are inserted as ``  <key>: <value>`` right before the
    last field line of the block.  ``computed_values`` supplies the value for
    each key; blank = empty string.
    """
    lines = block["raw"].splitlines(keepends=True)
    if not missing_fields:
        return lines

    # Find the last field line index within this block
    last_field_idx = -1
    for i, line in enumerate(lines):
        if re.match(r"^\s+[\w-]+:", line):
            last_field_idx = i

    if last_field_idx < 0:
        # No field lines at all — append after first line
        last_field_idx = 0

    indent_match = re.match(r"^(\s+)", lines[last_field_idx])
    indent = indent_match.group(1) if indent_match else "  "

    new_lines = []
    for i, line in enumerate(lines):
        new_lines.append(line)
        if i == last_field_idx:
            for key in missing_fields:
                val = computed_values.get(key, "")
                new_lines.append(f"{indent}{key}: {val}\n")

    return new_lines


# ── approval-queue specific logic ──────────────────────────────────────────


REQUIRED_APPROVAL_FIELDS = [
    "fingerprint",
    "son_bildirim",
    "son_kullanici_aksiyonu",
    "otomatik_erteleme_tarihi",
]


def migrate_approval_queue(dry_run: bool) -> tuple[int, int]:
    """Migrate approval-queue.md. Returns (records_changed, total_changes)."""
    today = _today_iso()
    deadline_str = _deadline_iso()

    with open(APPROVAL_QUEUE, "r", encoding="utf-8") as f:
        text = f.read()

    # Detect if already migrated (comment present)
    already_migrated = "<!-- migrated to v1.4 schema" in text

    blocks = parse_blocks(text, r"^\s+-\s+id:")
    total_changes = 0
    records_changed = 0

    new_text = text
    raw_lines = text.splitlines(keepends=True)

    # Process each block from bottom to top so line offsets stay valid
    for block in reversed(blocks):
        fields = block["fields"]
        baslik = fields.get("baslik", "")
        changes_for_entry = 0

        missing = []
        computed = {}

        for fld in REQUIRED_APPROVAL_FIELDS:
            if fld not in fields:
                missing.append(fld)
                if fld == "fingerprint" and baslik:
                    computed[fld] = md5_of(baslik)
                else:
                    computed[fld] = ""
                changes_for_entry += 1

        # Durum transition: "bekliyor" and before deadline → "pending_notified"
        durum = fields.get("durum", "").strip()
        olusturulma = fields.get("olusturulma", "").strip()
        if durum == "bekliyor":
            ts = _parse_timestamp(olusturulma)
            deadline_ts = _parse_timestamp(deadline_str)
            if ts is not None and deadline_ts is not None and ts < deadline_ts:
                # This requires a field-value edit within the block
                changes_for_entry += 1

        if changes_for_entry == 0:
            continue

        records_changed += 1
        total_changes += changes_for_entry

        # Build new lines for this block
        new_lines = rebuild_entry_lines(block, missing, computed)

        # Apply durum change inline
        if durum == "bekliyor":
            ts = _parse_timestamp(olusturulma)
            deadline_ts = _parse_timestamp(deadline_str)
            if ts is not None and deadline_ts is not None and ts < deadline_ts:
                for i, line in enumerate(new_lines):
                    if re.match(r"^\s+durum:\s+bekliyor", line):
                        new_lines[i] = re.sub(
                            r"\bdurum:\s+bekliyor", "durum: pending_notified", line
                        )
                        break

        # Replace in full text (slice approach)
        start_line = block["start"]
        end_line = block["end"]
        # Compute byte offsets
        raw_offset_start = sum(len(l) for l in raw_lines[:start_line])
        raw_offset_end = sum(len(l) for l in raw_lines[:end_line])

        old_block_text = text[raw_offset_start:raw_offset_end]
        new_block_text = "".join(new_lines)

        if dry_run:
            print(
                f"  [{fields.get('id','?')}] {baslik or '(no baslik)'}: "
                f"{changes_for_entry} change(s)"
            )
            if missing:
                print(f"       + missing fields: {missing}")
            if durum == "bekliyor":
                ts = _parse_timestamp(olusturulma)
                deadline_ts = _parse_timestamp(deadline_str)
                if ts is not None and deadline_ts is not None and ts < deadline_ts:
                    print(f"       + durum: bekliyor → pending_notified")
        else:
            text = text[:raw_offset_start] + new_block_text + text[raw_offset_end:]

    # Add migration comment at the top if not present
    comment = f"<!-- migrated to v1.4 schema on {today} -->\n"
    if not already_migrated:
        if dry_run:
            print(f"  [TOP] Add migration comment: {comment.strip()}")
            total_changes += 1
        else:
            # Insert after the first line (heading) or at the very top
            first_newline = text.find("\n")
            if first_newline >= 0 and text.startswith("#"):
                text = text[:first_newline+1] + comment + text[first_newline+1:]
            else:
                text = comment + text
            total_changes += 1
        if records_changed == 0:
            records_changed = 1  # the comment itself is a change

    if not dry_run:
        with file_lock(APPROVAL_QUEUE, timeout=15):
            with open(APPROVAL_QUEUE, "w", encoding="utf-8") as f:
                f.write(text)

    return records_changed, total_changes


# ── simple-fingerprint migration for outcome-ledger & jeff-feedback ────────


def migrate_fingerprints(filepath: str, dry_run: bool) -> tuple[int, int]:
    """Add missing ``fingerprint:`` field to every entry in a file."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    blocks = parse_blocks(text, r"^\s*-\s+id:")
    total_changes = 0
    records_changed = 0

    for block in reversed(blocks):
        fields = block["fields"]
        baslik = fields.get("baslik", "")
        if "fingerprint" in fields:
            continue

        records_changed += 1
        total_changes += 1
        val = md5_of(baslik) if baslik else ""
        if dry_run:
            print(
                f"  [{fields.get('id','?')}] {baslik or '(no baslik)'}: "
                f"+ fingerprint: {val or '(blank)'}"
            )
            continue

        new_lines = rebuild_entry_lines(block, ["fingerprint"],
                                        {"fingerprint": val})
        raw_lines = text.splitlines(keepends=True)
        start_offset = sum(len(l) for l in raw_lines[:block["start"]])
        end_offset = sum(len(l) for l in raw_lines[:block["end"]])
        text = text[:start_offset] + "".join(new_lines) + text[end_offset:]

    if not dry_run:
        with file_lock(filepath, timeout=15):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)

    return records_changed, total_changes


# ── main ───────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Migrate approval-queue and related files to v1.4 schema."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing any files.",
    )
    args = parser.parse_args()

    mode = "DRY RUN" if args.dry_run else "LIVE"
    print(f"=== {mode} — migration starting ===")
    print()

    # 1) approval-queue.md
    print("--- approval-queue.md ---")
    aq_rec, aq_chg = migrate_approval_queue(args.dry_run)
    print(f"  -> {aq_rec} kayit guncellendi, {aq_chg} degisiklik yapildi")
    print()

    # 2) outcome-ledger.md
    print("--- outcome-ledger.md ---")
    ol_rec, ol_chg = migrate_fingerprints(OUTCOME_LEDGER, args.dry_run)
    print(f"  -> {ol_rec} kayit guncellendi, {ol_chg} degisiklik yapildi")
    print()

    # 3) jeff-feedback.md
    print("--- jeff-feedback.md ---")
    jf_rec, jf_chg = migrate_fingerprints(JEFF_FEEDBACK, args.dry_run)
    print(f"  -> {jf_rec} kayit guncellendi, {jf_chg} degisiklik yapildi")
    print()

    total_rec = aq_rec + ol_rec + jf_rec
    total_chg = aq_chg + ol_chg + jf_chg
    if args.dry_run:
        print(f"=== DRY RUN complete: {total_rec} kayit guncellenecek, "
              f"{total_chg} degisiklik yapilacak ===")
    else:
        print(f"=== MIGRATION COMPLETE: {total_rec} kayit guncellendi, "
              f"{total_chg} degisiklik yapildi ===")


if __name__ == "__main__":
    main()
