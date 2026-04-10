import sqlite3
from datetime import datetime

data = [
    ("Scientists discover a new planet that supports life in our solar system", "REAL", 90),
    ("Breaking: Celebrity caught in scandal involving aliens from Mars", "FAKE", 85),
    ("Government announces new policy to support small businesses", "REAL", 88),
    ("Doctors warn that drinking cold water causes cancer", "FAKE", 80),
    ("Researchers find ancient city under the Sahara Desert", "REAL", 92),
    ("Facebook shutting down permanently next week, company confirms", "FAKE", 95),
    ("New technology reduces electricity usage by 40% in homes", "REAL", 91),
    ("Python snake found driving a car in Mumbai, shocking locals", "FAKE", 97),
    ("University develops vaccine that shows 95% success rate", "REAL", 94),
    ("Whales found flying in the sky above Japan after earthquake", "FAKE", 99),
]

conn = sqlite3.connect("instance/database.db")
cur = conn.cursor()

for text, prediction, confidence in data:
    cur.execute(
    "INSERT INTO text_news (text, prediction, confidence) VALUES (?, ?, ?)",
    (news, prediction, confidence)
)

conn.commit()
conn.close()

print("✅ Dataset inserted successfully")
