from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Text, JSON
from datetime import datetime
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    
    # User Settings & Profile
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True) # "Male", "Female", "Other"
    height = Column(Integer, nullable=True) # cm
    weight = Column(Integer, nullable=True) # kg
    openai_model = Column(String, default="gpt-4o")
    settings = Column(JSON, default={}) # For flexible preferences
    
    # Daily Plan Persistence (Rolling 2-day window)
    plan_today = Column(JSON, nullable=True)
    plan_tomorrow = Column(JSON, nullable=True)
    last_plan_date = Column(String, nullable=True) # YYYY-MM-DD

    activities = relationship("StravaActivity", back_populates="user")
    recoveries = relationship("WhoopRecovery", back_populates="user")
    training_plans = relationship("TrainingPlan", back_populates="user")
    goals = relationship("Goal", back_populates="user")
    workout_blocks = relationship("WorkoutBlock", back_populates="user")
    whoop_workouts = relationship("WhoopWorkout", back_populates="user")


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    description = Column(String)
    type = Column(String) # 'short_term' or 'long_term' (or 'dated'/'undated' logic handled in frontend/service)
    target_date = Column(DateTime, nullable=True) # For event-based goals
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active") # active, completed, abandoned (redundant with is_completed? let's keep status for legacy or more states)

    user = relationship("User", back_populates="goals")

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


class WorkoutBlock(Base):
    __tablename__ = "workout_blocks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(String) # YYYY-MM-DD
    type = Column(String) # Strength, Cardio, Recovery, etc.
    planned_duration_minutes = Column(Integer)
    notes = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="workout_blocks")

class WhoopWorkout(Base):
    __tablename__ = "whoop_workouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    whoop_id = Column(String, unique=True, index=True)
    sport_name = Column(String)
    start = Column(DateTime)
    end = Column(DateTime)
    timezone_offset = Column(String, nullable=True)
    strain = Column(Float)
    average_heart_rate = Column(Integer)
    max_heart_rate = Column(Integer)
    kilojoules = Column(Float)
    zone_durations = Column(JSON, nullable=True)
    
    user = relationship("User", back_populates="whoop_workouts")
