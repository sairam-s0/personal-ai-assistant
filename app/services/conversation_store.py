from uuid import uuid4

from app.config import Settings
from app.db.session import connect
from app.schemas.chat import Message


class ConversationStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def ensure_conversation(self, session_id: str | None, first_message: str) -> str:
        if session_id:
            with connect(self.settings) as db:
                row = db.execute(
                    "SELECT id FROM conversations WHERE id = ?",
                    (session_id,),
                ).fetchone()
                if row:
                    return session_id

        new_id = str(uuid4())
        title = first_message.strip().replace("\n", " ")[:60] or "New chat"
        with connect(self.settings) as db:
            db.execute(
                "INSERT INTO conversations (id, title) VALUES (?, ?)",
                (new_id, title),
            )
        return new_id

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with connect(self.settings) as db:
            db.execute(
                """
                INSERT INTO conversation_messages (conversation_id, role, content)
                VALUES (?, ?, ?)
                """,
                (session_id, role, content),
            )
            db.execute(
                "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (session_id,),
            )

    def get_messages(self, session_id: str, limit: int = 30) -> list[Message]:
        with connect(self.settings) as db:
            rows = db.execute(
                """
                SELECT role, content
                FROM conversation_messages
                WHERE conversation_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        return [
            Message(role=row["role"], content=row["content"])
            for row in reversed(rows)
            if row["role"] in {"user", "assistant", "system"}
        ]

    def list_conversations(self, limit: int = 20) -> list[dict]:
        with connect(self.settings) as db:
            rows = db.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM conversations
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
