from app.config import Settings
from app.db.session import connect
from app.utils.datetime_utils import now_local, parse_local_datetime, serialize_local


class ReminderTool:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_reminder(
        self,
        title: str,
        remind_at: str,
        notes: str = "",
    ) -> dict:
        title = title.strip()
        if not title:
            return {"ok": False, "error": "Reminder title is required."}

        try:
            parsed = parse_local_datetime(remind_at, self.settings.local_timezone)
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}

        with connect(self.settings) as db:
            cursor = db.execute(
                """
                INSERT INTO reminders (title, remind_at, timezone, notes)
                VALUES (?, ?, ?, ?)
                """,
                (
                    title,
                    serialize_local(parsed),
                    self.settings.local_timezone,
                    notes,
                ),
            )
        return {
            "ok": True,
            "id": cursor.lastrowid,
            "title": title,
            "remind_at": serialize_local(parsed),
            "timezone": self.settings.local_timezone,
        }

    def list_reminders(self, status: str = "scheduled", limit: int = 20) -> dict:
        status = status.strip().lower()
        limit = max(1, min(100, int(limit)))
        where = ""
        params: tuple = (limit,)
        if status != "all":
            where = "WHERE status = ?"
            params = (status, limit)

        with connect(self.settings) as db:
            rows = db.execute(
                f"""
                SELECT id, title, remind_at, timezone, status, notes, created_at, fired_at
                FROM reminders
                {where}
                ORDER BY remind_at ASC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return {"ok": True, "reminders": [dict(row) for row in rows]}

    def complete_reminder(self, reminder_id: int) -> dict:
        return self._set_status(reminder_id, "done")

    def cancel_reminder(self, reminder_id: int) -> dict:
        return self._set_status(reminder_id, "cancelled")

    def delete_reminder(self, reminder_id: int) -> dict:
        with connect(self.settings) as db:
            cursor = db.execute(
                "DELETE FROM reminders WHERE id = ?",
                (int(reminder_id),),
            )
        if cursor.rowcount == 0:
            return {"ok": False, "error": f"Reminder {reminder_id} was not found."}
        return {"ok": True, "id": reminder_id, "deleted": True}

    def due_reminders(self, limit: int = 20) -> dict:
        current = serialize_local(now_local(self.settings.local_timezone))
        limit = max(1, min(100, int(limit)))
        with connect(self.settings) as db:
            rows = db.execute(
                """
                SELECT id, title, remind_at, timezone, status, notes, created_at
                FROM reminders
                WHERE status = 'scheduled' AND remind_at <= ?
                ORDER BY remind_at ASC
                LIMIT ?
                """,
                (current, limit),
            ).fetchall()
        return {"ok": True, "reminders": [dict(row) for row in rows]}

    def mark_reminder_fired(self, reminder_id: int) -> dict:
        current = serialize_local(now_local(self.settings.local_timezone))
        with connect(self.settings) as db:
            cursor = db.execute(
                """
                UPDATE reminders
                SET status = 'fired', fired_at = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'scheduled'
                """,
                (current, int(reminder_id)),
            )
        return {"ok": cursor.rowcount > 0, "id": reminder_id}

    def _set_status(self, reminder_id: int, status: str) -> dict:
        with connect(self.settings) as db:
            cursor = db.execute(
                """
                UPDATE reminders
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, int(reminder_id)),
            )
        if cursor.rowcount == 0:
            return {"ok": False, "error": f"Reminder {reminder_id} was not found."}
        return {"ok": True, "id": reminder_id, "status": status}
