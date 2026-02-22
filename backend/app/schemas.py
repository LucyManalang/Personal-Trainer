"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


# --- User ---

class UserBase(BaseModel):
    email: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    openai_model: Optional[str] = "gpt-5-mini"
    settings: Optional[Any] = {}
    strava_access_token: Optional[str] = None
    whoop_access_token: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    openai_model: Optional[str] = None
    settings: Optional[Any] = None

class User(UserBase):
    id: int
    class Config:
        from_attributes = True


# --- Strava Activity ---

class StravaActivityBase(BaseModel):
    strava_id: int
    name: str
    distance: float
    moving_time: int
    total_elevation_gain: float
    type: str
    start_date: datetime
    average_heartrate: Optional[float] = None
    suffer_score: Optional[int] = None

class StravaActivityCreate(StravaActivityBase):
    pass

class StravaActivity(StravaActivityBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True


# --- WHOOP Recovery ---

class WhoopRecoveryBase(BaseModel):
    whoop_id: str
    date: str
    recovery_score: int
    resting_heart_rate: int
    hrv: int
    sleep_performance: Optional[int] = None

class WhoopRecoveryCreate(WhoopRecoveryBase):
    pass

class WhoopRecovery(WhoopRecoveryBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True


# --- Training Plan ---

class TrainingPlanBase(BaseModel):
    start_date: str
    end_date: str
    content: Any
    feedback: Optional[str] = None

class TrainingPlanCreate(TrainingPlanBase):
    pass

class TrainingPlan(TrainingPlanBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True


# --- Goal ---

class GoalBase(BaseModel):
    description: str
    type: str
    status: Optional[str] = "active"
    target_date: Optional[datetime] = None
    is_completed: Optional[bool] = False

class GoalCreate(GoalBase):
    pass

class GoalUpdate(BaseModel):
    description: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    target_date: Optional[datetime] = None
    is_completed: Optional[bool] = None

class Goal(GoalBase):
    id: int
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True


# --- Workout Block ---

class WorkoutBlockBase(BaseModel):
    date: str
    type: str
    planned_duration_minutes: int
    notes: Optional[str] = None
    is_completed: Optional[bool] = False

class WorkoutBlockCreate(WorkoutBlockBase):
    pass

class WorkoutBlock(WorkoutBlockBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True


# --- WHOOP Workout ---

class WhoopWorkoutBase(BaseModel):
    whoop_id: str
    sport_name: str
    start: datetime
    end: datetime
    timezone_offset: Optional[str] = None
    strain: float
    average_heart_rate: int
    max_heart_rate: int
    kilojoules: float
    zone_durations: Optional[Any] = None

class WhoopWorkoutCreate(WhoopWorkoutBase):
    pass

class WhoopWorkout(WhoopWorkoutBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True
