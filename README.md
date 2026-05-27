# Uniform Gallery

## First-time setup
```bash
docker compose up --build -d
```

## Applying database changes (init.sql updated)
The database only reads `init.sql` on first creation. To apply changes:
```bash
./reset.sh
```
Or manually:
```bash
docker compose down -v
docker compose up --build -d
```

## Adding / replacing uniform images
Images live in `backend/static/images/`. Drop files there and they are served immediately — no restart needed.

## URLs
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- Admin login: admin@school.edu / Admin@1234
