#!/bin/bash
# reset.sh — wipes the database volume and restarts all containers fresh
# Run this whenever you change init.sql or need a clean slate.

set -e

echo ">>> Stopping and removing all containers..."
docker compose down -v

echo ">>> Rebuilding and starting fresh..."
docker compose up --build -d

echo ""
echo "Done. The database has been reset with the latest init.sql."
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:5000"
