import requests
from datetime import datetime
from sqlalchemy.orm import Session
from ..models import User, WhoopRecovery, WhoopWorkout
import os

WHOOP_API_URL = "https://api.prod.whoop.com/developer/v2"

def refresh_whoop_token(user: User, db: Session):
    if not user.whoop_refresh_token:
        print("DEBUG: No refresh token available for user.")
        return None

    url = "https://api.prod.whoop.com/oauth/oauth2/token"
    # print(f"DEBUG: Refresh Token present? {bool(user.whoop_refresh_token)}")
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": user.whoop_refresh_token,
        "client_id": os.getenv("WHOOP_CLIENT_ID"),
        "client_secret": os.getenv("WHOOP_CLIENT_SECRET"),
        "scope": "read:recovery read:cycles read:workout read:sleep read:profile offline",
        "redirect_uri": "http://localhost:8000/auth/whoop/callback",
    }
    
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        data = response.json()
        user.whoop_access_token = data["access_token"]
        user.whoop_refresh_token = data["refresh_token"]
        user.whoop_expires_at = data["expires_in"] + 3600 # approximate
        db.commit()
        return data["access_token"]
    else:
        print(f"Failed to refresh WHOOP token: {response.text}")
    return None

def fetch_recoveries(user: User, db: Session, limit: int = 25):
    headers = {"Authorization": f"Bearer {user.whoop_access_token}"}
    params = {"limit": limit}

    # WHOOP V2 Recovery Endpoint
    print(f"DEBUG: Fetching recoveries from v2 endpoint...")
    response_recovery = requests.get(f"{WHOOP_API_URL}/recovery", headers=headers, params=params)
    
    # WHOOP V2 Sleep Endpoint
    print(f"DEBUG: Fetching sleep data from v2 endpoint...")
    response_sleep = requests.get(f"{WHOOP_API_URL}/activity/sleep", headers=headers, params=params)

    if response_recovery.status_code == 401 or response_sleep.status_code == 401:
        print("DEBUG: Token expired (401). Attempting refresh...")
        new_token = refresh_whoop_token(user, db)
        if new_token:
            print(f"DEBUG: Refresh successful.")
            headers = {"Authorization": f"Bearer {new_token}"}
            response_recovery = requests.get(f"{WHOOP_API_URL}/recovery", headers=headers, params=params)
            response_sleep = requests.get(f"{WHOOP_API_URL}/activity/sleep", headers=headers, params=params)
    
    if response_recovery.status_code != 200:
        error_msg = f"WHOOP Recovery API Error: {response_recovery.text}"
        print(error_msg)
        raise Exception(error_msg)
        
    if response_sleep.status_code != 200:
        # Sleep might fail if no sleep data? But usually just returns empty list.
        # Log warning but proceed with just recovery data if strictly necessary?
        # For now, treat as error to ensure we debug if it fails.
        error_msg = f"WHOOP Sleep API Error: {response_sleep.text}"
        print(error_msg)
        # raise Exception(error_msg) # Soft fail for sleep

    recovery_data = response_recovery.json()
    recovery_records = recovery_data.get("records", [])
    
    sleep_data = response_sleep.json() if response_sleep.status_code == 200 else {}
    sleep_records = sleep_data.get("records", [])
    
    # Map sleep data by cycle_id for easy lookup
    sleep_map = {}
    for s in sleep_records:
        cid = s.get("cycle_id")
        if cid:
            sleep_map[cid] = s

    print(f"DEBUG: Fetched {len(recovery_records)} recoveries and {len(sleep_records)} sleeps.")
    new_recoveries = []

    for record in recovery_records:
        score = record.get("score")
        if not score:
             continue
        
        # Use cycle_id as unique ID for recovery table
        cycle_id = record.get("cycle_id")
        rid = str(cycle_id)
        
        # Look up sleep data
        sleep_record = sleep_map.get(cycle_id)
        sleep_perf = None
        if sleep_record:
            sleep_score = sleep_record.get("score", {})
            sleep_perf = sleep_score.get("sleep_performance_percentage")
        
        existing = db.query(WhoopRecovery).filter(WhoopRecovery.whoop_id == rid).first()
        if existing:
            # Update existing if sleep performance is missing?
            if existing.sleep_performance is None and sleep_perf is not None:
                existing.sleep_performance = sleep_perf
                db.add(existing) # Mark for update
            continue
            
        # Date: Use created_at
        created_at = record.get("created_at")
        date_str = created_at.split("T")[0] if created_at else None

        new_recovery = WhoopRecovery(
            user_id=user.id,
            whoop_id=rid,
            date=date_str,
            recovery_score=score.get("recovery_score"),
            resting_heart_rate=score.get("resting_heart_rate"),
            hrv=score.get("hrv_rmssd_milli"),
            sleep_performance=sleep_perf
        )
        db.add(new_recovery)
        new_recoveries.append(new_recovery)
        
    db.commit()
    return new_recoveries

def fetch_workouts(user: User, db: Session, limit: int = 25):
    headers = {"Authorization": f"Bearer {user.whoop_access_token}"}
    params = {"limit": limit}

    print(f"DEBUG: Fetching workouts from v2 endpoint...")
    response = requests.get(f"{WHOOP_API_URL}/activity/workout", headers=headers, params=params)

    if response.status_code == 401:
        print("DEBUG: Token expired (401). Attempting refresh...")
        new_token = refresh_whoop_token(user, db)
        if new_token:
            print(f"DEBUG: Refresh successful.")
            headers = {"Authorization": f"Bearer {new_token}"}
            response = requests.get(f"{WHOOP_API_URL}/activity/workout", headers=headers, params=params)

    if response.status_code != 200:
        error_msg = f"WHOOP Workout API Error: {response.text}"
        print(error_msg)
        raise Exception(error_msg)
    
    data = response.json()
    records = data.get("records", [])
    print(f"DEBUG: Fetched {len(records)} workouts.")
    new_workouts = []

    for record in records:
        # Check existence
        wid = str(record.get("id"))
        existing = db.query(WhoopWorkout).filter(WhoopWorkout.whoop_id == wid).first()
        if existing:
            continue
            
        score = record.get("score", {})
        
        # Parse dates
        start_str = record.get("start")
        end_str = record.get("end")
        start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00")) if start_str else None
        end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00")) if end_str else None

        new_workout = WhoopWorkout(
            user_id=user.id,
            whoop_id=wid,
            sport_name=record.get("sport_name"),
            start=start_dt,
            end=end_dt,
            timezone_offset=record.get("timezone_offset"),
            strain=score.get("strain"),
            average_heart_rate=score.get("average_heart_rate"),
            max_heart_rate=score.get("max_heart_rate"),
            kilojoules=score.get("kilojoule"),
            zone_durations=score.get("zone_durations")
        )
        db.add(new_workout)
        new_workouts.append(new_workout)
    
    db.commit()
    return new_workouts
