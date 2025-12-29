FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ghdb_app /app/ghdb_app
COPY google-dork /app/google-dork
COPY lists /app/lists
COPY tools/lists /app/tools/lists

EXPOSE 8000

ENV GHDB_DB_PATH=/app/ghdb_app/data/app.db

CMD ["python", "-m", "uvicorn", "ghdb_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
