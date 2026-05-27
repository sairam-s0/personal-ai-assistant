from app.config import Settings
from app.db.session import connect


class TaskTool:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_task(
        self,
        title: str,
        priority: int = 3,
        due_at: str | None = None,
        notes: str = "",
    ) -> dict:
        title = title.strip()
        if not title:
            return {"ok": False, "error": "Task title is required."}

        priority = max(1, min(5, int(priority)))
        with connect(self.settings) as db:
            cursor = db.execute(
                """
                INSERT INTO tasks (title, priority, due_at, notes)
                VALUES (?, ?, ?, ?)
                """,
                (title, priority, due_at, notes),
            )
            return {"ok": True, "id": cursor.lastrowid, "title": title}

    def list_tasks(self, status: str = "open", limit: int = 20) -> dict:
        limit = max(1, min(50, int(limit)))
        status = status.strip().lower()
        where = ""
        params: tuple = (limit,)
        if status != "all":
            where = "WHERE status = ?"
            params = (status, limit)

        with connect(self.settings) as db:
            rows = db.execute(
                f"""
                SELECT id, title, status, priority, due_at, notes, created_at
                FROM tasks
                {where}
                ORDER BY priority DESC, COALESCE(due_at, '9999') ASC, updated_at DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return {"ok": True, "tasks": [dict(row) for row in rows]}

    def update_task(
        self,
        task_id: int,
        status: str | None = None,
        title: str | None = None,
        priority: int | None = None,
        due_at: str | None = None,
        notes: str | None = None,
    ) -> dict:
        updates = []
        params = []
        if status is not None:
            updates.append("status = ?")
            params.append(status.strip().lower())
        if title is not None:
            updates.append("title = ?")
            params.append(title.strip())
        if priority is not None:
            updates.append("priority = ?")
            params.append(max(1, min(5, int(priority))))
        if due_at is not None:
            updates.append("due_at = ?")
            params.append(due_at)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)

        if not updates:
            return {"ok": False, "error": "No task updates provided."}

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(int(task_id))
        with connect(self.settings) as db:
            cursor = db.execute(
                f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?",
                tuple(params),
            )
            if cursor.rowcount == 0:
                return {"ok": False, "error": f"Task {task_id} was not found."}
        return {"ok": True, "id": task_id}
