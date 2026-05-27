from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParsedResponse:
    content: str
    model: str
    usage: dict[str, int] | None


def parse_chat_response(completion: Any) -> ParsedResponse:
    choice = completion.choices[0]
    message = choice.message
    content = message.content or ""

    usage = None
    if getattr(completion, "usage", None):
        usage = {
            "prompt_tokens": completion.usage.prompt_tokens,
            "completion_tokens": completion.usage.completion_tokens,
            "total_tokens": completion.usage.total_tokens,
        }

    return ParsedResponse(
        content=content.strip(),
        model=getattr(completion, "model", ""),
        usage=usage,
    )
