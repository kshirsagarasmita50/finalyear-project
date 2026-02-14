from flask import Flask, render_template, request
import pymysql

app = Flask(__name__)

# MySQL Connection
db = pymysql.connect(
    host="localhost",
    user="root",
    password="",   # your MySQL password
    database="fake_news_db"
)

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/text-news", methods=["GET", "POST"])
def text_news():
    result = None
    confidence = None

    if request.method == "POST":
        news_text = request.form["news"]

        # Dummy logic (replace later with ML)
        if "holiday" in news_text.lower():
            result = "FAKE"
            confidence = 80
        else:
            result = "REAL"
            confidence = 85

        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO text_news (news_text, prediction, confidence) VALUES (%s, %s, %s)",
            (news_text, result, confidence)
        )
        db.commit()
        cursor.close()

    return render_template("text_news.html", result=result, confidence=confidence)

if __name__ == "__main__":
    app.run(debug=True)
