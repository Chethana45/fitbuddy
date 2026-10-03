"""
gemini_generator.py
Generates a personalised 7-day workout plan using Gemini 1.5 Pro.
"""

import os
import json
import re
import time
import logging
from dotenv import load_dotenv
from google import genai

logger = logging.getLogger(__name__)
load_dotenv()

_PRO_MODEL = os.getenv("GEMINI_WORKOUT_MODEL", "gemini-3.5-flash-lite")

_RETRY_DELAYS = [5, 15, 30]  # seconds between retries on 429

# ---------------------------------------------------------------------------
# Static fallback plans — returned when the API quota is exhausted so the
# page still loads instead of returning a 502.
# ---------------------------------------------------------------------------
_FALLBACK_PLAN_BASE = {
    "Day 1": {
        "focus": "Full-Body Strength",
        "warmup": "5 min brisk walk + arm circles and leg swings",
        "exercises": [
            {"name": "Bodyweight Squats", "sets": 3, "reps": "15"},
            {"name": "Push-Ups", "sets": 3, "reps": "12"},
            {"name": "Dumbbell Rows", "sets": 3, "reps": "12 each side"},
            {"name": "Plank Hold", "sets": 3, "reps": "30 seconds"},
        ],
        "cooldown": "5 min full-body stretch focusing on quads, chest and shoulders",
    },
    "Day 2": {
        "focus": "Active Recovery & Mobility",
        "warmup": "5 min easy walk",
        "exercises": [
            {"name": "Cat-Cow Stretch", "sets": 2, "reps": "10"},
            {"name": "Hip Circle Rotations", "sets": 2, "reps": "10 each side"},
            {"name": "Child's Pose", "sets": 3, "reps": "30 seconds"},
            {"name": "Seated Hamstring Stretch", "sets": 2, "reps": "30 seconds each"},
        ],
        "cooldown": "Deep breathing and foam rolling if available",
    },
    "Day 3": {
        "focus": "Lower Body",
        "warmup": "5 min jumping jacks + hip flexor stretch",
        "exercises": [
            {"name": "Lunges", "sets": 3, "reps": "12 each leg"},
            {"name": "Glute Bridges", "sets": 3, "reps": "15"},
            {"name": "Wall Sit", "sets": 3, "reps": "45 seconds"},
            {"name": "Calf Raises", "sets": 3, "reps": "20"},
        ],
        "cooldown": "5 min standing and seated leg stretches",
    },
    "Day 4": {
        "focus": "Upper Body Push",
        "warmup": "5 min shoulder rolls + light band pull-aparts",
        "exercises": [
            {"name": "Incline Push-Ups", "sets": 3, "reps": "15"},
            {"name": "Dumbbell Shoulder Press", "sets": 3, "reps": "12"},
            {"name": "Tricep Dips", "sets": 3, "reps": "12"},
            {"name": "Lateral Raises", "sets": 3, "reps": "15"},
        ],
        "cooldown": "Chest opener stretch — clasp hands behind back and lift arms",
    },
    "Day 5": {
        "focus": "Cardio & Core",
        "warmup": "3 min march in place + dynamic stretches",
        "exercises": [
            {"name": "High Knees", "sets": 3, "reps": "30 seconds"},
            {"name": "Mountain Climbers", "sets": 3, "reps": "30 seconds"},
            {"name": "Bicycle Crunches", "sets": 3, "reps": "20"},
            {"name": "Burpees", "sets": 3, "reps": "10"},
        ],
        "cooldown": "5 min walking cool-down + deep abdominal breathing",
    },
    "Day 6": {
        "focus": "Upper Body Pull",
        "warmup": "5 min arm swings + scapular squeezes",
        "exercises": [
            {"name": "Dumbbell Bicep Curls", "sets": 3, "reps": "12"},
            {"name": "Bent-Over Rows", "sets": 3, "reps": "12"},
            {"name": "Resistance Band Pull-Aparts", "sets": 3, "reps": "15"},
            {"name": "Superman Hold", "sets": 3, "reps": "30 seconds"},
        ],
        "cooldown": "Doorway chest stretch and lat side stretch",
    },
    "Day 7": {
        "focus": "Rest & Light Activity",
        "warmup": "Gentle 10 min walk outdoors",
        "exercises": [
            {"name": "Yoga Sun Salutation", "sets": 2, "reps": "5 flows"},
            {"name": "Standing Hip Flexor Stretch", "sets": 2, "reps": "30 seconds each"},
            {"name": "Thoracic Spine Rotation", "sets": 2, "reps": "10 each side"},
        ],
        "cooldown": "10 min guided meditation or relaxed breathing",
    },
}


def _get_fallback_plan(name: str, goal: str, intensity: str) -> dict:
    """Return a copy of the static fallback plan (quota-safe)."""
    import copy
    return copy.deepcopy(_FALLBACK_PLAN_BASE)


def _extract_json(text: str) -> dict:
    """Strip markdown fences and parse the first JSON object in the response."""
    clean = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", clean, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"Could not parse JSON from Gemini Pro response:\n{text}")


def _generate_workout(name: str, age: int, weight: float, goal: str,
                      intensity: str, experience_level: str = "Beginner") -> tuple[dict, bool]:
    """
    Call Gemini to generate a structured 7-day workout plan.

    Returns a dict with keys 'Day 1' … 'Day 7'. Each day contains:
      - focus     : muscle group / theme
      - warmup    : 5-10 min warm-up description
      - exercises : list of {name, sets, reps}
      - cooldown  : cooldown / recovery tip
    """
    prompt = f"""
You are FitBuddy, a professional personal trainer.
Create a detailed, personalised 7-day workout plan for this user:

- Name            : {name}
- Age             : {age} years
- Weight          : {weight} kg
- Goal            : {goal}
- Intensity       : {intensity}
- Experience Level: {experience_level}

Return ONLY valid JSON — no extra text, no markdown — using exactly this structure:

{{
  "Day 1": {{
    "focus": "<muscle group or theme>",
    "warmup": "<5–10 min warm-up description>",
    "exercises": [
      {{"name": "<exercise name>", "sets": <integer>, "reps": "<reps or duration>"}},
      ...
    ],
    "cooldown": "<cooldown or recovery tip>"
  }},
  "Day 2": {{ ... }},
  ...
  "Day 7": {{ ... }}
}}

Tailor the plan to the experience level:
- Beginner: simpler exercises, conservative volume, and clear technique cues.
- Intermediate: moderate complexity and balanced progression.
- Advanced: more challenging exercise selection and higher training volume.

Ensure the plan is realistic, progressive, and appropriate for the given intensity.
Rest days should still include light activity or stretching.
"""
    for delay in (*_RETRY_DELAYS, None):
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("Gemini workout request skipped: GEMINI_API_KEY is missing.")
                return _get_fallback_plan(name, goal, intensity), True
            logger.info("Gemini workout request started (model=%s).", _PRO_MODEL)
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=_PRO_MODEL, contents=prompt
            )
            plan = _extract_json(response.text)
            if set(plan) != {f"Day {day}" for day in range(1, 8)}:
                raise ValueError("Gemini response must contain exactly Day 1 through Day 7.")
            logger.info("Gemini workout request succeeded (model=%s).", _PRO_MODEL)
            return plan, False
        except ValueError as exc:
            raise RuntimeError(f"Failed to parse workout plan JSON: {exc}") from exc
        except Exception as exc:
            logger.error(
                "Gemini workout request failed (model=%s, error=%s).",
                _PRO_MODEL,
                str(exc).replace(api_key, "<redacted>")[:500],
            )
            if "429" in str(exc) and delay is not None:
                time.sleep(delay)
                continue
            break
    logger.warning("Using safe fallback workout plan after Gemini request failure.")
    return _get_fallback_plan(name, goal, intensity), True


def generate_workout_gemini(name: str, age: int, weight: float, goal: str,
                            intensity: str, experience_level: str = "Beginner") -> dict:
    """Generate a plan, falling back safely when Gemini is unavailable."""
    return _generate_workout(name, age, weight, goal, intensity, experience_level)[0]


def generate_workout_with_status(name: str, age: int, weight: float, goal: str,
                                 intensity: str, experience_level: str = "Beginner") -> tuple[dict, bool]:
    """Return the plan and whether a safe local fallback was used."""
    return _generate_workout(name, age, weight, goal, intensity, experience_level)
