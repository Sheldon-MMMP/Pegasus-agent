from langchain_openai import ChatOpenAI

from agent_server.models import Message
from agent_server.schemas import Role
from agent_server.services.exceptions import ServiceError
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)


def create_chat_model(
    settings: dict,
    model: str | None = None,
) -> ChatOpenAI:
    provider = settings.get("chat_provider", {})

    api_key = provider.get("api_key", None)
    base_url = provider.get("base_url", None)
    default_model = provider.get("model", None)

    if not api_key:
        raise ServiceError(
            "chat_api_key_missing",
            "Chat provider API key is not configured.",
        )

    if not base_url or not (model or default_model):
        raise ServiceError(
            "chat_provider_invalid",
            "Chat provider configuration is incomplete.",
        )

    return ChatOpenAI(
        model=model or default_model,
        base_url=base_url,
        api_key=api_key,
        streaming=True,
    )

def to_langchain_message(message: Message) -> BaseMessage:
    if message.role == Role.user.value:
        return HumanMessage(content=message.content)

    if message.role == Role.assistant.value:
        return AIMessage(content=message.content)

    if message.role == Role.system.value:
        return SystemMessage(content=message.content)

    raise ServiceError(
        "unsupported_message_role",
        f"Unsupported message role: {message.role}",
    )
