"""Test setup: force demo mode and a throwaway SQLite DB *before* the app is imported."""
import os
import tempfile

_tmpdir = tempfile.mkdtemp(prefix="fitbuddy-test-")
os.environ["DEMO_MODE"] = "true"
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmpdir, 'test.db')}"
os.environ["ADMIN_PASSWORD"] = "test-admin"
os.environ["SECRET_KEY"] = "test-secret"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def admin_client(client):
    r = client.post("/admin/login", data={"password": "test-admin"}, follow_redirects=False)
    assert r.status_code == 303
    return client
