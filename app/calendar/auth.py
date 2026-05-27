from pathlib import Path
from typing import Any
import json
from uuid import uuid4

from app.config import Settings


SCOPES = ["https://www.googleapis.com/auth/calendar"]
STATE_PATH = Path("data/google/oauth_state.json")


def google_calendar_setup_status(settings: Settings) -> dict:
    credentials_path = Path(settings.google_credentials_path)
    token_path = Path(settings.google_token_path)
    missing = []
    if not credentials_path.exists():
        missing.append(str(credentials_path))
    if not token_path.exists():
        missing.append(str(token_path))

    return {
        "ok": not missing,
        "credentials_path": str(credentials_path),
        "token_path": str(token_path),
        "missing": missing,
        "auth_command": (
            ".\\.venv\\Scripts\\python.exe scripts\\google_calendar_auth.py"
        ),
        "login_url": "/google-calendar/login",
    }


def build_google_auth_url(settings: Settings, redirect_uri: str) -> str:
    try:
        from google_auth_oauthlib.flow import Flow
    except ImportError as exc:
        raise RuntimeError(
            "Google auth dependency missing. Run: "
            ".\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt"
        ) from exc

    credentials_path = Path(settings.google_credentials_path)
    if not credentials_path.exists():
        raise RuntimeError(f"Missing Google credentials file: {credentials_path}")

    flow = Flow.from_client_secrets_file(str(credentials_path), scopes=SCOPES)
    flow.redirect_uri = redirect_uri
    state = str(uuid4())
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(
            {
                "state": state,
                "redirect_uri": redirect_uri,
                "code_verifier": flow.code_verifier,
            }
        ),
        encoding="utf-8",
    )
    return authorization_url


def finish_google_auth(settings: Settings, redirect_uri: str, code: str, state: str) -> None:
    try:
        from google_auth_oauthlib.flow import Flow
    except ImportError as exc:
        raise RuntimeError(
            "Google auth dependency missing. Run: "
            ".\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt"
        ) from exc

    if not STATE_PATH.exists():
        raise RuntimeError("OAuth state is missing. Start Google login again.")

    saved = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    if state != saved.get("state"):
        raise RuntimeError("OAuth state mismatch. Start Google login again.")

    credentials_path = Path(settings.google_credentials_path)
    token_path = Path(settings.google_token_path)
    flow = Flow.from_client_secrets_file(
        str(credentials_path),
        scopes=SCOPES,
        state=state,
        code_verifier=saved.get("code_verifier"),
    )
    flow.redirect_uri = saved.get("redirect_uri") or redirect_uri
    try:
        flow.fetch_token(code=code)
    except Exception as exc:
        raise RuntimeError(
            "Google OAuth token exchange failed. Start Google login again."
        ) from exc

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(flow.credentials.to_json(), encoding="utf-8")
    STATE_PATH.unlink(missing_ok=True)


def load_credentials(settings: Settings) -> Any:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError as exc:
        raise RuntimeError(
            "Google Calendar dependencies are not installed. "
            "Run: .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt"
        ) from exc

    token_path = Path(settings.google_token_path)
    if not token_path.exists():
        raise RuntimeError(
            "Google Calendar token is missing. Run: "
            ".\\.venv\\Scripts\\python.exe scripts\\google_calendar_auth.py"
        )

    credentials = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json(), encoding="utf-8")

    if not credentials or not credentials.valid:
        raise RuntimeError(
            "Google Calendar token is invalid. Re-run: "
            ".\\.venv\\Scripts\\python.exe scripts\\google_calendar_auth.py"
        )

    return credentials
