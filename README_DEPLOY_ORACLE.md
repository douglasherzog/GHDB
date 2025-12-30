# Deploy na Oracle Cloud Free Tier (VM + Docker)

## Visao geral

Este guia sobe a aplicacao (FastAPI) em uma VM Always Free usando Docker.

A aplicacao exige login e senha. Voce cria o primeiro usuario admin via variaveis de ambiente.

O codigo da aplicacao fica na pasta `ghdb_app/`.

## 1) Criar VM Always Free

- Crie uma instancia Linux (Ubuntu recomendado)
- Abra portas no Security List / NSG:
  - TCP 22 (SSH)
  - TCP 80 (HTTP) (recomendado)
  - TCP 443 (HTTPS) (quando voce tiver dominio)
  - Evite expor TCP 8000 diretamente (use reverse proxy)

## 2) Instalar Docker na VM

Siga o guia oficial do Docker para Ubuntu.

## 3) Subir o container

No seu PC (ou na VM, apos clonar o repo), faca build:

```bash
docker build -t ghdb-app:latest .
```

Crie uma pasta na VM para persistir o banco (SQLite):

```bash
mkdir -p /opt/ghdb/data
```

Rode definindo credenciais iniciais, uma secret key fixa e modo producao:

```bash
docker run -d --name ghdb \
  -p 8000:8000 \
  -v /opt/ghdb/data:/app/ghdb_app/data \
  -e GHDB_ENV="production" \
  -e GHDB_SECRET_KEY="coloque-uma-chave-longa-aqui" \
  -e GHDB_ADMIN_USERNAME="admin" \
  -e GHDB_ADMIN_PASSWORD="mude-essa-senha" \
  -e GHDB_SESSION_TTL_SECONDS="604800" \
  -e GHDB_COOKIE_SECURE="true" \
  ghdb-app:latest
```

Abra no browser:

- `http://IP_DA_VM:8000/login`

## 4) Colocar na porta 80 (recomendado)

Opcao A: Rodar o container na porta 80

```bash
docker run -d --name ghdb \
  -p 80:8000 \
  -v /opt/ghdb/data:/app/ghdb_app/data \
  -e GHDB_ENV="production" \
  -e GHDB_SECRET_KEY="coloque-uma-chave-longa-aqui" \
  -e GHDB_ADMIN_USERNAME="admin" \
  -e GHDB_ADMIN_PASSWORD="mude-essa-senha" \
  -e GHDB_SESSION_TTL_SECONDS="604800" \
  -e GHDB_COOKIE_SECURE="true" \
  ghdb-app:latest
```

Opcao B: Nginx como reverse proxy (porta 80/443), e container na 8000.

## 5) Operacao com docker compose (recomendado)

Se voce preferir nao rodar comandos longos de `docker run`, use o `docker-compose.yml` do repo.

Crie um arquivo `.env` na VM (na mesma pasta do `docker-compose.yml`) com as variaveis:

```bash
GHDB_SECRET_KEY=coloque-uma-chave-longa-aqui
GHDB_ADMIN_PASSWORD=mude-essa-senha
GHDB_ADMIN_USERNAME=admin
GHDB_SESSION_TTL_SECONDS=604800
GHDB_COOKIE_SECURE=false
```

Suba:

```bash
docker compose up -d --build
```

Observacao (sem dominio/HTTPS):

- Enquanto estiver usando apenas HTTP, mantenha `GHDB_COOKIE_SECURE=false`.
- Quando voce tiver um dominio e ativar HTTPS, troque para `GHDB_COOKIE_SECURE=true`.

## 5.1) Reverse proxy HTTP (Plano A, sem dominio)

O `docker-compose.yml` sobe o app em uma rede interna e expõe apenas a porta 80 via Caddy.

Abra no browser:

- `http://IP_DA_VM/login`

## 6) Backup e restore do SQLite

Backup (gera um arquivo em `backups/` dentro do volume):

```bash
bash ops/backup_db.sh
```

Restore (use o caminho do arquivo que deseja restaurar):

```bash
bash ops/restore_db.sh /opt/ghdb/data/backups/app_YYYYMMDD_HHMMSS.db
```

## Notas

- A indexacao inicial e feita no primeiro start e pode demorar um pouco.
- Para reindexar, use o botao "Reindexar" na UI.
- Para producao, use `GHDB_ENV=production` e uma `GHDB_SECRET_KEY` fixa e forte.
- O banco fica em `GHDB_DB_PATH` (default: `/app/ghdb_app/data/app.db`). O exemplo acima monta volume para persistir.
