"""
AI Coach service — context gathering and plan generation via OpenAI.

Builds a comprehensive context from user profile, Strava activities,
WHOOP recovery/workouts, and goals, then generates rolling 2-day
workout plans via OpenAI.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..models import User, StravaActivity, WhoopRecovery, TrainingPlan, Goal, WorkoutBlock, WhoopWorkout
from ..schemas import TrainingPlanCreate
from . import strava_client, whoop_client
import os
import json
import traceback
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_context(user: User, db: Session):
    """
    Build a comprehensive context dict from the user's recent data:
    - Profile (age, gender, height, weight, units)
    - Strava activities (last 28 days)
    - WHOOP recoveries (last 7 days)
    - WHOOP workouts (last 14 days)
    - Active goals (events + preferences)
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=28)
        activities = db.query(StravaActivity).filter(
            StravaActivity.user_id == user.id,
            StravaActivity.start_date >= cutoff_date
        ).all()

        units = user.settings.get('units', 'imperial')
        activity_summary = []
        for act in activities:
            if units == 'imperial':
                distance = f"{round(act.distance / 1609.34, 2)} mi"
            else:
                distance = f"{round(act.distance / 1000, 2)} km"

            activity_summary.append({
                "date": act.start_date.strftime("%Y-%m-%d"),
                "type": act.type,
                "distance": distance,
                "suffer_score": act.suffer_score
            })

        recovery_cutoff = datetime.now() - timedelta(days=7)
        recoveries = db.query(WhoopRecovery).filter(
            WhoopRecovery.user_id == user.id,
            WhoopRecovery.date >= recovery_cutoff.strftime("%Y-%m-%d")
        ).all()

        recovery_summary = [{
            "date": rec.date,
            "recovery_score": rec.recovery_score,
            "hrv": rec.hrv,
            "resting_hr": rec.resting_heart_rate,
            "sleep_performance": rec.sleep_performance
        } for rec in recoveries]

        workout_cutoff = datetime.now() - timedelta(days=14)
        whoop_workouts = db.query(WhoopWorkout).filter(
            WhoopWorkout.user_id == user.id,
            WhoopWorkout.start >= workout_cutoff
        ).all()

        whoop_workout_summary = [{
            "date": ww.start.strftime("%Y-%m-%d"),
            "sport": ww.sport_name,
            "strain": ww.strain,
            "avg_hr": ww.average_heart_rate,
            "max_hr": ww.max_heart_rate,
            "kilojoules": ww.kilojoules
        } for ww in whoop_workouts]

        goals = db.query(Goal).filter(
            Goal.user_id == user.id,
            Goal.status == "active"
        ).all()

        dated_goals = []
        undated_goals = []
        for g in goals:
            if g.target_date:
                try:
                    d_str = g.target_date.strftime("%Y-%m-%d") if isinstance(g.target_date, datetime) else str(g.target_date)[0:10]
                except Exception:
                    d_str = str(g.target_date)
                dated_goals.append({"description": g.description, "date": d_str, "type": g.type})
            else:
                undated_goals.append({"description": g.description, "type": g.type})

        dated_goals.sort(key=lambda x: x['date'])

        return {
            "profile": {
                "age": user.age,
                "gender": user.gender,
                "height": user.height,
                "weight": user.weight,
                "units": units,
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
        return {
            "profile": {},
            "activities": [],
            "recoveries": [],
            "whoop_workouts": [],
            "goals": {"events": [], "preferences": []}
        }


def sync_external_data(user: User, db: Session):
    """
    Sync Strava activities and WHOOP recovery/workout data.
    Each service is synced independently so one failure doesn't block the other.
    Returns a summary dict with counts and any error messages.
    """
    sync_result = {
        "strava": {"synced": 0, "error": None},
        "whoop": {"synced": 0, "error": None}
    }

    if user.strava_access_token:
        try:
            activities = strava_client.fetch_activities(user, db)
            sync_result["strava"]["synced"] = len(activities)
        except Exception as e:
            sync_result["strava"]["error"] = str(e)
    else:
        sync_result["strava"]["error"] = "Not connected"

    if user.whoop_access_token:
        try:
            recoveries = whoop_client.fetch_recoveries(user, db)
            workouts = whoop_client.fetch_workouts(user, db)
            sync_result["whoop"]["synced"] = len(recoveries) + len(workouts)
        except Exception as e:
            sync_result["whoop"]["error"] = str(e)
    else:
        sync_result["whoop"]["error"] = "Not connected"

    return sync_result


def get_or_generate_rolling_plan(user: User, db: Session):
    """
    Sync external data, then return a rolling 2-day plan (today + tomorrow).
    Uses caching:
    1. If a valid plan exists for today, return it (re-validating against schedule).
    2. If yesterday's plan exists, roll forward (yesterday's tomorrow → today).
    3. Otherwise, generate a fresh 2-day plan from scratch.
    """
    sync_result = sync_external_data(user, db)

    try:
        today = datetime.now().date()
        today_str = today.strftime("%Y-%m-%d")
        tomorrow_date = today + timedelta(days=1)
        tomorrow_str = tomorrow_date.strftime("%Y-%m-%d")

        context = get_context(user, db)

        def get_block_type(target_date):
            block = db.query(WorkoutBlock).filter(
                WorkoutBlock.user_id == user.id,
                WorkoutBlock.date == target_date.strftime("%Y-%m-%d")
            ).first()
            return block.type if block else "Rest"

        today_block_type = get_block_type(today)
        tomorrow_block_type = get_block_type(tomorrow_date)

        # 1. Check existing plan validity
        if user.last_plan_date == today_str and user.plan_today and user.plan_tomorrow:
            today_valid = (
                user.plan_today.get('date') == today_str and
                user.plan_today.get('block_type', 'Rest') == today_block_type
            )
            tomorrow_valid = (
                user.plan_tomorrow.get('block_type', 'Rest') == tomorrow_block_type
            )

            if today_valid and tomorrow_valid:
                return {"plan": [user.plan_today, user.plan_tomorrow], "sync": sync_result}

            if not today_valid:
                user.plan_today = generate_single_day_plan(user, db, context, today)
                user.plan_today['date'] = today_str

            if not tomorrow_valid:
                user.plan_tomorrow = generate_single_day_plan(user, db, context, tomorrow_date)
                user.plan_tomorrow['date'] = tomorrow_str

            db.commit()
            return {"plan": [user.plan_today, user.plan_tomorrow], "sync": sync_result}

        # 2. Rolling update (yesterday → today)
        yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        if user.last_plan_date == yesterday and user.plan_tomorrow:
            new_today = user.plan_tomorrow
            new_today['date'] = today_str

            if new_today.get('block_type') != today_block_type:
                refined_today = generate_single_day_plan(user, db, context, today)
            else:
                refined_today = refine_daily_plan(new_today, context, client, model=user.openai_model or "gpt-5-mini")

            refined_today['date'] = today_str

            new_tomorrow = generate_single_day_plan(user, db, context, tomorrow_date)
            new_tomorrow['date'] = tomorrow_str

            user.plan_today = refined_today
            user.plan_tomorrow = new_tomorrow
            user.last_plan_date = today_str
            db.commit()

            return {"plan": [refined_today, new_tomorrow], "sync": sync_result}

        # 3. Fresh generation
        plan_day_1 = generate_single_day_plan(user, db, context, today)
        plan_day_1['date'] = today_str

        plan_day_2 = generate_single_day_plan(user, db, context, tomorrow_date)
        plan_day_2['date'] = tomorrow_str

        user.plan_today = plan_day_1
        user.plan_tomorrow = plan_day_2
        user.last_plan_date = today_str
        db.commit()

        return {"plan": [plan_day_1, plan_day_2], "sync": sync_result}

    except Exception as e:
        print(f"Error in rolling plan generation: {e}")
        traceback.print_exc()
        return {"error": str(e), "sync": sync_result}


def refine_daily_plan(plan_day, context, client, model="gpt-5-mini"):
    """
    Refine an existing day plan based on fresh recovery data.
    Adjusts intensity/notes without changing the core routine.
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
            model=model,
            messages=[{"role": "system", "content": system_prompt}],
            response_format={"type": "json_object"}
        )
        content = completion.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Refinement failed: {e}")
        return plan_day


def generate_single_day_plan(user, db, context, target_date):
    """
    Generate a detailed workout plan for a single day.
    The plan respects the scheduled block type and duration, and incorporates
    the user's goals and recent recovery data.
    """
    date_str = target_date.strftime("%Y-%m-%d")

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
    - Strictly adhere to the Block Type and Duration.
    - Generate a specific 'routine' and 'focus'.
    - CRITICAL: ALL values must be PLAIN STRINGS. Do NOT nest objects or arrays.
    - The "routine" field must be a single string with numbered steps separated by newlines.
    - When a step references a named routine/exercise list from the user's preferences, format each exercise on its own line with a "- " prefix. For example:
      "1. Warm up 10 min.\n2. Perform your yoga routine:\n- Half-Kneeling Ankle Stretch\n- Seiza Pose\n- 90/90 Hip Rotations\n3. Cool down 5 min."
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
        model=user.openai_model or "gpt-5-mini",
        messages=[{"role": "system", "content": system_prompt}],
        response_format={"type": "json_object"}
    )

    plan_data = json.loads(completion.choices[0].message.content)

    plan_data['block_type'] = block_info['type']

    # Flatten any nested objects/arrays to plain strings
    for key in ['routine', 'focus', 'notes', 'intensity']:
        val = plan_data.get(key)
        if isinstance(val, list):
            plan_data[key] = ' '.join(
                str(item) if not isinstance(item, dict)
                else ' '.join(f"{k}: {v}" for k, v in item.items())
                for item in val
            )
        elif isinstance(val, dict):
            plan_data[key] = ' '.join(f"{k}: {v}" for k, v in val.items())

    return plan_data


def edit_day_plan(user: User, db: Session, day_key: str, messages: list):
    """
    Edit a day's plan via conversational chat.
    Takes the current plan and user messages, returns a chat reply
    and an updated plan. Persists the revision.

    Args:
        day_key: "today" or "tomorrow"
        messages: list of {"role": "user"|"assistant", "content": "..."}
    """
    current_plan = user.plan_today if day_key == "today" else user.plan_tomorrow
    if not current_plan:
        return {"reply": "No plan exists for this day yet. Generate a plan first.", "plan": None}

    context = get_context(user, db)

    system_prompt = f"""You are an expert Personal Trainer having a conversation with your client about their workout plan.

Current Plan:
{json.dumps(current_plan, indent=2)}

Client Context:
- Age/Gender: {context['profile'].get('age')}/{context['profile'].get('gender')}
- Units: {context['profile'].get('units', 'imperial')}
- Goals: {json.dumps(context['goals']['preferences'])}
- Recent Recovery: {json.dumps(context['recoveries'][-2:] if context['recoveries'] else 'No Data')}

Instructions:
1. Respond conversationally — acknowledge what the client wants, explain your changes.
2. Modify the plan according to their request.
3. Keep the same JSON structure for the plan.
4. ALL plan values must be PLAIN STRINGS (no nested objects/arrays).
5. The "routine" field must be a single string with numbered steps separated by newlines. When referencing a named routine/exercise list, format each exercise on its own line with a "- " prefix.
6. Do NOT change the "date" or "block_type" fields.

Output strict JSON:
{{
    "reply": "Your conversational response to the client",
    "revised_plan": {{ the full updated plan object }}
}}"""

    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        api_messages.append({"role": msg["role"], "content": msg["content"]})

    try:
        completion = client.chat.completions.create(
            model=user.openai_model or "gpt-5-mini",
            messages=api_messages,
            response_format={"type": "json_object"}
        )
        result = json.loads(completion.choices[0].message.content)

        revised = result.get("revised_plan", current_plan)

        # Flatten any nested values to plain strings
        for key in ['routine', 'focus', 'notes', 'intensity']:
            val = revised.get(key)
            if isinstance(val, list):
                revised[key] = ' '.join(
                    str(item) if not isinstance(item, dict)
                    else ' '.join(f"{k}: {v}" for k, v in item.items())
                    for item in val
                )
            elif isinstance(val, dict):
                revised[key] = ' '.join(f"{k}: {v}" for k, v in val.items())

        # Preserve date and block_type
        revised['date'] = current_plan.get('date')
        revised['block_type'] = current_plan.get('block_type')

        # Persist
        if day_key == "today":
            user.plan_today = revised
        else:
            user.plan_tomorrow = revised
        db.commit()

        return {"reply": result.get("reply", "Plan updated."), "plan": revised}

    except Exception as e:
        print(f"Edit plan failed: {e}")
        traceback.print_exc()
        return {"reply": f"Sorry, I couldn't process that: {str(e)}", "plan": current_plan}

