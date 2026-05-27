"""
Runs at startup via entrypoint.sh.
1. Waits for the database to be ready.
2. Creates tables if they don't exist (Render has no init.sql auto-run).
3. Seeds the admin account with a correct werkzeug hash.
4. Uploads seed images to Cloudinary if configured.
"""
import os
import time
import glob

import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash

DATABASE_URL = os.getenv("DATABASE_URL",
    "postgresql://uniform_user:uniform_pass@db:5432/uniform_gallery")

# ── 1. Wait for DB ────────────────────────────────────────────────────────────
def wait_for_db(retries=15, delay=3):
    for i in range(retries):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            conn.close()
            print("[seed] DB is ready")
            return
        except psycopg2.OperationalError:
            print(f"[seed] DB not ready, retry {i+1}/{retries}…")
            time.sleep(delay)
    raise RuntimeError("[seed] Could not connect to database after retries")

# ── 2. Create tables ──────────────────────────────────────────────────────────
CREATE_TABLES = """
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS student (
    student_id   SERIAL PRIMARY KEY,
    student_name VARCHAR(120) NOT NULL,
    email        VARCHAR(255) NOT NULL UNIQUE,
    password     VARCHAR(512) NOT NULL,
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS admin (
    admin_id   SERIAL PRIMARY KEY,
    admin_name VARCHAR(120) NOT NULL,
    email      VARCHAR(255) NOT NULL UNIQUE,
    password   VARCHAR(512) NOT NULL
);

CREATE TABLE IF NOT EXISTS uniform (
    uniform_id   SERIAL PRIMARY KEY,
    uniform_type VARCHAR(120) NOT NULL,
    description  TEXT,
    image_path   VARCHAR(512)
);

CREATE TABLE IF NOT EXISTS price (
    price_id   SERIAL PRIMARY KEY,
    uniform_id INTEGER NOT NULL REFERENCES uniform(uniform_id) ON DELETE CASCADE,
    label      VARCHAR(80) DEFAULT 'Standard',
    amount     NUMERIC(10,2) NOT NULL
);
"""

SEED_UNIFORMS = """
INSERT INTO uniform (uniform_type, description, image_path) VALUES
(
    'Official Uniform (Male) - Top',
    'Male polo shirt — cream/white with dark green collar accent and school emblem on the chest. Short-sleeved, tailored fit.',
    '/static/images/official_uniform__male__top.jpg'
),
(
    'Official Uniform (Male) - Bottom',
    'Male dark green slacks — straight cut with elastic waist and side pockets. Paired with the official polo shirt.',
    '/static/images/official_uniform__male__bottom.jpg'
),
(
    'Official Uniform (Female) - Top',
    'Female blouse — white short-sleeved button-up with school emblem pocket and dark green necktie.',
    '/static/images/official_uniform__female__top.jpg'
),
(
    'Official Uniform (Female) - Bottom',
    'Female dark green pleated skirt — knee-length with elastic waist. Worn with the official blouse and necktie.',
    '/static/images/official_uniform__female__bottom.jpg'
),
(
    'PE Shirt',
    'Physical Education shirt in school colors — dark green sides with white center panel and school emblem. Required every PE class schedule.',
    '/static/images/pe_shirt.jpg'
)
ON CONFLICT DO NOTHING;

INSERT INTO price (uniform_id, label, amount)
SELECT 1, unnest(ARRAY['XS','S','M','L','XL','XXL']),
           unnest(ARRAY[380,380,380,400,420,450]::numeric[])
WHERE NOT EXISTS (SELECT 1 FROM price WHERE uniform_id = 1);

INSERT INTO price (uniform_id, label, amount)
SELECT 2, unnest(ARRAY['XS','S','M','L','XL','XXL']),
           unnest(ARRAY[320,320,320,350,380,400]::numeric[])
WHERE NOT EXISTS (SELECT 1 FROM price WHERE uniform_id = 2);

INSERT INTO price (uniform_id, label, amount)
SELECT 3, unnest(ARRAY['XS','S','M','L','XL','XXL']),
           unnest(ARRAY[380,380,380,400,420,450]::numeric[])
WHERE NOT EXISTS (SELECT 1 FROM price WHERE uniform_id = 3);

INSERT INTO price (uniform_id, label, amount)
SELECT 4, unnest(ARRAY['XS','S','M','L','XL','XXL']),
           unnest(ARRAY[320,320,320,350,380,400]::numeric[])
WHERE NOT EXISTS (SELECT 1 FROM price WHERE uniform_id = 4);

INSERT INTO price (uniform_id, label, amount)
SELECT 5, unnest(ARRAY['XS','S','M','L','XL','XXL']),
           unnest(ARRAY[280,280,280,300,320,340]::numeric[])
WHERE NOT EXISTS (SELECT 1 FROM price WHERE uniform_id = 5);
"""

# ── 3. Cloudinary image upload ────────────────────────────────────────────────
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
    mapping = {}

    for path in glob.glob(os.path.join(images_dir, "*.jpg")) + \
                glob.glob(os.path.join(images_dir, "*.png")):
        basename  = os.path.basename(path)
        public_id = f"uniform-gallery/seed/{os.path.splitext(basename)[0]}"
        try:
            info = cloudinary.api.resource(public_id)
            mapping[f"/static/images/{basename}"] = info["secure_url"]
            print(f"[seed] Cloudinary already has {basename}")
        except Exception:
            result = cloudinary.uploader.upload(path, public_id=public_id)
            mapping[f"/static/images/{basename}"] = result["secure_url"]
            print(f"[seed] Uploaded {basename} → {result['secure_url']}")

    return mapping

# ── main ──────────────────────────────────────────────────────────────────────
def seed():
    wait_for_db()

    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    cur  = conn.cursor()

    # Create tables
    cur.execute(CREATE_TABLES)
    print("[seed] Tables OK")

    # Seed uniforms + prices
    cur.execute(SEED_UNIFORMS)
    print("[seed] Uniforms + prices OK")

    # Admin account (correct werkzeug hash, idempotent)
    hashed = generate_password_hash("Admin@1234", method="pbkdf2:sha256")
    cur.execute("""
        INSERT INTO admin (admin_name, email, password)
        VALUES ('Administrator', 'admin@school.edu', %s)
        ON CONFLICT (email) DO UPDATE SET password = EXCLUDED.password
    """, (hashed,))
    print("[seed] Admin password OK")

    conn.commit()

    # Update image paths to Cloudinary URLs if configured
    cld_map = upload_seed_images_to_cloudinary()
    if cld_map:
        for local_path, cdn_url in cld_map.items():
            cur.execute(
                "UPDATE uniform SET image_path=%s WHERE image_path=%s",
                (cdn_url, local_path))
        conn.commit()
        print(f"[seed] Updated {len(cld_map)} image paths to Cloudinary")

    cur.close()
    conn.close()
    print("[seed] Done ✓")

if __name__ == "__main__":
    seed()
