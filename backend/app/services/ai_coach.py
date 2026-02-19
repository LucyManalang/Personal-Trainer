from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..models import User, StravaActivity, WhoopRecovery, TrainingPlan, Goal, WorkoutBlock, WhoopWorkout
from ..schemas import TrainingPlanCreate
import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_context(user: User, db: Session):
    try:
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
                "distance": f"{round(act.distance / 1609.34, 2)} mi" if user.settings.get('units', 'imperial') == 'imperial' else f"{round(act.distance / 1000, 2)} km",
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
        
        # Categorize goals
        dated_goals = []
        undated_goals = []
        for g in goals:
            if g.target_date:
                try:
                    d_str = g.target_date.strftime("%Y-%m-%d") if isinstance(g.target_date, datetime) else str(g.target_date)[0:10]
                except:
                    d_str = str(g.target_date)

                dated_goals.append({
                    "description": g.description,
                    "date": d_str,
                    "type": g.type
                })
            else:
                undated_goals.append({
                    "description": g.description,
                    "type": g.type
                })

        # Sort dated goals by date
        dated_goals.sort(key=lambda x: x['date'])

        return {
            "profile": {
                "age": user.age,
                "gender": user.gender,
                "height": user.height,
                "weight": user.weight,
                "weight": user.weight,
                "units": user.settings.get('units', 'imperial'),
                "preferences": user.settings
            },
            "activities": activity_summary,
            "recoveries": recovery_summary,
            "whoop_workouts": whoop_workout_summary,
            "goals": {
                "events": dated_goals,
                "preferences": undated_goals
            }
        }
    except Exception as e:
        print(f"Error in get_context: {e}")
        # Return empty context to avoid crash
        return {
            "profile": {},
            "activities": [],
            "recoveries": [],
            "whoop_workouts": [],
            "goals": {"events": [], "preferences": []}
        }

def get_or_generate_rolling_plan(user: User, db: Session):
    try:
        today = datetime.now().date()
        today_str = today.strftime("%Y-%m-%d")
        tomorrow_date = today + timedelta(days=1)
        tomorrow_str = tomorrow_date.strftime("%Y-%m-%d")

        context = get_context(user, db)

        # Helper to get block type
        def get_block_type(target_date):
            block = db.query(WorkoutBlock).filter(
                WorkoutBlock.user_id == user.id,
                WorkoutBlock.date == target_date.strftime("%Y-%m-%d")
            ).first()
            return block.type if block else "Rest"

        today_block_type = get_block_type(today)
        tomorrow_block_type = get_block_type(tomorrow_date)

        # 1. CHECK FOR EXISTING PLAN & VALIDATE
        if user.last_plan_date == today_str and user.plan_today and user.plan_tomorrow:
            
            # Validation Flags
            today_valid = True
            tomorrow_valid = True
            
            # Check Date Integrity
            if user.plan_today.get('date') != today_str:
                print(f"Date Mismatch Today: {user.plan_today.get('date')} vs {today_str}")
                today_valid = False
            
            # Check Schedule Integrity (Block Type)
            stored_today_type = user.plan_today.get('block_type', 'Rest')
            # Normalize for comparison (handle case sensitivity or slight variations if needed, but strict for now)
            if stored_today_type != today_block_type:
                print(f"Schedule Mismatch Today: Plan={stored_today_type} vs Schedule={today_block_type}")
                today_valid = False

            # Check Tomorrow Integrity
            if user.plan_tomorrow.get('block_type', 'Rest') != tomorrow_block_type:
                print(f"Schedule Mismatch Tomorrow: Plan={user.plan_tomorrow.get('block_type')} vs Schedule={tomorrow_block_type}")
                tomorrow_valid = False
            
            if today_valid and tomorrow_valid:
                return {"plan": [user.plan_today, user.plan_tomorrow]}
            
            # If invalid, regenerate specific days
            if not today_valid:
                print("Regenerating Today due to mismatch...")
                user.plan_today = generate_single_day_plan(user, db, context, today)
                user.plan_today['date'] = today_str # Force date correctness

            if not tomorrow_valid:
                print("Regenerating Tomorrow due to mismatch...")
                user.plan_tomorrow = generate_single_day_plan(user, db, context, tomorrow_date)
                user.plan_tomorrow['date'] = tomorrow_str # Force date correctness
                
            db.commit()
            return {"plan": [user.plan_today, user.plan_tomorrow]}

        
        # 2. ROLLING UPDATE (Yesterday -> Today)
        yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        if user.last_plan_date == yesterday and user.plan_tomorrow:
            print("Rolling over plan: Tomorrow -> Today")
            
            # Move Tomorrow -> Today
            new_today = user.plan_tomorrow
            new_today['date'] = today_str # Force Update date to today
            
            # Check if the "Old Tomorrow" (Now Today) matches the ACTUAL Today's Schedule
            # It might have changed since yesterday!
            if new_today.get('block_type') != today_block_type:
                print("Rolled plan mismatch! Regenerating Today from scratch.")
                refined_today = generate_single_day_plan(user, db, context, today)
            else:
                # Refine Today if it matches
                refined_today = refine_daily_plan(new_today, context, client)
            
            # FORCE DATE on refined plan
            refined_today['date'] = today_str 
            
            # Generate New Tomorrow
            new_tomorrow = generate_single_day_plan(user, db, context, tomorrow_date)
            # FORCE DATE on new tomorrow
            new_tomorrow['date'] = tomorrow_str
            
            # Save
            user.plan_today = refined_today
            user.plan_tomorrow = new_tomorrow
            user.last_plan_date = today_str
            db.commit()
            
            return {"plan": [refined_today, new_tomorrow]}

        # 3. FRESH GENERATION (Stale or New User)
        print("Generating fresh 2-day plan")
        plan_day_1 = generate_single_day_plan(user, db, context, today)
        plan_day_1['date'] = today_str # Force date correctness
        
        plan_day_2 = generate_single_day_plan(user, db, context, tomorrow_date)
        plan_day_2['date'] = tomorrow_str # Force date correctness
        
        user.plan_today = plan_day_1
        user.plan_tomorrow = plan_day_2
        user.last_plan_date = today_str
        db.commit()
        
        return {"plan": [plan_day_1, plan_day_2]}

    except Exception as e:
        print(f"Error in rolling plan generation: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

def refine_daily_plan(plan_day, context, client):
    """
    Keeps the core routine but adjusts intensity/notes based on fresh recovery.
    """
    try:
        system_prompt = f"""
        You are an expert Personal Trainer. You have an existing workout plan for TODAY.
        Your job is to REFINE it based on the client's latest recovery metrics (Sleep, HRV) without changing the core workout substance.
        
        Current Plan:
        {json.dumps(plan_day)}
        
        Client Context:
        - Age/Gender: {context['profile'].get('age')}/{context['profile'].get('gender')}
        - Unit Pref: {context['profile'].get('units', 'imperial')}
        - Recent Recovery: {json.dumps(context['recoveries'][-1:] if context['recoveries'] else 'No Data')}
        
        Instructions:
        1. If recovery is POOR, lower intensity or suggest modifications in 'notes'.
        2. If recovery is GREAT, you might increase intensity slightly.
        3. DO NOT change the 'block_type', 'focus', or the core 'routine' steps unless absolutely necessary for safety.
        4. Update 'date' to match the current day if needed.
        
        Output:
        Return strict JSON of the modified plan object.
        """
        
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt}],
            response_format={"type": "json_object"}
        )
        content = completion.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Refinement failed: {e}")
        return plan_day # Fallback to original

def generate_single_day_plan(user, db, context, target_date):
    """
    Generates a single day plan for a specific date.
    """
    date_str = target_date.strftime("%Y-%m-%d")
    
    # Get specific block for this day
    block = db.query(WorkoutBlock).filter(
        WorkoutBlock.user_id == user.id,
        WorkoutBlock.date == date_str
    ).first()
    
    block_info = {
        "date": date_str,
        "type": block.type if block else "Rest",
        "duration": block.planned_duration_minutes if block else 0,
        "notes": block.notes if block else "No planned block"
    }

    system_prompt = f"""
    You are an expert Personal Trainer. Generate a detailed workout for {date_str}.
    
    Client:
    - Age/Gender: {context['profile'].get('age')}/{context['profile'].get('gender')}
    - Units: {context['profile'].get('units', 'imperial')}
    - Goals: {json.dumps(context['goals']['preferences'], indent=2)}
    
    Schedule Block:
    {json.dumps(block_info)}
    
    Recent Data:
    - Recovery: {json.dumps(context['recoveries'][-3:], indent=2)}
    - Activities: {json.dumps(context['activities'][-3:], indent=2)}
    
    Instructions:
    - strictly adhere to the Block Type and Duration.
    - generate a specific 'routine' and 'focus'.
    - CRITICAL: ALL values must be PLAIN STRINGS. Do NOT nest objects or arrays.
    - The "routine" field must be a single string with numbered steps, e.g. "1. Warm up 10 min. 2. Squats 3x10. 3. Cool down."
    - Output strictly Valid JSON object:
    {{
        "date": "{date_str}",
        "block_type": "...",
        "intensity": "Low/Medium/High",
        "focus": "a plain string",
        "routine": "a plain string with numbered steps",
        "notes": "a plain string"
    }}
    """
    
    
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt}],
        response_format={"type": "json_object"}
    )
    
    plan_data = json.loads(completion.choices[0].message.content)
    
    # HARD OVERWRITE: Force the block_type to match the schedule strictly
    plan_data['block_type'] = block_info['type']
    
    # Flatten any nested objects/arrays to plain strings
    for key in ['routine', 'focus', 'notes', 'intensity']:
        val = plan_data.get(key)
        if isinstance(val, list):
            plan_data[key] = ' '.join([str(item) if not isinstance(item, dict) else ' '.join(f"{k}: {v}" for k, v in item.items()) for item in val])
        elif isinstance(val, dict):
            plan_data[key] = ' '.join(f"{k}: {v}" for k, v in val.items())
    
    return plan_data
