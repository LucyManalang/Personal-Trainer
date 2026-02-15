
import sqlite3
import datetime

conn = sqlite3.connect('sql_app.db')
cursor = conn.cursor()

# Find duplicate "Recovery" block on Sunday Feb 15
date_target = "2026-02-15"
cursor.execute("SELECT id, type FROM workout_blocks WHERE date = ? AND type = 'Recovery'", (date_target,))
row = cursor.fetchone()

if row:
    block_id = row[0]
    print(f"Found conflicting Recovery block ID {block_id} on {date_target}. Deleting...")
    cursor.execute("DELETE FROM workout_blocks WHERE id = ?", (block_id,))
    conn.commit()
    print("Deleted.")
else:
    print(f"No conflicting Recovery block found on {date_target}.")

conn.close()
