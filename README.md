# Personal AI Trainer

## Vision
An intelligent, holistic **AI Personal Trainer** that adapts to your life. Unlike a static plan, this trainer understands your entire week—from Ultimate Frisbee to Cardio and Recovery. By integrating **Strava** and **WHOOP**, it dynamically generates detailed workout routines for your scheduled blocks, ensuring you train smarter, not just harder.

## Key Features

### 1. Holistic Goal Tracking
- **Short-term & Long-term Goals**: Define what you want to achieve (e.g., "Run comfortably at 5:30/km", "Chicago Marathon"). The AI considers these when planning every workout.
- **Preferences**: Set recurring preferences like "Incorporate Yoga twice a week" or "Sleep 8 hours a night".

### 2. Weekly Scheduling (Week Ahead)
- **Flexible Blocking**: Block out your week with high-level types (Cardio, Strength, Ultimate, Recovery, etc.) and durations.
- **Editable Blocks**: Click any day in the Week Ahead to edit its type, duration, and notes.
- **Default Schedule**: Initialize a fresh weekly schedule with your preferred defaults (e.g., Ultimate on Sun/Tue).
- **Auto-Load**: The schedule automatically loads on page refresh using your local timezone.

### 3. Smart Data Integration
- **Strava**: Syncs runs, paces, and heart rate data.
- **WHOOP**: 
    - **Recovery**: Daily recovery scores, HRV, and sleep performance influence workout intensity.
    - **Workouts**: Syncs strength, functional fitness, and other non-running activities.

### 4. AI Coach's Plan (Rolling 2-Day Plan)
- **Persistent Storage**: Plans are stored in the database (`plan_today`, `plan_tomorrow`) so they persist across page reloads without extra API calls.
- **Rolling Window**: Each day, yesterday's "Tomorrow" becomes "Today" (with recovery-based refinement), and a new "Tomorrow" is generated.
- **Schedule Sync**: The plan's `block_type` is **hard-overwritten** with the actual schedule from the database, guaranteeing the Coach's Plan always matches the Week Ahead.
- **Auto-Load**: The plan automatically loads on page refresh.
- **Context-Aware Coaching**: The AI considers your Goals, Schedule, Recent Load, and Recovery.
    - *Example*: If you have a "Strength" block and low recovery, it might suggest a "Low-Intensity Technical Session" instead of a "Max Effort Power Day".

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- `uvicorn` and `fastapi`
- `.env` file with API keys for Strava, WHOOP, and OpenAI.

### Running the App

1.  **Start the Backend**:
    ```bash
    cd backend
    uvicorn app.main:app --reload
    ```

2.  **Start the Frontend**:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

3.  **Access the App**:
    - Frontend: `http://localhost:5173`
    - API Docs: `http://localhost:8000/docs`

### Resetting the Schedule
If the weekly schedule gets out of sync, you can reset it:
1.  Click the **"Initialize / Reset"** button in the Week Ahead section, or
2.  Run the reset script manually:
    ```bash
    cd backend
    python3 reset_schedule.py
    ```
    Then click "Initialize / Reset" in the UI to regenerate.

### Resetting the Daily Plan
To force a fresh AI plan generation:
```bash
cd backend
python3 reset_plan.py
```
Then refresh the page.

## Project Structure

| Path | Description |
|------|-------------|
| `backend/app/models.py` | Database schemas (User, Goal, WorkoutBlock, etc.) |
| `backend/app/services/ai_coach.py` | The brain — aggregates data, prompts GPT-4o, enforces schedule sync |
| `backend/app/routers/schedule.py` | Weekly blocking logic and schedule initialization |
| `backend/app/routers/coach.py` | AI Coach API endpoints |
| `backend/app/services/whoop_client.py` | WHOOP OAuth and data syncing |
| `frontend/src/components/DailyPlan.jsx` | Coach's Plan UI (auto-loading, formatted steps) |
| `frontend/src/components/WeeklySchedule.jsx` | Week Ahead UI (editable blocks, timezone-safe) |
| `frontend/src/components/EditBlockModal.jsx` | Modal for editing individual workout blocks |
| `backend/reset_schedule.py` | Utility to clear and reset the weekly schedule |
| `backend/reset_plan.py` | Utility to clear the stored daily plan |