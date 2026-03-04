#!/usr/bin/env bash
# backup_sqlite.sh — Safe SQLite backup using .backup command.
# Usage: ./scripts/backup_sqlite.sh [DB_PATH] [BACKUP_DIR]
#   DB_PATH    defaults to /app/data/app.db
#   BACKUP_DIR defaults to /app/data/backups
# Keeps the last 7 backups (retention).
set -euo pipefail

DB_PATH="${1:-/app/data/app.db}"
BACKUP_DIR="${2:-/app/data/backups}"

if [ ! -f "$DB_PATH" ]; then
  echo "ERROR: Database not found at $DB_PATH" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/app_${TIMESTAMP}.db"

sqlite3 "$DB_PATH" ".backup '${BACKUP_FILE}'"

echo "Backup created: ${BACKUP_FILE}"

# Retention: keep only the last 7 backups
cd "$BACKUP_DIR"
ls -1t app_*.db 2>/dev/null | tail -n +8 | xargs -r rm -f

echo "Retention applied (last 7 kept)."
