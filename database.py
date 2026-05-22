import sqlite3

conn = sqlite3.connect("grades.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    grade INTEGER NOT NULL
)
""")

conn.commit()
conn.close()