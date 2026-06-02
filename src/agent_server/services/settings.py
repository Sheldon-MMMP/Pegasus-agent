from agent_server.schemas import SettingsDTO, UpdateSettingsRequest
from agent_server.state import settings_state


def get_settings() -> SettingsDTO:
    return settings_state


def update_settings(request: UpdateSettingsRequest) -> SettingsDTO:
    if request.approval_mode is not None:
        settings_state.approval_mode = request.approval_mode

    if request.chat_provider is not None:
        if request.chat_provider.base_url is not None:
            settings_state.chat_provider.base_url = request.chat_provider.base_url

        if request.chat_provider.model is not None:
            settings_state.chat_provider.model = request.chat_provider.model

        if request.chat_provider.api_key is not None:
            settings_state.chat_provider.api_key_configured = True

    if request.embedding_provider is not None:
        if request.embedding_provider.base_url is not None:
            settings_state.embedding_provider.base_url = request.embedding_provider.base_url

        if request.embedding_provider.model is not None:
            settings_state.embedding_provider.model = request.embedding_provider.model

        if request.embedding_provider.api_key is not None:
            settings_state.embedding_provider.api_key_configured = True

    if request.milvus is not None:
        if request.milvus.uri is not None:
            settings_state.milvus.uri = request.milvus.uri

        if request.milvus.database is not None:
            settings_state.milvus.database = request.milvus.database

    if request.workspace is not None:
        if request.workspace.name is not None:
            settings_state.workspace.name = request.workspace.name

        if request.workspace.root_path is not None:
            settings_state.workspace.root_path = request.workspace.root_path

    return settings_state
