FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Label fix: 2026-05-31 — all 145 GECS codes now correct, no Single Segment
COPY . .

EXPOSE 7860

CMD ["python", "app.py"]
