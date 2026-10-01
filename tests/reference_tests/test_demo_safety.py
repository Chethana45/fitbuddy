"""Pure-function tests: demo-mode plans and revisions follow the safety and feedback rules."""
import re

import pytest

from app.demo_data import (EQUIPMENT, INJURY_NOTE, LIBRARY, LOW_IMPACT_NOTE, SENIOR_NOTE,
                           TEEN_LEVEL_NOTE, TEEN_NOTE, UNCHANGED, _goal_key, _kind_of,
                           demo_revise_plan, demo_workout_plan)
from app.schemas import WorkoutPlan

HIGH_IMPACT = re.compile(r"Jump|Box|Sprint|Burpees|Tempo Run|Jogging")
BALANCE = {"Single-Leg Stand", "Heel-to-Toe Walk", "Step-Ups to a Low Step"}

# (goal, intensity, experience, age, weight)
PROFILES = {
    "teen beginner": ("muscle gain", "high", "beginner", 15, 55),
    "adult intermediate": ("general fitness", "medium", "intermediate", 30, 75),
    "senior": ("weight loss", "high", "advanced", 65, 80),
    "heavy advanced": ("weight loss", "high", "advanced", 35, 120),
    "free-text goal": ("run a 10k", "medium", "beginner", 28, 68),
}
FEEDBACKS = ["More cardio", "Add a rest day", "Shorter workouts", "No equipment",
             "more yoga", "no jumping please", "my knee hurts", "I'm not tired, want more workouts",
             "make it purple"]


def make(name: str) -> tuple[dict, dict]:
    goal, intensity, experience, age, weight = PROFILES[name]
    profile = {"experience": experience, "age": age, "intensity": intensity, "weight": weight}
    return demo_workout_plan(goal, intensity, experience, age=age, weight=weight), profile


def names(plan: dict) -> list[str]:
    return [ex["name"] for d in plan["days"] for ex in d["exercises"]]


def training_days(plan: dict) -> list[dict]:
    return [d for d in plan["days"] if not d["is_rest_day"]]


def strength_days(plan: dict) -> int:
    return sum(_kind_of(d) in ("upper", "lower", "full") for d in training_days(plan))


def low_rep(reps: str) -> int:
    return int(re.match(r"\d+", reps).group())


def assert_valid(plan: dict) -> None:
    WorkoutPlan.model_validate(plan)
    assert [d["day"] for d in plan["days"]] == list(range(1, 8))
    assert any(d["is_rest_day"] for d in plan["days"])


@pytest.mark.parametrize("profile_name", PROFILES)
def test_every_profile_and_feedback_validates(profile_name):
    plan, profile = make(profile_name)
    assert_valid(plan)
    for fb in FEEDBACKS:
        new = demo_revise_plan(plan, fb, **profile)
        assert_valid(new)
        if profile["age"] < 18:
            assert all(ex["sets"] <= 3 for d in new["days"] for ex in d["exercises"]
                       if ex["sets"])


def test_more_cardio_turns_a_strength_day_into_cardio():
    plan = demo_workout_plan("muscle gain", "medium", "intermediate", age=30, weight=70)
    new = demo_revise_plan(plan, "More cardio", experience="intermediate", age=30,
                           intensity="medium", weight=70)
    before = sum("Cardio" in d["focus"] for d in plan["days"])
    assert sum("Cardio" in d["focus"] for d in new["days"]) == before + 1
    assert "Revised: turned day" in new["summary"]


def test_negated_feedback_does_not_reduce_training():
    plan, profile = make("adult intermediate")
    new = demo_revise_plan(plan, "I'm not tired, want more workouts", **profile)
    assert len(training_days(new)) >= len(training_days(plan))
    no_cardio = demo_revise_plan(plan, "no cardio please", **profile)
    assert no_cardio["days"] == plan["days"]
    assert UNCHANGED in no_cardio["summary"]


@pytest.mark.parametrize("feedback", ["knee injury", "my back hurts", "sore shoulder"])
def test_injury_adds_note_and_removes_high_impact(feedback):
    plan = demo_workout_plan("weight loss", "high", "advanced", age=30)
    assert [n for n in names(plan) if HIGH_IMPACT.search(n)]
    new = demo_revise_plan(plan, feedback, experience="advanced", age=30, intensity="high")
    assert INJURY_NOTE in new["safety_notes"]
    assert not [n for n in names(new) if HIGH_IMPACT.search(n)]
    assert not [n for n in names(new) if re.search(r"Barbell|Deadlift|Weighted", n)]
    # the injury keeps applying to later revisions
    later = demo_revise_plan(new, "more cardio", experience="advanced", age=30, intensity="high")
    assert not [n for n in names(later) if HIGH_IMPACT.search(n)]


def test_no_pain_is_not_an_injury():
    plan, profile = make("adult intermediate")
    new = demo_revise_plan(plan, "no pain at all, all good", **profile)
    assert INJURY_NOTE not in new["safety_notes"]


def test_more_yoga_adds_a_mobility_session():
    plan, profile = make("adult intermediate")
    new = demo_revise_plan(plan, "more yoga", **profile)
    assert any(_kind_of(d) == "mobility" for d in training_days(new))
    assert "mobility and yoga" in new["summary"]


def test_no_jumping_replaces_jump_moves():
    plan = demo_workout_plan("endurance", "medium", "intermediate", age=30)
    assert {"Jump Squats", "Burpees"} <= set(names(plan))
    new = demo_revise_plan(plan, "less jumping", experience="intermediate", age=30,
                           intensity="medium")
    assert not [n for n in names(new) if HIGH_IMPACT.search(n)]
    assert "jumping" in new["summary"]


def test_unmatched_feedback_says_plan_is_unchanged():
    plan, profile = make("adult intermediate")
    new = demo_revise_plan(plan, "make it purple", **profile)
    assert new["days"] == plan["days"]
    assert new["summary"].endswith(UNCHANGED)
    assert "added a note" not in new["summary"]


def test_heavy_user_gets_low_impact_plan_and_revisions():
    plan, profile = make("heavy advanced")
    assert not [n for n in names(plan) if HIGH_IMPACT.search(n)]
    assert LOW_IMPACT_NOTE in plan["safety_notes"]
    for fb in ["More cardio", "Shorter workouts", "I'm not tired, want more workouts"]:
        new = demo_revise_plan(plan, fb, **profile)
        assert not [n for n in names(new) if HIGH_IMPACT.search(n)]


def test_senior_gets_balance_work_and_beginner_strength():
    plan, profile = make("senior")
    advanced = {n for kind in LIBRARY.values() for n, _ in kind["advanced"]}
    assert not advanced & set(names(plan))
    assert sum(any(ex["name"] in BALANCE for ex in d["exercises"]) for d in plan["days"]) >= 2
    assert SENIOR_NOTE in plan["safety_notes"]
    assert not [n for n in names(plan) if HIGH_IMPACT.search(n)]
    for fb in ["More cardio", "Shorter workouts", "No equipment"]:
        new = demo_revise_plan(plan, fb, **profile)
        assert BALANCE & set(names(new))
        assert not advanced & set(names(new))
        assert new["safety_notes"].count(SENIOR_NOTE) == 1


def test_weight_changes_the_plan():
    light = demo_workout_plan("weight loss", "medium", "beginner", age=30, weight=70)
    heavy = demo_workout_plan("weight loss", "medium", "beginner", age=30, weight=120)
    assert names(light) != names(heavy)
    teen = demo_workout_plan("weight loss", "medium", "beginner", age=15, weight=55)
    heavy_adult = demo_workout_plan("weight loss", "medium", "beginner", age=40, weight=120)
    assert teen["days"] != heavy_adult["days"]


def test_warmups_vary_and_repeated_sessions_are_labelled():
    plan = demo_workout_plan("muscle gain", "medium", "intermediate", age=30)
    warmups = {d["warmup"] for d in training_days(plan)}
    assert len(warmups) >= 3
    focuses = [d["focus"] for d in training_days(plan)]
    assert len(set(focuses)) == len(focuses)
    upper = [d for d in plan["days"] if _kind_of(d) == "upper"]
    assert upper[0]["exercises"] != upper[1]["exercises"]


@pytest.mark.parametrize("goal", ["muscle gain", "endurance"])
def test_repeated_session_types_differ(goal):
    plan = demo_workout_plan(goal, "medium", "intermediate", age=30)
    days = training_days(plan)
    assert len({d["warmup"] for d in days}) == len(days)
    content = [[(ex["name"], ex["reps"]) for ex in d["exercises"]] for d in days]
    assert all(content.count(c) == 1 for c in content)
    revised = demo_revise_plan(plan, "More cardio", experience="intermediate", age=30,
                               intensity="medium", weight=70)
    cardio = [d for d in revised["days"] if _kind_of(d) == "cardio"]
    assert len({str(d["exercises"]) for d in cardio}) == len(cardio)


def test_units_are_sensible():
    advanced = demo_workout_plan("general fitness", "high", "advanced", age=30)
    knee_raises = [ex for d in advanced["days"] for ex in d["exercises"]
                   if ex["name"] == "Hanging Knee Raises"]
    assert knee_raises and all("sec" not in ex["reps"] for ex in knee_raises)
    for d in demo_workout_plan("endurance", "high", "intermediate", age=30)["days"]:
        timed = [ex for ex in d["exercises"] if re.fullmatch(r"\d+ min", ex["reps"])]
        assert len(timed) <= 1
    low = demo_workout_plan("muscle gain", "low", "beginner", age=30)
    high = demo_workout_plan("muscle gain", "high", "beginner", age=30)
    low_reps = {ex["name"]: ex["reps"] for d in low["days"] for ex in d["exercises"]}
    for d in high["days"]:
        for ex in d["exercises"]:
            if ex["name"] in ("Bodyweight Squats", "Incline Push-Ups", "Glute Bridges"):
                assert low_rep(ex["reps"]) >= low_rep(low_reps[ex["name"]])


@pytest.mark.parametrize("profile_name", ["teen beginner", "adult intermediate", "heavy advanced"])
def test_no_equipment_keeps_focus_and_removes_gear(profile_name):
    plan, profile = make(profile_name)
    new = demo_revise_plan(plan, "No equipment", **profile)
    assert [_kind_of(d) for d in new["days"]] == [_kind_of(d) for d in plan["days"]]
    assert not [n for n in names(new) if EQUIPMENT.search(n)]
    for d in new["days"]:
        if _kind_of(d) == "upper":
            assert {ex["name"] for ex in d["exercises"]} & {
                "Push-Ups (knees down if needed)", "Pike Push-Ups", "Chair Dips", "Incline Push-Ups"}


def test_revised_note_does_not_pile_up():
    plan, profile = make("adult intermediate")
    for fb in ["More cardio", "Add a rest day", "Shorter workouts"]:
        plan = demo_revise_plan(plan, fb, **profile)
    assert plan["summary"].count("Revised:") == 1
    assert "shortened" in plan["summary"] and "cardio" not in plan["summary"].split("Revised:")[1]


def test_repeated_revisions_keep_strength_days():
    plan = demo_workout_plan("muscle gain", "high", "intermediate", age=30)
    for fb in ["More cardio", "Add a rest day"] * 4:
        plan = demo_revise_plan(plan, fb, experience="intermediate", age=30, intensity="high")
        assert_valid(plan)
        assert strength_days(plan) >= 2


def test_shorter_workouts_shorten_cardio():
    plan = demo_workout_plan("endurance", "high", "intermediate", age=30)
    new = demo_revise_plan(plan, "Shorter workouts", experience="intermediate", age=30,
                           intensity="high")
    assert "40 min" in [ex["reps"] for d in plan["days"] for ex in d["exercises"]]
    reps = [ex["reps"] for d in training_days(new) for ex in d["exercises"]]
    assert "40 min" not in reps and "25 min" in reps


def test_free_text_goal_reads_grammatically():
    plan, _ = make("free-text goal")
    assert "endurance week" in plan["summary"]
    assert "your goal: run a 10k" in plan["summary"]
    assert "built for run" not in plan["summary"]


def test_teen_level_downgrade_is_explained():
    plan = demo_workout_plan("muscle gain", "high", "advanced", age=16)
    assert TEEN_LEVEL_NOTE in plan["safety_notes"] and TEEN_NOTE in plan["safety_notes"]
    assert "intermediate for under-18s" in plan["summary"]
    advanced = {n for kind in LIBRARY.values() for n, _ in kind["advanced"]}
    new = demo_revise_plan(plan, "more cardio", experience="advanced", age=16, intensity="high")
    assert not advanced & set(names(new))
    assert all(ex["sets"] <= 3 for d in new["days"] for ex in d["exercises"] if ex["sets"])


def test_revision_restores_rest_day_if_missing():
    plan = demo_workout_plan("general fitness", "medium")
    for d in plan["days"]:
        d["is_rest_day"] = False
    assert_valid(demo_revise_plan(plan, "shorter workouts"))


@pytest.mark.parametrize("goal,expected", [
    ("lean muscle", "muscle gain"),
    ("reduce fatigue", "general fitness"),
    ("lose fat", "weight loss"),
    ("run a 10k", "endurance"),
    ("more yoga", "flexibility"),
    ("Endurance", "endurance"),
])
def test_goal_key(goal, expected):
    assert _goal_key(goal) == expected


def test_update_plan_route_passes_user_profile(client):
    r = client.post("/generate-plan", json={"name": "Teen", "age": 15, "weight_kg": 55,
                                            "goal": "muscle gain", "intensity": "high",
                                            "experience": "beginner"})
    uid = r.json()["user_id"]
    r = client.post(f"/update-plan/{uid}", json={"feedback": "More cardio"})
    assert r.status_code == 200
    plan = r.json()["updated_plan"]
    plan_names = [e["name"] for d in plan["days"] for e in d["exercises"]]
    assert not [n for n in plan_names if HIGH_IMPACT.search(n)]
    assert all((e["sets"] or 0) <= 3 for d in plan["days"] for e in d["exercises"])
    assert TEEN_NOTE in plan["safety_notes"]
