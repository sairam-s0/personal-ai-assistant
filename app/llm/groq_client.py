from typing import Any

from groq import APIConnectionError, APIStatusError, AsyncGroq, RateLimitError

from app.config import Settings


class GroqClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required. Add it to your .env file.")
        self.settings = settings
        self.client = AsyncGroq(api_key=settings.groq_api_key)

    async def chat(
        self,
        messages: list[dict],
        max_completion_tokens: int | None = None,
        temperature: float = 0.2,
        tools: list[dict] | None = None,
        tool_choice: str | None = "auto",
    ) -> Any:
        try:
            kwargs = {}
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = tool_choice

            return await self.client.chat.completions.create(
                model=self.settings.groq_model,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=(
                    max_completion_tokens
                    or self.settings.groq_default_max_completion_tokens
                ),
                **kwargs,
            )
        except RateLimitError as exc:
            raise RuntimeError("Groq rate limit reached. Try again shortly.") from exc
        except APIConnectionError as exc:
            raise RuntimeError("Could not connect to Groq API.") from exc
        except APIStatusError as exc:
            raise RuntimeError(f"Groq API error: {exc.status_code}") from exc
