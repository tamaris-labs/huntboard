# Image de l'application Huntboard.
# Contexte de construction : racine du dépôt (voir docker-compose.yml).
FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/tamaris-labs/huntboard" \
      org.opencontainers.image.description="Huntboard: job-search board with daily scored watch, pipeline and AI assistant" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HUNTBOARD_DATA_DIR=/data

WORKDIR /app/backend
COPY app/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/backend/huntboard ./huntboard
COPY app/frontend /app/frontend
# Une seule page partagée avec le kit Claude, et la configuration d'exemple
COPY kit/skills/huntboard/template/huntboard.html /app/frontend/huntboard.html
COPY kit/skills/huntboard/config.example.json /app/frontend/config.example.json
COPY kit/skills/huntboard/assets/basemap.json /app/frontend/basemap.json

RUN useradd --create-home --uid 1000 huntboard && mkdir -p /data && chown huntboard /data
USER huntboard
VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=60s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')" || exit 1

CMD ["uvicorn", "huntboard.main:app", "--host", "0.0.0.0", "--port", "8000"]
