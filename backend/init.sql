-- Uniform Gallery – Database Schema
-- NOTE: The admin password hash is set correctly by seed_admin.py at startup.
--       The placeholder row below is intentionally a known-bad hash so that
--       nobody can log in before seed_admin.py runs.

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

-- Admin placeholder row – seed_admin.py replaces the password at startup
INSERT INTO admin (admin_name, email, password)
VALUES ('Administrator', 'admin@school.edu', 'PENDING_SEED')
ON CONFLICT (email) DO NOTHING;

-- 5 seed uniforms (image_path updated to Cloudinary by seed_admin.py if configured)
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

-- Prices – Official Uniform (Male) Top (id=1)
INSERT INTO price (uniform_id, label, amount)
SELECT 1, unnest(ARRAY['XS','S','M','L','XL','XXL']),
           unnest(ARRAY[380,380,380,400,420,450]::numeric[])
WHERE NOT EXISTS (SELECT 1 FROM price WHERE uniform_id = 1);

-- Prices – Official Uniform (Male) Bottom (id=2)
INSERT INTO price (uniform_id, label, amount)
SELECT 2, unnest(ARRAY['XS','S','M','L','XL','XXL']),
           unnest(ARRAY[320,320,320,350,380,400]::numeric[])
WHERE NOT EXISTS (SELECT 1 FROM price WHERE uniform_id = 2);

-- Prices – Official Uniform (Female) Top (id=3)
INSERT INTO price (uniform_id, label, amount)
SELECT 3, unnest(ARRAY['XS','S','M','L','XL','XXL']),
           unnest(ARRAY[380,380,380,400,420,450]::numeric[])
WHERE NOT EXISTS (SELECT 1 FROM price WHERE uniform_id = 3);

-- Prices – Official Uniform (Female) Bottom (id=4)
INSERT INTO price (uniform_id, label, amount)
SELECT 4, unnest(ARRAY['XS','S','M','L','XL','XXL']),
           unnest(ARRAY[320,320,320,350,380,400]::numeric[])
WHERE NOT EXISTS (SELECT 1 FROM price WHERE uniform_id = 4);

-- Prices – PE Shirt (id=5)
INSERT INTO price (uniform_id, label, amount)
SELECT 5, unnest(ARRAY['XS','S','M','L','XL','XXL']),
           unnest(ARRAY[280,280,280,300,320,340]::numeric[])
WHERE NOT EXISTS (SELECT 1 FROM price WHERE uniform_id = 5);
