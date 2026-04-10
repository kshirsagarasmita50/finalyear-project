import sqlite3

conn = sqlite3.connect("instance/database.db")
cur = conn.cursor()

print("---- USERS ----")
for row in cur.execute("SELECT * FROM users"):
    print(row)

print("\n---- PREDICTIONS ----")
for row in cur.execute("SELECT * FROM predictions"):
    print(row)

conn.close()