import sqlite3
import os

db_path = os.path.join("instance", "database.db")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table';
    """)

    tables = cursor.fetchall()

    print("📂 Tables in database:")
    for table in tables:
        print(table[0])

    conn.close()

except Exception as e:
    print("❌ Error:", e)
