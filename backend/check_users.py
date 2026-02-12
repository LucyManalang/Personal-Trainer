from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import User
from app.database import SQLALCHEMY_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_users():
    db = SessionLocal()
    users = db.query(User).all()
    print(f"Found {len(users)} users.")
    for user in users:
        print(f"User ID: {user.id}, Email: {user.email}")
        print(f"  Strava Token: {'Set' if user.strava_access_token else 'None'}")
        print(f"  Whoop Token: {'Set' if user.whoop_access_token else 'None'}")
        print(f"  Recoveries count: {len(user.recoveries)}")
    db.close()

if __name__ == "__main__":
    check_users()
