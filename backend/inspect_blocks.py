
import sqlite3
import datetime

conn = sqlite3.connect('sql_app.db')
cursor = conn.cursor()

today = datetime.datetime.now().date().strftime("%Y-%m-%d")
tomorrow = (datetime.datetime.now().date() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

print(f"Checking Blocks for Today ({today}) and Tomorrow ({tomorrow})...")

cursor.execute("SELECT date, type, NOTES FROM workout_blocks WHERE date = ? OR date = ?", (today, tomorrow))
rows = cursor.fetchall()

if not rows:
    print("NO BLOCKS FOUND FOR TODAY OR TOMORROW!")
else:
    for row in rows:
        print(f"Date: {row[0]}, Type: {row[1]}, Notes: {row[2]}")

print("\n--- All Blocks (First 10) ---")
cursor.execute("SELECT date, type FROM workout_blocks ORDER BY date LIMIT 10")
for row in rows:
    print(f"{row[0]}: {row[1]}")

conn.close()
