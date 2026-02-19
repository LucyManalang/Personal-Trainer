"""
Database models for the Personal Trainer application.

All models use SQLAlchemy ORM with SQLite backend. Heights are stored in cm,
weights in kg, and dates as YYYY-MM-DD strings or DateTime objects.
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Text, JSON
from datetime import datetime
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    """Core user model with profile, settings, cached plans, and OAuth tokens."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)

    # Profile
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    height = Column(Integer, nullable=True)  # cm
    weight = Column(Integer, nullable=True)  # kg
    openai_model = Column(String, default="gpt-4o")
    settings = Column(JSON, default={})

    # OAuth tokens
    strava_access_token = Column(String, nullable=True)
    strava_refresh_token = Column(String, nullable=True)
    strava_expires_at = Column(Integer, nullable=True)
    whoop_access_token = Column(String, nullable=True)
    whoop_refresh_token = Column(String, nullable=True)
    whoop_expires_at = Column(Integer, nullable=True)

    # Cached daily plan (rolling 2-day window)
    plan_today = Column(JSON, nullable=True)
    plan_tomorrow = Column(JSON, nullable=True)
    last_plan_date = Column(String, nullable=True)

    # Relationships
    activities = relationship("StravaActivity", back_populates="user")
    recoveries = relationship("WhoopRecovery", back_populates="user")
    training_plans = relationship("TrainingPlan", back_populates="user")
    goals = relationship("Goal", back_populates="user")
    workout_blocks = relationship("WorkoutBlock", back_populates="user")
    whoop_workouts = relationship("WhoopWorkout", back_populates="user")


class Goal(Base):
    """User goal — can be a dated event, preference, or short/long-term goal."""
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    description = Column(String)
    type = Column(String)  # 'short_term', 'long_term', 'preference', 'event', 'other'
    target_date = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")  # 'active', 'completed'

    user = relationship("User", back_populates="goals")


class StravaActivity(Base):
    """Synced activity from the Strava API."""
    __tablename__ = "strava_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    strava_id = Column(Integer, unique=True, index=True)
    name = Column(String)
    distance = Column(Float)  # meters
    moving_time = Column(Integer)  # seconds
    total_elevation_gain = Column(Float)  # meters
    type = Column(String)
    start_date = Column(DateTime)
    average_heartrate = Column(Float, nullable=True)
    suffer_score = Column(Integer, nullable=True)

    user = relationship("User", back_populates="activities")


class WhoopRecovery(Base):
    """Synced recovery score from the WHOOP API."""
    __tablename__ = "whoop_recoveries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    whoop_id = Column(String, unique=True, index=True)
    date = Column(String)  # YYYY-MM-DD
    recovery_score = Column(Integer)
    resting_heart_rate = Column(Integer)
    hrv = Column(Integer)
    sleep_performance = Column(Integer, nullable=True)

    user = relationship("User", back_populates="recoveries")


class TrainingPlan(Base):
    """AI-generated training plan for a date range."""
    __tablename__ = "training_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    start_date = Column(String)
    end_date = Column(String)
    content = Column(JSON)
    feedback = Column(Text, nullable=True)

    user = relationship("User", back_populates="training_plans")


class WorkoutBlock(Base):
    """Single day workout block in the weekly schedule."""
    __tablename__ = "workout_blocks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(String)  # YYYY-MM-DD
    type = Column(String)  # Gym, Running, Ultimate, Recovery, Rest, etc.
    planned_duration_minutes = Column(Integer)
    notes = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False)

    user = relationship("User", back_populates="workout_blocks")


class WhoopWorkout(Base):
    """Synced workout data from the WHOOP API."""
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
