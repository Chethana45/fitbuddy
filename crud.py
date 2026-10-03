from sqlalchemy.orm import Session
import models, schemas

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_name(db: Session, name: str):
    return db.query(models.User).filter(models.User.name == name).first()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        name=user.name,
        age=user.age,
        gender=user.gender,
        weight=user.weight,
        goal=user.goal,
        intensity=user.intensity
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, db_user: models.User, user: schemas.UserCreate):
    db_user.age = user.age
    db_user.gender = user.gender
    db_user.weight = user.weight
    db_user.goal = user.goal
    db_user.intensity = user.intensity
    db.commit()
    db.refresh(db_user)
    return db_user

def create_workout_plan(db: Session, plan_content: str, user_id: int):
    db_plan = models.WorkoutPlan(plan_content=plan_content, user_id=user_id)
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

def get_workout_plan(db: Session, plan_id: int):
    return db.query(models.WorkoutPlan).filter(models.WorkoutPlan.id == plan_id).first()

def get_latest_workout_plan(db: Session, user_id: int):
    return db.query(models.WorkoutPlan).filter(models.WorkoutPlan.user_id == user_id).order_by(models.WorkoutPlan.id.desc()).first()

def create_feedback(db: Session, feedback: schemas.FeedbackCreate):
    db_feedback = models.Feedback(feedback_text=feedback.feedback_text, plan_id=feedback.plan_id)
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

def update_workout_plan(db: Session, db_plan: models.WorkoutPlan, new_content: str):
    db_plan.plan_content = new_content
    db.commit()
    db.refresh(db_plan)
    return db_plan
