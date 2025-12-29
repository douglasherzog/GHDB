#!/usr/bin/env bash
set -euo pipefail

backup_file="${1:-}"
if [ -z "$backup_file" ]; then
  echo "usage: ops/restore_db.sh /opt/ghdb/data/backups/app_YYYYMMDD_HHMMSS.db" >&2
  exit 2
fi

if [ ! -f "$backup_file" ]; then
  echo "backup not found: $backup_file" >&2
  exit 2
fi

docker compose stop ghdb
cp -f "$backup_file" /opt/ghdb/data/app.db
docker compose up -d ghdb
