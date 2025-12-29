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
  - TCP 443 (HTTPS) (opcional)
  - ou TCP 8000 (se voce quiser expor direto, nao recomendado)

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

## Notas

- A indexacao inicial e feita no primeiro start e pode demorar um pouco.
- Para reindexar, use o botao "Reindexar" na UI.
- Para producao, use `GHDB_ENV=production` e uma `GHDB_SECRET_KEY` fixa e forte.
- O banco fica em `GHDB_DB_PATH` (default: `/app/ghdb_app/data/app.db`). O exemplo acima monta volume para persistir.
