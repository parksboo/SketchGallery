#!/usr/bin/env bash
set -euo pipefail

DB_PATH="${SKETCH_DB_PATH:-data/sketch_gallery.db}"

if [[ ! -f "${DB_PATH}" ]]; then
  echo "[database] db file not found: ${DB_PATH}"
  exit 1
fi

echo "[database] row counts"
sqlite3 "${DB_PATH}" "SELECT status, COUNT(*) FROM jobs GROUP BY status ORDER BY status;"
