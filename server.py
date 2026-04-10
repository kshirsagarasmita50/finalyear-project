from flask import Flask, render_template, request, redirect, url_for
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ---------------- LOGIN PAGE ----------------
@app.route("/")
def login_page():
    return render_template("login.html")

# ---------------- LOGIN CHECK ----------------
@app.route("/login", methods=["POST"])
def login_post():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    

    print("USERNAME:", username)
    print("PASSWORD:", password)

    if username == "admin" and password == "Admin@123":
        return redirect(url_for("dashboard"))
    else:
        return """
        <h2 style="color:red;">❌ Invalid Login</h2>
        <a href="/">Try again</a>
        """

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    return "<h1>✅ Login Successful – Welcome to Dashboard</h1>"

# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(debug=True)
