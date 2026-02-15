import sys
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add project root to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import User
from app.services.ai_coach import get_context
from app.routers.schedule import initialize_weekly_schedule

def verify():
    db = SessionLocal()
    user = db.query(User).first()
    
    print(f"Verifying context for user: {user.email}")
    
    # 1. Initialize Schedule (to ensure we have blocks to plan for)
    print("\n--- Initializing Weekly Schedule ---")
    # We need to simulate the dependency injection
    try:
        blocks = initialize_weekly_schedule(current_user=user, db=db)
        print(f"Generated {len(blocks)} blocks for the upcoming week.")
        for b in blocks:
             print(f"  {b.date}: {b.type} ({b.planned_duration_minutes} min)")
    except Exception as e:
        print(f"Error initializing schedule: {e}")

    # 2. Check AI Context
    print("\n--- AI Context Retrieval ---")
    context = get_context(user, db)
    
    print(f"Profile: Age={context['profile']['age']}, Gender={context['profile']['gender']}")
    print(f"Preferences: {context['profile']['preferences']}")
    
    print(f"\nDated Goals (Events): {len(context['goals']['events'])}")
    for g in context['goals']['events']:
        print(f"  - {g['date']}: {g['description']} ({g['type']})")
        
    print(f"\nUndated Goals: {len(context['goals']['preferences'])}")
    for g in context['goals']['preferences']:
        print(f"  - {g['description']} ({g['type']})")

    # 3. Prompt Construction Check (Logical)
    # We won't call OpenAI here to save cost/time, but we verified the data is available.
    if context['profile']['age'] == 30 and len(context['goals']['events']) > 0:
        print("\nSUCCESS: AI Context contains new User Profile and Goal data.")
    else:
        print("\nFAILURE: Context missing required data.")

if __name__ == "__main__":
    verify()
