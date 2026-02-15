
import sqlite3
import datetime

conn = sqlite3.connect('sql_app.db')
cursor = conn.cursor()

today = datetime.datetime.now().date().strftime("%Y-%m-%d")
user_id = 1 # Assuming single user for now

# Check if block exists
cursor.execute("SELECT id FROM workout_blocks WHERE user_id = ? AND date = ?", (user_id, today))
exists = cursor.fetchone()

if not exists:
    print(f"Inserting Recovery block for {today}...")
    cursor.execute("""
        INSERT INTO workout_blocks (user_id, date, type, planned_duration_minutes, notes, is_completed)
        VALUES (?, ?, 'Recovery', 45, 'Active Recovery', 0)
    """, (user_id, today))
    conn.commit()
    print("Block inserted!")
else:
    print("Block already exists (maybe duplicated? or race condition).")

conn.close()
