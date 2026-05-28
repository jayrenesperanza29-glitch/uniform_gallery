import os
import time
import glob

import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash

DATABASE_URL = os.getenv("DATABASE_URL",
    "postgresql://uniform_user:uniform_pass@db:5432/uniform_gallery")

# ── Wait for DB ────────────────────────────────────────────────────────────
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

# ── One-time migrations (safe to re-run) ──────────────────────────────────
MIGRATE = """
-- Add UNIQUE constraint on uniform_type if missing.
-- This is the root fix for the duplicate-on-restart bug.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uniform_uniform_type_key'
    ) THEN
        -- Remove duplicates first (keep the lowest ID per type)
        DELETE FROM uniform
        WHERE uniform_id NOT IN (
            SELECT MIN(uniform_id) FROM uniform GROUP BY uniform_type
        );
        ALTER TABLE uniform ADD CONSTRAINT uniform_uniform_type_key UNIQUE (uniform_type);
    END IF;
END $$;

-- Create tombstone table if it doesn't exist yet (existing deployments)
CREATE TABLE IF NOT EXISTS uniform_deleted (
    uniform_type VARCHAR(120) PRIMARY KEY,
    deleted_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Reassign uniform IDs to be continuous (1, 2, 3, ...) with no gaps.
-- Prices are updated via CASCADE-aware temp mapping so foreign keys stay intact.
DO $$
DECLARE
    r        RECORD;
    new_id   INT := 1;
    max_id   INT;
BEGIN
    -- Only run if there are gaps
    SELECT MAX(uniform_id) INTO max_id FROM uniform;
    IF max_id IS NULL OR max_id = (SELECT COUNT(*) FROM uniform) THEN
        -- No gaps, nothing to do
    ELSE
        -- Temporarily drop the FK so we can reassign IDs freely
        ALTER TABLE price DROP CONSTRAINT IF EXISTS price_uniform_id_fkey;

        FOR r IN SELECT uniform_id FROM uniform ORDER BY uniform_id LOOP
            IF r.uniform_id <> new_id THEN
                UPDATE price   SET uniform_id = new_id WHERE uniform_id = r.uniform_id;
                UPDATE uniform SET uniform_id = new_id WHERE uniform_id = r.uniform_id;
            END IF;
            new_id := new_id + 1;
        END LOOP;

        -- Restore the FK
        ALTER TABLE price ADD CONSTRAINT price_uniform_id_fkey
            FOREIGN KEY (uniform_id) REFERENCES uniform(uniform_id) ON DELETE CASCADE;

        -- Reset the sequence so the next INSERT continues from the right number
        PERFORM setval('uniform_uniform_id_seq', (SELECT MAX(uniform_id) FROM uniform));
    END IF;
END $$;
"""

# ── Create tables ──────────────────────────────────────────────────────────
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

-- Tombstone: tracks uniforms deleted by an admin so the seed never re-adds them
CREATE TABLE IF NOT EXISTS uniform_deleted (
    uniform_type VARCHAR(120) PRIMARY KEY,
    deleted_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""

SEED_UNIFORMS = """
-- Ensure uniform_type is unique so ON CONFLICT works on existing DBs
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uniform_uniform_type_key'
    ) THEN
        -- Remove any accidental duplicates first, keeping the lowest ID
        DELETE FROM uniform u
        WHERE u.uniform_id NOT IN (
            SELECT MIN(uniform_id) FROM uniform GROUP BY uniform_type
        );
        ALTER TABLE uniform ADD CONSTRAINT uniform_uniform_type_key UNIQUE (uniform_type);
    END IF;
END $$;

INSERT INTO uniform (uniform_type, description, image_path) VALUES
(
    'Official Uniform (Male) - Top',
    'Male polo shirt — cream/white with dark green collar accent and DLSP school emblem on the chest. Short-sleeved, tailored fit.',
    '/static/images/official_uniform__male__top.jpg'
),
(
    'Official Uniform (Male) - Bottom',
    'Male dark green slacks — straight cut with elastic waist and side pockets. Paired with the official polo shirt.',
    '/static/images/official_uniform__male__bottom.jpg'
),
(
    'Official Uniform (Female) - Top',
    'Female blouse — white short-sleeved button-up with DLSP school emblem pocket and dark green necktie.',
    '/static/images/official_uniform__female__top.jpg'
),
(
    'Official Uniform (Female) - Bottom',
    'Female dark green pleated skirt — knee-length with elastic waist. Worn with the official blouse and necktie.',
    '/static/images/official_uniform__female__bottom.jpg'
),
(
    'Official PE Shirt',
    'Physical Education shirt in DLSP school colors — dark green sides with white center panel and school emblem. Required every PE class schedule.',
    '/static/images/pe_shirt.jpg'
),
(
    'Official PE Pants',
    'Physical Education pants in DLSP school colors — dark green with elastic waist and side pockets. Required every PE class schedule.',
    '/static/images/pe_pants.jpg'
)
ON CONFLICT (uniform_type) DO NOTHING;

-- Remove any just-inserted uniforms that were previously deleted by an admin
DELETE FROM uniform
WHERE uniform_type IN (SELECT uniform_type FROM uniform_deleted);

INSERT INTO price (uniform_id, label, amount)
SELECT u.uniform_id, v.label, v.amount
FROM uniform u
JOIN (VALUES
    ('Official Uniform (Male) - Top',    'XS',  380::numeric),
    ('Official Uniform (Male) - Top',    'S',   380),
    ('Official Uniform (Male) - Top',    'M',   380),
    ('Official Uniform (Male) - Top',    'L',   400),
    ('Official Uniform (Male) - Top',    'XL',  420),
    ('Official Uniform (Male) - Top',    'XXL', 450),

    ('Official Uniform (Male) - Bottom', 'XS',  320),
    ('Official Uniform (Male) - Bottom', 'S',   320),
    ('Official Uniform (Male) - Bottom', 'M',   320),
    ('Official Uniform (Male) - Bottom', 'L',   350),
    ('Official Uniform (Male) - Bottom', 'XL',  380),
    ('Official Uniform (Male) - Bottom', 'XXL', 400),

    ('Official Uniform (Female) - Top',    'XS',  380),
    ('Official Uniform (Female) - Top',    'S',   380),
    ('Official Uniform (Female) - Top',    'M',   380),
    ('Official Uniform (Female) - Top',    'L',   400),
    ('Official Uniform (Female) - Top',    'XL',  420),
    ('Official Uniform (Female) - Top',    'XXL', 450),

    ('Official Uniform (Female) - Bottom', 'XS',  320),
    ('Official Uniform (Female) - Bottom', 'S',   320),
    ('Official Uniform (Female) - Bottom', 'M',   320),
    ('Official Uniform (Female) - Bottom', 'L',   350),
    ('Official Uniform (Female) - Bottom', 'XL',  380),
    ('Official Uniform (Female) - Bottom', 'XXL', 400),

    ('Official PE Shirt', 'XS',  280),
    ('Official PE Shirt', 'S',   280),
    ('Official PE Shirt', 'M',   280),
    ('Official PE Shirt', 'L',   300),
    ('Official PE Shirt', 'XL',  320),
    ('Official PE Shirt', 'XXL', 340),

    ('Official PE Pants', 'XS',  280),
    ('Official PE Pants', 'S',   280),
    ('Official PE Pants', 'M',   280),
    ('Official PE Pants', 'L',   300),
    ('Official PE Pants', 'XL',  320),
    ('Official PE Pants', 'XXL', 340)
) AS v(uniform_type, label, amount) ON u.uniform_type = v.uniform_type
WHERE NOT EXISTS (
    SELECT 1 FROM price p WHERE p.uniform_id = u.uniform_id AND p.label = v.label
);
"""

# ── Cloudinary image upload ────────────────────────────────────────────────
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

    # Run migrations (safe to re-run — fixes duplicate bug on existing DBs)
    cur.execute(MIGRATE)
    conn.commit()
    print("[seed] Migrations OK")

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
