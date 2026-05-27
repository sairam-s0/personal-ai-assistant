import pytest

from app.config import Settings
from app.llm.prompt_builder import PromptBuilder
from app.schemas.chat import Message


def test_prompt_builder_adds_system_history_and_user_message() -> None:
    settings = Settings(groq_api_key="test", groq_max_context_tokens=1000)
    builder = PromptBuilder(settings=settings)

    messages = builder.build_messages(
        user_message="What should I do next?",
        history=[Message(role="assistant", content="You were planning tasks.")],
    )

    assert messages[0]["role"] == "system"
    assert messages[1] == {
        "role": "assistant",
        "content": "You were planning tasks.",
    }
    assert messages[-1] == {"role": "user", "content": "What should I do next?"}


def test_prompt_builder_rejects_oversized_context() -> None:
    settings = Settings(groq_api_key="test", groq_max_context_tokens=1)
    builder = PromptBuilder(settings=settings)

    with pytest.raises(ValueError, match="Prompt is too large"):
        builder.build_messages(user_message="hello")
