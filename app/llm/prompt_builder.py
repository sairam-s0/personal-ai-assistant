from app.config import Settings
from app.llm.token_counter import count_message_tokens
from app.schemas.chat import Message


SYSTEM_PROMPT = """You are a practical personal AI assistant.

Current capabilities:
- Answer the user's message using Groq.
- Use tools when useful for durable local memory and local tasks.
- Use local time and reminder tools for scheduling reminder requests.
- Use Google Calendar tools for calendar queries, events, deletion, updates, quick-add, and free/busy when configured.
- Only say a Google Calendar write succeeded when the tool result has ok=true.
- For Google Calendar event creation, mention whether verified_on_google is true and whether reminders are present.
- If the user asks for a reminder/alert/notification in Google Calendar, include reminders_minutes.
- Save memory only for stable facts, preferences, goals, constraints, or explicit user requests.
- Search memory before answering when prior context may matter.
- Call get_current_time before interpreting relative dates or times.
- Be concise and action-oriented.

Limitations:
- Google Calendar requires local OAuth setup before calendar tools can access the account.
- Files and RAG are not available yet.
"""


class PromptBuilder:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_messages(
        self,
        user_message: str,
        history: list[Message] | None = None,
        memory_context: list[dict] | None = None,
    ) -> list[dict]:
        messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

        if memory_context:
            memory_lines = [
                f"- [{item['memory_type']}; importance {item['importance']}] {item['content']}"
                for item in memory_context
            ]
            messages.append(
                {
                    "role": "system",
                    "content": "Relevant local memories from this PC:\n"
                    + "\n".join(memory_lines),
                }
            )

        for item in history or []:
            messages.append({"role": item.role, "content": item.content})

        messages.append({"role": "user", "content": user_message})
        token_count = count_message_tokens(messages)

        if token_count > self.settings.groq_max_context_tokens:
            raise ValueError(
                "Prompt is too large for the configured Groq context window. "
                "Shorten the conversation history and try again."
            )

        return messages
