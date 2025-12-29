from __future__ import annotations

import json
import os
import secrets
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, URLSafeSerializer
from passlib.context import CryptContext

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = Path(os.getenv("GHDB_DB_PATH", str(DATA_DIR / "app.db")))

SECRET_KEY = os.getenv("GHDB_SECRET_KEY") or secrets.token_urlsafe(32)
COOKIE_NAME = "ghdb_session"
serializer = URLSafeSerializer(SECRET_KEY, salt="ghdb_session_v1")

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@dataclass(frozen=True)
class SearchHit:
    source: str
    origin: str
    key: str
    text: str


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    con = _connect()
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL UNIQUE,
              password_hash TEXT NOT NULL,
              is_admin INTEGER NOT NULL DEFAULT 0,
              is_active INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )

        cols = {r["name"] for r in con.execute("PRAGMA table_info(users)").fetchall()}
        if "is_admin" not in cols:
            con.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
        if "is_active" not in cols:
            con.execute("ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")

        con.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS dorks_fts USING fts5(
              source,
              origin,
              key,
              text,
              tokenize='unicode61'
            )
            """
        )
        con.commit()
    finally:
        con.close()


def ensure_admin_from_env() -> None:
    username = os.getenv("GHDB_ADMIN_USERNAME")
    password = os.getenv("GHDB_ADMIN_PASSWORD")
    if not username or not password:
        return

    con = _connect()
    try:
        row = con.execute("SELECT id, is_admin, is_active FROM users WHERE username=?", (username,)).fetchone()
        if row:
            con.execute(
                "UPDATE users SET is_admin=1, is_active=1 WHERE id=?",
                (int(row["id"]),),
            )
            con.commit()
            return
        con.execute(
            "INSERT INTO users (username, password_hash, is_admin, is_active) VALUES (?, ?, 1, 1)",
            (username, pwd_context.hash(password)),
        )
        con.commit()
    finally:
        con.close()


def _iter_text_lines(p: Path) -> Iterable[str]:
    try:
        content = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    for raw in content.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        yield line


def rebuild_index() -> None:
    repo_root = BASE_DIR.parent

    sources: list[tuple[str, Path]] = [
        ("google-dork", repo_root / "google-dork"),
        ("lists", repo_root / "lists"),
    ]

    con = _connect()
    try:
        con.execute("DELETE FROM dorks_fts")

        for source_name, folder in sources:
            if not folder.exists():
                continue

            for p in folder.rglob("*"):
                if not p.is_file():
                    continue
                if p.suffix.lower() not in {".txt", ".dorks", ""}:
                    continue

                origin = str(p.relative_to(repo_root))
                idx = 0
                for line in _iter_text_lines(p):
                    idx += 1
                    con.execute(
                        "INSERT INTO dorks_fts (source, origin, key, text) VALUES (?, ?, ?, ?)",
                        (source_name, origin, str(idx), line),
                    )

        dorks_json = repo_root / "tools" / "lists" / "dorks.json"
        if dorks_json.exists():
            data = json.loads(dorks_json.read_text(encoding="utf-8", errors="ignore"))
            for k, v in data.items():
                con.execute(
                    "INSERT INTO dorks_fts (source, origin, key, text) VALUES (?, ?, ?, ?)",
                    ("dorks.json", str(dorks_json.relative_to(repo_root)), str(k), str(v)),
                )

        con.commit()
    finally:
        con.close()


def _get_session_user_id(request: Request) -> Optional[int]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        data = serializer.loads(token)
    except BadSignature:
        return None
    uid = data.get("uid") if isinstance(data, dict) else None
    return int(uid) if uid is not None else None


def require_user_id(request: Request) -> int:
    uid = _get_session_user_id(request)
    if uid is None:
        raise HTTPException(status_code=401)
    return uid


def require_user(request: Request) -> sqlite3.Row:
    uid = require_user_id(request)
    con = _connect()
    try:
        row = con.execute(
            "SELECT id, username, is_admin, is_active FROM users WHERE id=?",
            (uid,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=401)
        if int(row["is_active"]) != 1:
            raise HTTPException(status_code=401)
        return row
    finally:
        con.close()


def require_admin(user: sqlite3.Row = Depends(require_user)) -> sqlite3.Row:
    if int(user["is_admin"]) != 1:
        raise HTTPException(status_code=403)
    return user


@app.on_event("startup")
def _startup() -> None:
    init_db()
    ensure_admin_from_env()

    con = _connect()
    try:
        row = con.execute("SELECT COUNT(1) AS c FROM dorks_fts").fetchone()
        if not row or int(row["c"]) == 0:
            rebuild_index()
    finally:
        con.close()


@app.exception_handler(HTTPException)
def _http_exc_handler(request: Request, exc: HTTPException):
    if exc.status_code != 401:
        raise exc
    return RedirectResponse(url="/login", status_code=303)


@app.get("/", response_class=HTMLResponse)
def home(request: Request, user=Depends(require_user)):
    return templates.TemplateResponse(
        "search.html",
        {"request": request, "user": user, "q": "", "source": "", "hits": []},
    )


@app.get("/help", response_class=HTMLResponse)
def help_page(request: Request, user=Depends(require_user)):
    return templates.TemplateResponse(
        "help.html",
        {"request": request, "user": user},
    )


@app.get("/help/wizard", response_class=HTMLResponse)
def help_wizard_page(request: Request, user=Depends(require_user)):
    return templates.TemplateResponse(
        "help_wizard.html",
        {"request": request, "user": user},
    )


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if _get_session_user_id(request) is not None:
        return RedirectResponse(url="/", status_code=303)

    error = request.query_params.get("error")
    return templates.TemplateResponse("login.html", {"request": request, "error": error})


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    con = _connect()
    try:
        row = con.execute(
            "SELECT id, username, password_hash, is_active FROM users WHERE username=?",
            (username,),
        ).fetchone()

        if not row:
            return RedirectResponse(url="/login?error=Usu%C3%A1rio%20ou%20senha%20inv%C3%A1lidos.", status_code=303)
        if int(row["is_active"]) != 1:
            return RedirectResponse(url="/login?error=Usu%C3%A1rio%20desativado.%20Fale%20com%20o%20administrador.", status_code=303)
        if not pwd_context.verify(password, row["password_hash"]):
            return RedirectResponse(url="/login?error=Usu%C3%A1rio%20ou%20senha%20inv%C3%A1lidos.", status_code=303)

        resp = RedirectResponse(url="/", status_code=303)
        resp.set_cookie(
            COOKIE_NAME,
            serializer.dumps({"uid": int(row["id"])}),
            httponly=True,
            samesite="lax",
        )
        return resp
    finally:
        con.close()


@app.post("/logout")
def logout():
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie(COOKIE_NAME)
    return resp


@app.get("/search", response_class=HTMLResponse)
def search(request: Request, q: str = "", source: str = "", user=Depends(require_user)):
    q_norm = (q or "").strip()
    source_norm = (source or "").strip()

    hits: list[SearchHit] = []
    if q_norm:
        con = _connect()
        try:
            if source_norm:
                rows = con.execute(
                    """
                    SELECT source, origin, key, text
                    FROM dorks_fts
                    WHERE dorks_fts MATCH ? AND source = ?
                    LIMIT 200
                    """,
                    (q_norm, source_norm),
                ).fetchall()
            else:
                rows = con.execute(
                    """
                    SELECT source, origin, key, text
                    FROM dorks_fts
                    WHERE dorks_fts MATCH ?
                    LIMIT 200
                    """,
                    (q_norm,),
                ).fetchall()

            hits = [SearchHit(r["source"], r["origin"], r["key"], r["text"]) for r in rows]
        finally:
            con.close()

    return templates.TemplateResponse(
        "search.html",
        {"request": request, "user": user, "q": q, "source": source, "hits": hits},
    )


@app.post("/admin/reindex")
def admin_reindex(user=Depends(require_user)):
    rebuild_index()
    return RedirectResponse(url="/", status_code=303)


@app.get("/admin/users", response_class=HTMLResponse)
def admin_users(request: Request, admin=Depends(require_admin)):
    msg = request.query_params.get("msg")
    con = _connect()
    try:
        users = con.execute(
            "SELECT id, username, is_admin, is_active, created_at FROM users ORDER BY id ASC"
        ).fetchall()
    finally:
        con.close()

    return templates.TemplateResponse(
        "admin_users.html",
        {"request": request, "user": admin, "users": users, "msg": msg},
    )


@app.post("/admin/users/create")
def admin_users_create(
    username: str = Form(...),
    password: str = Form(...),
    is_admin: Optional[str] = Form(None),
    admin=Depends(require_admin),
):
    username_norm = (username or "").strip()
    if not username_norm:
        return RedirectResponse(url="/admin/users?msg=Usu%C3%A1rio%20n%C3%A3o%20pode%20ficar%20em%20branco.", status_code=303)

    con = _connect()
    try:
        exists = con.execute("SELECT id FROM users WHERE username=?", (username_norm,)).fetchone()
        if exists:
            return RedirectResponse(url="/admin/users?msg=Usu%C3%A1rio%20j%C3%A1%20existe.", status_code=303)

        con.execute(
            "INSERT INTO users (username, password_hash, is_admin, is_active) VALUES (?, ?, ?, 1)",
            (username_norm, pwd_context.hash(password), 1 if is_admin else 0),
        )
        con.commit()
    finally:
        con.close()

    return RedirectResponse(url="/admin/users?msg=Usu%C3%A1rio%20criado%20com%20sucesso.", status_code=303)


@app.post("/admin/users/{user_id}/toggle")
def admin_users_toggle(user_id: int, admin=Depends(require_admin)):
    con = _connect()
    try:
        row = con.execute(
            "SELECT id, is_active, is_admin FROM users WHERE id=?",
            (int(user_id),),
        ).fetchone()
        if not row:
            return RedirectResponse(url="/admin/users?msg=Usu%C3%A1rio%20n%C3%A3o%20encontrado.", status_code=303)

        if int(row["id"]) == int(admin["id"]):
            return RedirectResponse(url="/admin/users?msg=Voc%C3%AA%20n%C3%A3o%20pode%20desativar%20seu%20pr%C3%B3prio%20usu%C3%A1rio.", status_code=303)

        new_active = 0 if int(row["is_active"]) == 1 else 1
        con.execute("UPDATE users SET is_active=? WHERE id=?", (new_active, int(user_id)))
        con.commit()
    finally:
        con.close()

    return RedirectResponse(url="/admin/users?msg=Status%20do%20usu%C3%A1rio%20atualizado.", status_code=303)


@app.post("/admin/users/{user_id}/reset")
def admin_users_reset_password(user_id: int, new_password: str = Form(...), admin=Depends(require_admin)):
    con = _connect()
    try:
        row = con.execute("SELECT id FROM users WHERE id=?", (int(user_id),)).fetchone()
        if not row:
            return RedirectResponse(url="/admin/users?msg=Usu%C3%A1rio%20n%C3%A3o%20encontrado.", status_code=303)
        con.execute(
            "UPDATE users SET password_hash=? WHERE id=?",
            (pwd_context.hash(new_password), int(user_id)),
        )
        con.commit()
    finally:
        con.close()

    return RedirectResponse(url="/admin/users?msg=Senha%20resetada%20com%20sucesso.", status_code=303)


@app.get("/dorks/open")
def open_dork(template: str, value: str = "", user=Depends(require_user)):
    t = (template or "").strip()
    v = (value or "").strip()

    if "{}" in t:
        url = t.format(v)
    elif t.startswith("http://") or t.startswith("https://"):
        url = t
    else:
        import urllib.parse

        q = t.replace("{domain}", v).replace("{term}", v)
        url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(q)

    return RedirectResponse(url=url, status_code=302)
