set -e

echo ">>> Rebuilding backend with new code..."
docker compose up --build -d backend

echo ">>> Waiting for backend to be ready..."
sleep 5

echo ">>> Running admin seed inside container..."
docker exec uniform_backend python seed_admin.py

echo ""
echo "Done! Try logging in:"
echo "  Admin:   admin@school.edu / Admin@1234"
echo ""
echo "Note: any student accounts created before this fix will need to re-register."
