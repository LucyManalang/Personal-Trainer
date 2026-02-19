"""
Data Router — Goals CRUD and user schedule management.

Also provides sync endpoints for Strava activities and WHOOP recoveries.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Goal
from ..services import strava_client, whoop_client
from ..schemas import GoalCreate, GoalUpdate, Goal as GoalSchema

router = APIRouter()


@router.get("/goals", response_model=list[GoalSchema])
def get_goals(db: Session = Depends(get_db)):
    """Return all goals for the current user."""
    user = db.query(User).first()
    if not user:
        return []
    return db.query(Goal).filter(Goal.user_id == user.id).all()


@router.post("/goals", response_model=GoalSchema)
def create_goal(goal: GoalCreate, db: Session = Depends(get_db)):
    """Create a new goal."""
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_goal = Goal(
        user_id=user.id,
        description=goal.description,
        type=goal.type,
        status=goal.status,
        target_date=goal.target_date,
        is_completed=goal.is_completed
    )
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal


@router.put("/goals/{goal_id}", response_model=GoalSchema)
def update_goal(goal_id: int, goal_update: GoalUpdate, db: Session = Depends(get_db)):
    """Update an existing goal's fields."""
    db_goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not db_goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    if goal_update.description is not None: db_goal.description = goal_update.description
    if goal_update.type is not None: db_goal.type = goal_update.type
    if goal_update.status is not None: db_goal.status = goal_update.status
    if goal_update.target_date is not None: db_goal.target_date = goal_update.target_date
    if goal_update.is_completed is not None:
        db_goal.is_completed = goal_update.is_completed
        db_goal.status = "completed" if goal_update.is_completed else "active"

    db.commit()
    db.refresh(db_goal)
    return db_goal


@router.delete("/goals/{goal_id}")
def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    """Delete a goal by ID."""
    db_goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not db_goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    db.delete(db_goal)
    db.commit()
    return {"message": "Goal deleted"}


# --- User Schedule (stored in user.settings["schedule"]) ---

@router.get("/schedule")
def get_schedule(db: Session = Depends(get_db)):
    """Return the user's saved weekly schedule template."""
    user = db.query(User).first()
    if not user:
        return {"schedule": {}}
    settings = user.settings or {}
    return {"schedule": settings.get("schedule", {})}


@router.put("/schedule")
def update_schedule(body: dict, db: Session = Depends(get_db)):
    """Save the user's weekly schedule template (Mon-Sun activity types and durations)."""
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    schedule_data = body.get("schedule", {})
    settings = dict(user.settings or {})
    settings["schedule"] = schedule_data
    user.settings = settings

    db.commit()
    db.refresh(user)
    return {"schedule": settings["schedule"]}


# --- External Service Sync ---

@router.post("/sync/strava")
def sync_strava(db: Session = Depends(get_db)):
    """Sync recent activities from Strava."""
    user = db.query(User).first()
    if not user or not user.strava_access_token:
        raise HTTPException(status_code=401, detail="User not authenticated with Strava")

    activities = strava_client.fetch_activities(user, db)
    return {"message": f"Synced {len(activities)} new activities", "count": len(activities)}


@router.post("/sync/whoop")
def sync_whoop(db: Session = Depends(get_db)):
    """Sync recent recoveries from WHOOP."""
    user = db.query(User).first()
    if not user or not user.whoop_access_token:
        raise HTTPException(status_code=401, detail="User not authenticated with WHOOP")

    try:
        recoveries = whoop_client.fetch_recoveries(user, db)
        return {"message": f"Synced {len(recoveries)} new recoveries", "count": len(recoveries)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
