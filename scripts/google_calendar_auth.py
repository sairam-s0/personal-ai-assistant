from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.calendar.auth import SCOPES
from app.config import get_settings


def main() -> None:
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise SystemExit(
            "Google auth dependency missing. Run: "
            ".\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt"
        ) from exc

    settings = get_settings()
    credentials_path = Path(settings.google_credentials_path)
    token_path = Path(settings.google_token_path)

    if not credentials_path.exists():
        raise SystemExit(
            f"Missing {credentials_path}. Download OAuth desktop credentials "
            "from Google Cloud Console and place them there."
        )

    token_path.parent.mkdir(parents=True, exist_ok=True)
    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
    credentials = flow.run_local_server(port=0)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    print(f"Saved Google Calendar token to {token_path}")


if __name__ == "__main__":
    main()
