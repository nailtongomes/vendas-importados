#!/usr/bin/env bash
# check_integrity.sh — Run PRAGMA integrity_check on the SQLite database.
# Exits with 0 if OK, non-zero otherwise.
# Usage: ./scripts/check_integrity.sh [DB_PATH]
set -euo pipefail

DB_PATH="${1:-/app/data/app.db}"

if [ ! -f "$DB_PATH" ]; then
  echo "ERROR: Database not found at $DB_PATH" >&2
  exit 1
fi

RESULT=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;")

if [ "$RESULT" = "ok" ]; then
  echo "Integrity check passed."
  exit 0
else
  echo "INTEGRITY CHECK FAILED:" >&2
  echo "$RESULT" >&2
  exit 1
fi
