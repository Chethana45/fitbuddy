# FitBuddy Technical Architecture

## 1. Overview & Objectives

**FitBuddy** is an AI-powered fitness and nutrition planning platform designed to democratize access to personalized, structured, and goal-oriented fitness regimens. The application leverages Google's Gemini models to generate customized 7-day workout schedules, actionable dietary recommendations, and adaptive plan refinements based on natural-language user feedback.

---

## 2. Technical Architecture Diagram

```
+-------------------------------------------------------------------------------+
|                               User (Web Browser)                             |
+---------------------------------------+---------------------------------------+
                                        | HTTP Requests (Form / AJAX)
                                        v
+-------------------------------------------------------------------------------+
|                    FastAPI Backend (app/main.py & lifespan)                   |
+-------------------+-------------------+-------------------+-------------------+
                    |                   |                   |
                    v                   v                   v
     +--------------------+ +-------------------+ +--------------------+
     |   HTML Templating  | |   Workout Logic   | |    Admin Panel     |
     |   (Jinja2 + CSS)   | |  (routes.py + AI) | |  /view-all-users   |
     +----------+---------+ +---------+---------+ +----------+---------+
                |                     |                      |
                v                     v                      v
        [ index.html ]        [ result.html ]        [ all_users.html ]
         (Input Form)           (Plan Page)          (Coach Dashboard)
                                      |
                                      v
     +------------------------------------------------------------------+
     |      Gemini 3.1 Pro & Gemini Flash API (Google Generative AI)    |
     |  - Workout Plan Generator (app/gemini_generator.py)              |
     |  - Nutrition Tip Generator (app/gemini_flash_generator.py)       |
     +--------------------------------+---------------------------------+
                                      |
                                      v
     +------------------------------------------------------------------+
     |         Feedback-Based AI Plan Updater (app/updated_plan.py)      |
     |  - Preserves original plan & generates adaptive revision         |
     +--------------------------------+---------------------------------+
                                      |
                                      v
     +------------------------------------------------------------------+
     |            SQLite + SQLAlchemy ORM Persistence (fitbuddy.db)     |
     |  - User Table (`users`): user_id, name, age, weight, goal, level  |
     |  - WorkoutPlan Table (`plans`): original_plan, updated_plan, tip |
     |  - WorkoutProgress Table (`workout_progress`): day completion    |
     +------------------------------------------------------------------+
```

---

## 3. Core System Components

### 3.1 Frontend Presentation Layer
- **HTML5 & Semantic Structure**: Modular forms and presentation cards capturing user inputs and displaying day-by-day routines.
- **Modern Dark Glassmorphism CSS (`static/css/style.css`)**: Glass cards with background blur (`backdrop-filter: blur(20px)`), neon accents, responsive Flexbox/Grid layouts, custom scrollbars, and accessible form controls.
- **Interactive JavaScript (`static/js/script.js`)**: Real-time form validation, training intensity selector pills, plan refinement chip autofill, and animated loading spinners.
- **Jinja2 Templating Engine**: Dynamic server-side rendering of user plans, exercise tables, progress trackers, and coach management metrics.

### 3.2 Backend Application Layer (FastAPI)
- **FastAPI Framework (`app/main.py`)**: Asynchronous, high-performance web framework providing automated OpenAPI documentation at `/docs` and route orchestration.
- **Routing Engine (`app/routes.py`)**: Handles incoming HTTP requests, validates form payloads, triggers Gemini AI generators, persists records, and returns rendered Jinja2 templates.
- **Validation Schemas (`app/schemas.py`)**: Strict Pydantic models (`UserInput`, `FeedbackRequest`) enforcing bounds on user age, weight, fitness goals, and training intensity.

### 3.3 Artificial Intelligence Layer (Google Gemini)
- **Workout Plan Generator (`app/gemini_generator.py`)**: Employs **Gemini 3.1 Pro** (`gemini-3.1-pro` or configurable) to craft comprehensive 7-day workout plans structured strictly in JSON format (including warm-up, core exercise sets/reps, and cooldown).
- **Nutrition Tip Generator (`app/gemini_flash_generator.py`)**: Utilizes **Gemini Flash** (`gemini-3.8-flash`) for sub-second delivery of targeted, goal-aligned nutritional advice.
- **Feedback-Based Plan Updater (`app/updated_plan.py`)**: Accepts an existing plan and natural-language user feedback (e.g., *"more core work"*, *"replace squats due to knee pain"*), producing an updated workout plan while leaving the original plan intact in the database.
- **Nutrition Logic Helper (`app/nutrition.py`)**: Provides dietary macronutrient distributions and food focus lists for all goals.
- **Resilience & Fallback**: Automatic multi-tier retries with exponential backoff on 429 quota limits, and safe deterministic offline fallback plans when API keys are absent.

### 3.4 Data Persistence Layer (SQLite + SQLAlchemy)
- **Database Engine**: Local SQLite database stored in `fitbuddy.db`.
- **SQLAlchemy ORM (`app/database.py`)**: Manages object-relational mapping, database transactions, foreign key constraints, cascade deletions, and automatic schema migrations.
  - **`users` Table**: Stores client name, age, weight, goal, intensity, experience level, custom user ID, and last activity timestamp.
  - **`plans` Table (`WorkoutPlan`)**: Stores relationship to user, original JSON plan, updated JSON plan, nutrition tip, and creation timestamps.
  - **`workout_progress` Table**: Tracks day-by-day (Day 1 to Day 7) completion states with unique constraints and timestamped check-ins.

---

## 4. End-to-End Data Flow

### Scenario 1: Initial Plan Generation
1. The user navigates to `/` and inputs their name, user ID, age, weight, fitness goal, experience level, and intensity.
2. The browser submits a `POST /generate-workout` request.
3. FastAPI parses and validates the form data via `UserInput`.
4. `generate_workout_gemini()` contacts Gemini 3.1 Pro to generate a structured 7-day schedule.
5. Concurrently, `generate_nutrition_tip_with_flash()` queries Gemini Flash for a concise dietary tip.
6. `save_user()` and `save_plan()` persist the profile and original plan to `fitbuddy.db`.
7. `result.html` is rendered displaying the 7-day plan, nutrition tip, and workout progress tracker.

### Scenario 2: Adaptive Feedback Refinement
1. On `result.html`, the user enters natural-language feedback or selects a quick suggestion chip.
2. Form submits `POST /submit-feedback` with `plan_id` and `feedback`.
3. `get_original_plan()` fetches the active plan from `fitbuddy.db`.
4. `update_workout_plan()` invokes Gemini 3.1 Pro with the original plan and the user's modifications.
5. `update_plan()` saves the resulting plan into `plans.updated_plan` (preserving `plans.original_plan`).
6. `result.html` re-renders with a "Plan Updated" badge and the refined workout plan.

### Scenario 3: Targeted Nutrition Guidance
1. Gemini Flash evaluates the user's goal (`Weight Loss`, `Muscle Gain`, `Endurance`, `General Fitness`, or `Mobility`).
2. Gemini returns high-impact dietary guidance (e.g., protein targets, hydration timing, or caloric distribution).
3. The tip is displayed in a dedicated card on the result page.

### Scenario 4: Coach & Admin Oversight
1. A trainer accesses `/view-all-users`.
2. The server queries `get_all_users()` and `get_all_plans()`.
3. `all_users.html` renders a management dashboard featuring KPI cards, client summary tables, day-completion metrics, JSON plan inspection drawers, and record deletion controls.
