import sys
import os
from datetime import datetime, timedelta

# Add project root to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app.models import User, Goal, WorkoutBlock

def seed():
    db = SessionLocal()
    print("Seeding data...")

    # 1. Get or Create User
    user = db.query(User).first()
    if not user:
        user = User(email="lucy@example.com")
        db.add(user)
        db.commit()
        db.refresh(user)
    
    print(f"User found: {user.email}")
    
    # 2. Update Settings
    user.age = 30
    user.gender = "Female"
    user.height = 165
    user.weight = 60
    user.openai_model = "gpt-4o"
    user.settings = {
        "preferred_workout_time": "07:00",
        "equipment": ["Dumbbells", "Yoga Mat"],
        "injuries": [],
        "diet": "Vegetarian"
    }
    db.commit()
    print("User profile updated.")

    # 3. Add Goals
    db.query(Goal).filter(Goal.user_id == user.id).delete()
    
    # Event
    marathon_date = datetime.now() + timedelta(days=90)
    g1 = Goal(
        user_id=user.id,
        description="Chicago Marathon",
        type="event",
        target_date=marathon_date,
        status="active"
    )
    
    # Preferences
    g2 = Goal(user_id=user.id, description="Run comfortably at 5:30/km pace", type="short_term", status="active")
    g3 = Goal(user_id=user.id, description="Incorporate Yoga twice a week", type="preference", status="active")
    g4 = Goal(user_id=user.id, description="Sleep 8 hours a night", type="preference", status="active")
    
    db.add(g1)
    db.add(g2)
    db.add(g3)
    db.add(g4)
    db.commit()
    print("Goals seeded.")

    # 4. Add Workout History (Last 4 weeks)
    today = datetime.now().date()
    
    # Pattern: 0=Run, 1=Strength, 2=Run, 3=Strength, 4=Run, 5=Long Run, 6=Yoga
    history_pattern = {
        0: ("Run", 45),
        1: ("Strength", 60),
        2: ("Run", 45),
        3: ("Strength", 60),
        4: ("Run", 30),
        5: ("Long Run", 90), 
        6: ("Yoga", 60)
    }
    
    # Clear existing history for user
    db.query(WorkoutBlock).filter(WorkoutBlock.user_id == user.id).delete()
    
    # Create last 28 days
    start_history = today - timedelta(days=28)
    for i in range(28):
        date_obj = start_history + timedelta(days=i)
        
        wd = date_obj.weekday()
        w_type, duration = history_pattern.get(wd, ("Rest", 0))
        
        b = WorkoutBlock(
            user_id=user.id,
            date=date_obj.strftime("%Y-%m-%d"),
            type=w_type,
            planned_duration_minutes=duration,
            is_completed=True 
        )
        db.add(b)
            
    db.commit()
    print("History seeded (28 days).")
    
    db.close()
    print("Seed complete!")

if __name__ == "__main__":
    seed()
