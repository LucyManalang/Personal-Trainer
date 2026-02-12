from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..services import strava_client, whoop_client

router = APIRouter()

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
