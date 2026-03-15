"""
AI Coach service — self-prompting plan generation via OpenAI.

Uses a two-step chain:
  1. Compute recovery insights (pure math) + generate coaching analysis (LLM)
  2. Generate day plans from the analysis (LLM)

Also handles conversational plan editing and daily refinement.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
from ..models import (
    User, StravaActivity, WhoopRecovery, TrainingPlan,
    Goal, WorkoutBlock, WhoopWorkout, ReadinessCheckIn,
)
from ..schemas import TrainingPlanCreate
from . import strava_client, whoop_client
import os
import json
import traceback
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------------------------------------------------------------------------
# Context gathering
# ---------------------------------------------------------------------------

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
            "kilojoules": ww.kilojoules,
            "zone_durations": ww.zone_durations
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


# ---------------------------------------------------------------------------
# Recovery insights (pure computation — no LLM)
# ---------------------------------------------------------------------------

def compute_recovery_insights(context: dict, readiness: Optional[dict] = None) -> dict:
    """
    Compute analytics from raw context data:
    - Recovery trend (7-day average, direction, deviation from baseline)
    - Sleep trend (average performance, sleep debt flag)
    - Strain balance (acute vs chronic, acute:chronic ratio)
    - HR zone load (time in Zone 4-5 over last 7 days)
    - Subjective readiness (from check-in, if available)
    """
    recoveries = context.get("recoveries", [])
    whoop_workouts = context.get("whoop_workouts", [])

    # --- Recovery trend ---
    recovery_scores = [r["recovery_score"] for r in recoveries if r.get("recovery_score") is not None]
    hrv_values = [r["hrv"] for r in recoveries if r.get("hrv") is not None]

    recovery_7d_avg = round(sum(recovery_scores) / len(recovery_scores), 1) if recovery_scores else None
    hrv_7d_avg = round(sum(hrv_values) / len(hrv_values), 1) if hrv_values else None

    # Determine trend direction (compare first half vs second half)
    def _trend_direction(values):
        if len(values) < 3:
            return "insufficient_data"
        mid = len(values) // 2
        first_half = sum(values[:mid]) / mid
        second_half = sum(values[mid:]) / (len(values) - mid)
        diff = second_half - first_half
        if diff > 5:
            return "rising"
        elif diff < -5:
            return "declining"
        return "stable"

    # Consecutive low recovery days (below 50%)
    consecutive_low = 0
    for score in reversed(recovery_scores):
        if score < 50:
            consecutive_low += 1
        else:
            break

    today_vs_baseline = None
    if recovery_scores and recovery_7d_avg:
        today_vs_baseline = round(recovery_scores[-1] - recovery_7d_avg, 1)

    recovery_trend = {
        "7d_avg": recovery_7d_avg,
        "hrv_7d_avg": hrv_7d_avg,
        "direction": _trend_direction(recovery_scores),
        "today_vs_baseline": today_vs_baseline,
        "consecutive_low_days": consecutive_low
    }

    # --- Sleep trend ---
    sleep_scores = [r["sleep_performance"] for r in recoveries if r.get("sleep_performance") is not None]
    sleep_7d_avg = round(sum(sleep_scores) / len(sleep_scores), 1) if sleep_scores else None
    low_sleep_days = sum(1 for s in sleep_scores if s < 75)
    sleep_debt_flag = low_sleep_days >= 3

    sleep_trend = {
        "7d_avg_performance": sleep_7d_avg,
        "sleep_debt_flag": sleep_debt_flag,
        "low_sleep_days": low_sleep_days,
        "last_night": sleep_scores[-1] if sleep_scores else None
    }

    # --- Strain / training load balance ---
    # Acute = last 7 days, Chronic = last 28 days (using all available whoop workouts)
    today = datetime.now().date()
    seven_days_ago = today - timedelta(days=7)

    acute_strain = 0
    chronic_strain = 0
    for ww in whoop_workouts:
        strain = ww.get("strain") or 0
        chronic_strain += strain
        try:
            ww_date = datetime.strptime(ww["date"], "%Y-%m-%d").date()
            if ww_date >= seven_days_ago:
                acute_strain += strain
        except (ValueError, KeyError):
            pass

    # Normalize chronic to 7-day equivalent for ratio
    chronic_days = 14  # whoop_workouts covers 14 days of data
    chronic_weekly = (chronic_strain / chronic_days * 7) if chronic_days > 0 else 0
    acr = round(acute_strain / chronic_weekly, 2) if chronic_weekly > 0 else None

    if acr is None:
        risk_level = "unknown"
    elif acr > 1.5:
        risk_level = "high"
    elif acr > 1.3:
        risk_level = "moderate"
    else:
        risk_level = "low"

    strain_balance = {
        "acute_7d": round(acute_strain, 1),
        "chronic_14d": round(chronic_strain, 1),
        "acute_chronic_ratio": acr,
        "risk_level": risk_level
    }

    # --- HR zone load (Zone 4-5 minutes in last 7 days) ---
    zone_4_5_ms = 0
    for ww in whoop_workouts:
        try:
            ww_date = datetime.strptime(ww["date"], "%Y-%m-%d").date()
            if ww_date < seven_days_ago:
                continue
        except (ValueError, KeyError):
            continue
        zones = ww.get("zone_durations")
        if zones and isinstance(zones, dict):
            # WHOOP zone keys vary — look for zone_four, zone_five or index 3,4
            for key in ["zone_four", "zone_five", "3", "4"]:
                zone_4_5_ms += zones.get(key, 0)
        elif zones and isinstance(zones, list) and len(zones) >= 5:
            zone_4_5_ms += (zones[3] if zones[3] else 0) + (zones[4] if zones[4] else 0)

    zone_4_5_minutes = round(zone_4_5_ms / 60000, 1)  # ms → minutes

    hr_zone_load = {
        "zone_4_5_minutes_7d": zone_4_5_minutes,
        "high_intensity_flag": zone_4_5_minutes > 120
    }

    insights = {
        "recovery_trend": recovery_trend,
        "sleep_trend": sleep_trend,
        "strain_balance": strain_balance,
        "hr_zone_load": hr_zone_load,
    }

    if readiness:
        insights["readiness"] = readiness

    return insights


# ---------------------------------------------------------------------------
# Step 1: Coaching analysis (LLM self-prompt)
# ---------------------------------------------------------------------------

def generate_coaching_analysis(
    user: User,
    db: Session,
    context: dict,
    insights: dict,
    schedule_blocks: List[dict],
) -> dict:
    """
    Step 1 of the self-prompting chain.
    The AI reasons about all available data and produces a structured
    coaching analysis that will feed into plan generation (Step 2).
    """
    model = user.openai_model or "gpt-5-mini"

    system_prompt = f"""You are an elite sports-science analyst preparing a coaching brief for a personal trainer.

CLIENT PROFILE:
{json.dumps(context['profile'], indent=2)}

GOALS & EVENTS:
{json.dumps(context['goals'], indent=2)}

SCHEDULED BLOCKS (next 2 days):
{json.dumps(schedule_blocks, indent=2)}

RECENT ACTIVITIES (last 28 days):
{json.dumps(context['activities'], indent=2)}

WHOOP WORKOUTS (last 14 days, with strain + HR zones):
{json.dumps(context['whoop_workouts'], indent=2)}

RECOVERY DATA (last 7 days):
{json.dumps(context['recoveries'], indent=2)}

COMPUTED INSIGHTS:
{json.dumps(insights, indent=2)}

YOUR TASK — produce a structured coaching analysis covering:

1. **Recovery Assessment**: Interpret the recovery trend, HRV, sleep quality. Is the client recovered, under-recovered, or peaking? Cite specific numbers.

2. **Training Load Assessment**: Analyze the acute:chronic workload ratio and recent strain. Is load appropriate, spiking, or insufficient? Note injury risk level.

3. **Sleep Assessment**: Comment on sleep debt, recent sleep performance. Any concerns?

4. **HR Zone Analysis**: Has the client been spending too much time in high-intensity zones (4-5)? Should today favor aerobic or recovery zones instead?

5. **Subjective Readiness**: If a readiness check-in is available, integrate the client's self-reported energy, soreness, and mood. Note any areas to avoid loading.

6. **Goal Proximity**: How close are upcoming events/goals? Does periodization need adjustment?

7. **Recommendations**: For each of the next 2 days, provide:
   - Recommended intensity level (Low / Medium / High)
   - Muscle groups or movement patterns to emphasize
   - Muscle groups or areas to avoid (if soreness reported)
   - Key adjustments based on all the above

Output strict JSON:
{{
    "recovery_status": "string summary",
    "training_load_status": "string summary",
    "sleep_status": "string summary",
    "hr_zone_status": "string summary",
    "readiness_status": "string summary or 'No check-in submitted'",
    "goal_proximity": "string summary",
    "day_recommendations": {{
        "today": {{
            "recommended_intensity": "Low/Medium/High",
            "emphasis": "string",
            "avoid": "string or 'None'",
            "adjustments": "string"
        }},
        "tomorrow": {{
            "recommended_intensity": "Low/Medium/High",
            "emphasis": "string",
            "avoid": "string or 'None'",
            "adjustments": "string"
        }}
    }},
    "overall_notes": "string — any other important observations"
}}"""

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt}],
            response_format={"type": "json_object"}
        )
        analysis = json.loads(completion.choices[0].message.content)
        print(f"[Coach] Analysis generated: recovery={analysis.get('recovery_status', 'N/A')[:60]}")
        return analysis
    except Exception as e:
        print(f"[Coach] Analysis generation failed: {e}")
        traceback.print_exc()
        return {"error": str(e), "recovery_status": "Analysis unavailable"}


# ---------------------------------------------------------------------------
# Step 2: Single-day plan generation (from analysis)
# ---------------------------------------------------------------------------

def generate_single_day_plan(user, db, context, target_date, coaching_analysis=None):
    """
    Generate a detailed workout plan for a single day.
    Uses the coaching analysis (Step 1 output) as primary context instead
    of dumping raw data into the prompt.
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

    day_key = "today" if target_date == datetime.now().date() else "tomorrow"

    # Build the system prompt — use coaching analysis if available
    if coaching_analysis and "error" not in coaching_analysis:
        day_rec = coaching_analysis.get("day_recommendations", {}).get(day_key, {})

        system_prompt = f"""You are an expert Personal Trainer. Generate a detailed workout for {date_str}.

CLIENT:
- Age/Gender: {context['profile'].get('age')}/{context['profile'].get('gender')}
- Units: {context['profile'].get('units', 'imperial')}
- Preferences/Goals: {json.dumps(context['goals']['preferences'], indent=2)}

SCHEDULE BLOCK:
{json.dumps(block_info)}

COACH'S ANALYSIS FOR THIS DAY:
- Recovery Status: {coaching_analysis.get('recovery_status', 'N/A')}
- Training Load: {coaching_analysis.get('training_load_status', 'N/A')}
- Sleep: {coaching_analysis.get('sleep_status', 'N/A')}
- HR Zones: {coaching_analysis.get('hr_zone_status', 'N/A')}
- Readiness: {coaching_analysis.get('readiness_status', 'N/A')}
- Recommended Intensity: {day_rec.get('recommended_intensity', 'N/A')}
- Emphasis: {day_rec.get('emphasis', 'N/A')}
- Avoid: {day_rec.get('avoid', 'None')}
- Key Adjustments: {day_rec.get('adjustments', 'N/A')}
- Overall Notes: {coaching_analysis.get('overall_notes', '')}

Instructions:
- Strictly adhere to the Block Type and Duration.
- Follow the coach's analysis for intensity and emphasis.
- If the analysis says to avoid certain muscle groups, respect that.
- Generate a specific 'routine' and 'focus'.
- CRITICAL: ALL values must be PLAIN STRINGS. Do NOT nest objects or arrays.
- The "routine" field must be a single string with numbered steps separated by newlines.
- When a step references a named routine/exercise list from the user's preferences, format each exercise on its own line with a "- " prefix.
- Output strictly Valid JSON object:
{{
    "date": "{date_str}",
    "block_type": "...",
    "intensity": "Low/Medium/High",
    "focus": "a plain string",
    "routine": "a plain string with numbered steps",
    "notes": "a plain string"
}}"""
    else:
        # Fallback: no analysis available — use raw data (original behavior)
        system_prompt = f"""You are an expert Personal Trainer. Generate a detailed workout for {date_str}.

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
- When a step references a named routine/exercise list from the user's preferences, format each exercise on its own line with a "- " prefix.
- Output strictly Valid JSON object:
{{
    "date": "{date_str}",
    "block_type": "...",
    "intensity": "Low/Medium/High",
    "focus": "a plain string",
    "routine": "a plain string with numbered steps",
    "notes": "a plain string"
}}"""

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


# ---------------------------------------------------------------------------
# External data sync
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Rolling plan orchestrator
# ---------------------------------------------------------------------------

def get_or_generate_rolling_plan(user: User, db: Session):
    """
    Sync external data, then return a rolling 2-day plan (today + tomorrow).
    Uses the two-step self-prompting chain:
      1. Compute insights + generate coaching analysis
      2. Generate day plans from the analysis

    Caching:
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

        # Fetch today's readiness check-in (if any)
        readiness_checkin = db.query(ReadinessCheckIn).filter(
            ReadinessCheckIn.user_id == user.id,
            ReadinessCheckIn.date == today_str
        ).first()

        readiness_data = None
        if readiness_checkin:
            readiness_data = {
                "energy": readiness_checkin.energy_level,
                "soreness": readiness_checkin.soreness_notes,
                "mood": readiness_checkin.mood
            }

        def get_block_info(target_date):
            block = db.query(WorkoutBlock).filter(
                WorkoutBlock.user_id == user.id,
                WorkoutBlock.date == target_date.strftime("%Y-%m-%d")
            ).first()
            return {
                "date": target_date.strftime("%Y-%m-%d"),
                "type": block.type if block else "Rest",
                "duration": block.planned_duration_minutes if block else 0,
                "notes": block.notes if block else ""
            }

        today_block_type = get_block_info(today)["type"]
        tomorrow_block_type = get_block_info(tomorrow_date)["type"]

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
                return {
                    "plan": [user.plan_today, user.plan_tomorrow],
                    "coach_analysis": user.coach_analysis,
                    "sync": sync_result
                }

            # Re-generate invalid days with fresh analysis
            insights = compute_recovery_insights(context, readiness_data)
            schedule_blocks = [get_block_info(today), get_block_info(tomorrow_date)]
            analysis = generate_coaching_analysis(user, db, context, insights, schedule_blocks)

            if not today_valid:
                user.plan_today = generate_single_day_plan(user, db, context, today, analysis)
                user.plan_today['date'] = today_str

            if not tomorrow_valid:
                user.plan_tomorrow = generate_single_day_plan(user, db, context, tomorrow_date, analysis)
                user.plan_tomorrow['date'] = tomorrow_str

            user.coach_analysis = analysis
            db.commit()
            return {
                "plan": [user.plan_today, user.plan_tomorrow],
                "coach_analysis": analysis,
                "sync": sync_result
            }

        # 2. Rolling update (yesterday → today)
        yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        if user.last_plan_date == yesterday and user.plan_tomorrow:
            new_today = user.plan_tomorrow
            new_today['date'] = today_str

            # Always regenerate with fresh analysis on roll-forward
            insights = compute_recovery_insights(context, readiness_data)
            schedule_blocks = [get_block_info(today), get_block_info(tomorrow_date)]
            analysis = generate_coaching_analysis(user, db, context, insights, schedule_blocks)

            if new_today.get('block_type') != today_block_type:
                refined_today = generate_single_day_plan(user, db, context, today, analysis)
            else:
                refined_today = refine_daily_plan(new_today, context, analysis, model=user.openai_model or "gpt-5-mini")

            refined_today['date'] = today_str

            new_tomorrow = generate_single_day_plan(user, db, context, tomorrow_date, analysis)
            new_tomorrow['date'] = tomorrow_str

            user.plan_today = refined_today
            user.plan_tomorrow = new_tomorrow
            user.coach_analysis = analysis
            user.last_plan_date = today_str
            db.commit()

            return {
                "plan": [refined_today, new_tomorrow],
                "coach_analysis": analysis,
                "sync": sync_result
            }

        # 3. Fresh generation with full self-prompting chain
        insights = compute_recovery_insights(context, readiness_data)
        schedule_blocks = [get_block_info(today), get_block_info(tomorrow_date)]
        analysis = generate_coaching_analysis(user, db, context, insights, schedule_blocks)

        plan_day_1 = generate_single_day_plan(user, db, context, today, analysis)
        plan_day_1['date'] = today_str

        plan_day_2 = generate_single_day_plan(user, db, context, tomorrow_date, analysis)
        plan_day_2['date'] = tomorrow_str

        user.plan_today = plan_day_1
        user.plan_tomorrow = plan_day_2
        user.coach_analysis = analysis
        user.last_plan_date = today_str
        db.commit()

        return {
            "plan": [plan_day_1, plan_day_2],
            "coach_analysis": analysis,
            "sync": sync_result
        }

    except Exception as e:
        print(f"Error in rolling plan generation: {e}")
        traceback.print_exc()
        return {"error": str(e), "sync": sync_result}


# ---------------------------------------------------------------------------
# Refinement & editing
# ---------------------------------------------------------------------------

def refine_daily_plan(plan_day, context, coaching_analysis=None, model="gpt-5-mini"):
    """
    Refine an existing day plan based on fresh recovery data and coaching analysis.
    Adjusts intensity/notes without changing the core routine.
    """
    try:
        analysis_section = ""
        if coaching_analysis and "error" not in coaching_analysis:
            analysis_section = f"""
        Coach's Latest Analysis:
        - Recovery: {coaching_analysis.get('recovery_status', 'N/A')}
        - Sleep: {coaching_analysis.get('sleep_status', 'N/A')}
        - Readiness: {coaching_analysis.get('readiness_status', 'N/A')}
        - Training Load: {coaching_analysis.get('training_load_status', 'N/A')}
        """

        system_prompt = f"""
        You are an expert Personal Trainer. You have an existing workout plan for TODAY.
        Your job is to REFINE it based on the client's latest recovery metrics and coaching analysis.
        
        Current Plan:
        {json.dumps(plan_day)}
        
        Client Context:
        - Age/Gender: {context['profile'].get('age')}/{context['profile'].get('gender')}
        - Unit Pref: {context['profile'].get('units', 'imperial')}
        - Recent Recovery: {json.dumps(context['recoveries'][-1:] if context['recoveries'] else 'No Data')}
        {analysis_section}
        
        Instructions:
        1. If recovery is POOR or analysis recommends lower intensity, lower intensity or suggest modifications in 'notes'.
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

    # Include coaching analysis and recovery insights for better edit responses
    analysis_section = ""
    if user.coach_analysis and "error" not in user.coach_analysis:
        ca = user.coach_analysis
        analysis_section = f"""
Coach's Analysis:
- Recovery: {ca.get('recovery_status', 'N/A')}
- Training Load: {ca.get('training_load_status', 'N/A')}
- Sleep: {ca.get('sleep_status', 'N/A')}
- Readiness: {ca.get('readiness_status', 'N/A')}
"""

    system_prompt = f"""You are an expert Personal Trainer having a conversation with your client about their workout plan.

Current Plan:
{json.dumps(current_plan, indent=2)}

Client Context:
- Age/Gender: {context['profile'].get('age')}/{context['profile'].get('gender')}
- Units: {context['profile'].get('units', 'imperial')}
- Goals: {json.dumps(context['goals']['preferences'])}
- Recent Recovery: {json.dumps(context['recoveries'][-2:] if context['recoveries'] else 'No Data')}
{analysis_section}
Instructions:
1. Respond conversationally — acknowledge what the client wants, explain your changes.
2. Modify the plan according to their request.
3. Keep the same JSON structure for the plan.
4. ALL plan values must be PLAIN STRINGS (no nested objects/arrays).
5. The "routine" field must be a single string with numbered steps separated by newlines. When referencing a named routine/exercise list, format each exercise on its own line with a "- " prefix.
6. Do NOT change the "date" or "block_type" fields.
7. Reference recovery data and coaching analysis when explaining your modifications.

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
