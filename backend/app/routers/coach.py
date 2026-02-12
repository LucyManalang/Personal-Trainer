from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..schemas import TrainingPlanCreate
from ..database import get_db

from ..services import ai_coach
from ..models import User

router = APIRouter()

@router.post("/generate")
def generate_plan(plan_request: TrainingPlanCreate, db: Session = Depends(get_db)):
    user = db.query(User).first()
    # If no user, mock one for testing or raise error
    if not user:
        # For testing purposes allow generation without full auth if needed, but better to enforce
        # raise HTTPException(status_code=401, detail="User not found")
        pass 
        
    plan = ai_coach.generate_training_plan(user, plan_request, db)
    return plan
