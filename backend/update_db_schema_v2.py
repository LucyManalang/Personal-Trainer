import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sql_app.db")

def migrate():
    print(f"Migrating database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Add columns to 'users' table
    # Columns: age (INTEGER), gender (VARCHAR), height (INTEGER), weight (INTEGER), openai_model (VARCHAR), settings (JSON)
    
    user_columns = [
        ("age", "INTEGER"),
        ("gender", "VARCHAR"),
        ("height", "INTEGER"),
        ("weight", "INTEGER"),
        ("openai_model", "VARCHAR DEFAULT 'gpt-4o'"),
        ("settings", "JSON")
    ]
    
    print("Checking 'users' table...")
    # USDA check if columns exist
    cursor.execute("PRAGMA table_info(users)")
    existing_cols = [row[1] for row in cursor.fetchall()]
    
    for col_name, col_type in user_columns:
        if col_name not in existing_cols:
            print(f"Adding '{col_name}' to users...")
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")
        else:
            print(f"Column '{col_name}' already exists in users.")

    # 2. Add columns to 'goals' table
    # Columns: target_date (DATETIME), is_completed (BOOLEAN)
    goal_columns = [
        ("target_date", "DATETIME"),
        ("is_completed", "BOOLEAN DEFAULT 0")
    ]
    
    print("Checking 'goals' table...")
    cursor.execute("PRAGMA table_info(goals)")
    existing_goal_cols = [row[1] for row in cursor.fetchall()]
    
    for col_name, col_type in goal_columns:
        if col_name not in existing_goal_cols:
            print(f"Adding '{col_name}' to goals...")
            try:
                cursor.execute(f"ALTER TABLE goals ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")
        else:
            print(f"Column '{col_name}' already exists in goals.")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
