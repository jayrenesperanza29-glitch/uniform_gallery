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
    uniform_type VARCHAR(120) NOT NULL UNIQUE,
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

-- 6 seed uniforms (image_path updated to Cloudinary by seed_admin.py if configured)
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
    'PE Shirt',
    'Physical Education shirt in DLSP school colors — dark green sides with white center panel and school emblem. Required every PE class schedule.',
    '/static/images/pe_shirt.jpg'
),
(
    'Official PE Pants',
    'Physical Education pants in DLSP school colors — dark green with elastic waist and side pockets. Required every PE class schedule.',
    '/static/images/pe_pants.jpg'
)
ON CONFLICT (uniform_type) DO NOTHING;

-- Prices – seed by uniform_type so IDs don't need to be hardcoded
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

    ('PE Shirt', 'XS',  280),
    ('PE Shirt', 'S',   280),
    ('PE Shirt', 'M',   280),
    ('PE Shirt', 'L',   300),
    ('PE Shirt', 'XL',  320),
    ('PE Shirt', 'XXL', 340),

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
