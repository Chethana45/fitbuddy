from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class FeedbackBase(BaseModel):
    feedback_text: str

class FeedbackCreate(FeedbackBase):
    plan_id: int

class Feedback(FeedbackBase):
    id: int
    plan_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class WorkoutPlanBase(BaseModel):
    plan_content: str

class WorkoutPlanCreate(WorkoutPlanBase):
    pass

class WorkoutPlan(WorkoutPlanBase):
    id: int
    user_id: int
    created_at: datetime
    feedbacks: List[Feedback] = []

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    name: str
    age: int
    gender: str
    weight: int
    goal: str
    intensity: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    plans: List[WorkoutPlan] = []

    class Config:
        from_attributes = True
