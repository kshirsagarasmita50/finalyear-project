import sqlite3

conn = sqlite3.connect("instance/database.db")
cur = conn.cursor()

rows = cur.execute("SELECT * FROM news").fetchall()

for r in rows:
    print(r)

conn.close()