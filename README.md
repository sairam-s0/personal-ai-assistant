# Personal AI Assistant

A local-first personal assistant built with FastAPI, Groq, SQLite, and a lightweight browser UI. It can chat, remember useful context, manage local tasks and reminders, report the current local time, and connect to Google Calendar when OAuth credentials are configured.

## What It Does

- Serves a browser chat UI at `/`
- Provides a `/chat` API backed by Groq chat completions
- Stores chat sessions, memories, tasks, and reminders locally in SQLite
- Supports tool calling for memory, tasks, reminders, current time, and Google Calendar
- Offers Google Calendar OAuth login and calendar/event operations
- Includes pytest coverage for the main API, tools, prompt building, and Google auth behavior

## Tech Stack

- Python
- FastAPI
- Groq SDK
- SQLite
- Pydantic settings
- Google Calendar API
- Pytest

## Project Structure

```text
app/
  agents/          Chat orchestration and tool loop
  calendar/        Google OAuth and Calendar service helpers
  db/              SQLite setup
  llm/             Groq client, prompt builder, token guard, response parser
  schemas/         API request and response models
  services/        Local conversation storage
  tools/           Memory, task, reminder, time, and calendar tools
  ui/              Browser UI and static assets
scripts/           Utility scripts
tests/             Automated tests
```

## Getting Started

### 1. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure environment variables

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set at least:

```text
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
```

Optional settings include:

```text
DATABASE_URL=sqlite:///data/assistant.db
LOCAL_TIMEZONE=Asia/Kolkata
GOOGLE_CREDENTIALS_PATH=data/google/credentials.json
GOOGLE_TOKEN_PATH=data/google/token.json
APP_ENV=development
LOG_LEVEL=INFO
```

## Run Locally

```powershell
uvicorn app.main:app --reload
```

Open the app:

```text
http://127.0.0.1:8000/
```

Check the API health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Send a chat message:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/chat `
  -ContentType "application/json" `
  -Body '{"message":"Plan my day at a high level."}'
```

Interactive API docs are available at:

```text
http://127.0.0.1:8000/docs
```

## Google Calendar Setup

Google Calendar is optional. The app still runs without it, but calendar tools will report missing credentials until OAuth is configured.

1. Enable the Google Calendar API in Google Cloud Console.
2. Create OAuth credentials with application type `Desktop app`.
3. Download the JSON credentials file.
4. Save it as:

```text
data/google/credentials.json
```

5. Run the local auth script:

```powershell
.\.venv\Scripts\python.exe scripts\google_calendar_auth.py
```

This creates:

```text
data/google/token.json
```

You can also use the browser OAuth flow exposed by the app:

```text
http://127.0.0.1:8000/google-calendar/login
```

## Run Tests

```powershell
pytest
```

## API Highlights

- `GET /` - browser UI
- `GET /health` - service status
- `GET /time` - current local time
- `POST /chat` - assistant chat endpoint
- `GET /sessions` - saved chat sessions
- `GET /sessions/{session_id}` - messages for one session
- `GET /reminders` - scheduled reminders
- `GET /reminders/due` - reminders ready to fire
- `POST /reminders/{reminder_id}/fired` - mark a reminder as fired
- `DELETE /reminders/{reminder_id}` - delete a reminder
- `GET /google-calendar/status` - Calendar connection status
- `GET /google-calendar/login` - start Calendar OAuth

## Notes For GitHub Visitors

This project is intended as a personal, local assistant rather than a hosted multi-user service. Secrets, Google tokens, local databases, logs, and generated runtime files should stay out of version control.

The bundled `readme.txt` belongs to a separate Windows utility file and is not the project README. Start with this `README.md` for setup and development.

## License

See [LICENSE](LICENSE).
