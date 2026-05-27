from app.config import Settings
from app.utils.datetime_utils import now_local, serialize_local


class TimeTool:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def get_current_time(self) -> dict:
        current = now_local(self.settings.local_timezone)
        return {
            "ok": True,
            "timezone": self.settings.local_timezone,
            "iso": serialize_local(current),
            "date": current.date().isoformat(),
            "time": current.strftime("%H:%M:%S"),
            "weekday": current.strftime("%A"),
        }
