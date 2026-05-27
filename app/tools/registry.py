import json
from collections.abc import Callable

from app.config import Settings
from app.tools.google_calendar_tool import GoogleCalendarTool
from app.tools.memory_tool import MemoryTool
from app.tools.reminder_tool import ReminderTool
from app.tools.task_tool import TaskTool
from app.tools.time_tool import TimeTool


class ToolRegistry:
    def __init__(self, settings: Settings) -> None:
        memory = MemoryTool(settings)
        tasks = TaskTool(settings)
        reminders = ReminderTool(settings)
        time = TimeTool(settings)
        gcal = GoogleCalendarTool(settings)
        self._functions: dict[str, Callable[..., dict]] = {
            "get_current_time": time.get_current_time,
            "get_google_calendar_status": gcal.get_google_calendar_status,
            "list_google_calendars": gcal.list_google_calendars,
            "list_google_calendar_events": gcal.list_google_calendar_events,
            "get_google_calendar_event": gcal.get_google_calendar_event,
            "create_google_calendar_event": gcal.create_google_calendar_event,
            "quick_add_google_calendar_event": gcal.quick_add_google_calendar_event,
            "update_google_calendar_event": gcal.update_google_calendar_event,
            "delete_google_calendar_event": gcal.delete_google_calendar_event,
            "find_google_calendar_free_slots": gcal.find_google_calendar_free_slots,
            "save_memory": memory.save_memory,
            "search_memory": memory.search_memory,
            "list_memories": memory.list_memories,
            "create_task": tasks.create_task,
            "list_tasks": tasks.list_tasks,
            "update_task": tasks.update_task,
            "create_reminder": reminders.create_reminder,
            "list_reminders": reminders.list_reminders,
            "complete_reminder": reminders.complete_reminder,
            "cancel_reminder": reminders.cancel_reminder,
            "delete_reminder": reminders.delete_reminder,
        }

    def schemas(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "Get the current local date, time, timezone, and weekday for the user's PC.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_google_calendar_status",
                    "description": "Check whether Google Calendar credentials and token are configured on this PC.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_google_calendars",
                    "description": "List calendars available in the connected Google Calendar account.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_google_calendar_events",
                    "description": "List Google Calendar events in a time range.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "time_min": {"type": "string"},
                            "time_max": {"type": "string"},
                            "calendar_id": {"type": "string"},
                            "max_results": {"type": "integer", "minimum": 1, "maximum": 100},
                        },
                        "required": ["time_min"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_google_calendar_event",
                    "description": "Get one Google Calendar event by event id.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "event_id": {"type": "string"},
                            "calendar_id": {"type": "string"},
                        },
                        "required": ["event_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_google_calendar_event",
                    "description": "Create a Google Calendar event with optional location, attendees, description, and popup reminders.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "summary": {"type": "string"},
                            "start": {"type": "string"},
                            "end": {"type": "string"},
                            "calendar_id": {"type": "string"},
                            "description": {"type": "string"},
                            "location": {"type": "string"},
                            "attendees": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "reminders_minutes": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "Popup reminder offsets before the event, for example [10] for 10 minutes before.",
                            },
                        },
                        "required": ["summary", "start", "end"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "quick_add_google_calendar_event",
                    "description": "Use Google Calendar quickAdd to create an event from a natural-language text string.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "calendar_id": {"type": "string"},
                        },
                        "required": ["text"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "update_google_calendar_event",
                    "description": "Update an existing Google Calendar event. If changing time, provide both start and end.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "event_id": {"type": "string"},
                            "calendar_id": {"type": "string"},
                            "summary": {"type": "string"},
                            "start": {"type": "string"},
                            "end": {"type": "string"},
                            "description": {"type": "string"},
                            "location": {"type": "string"},
                            "reminders_minutes": {
                                "type": "array",
                                "items": {"type": "integer"},
                            },
                        },
                        "required": ["event_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_google_calendar_event",
                    "description": "Delete a Google Calendar event by event id.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "event_id": {"type": "string"},
                            "calendar_id": {"type": "string"},
                        },
                        "required": ["event_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "find_google_calendar_free_slots",
                    "description": "Find free time slots in Google Calendar using the FreeBusy API.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "time_min": {"type": "string"},
                            "time_max": {"type": "string"},
                            "duration_minutes": {"type": "integer", "minimum": 1},
                            "calendar_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["time_min", "time_max", "duration_minutes"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "save_memory",
                    "description": "Save a durable memory about the user, preferences, goals, facts, or important context.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "memory_type": {
                                "type": "string",
                                "enum": ["profile", "goal", "preference", "note"],
                            },
                            "importance": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 5,
                            },
                        },
                        "required": ["content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_memory",
                    "description": "Search durable local memory stored on this PC.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_memories",
                    "description": "List the most important recent memories.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "minimum": 1, "maximum": 50}
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_task",
                    "description": "Create a local task.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "priority": {"type": "integer", "minimum": 1, "maximum": 5},
                            "due_at": {"type": "string", "description": "Optional ISO-like date or datetime."},
                            "notes": {"type": "string"},
                        },
                        "required": ["title"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_tasks",
                    "description": "List local tasks.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "enum": ["open", "done", "all"]},
                            "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "update_task",
                    "description": "Update a local task by id.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "integer"},
                            "status": {"type": "string"},
                            "title": {"type": "string"},
                            "priority": {"type": "integer", "minimum": 1, "maximum": 5},
                            "due_at": {"type": "string"},
                            "notes": {"type": "string"},
                        },
                        "required": ["task_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_reminder",
                    "description": "Create a local reminder on this PC. Use get_current_time first when the user gives relative dates like tomorrow, tonight, or in 20 minutes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "remind_at": {
                                "type": "string",
                                "description": "ISO datetime or phrase like 'in 20 minutes', 'today 6 PM', or 'tomorrow 9 AM'.",
                            },
                            "notes": {"type": "string"},
                        },
                        "required": ["title", "remind_at"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_reminders",
                    "description": "List local reminders.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["scheduled", "fired", "done", "cancelled", "all"],
                            },
                            "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "complete_reminder",
                    "description": "Mark a local reminder as done.",
                    "parameters": {
                        "type": "object",
                        "properties": {"reminder_id": {"type": "integer"}},
                        "required": ["reminder_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "cancel_reminder",
                    "description": "Cancel a local reminder.",
                    "parameters": {
                        "type": "object",
                        "properties": {"reminder_id": {"type": "integer"}},
                        "required": ["reminder_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_reminder",
                    "description": "Permanently delete a local reminder by id when the user explicitly asks to delete or remove it.",
                    "parameters": {
                        "type": "object",
                        "properties": {"reminder_id": {"type": "integer"}},
                        "required": ["reminder_id"],
                    },
                },
            },
        ]

    def execute(self, name: str, raw_arguments: str | dict | None) -> dict:
        if name not in self._functions:
            return {"ok": False, "error": f"Unknown tool: {name}"}

        if raw_arguments is None:
            arguments = {}
        elif isinstance(raw_arguments, dict):
            arguments = raw_arguments
        else:
            try:
                arguments = json.loads(raw_arguments or "{}")
            except json.JSONDecodeError as exc:
                return {"ok": False, "error": f"Invalid tool arguments: {exc}"}

        try:
            return self._functions[name](**arguments)
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
