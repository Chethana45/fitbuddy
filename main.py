from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import database, models, schemas, crud
from services import ai_service
import os

# Create DB tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="FitBuddy API")

# Setup templates and static files
os.makedirs("templates", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    # Simple UI
    return templates.TemplateResponse("index.html", {"request": request, "users": users})

# --- API Endpoints --- #

@app.post("/users", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_name(db, name=user.name)
    if db_user:
        db_user = crud.update_user(db, db_user, user)
    else:
        db_user = crud.create_user(db=db, user=user)
    return db_user

@app.post("/generate_plan")
def generate_workout_plan(
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    weight: int = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    db: Session = Depends(get_db)
):
    # 1. Ensure User exists
    user_data = schemas.UserCreate(name=name, age=age, gender=gender, weight=weight, goal=goal, intensity=intensity)
    db_user = crud.get_user_by_name(db, name=name)
    if not db_user:
        db_user = crud.create_user(db, user_data)
    else:
        db_user = crud.update_user(db, db_user, user_data)
        
    # 2. Call AI Service
    plan_text = ai_service.generate_workout_plan(
        name=db_user.name,
        age=db_user.age,
        gender=db_user.gender,
        weight=db_user.weight,
        goal=db_user.goal,
        intensity=db_user.intensity
    )
    
    # 3. Store Plan
    crud.create_workout_plan(db, plan_content=plan_text, user_id=db_user.id)
    
    # 4. Redirect to view plan UI logic. A modern SPA would use JSON, but since we are doing some SSR + Vanilla JS, let's return JSON for frontend JS to handle
    return {"status": "success", "user_id": db_user.id, "plan": plan_text}

@app.get("/users/{user_id}/latest_plan")
def get_latest_plan(user_id: int, db: Session = Depends(get_db)):
    db_plan = crud.get_latest_workout_plan(db, user_id=user_id)
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"plan_id": db_plan.id, "plan_content": db_plan.plan_content}

@app.post("/update_plan")
def update_workout_plan(
    plan_id: int = Form(...),
    feedback_text: str = Form(...),
    db: Session = Depends(get_db)
):
    # 1. Fetch Plan
    db_plan = crud.get_workout_plan(db, plan_id=plan_id)
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # 2. Save Feedback
    feedback_data = schemas.FeedbackCreate(plan_id=plan_id, feedback_text=feedback_text)
    crud.create_feedback(db, feedback=feedback_data)
    
    # 3. Regenerate Plan
    new_plan_text = ai_service.revise_workout_plan(
        current_plan=db_plan.plan_content,
        feedback=feedback_text
    )
    
    # 4. Update the DB plan content with new plan text
    db_plan = crud.update_workout_plan(db, db_plan, new_plan_text)
    
    return {"status": "success", "plan_id": db_plan.id, "plan": db_plan.plan_content}

@app.get("/nutrition_tip")
def get_nutrition_tip(goal: str):
    tip = ai_service.generate_nutrition_tip(goal)
    return {"tip": tip}
