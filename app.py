from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import secrets
import random

app = Flask(__name__)
CORS(app)

DB = "database.db"
ADMIN_PASSWORD = "MineCashy@2026"

# =========================
# DATABASE
# =========================

def get_db():
    return sqlite3.connect(DB)

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        telegram TEXT PRIMARY KEY,
        ref_code TEXT,
        referred_by TEXT,
        wallet REAL DEFAULT 0,
        deposit REAL DEFAULT 0,
        boost REAL DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS deposits(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram TEXT,
        amount REAL,
        utr TEXT UNIQUE,
        status TEXT DEFAULT 'pending'
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS boost_keys(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        boost_key TEXT UNIQUE,
        amount REAL,
        status TEXT DEFAULT 'unused',
        used_by TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# HOME
# =========================

@app.route("/")
def home():
    return "Mine Cashy Backend Running ✅"

# =========================
# REGISTER USER
# =========================

@app.route("/register", methods=["POST"])
def register():

    data = request.json

    telegram = str(data.get("telegram"))
    ref = data.get("ref")

    ref_code = "USER" + telegram[-4:]

    conn = get_db()
    c = conn.cursor()

    try:
        c.execute("""
        INSERT INTO users
        (telegram, ref_code, referred_by)
        VALUES (?, ?, ?)
        """, (telegram, ref_code, ref))

        conn.commit()

    except:
        pass

    conn.close()

    return jsonify({
        "status": "success",
        "ref_code": ref_code
    })

# =========================
# USER INFO
# =========================

@app.route("/user/<telegram>")
def get_user(telegram):

    conn = get_db()
    c = conn.cursor()

    c.execute("""
    SELECT wallet,deposit,boost,ref_code
    FROM users
    WHERE telegram=?
    """, (telegram,))

    row = c.fetchone()

    conn.close()

    if not row:
        return jsonify({"status":"not_found"})

    return jsonify({
        "wallet": row[0],
        "deposit": row[1],
        "boost": row[2],
        "ref_code": row[3]
    })

# =========================
# MANUAL DEPOSIT
# =========================

@app.route("/manual-deposit", methods=["POST"])
def manual_deposit():

    data = request.json

    telegram = data.get("telegram")
    amount = float(data.get("amount", 0))
    utr = data.get("utr")

    if amount <= 0:
        return jsonify({"status":"invalid_amount"})

    conn = get_db()
    c = conn.cursor()

    c.execute(
        "SELECT * FROM deposits WHERE utr=?",
        (utr,)
    )

    if c.fetchone():
        conn.close()
        return jsonify({"status":"duplicate"})

    c.execute("""
    INSERT INTO deposits
    (telegram, amount, utr)
    VALUES (?, ?, ?)
    """, (telegram, amount, utr))

    conn.commit()
    conn.close()

    return jsonify({"status":"pending"})

# =========================
# APPROVE DEPOSIT
# =========================

@app.route("/admin/approve", methods=["POST"])
def approve():

    deposit_id = request.json["id"]

    conn = get_db()
    c = conn.cursor()

    c.execute("""
    SELECT telegram,amount,status
    FROM deposits
    WHERE id=?
    """, (deposit_id,))

    row = c.fetchone()

    if not row:
        conn.close()
        return jsonify({"status":"not_found"})

    telegram, amount, status = row

    if status != "pending":
        conn.close()
        return jsonify({"status":"already_done"})

    c.execute("""
    UPDATE deposits
    SET status='approved'
    WHERE id=?
    """, (deposit_id,))

    c.execute("""
    UPDATE users
    SET wallet = wallet + ?,
        deposit = deposit + ?
    WHERE telegram=?
    """, (amount, amount, telegram))

    conn.commit()
    conn.close()

    return jsonify({"status":"approved"})

# =========================
# ACTIVATE KEY
# =========================

@app.route("/activate-key", methods=["POST"])
def activate_key():

    data = request.json

    telegram = data.get("telegram")
    key = data.get("key")

    conn = get_db()
    c = conn.cursor()

    c.execute("""
    SELECT amount,status
    FROM boost_keys
    WHERE boost_key=?
    """, (key,))

    row = c.fetchone()

    if not row:
        conn.close()
        return jsonify({"status":"invalid"})

    amount, status = row

    if status != "unused":
        conn.close()
        return jsonify({"status":"used"})

    c.execute("""
    UPDATE boost_keys
    SET status='used',
        used_by=?
    WHERE boost_key=?
    """, (telegram, key))

    c.execute("""
    UPDATE users
    SET boost = boost + ?
    WHERE telegram=?
    """, (amount, telegram))

    conn.commit()
    conn.close()

    return jsonify({
        "status":"success",
        "amount":amount
    })

# =========================
# PRIVATE ADMIN PANEL
# =========================

@app.route("/admin")
def admin():

    password = request.args.get("password")

    if password != ADMIN_PASSWORD:
        return "Access Denied", 403

    return """
    <h2>Mine Cashy Admin</h2>

    <form action="/admin/generate" method="post">

        <input type="hidden"
        name="password"
        value="Yogesh@2203">

        <input type="number"
        name="amount"
        placeholder="Boost Amount"
        required>

        <button>
        Generate Key
        </button>

    </form>
    """

# =========================
# GENERATE KEY
# =========================

@app.route("/admin/generate", methods=["POST"])
def admin_generate():

    if request.form.get("password") != ADMIN_PASSWORD:
        return "Access Denied", 403

    amount = int(request.form["amount"])

    key = "MC-" + secrets.token_hex(4).upper()

    conn = get_db()
    c = conn.cursor()

    c.execute("""
    INSERT INTO boost_keys
    (boost_key, amount)
    VALUES (?, ?)
    """, (key, amount))

    conn.commit()
    conn.close()

    return f"""
    <h1>Key Generated Successfully</h1>

    <p><b>Amount:</b> {amount}</p>

    <p><b>Key:</b></p>

    <h2>{key}</h2>

    <br>

    <a href="/admin?password={ADMIN_PASSWORD}">
    Generate Another
    </a>
    """

# =========================
# QUICK KEY API
# =========================

@app.route("/admin/create/<int:amount>")
def create_key(amount):

    key = "MC-" + secrets.token_hex(4).upper()

    conn = get_db()
    c = conn.cursor()

    c.execute("""
    INSERT INTO boost_keys
    (boost_key, amount)
    VALUES (?, ?)
    """, (key, amount))

    conn.commit()
    conn.close()

    return jsonify({
        "status":"success",
        "key":key,
        "amount":amount
    })

# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)