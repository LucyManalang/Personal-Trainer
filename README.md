# Personal AI Trainer

## Vision
To build an intelligent, holistic **AI Personal Trainer** that helps you achieve your fitness goals by adapting to your life. Unlike a static plan or a simple running coach, this trainer understands your entire week—from Strength training to Cardio and Recovery. By integrating **Strava** (runs/activities) and **WHOOP** (sleep, recovery, non-running workouts), it dynamically generates detailed workout routines for your scheduled blocks, ensuring you train smarter, not just harder.

## Key Features

### 1. Holistic Goal Tracking
- **Short-term & Long-term Goals**: Define what you want to achieve (e.g., "Improve 5k time", "Increase Bench Press"). The AI considers these goals when planning every workout.

### 2. Weekly Scheduling
- **Flexible Blocking**: "Block out" your week in advance with high-level types (Strength, Cardio, Recovery, etc.) and durations.
- **Life-First Design**: The trainer fills in the details *for* you based on these blocks, respecting your time constraints.
- **Endpoints**:
    - `POST /schedule/init`: Automatically generates a default weekly structure.
    - `PUT /schedule/{id}`: Modify blocks to fit your changing schedule.

### 3. Smart Data Integration
- **Strava**: Syncs your runs, paces, and heart rate data.
- **WHOOP**: 
    - **Recovery**: Daily recovery scores, HRV, and sleep performance influence workout intensity.
    - **Workouts**: Syncs strength, functional fitness, and other non-running activities to give the AI a complete picture of your strain.

### 4. AI-Powered Planning (Next 3 Days)
- **Context-Aware Coaching**: The AI looks at your:
    - **Goals**
    - **Schedule** (What available time do I have?)
    - **Recent Load** (What have I done lately?)
    - **Recovery** (How ready am I to perform?)
- **Detailed Routines**: It generates specific instructions for your next 3 days. 
    - *Example*: If you have a "Strength" block and low recovery, it might suggest a "Low-Intensity Technical Session" instead of a "Max Effort Power Day".

## Getting Started

### Prerequisites
- Python 3.9+
- `uvicorn` and `fastapi`
- `.env` file with API keys for Strava, WHOOP, and OpenAI.

### Running the App
1.  **Start the Server**:
    ```bash
    uvicorn app.main:app --reload
    ```
2.  **Access the API Docs**:
    Go to `http://localhost:8000/docs` to interact with the endpoints.

### Testing the "Personal Trainer" Flow
We have included a comprehensive test script to demonstrate the full loop:
1.  **Ensure Server is STOPPED** (to avoid database locks).
2.  Run the test script:
    ```bash
    python3 backend/test_personal_trainer_flow.py
    ```
    This script will:
    - Create a sample User and Goal (if missing).
    - Ensure your next 3 days have Workout Blocks.
    - Call the AI Coach to generate a detailed plan.
    - Print the JSON plan to the console.

## Project Structure
- `backend/app/models.py`: Database schemas (User, Goal, WorkoutBlock, WhoopWorkout, etc.).
- `backend/app/services/ai_coach.py`: The brain. Aggregates data and prompts GPT-4o.
- `backend/app/routers/schedule.py`: Manages the weekly blocking logic.
- `backend/app/services/whoop_client.py`: Handles OAuth and data syncing (Recovery, Sleep, Workouts).