
import sqlite3
import datetime

conn = sqlite3.connect('sql_app.db')
cursor = conn.cursor()

today = datetime.datetime.now().date().strftime("%Y-%m-%d")
print(f"--- Workout Blocks from {today} onwards ---")

cursor.execute("SELECT id, date, type, planned_duration_minutes FROM workout_blocks WHERE date >= ? ORDER BY date", (today,))
rows = cursor.fetchall()

if not rows:
    print("No blocks found.")
else:
    for row in rows:
        print(f"ID: {row[0]}, Date: {row[1]}, Type: {row[2]}, Duration: {row[3]}")

conn.close()
