from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    class Config:
        from_attributes = True

# Strava Activity Schemas
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

# Whoop Recovery Schemas
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

# Training Plan Schemas
class TrainingPlanBase(BaseModel):
    start_date: str
    end_date: str
    content: Any # JSON
    feedback: Optional[str] = None

class TrainingPlanCreate(TrainingPlanBase):
    pass

class TrainingPlan(TrainingPlanBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True

# Goal Schemas
class GoalBase(BaseModel):
    description: str
    type: str # 'short_term' or 'long_term'
    status: Optional[str] = "active"

class GoalCreate(GoalBase):
    pass

class Goal(GoalBase):
    id: int
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Workout Block Schemas
class WorkoutBlockBase(BaseModel):
    date: str # YYYY-MM-DD
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

# Whoop Workout Schemas
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
