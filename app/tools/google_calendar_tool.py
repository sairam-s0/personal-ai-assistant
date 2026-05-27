from app.calendar.service import GoogleCalendarService
from app.config import Settings


class GoogleCalendarTool:
    def __init__(self, settings: Settings) -> None:
        self.service = GoogleCalendarService(settings)

    def get_google_calendar_status(self) -> dict:
        return self.service.status()

    def list_google_calendars(self) -> dict:
        return self._safe(self.service.list_calendars)

    def list_google_calendar_events(self, **kwargs) -> dict:
        return self._safe(self.service.list_events, **kwargs)

    def get_google_calendar_event(self, **kwargs) -> dict:
        return self._safe(self.service.get_event, **kwargs)

    def create_google_calendar_event(self, **kwargs) -> dict:
        return self._safe(self.service.create_event, **kwargs)

    def quick_add_google_calendar_event(self, **kwargs) -> dict:
        return self._safe(self.service.quick_add_event, **kwargs)

    def update_google_calendar_event(self, **kwargs) -> dict:
        return self._safe(self.service.update_event, **kwargs)

    def delete_google_calendar_event(self, **kwargs) -> dict:
        return self._safe(self.service.delete_event, **kwargs)

    def find_google_calendar_free_slots(self, **kwargs) -> dict:
        return self._safe(self.service.find_free_slots, **kwargs)

    def _safe(self, fn, **kwargs) -> dict:
        try:
            return fn(**kwargs)
        except Exception as exc:
            return {"ok": False, "error": str(exc), **self.service.status()}
