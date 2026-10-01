from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app import database
from app.main import app

client = TestClient(app)


def _reset_db():
    with database.SessionLocal() as db:
        db.execute(database.WorkoutProgress.__table__.delete())
        db.execute(database.Plan.__table__.delete())
        db.execute(database.User.__table__.delete())
        db.commit()


def test_homepage_loads():
    _reset_db()
    response = client.get('/')
    assert response.status_code == 200
    assert 'Experience Level' in response.text


def test_experience_level_validation():
    response = client.post(
        '/generate-workout',
        data={
            'username': 'Alice',
            'user_id': 'u-invalid-exp',
            'age': 28,
            'weight': 71,
            'goal': 'Weight Loss',
            'intensity': 'medium',
            'experience_level': 'Invalid',
        },
    )
    assert response.status_code == 422


def test_workout_generation_persists_user_and_plan():
    _reset_db()
    payload = {
        'username': 'Alice Test',
        'user_id': 'user-001',
        'age': 30,
        'weight': 68,
        'goal': 'Weight Loss',
        'intensity': 'medium',
        'experience_level': 'Beginner',
    }
    response = client.post('/generate-workout', data=payload)
    assert response.status_code == 200, response.text
    assert 'Workout Progress' in response.text
    assert 'Experience: Beginner' in response.text

    with database.SessionLocal() as db:
        user = db.query(database.User).filter(database.User.user_id == payload['user_id']).one()
        assert user.experience_level == 'Beginner'
        assert user.last_activity is not None
        assert len(user.plans) == 1


def test_progress_completion_and_summary():
    _reset_db()
    payload = {
        'username': 'Bob',
        'user_id': 'user-002',
        'age': 35,
        'weight': 74,
        'goal': 'Muscle Gain',
        'intensity': 'high',
        'experience_level': 'Intermediate',
    }
    client.post('/generate-workout', data=payload)

    with database.SessionLocal() as db:
        user = db.query(database.User).filter(database.User.user_id == payload['user_id']).one()
        user_id = user.id

    progress_response = client.get(f'/progress/{user_id}')
    assert progress_response.status_code == 200
    progress_json = progress_response.json()
    assert progress_json['completed_days'] == 0
    assert progress_json['total_days'] == 7
    assert progress_json['progress_percentage'] == 0

    complete_response = client.post(f'/progress/{user_id}/3/complete', follow_redirects=False)
    assert complete_response.status_code == 303

    updated_progress = client.get(f'/progress/{user_id}')
    summary = updated_progress.json()
    assert summary['completed_days'] == 1
    assert summary['progress_percentage'] == 14
    assert summary['day_status'][3] is True


def test_duplicate_progress_completion_is_prevented():
    _reset_db()
    payload = {
        'username': 'Carol',
        'user_id': 'user-003',
        'age': 27,
        'weight': 62,
        'goal': 'General Fitness',
        'intensity': 'low',
        'experience_level': 'Advanced',
    }
    client.post('/generate-workout', data=payload)
    with database.SessionLocal() as db:
        user = db.query(database.User).filter(database.User.user_id == payload['user_id']).one()
        user_id = user.id

    first = client.post(f'/progress/{user_id}/1/complete', follow_redirects=False)
    second = client.post(f'/progress/{user_id}/1/complete', follow_redirects=False)
    assert first.status_code == 303
    assert second.status_code == 303

    with database.SessionLocal() as db:
        rows = db.query(database.WorkoutProgress).filter(database.WorkoutProgress.user_id == user_id).all()
        assert len(rows) == 1
        assert rows[0].day_number == 1
        assert rows[0].completed is True


def test_invalid_day_number_is_rejected():
    _reset_db()
    payload = {
        'username': 'Dane',
        'user_id': 'user-004',
        'age': 41,
        'weight': 82,
        'goal': 'Improve Endurance',
        'intensity': 'medium',
        'experience_level': 'Beginner',
    }
    client.post('/generate-workout', data=payload)
    with database.SessionLocal() as db:
        user = db.query(database.User).filter(database.User.user_id == payload['user_id']).one()
        user_id = user.id

    response = client.post(f'/progress/{user_id}/9/complete')
    assert response.status_code == 400


def test_admin_user_listing_and_delete_removes_related_data():
    _reset_db()
    with database.SessionLocal() as db:
        user = database.save_user(
            db,
            name='Delete Me',
            age=33,
            weight=75,
            goal='Flexibility & Mobility',
            intensity='low',
            user_id='user-005',
            experience_level='Advanced',
            last_activity=datetime.now(timezone.utc),
        )
        db.add(database.Plan(user_id=user.id, original_plan='{"Day 1": {"focus": "Test"}}', nutrition_tip='Hydrate'))
        db.add(
            database.WorkoutProgress(
                user_id=user.id,
                day_number=2,
                day_name='Day 2',
                completed=True,
                completed_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

    list_response = client.get('/view-all-users')
    assert list_response.status_code == 200
    assert 'Delete Me' in list_response.text
    assert 'Experience' in list_response.text
    assert 'Last Activity' in list_response.text

    delete_response = client.post(f'/admin/users/{user.id}/delete', follow_redirects=False)
    assert delete_response.status_code == 303

    with database.SessionLocal() as db:
        assert db.query(database.User).filter(database.User.id == user.id).first() is None
        assert db.query(database.Plan).filter(database.Plan.user_id == user.id).count() == 0
        assert db.query(database.WorkoutProgress).filter(database.WorkoutProgress.user_id == user.id).count() == 0


def test_fallback_behavior_when_gemini_key_missing(monkeypatch):
    _reset_db()
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    payload = {
        'username': 'Fallback User',
        'user_id': 'user-006',
        'age': 26,
        'weight': 69,
        'goal': 'Weight Loss',
        'intensity': 'low',
        'experience_level': 'Beginner',
    }
    response = client.post('/generate-workout', data=payload)
    assert response.status_code == 200
    assert 'Workout Progress' in response.text