"""
WHOOP API client — token refresh, recovery syncing, and workout syncing.
"""

import os
import time
import requests
from datetime import datetime
from sqlalchemy.orm import Session
from ..models import User, WhoopRecovery, WhoopWorkout

WHOOP_API_URL = "https://api.prod.whoop.com/developer/v2"


def refresh_whoop_token(user: User, db: Session):
    """Refresh the user's WHOOP OAuth access token using the stored refresh token."""
    if not user.whoop_refresh_token:
        return None

    url = "https://api.prod.whoop.com/oauth/oauth2/token"
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
        user.whoop_expires_at = int(time.time()) + data.get("expires_in", 3600)
        db.commit()
        return data["access_token"]
    return None


def fetch_recoveries(user: User, db: Session, limit: int = 25):
    """
    Fetch recent recovery and sleep data from WHOOP.
    Automatically retries with a refreshed token on 401 responses.
    Joins sleep performance data with recovery records by cycle_id.
    """
    headers = {"Authorization": f"Bearer {user.whoop_access_token}"}
    params = {"limit": limit}

    response_recovery = requests.get(f"{WHOOP_API_URL}/recovery", headers=headers, params=params)
    response_sleep = requests.get(f"{WHOOP_API_URL}/activity/sleep", headers=headers, params=params)

    if response_recovery.status_code == 401 or response_sleep.status_code == 401:
        new_token = refresh_whoop_token(user, db)
        if new_token:
            headers = {"Authorization": f"Bearer {new_token}"}
            response_recovery = requests.get(f"{WHOOP_API_URL}/recovery", headers=headers, params=params)
            response_sleep = requests.get(f"{WHOOP_API_URL}/activity/sleep", headers=headers, params=params)

    if response_recovery.status_code != 200:
        raise Exception(f"WHOOP Recovery API Error: {response_recovery.text}")

    recovery_data = response_recovery.json()
    recovery_records = recovery_data.get("records", [])

    sleep_data = response_sleep.json() if response_sleep.status_code == 200 else {}
    sleep_records = sleep_data.get("records", [])

    sleep_map = {}
    for s in sleep_records:
        cid = s.get("cycle_id")
        if cid:
            sleep_map[cid] = s

    new_recoveries = []

    for record in recovery_records:
        score = record.get("score")
        if not score:
            continue

        cycle_id = record.get("cycle_id")
        rid = str(cycle_id)

        sleep_record = sleep_map.get(cycle_id)
        sleep_perf = None
        if sleep_record:
            sleep_score = sleep_record.get("score", {})
            sleep_perf = sleep_score.get("sleep_performance_percentage")

        existing = db.query(WhoopRecovery).filter(WhoopRecovery.whoop_id == rid).first()
        if existing:
            if existing.sleep_performance is None and sleep_perf is not None:
                existing.sleep_performance = sleep_perf
                db.add(existing)
            continue

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
    """
    Fetch recent workouts from WHOOP.
    Automatically retries with a refreshed token on 401 responses.
    """
    headers = {"Authorization": f"Bearer {user.whoop_access_token}"}
    params = {"limit": limit}

    response = requests.get(f"{WHOOP_API_URL}/activity/workout", headers=headers, params=params)

    if response.status_code == 401:
        new_token = refresh_whoop_token(user, db)
        if new_token:
            headers = {"Authorization": f"Bearer {new_token}"}
            response = requests.get(f"{WHOOP_API_URL}/activity/workout", headers=headers, params=params)

    if response.status_code != 200:
        raise Exception(f"WHOOP Workout API Error: {response.text}")

    data = response.json()
    records = data.get("records", [])
    new_workouts = []

    for record in records:
        wid = str(record.get("id"))
        existing = db.query(WhoopWorkout).filter(WhoopWorkout.whoop_id == wid).first()
        if existing:
            continue

        score = record.get("score", {})

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
