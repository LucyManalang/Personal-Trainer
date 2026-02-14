from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..models import User, StravaActivity, WhoopRecovery, TrainingPlan, Goal, WorkoutBlock, WhoopWorkout
from ..schemas import TrainingPlanCreate
import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_context(user: User, db: Session):
    # 1. Activities (Strava) - Last 28 days
    cutoff_date = datetime.now() - timedelta(days=28)
    activities = db.query(StravaActivity).filter(
        StravaActivity.user_id == user.id,
        StravaActivity.start_date >= cutoff_date
    ).all()
    
    activity_summary = []
    for act in activities:
        activity_summary.append({
            "date": act.start_date.strftime("%Y-%m-%d"),
            "type": act.type,
            "distance_km": round(act.distance / 1000, 2),
            "suffer_score": act.suffer_score
        })

    # 2. Recovery (WHOOP) - Last 7 days
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
            "resting_hr": rec.resting_heart_rate,
            "sleep_performance": rec.sleep_performance
        })

    # 3. Workouts (WHOOP) - Last 14 days
    workout_cutoff = datetime.now() - timedelta(days=14)
    whoop_workouts = db.query(WhoopWorkout).filter(
        WhoopWorkout.user_id == user.id,
        WhoopWorkout.start >= workout_cutoff
    ).all()
    
    whoop_workout_summary = []
    for ww in whoop_workouts:
        whoop_workout_summary.append({
            "date": ww.start.strftime("%Y-%m-%d"),
            "sport": ww.sport_name,
            "strain": ww.strain,
            "avg_hr": ww.average_heart_rate,
            "max_hr": ww.max_heart_rate,
            "kilojoules": ww.kilojoules
        })
        
    # 4. Goals
    goals = db.query(Goal).filter(
        Goal.user_id == user.id,
        Goal.status == "active"
    ).all()
    goal_summary = [{"type": g.type, "description": g.description} for g in goals]
        
    return {
        "activities": activity_summary,
        "recoveries": recovery_summary,
        "whoop_workouts": whoop_workout_summary,
        "goals": goal_summary
    }

def generate_3_day_plan(user: User, db: Session):
    context = get_context(user, db)
    
    # Get next 3 days of workout blocks
    today = datetime.now().date()
    end_date = today + timedelta(days=3) # Today, T+1, T+2
    
    blocks = db.query(WorkoutBlock).filter(
        WorkoutBlock.user_id == user.id,
        WorkoutBlock.date >= today.strftime("%Y-%m-%d"),
        WorkoutBlock.date < end_date.strftime("%Y-%m-%d")
    ).order_by(WorkoutBlock.date).all()
    
    if not blocks:
         return {"message": "No workout blocks found for the next 3 days. Please initialize your schedule first."}
         
    blocks_context = []
    for b in blocks:
        blocks_context.append({
            "date": b.date,
            "type": b.type,
            "duration": b.planned_duration_minutes,
            "notes": b.notes
        })
    
    # Prompt Construction
    system_prompt = """
    You are an expert Personal Trainer AI. Your client has a pre-defined schedule of workout blocks (Type + Duration).
    Your job is to fill in the specific details for these blocks for the next 3 days.
    
    Inputs:
    1. Goals: The client's short and long term goals.
    2. Context: Recent Strava runs, WHOOP recoveries (Sleep/HRV), and WHOOP workouts (Strength/Cardio).
    3. Schedule: The specific blocks you must detail.
    
    Instructions:
    - Respect the Block Type and Duration strictly.
    - Provide a specific "Routine" or "Workout" valid for that type.
    - If type is "Strength", specify exercises/sets/reps or focus area.
    - If type is "Cardio" or "Run", specify pace, intervals, or steady state based on recovery.
    - Be holistic. If recovery is low, adjust intensity but keep duration if possible, or advise modification.
    
    Output Format:
    Return strictly Valid JSON. An object with a key "plan" containing an array of 3 objects (one for each day).
    Example:
    {
      "plan": [
        {
          "date": "YYYY-MM-DD",
          "block_type": "Strength",
          "focus": "Upper Body Power",
          "routine": "3x5 Bench Press, 3x8 Pullups...",
          "intensity": "High",
          "notes": "Focus on explosive tempo."
        }
      ]
    }
    """
    
    user_prompt = f"""
    Current Date: {today}
    
    Client Goals:
    {json.dumps(context['goals'], indent=2)}
    
    Upcoming Schedule (Blocks to Detail):
    {json.dumps(blocks_context, indent=2)}
    
    Recent Physiology (Recovery/Sleep):
    {json.dumps(context['recoveries'][-3:], indent=2)} 
    
    Recent Workouts (WHOOP):
    {json.dumps(context['whoop_workouts'][-5:], indent=2)}
    
    Recent Runs (Strava):
    {json.dumps(context['activities'][-5:], indent=2)}
    
    Generate the detailed plan for these 3 days.
    """
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        content = completion.choices[0].message.content
        plan_data = json.loads(content)
        
        # Save plan to DB? 
        # The user didn't ask to save it as a "TrainingPlan" object specifically, but implied it's the trainer giving info.
        # Let's save it as a TrainingPlan for history.
        new_plan = TrainingPlan(
            user_id=user.id,
            start_date=today.strftime("%Y-%m-%d"),
            end_date=(today + timedelta(days=2)).strftime("%Y-%m-%d"),
            content=plan_data,
            feedback="Auto-generated 3-day plan"
        )
        db.add(new_plan)
        db.commit()
        
        return plan_data
        
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return {"error": str(e)}
