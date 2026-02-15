
import sqlite3
import datetime

conn = sqlite3.connect('sql_app.db')
cursor = conn.cursor()

print("Shifting 'Ultimate' blocks back by 1 day...")

# Find all Ultimate blocks
cursor.execute("SELECT id, date, type FROM workout_blocks WHERE type LIKE '%ultimate%'")
rows = cursor.fetchall()

for row in rows:
    block_id, date_str, b_type = row
    current_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    # Shift back by 1 day
    new_date = current_date - datetime.timedelta(days=1)
    new_date_str = new_date.strftime("%Y-%m-%d")
    
    print(f"Shifting ID {block_id} ({b_type}) from {date_str} to {new_date_str}")
    
    cursor.execute("UPDATE workout_blocks SET date = ? WHERE id = ?", (new_date_str, block_id))

conn.commit()
print("Shift complete.")
conn.close()
