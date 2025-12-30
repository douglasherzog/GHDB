#!/usr/bin/env bash
set -euo pipefail

USER_NAME="admin"
NEW_PASS="${1:-}"

if [ -z "$NEW_PASS" ]; then
  echo "usage: ops/reset_admin_password.sh <NEW_PASSWORD>" >&2
  exit 2
fi

python_script=$(cat <<'PY'
import os
import sqlite3
from passlib.context import CryptContext

user = os.environ.get("GHDB_RESET_USER") or "admin"
new_pass = os.environ.get("GHDB_RESET_PASSWORD")
if not new_pass:
    raise SystemExit("GHDB_RESET_PASSWORD not set")

pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
con = sqlite3.connect("/app/ghdb_app/data/app.db")
cur = con.execute(
    "UPDATE users SET password_hash=? WHERE username=?",
    (pwd.hash(new_pass), user),
)
con.commit()
print("OK: rows updated =", cur.rowcount)
PY
)

echo "Resetting password for user '$USER_NAME' in container 'ghdb'..."

echo "$python_script" | GHDB_RESET_USER="$USER_NAME" GHDB_RESET_PASSWORD="$NEW_PASS" docker exec -i ghdb python -
