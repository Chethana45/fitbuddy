"""
updated_plan.py
Refines an existing workout plan based on user feedback using Gemini 1.5 Pro.
"""

import json
import os
import re
import time
import logging
from dotenv import load_dotenv
from google import genai

logger = logging.getLogger(__name__)
load_dotenv()
_PRO_MODEL = os.getenv("GEMINI_WORKOUT_MODEL", "gemini-3.5-flash-lite")
_RETRY_DELAYS = [5, 15, 30]


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
    raise ValueError(f"Could not parse JSON from Gemini response:\n{text}")


def update_workout_plan(original_plan: dict, feedback: str) -> dict:
    """
    Send the existing 7-day plan and the user's feedback to Gemini 1.5 Pro.
    Returns a modified plan dict that incorporates the requested changes.

    Args:
        original_plan: dict – the parsed JSON of the current plan.
        feedback: str  – free-text user feedback (e.g. "Add yoga", "More cardio").

    Returns:
        Updated plan dict with the same Day 1 – Day 7 structure.
    """
    prompt = f"""
You are FitBuddy, a professional personal trainer.
A user has the following 7-day workout plan:

{json.dumps(original_plan, indent=2)}

The user's feedback is: "{feedback}"

Update the plan to incorporate the feedback. Return ONLY valid JSON with the
same structure (Day 1 … Day 7, each with focus, warmup, exercises, cooldown).
No extra commentary, no markdown, just the JSON object.
"""
    for delay in (*_RETRY_DELAYS, None):
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("Gemini refinement request skipped: GEMINI_API_KEY is missing.")
                return original_plan
            logger.info("Gemini refinement request started (model=%s).", _PRO_MODEL)
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=_PRO_MODEL, contents=prompt
            )
            updated_plan = _extract_json(response.text)
            logger.info("Gemini refinement request succeeded (model=%s).", _PRO_MODEL)
            return updated_plan
        except ValueError as exc:
            raise RuntimeError(f"Failed to parse updated plan JSON: {exc}") from exc
        except Exception as exc:
            logger.error(
                "Gemini refinement request failed (model=%s, error=%s).",
                _PRO_MODEL,
                str(exc).replace(api_key, "<redacted>")[:500],
            )
            if "429" in str(exc) and delay is not None:
                time.sleep(delay)
                continue
            break  # Non-429 — fall through to fallback
    # Quota exhausted — return the original plan unchanged rather than a 502
    logger.warning("Keeping current plan after Gemini refinement failure.")
    return original_plan
