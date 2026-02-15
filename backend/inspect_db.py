
import sqlite3
import json

conn = sqlite3.connect('sql_app.db')
cursor = conn.cursor()

cursor.execute("SELECT id, last_plan_date, plan_today, plan_tomorrow FROM users LIMIT 1")
row = cursor.fetchone()

if row:
    print(f"ID: {row[0]}")
    print(f"Last Plan Date (DB Column): {row[1]}")
    
    plan_today = json.loads(row[2]) if row[2] else None
    if plan_today:
        print(f"Plan Today Internal Date: {plan_today.get('date')}")
    else:
        print("Plan Today is NULL")

conn.close()
