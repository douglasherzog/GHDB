#!/usr/bin/env bash
set -euo pipefail

timestamp="$(date +%Y%m%d_%H%M%S)"
backup_dir="/app/ghdb_app/data/backups"
backup_file="$backup_dir/app_${timestamp}.db"

docker exec ghdb python -c "import os, sqlite3; os.makedirs('${backup_dir}', exist_ok=True); src=sqlite3.connect('/app/ghdb_app/data/app.db'); dst=sqlite3.connect('${backup_file}'); src.backup(dst); dst.close(); src.close()"

echo "$backup_file"
