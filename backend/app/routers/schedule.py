from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from ..database import get_db
from ..models import User, WorkoutBlock
from ..schemas import WorkoutBlock as WorkoutBlockSchema, WorkoutBlockCreate
from .auth import get_current_user

router = APIRouter()

@router.post("/init", response_model=List[WorkoutBlockSchema])
def initialize_weekly_schedule(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initialize workout blocks for the next 7 days if they don't exist.
    Default pattern: 
    - Mon: Cardio
    - Tue: Strength
    - Wed: Cardio
    - Thu: Strength
    - Fri: Cardio
    - Sat: Long Cardio
    - Sun: Recovery
    """
    today = datetime.now().date()
    start_date = today + timedelta(days=(7 - today.weekday())) # Next Monday
    # actually user said "next week", but technically could just be next 7 days. 
    # Let's just do next 7 days from tomorrow for simplicity or next Monday?
    # User said "at the beginning of each week... for the next week". 
    # Let's do next 7 days starting tomorrow to be safe/immediately useful.
    start_date = today
    
    new_blocks = []
    
    # Try to load user-defined schedule from settings, fall back to hardcoded default
    hardcoded_schedule = {
        0: ("Gym", 60),          # Mon
        1: ("Ultimate", 120),    # Tue
        2: ("Running", 45),      # Wed
        3: ("Gym", 60),          # Thu
        4: ("Running", 45),      # Fri
        5: ("Running", 60),      # Sat
        6: ("Ultimate", 120)     # Sun
    }
    
    user_settings = current_user.settings or {}
    saved_schedule = user_settings.get("schedule", {})
    
    if saved_schedule:
        # Convert stored format {"0": ["Gym", 60], ...} → {0: ("Gym", 60), ...}
        default_schedule = {}
        for k, v in saved_schedule.items():
            default_schedule[int(k)] = (v[0], int(v[1]))
    else:
        default_schedule = hardcoded_schedule

    for i in range(7):
        date_obj = start_date + timedelta(days=i)
        date_str = date_obj.strftime("%Y-%m-%d")
        
        # Delete any existing block for this date so reset truly resets
        db.query(WorkoutBlock).filter(
            WorkoutBlock.user_id == current_user.id,
            WorkoutBlock.date == date_str
        ).delete()
            
        weekday = date_obj.weekday()
        
        # History-based estimation: Look at last 4 weeks
        # DISABLE HISTORY FOR RESET: User wants a clean slate based on preferences (Default Dictionary)
        # 1. Check local WorkoutBlock history
        # past_dates = [(date_obj - timedelta(weeks=w)).strftime("%Y-%m-%d") for w in range(1, 5)]
        
        # history = db.query(WorkoutBlock).filter(
        #     WorkoutBlock.user_id == current_user.id,
        #     WorkoutBlock.date.in_(past_dates)
        # ).all()
        
        # if history:
        #     # Find most common type
        #     types = [b.type for b in history]
        #     w_type = max(set(types), key=types.count)
        #     # Avg duration
        #     durations = [b.planned_duration_minutes for b in history if b.type == w_type]
        #     duration = sum(durations) // len(durations)
        # else:
            # 2. Check Strava/Whoop History (Fallback if no local blocks)
            # ... (Skipping complex fallback to ensure clean reset)
            
        # 3. Use Default Pattern strictly
        w_type, duration = default_schedule.get(weekday, ("Rest", 0))
        
        block = WorkoutBlock(
            user_id=current_user.id,
            date=date_str,
            type=w_type,
            planned_duration_minutes=duration,
            is_completed=False
        )
        db.add(block)
        new_blocks.append(block)
    
    db.commit()
    
    # Return all blocks for the period
    all_blocks = db.query(WorkoutBlock).filter(
        WorkoutBlock.user_id == current_user.id,
        WorkoutBlock.date >= start_date.strftime("%Y-%m-%d"),
        WorkoutBlock.date <= (start_date + timedelta(days=6)).strftime("%Y-%m-%d")
    ).all()
    
    return all_blocks

@router.get("/", response_model=List[WorkoutBlockSchema])
def get_schedule(
    start_date: str = None,
    end_date: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(WorkoutBlock).filter(WorkoutBlock.user_id == current_user.id)
    
    if start_date:
        query = query.filter(WorkoutBlock.date >= start_date)
    else:
        # Default to today onwards
        query = query.filter(WorkoutBlock.date >= datetime.now().strftime("%Y-%m-%d"))
        
    if end_date:
        query = query.filter(WorkoutBlock.date <= end_date)
        
    return query.order_by(WorkoutBlock.date).all()

@router.put("/{block_id}", response_model=WorkoutBlockSchema)
def update_block(
    block_id: int,
    block_update: WorkoutBlockCreate, # Re-using create schema for simplicity, or should define Update schema
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    block = db.query(WorkoutBlock).filter(
        WorkoutBlock.id == block_id,
        WorkoutBlock.user_id == current_user.id
    ).first()
    
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
        
    block.type = block_update.type
    block.planned_duration_minutes = block_update.planned_duration_minutes
    block.notes = block_update.notes
    block.is_completed = block_update.is_completed
    
    db.commit()
    db.refresh(block)
    return block
