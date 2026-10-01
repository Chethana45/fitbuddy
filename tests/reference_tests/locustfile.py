"""Load test for FitBuddy (Phase 6). Start the app in demo mode first:

    DEMO_MODE=true uvicorn app.main:app --port 8000
    locust -f tests/locustfile.py --headless -u 50 -r 10 -t 60s \
        --host http://127.0.0.1:8000 --csv reports/perf --html reports/perf.html
"""
import random

from locust import HttpUser, between, task

GOALS = ["weight loss", "muscle gain", "general fitness", "flexibility", "endurance"]


class FitBuddyUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def home(self):
        self.client.get("/", name="GET /")

    @task(2)
    def health(self):
        self.client.get("/api/health", name="GET /api/health")

    @task(2)
    def nutrition_tip(self):
        self.client.get("/nutrition-tip", params={"goal": random.choice(GOALS)},
                        name="GET /nutrition-tip")

    @task(1)
    def generate_plan(self):
        payload = {
            "name": f"Load User {random.randint(1, 10_000)}",
            "age": random.randint(18, 70),
            "weight_kg": round(random.uniform(50, 110), 1),
            "goal": random.choice(GOALS),
            "intensity": random.choice(["low", "medium", "high"]),
            "experience": random.choice(["beginner", "intermediate", "advanced"]),
        }
        with self.client.post("/generate-plan", json=payload, name="POST /generate-plan",
                              catch_response=True) as resp:
            if resp.status_code != 200 or len(resp.json().get("workout_plan", {}).get("days", [])) != 7:
                resp.failure(f"bad response {resp.status_code}")
