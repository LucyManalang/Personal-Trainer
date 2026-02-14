import json
from dotenv import load_dotenv
load_dotenv() # Load env before imports
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import SQLALCHEMY_DATABASE_URL
from app.models import User, Goal, WorkoutBlock
from app.services.ai_coach import generate_3_day_plan

# Setup database connection
# Setup database connection
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_path = os.path.join(BASE_DIR, "sql_app.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_path}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def test_full_flow():
    print("--- Starting Personal Trainer Flow Test ---")
    
    # 1. Get User
    user = db.query(User).first()
    if not user:
        print("ERROR: No user found. Please run the app and login/sync first.")
        return
    print(f"User: {user.email}")

    # 2. Setup Goals (if none)
    goals = db.query(Goal).filter(Goal.user_id == user.id, Goal.status == "active").all()
    if not goals:
        print("No active goals found. Creating a sample goal...")
        new_goal = Goal(
            user_id=user.id,
            description="Improve 5k time and build upper body strength",
            type="long_term"
        )
        db.add(new_goal)
        db.commit()
        print(f"Created Goal: {new_goal.description}")
    else:
        print(f"Found {len(goals)} active goals.")

    # 3. Setup Schedule (Next 3 Days)
    today = datetime.now().date()
    print(f"\nChecking schedule for next 3 days starting {today}...")
    
    for i in range(3):
        d = today + timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        block = db.query(WorkoutBlock).filter(WorkoutBlock.user_id == user.id, WorkoutBlock.date == d_str).first()
        
        if not block:
            # Create a default block if missing
            w_type = "Strength" if i % 2 == 0 else "Cardio" # Alternating
            print(f"Creating missing block for {d_str}: {w_type}")
            block = WorkoutBlock(
                user_id=user.id,
                date=d_str,
                type=w_type,
                planned_duration_minutes=45
            )
            db.add(block)
            db.commit()
        else:
            print(f"Found block for {d_str}: {block.type}")
            
    # 4. Generate AI Plan
    print("\nRequesting AI 3-Day Plan...")
    try:
        # Load environment variables for OpenAI key if needed
        from dotenv import load_dotenv
        load_dotenv()
        
        plan = generate_3_day_plan(user, db)
        
        if "error" in plan:
            print(f"AI Generation Error: {plan['error']}")
        else:
            print("\nSUCCESS! Here is your generated plan:")
            print(json.dumps(plan, indent=2))
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    test_full_flow()
