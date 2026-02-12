from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import User
from app.database import SQLALCHEMY_DATABASE_URL
from app.services import whoop_client

# Setup database connection
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def debug_sync():
    user = db.query(User).first()
    if not user:
        print("No user found")
        return

    print(f"Testing WHOOP sync for user: {user.email}")
    print(f"Current Access Token: {user.whoop_access_token[:10]}...")
    
    # This calls existing logic which prints errors to stdout
    recoveries = whoop_client.fetch_recoveries(user, db)
    print(f"Recoveries returned: {len(recoveries)}")

if __name__ == "__main__":
    debug_sync()
