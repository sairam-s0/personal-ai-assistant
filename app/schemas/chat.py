from typing import Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)
    history: list[Message] = Field(default_factory=list)
    session_id: str | None = None
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_completion_tokens: int | None = Field(default=None, ge=1, le=32_768)


class ChatResponse(BaseModel):
    message: str
    model: str
    session_id: str
    usage: dict[str, int] | None = None
    tool_results: list[dict] = Field(default_factory=list)
