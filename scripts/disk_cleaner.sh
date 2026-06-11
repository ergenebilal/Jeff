#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-${DISK_CLEANER_ROOT:-$HOME}}"
DRY_RUN="${DRY_RUN:-1}"
TARGET_EXTENSIONS="${TARGET_EXTENSIONS:-log,tmp,cache,old}"
MAX_DEPTH="${MAX_DEPTH:-4}"

if [[ ! -d "$ROOT_DIR" ]]; then
  echo "Root directory not found: $ROOT_DIR" >&2
  exit 1
fi

IFS=',' read -r -a EXTENSIONS <<< "$TARGET_EXTENSIONS"
mapfile -t CANDIDATES < <(
  find "$ROOT_DIR" -maxdepth "$MAX_DEPTH" -type f -print 2>/dev/null |
    while IFS= read -r file; do
      for ext in "${EXTENSIONS[@]}"; do
        if [[ "$file" == *."$ext" ]]; then
          printf '%s\n' "$file"
          break
        fi
      done
    done |
    sort
)

echo "DRY_RUN=$DRY_RUN"
echo "ROOT_DIR=$ROOT_DIR"
echo "Candidates:${#CANDIDATES[@]}"

if [[ ${#CANDIDATES[@]} -eq 0 ]]; then
  echo "No candidates found."
  exit 0
fi

for file in "${CANDIDATES[@]}"; do
  printf '%s\n' "$file"
done

if [[ "$DRY_RUN" != "0" ]]; then
  echo "Dry-run only. Set DRY_RUN=0 and confirm with CONFIRM_DELETE=YES to delete."
  exit 0
fi

if [[ "${CONFIRM_DELETE:-}" != "YES" ]]; then
  echo "Deletion skipped. Export CONFIRM_DELETE=YES to continue."
  exit 0
fi

for file in "${CANDIDATES[@]}"; do
  rm -f -- "$file"
done

echo "Deletion complete."
