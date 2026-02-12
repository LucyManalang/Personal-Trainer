# Personal AI Running Coach

## Vision
To build an intelligent, adaptive running coach that leverages diverse data sources to optimize marathon training. By integrating **Strava** (performance data) and **WHOOP** (physiological recovery data), the AI Coach dynamically adjusts daily training recommendations. It balances training load with recovery capacity, ensuring athletes train smarter, reduce injury risk, and peak at the right time.

## Current Progress

### Backend Infrastructure
- **FastAPI** application structure with SQLite database.
- **SQLAlchemy** ORM models for Users, Activities, Recoveries, and Training Plans.
- **Authentication**: OAuth2 implementation for both Strava and WHOOP APIs.

### Data Integration
- **Strava Integration**: Syncs run activities including distance, moving time, elevation, and heart rate data.
- **WHOOP Integration**: Syncs daily recovery scores, HRV, resting heart rate, and sleep performance. Auto-refreshes tokens and handles API errors gracefully.
- **Seeding Tools**: Development scripts (`backend/seed_recoveries.py`) to populate the database with mock physiological data for testing logic without live API limits.

### AI Coach Engine
- **Context Awareness**: Aggregates the last 28 days of training load and 7 days of recovery trends to inform decision-making.
- **Plan Generation**: Uses **GPT-4o** to generate structured, 7-day training schedules in JSON format.
- **Logic**: Applies elite coaching principles—reducing intensity when recovery is low (<33%) and capitalizing on high-recovery days (>66%).

## Next Steps

### 1. Frontend Interface
- Build a web dashboard (React/Next.js) for users to:
  - View their current training plan.
  - See visualization of Training Load vs. Recovery.
  - Manually trigger data syncs.

### 2. Automation & Scheduling
- Implement background tasks (e.g., Celery) to automatically sync data and regenerate daily advice every morning.
- Send push notifications or emails with the day's workout.

### 3. Advanced AI Features
- **Long-term Periodization**: Extend planning horizon beyond 7 days to manage macro-cycles (base, build, taper).
- **Metric Analytics**: Calculate Acute-to-Chronic Workload Ratio (ACWR) to better predict injury risk.
- **Feedback Loop**: Allow users to rate completed workouts ("Too hard", "Too easy") to fine-tune future intensity.