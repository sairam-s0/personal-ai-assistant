# Personal Assistant

Phase 1 implements the core Groq chat layer and a small FastAPI API around it.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set `GROQ_API_KEY`.

## Run

```powershell
uvicorn app.main:app --reload
```

## Try It

Open the browser UI:

```text
http://127.0.0.1:8000/
```

Or call the API directly:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/chat `
  -ContentType "application/json" `
  -Body '{"message":"Plan my day at a high level."}'
```

## Phase 1 Scope

- FastAPI app
- Settings loader
- Groq client wrapper
- Prompt builder
- Token budget guard
- Basic response parser
- `/chat` endpoint

## Phase 2 Scope

- Groq tool-calling loop
- Local SQLite memory stored at `data/assistant.db`
- Local tasks tool
- Past chat sessions stored on this PC
- UI session picker

## Phase 3 Scope

- Local timezone-aware `get_current_time` tool
- Local reminders stored in SQLite
- Browser notification polling while the web app is open
- Reminder APIs: `/reminders`, `/reminders/due`, `/reminders/{id}/fired`

## Google Calendar Setup

1. Install the Google dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

2. Create OAuth credentials in Google Cloud Console:

- Application type: Desktop app
- Calendar API enabled
- Download the JSON file

3. Place it here:

```text
data/google/credentials.json
```

4. Run the local auth flow:

```powershell
.\.venv\Scripts\python.exe scripts\google_calendar_auth.py
```

That creates:

```text
data/google/token.json
```

After that, the assistant can list calendars, list events, create events, quick-add events, update events, delete events, and find free slots.

Next phases should add scheduler optimization, MCP, RAG, and richer UI controls in that order.
