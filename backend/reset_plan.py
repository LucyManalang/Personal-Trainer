
import sqlite3

conn = sqlite3.connect('sql_app.db')
cursor = conn.cursor()

# Reset plan columns for all users (or specifically the first one if we wanted to be specific, but single user app)
cursor.execute("UPDATE users SET plan_today = NULL, plan_tomorrow = NULL, last_plan_date = NULL")
conn.commit()

print("Daily Plan columns have been reset to NULL.")
conn.close()
