import os
import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
WHOOP_CLIENT_ID = os.getenv("WHOOP_CLIENT_ID")
WHOOP_CLIENT_SECRET = os.getenv("WHOOP_CLIENT_SECRET")

# Strava
@router.get("/strava/login")
def strava_login():
    redirect_uri = "http://localhost:8000/auth/strava/callback"
    scope = "read,activity:read_all"
    url = (
        f"https://www.strava.com/oauth/authorize"
        f"?client_id={STRAVA_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&approval_prompt=force"
        f"&scope={scope}"
    )
    return RedirectResponse(url)

@router.get("/strava/callback")
def strava_callback(code: str, db: Session = Depends(get_db)):
    token_url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
    }
    
    response = requests.post(token_url, data=payload)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to retrieve Strava token")
    
    data = response.json()
    
    # Check if user exists (mocking 'current user' logic by using email or just creating single user for now)
    # Since this is a personal tool, we can assume a single user or identifying by athlete_id if we want multi-user
    # For now, let's just make/update the first user record found or create new.
    
    athlete = data.get("athlete", {})
    # In a real app we'd probably use a JWT and link accounts. 
    # Here, we'll store the Strava athlete ID or update the first user.
    
    # Simple Logic: Check if we have any user, if not create one. Determine identity later.
    user = db.query(User).first()
    if not user:
        user = User(email="user@example.com") # Placeholder email
        db.add(user)
        db.commit()
        db.refresh(user)
        
    user.strava_access_token = data["access_token"]
    user.strava_refresh_token = data["refresh_token"]
    user.strava_expires_at = data["expires_at"]
    
    db.commit()
    
    return {"message": "Strava connected successfully", "athlete": athlete}

# WHOOP
@router.get("/whoop/login")
def whoop_login():
    redirect_uri = "http://localhost:8000/auth/whoop/callback"
    scope = "read:recovery read:sleep"
    # Generate a random state string (must be at least 8 chars)
    import secrets
    state = secrets.token_urlsafe(16)
    
    url = (
        f"https://api.prod.whoop.com/oauth/oauth2/auth"
        f"?client_id={WHOOP_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&state={state}"
    )
    return RedirectResponse(url)

@router.get("/whoop/callback")
def whoop_callback(code: str = None, error: str = None, state: str = None, db: Session = Depends(get_db)):
    if error:
         return {"error": error, "detail": "Authorization failed or denied."}
    
    if not code:
        raise HTTPException(status_code=400, detail="No code received from WHOOP")

    try:
        token_url = "https://api.prod.whoop.com/oauth/oauth2/token"
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": WHOOP_CLIENT_ID,
            "client_secret": WHOOP_CLIENT_SECRET,
            "redirect_uri": "http://localhost:8000/auth/whoop/callback",
        }
        
        print(f"DEBUG: Requesting token with payload: content_type=application/x-www-form-urlencoded")
        response = requests.post(token_url, data=payload)
        
        print(f"DEBUG: Token response status: {response.status_code}")
        print(f"DEBUG: Token response body: {response.text}")

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to retrieve WHOOP token: {response.text}")
        
        data = response.json()
        
        user = db.query(User).first()
        if not user:
            print("DEBUG: Creating new user")
            user = User(email="user@example.com")
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
             print(f"DEBUG: Updating existing user: {user.id}")

        user.whoop_access_token = data.get("access_token")
        user.whoop_refresh_token = data.get("refresh_token")
        # Handle expires_in carefully
        expires_in = data.get("expires_in")
        if expires_in:
            user.whoop_expires_at = int(expires_in) + 3600 # Store as roughly 'now + seconds' is wrong? 
            # Wait, expires_at column expects a timestamp (integer)?
            # In Strava implementation: user.strava_expires_at = data["expires_at"] (Unix timestamp)
            # WHOOP gives 'expires_in' (seconds duration).
            # So I should add to current time? 
            # Earlier I did: user.whoop_expires_at = data["expires_in"] + 3600
            # That logic was: take the duration (e.g. 3600) and add 3600? No, that's weird.
            # It should be: current_time + expires_in.
            import time
            user.whoop_expires_at = int(time.time()) + int(expires_in)
        
        db.commit()

        return {"message": "WHOOP connected successfully", "debug_data": data}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": "Internal Server Error", "details": str(e), "trace": traceback.format_exc()}
