# Personal AI Trainer

## Vision
An intelligent, holistic **AI Personal Trainer** that adapts to your life. Unlike a static plan, this trainer understands your entire week, from workouts to recovery. By integrating **Strava** and **WHOOP**, it dynamically generates detailed workout routines for your scheduled blocks, ensuring you train smarter.

## Key Feature

### 1. Holistic Goal Tracking
- **Short-term & Long-term Goals**: Define what you want to achieve (e.g., "Run comfortably at 5:30/km", "Stay active every day"). The AI considers these when planning every workout.
- **Preferences & Workouts**: Set recurring preferences like "I prefer running over cycling" and specified workouts for the coach to give you when prompted.
- **Upcoming Events**: Dated goals with deadlines that the AI factors into periodization.
- **Collapsible Sections**: Goals panel is organized into Upcoming Events, Preferences, Goals, and Schedule sections.

### 2. Weekly Schedule
- **Configurable Template**: Set your default weekly activities and durations directly in the Goals panel's Schedule section.
- **Editable Blocks**: Click any day in the Week Ahead to edit its type, duration, and notes.
- **Auto-Fill**: Missing days are automatically populated from your saved schedule template without overwriting manual edits.
- **Reset**: The "Reset" button rebuilds all 7 days from your template.

### 3. Smart Data Integration
- **Auto-Sync**: Strava and WHOOP data sync automatically before every plan generation, no manual sync needed.
- **Strava**: Syncs runs, rides, and activity data (distance, pace, suffer score).
- **WHOOP**:
    - **Recovery**: Daily recovery scores, HRV, and sleep performance influence workout intensity.
    - **Workouts**: Syncs strength, functional fitness, and other activities.
- **Sync Status**: A status bar in the Daily Plan shows sync results after each refresh.

### 4. AI Coach's Plan (Rolling 2-Day Plan)
- **Persistent Storage**: Plans are cached on the user model (`plan_today`, `plan_tomorrow`) and persist across page reloads.
- **Rolling Window**: Each day, yesterday's "Tomorrow" becomes "Today" (with recovery-based refinement), and a new "Tomorrow" is generated.
- **Schedule Sync**: The plan's `block_type` is hard-overwritten with the actual schedule, guaranteeing the plan always matches the Week Ahead.
- **Context-Aware Coaching**: The AI considers your Goals, Schedule, Recent Load, and Recovery.
    - *Example*: If you have a "Strength" block and low recovery, it might suggest a lower-intensity session instead of max effort.

### 5. Conversational Plan Editing
- **Pencil Button**: Each day card has an edit icon that opens a chat modal.
- **Chat with Coach**: Ask the AI to modify your plan in natural language (e.g., "Make it 30 min shorter", "I tweaked my ankle", "Swap squats for deadlifts").
- **Live Updates**: The plan card refreshes immediately with the coach's revisions.
- **Persistent**: Edits are saved to the backend and survive page refreshes.

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- `.env` file in `backend/` with:
  ```
  STRAVA_CLIENT_ID=...
  STRAVA_CLIENT_SECRET=...
  WHOOP_CLIENT_ID=...
  WHOOP_CLIENT_SECRET=...
  OPENAI_API_KEY=...
  ```

### Running the App

1. **Start the Backend**:
    ```bash
    cd backend
    uvicorn app.main:app --reload
    ```

2. **Start the Frontend**:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

3. **Access the App**:
    - Frontend: `http://localhost:5173`
    - API Docs: `http://localhost:8000/docs`

### Connecting Integrations
- **Strava**: Visit `http://localhost:8000/auth/strava/login` to authorize.
- **WHOOP**: Visit `http://localhost:8000/auth/whoop/login` to authorize.

After connecting, data syncs automatically whenever you generate or refresh a plan.

## Project Structure

| Path | Description |
|------|-------------|
| **Backend** | |
| `backend/app/main.py` | FastAPI app setup, CORS, router registration |
| `backend/app/models.py` | SQLAlchemy models (User, Goal, WorkoutBlock, etc.) |
| `backend/app/schemas.py` | Pydantic request/response schemas |
| `backend/app/database.py` | Database engine and session configuration |
| `backend/app/routers/auth.py` | OAuth flows for Strava, WHOOP, and user auth |
| `backend/app/routers/coach.py` | AI Coach endpoints (plan generation, plan editing) |
| `backend/app/routers/data.py` | Data endpoints (goals, schedule settings, sync) |
| `backend/app/routers/schedule.py` | Weekly schedule initialization and auto-fill |
| `backend/app/services/ai_coach.py` | GPT-4o integration: context building, plan generation, conversational editing |
| `backend/app/services/strava_client.py` | Strava API client: token refresh, activity sync |
| `backend/app/services/whoop_client.py` | WHOOP API client: token refresh, recovery/workout sync |
| **Frontend** | |
| `frontend/src/App.jsx` | App shell with navigation |
| `frontend/src/pages/Dashboard.jsx` | Main dashboard layout |
| `frontend/src/pages/SettingsPage.jsx` | User profile and integration settings |
| `frontend/src/components/DailyPlan.jsx` | AI Coach plan display with sync status and edit buttons |
| `frontend/src/components/PlanEditChat.jsx` | Chat modal for conversational plan editing |
| `frontend/src/components/WeeklySchedule.jsx` | Week Ahead grid with editable blocks |
| `frontend/src/components/EditBlockModal.jsx` | Modal for editing individual workout blocks |
| `frontend/src/components/GoalList.jsx` | Goals panel with collapsible sections and schedule input |
| `frontend/src/components/GoalModal.jsx` | Modal for creating/editing goals |