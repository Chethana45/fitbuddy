# FitBuddy Project Workflow & Implementation Report

FitBuddy – AI Fitness Plan Generator using Gemini Models  
Complete Milestone & Activity Implementation Guide

---

## Executive Summary

FitBuddy is an intelligent, web-based health-tech application that leverages Google's Generative AI Gemini models to architect personalized 7-day workout schedules and practical nutritional recommendations. Built with **FastAPI**, **SQLite**, **SQLAlchemy ORM**, and modern **Jinja2** dark glassmorphism templates, the platform delivers a seamless, adaptive fitness coaching experience.

---

## Project Scenarios

### Scenario 1: Personalized 7-Day Workout & Nutrition Generation
- **User Action**: The client inputs their name, unique user ID, age, weight (kg), fitness objective (e.g., Weight Loss, Muscle Gain), experience level (Beginner, Intermediate, Advanced), and preferred training intensity (Low, Medium, High).
- **System Execution**: FastAPI processes and validates the form inputs via the `UserInput` Pydantic schema. The backend calls `generate_workout_gemini()` (Gemini 3.1 Pro) to produce a day-by-day workout routine with warm-ups, sets, reps, and cooldowns. Concurrently, `generate_nutrition_tip_with_flash()` (Gemini Flash) generates an actionable dietary tip.
- **Persistence & Output**: Records are stored in `fitbuddy.db` (`users` and `plans` tables) and displayed on `result.html` with interactive 7-day cards and a progress tracker.

### Scenario 2: Feedback-Driven Adaptive Plan Refinement
- **User Action**: A user reviews their active plan and requests changes, such as *"Add yoga on Day 3"* or *"Reduce impact on knees"*, or clicks a quick suggestion chip.
- **System Execution**: The form submits a `POST /submit-feedback` request with `plan_id` and natural-language instructions. `update_workout_plan()` sends the original plan and user feedback to Gemini 3.1 Pro.
- **Persistence & Output**: The refined plan is stored in `plans.updated_plan` while `plans.original_plan` is preserved. `result.html` refreshes with a visible "Plan Updated" badge.

### Scenario 3: Goal-Aligned Targeted Nutrition & Recovery
- **User Action**: The client selects their fitness goal during intake.
- **System Execution**: Gemini Flash generates targeted dietary advice specific to the selected goal (e.g., post-workout protein targets for Muscle Gain, caloric deficit guidance for Weight Loss, complex carbs for Endurance).
- **Output**: Displayed prominently in a dedicated nutrition banner on the results page.

### Scenario 4: Coach & Admin Dashboard Oversight
- **User Action**: A fitness coach or administrator accesses `/view-all-users`.
- **System Execution**: The server fetches all registered users, workout plans, and day completion records.
- **Output**: `all_users.html` presents an administrative dashboard with aggregate KPI cards, client summary tables, day-by-day completion bars, expandable JSON inspection drawers, and client deletion actions.

---

## Technical Architecture Overview

```
+-------------------------------------------------------------------------------+
|                               User (Web Browser)                             |
+---------------------------------------+---------------------------------------+
                                        | HTTP Form Submissions / REST Calls
                                        v
+-------------------------------------------------------------------------------+
|                    FastAPI Application Entry (app/main.py)                    |
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

## Milestone 1: Model Selection and Architecture

### Activity 1.1: Research and Select the Appropriate Generative AI Model

#### 1. Project Requirements Analysis
The AI model needed to:
- Generate strictly structured 7-day workout plans with warm-up, core exercise sets/reps, and cooldowns.
- Provide concise, practical dietary recommendations.
- Refine existing plans dynamically according to user feedback.
- Deliver rapid, low-latency inference suitable for web interfaces.
- Feature reliable local fallback capabilities when API keys or quotas are constrained.

#### 2. Comparative Model Evaluation
Prior to choosing Gemini, several open-source and Hugging Face alternatives were evaluated:
- **T5 & BART**: Effective for text summarization, but struggled to maintain strict 7-day JSON structures without fine-tuning.
- **DistilBERT**: Suitable for classification, but lacks multi-day generative instruction-following capabilities.
- **Bloom**: General-purpose LLM, but demanded heavy local GPU infrastructure or hosted Hugging Face endpoints with higher latency.

#### 3. Final Model Selection: Google Gemini
Google Gemini was selected for production:
- **Gemini 3.1 Pro (`gemini-3.1-pro`)**:
  - Assigned to **Workout Plan Generation** and **Plan Refinement via Feedback**.
  - Excels at complex instruction adherence, multi-turn context retention, and strict JSON output formatting.
- **Gemini Flash (`gemini-3.8-flash`)**:
  - Assigned to **Nutrition & Recovery Tip Generation**.
  - Optimized for lightweight, sub-second latency and direct dietary heuristics.

#### Key Advantages of Gemini:
- Direct API integration with Python SDK (`google-genai` and `google-generativeai`).
- High prompt comprehension with zero-shot structured JSON output.
- Scalable, cost-effective, and robust with exponential backoff retries.

### Activity 1.2: Define the Application Architecture
- **Frontend**: Responsive HTML5, Jinja2 dynamic templates, modern glassmorphism CSS, and vanilla JavaScript.
- **Backend**: FastAPI web framework with asynchronous lifespans, route handlers, and Pydantic validation.
- **AI Integration**: Dual Gemini engine orchestrating workout creation and nutrition advice.
- **Database**: SQLite embedded database managed through SQLAlchemy ORM with foreign keys and cascade deletions.

### Activity 1.3: Set Up the Development Environment
Directory structure:
```text
fitbuddy/
├── requirements.txt            # Project dependencies
├── .env.example                # Template for environment variables
├── .env                        # Local environment configuration
├── fitbuddy.db                 # SQLite database (auto-generated)
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── routes.py               # Core route handlers
│   ├── database.py             # SQLAlchemy models and persistence logic
│   ├── schemas.py              # Pydantic validation models
│   ├── gemini_generator.py     # Gemini Pro workout generator
│   ├── gemini_flash_generator.py # Gemini Flash nutrition tip generator
│   ├── updated_plan.py         # Feedback-based plan updater
│   ├── nutrition.py            # Nutrition macro splits and food lists
│   └── templates/
│       ├── index.html          # Form intake page
│       ├── result.html         # 7-Day plan & feedback page
│       └── all_users.html      # Admin dashboard page
├── static/
│   ├── css/
│   │   └── style.css           # Glassmorphism styling
│   ├── js/
│   │   └── script.js           # Client-side interactivity
│   └── images/
│       └── gym-bg.jpg          # Fitness backdrop image
├── docs/                       # Architecture, API & testing documentation
└── tests/                      # Automated pytest validation suite
```

---

## Milestone 2: Core Functionalities Development

### Activity 2.1: Develop the Core Functionalities
1. **Workout Plan Generation (`gemini_generator.py`)**:
   - Implements `generate_workout_gemini()` and `generate_workout_with_status()`.
   - Sends client parameters (name, age, weight, goal, intensity) to Gemini 3.1 Pro.
   - Extracts and validates a 7-day JSON dictionary containing `focus`, `warmup`, `exercises` (with `name`, `sets`, `reps`), and `cooldown`.
   - Fallback engine: Supplies deterministic, goal-specific offline plans if the API key is absent or quota is exceeded.

2. **Nutrition Tip Generation (`gemini_flash_generator.py`)**:
   - Implements `generate_nutrition_tip_with_flash(goal)`.
   - Uses Gemini Flash to return 1–2 practical, science-backed dietary tips tailored to the selected goal.

3. **Feedback-Based Plan Updating (`updated_plan.py`)**:
   - Implements `update_workout_plan(original_plan, feedback)`.
   - Sends the current plan and user requests to Gemini 3.1 Pro to revise specific days while preserving the overall training structure.

4. **User & Plan Persistence (`database.py`)**:
   - `save_user()`: Persists client profile details.
   - `save_plan()`: Stores the initial plan and nutrition tip.
   - `update_plan()`: Saves modified plans into `updated_plan` without overwriting `original_plan`.
   - `get_original_plan()`, `get_user()`, `get_all_users()`, `get_all_plans()`: Query operations for result rendering and administrative oversight.
   - `mark_workout_day_complete()`, `get_user_progress_summary()`: Daily workout checklist management.
   - `delete_user_with_associated_data()`: Cascade delete removing user, plans, and progress records.

5. **Admin View (`all_users.html`)**:
   - Accessible via `/view-all-users`, allowing coaches to review client registrations, activity timestamps, original vs. updated JSON plans, and progress percentages.

### Activity 2.2: Implement FastAPI Backend & Validation
- **Pydantic Schemas (`schemas.py`)**:
  - `UserInput`: Validates `username`, `user_id`, `age` (10–100), `weight` ($\ge 20$), `goal`, `intensity` (`low|medium|high`), and `experience_level`.
  - `FeedbackRequest`: Validates `plan_id` and non-empty `feedback`.
- **Form Capture**: Captures HTML form data via `Form(...)` parameters, mapping directly to schemas and catching invalid requests with HTTP 422.

---

## Milestone 3: routes.py Development

### Activity 3.1: Main Application Logic in `routes.py`
The router acts as the operational hub connecting templates, AI generators, and database models:
- **`GET /`**: Renders `index.html`.
- **`POST /generate-workout`**:
  - Validates form inputs.
  - Generates workout and nutrition tips via Gemini.
  - Persists user and plan records.
  - Returns `result.html` with dynamic context.
- **`GET /result/{plan_id}`**: Retrieves and displays an active plan by primary key.
- **`POST /submit-feedback`**:
  - Fetches the active plan.
  - Queries Gemini 3.1 Pro for plan adjustments.
  - Updates `plans.updated_plan` in the database.
  - Renders `result.html` with an updated badge.
- **`GET /view-all-users`**: Aggregates all user profiles, plans, and completion metrics for coach oversight.
- **`POST /admin/users/{user_id}/delete`**: Administrative record cleanup with cascade deletion.
- **Progress Tracking Routes**: `GET /progress/{user_id}` and `POST /progress/{user_id}/{day_number}/complete`.

---

## Milestone 4: Frontend Development

### Activity 4.1: UI Design & Styling
- **Base Layout**: Semantic HTML5 with dark fitness theme, responsive Flexbox and CSS Grid layouts.
- **Visual Style**: Dark Glassmorphism with translucent surfaces, frosted glass blur, neon accent borders, and responsive cards.
- **Interactive Controls**:
  - Pill-based training intensity selectors (🐢 Low, 🏃 Medium, 🔥 High).
  - Quick-fill plan refinement chips (e.g., *"Add 15m Yoga"*, *"Upper Body Focus"*).
  - Animated loading spinners during AI generation.

### Activity 4.2: Dynamic Jinja2 Templates
- **`index.html`**: User intake form bound to `/generate-workout`.
- **`result.html`**:
  - Client profile header with metadata chips.
  - Interactive 7-day plan cards colored by day index.
  - Exercise sub-lists with sets, reps, warm-ups, and cooldowns.
  - Nutrition tip highlight card.
  - Day completion checklist and visual progress bar.
  - Feedback input form for plan updates.
- **`all_users.html`**:
  - KPI summary metric cards (Total Users, Active Tracking, AI Engine Status).
  - Data table with client avatars, status tags, expandable JSON plan inspection drawers, and deletion actions.

---

## Milestone 5: Deployment & Verification

### Activity 5.1: Preparing the Application for Local Deployment
1. Virtual environment setup:
   ```powershell
   python -m venv fitbuddy-env
   .\fitbuddy-env\Scripts\activate
   ```
2. Dependency installation:
   ```powershell
   pip install -r requirements.txt
   ```
3. Configuration:
   ```powershell
   copy .env.example .env
   ```
   Configure `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) in `.env`.

### Activity 5.2: Testing and Verifying Deployment
1. Start the server:
   ```powershell
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
2. Verify endpoints:
   - Application Homepage: `http://127.0.0.1:8000/`
   - Admin Dashboard: `http://127.0.0.1:8000/view-all-users`
   - Interactive Swagger API Documentation: `http://127.0.0.1:8000/docs`
3. Automated test execution:
   ```powershell
   python -m pytest
   ```
   **Result**: 8 of 8 test cases passed with 100% success rate across input validation, database persistence, plan updating, progress tracking, fallback behavior, and admin cascade deletion.
