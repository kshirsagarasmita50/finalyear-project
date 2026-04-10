import sqlite3
import os

os.makedirs("instance", exist_ok=True)

conn = sqlite3.connect("instance/database.db")
cur = conn.cursor()

# users table
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

# insert login user
cur.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ("admin", "1234"))

# predictions table
cur.execute("""
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news_text TEXT,
    prediction TEXT,
    confidence REAL
)
""")

conn.commit()
conn.close()

print("Database & tables created!")