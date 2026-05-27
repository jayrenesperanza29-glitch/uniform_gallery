"""
Runs once at startup to ensure the admin account exists with a correct
werkzeug PBKDF2-SHA256 hash.  Safe to run multiple times (idempotent upsert).
Also uploads the bundled static images to Cloudinary when configured,
so fresh Render deploys always have the seed images available.
"""
import os
import time
import glob

import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash

DATABASE_URL = os.getenv("DATABASE_URL",
    "postgresql://uniform_user:uniform_pass@db:5432/uniform_gallery")

# ── wait for DB (helpful on first Docker-compose boot) ───────────────────────
def wait_for_db(retries=10, delay=2):
    for i in range(retries):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            conn.close()
            return
        except psycopg2.OperationalError:
            print(f"[seed_admin] DB not ready, retry {i+1}/{retries}…")
            time.sleep(delay)
    raise RuntimeError("[seed_admin] Could not connect to database")

# ── Cloudinary: upload seed images once ──────────────────────────────────────
def upload_seed_images_to_cloudinary():
    try:
        import cloudinary
        import cloudinary.uploader
        import cloudinary.api
    except ImportError:
        return {}

    if not all(os.getenv(k) for k in (
            "CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET")):
        return {}

    cloudinary.config(
        cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key    = os.getenv("CLOUDINARY_API_KEY"),
        api_secret = os.getenv("CLOUDINARY_API_SECRET"),
        secure     = True,
    )

    images_dir = os.path.join(os.path.dirname(__file__), "static", "images")
    mapping = {}  # filename → cloudinary secure_url

    for path in glob.glob(os.path.join(images_dir, "*.jpg")) + \
                glob.glob(os.path.join(images_dir, "*.png")):
        basename = os.path.basename(path)
        public_id = f"uniform-gallery/seed/{os.path.splitext(basename)[0]}"
        try:
            # check if already uploaded
            info = cloudinary.api.resource(public_id)
            mapping[f"/static/images/{basename}"] = info["secure_url"]
            print(f"[seed_admin] Cloudinary already has {basename}")
        except Exception:
            result = cloudinary.uploader.upload(path, public_id=public_id)
            mapping[f"/static/images/{basename}"] = result["secure_url"]
            print(f"[seed_admin] Uploaded {basename} → {result['secure_url']}")

    return mapping

# ── main seed ─────────────────────────────────────────────────────────────────
def seed():
    wait_for_db()
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    cur  = conn.cursor()

    # 1. Fix admin password (correct werkzeug hash)
    hashed = generate_password_hash("Admin@1234", method="pbkdf2:sha256")
    cur.execute("""
        INSERT INTO admin (admin_name, email, password)
        VALUES ('Administrator', 'admin@school.edu', %s)
        ON CONFLICT (email) DO UPDATE SET password = EXCLUDED.password
    """, (hashed,))
    print("[seed_admin] Admin password set OK")

    # 2. If Cloudinary is configured, update image_path for seed uniforms
    cld_map = upload_seed_images_to_cloudinary()
    if cld_map:
        cur.execute("SELECT uniform_id, image_path FROM uniform")
        rows = cur.fetchall()
        for row in rows:
            new_url = cld_map.get(row["image_path"])
            if new_url and new_url != row["image_path"]:
                cur.execute(
                    "UPDATE uniform SET image_path=%s WHERE uniform_id=%s",
                    (new_url, row["uniform_id"]))
                print(f"[seed_admin] Updated uniform {row['uniform_id']} image → Cloudinary")

    conn.commit()
    cur.close()
    conn.close()
    print("[seed_admin] Done")

if __name__ == "__main__":
    seed()
