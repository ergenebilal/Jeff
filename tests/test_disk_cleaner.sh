#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(mktemp -d)"
trap 'rm -rf "$ROOT_DIR"' EXIT

mkdir -p "$ROOT_DIR/a"
printf 'log\n' > "$ROOT_DIR/a/test.log"
printf 'keep\n' > "$ROOT_DIR/a/keep.txt"

OUTPUT="$(DISK_CLEANER_ROOT="$ROOT_DIR" bash "$(dirname "$0")/../scripts/disk_cleaner.sh")"

printf '%s\n' "$OUTPUT" | grep -q 'DRY_RUN=1'
printf '%s\n' "$OUTPUT" | grep -q 'Candidates:1'
test -f "$ROOT_DIR/a/test.log"
test -f "$ROOT_DIR/a/keep.txt"

DRY_RUN=0 CONFIRM_DELETE=YES DISK_CLEANER_ROOT="$ROOT_DIR" bash "$(dirname "$0")/../scripts/disk_cleaner.sh" >/tmp/hermes_disk_cleaner_test.out
test ! -f "$ROOT_DIR/a/test.log"
test -f "$ROOT_DIR/a/keep.txt"
