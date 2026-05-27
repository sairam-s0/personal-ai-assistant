from pathlib import Path

from app.config import Settings
from app.db.session import init_db
from app.services.conversation_store import ConversationStore
from app.tools.memory_tool import MemoryTool
from app.tools.google_calendar_tool import GoogleCalendarTool
from app.tools.reminder_tool import ReminderTool
from app.tools.task_tool import TaskTool
from app.tools.time_tool import TimeTool


def test_memory_tool_saves_and_searches(tmp_path: Path) -> None:
    settings = Settings(
        groq_api_key="test",
        database_url=f"sqlite:///{tmp_path / 'assistant.db'}",
    )
    init_db(settings)
    tool = MemoryTool(settings)

    saved = tool.save_memory("User prefers evening study.", "preference", 5)
    result = tool.search_memory("evening study")

    assert saved["ok"] is True
    assert result["memories"][0]["content"] == "User prefers evening study."


def test_task_tool_creates_and_lists_tasks(tmp_path: Path) -> None:
    settings = Settings(
        groq_api_key="test",
        database_url=f"sqlite:///{tmp_path / 'assistant.db'}",
    )
    init_db(settings)
    tool = TaskTool(settings)

    created = tool.create_task("Revise embedded systems", priority=4)
    listed = tool.list_tasks()

    assert created["ok"] is True
    assert listed["tasks"][0]["title"] == "Revise embedded systems"


def test_conversation_store_persists_messages(tmp_path: Path) -> None:
    settings = Settings(
        groq_api_key="test",
        database_url=f"sqlite:///{tmp_path / 'assistant.db'}",
    )
    init_db(settings)
    store = ConversationStore(settings)

    session_id = store.ensure_conversation(None, "Hello assistant")
    store.add_message(session_id, "user", "Hello assistant")
    store.add_message(session_id, "assistant", "Hello.")

    messages = store.get_messages(session_id)

    assert [message.role for message in messages] == ["user", "assistant"]
    assert store.list_conversations()[0]["id"] == session_id


def test_time_tool_returns_local_time(tmp_path: Path) -> None:
    settings = Settings(
        groq_api_key="test",
        database_url=f"sqlite:///{tmp_path / 'assistant.db'}",
        local_timezone="Asia/Kolkata",
    )
    tool = TimeTool(settings)

    result = tool.get_current_time()

    assert result["ok"] is True
    assert result["timezone"] == "Asia/Kolkata"
    assert "iso" in result


def test_reminder_tool_creates_and_lists_reminders(tmp_path: Path) -> None:
    settings = Settings(
        groq_api_key="test",
        database_url=f"sqlite:///{tmp_path / 'assistant.db'}",
        local_timezone="Asia/Kolkata",
    )
    init_db(settings)
    tool = ReminderTool(settings)

    created = tool.create_reminder("Drink water", "in 1 hour")
    listed = tool.list_reminders()

    assert created["ok"] is True
    assert listed["reminders"][0]["title"] == "Drink water"


def test_due_reminder_can_be_marked_fired(tmp_path: Path) -> None:
    settings = Settings(
        groq_api_key="test",
        database_url=f"sqlite:///{tmp_path / 'assistant.db'}",
        local_timezone="Asia/Kolkata",
    )
    init_db(settings)
    tool = ReminderTool(settings)

    created = tool.create_reminder("Stand up", "now")
    due = tool.due_reminders()
    fired = tool.mark_reminder_fired(created["id"])

    assert due["reminders"][0]["title"] == "Stand up"
    assert fired["ok"] is True


def test_reminder_tool_deletes_reminder(tmp_path: Path) -> None:
    settings = Settings(
        groq_api_key="test",
        database_url=f"sqlite:///{tmp_path / 'assistant.db'}",
        local_timezone="Asia/Kolkata",
    )
    init_db(settings)
    tool = ReminderTool(settings)

    created = tool.create_reminder("Delete me", "in 1 hour")
    deleted = tool.delete_reminder(created["id"])
    listed = tool.list_reminders(status="all")

    assert deleted == {"ok": True, "id": created["id"], "deleted": True}
    assert listed["reminders"] == []


def test_google_calendar_status_reports_missing_setup(tmp_path: Path) -> None:
    settings = Settings(
        groq_api_key="test",
        database_url=f"sqlite:///{tmp_path / 'assistant.db'}",
        google_credentials_path=str(tmp_path / "credentials.json"),
        google_token_path=str(tmp_path / "token.json"),
    )
    tool = GoogleCalendarTool(settings)

    status = tool.get_google_calendar_status()

    assert status["ok"] is False
    assert str(tmp_path / "credentials.json") in status["missing"]
    assert str(tmp_path / "token.json") in status["missing"]
