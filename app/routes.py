"""
routes.py
Core route handlers for the FitBuddy FastAPI application.

Route map
─────────
GET  /                  → index.html  (user input form)
POST /generate-workout  → calls generate_workout_gemini() + generate_nutrition_tip_with_flash()
GET  /result/{plan_id}  → result.html (plan display + feedback form)
POST /submit-feedback   → calls update_workout_plan() with original plan + feedback
GET  /view-all-users    → all_users.html (admin dashboard)
"""

import json
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .database import (
    User,
    delete_user_with_associated_data,
    get_all_users,
    get_db,
    get_original_plan,
    get_user,
    get_user_progress_summary,
    get_user_progress_summary_api,
    mark_workout_day_complete,
    save_plan,
    save_user,
    touch_user_activity,
    update_plan,
)
from .gemini_generator import generate_workout_with_status
from .gemini_flash_generator import generate_nutrition_tip_with_flash
from .updated_plan import update_workout_plan

# ---------------------------------------------------------------------------
# Templates (resolved relative to this file's directory)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

router = APIRouter()
VALID_GOALS = {
    "Weight Loss", "Muscle Gain", "Improve Endurance",
    "General Fitness", "Flexibility & Mobility",
}
VALID_EXPERIENCE_LEVELS = {"Beginner", "Intermediate", "Advanced"}
SAFETY_DISCLAIMER = (
    "FitBuddy provides AI-generated fitness suggestions for general informational "
    "purposes only. Consult a qualified healthcare or fitness professional before "
    "starting a new exercise or nutrition program, especially if you have medical "
    "conditions or injuries."
)


def _build_progress_context(db: Session, user: User | None):
    if user is None:
        return {
            "completed_days": 0,
            "total_days": 7,
            "progress_percentage": 0,
            "day_status": {day: False for day in range(1, 8)},
            "user_last_activity": None,
        }

    summary = get_user_progress_summary(db, user.id)
    user_last_activity = user.last_activity.isoformat() if user.last_activity else None
    return {
        "completed_days": summary["completed_days"],
        "total_days": summary["total_days"],
        "progress_percentage": summary["progress_percentage"],
        "day_status": summary["day_status"],
        "user_last_activity": user_last_activity,
    }


# ---------------------------------------------------------------------------
# GET /  –  User input form
# ---------------------------------------------------------------------------
@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})


# ---------------------------------------------------------------------------
# POST /generate-workout  –  Scenario 1: process form → generate plan + tip
# ---------------------------------------------------------------------------
@router.post("/generate-workout",
             summary="Generate a personalised 7-day workout plan",
             description="Accepts HTML form input (UserInput schema), calls Gemini for the "
                         "workout plan and nutrition tip, persists both, and renders the result page.")
async def generate_workout(
    request: Request,
    username: str = Form(..., description="Display name of the user"),
    user_id: str = Form(..., description="Unique user identifier"),
    age: int = Form(..., ge=10, le=100),
    weight: float = Form(..., ge=20.0, description="Weight in kg"),
    goal: str = Form(..., description="Fitness goal"),
    intensity: str = Form(..., description="low | medium | high"),
    experience_level: str = Form(..., description="Beginner | Intermediate | Advanced"),
    db: Session = Depends(get_db),
):
    if not username.strip() or not user_id.strip():
        raise HTTPException(status_code=422, detail="Name and User ID are required.")
    if goal not in VALID_GOALS:
        raise HTTPException(status_code=422, detail="Please select a valid fitness goal.")
    if intensity not in {"low", "medium", "high"}:
        raise HTTPException(status_code=422, detail="Please select a valid intensity.")
    if experience_level not in VALID_EXPERIENCE_LEVELS:
        raise HTTPException(status_code=422, detail="Please select a valid experience level.")
    try:
        user = save_user(
            db,
            name=username,
            age=age,
            weight=weight,
            goal=goal,
            intensity=intensity,
            user_id=user_id.strip(),
            experience_level=experience_level,
            last_activity=datetime.now(timezone.utc),
        )
        touch_user_activity(db, user.id)

        plan_dict, used_fallback = generate_workout_with_status(
            username, age, weight, goal, intensity, experience_level
        )
        tip = generate_nutrition_tip_with_flash(goal)
        plan = save_plan(db, user_id=user.id, original_plan=json.dumps(plan_dict), nutrition_tip=tip)

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="The plan could not be saved. Please try again.")
    except RuntimeError:
        raise HTTPException(status_code=502, detail="The AI service returned an invalid response.")

    progress_context = _build_progress_context(db, user)
    return templates.TemplateResponse(request, "result.html", {
        "request": request,
        "username": username,
        "age": age,
        "weight": weight,
        "goal": goal,
        "intensity": intensity,
        "experience_level": experience_level,
        "user_id": user_id,
        "user_pk_id": user.id,
        "workout_plan": plan_dict,
        "nutrition_tip": tip,
        "plan_id": plan.id,
        "is_updated": False,
        "used_fallback": used_fallback,
        "safety_disclaimer": SAFETY_DISCLAIMER,
        **progress_context,
    })


# ---------------------------------------------------------------------------
# GET /result/{plan_id}  –  Display plan, tip, and feedback form
# ---------------------------------------------------------------------------
@router.get("/result/{plan_id}")
async def result(request: Request, plan_id: int, db: Session = Depends(get_db)):
    plan = get_original_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")

    active_json = plan.updated_plan if plan.updated_plan else plan.original_plan
    try:
        active_plan = json.loads(active_json)
    except json.JSONDecodeError:
        active_plan = {}

    u = plan.user
    progress_context = _build_progress_context(db, u)
    return templates.TemplateResponse(request, "result.html", {
        "request": request,
        "username": u.name if u else "",
        "age": u.age if u else "",
        "weight": u.weight if u else "",
        "goal": u.goal if u else "",
        "intensity": u.intensity if u else "",
        "experience_level": u.experience_level if u else "Beginner",
        "user_id": u.user_id if u else "",
        "user_pk_id": u.id if u else None,
        "workout_plan": active_plan,
        "nutrition_tip": plan.nutrition_tip,
        "plan_id": plan.id,
        "is_updated": bool(plan.updated_plan),
        "used_fallback": False,
        "safety_disclaimer": SAFETY_DISCLAIMER,
        **progress_context,
    })


# ---------------------------------------------------------------------------
# POST /submit-feedback
# ---------------------------------------------------------------------------
@router.post("/submit-feedback",
             summary="Refine an existing workout plan",
             description="Accepts plan_id + free-text feedback. The plan is updated and saved separately from the original.")
async def submit_feedback(
    request: Request,
    plan_id: int = Form(..., gt=0, description="ID of the plan to refine"),
    feedback: str = Form(..., min_length=1, description="User feedback for plan refinement"),
    db: Session = Depends(get_db),
):
    plan = get_original_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")

    try:
        base_json = plan.updated_plan if plan.updated_plan else plan.original_plan
        base_dict = json.loads(base_json)
        updated_dict = update_workout_plan(base_dict, feedback)
        update_plan(db, plan_id=plan_id, updated_plan=json.dumps(updated_dict))
        if plan.user is not None:
            touch_user_activity(db, plan.user.id)
    except (RuntimeError, json.JSONDecodeError):
        raise HTTPException(status_code=502, detail="The plan could not be updated. Your current plan is unchanged.")

    u = plan.user
    progress_context = _build_progress_context(db, u)
    return templates.TemplateResponse(request, "result.html", {
        "request": request,
        "username": u.name if u else "",
        "age": u.age if u else "",
        "weight": u.weight if u else "",
        "goal": u.goal if u else "",
        "intensity": u.intensity if u else "",
        "experience_level": u.experience_level if u else "Beginner",
        "user_id": u.user_id if u else "",
        "user_pk_id": u.id if u else None,
        "workout_plan": updated_dict,
        "nutrition_tip": plan.nutrition_tip,
        "plan_id": plan_id,
        "is_updated": True,
        "used_fallback": False,
        "safety_disclaimer": SAFETY_DISCLAIMER,
        **progress_context,
    })


# ---------------------------------------------------------------------------
# POST /progress/{user_id}/{day_number}/complete
# ---------------------------------------------------------------------------
@router.post("/progress/{user_id}/{day_number}/complete")
async def complete_workout_day(
    user_id: int,
    day_number: int,
    db: Session = Depends(get_db),
):
    if not 1 <= day_number <= 7:
        raise HTTPException(status_code=400, detail="Day number must be between 1 and 7.")

    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    try:
        mark_workout_day_complete(db, user.id, day_number)
        touch_user_activity(db, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Progress could not be updated.")

    latest_plan = user.plans[-1] if user.plans else None
    if latest_plan is None:
        return RedirectResponse(url="/view-all-users", status_code=303)
    return RedirectResponse(url=f"/result/{latest_plan.id}", status_code=303)


# ---------------------------------------------------------------------------
# GET /progress/{user_id}
# ---------------------------------------------------------------------------
@router.get("/progress/{user_id}")
async def get_progress(user_id: int, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    summary = get_user_progress_summary_api(db, user.id)
    return {
        "completed_days": summary["completed_days"],
        "total_days": summary["total_days"],
        "progress_percentage": summary["progress_percentage"],
        "day_status": summary["day_status"],
    }


# ---------------------------------------------------------------------------
# POST /admin/users/{user_id}/delete
# ---------------------------------------------------------------------------
@router.post("/admin/users/{user_id}/delete")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    try:
        deleted = delete_user_with_associated_data(db, user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="User not found.")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="The user could not be deleted.")
    return RedirectResponse(url="/view-all-users", status_code=303)


# ---------------------------------------------------------------------------
# GET /view-all-users  –  Admin dashboard
# ---------------------------------------------------------------------------
@router.get("/view-all-users")
async def view_all_users(request: Request, db: Session = Depends(get_db)):
    orm_users = get_all_users(db)
    users = []
    for u in orm_users:
        latest = u.plans[-1] if u.plans else None
        progress = _build_progress_context(db, u)
        users.append({
            "id": u.id,
            "name": u.name,
            "age": u.age,
            "weight": u.weight,
            "goal": u.goal,
            "intensity": u.intensity,
            "experience_level": u.experience_level,
            "completed_days": progress["completed_days"],
            "progress_percentage": progress["progress_percentage"],
            "last_activity": u.last_activity.strftime("%Y-%m-%d %H:%M") if u.last_activity else 'Never',
            "user_id": u.user_id or "",
            "original_plan": latest.original_plan if latest else "",
            "updated_plan": latest.updated_plan if latest else "",
            "nutrition_tip": latest.nutrition_tip if latest else "",
            "plan_id": latest.id if latest else None,
        })

    return templates.TemplateResponse(request, "all_users.html", {
        "request": request,
        "users": users,
    })
