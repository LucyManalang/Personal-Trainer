import requests
from datetime import datetime
from sqlalchemy.orm import Session
from ..models import User, StravaActivity
import os

STRAVA_API_URL = "https://www.strava.com/api/v3"

def refresh_strava_token(user: User, db: Session):
    url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": os.getenv("STRAVA_CLIENT_ID"),
        "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
        "refresh_token": user.strava_refresh_token,
        "grant_type": "refresh_token",
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        data = response.json()
        user.strava_access_token = data["access_token"]
        user.strava_refresh_token = data["refresh_token"]
        user.strava_expires_at = data["expires_at"]
        db.commit()
        return data["access_token"]
    return None

def fetch_activities(user: User, db: Session, limit: int = 30):
    # Check expiry
    # Note: strava_expires_at is unix timestamp
    import time
    if user.strava_expires_at and user.strava_expires_at < time.time():
        print("Refreshing Strava token...")
        refresh_strava_token(user, db)

    headers = {"Authorization": f"Bearer {user.strava_access_token}"}
    params = {"per_page": limit}
    
    response = requests.get(f"{STRAVA_API_URL}/athlete/activities", headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error fetching activities: {response.text}")
        return []

    activities_data = response.json()
    new_activities = []
    
    for activity in activities_data:
        # Check if exists
        existing = db.query(StravaActivity).filter(StravaActivity.strava_id == activity["id"]).first()
        if existing:
            continue
            
        # Parse date
        # Strava date format: 2018-02-16T14:52:54Z
        start_date = datetime.strptime(activity["start_date_local"], "%Y-%m-%dT%H:%M:%SZ")

        new_activity = StravaActivity(
            user_id=user.id,
            strava_id=activity["id"],
            name=activity["name"],
            distance=activity["distance"],
            moving_time=activity["moving_time"],
            total_elevation_gain=activity["total_elevation_gain"],
            type=activity["type"],
            start_date=start_date,
            average_heartrate=activity.get("average_heartrate"),
            suffer_score=activity.get("suffer_score")
        )
        db.add(new_activity)
        new_activities.append(new_activity)
    
    db.commit()
    return new_activities
