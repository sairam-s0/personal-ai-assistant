from app.config import Settings
from app.db.session import connect


class MemoryTool:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def save_memory(
        self,
        content: str,
        memory_type: str = "note",
        importance: int = 3,
    ) -> dict:
        content = content.strip()
        if not content:
            return {"ok": False, "error": "Memory content is required."}

        importance = max(1, min(5, int(importance)))
        with connect(self.settings) as db:
            cursor = db.execute(
                """
                INSERT INTO memories (content, memory_type, importance)
                VALUES (?, ?, ?)
                """,
                (content, memory_type.strip() or "note", importance),
            )
            return {"ok": True, "id": cursor.lastrowid, "content": content}

    def search_memory(self, query: str, limit: int = 5) -> dict:
        query = query.strip()
        limit = max(1, min(20, int(limit)))
        if not query:
            return self.list_memories(limit=limit)

        terms = [term.lower() for term in query.split() if len(term) > 2]
        with connect(self.settings) as db:
            rows = db.execute(
                """
                SELECT id, content, memory_type, importance, created_at
                FROM memories
                ORDER BY importance DESC, updated_at DESC
                LIMIT 100
                """
            ).fetchall()

        ranked = []
        for row in rows:
            content = row["content"].lower()
            score = sum(1 for term in terms if term in content)
            if score or query.lower() in content:
                ranked.append((score + row["importance"], row))

        ranked.sort(key=lambda item: item[0], reverse=True)
        memories = [dict(row) for _, row in ranked[:limit]]
        return {"ok": True, "memories": memories}

    def list_memories(self, limit: int = 10) -> dict:
        limit = max(1, min(50, int(limit)))
        with connect(self.settings) as db:
            rows = db.execute(
                """
                SELECT id, content, memory_type, importance, created_at
                FROM memories
                ORDER BY importance DESC, updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return {"ok": True, "memories": [dict(row) for row in rows]}
