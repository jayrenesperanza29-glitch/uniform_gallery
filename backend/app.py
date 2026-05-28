import os
import binascii
import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

import jwt
import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request, send_from_directory, g
from flask_cors import CORS

# ── Cloudinary (optional) ────────────────────────────────────────────────────
try:
    import cloudinary
    import cloudinary.uploader
    _cld_ok = all(os.getenv(k) for k in (
        "CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"))
    if _cld_ok:
        cloudinary.config(
            cloud_name  = os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key     = os.getenv("CLOUDINARY_API_KEY"),
            api_secret  = os.getenv("CLOUDINARY_API_SECRET"),
            secure      = True,
        )
    CLOUDINARY_CONFIGURED = _cld_ok
except ImportError:
    CLOUDINARY_CONFIGURED = False

# ── App setup ────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.errorhandler(404)
def not_found(e):      return jsonify({"error": "Not found"}), 404
@app.errorhandler(405)
def method_not_allowed(e): return jsonify({"error": "Method not allowed"}), 405
@app.errorhandler(500)
def internal_error(e): return jsonify({"error": "Internal server error"}), 500

JWT_SECRET   = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALG      = "HS256"
JWT_EXP_HRS  = 8
DATABASE_URL = os.getenv("DATABASE_URL",
    "postgresql://uniform_user:uniform_pass@db:5432/uniform_gallery")
IMAGES_DIR   = os.path.join(os.path.dirname(__file__), "static", "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# ── DB helpers ───────────────────────────────────────────────────────────────
def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(DATABASE_URL,
                                cursor_factory=psycopg2.extras.RealDictCursor)
    return g.db

@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db: db.close()

def query(sql, params=(), one=False, commit=False):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(sql, params)
        if commit:
            conn.commit()
            return cur.rowcount
        rows = cur.fetchall()
        return rows[0] if (one and rows) else rows

# ── Password helpers ─────────────────────────────────────────────────────────
def _hash_password(pw: str) -> str:
    return generate_password_hash(pw, method="pbkdf2:sha256")

def _check_password(pw: str, stored: str) -> bool:
    try:    return check_password_hash(stored, pw)
    except: return False

# ── JWT helpers ──────────────────────────────────────────────────────────────
def _make_token(identity: dict) -> str:
    payload = {
        **identity,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXP_HRS),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def jwt_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Missing token"}), 401
        token = auth.split(" ", 1)[1]
        try:
            g.current_user = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not g.current_user.get("is_admin"):
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return wrapper

# ── Auth routes ──────────────────────────────────────────────────────────────
@app.route("/api/auth/register", methods=["POST"])
def register():
    data  = request.get_json(force=True)
    name  = (data.get("student_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    pw    = data.get("password", "")
    if not (name and email and pw):
        return jsonify({"error": "All fields are required"}), 400
    if len(pw) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if query("SELECT student_id FROM student WHERE email=%s", (email,), one=True):
        return jsonify({"error": "Email already registered"}), 409
    query("INSERT INTO student (student_name, email, password) VALUES (%s,%s,%s)",
          (name, email, _hash_password(pw)), commit=True)
    row = query("SELECT student_id, student_name, email FROM student WHERE email=%s",
                (email,), one=True)
    token = _make_token({"sub": row["student_id"], "name": row["student_name"],
                         "email": email, "is_admin": False})
    return jsonify({"token": token, "user": dict(row)}), 201

@app.route("/api/auth/login", methods=["POST"])
def login():
    data  = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    pw    = data.get("password", "")

    student = query("SELECT * FROM student WHERE email=%s", (email,), one=True)
    if student and _check_password(pw, student["password"]):
        token = _make_token({"sub": student["student_id"],
                             "name": student["student_name"],
                             "email": email, "is_admin": False})
        return jsonify({"token": token, "user": {
            "student_id": student["student_id"],
            "name":       student["student_name"],
            "email":      email, "is_admin": False,
        }})

    admin = query("SELECT * FROM admin WHERE email=%s", (email,), one=True)
    if admin and _check_password(pw, admin["password"]):
        token = _make_token({"sub": admin["admin_id"],
                             "name": admin["admin_name"],
                             "email": email, "is_admin": True})
        return jsonify({"token": token, "user": {
            "admin_id": admin["admin_id"],
            "name":     admin["admin_name"],
            "email":    email, "is_admin": True,
        }})

    return jsonify({"error": "Invalid email or password"}), 401

@app.route("/api/auth/me", methods=["GET"])
@jwt_required
def me():
    return jsonify({"user": g.current_user})

# ── Uniform / Gallery routes ─────────────────────────────────────────────────
@app.route("/api/uniforms", methods=["GET"])
@jwt_required
def list_uniforms():
    rows = query("""
        SELECT u.uniform_id, u.uniform_type, u.description, u.image_path,
               json_agg(
                   json_build_object('price_id', p.price_id,
                                     'label', p.label, 'amount', p.amount)
                   ORDER BY p.price_id
               ) AS prices
        FROM uniform u
        LEFT JOIN price p ON p.uniform_id = u.uniform_id
        GROUP BY u.uniform_id
        ORDER BY u.uniform_id
    """)
    return jsonify({"uniforms": [dict(r) for r in rows]})

@app.route("/api/uniforms/<int:uid>", methods=["GET"])
@jwt_required
def get_uniform(uid):
    row = query("""
        SELECT u.uniform_id, u.uniform_type, u.description, u.image_path,
               json_agg(
                   json_build_object('price_id', p.price_id,
                                     'label', p.label, 'amount', p.amount)
                   ORDER BY p.price_id
               ) AS prices
        FROM uniform u
        LEFT JOIN price p ON p.uniform_id = u.uniform_id
        WHERE u.uniform_id = %s
        GROUP BY u.uniform_id
    """, (uid,), one=True)
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(row))

# ── Admin – uniform CRUD ─────────────────────────────────────────────────────
@app.route("/api/admin/uniforms", methods=["POST"])
@jwt_required
@admin_required
def create_uniform():
    data = request.get_json(force=True)
    row  = query(
        "INSERT INTO uniform (uniform_type, description, image_path)"
        " VALUES (%s,%s,%s) RETURNING *",
        (data["uniform_type"], data.get("description",""), data.get("image_path","")),
        one=True, commit=False)
    get_db().commit()
    return jsonify(dict(row)), 201

@app.route("/api/admin/uniforms/<int:uid>", methods=["PUT"])
@jwt_required
@admin_required
def update_uniform(uid):
    data = request.get_json(force=True)
    query("UPDATE uniform SET uniform_type=%s, description=%s, image_path=%s"
          " WHERE uniform_id=%s",
          (data["uniform_type"], data.get("description",""),
           data.get("image_path",""), uid), commit=True)
    return jsonify({"message": "Updated"})

@app.route("/api/admin/uniforms/<int:uid>", methods=["DELETE"])
@jwt_required
@admin_required
def delete_uniform(uid):
    row = query("SELECT uniform_type FROM uniform WHERE uniform_id=%s", (uid,), one=True)
    if row:
        query(
            "INSERT INTO uniform_deleted (uniform_type) VALUES (%s) ON CONFLICT DO NOTHING",
            (row["uniform_type"],), commit=True
        )
    query("DELETE FROM uniform WHERE uniform_id=%s", (uid,), commit=True)
    return jsonify({"message": "Deleted"})

# ── Admin – price CRUD ───────────────────────────────────────────────────────
@app.route("/api/admin/prices", methods=["POST"])
@jwt_required
@admin_required
def add_price():
    data = request.get_json(force=True)
    row  = query(
        "INSERT INTO price (uniform_id, label, amount) VALUES (%s,%s,%s) RETURNING *",
        (data["uniform_id"], data.get("label","Standard"), data["amount"]),
        one=True, commit=False)
    get_db().commit()
    return jsonify(dict(row)), 201

@app.route("/api/admin/prices/<int:pid>", methods=["PUT"])
@jwt_required
@admin_required
def update_price(pid):
    data = request.get_json(force=True)
    query("UPDATE price SET label=%s, amount=%s WHERE price_id=%s",
          (data.get("label","Standard"), data["amount"], pid), commit=True)
    return jsonify({"message": "Updated"})

@app.route("/api/admin/prices/<int:pid>", methods=["DELETE"])
@jwt_required
@admin_required
def delete_price(pid):
    query("DELETE FROM price WHERE price_id=%s", (pid,), commit=True)
    return jsonify({"message": "Deleted"})

@app.route("/api/admin/students", methods=["GET"])
@jwt_required
@admin_required
def list_students():
    rows = query("SELECT student_id, student_name, email, created_at"
                 " FROM student ORDER BY created_at DESC")
    return jsonify({"students": [dict(r) for r in rows]})

# ── Image upload ─────────────────────────────────────────────────────────────
@app.route("/api/admin/upload", methods=["POST"])
@jwt_required
@admin_required
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files["file"]
    ext  = os.path.splitext(file.filename)[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        return jsonify({"error": "Invalid file type"}), 400

    # ── Cloudinary path (persistent — required on Render free tier) ──────────
    if CLOUDINARY_CONFIGURED:
        result = cloudinary.uploader.upload(
            file,
            folder          = "uniform-gallery",
            allowed_formats = ["jpg", "jpeg", "png", "gif", "webp"],
        )
        return jsonify({"image_path": result["secure_url"]})

    # ── Local path (Docker / dev — ephemeral on Render) ──────────────────────
    filename = f"{binascii.hexlify(os.urandom(8)).decode()}{ext}"
    file.save(os.path.join(IMAGES_DIR, filename))
    return jsonify({"image_path": f"/static/images/{filename}"})

@app.route("/static/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(IMAGES_DIR, filename)

# ── Health ───────────────────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "cloudinary": CLOUDINARY_CONFIGURED})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
