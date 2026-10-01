from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Used to document / validate the HTML form inputs for /generate-workout
# ---------------------------------------------------------------------------
class UserInput(BaseModel):
    """Mirrors the index.html form fields captured via Form(...)."""
    username:         str = Field(..., min_length=1, max_length=100, description="Display name")
    user_id:          str = Field(..., min_length=1, max_length=50, description="Unique user identifier")
    age:              int = Field(..., ge=10, le=100)
    weight:           float = Field(..., ge=20.0, description="Weight in kg")
    goal:             str = Field(..., min_length=1)
    intensity:        str = Field(..., pattern="^(low|medium|high)$")
    experience_level: Literal["Beginner", "Intermediate", "Advanced"]


# ---------------------------------------------------------------------------
# Used to document / validate the feedback form inputs for /submit-feedback
# ---------------------------------------------------------------------------
class FeedbackRequest(BaseModel):
    """Mirrors the result.html feedback form fields captured via Form(...)."""
    plan_id:  int = Field(..., gt=0)
    feedback: str = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# Kept for backward-compatibility (internal use / API docs)
# ---------------------------------------------------------------------------
class UserCreate(BaseModel):
    name:             str = Field(..., min_length=1, max_length=100)
    age:              int = Field(..., ge=10, le=100)
    weight:           float = Field(..., ge=20.0)
    goal:             str = Field(..., min_length=1)
    intensity:        str = Field(..., pattern="^(low|medium|high)$")
    experience_level: Literal["Beginner", "Intermediate", "Advanced"]


class PlanResponse(BaseModel):
    plan_id:       int
    user_id:       int
    original_plan: str
    updated_plan:  Optional[str] = None
    nutrition_tip: Optional[str] = None

    class Config:
        from_attributes = True
