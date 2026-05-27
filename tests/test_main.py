from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def test_root_serves_ui() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "Personal Assistant" in response.text


def test_favicon_is_empty_success() -> None:
    client = TestClient(app)

    response = client.get("/favicon.ico")

    assert response.status_code == 204


def test_google_calendar_login_reports_missing_credentials(tmp_path) -> None:
    settings = get_settings()
    original_credentials_path = settings.google_credentials_path
    original_token_path = settings.google_token_path
    settings.google_credentials_path = str(tmp_path / "missing_credentials.json")
    settings.google_token_path = str(tmp_path / "token.json")
    client = TestClient(app)

    try:
        response = client.get("/google-calendar/login", follow_redirects=False)
    finally:
        settings.google_credentials_path = original_credentials_path
        settings.google_token_path = original_token_path

    assert response.status_code == 400
    assert "Missing Google credentials file" in response.json()["detail"]
