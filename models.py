from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    gender = Column(String)
    weight = Column(Integer)
    goal = Column(String)
    intensity = Column(String)

    plans = relationship("WorkoutPlan", back_populates="user", cascade="all, delete-orphan")

class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="plans")
    feedbacks = relationship("Feedback", back_populates="plan", cascade="all, delete-orphan")

class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("workout_plans.id"))
    feedback_text = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    plan = relationship("WorkoutPlan", back_populates="feedbacks")
