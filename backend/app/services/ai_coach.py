from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..models import User, StravaActivity, WhoopRecovery, TrainingPlan
from ..schemas import TrainingPlanCreate
import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_context(user: User, db: Session):
    # 1. Fetch recent activities (last 28 days for load)
    cutoff_date = datetime.now() - timedelta(days=28)
    activities = db.query(StravaActivity).filter(
        StravaActivity.user_id == user.id,
        StravaActivity.start_date >= cutoff_date
    ).all()
    
    # Summarize activity data
    activity_summary = []
    for act in activities:
        activity_summary.append({
            "date": act.start_date.strftime("%Y-%m-%d"),
            "type": act.type,
            "distance_km": round(act.distance / 1000, 2),
            "suffer_score": act.suffer_score
        })

    # 2. Fetch recent recovery (last 7 days)
    recovery_cutoff = datetime.now() - timedelta(days=7)
    recoveries = db.query(WhoopRecovery).filter(
        WhoopRecovery.user_id == user.id,
        WhoopRecovery.date >= recovery_cutoff.strftime("%Y-%m-%d")
    ).all()
    
    recovery_summary = []
    for rec in recoveries:
        recovery_summary.append({
            "date": rec.date,
            "recovery_score": rec.recovery_score,
            "hrv": rec.hrv,
            "resting_hr": rec.resting_heart_rate
        })
        
    return {
        "activities": activity_summary,
        "recoveries": recovery_summary
    }

def generate_training_plan(user: User, request_data: TrainingPlanCreate, db: Session):
    context = get_context(user, db)
    
    # Prompt Construction
    system_prompt = """
    You are an expert elite running coach. Your goal is to create a personalized 7-day training plan for an athlete training for a marathon.
    Use the provided physiological data (WHOOP) and training history (Strava) to adapt the plan.
    
    Principles:
    - If recovery is low (<33%), prescribe rest or active recovery.
    - If recovery is high (>66%) and recent load is manageable, suggest key workouts (intervals, tempo, long run).
    - Respect the athlete's specific requests constraints.
    
    Output Format:
    Return strictly Valid JSON. The JSON should be an array of objects, each representing a day.
    Example:
    [
        {"date": "YYYY-MM-DD", "type": "Run", "focus": "Easy", "description": "Run 5km easy", "distance_km": 5},
        {"date": "YYYY-MM-DD", "type": "Rest", "focus": "Recovery", "description": "Rest day", "distance_km": 0}
    ]
    """
    
    user_prompt = f"""
    App Current Date: {datetime.now().strftime("%Y-%m-%d")}
    Plan Start Date: {request_data.start_date}
    Plan End Date: {request_data.end_date}
    
    User Feedback/Request: "{request_data.feedback or 'None'}"
    
    Recent Training History (Last 28 days):
    {json.dumps(context['activities'], indent=2)}
    
    Recent Recovery Data (Last 7 days):
    {json.dumps(context['recoveries'], indent=2)}
    
    Generate the plan for the requested dates.
    """
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini", # Cost-effective: ~$0.15 / 1M tokens vs ~$2.50 for gpt-4o
            messages=[
                {"role": "system", "content": system_prompt + "\nReturn a JSON object with a key 'plan' containing the list of days."},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        content = completion.choices[0].message.content
        plan_json = json.loads(content)
        
        # Save plan to DB
        # Check if plan format is wrapped in a key or is the array directly. 
        # The prompt asked for array. But response_format json_object usually requires a root object.
        # Let's start lenient.
        
        # Usually model with json_object mode puts it in a key if instructed, or we might need to adjust prompt.
        # Let's adjust prompt to "Return JSON object with key 'plan' containing the array".
        pass 
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return {"error": str(e)}

    # Refined prompt for JSON object structure to be safe
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt + "\nReturn a JSON object with a key 'plan' containing the list of days."},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )
    content = completion.choices[0].message.content
    plan_data = json.loads(content)
    
    # Store in DB
    new_plan = TrainingPlan(
        user_id=user.id,
        start_date=request_data.start_date,
        end_date=request_data.end_date,
        content=plan_data,
        feedback=request_data.feedback
    )
    db.add(new_plan)
    db.commit()
    
    return plan_data
