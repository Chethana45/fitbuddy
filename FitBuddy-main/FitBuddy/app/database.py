import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# ---------------------------------------------------------------------------
# Engine & session
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'fitbuddy.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
Base = declarative_base()


# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id                 = Column(Integer, primary_key=True, index=True)
    user_id            = Column(String(50), nullable=True, index=True)
    name               = Column(String(100), nullable=False)
    age                = Column(Integer, nullable=False)
    weight             = Column(Float, nullable=False)
    goal               = Column(String(100), nullable=False)
    intensity          = Column(String(50), nullable=False)
    experience_level   = Column(String(50), nullable=False, default="Beginner")
    last_activity      = Column(DateTime, nullable=True)
    created_at         = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    plans = relationship("Plan", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("WorkoutProgress", back_populates="user", cascade="all, delete-orphan")


class Plan(Base):
    __tablename__ = "plans"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_plan = Column(Text, nullable=False)
    updated_plan  = Column(Text, nullable=True)
    nutrition_tip = Column(Text, nullable=True)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                            onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="plans")


class WorkoutProgress(Base):
    __tablename__ = "workout_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "day_number", name="uq_workout_progress_user_day"),
    )

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    day_number   = Column(Integer, nullable=False)
    day_name     = Column(String(50), nullable=False)
    completed    = Column(Boolean, nullable=False, default=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="progress")


# ---------------------------------------------------------------------------
# DB dependency (for FastAPI)
# ---------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_user_columns(db):
    inspector = db.execute(text("PRAGMA table_info(users)"))
    columns = {row[1] for row in inspector.fetchall()}

    if "experience_level" not in columns:
        db.execute(text("ALTER TABLE users ADD COLUMN experience_level VARCHAR(50) DEFAULT 'Beginner'"))
    if "last_activity" not in columns:
        db.execute(text("ALTER TABLE users ADD COLUMN last_activity DATETIME"))

    db.execute(text("UPDATE users SET experience_level = 'Beginner' WHERE experience_level IS NULL"))


def _ensure_workout_progress_columns(db):
    inspector = db.execute(text("PRAGMA table_info(workout_progress)"))
    columns = {row[1] for row in inspector.fetchall()}

    if "day_number" not in columns:
        db.execute(text("ALTER TABLE workout_progress ADD COLUMN day_number INTEGER"))
    if "day_name" not in columns:
        db.execute(text("ALTER TABLE workout_progress ADD COLUMN day_name VARCHAR(50)"))
    if "completed" not in columns:
        db.execute(text("ALTER TABLE workout_progress ADD COLUMN completed BOOLEAN DEFAULT 0"))
    if "completed_at" not in columns:
        db.execute(text("ALTER TABLE workout_progress ADD COLUMN completed_at DATETIME"))


def init_db():
    with engine.begin() as conn:
        Base.metadata.create_all(bind=conn)

        user_table = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        ).fetchone()
        if user_table:
            _ensure_user_columns(conn)

        progress_table = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='workout_progress'")
        ).fetchone()
        if progress_table:
            _ensure_workout_progress_columns(conn)

        index_name = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='index' AND name='uq_workout_progress_user_day'")
        ).fetchone()
        if index_name is None:
            conn.execute(
                text("CREATE UNIQUE INDEX IF NOT EXISTS uq_workout_progress_user_day ON workout_progress (user_id, day_number)")
            )


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------
def save_user(db, name: str, age: int, weight: float, goal: str,
              intensity: str, user_id: str, experience_level: str = "Beginner",
              last_activity: Optional[datetime] = None) -> User:
    user = User(
        name=name,
        age=age,
        weight=weight,
        goal=goal,
        intensity=intensity,
        user_id=user_id,
        experience_level=experience_level or "Beginner",
        last_activity=last_activity or datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def save_plan(db, user_id: int, original_plan: str, nutrition_tip: str) -> Plan:
    plan = Plan(user_id=user_id, original_plan=original_plan, nutrition_tip=nutrition_tip)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def update_plan(db, plan_id: int, updated_plan: str) -> Plan:
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        return None
    plan.updated_plan = updated_plan
    plan.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(plan)
    return plan


def touch_user_activity(db, user_id: int) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    user.last_activity = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user


def get_original_plan(db, plan_id: int) -> Plan:
    return db.query(Plan).filter(Plan.id == plan_id).first()


def get_user(db, user_id: int) -> User:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_user_id(db, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.user_id == user_id).first()


def get_plan(db, plan_id: int) -> Optional[Plan]:
    return db.query(Plan).filter(Plan.id == plan_id).first()


def get_all_users(db):
    return db.query(User).order_by(User.created_at.desc()).all()


def get_all_plans(db):
    """Return every plan ordered newest-first, with user eagerly loaded."""
    return db.query(Plan).order_by(Plan.created_at.desc()).all()


def get_workout_progress(db, user_id: int, day_number: int) -> Optional[WorkoutProgress]:
    return (
        db.query(WorkoutProgress)
        .filter(WorkoutProgress.user_id == user_id, WorkoutProgress.day_number == day_number)
        .first()
    )


def get_user_progress_summary(db, user_id: int) -> dict:
    rows = (
        db.query(WorkoutProgress)
        .filter(WorkoutProgress.user_id == user_id, WorkoutProgress.completed.is_(True))
        .all()
    )
    completed_days = len(rows)
    total_days = 7
    percentage = round((completed_days / total_days) * 100) if total_days else 0
    day_status = {day: False for day in range(1, total_days + 1)}
    for row in rows:
        if 1 <= row.day_number <= total_days:
            day_status[row.day_number] = True
    return {
        "completed_days": completed_days,
        "total_days": total_days,
        "progress_percentage": percentage,
        "day_status": day_status,
    }


def get_user_progress_summary_api(db, user_id: int) -> dict:
    summary = get_user_progress_summary(db, user_id)
    ordered_status = [False] + [summary["day_status"].get(day, False) for day in range(1, summary["total_days"] + 1)]
    return {
        "completed_days": summary["completed_days"],
        "total_days": summary["total_days"],
        "progress_percentage": summary["progress_percentage"],
        "day_status": ordered_status,
    }


def mark_workout_day_complete(db, user_id: int, day_number: int) -> WorkoutProgress:
    if not 1 <= day_number <= 7:
        raise ValueError("Day number must be between 1 and 7.")

    progress = get_workout_progress(db, user_id, day_number)
    if progress is not None:
        if progress.completed is False:
            progress.completed = True
            progress.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(progress)
        return progress

    progress = WorkoutProgress(
        user_id=user_id,
        day_number=day_number,
        day_name=f"Day {day_number}",
        completed=True,
        completed_at=datetime.now(timezone.utc),
    )
    db.add(progress)
    db.commit()
    db.refresh(progress)
    return progress


def delete_user_with_associated_data(db, user_id: int) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    for progress in list(user.progress):
        db.delete(progress)
    for plan in list(user.plans):
        db.delete(plan)
    db.delete(user)
    db.commit()
    return True
