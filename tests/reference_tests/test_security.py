"""Security tests: random SECRET_KEY for placeholders, admin disabled on empty password."""
import logging

from fastapi.testclient import TestClient
from itsdangerous import URLSafeTimedSerializer

from app import config, routes
from app.main import app
from app.routes import ADMIN_COOKIE, ADMIN_DISABLED_MSG


def test_resolve_secret_key_replaces_placeholders():
    for raw in (None, "", "change-me"):
        a, b = config._resolve_secret_key(raw), config._resolve_secret_key(raw)
        assert len(a) >= 32 and a != b and a != "change-me"
    assert config._resolve_secret_key("my-real-secret") == "my-real-secret"


def test_forged_change_me_cookie_rejected(client, monkeypatch):
    # Sign sessions with the key the app would get from SECRET_KEY=change-me.
    monkeypatch.setattr(routes, "_signer", URLSafeTimedSerializer(
        config._resolve_secret_key("change-me"), salt="fitbuddy-admin"))
    forged = URLSafeTimedSerializer("change-me", salt="fitbuddy-admin").dumps("admin")
    client.cookies.set(ADMIN_COOKIE, forged)
    assert client.get("/view-all-users").status_code == 401


def test_startup_warnings():
    assert any("SECRET_KEY" in w for w in config.startup_warnings("change-me", "strong-pass"))
    assert any("admin123" in w for w in config.startup_warnings("real", "admin123"))
    assert config.startup_warnings("real", "strong-pass") == []


def test_startup_warnings_logged(monkeypatch, caplog):
    monkeypatch.setattr(config, "STARTUP_WARNINGS", config.startup_warnings("real", "admin123"))
    with caplog.at_level(logging.WARNING, logger="fitbuddy.config"), TestClient(app):
        pass
    assert any("admin123" in r.getMessage() for r in caplog.records)


def test_empty_admin_password_disables_admin(admin_client, monkeypatch):
    assert admin_client.get("/view-all-users").status_code == 200
    monkeypatch.setattr(config, "ADMIN_PASSWORD", "")
    r = admin_client.post("/admin/login", data={"password": ""}, follow_redirects=False)
    assert r.status_code == 401
    assert ADMIN_DISABLED_MSG in r.text
    assert ADMIN_COOKIE not in r.cookies
    assert admin_client.get("/view-all-users").status_code == 401
