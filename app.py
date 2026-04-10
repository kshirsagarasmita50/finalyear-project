import os
import sqlite3
import joblib
from flask import Flask, render_template, request, redirect, jsonify, session, flash
import random
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from flask_cors import CORS

# ---------------- APP SETUP ----------------
app = Flask(__name__)
app.secret_key = "secret123"

# ✅ FIXED CORS (no 403 issue)
CORS(app)

# ---------------- CONFIG ----------------
app.config['UPLOAD_FOLDER'] = "uploads"
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB

os.makedirs("instance", exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------- LOAD MODEL ----------------
try:
    model = joblib.load("model.pkl")
    vectorizer = joblib.load("vectorizer.pkl")
    print("✅ Models loaded successfully")
except:
    print("⚠️ Model not found, using demo mode")
    model = None
    vectorizer = None


# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("instance/database.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS predictions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        news_text TEXT,
        prediction TEXT,
        confidence REAL,
        username TEXT
    )
    """)

    default_password = generate_password_hash("1234")
    cur.execute(
        "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
        ("admin", default_password)
    )

    conn.commit()
    conn.close()
    print("✅ Database ready")


# ---------------- LOGIN REQUIRED ----------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            flash("Please login first", "error")
            return redirect("/")
        return f(*args, **kwargs)
    return wrapper


# ---------------- SAVE PREDICTION ----------------
def save_prediction(text, result, confidence, username):
    try:
        conn = sqlite3.connect("instance/database.db")
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO predictions (news_text, prediction, confidence, username) VALUES (?, ?, ?, ?)",
            (text, result, confidence, username)
        )

        conn.commit()
        conn.close()
    except Exception as e:
        print("DB Error:", e)


# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect("instance/database.db")
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            flash("Registration successful!", "success")
            return redirect("/")
        except sqlite3.IntegrityError:
            flash("Username already exists!", "error")
            return redirect("/register")
        finally:
            conn.close()

    return render_template("register.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("instance/database.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cur.fetchone()
    conn.close()

    if user and check_password_hash(user["password"], password):
        session["username"] = user["username"]
        flash("Login successful", "success")
        return redirect("/dashboard")
    else:
        flash("Invalid login", "error")
        return redirect("/")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=session["username"])


@app.route("/text-check")
@login_required
def text_check():
    return render_template("text_news.html")


@app.route("/image-check")
@login_required
def image_check():
    return render_template("image_news.html")


@app.route("/ai-tool")
@login_required
def ai_tool():
    return render_template("ai_tool.html")


# ---------------- TEXT PREDICTION ----------------
@app.route("/predict", methods=["POST"])
@login_required
def predict():
    data = request.get_json()
    text = data.get("text", "")

    if len(text) < 10:
        return jsonify({"error": "Text too short"}), 400

    if model and vectorizer:
        transformed = vectorizer.transform([text])
        pred = model.predict(transformed)[0]
        prediction = "REAL" if pred == 1 else "FAKE"

        try:
            prob = model.predict_proba(transformed)[0]
            confidence = round(max(prob) * 100)
        except:
            confidence = 80
    else:
        prediction = "FAKE"
        confidence = 50

    save_prediction(text, prediction, confidence, session["username"])

    return jsonify({
        "prediction": prediction,
        "confidence": confidence
    })


# ---------------- IMAGE PREDICTION (FIXED) ----------------
@app.route("/image-predict", methods=["POST"])
def image_predict():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # Demo prediction
    prediction = random.choice(["REAL", "FAKE"])
    confidence = random.randint(60, 99)

    username = session.get("username", "guest")
    save_prediction(filename, prediction, confidence, username)

    return jsonify({
        "prediction": prediction,
        "confidence": confidence
    })


# ---------------- HISTORY ----------------
@app.route("/history")
@login_required
def history():
    conn = sqlite3.connect("instance/database.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT news_text, prediction, confidence 
        FROM predictions 
        WHERE username=? 
        ORDER BY id DESC
    """, (session["username"],))

    data = cur.fetchall()
    conn.close()

    return render_template("history.html", data=data)


# ---------------- PROFILE ----------------
@app.route("/profile")
@login_required
def profile():
    conn = sqlite3.connect("instance/database.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT username FROM users WHERE username=?", (session["username"],))
    user = cur.fetchone()

    conn.close()

    return render_template("profile.html", user=user)


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- RUN ----------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)