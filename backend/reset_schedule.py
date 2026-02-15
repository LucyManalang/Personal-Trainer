
import sqlite3
import datetime

conn = sqlite3.connect('sql_app.db')
cursor = conn.cursor()

today = datetime.datetime.now().date().strftime("%Y-%m-%d")

print(f"Deleting all workout blocks from {today} onwards...")
cursor.execute("DELETE FROM workout_blocks WHERE date >= ?", (today,))
deleted_count = cursor.rowcount
print(f"Deleted {deleted_count} blocks.")

conn.commit()
conn.close()
