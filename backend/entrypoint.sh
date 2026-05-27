#!/bin/sh
set -e

echo "[entrypoint] Running seed…"
python seed_admin.py

echo "[entrypoint] Starting server…"
if [ "$FLASK_ENV" = "development" ]; then
  exec python app.py
else
  exec gunicorn app:app \
    --bind "0.0.0.0:${PORT:-5000}" \
    --workers 2 \
    --timeout 120 \
    --access-logfile -
fi
