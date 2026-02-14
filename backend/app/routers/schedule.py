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
    start_date = today + timedelta(days=1)
    
    new_blocks = []
    default_schedule = {
        0: ("Cardio", 45),       # Mon
        1: ("Strength", 60),     # Tue
        2: ("Cardio", 45),       # Wed
        3: ("Strength", 60),     # Thu
        4: ("Cardio", 45),       # Fri
        5: ("Long Cardio", 90),  # Sat
        6: ("Recovery", 30)      # Sun
    }

    for i in range(7):
        date_obj = start_date + timedelta(days=i)
        date_str = date_obj.strftime("%Y-%m-%d")
        
        # Check if exists
        existing = db.query(WorkoutBlock).filter(
            WorkoutBlock.user_id == current_user.id,
            WorkoutBlock.date == date_str
        ).first()
        
        if existing:
            continue
            
        weekday = date_obj.weekday()
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
