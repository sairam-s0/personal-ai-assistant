from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.agents.orchestrator import Orchestrator
from app.calendar.auth import build_google_auth_url, finish_google_auth
from app.config import get_settings
from app.db.session import init_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.conversation_store import ConversationStore
from app.tools.google_calendar_tool import GoogleCalendarTool
from app.tools.reminder_tool import ReminderTool
from app.tools.time_tool import TimeTool


settings = get_settings()
BASE_DIR = Path(__file__).resolve().parent
UI_DIR = BASE_DIR / "ui"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(settings)
    yield


app = FastAPI(title="Personal AI Assistant", version="0.2.0", lifespan=lifespan)
app.mount("/assets", StaticFiles(directory=UI_DIR / "assets"), name="assets")
orchestrator = Orchestrator(settings=settings)
conversations = ConversationStore(settings=settings)
reminders = ReminderTool(settings=settings)
time_tool = TimeTool(settings=settings)
google_calendar = GoogleCalendarTool(settings=settings)


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(UI_DIR / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=204)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


@app.get("/time")
async def current_time() -> dict:
    return time_tool.get_current_time()


@app.get("/google-calendar/status")
async def google_calendar_status() -> dict:
    return google_calendar.get_google_calendar_status()


@app.get("/google-calendar/login", include_in_schema=False)
async def google_calendar_login(request: Request) -> RedirectResponse:
    try:
        redirect_uri = str(request.url_for("google_calendar_callback"))
        auth_url = build_google_auth_url(settings, redirect_uri)
        return RedirectResponse(auth_url)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/google-calendar/callback", include_in_schema=False)
async def google_calendar_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    if error:
        return RedirectResponse(f"/?google_calendar_error={error}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing Google OAuth code/state.")

    try:
        redirect_uri = str(request.url_for("google_calendar_callback"))
        finish_google_auth(settings, redirect_uri, code, state)
        return RedirectResponse("/?google_calendar=connected")
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/sessions")
async def sessions() -> dict[str, list[dict]]:
    return {"sessions": conversations.list_conversations()}


@app.get("/sessions/{session_id}")
async def session_messages(session_id: str) -> dict[str, list[dict]]:
    messages = conversations.get_messages(session_id, limit=100)
    return {"messages": [message.model_dump() for message in messages]}


@app.get("/reminders")
async def list_reminders(status: str = "scheduled") -> dict:
    return reminders.list_reminders(status=status)


@app.get("/reminders/due")
async def due_reminders() -> dict:
    return reminders.due_reminders()


@app.post("/reminders/{reminder_id}/fired")
async def mark_reminder_fired(reminder_id: int) -> dict:
    return reminders.mark_reminder_fired(reminder_id)


@app.delete("/reminders/{reminder_id}")
async def delete_reminder(reminder_id: int) -> dict:
    return reminders.delete_reminder(reminder_id)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        return await orchestrator.chat(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
