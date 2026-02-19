"""
Coach Router — AI-powered training plan generation and editing.

Provides endpoints for generating multi-day rolling workout plans
and conversationally editing individual day plans via OpenAI.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
from ..schemas import TrainingPlanCreate
from ..database import get_db
from ..services import ai_coach
from ..models import User
from .auth import get_current_user

router = APIRouter()


class EditPlanRequest(BaseModel):
    """Request body for conversational plan editing."""
    day: str  # "today" or "tomorrow"
    messages: List[dict]  # [{"role": "user", "content": "..."}]


@router.post("/generate")
def generate_plan(plan_request: TrainingPlanCreate, db: Session = Depends(get_db)):
    """Generate a training plan from a specific date range request."""
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    plan = ai_coach.generate_training_plan(user, plan_request, db)
    return plan


@router.post("/plan-3-day")
def generate_rolling_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate or retrieve a rolling 2-day plan (today + tomorrow)."""
    plan = ai_coach.get_or_generate_rolling_plan(current_user, db)
    return plan


@router.post("/edit-plan")
def edit_plan(
    request: EditPlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Edit a day's plan via conversational chat with the AI coach."""
    if request.day not in ("today", "tomorrow"):
        raise HTTPException(status_code=400, detail="day must be 'today' or 'tomorrow'")
    result = ai_coach.edit_day_plan(current_user, db, request.day, request.messages)
    return result

