FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y git git-lfs && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN git lfs install 2>/dev/null || true && git lfs pull 2>/dev/null || echo "LFS pull skipped - models will load as offline"

EXPOSE 8080

CMD ["sh", "-lc", "gunicorn server:app --bind 0.0.0.0:${PORT:-8080} --workers 1 --timeout 120 --preload"]
