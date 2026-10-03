# FitBuddy Architecture

## Problem and objective

FitBuddy makes a beginner-friendly seven-day fitness plan easier to create and
refine without replacing professional medical or fitness advice.

## Model selection

Google Gemini is used because the project requires Gemini and its generative
API can produce structured plans and natural-language refinements. Workout and
nutrition model IDs are environment-configurable.

## Components and data flow

1. A Jinja2 form sends validated profile data to FastAPI.
2. The route asks Gemini for a seven-day JSON plan and a recovery tip.
3. SQLAlchemy stores the user and original plan in SQLite.
4. The result page renders the active plan.
5. Feedback is sent with the current active plan; the response is stored as
   `updated_plan`, leaving `original_plan` unchanged.
6. The dashboard reads users and their latest plans.

## Database design

`User` has a one-to-many relationship with `Plan`. `User.user_id` stores the
identifier entered in the form. `Plan` stores original and updated JSON,
nutrition tip, and timestamps.

## Safety and resilience

Prompts request age- and intensity-appropriate suggestions and avoidance of
unsafe recommendations. Missing credentials, API failures, and malformed JSON
use safe local content without exposing stack traces or secrets.
