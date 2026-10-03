# FitBuddy - AI Fitness Plan Generator using Gemini Models

## Overview

FitBuddy is a FastAPI web application that creates a personalized seven-day
workout plan and nutrition/recovery tip. Users can refine the active plan with
natural-language feedback while the original plan remains preserved.

## Features

- Validated name, user ID, age, weight, goal, and intensity input.
- Gemini-powered workout, nutrition, and feedback generation.
- Safe local fallback content when Gemini is unavailable.
- SQLite and SQLAlchemy persistence for users and plans.
- Responsive Jinja2 pages and a coach/admin dashboard.
- Fitness safety disclaimer and friendly error messages.

## Technology Stack

Python, FastAPI, Uvicorn, Google Gemini SDK, SQLite, SQLAlchemy, Pydantic,
Jinja2, HTML, CSS, and JavaScript.

## System Architecture

The browser submits forms to `app/routes.py`. Route handlers validate input,
call the Gemini modules, persist records through `app/database.py`, and render
Jinja2 templates. The database stores both `original_plan` and
`updated_plan`.

## Project Structure

```text
app/                 FastAPI application and domain modules
app/templates/       Jinja2 templates
static/css/          Shared CSS
static/js/           Browser interactions
static/images/       Existing gym background
docs/                Architecture, API, and testing documentation
```

## Setup

```powershell
python -m venv fitbuddy-env
fitbuddy-env\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Set `GEMINI_API_KEY` in `.env`, then run:

```powershell
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 and the API documentation at
http://127.0.0.1:8000/docs.

The Uvicorn terminal logs Gemini request start, success, and sanitized failure
messages. API keys and prompts are never logged.

## Environment Variables

| Variable | Purpose |
| --- | --- |
| `GEMINI_API_KEY` | Gemini API key; optional for local fallback mode |
| `GEMINI_WORKOUT_MODEL` | Workout and refinement model (default: `gemini-3.5-flash-lite`) |
| `GEMINI_NUTRITION_MODEL` | Nutrition tip model (default: `gemini-3.5-flash-lite`) |

## API Routes

- `GET /` - homepage form.
- `POST /generate-workout` - creates a user and plan.
- `GET /result/{plan_id}` - displays the active plan.
- `POST /submit-feedback` - refines the active plan.
- `GET /view-all-users` - coach/admin dashboard.

## Database

SQLite is stored in `fitbuddy.db`. SQLAlchemy models store users, the submitted
user ID, and one or more related plans. Refinement writes only `updated_plan`.

## Gemini Integration

Workout and refinement prompts request a strict seven-day JSON structure.
Nutrition uses a concise goal-specific prompt. Model names are configurable and
all calls have safe fallback behavior.

## Testing

The validation status is recorded in [docs/testing.md](docs/testing.md).

## Future Enhancements

Authentication for the dashboard, database migrations, automated integration
tests, and a richer plan history view would be useful next steps.
