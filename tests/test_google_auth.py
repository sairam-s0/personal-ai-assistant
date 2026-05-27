import json
from pathlib import Path

import app.calendar.auth as auth
from app.config import Settings


class FakeCredentials:
    def to_json(self) -> str:
        return '{"token":"ok"}'


class FakeFlow:
    created = []

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.redirect_uri = None
        self.code_verifier = kwargs.get("code_verifier")
        self.credentials = FakeCredentials()
        FakeFlow.created.append(self)

    @classmethod
    def from_client_secrets_file(cls, _path, scopes, **kwargs):
        return cls(scopes=scopes, **kwargs)

    def authorization_url(self, **_kwargs):
        self.code_verifier = "saved-verifier"
        return "https://accounts.google.com/o/oauth2/auth", "ignored-state"

    def fetch_token(self, code):
        self.fetched_code = code
        return {"access_token": "ok"}


def test_google_oauth_persists_code_verifier(tmp_path: Path, monkeypatch) -> None:
    credentials_path = tmp_path / "credentials.json"
    token_path = tmp_path / "token.json"
    credentials_path.write_text("{}", encoding="utf-8")
    state_path = tmp_path / "oauth_state.json"
    settings = Settings(
        groq_api_key="test",
        google_credentials_path=str(credentials_path),
        google_token_path=str(token_path),
    )

    monkeypatch.setattr(auth, "STATE_PATH", state_path)
    monkeypatch.setattr(
        "google_auth_oauthlib.flow.Flow",
        FakeFlow,
    )
    FakeFlow.created.clear()

    auth.build_google_auth_url(settings, "http://127.0.0.1:8000/google-calendar/callback")
    saved = json.loads(state_path.read_text(encoding="utf-8"))
    auth.finish_google_auth(
        settings,
        "http://127.0.0.1:8000/google-calendar/callback",
        code="auth-code",
        state=saved["state"],
    )

    callback_flow = FakeFlow.created[-1]
    assert saved["code_verifier"] == "saved-verifier"
    assert callback_flow.kwargs["code_verifier"] == "saved-verifier"
    assert token_path.exists()
