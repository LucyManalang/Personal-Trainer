from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import random
from app.models import User, WhoopRecovery
from app.database import SQLALCHEMY_DATABASE_URL

# Setup database connection
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def seed_recoveries():
    user = db.query(User).first()
    if not user:
        print("No user found! Please run the app to create a user first.")
        return

    print(f"Seeding recoveries for User: {user.email}")

    # Generate last 30 days of data
    today = datetime.now()
    
    count = 0
    for i in range(30):
        date_obj = today - timedelta(days=i)
        date_str = date_obj.strftime("%Y-%m-%d")
        
        # Check if exists
        existing = db.query(WhoopRecovery).filter(
            WhoopRecovery.user_id == user.id,
            WhoopRecovery.date == date_str
        ).first()
        
        if existing:
            continue
            
        # Create mock data
        recovery_score = random.randint(30, 99)
        rhr = random.randint(45, 65)
        hrv = random.randint(40, 120)
        sleep_perf = random.randint(70, 100)
        
        recovery = WhoopRecovery(
            user_id=user.id,
            whoop_id=f"seed_{date_str}",
            date=date_str,
            recovery_score=recovery_score,
            resting_heart_rate=rhr,
            hrv=hrv,
            sleep_performance=sleep_perf
        )
        db.add(recovery)
        count += 1
        
    db.commit()
    print(f"Successfully added {count} recovery records.")
    db.close()

if __name__ == "__main__":
    seed_recoveries()
