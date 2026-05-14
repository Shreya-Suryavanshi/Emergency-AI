from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
import pickle
from pathlib import Path
from datetime import datetime, timezone
import os
import sqlite3
from deep_translator import GoogleTranslator
from werkzeug.security import generate_password_hash, check_password_hash

BACKEND_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = (BACKEND_DIR / ".." / "frontend").resolve()
AUTH_DB_PATH = BACKEND_DIR / "auth.db"
DEFAULT_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@emergency.local").strip().lower()
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123").strip()

app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = os.getenv("APP_SECRET_KEY", "change-me-for-production")

# Load ML model
with (BACKEND_DIR / "model.pkl").open("rb") as f:
    model, vectorizer = pickle.load(f)

chat_log = []

responses = {
    "fire": "Fire response team has been notified.",
    "medical": "Medical response team has been notified.",
    "police": "Police control room has been notified.",
    "natural_disaster": "Disaster response team has been notified.",
    "utility": "Utility emergency support has been notified."
}


def get_auth_db():
    conn = sqlite3.connect(AUTH_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


def init_auth_db() -> None:
    conn = get_auth_db()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        if not _column_exists(conn, "users", "role"):
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
        if not _column_exists(conn, "users", "is_active"):
            conn.execute("ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")
        if not _column_exists(conn, "users", "last_login_at"):
            conn.execute("ALTER TABLE users ADD COLUMN last_login_at TEXT")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_email TEXT,
                msg TEXT NOT NULL,
                translated TEXT,
                category TEXT,
                response TEXT,
                location_text TEXT,
                lat TEXT,
                lon TEXT,
                people_caught TEXT,
                people_injured TEXT,
                lang TEXT,
                ts TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        if not _column_exists(conn, "chat_records", "issue_status"):
            conn.execute("ALTER TABLE chat_records ADD COLUMN issue_status TEXT NOT NULL DEFAULT 'unresolved'")
        if not _column_exists(conn, "chat_records", "resolved_by"):
            conn.execute("ALTER TABLE chat_records ADD COLUMN resolved_by TEXT")
        if not _column_exists(conn, "chat_records", "resolved_ts"):
            conn.execute("ALTER TABLE chat_records ADD COLUMN resolved_ts TEXT")
        if not _column_exists(conn, "chat_records", "is_archived"):
            conn.execute("ALTER TABLE chat_records ADD COLUMN is_archived INTEGER NOT NULL DEFAULT 0")
        if not _column_exists(conn, "chat_records", "archived_by"):
            conn.execute("ALTER TABLE chat_records ADD COLUMN archived_by TEXT")
        if not _column_exists(conn, "chat_records", "archived_ts"):
            conn.execute("ALTER TABLE chat_records ADD COLUMN archived_ts TEXT")

        # Ensure at least one admin user exists for admin page access.
        admin_row = conn.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1").fetchone()
        if not admin_row:
            existing = conn.execute("SELECT id FROM users WHERE email = ?", (DEFAULT_ADMIN_EMAIL,)).fetchone()
            if existing:
                conn.execute("UPDATE users SET role = 'admin' WHERE id = ?", (existing["id"],))
            else:
                conn.execute(
                    "INSERT INTO users (email, password_hash, created_at, role) VALUES (?, ?, ?, 'admin')",
                    (
                        DEFAULT_ADMIN_EMAIL,
                        generate_password_hash(DEFAULT_ADMIN_PASSWORD),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
        conn.commit()
    finally:
        conn.close()


init_auth_db()


def translate_text(text: str, source: str = "auto", target: str = "en") -> str:
    """
    Google translation with two modes:
    - cloud: official Google Cloud Translate API (when configured)
    - web: deep-translator GoogleTranslator fallback (no paid setup)
    """
    mode = (os.getenv("GOOGLE_TRANSLATE_MODE") or "web").strip().lower()

    if not text:
        return text
    if source == target:
        return text

    if mode == "cloud":
        try:
            from google.cloud import translate_v2 as translate

            client = translate.Client()
            result = client.translate(text, source_language=source if source != "auto" else None, target_language=target)
            translated = result.get("translatedText")
            if translated:
                return translated
        except Exception:
            # Fall back to web translator below
            pass

    return GoogleTranslator(source=source, target=target).translate(text)


@app.post("/auth/register")
def auth_register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or "@" not in email:
        return jsonify({"ok": False, "error": "Valid email is required."}), 400
    if len(password) < 6:
        return jsonify({"ok": False, "error": "Password must be at least 6 characters."}), 400

    conn = get_auth_db()
    try:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            return jsonify({"ok": False, "error": "Email already registered."}), 409

        password_hash = generate_password_hash(password)
        conn.execute(
            "INSERT INTO users (email, password_hash, created_at, role) VALUES (?, ?, ?, 'user')",
            (email, password_hash, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"ok": True, "message": "Account created. Please sign in."})


@app.post("/auth/login")
def auth_login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    conn = get_auth_db()
    try:
        row = conn.execute(
            "SELECT id, email, password_hash, role, is_active FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    finally:
        conn.close()

    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify({"ok": False, "error": "Invalid email or password."}), 401
    if int(row["is_active"] or 0) != 1:
        return jsonify({"ok": False, "error": "Account is disabled. Contact admin."}), 403

    conn = get_auth_db()
    try:
        conn.execute(
            "UPDATE users SET last_login_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), row["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    session["user_id"] = row["id"]
    session["user_email"] = row["email"]
    session["user_role"] = row["role"] or "user"
    return jsonify({"ok": True, "user": {"id": row["id"], "email": row["email"], "role": row["role"] or "user"}})


@app.post("/auth/logout")
def auth_logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/auth/me")
def auth_me():
    user_id = session.get("user_id")
    user_email = session.get("user_email")
    user_role = session.get("user_role") or "user"
    if not user_id or not user_email:
        return jsonify({"ok": True, "authenticated": False, "user": None})
    return jsonify({"ok": True, "authenticated": True, "user": {"id": user_id, "email": user_email, "role": user_role}})


@app.get("/records/me")
def records_me():
    user_id = session.get("user_id")
    user_email = session.get("user_email")
    if not user_id or not user_email:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401

    conn = get_auth_db()
    try:
        rows = conn.execute(
            """
            SELECT id, user_email, msg, translated, category, response, location_text,
                   lat, lon, people_caught, people_injured, lang, ts, issue_status, resolved_by, resolved_ts
            FROM chat_records
            WHERE user_id = ?
              AND IFNULL(is_archived, 0) = 0
            ORDER BY id DESC
            """,
            (user_id,),
        ).fetchall()
    finally:
        conn.close()

    return jsonify({"ok": True, "records": [dict(r) for r in rows]})


@app.get("/records/all")
def records_all():
    user_id = session.get("user_id")
    user_role = session.get("user_role")
    if not user_id:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401
    if user_role != "admin":
        return jsonify({"ok": False, "error": "Admin access required"}), 403

    user_email_q = (request.args.get("user_email") or "").strip().lower()
    category_q = (request.args.get("category") or "").strip().lower()
    status_q = (request.args.get("status") or "").strip().lower()
    start_q = (request.args.get("start") or "").strip()
    end_q = (request.args.get("end") or "").strip()
    include_archived = (request.args.get("include_archived") or "false").strip().lower() == "true"

    query = """
        SELECT id, user_email, msg, translated, category, response, location_text,
               lat, lon, people_caught, people_injured, lang, ts, issue_status, resolved_by, resolved_ts,
               IFNULL(is_archived, 0) AS is_archived, archived_by, archived_ts
        FROM chat_records
        WHERE 1=1
    """
    params: list[str] = []
    if not include_archived:
        query += " AND IFNULL(is_archived, 0) = 0"
    if user_email_q:
        query += " AND LOWER(IFNULL(user_email, '')) LIKE ?"
        params.append(f"%{user_email_q}%")
    if category_q:
        query += " AND LOWER(IFNULL(category, '')) = ?"
        params.append(category_q)
    if status_q:
        query += " AND LOWER(IFNULL(issue_status, 'unresolved')) = ?"
        params.append(status_q)
    if start_q:
        query += " AND IFNULL(ts, '') >= ?"
        params.append(start_q)
    if end_q:
        query += " AND IFNULL(ts, '') <= ?"
        params.append(end_q)
    query += " ORDER BY id DESC"

    conn = get_auth_db()
    try:
        rows = conn.execute(query, tuple(params)).fetchall()
    finally:
        conn.close()

    return jsonify({"ok": True, "records": [dict(r) for r in rows]})


def _admin_required():
    user_id = session.get("user_id")
    user_role = session.get("user_role")
    if not user_id:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401
    if user_role != "admin":
        return jsonify({"ok": False, "error": "Admin access required"}), 403
    return None


@app.post("/records/<int:record_id>/status")
def update_record_status(record_id: int):
    guard = _admin_required()
    if guard:
        return guard
    user_id = session.get("user_id")
    admin_email = session.get("user_email")

    data = request.get_json(silent=True) or {}
    new_status = (data.get("status") or "").strip().lower()
    if new_status not in {"unresolved", "resolved", "on_hold"}:
        return jsonify({"ok": False, "error": "Invalid status"}), 400

    resolved_by = admin_email if new_status in {"resolved", "on_hold"} else None
    resolved_ts = datetime.now(timezone.utc).isoformat() if new_status in {"resolved", "on_hold"} else None

    conn = get_auth_db()
    try:
        row = conn.execute("SELECT id FROM chat_records WHERE id = ?", (record_id,)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Record not found"}), 404
        conn.execute(
            """
            UPDATE chat_records
            SET issue_status = ?, resolved_by = ?, resolved_ts = ?
            WHERE id = ?
            """,
            (new_status, resolved_by, resolved_ts, record_id),
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"ok": True, "message": "Status updated", "record_id": record_id, "status": new_status})


@app.post("/records/bulk-status")
def bulk_update_status():
    guard = _admin_required()
    if guard:
        return guard
    admin_email = session.get("user_email")
    data = request.get_json(silent=True) or {}
    ids = data.get("ids") or []
    new_status = (data.get("status") or "").strip().lower()
    if not isinstance(ids, list) or not ids:
        return jsonify({"ok": False, "error": "ids list is required"}), 400
    if new_status not in {"unresolved", "resolved", "on_hold"}:
        return jsonify({"ok": False, "error": "Invalid status"}), 400
    resolved_by = admin_email if new_status in {"resolved", "on_hold"} else None
    resolved_ts = datetime.now(timezone.utc).isoformat() if new_status in {"resolved", "on_hold"} else None

    conn = get_auth_db()
    try:
        qmarks = ",".join("?" for _ in ids)
        conn.execute(
            f"""
            UPDATE chat_records
            SET issue_status = ?, resolved_by = ?, resolved_ts = ?
            WHERE id IN ({qmarks})
            """,
            (new_status, resolved_by, resolved_ts, *ids),
        )
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True, "updated": len(ids), "status": new_status})


@app.post("/records/bulk-archive")
def bulk_archive():
    guard = _admin_required()
    if guard:
        return guard
    admin_email = session.get("user_email")
    data = request.get_json(silent=True) or {}
    ids = data.get("ids") or []
    archive_flag = bool(data.get("archive", True))
    if not isinstance(ids, list) or not ids:
        return jsonify({"ok": False, "error": "ids list is required"}), 400

    archived_by = admin_email if archive_flag else None
    archived_ts = datetime.now(timezone.utc).isoformat() if archive_flag else None
    conn = get_auth_db()
    try:
        qmarks = ",".join("?" for _ in ids)
        conn.execute(
            f"""
            UPDATE chat_records
            SET is_archived = ?, archived_by = ?, archived_ts = ?
            WHERE id IN ({qmarks})
            """,
            (1 if archive_flag else 0, archived_by, archived_ts, *ids),
        )
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True, "updated": len(ids), "archived": archive_flag})


@app.post("/records/bulk-delete")
def bulk_delete():
    guard = _admin_required()
    if guard:
        return guard
    data = request.get_json(silent=True) or {}
    ids = data.get("ids") or []
    if not isinstance(ids, list) or not ids:
        return jsonify({"ok": False, "error": "ids list is required"}), 400
    conn = get_auth_db()
    try:
        qmarks = ",".join("?" for _ in ids)
        conn.execute(f"DELETE FROM chat_records WHERE id IN ({qmarks})", (*ids,))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True, "deleted": len(ids)})


@app.get("/admin/users")
def admin_users():
    guard = _admin_required()
    if guard:
        return guard
    conn = get_auth_db()
    try:
        rows = conn.execute(
            """
            SELECT u.id, u.email, u.role, IFNULL(u.is_active,1) AS is_active, u.created_at, u.last_login_at,
                   COUNT(cr.id) AS total_records,
                   SUM(CASE WHEN IFNULL(cr.issue_status,'unresolved')='unresolved' THEN 1 ELSE 0 END) AS unresolved_count,
                   MAX(cr.ts) AS last_record_at
            FROM users u
            LEFT JOIN chat_records cr ON cr.user_id = u.id
            GROUP BY u.id, u.email, u.role, u.is_active, u.created_at, u.last_login_at
            ORDER BY u.id DESC
            """
        ).fetchall()
    finally:
        conn.close()
    return jsonify({"ok": True, "users": [dict(r) for r in rows]})


@app.post("/admin/users/<int:target_user_id>/active")
def admin_user_active(target_user_id: int):
    guard = _admin_required()
    if guard:
        return guard
    data = request.get_json(silent=True) or {}
    is_active = 1 if bool(data.get("is_active", True)) else 0
    conn = get_auth_db()
    try:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (target_user_id,)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "User not found"}), 404
        conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (is_active, target_user_id))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True, "user_id": target_user_id, "is_active": bool(is_active)})


@app.post("/admin/users/<int:target_user_id>/role")
def admin_user_role(target_user_id: int):
    guard = _admin_required()
    if guard:
        return guard
    data = request.get_json(silent=True) or {}
    role = (data.get("role") or "").strip().lower()
    if role not in {"admin", "user"}:
        return jsonify({"ok": False, "error": "Invalid role"}), 400
    conn = get_auth_db()
    try:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (target_user_id,)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "User not found"}), 404
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, target_user_id))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True, "user_id": target_user_id, "role": role})


@app.post("/admin/users/<int:target_user_id>/reset-password")
def admin_reset_password(target_user_id: int):
    guard = _admin_required()
    if guard:
        return guard
    data = request.get_json(silent=True) or {}
    new_password = data.get("new_password") or ""
    if len(new_password) < 6:
        return jsonify({"ok": False, "error": "New password must be at least 6 characters"}), 400
    conn = get_auth_db()
    try:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (target_user_id,)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "User not found"}), 404
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (generate_password_hash(new_password), target_user_id),
        )
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True, "user_id": target_user_id})


@app.route("/", methods=["GET"])
def home():
    # Open authentication page first.
    login_path = FRONTEND_DIR / "login.html"
    if login_path.exists():
        return send_from_directory(FRONTEND_DIR, "login.html")
    return "🚀 Emergency AI Backend Running Successfully!"


@app.route("/<path:path>", methods=["GET"])
def frontend_files(path: str):
    file_path = FRONTEND_DIR / path
    if file_path.exists() and file_path.is_file():
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json

    user_text = (data.get("message") or "").strip()
    if not user_text:
        return jsonify({"response": "Please enter an emergency message.", "category": "unknown", "translated": ""}), 400

    lat = data.get("lat", "")
    lon = data.get("lon", "")
    location_text = (data.get("locationText") or "").strip()
    people_caught = data.get("peopleCaught", "")
    people_injured = data.get("peopleInjured", "")
    lang = (data.get("lang") or "en").strip()  # e.g. "hi-IN" from UI
    target_lang = (lang.split("-")[0] if lang else "en").lower()  # "hi"

    # Translate user input to English for ML model
    try:
        translated = translate_text(user_text, source="auto", target="en")
    except Exception:
        translated = user_text

    # ML Prediction
    X = vectorizer.transform([translated])
    pred = model.predict(X)[0]

    response = responses.get(pred, "Emergency response has been initiated.")

    # Location-based message
    if pred == "fire":
        location_msg = "Nearest fire station contacted"
    elif pred == "medical":
        location_msg = "Nearest hospital alerted"
    elif pred == "police":
        location_msg = "Nearest police station informed"
    elif pred == "natural_disaster":
        location_msg = "Nearest disaster control room informed"
    elif pred == "utility":
        location_msg = "Nearest utility control room informed"
    else:
        location_msg = "Nearest emergency control room informed"

    details = []
    if location_text:
        details.append(f"Location: {location_text}")
    if lat and lon:
        details.append(f"GPS: {lat}, {lon}")
    if people_caught != "" and people_caught is not None:
        details.append(f"People trapped: {people_caught}")
    if people_injured != "" and people_injured is not None:
        details.append(f"Injured: {people_injured}")

    detail_str = f" | {' | '.join(details)}" if details else ""

    # Fire flow requested by user:
    # 1) if fire and location missing -> ask location
    # 2) if fire and location present -> confirm helpers ETA
    if pred == "fire" and not location_text:
        final_response_en = (
            "Fire emergency detected. Please provide your exact location "
            "(address and nearby landmark) so we can route support immediately."
        )
    elif pred == "fire" and location_text:
        final_response_en = (
            f"Location received: {location_text}. "
            "Emergency helpers are on the way. Estimated arrival time is about 5 minutes."
        )
    else:
        final_response_en = f"{response} {location_msg}{detail_str}"

    # Translate response back to user's selected language (if needed)
    final_response = final_response_en
    if target_lang and target_lang != "en":
        try:
            final_response = translate_text(final_response_en, source="en", target=target_lang)
        except Exception:
            final_response = final_response_en

    # Store logs (in-memory + persistent per-user records)
    chat_log.append({
        "msg": user_text,
        "translated": translated,
        "type": pred,
        "location": [lat, lon],
        "locationText": location_text,
        "peopleCaught": people_caught,
        "peopleInjured": people_injured,
        "lang": target_lang,
        "ts": datetime.now(timezone.utc).isoformat()
    })

    user_id = session.get("user_id")
    user_email = session.get("user_email")
    conn = get_auth_db()
    try:
        conn.execute(
            """
            INSERT INTO chat_records (
                user_id, user_email, msg, translated, category, response, location_text,
                lat, lon, people_caught, people_injured, lang, ts, issue_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                user_email,
                user_text,
                translated,
                pred,
                final_response,
                location_text,
                str(lat),
                str(lon),
                str(people_caught),
                str(people_injured),
                target_lang,
                datetime.now(timezone.utc).isoformat(),
                "unresolved",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({
        "response": final_response,
        "category": pred,
        "translated": translated
    })


@app.route("/stats")
def stats():
    return jsonify({
        "total_chats": len(chat_log),
        "logs": chat_log
    })


if __name__ == "__main__":
    app.run(debug=True)