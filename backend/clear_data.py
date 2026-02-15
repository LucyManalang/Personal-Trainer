import sys
import os

# Add project root to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app.models import Goal, WorkoutBlock, TrainingPlan

def clear_data():
    db = SessionLocal()
    print("Clearing seed data...")
    
    # Clear Goals
    deleted_goals = db.query(Goal).delete()
    print(f"Deleted {deleted_goals} goals.")
    
    # Clear Workout Blocks
    deleted_blocks = db.query(WorkoutBlock).delete()
    print(f"Deleted {deleted_blocks} workout blocks.")
    
    # Clear Training Plans
    deleted_plans = db.query(TrainingPlan).delete()
    print(f"Deleted {deleted_plans} training plans.")
    
    db.commit()
    db.close()
    print("Data cleared manually.")

if __name__ == "__main__":
    clear_data()
