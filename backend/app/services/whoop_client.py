import requests
from datetime import datetime
from sqlalchemy.orm import Session
from ..models import User, WhoopRecovery
import os

WHOOP_API_URL = "https://api.prod.whoop.com/developer/v1"

def refresh_whoop_token(user: User, db: Session):
    url = "https://api.prod.whoop.com/oauth/oauth2/token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": user.whoop_refresh_token,
        "client_id": os.getenv("WHOOP_CLIENT_ID"),
        "client_secret": os.getenv("WHOOP_CLIENT_SECRET"),
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        data = response.json()
        user.whoop_access_token = data["access_token"]
        user.whoop_refresh_token = data["refresh_token"]
        user.whoop_expires_at = data["expires_in"] + 3600 # approximate
        db.commit()
        return data["access_token"]
    return None

def fetch_recoveries(user: User, db: Session, limit: int = 25):
    # Check expiry (simplified check)
    # In real world, check current time vs expires_at
    
    headers = {"Authorization": f"Bearer {user.whoop_access_token}"}
    params = {"limit": limit}

    # WHOOP Recovery Endpoint
    response = requests.get(f"{WHOOP_API_URL}/recovery", headers=headers, params=params)
    
    if response.status_code == 401:
        # Try refresh
        new_token = refresh_whoop_token(user, db)
        if new_token:
            headers = {"Authorization": f"Bearer {new_token}"}
            response = requests.get(f"{WHOOP_API_URL}/recovery", headers=headers, params=params)
    
    if response.status_code != 200:
        error_msg = f"WHOOP API Error: {response.text}"
        print(error_msg)
        raise Exception(error_msg)
        # return [] # Removed to ensure error bubbles up

    data = response.json()
    records = data.get("records", [])
    new_recoveries = []

    for record in records:
        # record has: id, user_id, created_at, updated_at, score_state, score, etc.
        # score has: recovery_score, resting_heart_rate, hrv_rmssd_milli
        
        rid = str(record["id"])
        existing = db.query(WhoopRecovery).filter(WhoopRecovery.whoop_id == rid).first()
        if existing:
            continue
            
        score = record.get("score", {})
        
        new_recovery = WhoopRecovery(
            user_id=user.id,
            whoop_id=rid,
            date=record.get("date"), # Check format usage
            recovery_score=score.get("recovery_score"),
            resting_heart_rate=score.get("resting_heart_rate"),
            hrv=score.get("hrv_rmssd_milli"),
            sleep_performance=score.get("sleep_performance_percentage") # Might be in a different endpoint, but checking here
        )
        db.add(new_recovery)
        new_recoveries.append(new_recovery)
        
    db.commit()
    return new_recoveries
