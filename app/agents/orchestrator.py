import json

from app.config import Settings
from app.llm.groq_client import GroqClient
from app.llm.prompt_builder import PromptBuilder
from app.llm.response_parser import parse_chat_response
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.conversation_store import ConversationStore
from app.tools.memory_tool import MemoryTool
from app.tools.registry import ToolRegistry


class Orchestrator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.prompt_builder = PromptBuilder(settings=settings)
        self.conversations = ConversationStore(settings=settings)
        self.memory = MemoryTool(settings=settings)
        self.tools = ToolRegistry(settings=settings)

    async def chat(self, request: ChatRequest) -> ChatResponse:
        session_id = self.conversations.ensure_conversation(
            request.session_id,
            request.message,
        )
        stored_history = self.conversations.get_messages(session_id)
        history = request.history or stored_history
        memory_result = self.memory.search_memory(request.message, limit=6)
        memories = memory_result.get("memories", [])

        messages = self.prompt_builder.build_messages(
            user_message=request.message,
            history=history,
            memory_context=memories,
        )
        llm = GroqClient(settings=self.settings)
        completion = await llm.chat(
            messages=messages,
            max_completion_tokens=request.max_completion_tokens,
            temperature=request.temperature,
            tools=self.tools.schemas(),
        )

        tool_results: list[dict] = []
        for _ in range(5):
            choice_message = completion.choices[0].message
            tool_calls = getattr(choice_message, "tool_calls", None) or []
            if not tool_calls:
                break

            messages.append(choice_message.model_dump(exclude_none=True))
            for tool_call in tool_calls:
                result = self.tools.execute(
                    tool_call.function.name,
                    tool_call.function.arguments,
                )
                tool_results.append(
                    {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                        "result": result,
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": json.dumps(result),
                    }
                )

            completion = await llm.chat(
                messages=messages,
                max_completion_tokens=request.max_completion_tokens,
                temperature=request.temperature,
                tools=self.tools.schemas(),
            )

        parsed = parse_chat_response(completion)
        self.conversations.add_message(session_id, "user", request.message)
        self.conversations.add_message(session_id, "assistant", parsed.content)
        return ChatResponse(
            message=parsed.content,
            model=parsed.model,
            usage=parsed.usage,
            session_id=session_id,
            tool_results=tool_results,
        )
