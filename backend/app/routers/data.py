from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Goal
from ..services import strava_client, whoop_client
from ..schemas import GoalCreate, GoalUpdate, Goal as GoalSchema

router = APIRouter()

@router.get("/goals", response_model=list[GoalSchema])
def get_goals(db: Session = Depends(get_db)):
    # Assuming single user for now or getting first user
    user = db.query(User).first()
    if not user:
        return []
    # Return all goals so frontend can sort/filter (or just active/completed? Let's return active + completed to show history if needed, but user said remove via checkbox. 
    # Valid "active" strategy: return all that are NOT 'abandoned' or deleted.
    # The delete endpoint actually deletes.
    # So let's return everything.
    return db.query(Goal).filter(Goal.user_id == user.id).all()

@router.post("/goals", response_model=GoalSchema)
def create_goal(goal: GoalCreate, db: Session = Depends(get_db)):
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
    db_goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not db_goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    if goal_update.description is not None: db_goal.description = goal_update.description
    if goal_update.type is not None: db_goal.type = goal_update.type
    if goal_update.status is not None: db_goal.status = goal_update.status
    if goal_update.target_date is not None: db_goal.target_date = goal_update.target_date
    if goal_update.is_completed is not None: 
        db_goal.is_completed = goal_update.is_completed
        if goal_update.is_completed:
            db_goal.status = "completed"
        else:
            db_goal.status = "active"
    
    db.commit()
    db.refresh(db_goal)
    return db_goal

@router.delete("/goals/{goal_id}")
def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    db_goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not db_goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    db.delete(db_goal)
    db.commit()
    return {"message": "Goal deleted"}

@router.post("/sync/strava")
def sync_strava(db: Session = Depends(get_db)):
    # Get first user for now
    user = db.query(User).first()
    if not user or not user.strava_access_token:
        raise HTTPException(status_code=401, detail="User not authenticated with Strava")
    
    activities = strava_client.fetch_activities(user, db)
    return {"message": f"Synced {len(activities)} new activities", "count": len(activities)}


@router.post("/sync/whoop")
def sync_whoop(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user or not user.whoop_access_token:
        raise HTTPException(status_code=401, detail="User not authenticated with WHOOP")
    
    try:
        recoveries = whoop_client.fetch_recoveries(user, db)
        return {"message": f"Synced {len(recoveries)} new recoveries", "count": len(recoveries)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
