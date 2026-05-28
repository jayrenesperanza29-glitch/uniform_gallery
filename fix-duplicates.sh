set -e

echo ">>> Deduplicating uniform table and adding UNIQUE constraint..."
docker exec uniform_db psql -U uniform_user -d uniform_gallery << 'SQL'
-- 1. Remove duplicates, keep lowest uniform_id per type
DELETE FROM uniform
WHERE uniform_id NOT IN (
    SELECT MIN(uniform_id) FROM uniform GROUP BY uniform_type
);

-- 2. Add UNIQUE constraint if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uniform_uniform_type_key'
    ) THEN
        ALTER TABLE uniform ADD CONSTRAINT uniform_uniform_type_key UNIQUE (uniform_type);
    END IF;
END $$;

-- 3. Insert Official PE Pants if missing
INSERT INTO uniform (uniform_type, description, image_path)
VALUES (
    'Official PE Pants',
    'Physical Education pants in DLSP school colors — dark green with elastic waist and side pockets. Required every PE class schedule.',
    '/static/images/pe_pants.jpg'
)
ON CONFLICT (uniform_type) DO NOTHING;

-- 4. Seed PE Pants prices if missing
INSERT INTO price (uniform_id, label, amount)
SELECT u.uniform_id, v.label, v.amount
FROM uniform u
JOIN (VALUES
    ('Official PE Pants', 'XS',  280::numeric),
    ('Official PE Pants', 'S',   280),
    ('Official PE Pants', 'M',   280),
    ('Official PE Pants', 'L',   300),
    ('Official PE Pants', 'XL',  320),
    ('Official PE Pants', 'XXL', 340)
) AS v(uniform_type, label, amount) ON u.uniform_type = v.uniform_type
WHERE NOT EXISTS (
    SELECT 1 FROM price p WHERE p.uniform_id = u.uniform_id AND p.label = v.label
);

SELECT 'Done! Uniform count: ' || COUNT(*) FROM uniform;
SQL

echo ""
echo ">>> Rebuilding backend..."
docker compose up --build -d backend

echo ""
echo "Done! The duplicate bug is fixed."
echo "Duplicates removed, UNIQUE constraint added, Official PE Pants seeded."
