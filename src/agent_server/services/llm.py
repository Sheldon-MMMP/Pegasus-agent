from langchain_openai import ChatOpenAI

from agent_server.schemas import SettingsDTO
from agent_server.services.exceptions import ServiceError

def create_chat_model(settings:SettingsDTO) -> ChatOpenAI:
    provider = settings.chat_provider

    if not provider.api_key_configured:
        raise ServiceError(
            "chat_api_key_missing",
            "Chat provider API key is not configured.",
        )

    return ChatOpenAI(
        model=provider.model,
        base_url=provider.base_url,
        api_key="TODO",
        streaming=True,
    )