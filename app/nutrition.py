"""
nutrition.py
Optional helpers for nutrition-specific logic.
Provides goal-to-focus mappings and macro guidelines to enrich prompts or UI.
"""

# Suggested macronutrient split per goal (protein / carbs / fat — % of calories)
GOAL_MACROS: dict[str, dict] = {
    "Weight Loss": {
        "protein": 35,
        "carbs": 35,
        "fat": 30,
        "note": "Caloric deficit of ~300–500 kcal/day recommended.",
    },
    "Muscle Gain": {
        "protein": 30,
        "carbs": 50,
        "fat": 20,
        "note": "Caloric surplus of ~200–400 kcal/day recommended.",
    },
    "Improve Endurance": {
        "protein": 20,
        "carbs": 60,
        "fat": 20,
        "note": "Prioritise complex carbs for sustained energy.",
    },
    "General Fitness": {
        "protein": 25,
        "carbs": 50,
        "fat": 25,
        "note": "Balanced diet with whole foods and adequate hydration.",
    },
    "Flexibility & Mobility": {
        "protein": 25,
        "carbs": 45,
        "fat": 30,
        "note": "Anti-inflammatory foods (omega-3s, leafy greens) support recovery.",
    },
}

# Key micronutrients / foods for each goal
GOAL_FOCUS_FOODS: dict[str, list[str]] = {
    "Weight Loss":           ["leafy greens", "lean chicken", "Greek yoghurt", "oats", "berries"],
    "Muscle Gain":           ["eggs", "salmon", "quinoa", "cottage cheese", "sweet potato"],
    "Improve Endurance":     ["bananas", "brown rice", "beetroot", "whole-grain pasta", "dates"],
    "General Fitness":       ["avocado", "mixed nuts", "legumes", "broccoli", "whole-grain bread"],
    "Flexibility & Mobility":["walnuts", "turmeric", "spinach", "blueberries", "olive oil"],
}


def get_nutrition_context(goal: str) -> dict:
    """
    Return macro split and key focus foods for a given fitness goal.
    Used to enrich UI tooltips or supplement Gemini prompts.
    """
    macros = GOAL_MACROS.get(goal, GOAL_MACROS["General Fitness"])
    foods  = GOAL_FOCUS_FOODS.get(goal, GOAL_FOCUS_FOODS["General Fitness"])
    return {"goal": goal, "macros": macros, "focus_foods": foods}


def build_nutrition_prompt_context(goal: str) -> str:
    """
    Build a concise string that can be appended to Gemini prompts to
    provide nutrition context for richer, goal-specific responses.
    """
    ctx = get_nutrition_context(goal)
    macros = ctx["macros"]
    foods  = ", ".join(ctx["focus_foods"])
    return (
        f"Nutrition context for {goal}: "
        f"Protein {macros['protein']}% | Carbs {macros['carbs']}% | Fat {macros['fat']}%. "
        f"Key foods: {foods}. {macros['note']}"
    )
