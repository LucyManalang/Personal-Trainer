
import sqlite3

# Connect to the database
conn = sqlite3.connect('sql_app.db')
cursor = conn.cursor()

# Add new columns if they don't exist
try:
    cursor.execute("ALTER TABLE users ADD COLUMN plan_today JSON")
    print("Added plan_today column")
except sqlite3.OperationalError:
    print("plan_today column already exists")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN plan_tomorrow JSON")
    print("Added plan_tomorrow column")
except sqlite3.OperationalError:
    print("plan_tomorrow column already exists")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN last_plan_date VARCHAR")
    print("Added last_plan_date column")
except sqlite3.OperationalError:
    print("last_plan_date column already exists")

conn.commit()
conn.close()
