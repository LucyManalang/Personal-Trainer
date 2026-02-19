"""
Schedule Router — Workout block initialization and management.

Provides endpoints to initialize/reset the weekly workout schedule,
retrieve scheduled blocks, and update individual blocks.
"""

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
    Reset and initialize workout blocks for the next 7 days starting today.
    Uses the user's saved schedule from settings, falling back to a
    hardcoded default if none is configured.
    """
    today = datetime.now().date()
    start_date = today

    new_blocks = []

    hardcoded_schedule = {
        0: ("Gym", 60),
        1: ("Ultimate", 120),
        2: ("Running", 45),
        3: ("Gym", 60),
        4: ("Running", 45),
        5: ("Running", 60),
        6: ("Ultimate", 120)
    }

    user_settings = current_user.settings or {}
    saved_schedule = user_settings.get("schedule", {})

    if saved_schedule:
        default_schedule = {}
        for k, v in saved_schedule.items():
            default_schedule[int(k)] = (v[0], int(v[1]))
    else:
        default_schedule = hardcoded_schedule

    for i in range(7):
        date_obj = start_date + timedelta(days=i)
        date_str = date_obj.strftime("%Y-%m-%d")

        db.query(WorkoutBlock).filter(
            WorkoutBlock.user_id == current_user.id,
            WorkoutBlock.date == date_str
        ).delete()

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
    """
    Retrieve workout blocks filtered by date range. Defaults to a 7-day
    window starting today. Automatically creates blocks for any missing
    days using the user's saved schedule, without overwriting existing blocks.
    """
    today = datetime.now().date()
    range_start = start_date or today.strftime("%Y-%m-%d")
    range_end = end_date or (today + timedelta(days=6)).strftime("%Y-%m-%d")

    # Auto-fill missing days in the 7-day window
    hardcoded_schedule = {
        0: ("Gym", 60), 1: ("Ultimate", 120), 2: ("Running", 45),
        3: ("Gym", 60), 4: ("Running", 45), 5: ("Running", 60),
        6: ("Ultimate", 120)
    }

    user_settings = current_user.settings or {}
    saved_schedule = user_settings.get("schedule", {})

    if saved_schedule:
        default_schedule = {int(k): (v[0], int(v[1])) for k, v in saved_schedule.items()}
    else:
        default_schedule = hardcoded_schedule

    existing_dates = {
        b.date for b in db.query(WorkoutBlock).filter(
            WorkoutBlock.user_id == current_user.id,
            WorkoutBlock.date >= range_start,
            WorkoutBlock.date <= range_end
        ).all()
    }

    created = False
    for i in range(7):
        date_obj = today + timedelta(days=i)
        date_str = date_obj.strftime("%Y-%m-%d")
        if date_str not in existing_dates:
            weekday = date_obj.weekday()
            w_type, duration = default_schedule.get(weekday, ("Rest", 0))
            db.add(WorkoutBlock(
                user_id=current_user.id,
                date=date_str,
                type=w_type,
                planned_duration_minutes=duration,
                is_completed=False
            ))
            created = True

    if created:
        db.commit()

    query = db.query(WorkoutBlock).filter(
        WorkoutBlock.user_id == current_user.id,
        WorkoutBlock.date >= range_start,
        WorkoutBlock.date <= range_end
    )
    return query.order_by(WorkoutBlock.date).all()


@router.put("/{block_id}", response_model=WorkoutBlockSchema)
def update_block(
    block_id: int,
    block_update: WorkoutBlockCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a specific workout block's type, duration, notes, or completion status."""
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
