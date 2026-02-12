from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    
    # Strava Credentials
    strava_access_token = Column(String, nullable=True)
    strava_refresh_token = Column(String, nullable=True)
    strava_expires_at = Column(Integer, nullable=True)
    
    # WHOOP Credentials
    whoop_access_token = Column(String, nullable=True)
    whoop_refresh_token = Column(String, nullable=True)
    whoop_expires_at = Column(Integer, nullable=True)

    activities = relationship("StravaActivity", back_populates="user")
    recoveries = relationship("WhoopRecovery", back_populates="user")
    training_plans = relationship("TrainingPlan", back_populates="user")

class StravaActivity(Base):
    __tablename__ = "strava_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    strava_id = Column(Integer, unique=True, index=True)
    name = Column(String)
    distance = Column(Float) # meters
    moving_time = Column(Integer) # seconds
    total_elevation_gain = Column(Float) # meters
    type = Column(String)
    start_date = Column(DateTime)
    average_heartrate = Column(Float, nullable=True)
    suffer_score = Column(Integer, nullable=True)

    user = relationship("User", back_populates="activities")

class WhoopRecovery(Base):
    __tablename__ = "whoop_recoveries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    whoop_id = Column(String, unique=True, index=True) # WHOOP IDs are strings
    date = Column(String) # YYYY-MM-DD
    recovery_score = Column(Integer)
    resting_heart_rate = Column(Integer)
    hrv = Column(Integer)
    sleep_performance = Column(Integer, nullable=True)

    user = relationship("User", back_populates="recoveries")

class TrainingPlan(Base):
    __tablename__ = "training_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    start_date = Column(String) # YYYY-MM-DD
    end_date = Column(String) # YYYY-MM-DD
    content = Column(JSON)
    feedback = Column(Text, nullable=True)

    user = relationship("User", back_populates="training_plans")
