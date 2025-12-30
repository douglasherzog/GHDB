@echo off
setlocal EnableExtensions

set "USER=admin"

if "%~1"=="" (
  echo Uso: scripts\reset-admin-password.cmd NOVA_SENHA
  echo Ex:  scripts\reset-admin-password.cmd MinhaSenhaForte123@
  exit /b 2
)

set "NEWPASS=%~1"
echo Resetando senha do usuario "%USER%" no container "ghdb"...
echo.

REM Usa Python dentro do container para gerar hash e atualizar o SQLite.
echo import sqlite3> %TEMP%\ghdb_reset_admin_pw.py
echo from passlib.context import CryptContext>> %TEMP%\ghdb_reset_admin_pw.py
echo pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")>> %TEMP%\ghdb_reset_admin_pw.py
echo con = sqlite3.connect("/app/ghdb_app/data/app.db")>> %TEMP%\ghdb_reset_admin_pw.py
echo cur = con.execute("UPDATE users SET password_hash=? WHERE username=?", (pwd.hash(r"%NEWPASS%"), r"%USER%"))>> %TEMP%\ghdb_reset_admin_pw.py
echo con.commit()>> %TEMP%\ghdb_reset_admin_pw.py
echo print("OK: rows updated =", cur.rowcount)>> %TEMP%\ghdb_reset_admin_pw.py

type %TEMP%\ghdb_reset_admin_pw.py | docker exec -i ghdb python -
set "RC=%ERRORLEVEL%"
del /f /q %TEMP%\ghdb_reset_admin_pw.py >nul 2>&1

exit /b %RC%
