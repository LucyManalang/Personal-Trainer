
import sqlite3
import datetime

conn = sqlite3.connect('sql_app.db')
cursor = conn.cursor()

today = datetime.datetime.now().date().strftime("%Y-%m-%d")
tomorrow = (datetime.datetime.now().date() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

print(f"Checking for Duplicates on {today} and {tomorrow}...")

cursor.execute("SELECT id, date, type FROM workout_blocks WHERE date IN (?, ?) ORDER BY date", (today, tomorrow))
rows = cursor.fetchall()

for row in rows:
    print(f"ID: {row[0]}, Date: {row[1]}, Type: {row[2]}")

conn.close()
