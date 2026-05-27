from datetime import datetime, timedelta

from app.calendar.auth import google_calendar_setup_status, load_credentials
from app.config import Settings
from app.utils.datetime_utils import parse_local_datetime, serialize_local


class GoogleCalendarService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def status(self) -> dict:
        setup = google_calendar_setup_status(self.settings)
        return {
            **setup,
            "default_calendar_id": self.settings.google_calendar_default_id,
        }

    def _service(self):
        try:
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise RuntimeError(
                "Google Calendar dependencies are not installed. "
                "Run: .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt"
            ) from exc

        credentials = load_credentials(self.settings)
        return build("calendar", "v3", credentials=credentials)

    def list_calendars(self) -> dict:
        service = self._service()
        result = service.calendarList().list().execute()
        calendars = [
            {
                "id": item.get("id"),
                "summary": item.get("summary"),
                "primary": item.get("primary", False),
                "access_role": item.get("accessRole"),
                "time_zone": item.get("timeZone"),
            }
            for item in result.get("items", [])
        ]
        return {"ok": True, "calendars": calendars}

    def list_events(
        self,
        time_min: str,
        time_max: str | None = None,
        calendar_id: str | None = None,
        max_results: int = 20,
    ) -> dict:
        service = self._service()
        calendar_id = calendar_id or self.settings.google_calendar_default_id
        start = parse_local_datetime(time_min, self.settings.local_timezone)
        end = (
            parse_local_datetime(time_max, self.settings.local_timezone)
            if time_max
            else start + timedelta(days=1)
        )
        result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=serialize_local(start),
                timeMax=serialize_local(end),
                maxResults=max(1, min(100, int(max_results))),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return {
            "ok": True,
            "calendar_id": calendar_id,
            "events": [self._event_summary(item) for item in result.get("items", [])],
        }

    def get_event(self, event_id: str, calendar_id: str | None = None) -> dict:
        service = self._service()
        calendar_id = calendar_id or self.settings.google_calendar_default_id
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        return {"ok": True, "event": self._event_summary(event)}

    def create_event(
        self,
        summary: str,
        start: str,
        end: str,
        calendar_id: str | None = None,
        description: str = "",
        location: str = "",
        attendees: list[str] | None = None,
        reminders_minutes: list[int] | None = None,
    ) -> dict:
        service = self._service()
        calendar_id = calendar_id or self.settings.google_calendar_default_id
        body = self._event_body(
            summary=summary,
            start=start,
            end=end,
            description=description,
            location=location,
            attendees=attendees,
            reminders_minutes=reminders_minutes,
        )
        event = service.events().insert(calendarId=calendar_id, body=body).execute()
        verified = (
            service.events()
            .get(calendarId=calendar_id, eventId=event["id"])
            .execute()
        )
        return {
            "ok": True,
            "calendar_id": calendar_id,
            "verified_on_google": True,
            "event": self._event_summary(verified),
        }

    def quick_add_event(self, text: str, calendar_id: str | None = None) -> dict:
        service = self._service()
        calendar_id = calendar_id or self.settings.google_calendar_default_id
        event = (
            service.events()
            .quickAdd(calendarId=calendar_id, text=text)
            .execute()
        )
        verified = (
            service.events()
            .get(calendarId=calendar_id, eventId=event["id"])
            .execute()
        )
        return {
            "ok": True,
            "calendar_id": calendar_id,
            "verified_on_google": True,
            "event": self._event_summary(verified),
        }

    def update_event(
        self,
        event_id: str,
        calendar_id: str | None = None,
        summary: str | None = None,
        start: str | None = None,
        end: str | None = None,
        description: str | None = None,
        location: str | None = None,
        reminders_minutes: list[int] | None = None,
    ) -> dict:
        service = self._service()
        calendar_id = calendar_id or self.settings.google_calendar_default_id
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

        if summary is not None:
            event["summary"] = summary
        if description is not None:
            event["description"] = description
        if location is not None:
            event["location"] = location
        if start is not None and end is not None:
            event.update(self._time_fields(start, end))
        if reminders_minutes is not None:
            event["reminders"] = self._reminders(reminders_minutes)

        updated = (
            service.events()
            .update(calendarId=calendar_id, eventId=event_id, body=event)
            .execute()
        )
        return {"ok": True, "event": self._event_summary(updated)}

    def delete_event(self, event_id: str, calendar_id: str | None = None) -> dict:
        service = self._service()
        calendar_id = calendar_id or self.settings.google_calendar_default_id
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return {"ok": True, "event_id": event_id, "deleted": True}

    def find_free_slots(
        self,
        time_min: str,
        time_max: str,
        duration_minutes: int,
        calendar_ids: list[str] | None = None,
    ) -> dict:
        service = self._service()
        calendar_ids = calendar_ids or [self.settings.google_calendar_default_id]
        start = parse_local_datetime(time_min, self.settings.local_timezone)
        end = parse_local_datetime(time_max, self.settings.local_timezone)
        duration = timedelta(minutes=max(1, int(duration_minutes)))
        body = {
            "timeMin": serialize_local(start),
            "timeMax": serialize_local(end),
            "items": [{"id": calendar_id} for calendar_id in calendar_ids],
        }
        result = service.freebusy().query(body=body).execute()
        busy = []
        for calendar in result.get("calendars", {}).values():
            for item in calendar.get("busy", []):
                busy.append(
                    (
                        parse_local_datetime(item["start"], self.settings.local_timezone),
                        parse_local_datetime(item["end"], self.settings.local_timezone),
                    )
                )
        busy.sort(key=lambda item: item[0])

        free_slots = []
        cursor = start
        for busy_start, busy_end in busy:
            if busy_start > cursor and busy_start - cursor >= duration:
                free_slots.append(
                    {"start": serialize_local(cursor), "end": serialize_local(busy_start)}
                )
            if busy_end > cursor:
                cursor = busy_end
        if end > cursor and end - cursor >= duration:
            free_slots.append({"start": serialize_local(cursor), "end": serialize_local(end)})

        return {"ok": True, "free_slots": free_slots}

    def _event_body(
        self,
        summary: str,
        start: str,
        end: str,
        description: str = "",
        location: str = "",
        attendees: list[str] | None = None,
        reminders_minutes: list[int] | None = None,
    ) -> dict:
        body = {
            "summary": summary,
            "description": description,
            "location": location,
            **self._time_fields(start, end),
        }
        if attendees:
            body["attendees"] = [{"email": email} for email in attendees]
        if reminders_minutes is not None:
            body["reminders"] = self._reminders(reminders_minutes)
        return body

    def _time_fields(self, start: str, end: str) -> dict:
        parsed_start = parse_local_datetime(start, self.settings.local_timezone)
        parsed_end = parse_local_datetime(end, self.settings.local_timezone)
        return {
            "start": {
                "dateTime": serialize_local(parsed_start),
                "timeZone": self.settings.local_timezone,
            },
            "end": {
                "dateTime": serialize_local(parsed_end),
                "timeZone": self.settings.local_timezone,
            },
        }

    def _reminders(self, minutes: list[int]) -> dict:
        return {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": max(0, int(value))}
                for value in minutes
            ],
        }

    def _event_summary(self, event: dict) -> dict:
        return {
            "id": event.get("id"),
            "summary": event.get("summary"),
            "description": event.get("description", ""),
            "location": event.get("location", ""),
            "start": event.get("start", {}),
            "end": event.get("end", {}),
            "html_link": event.get("htmlLink"),
            "status": event.get("status"),
            "creator": event.get("creator", {}),
            "organizer": event.get("organizer", {}),
            "reminders": event.get("reminders", {}),
        }
