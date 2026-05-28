from uuid import uuid4

from agent_server.schemas import (
    ApprovalMode,
    ChatProviderDTO,
    EmbeddingProviderDTO,
    MemoryDTO,
    MilvusDTO,
    MilvusStatus,
    SettingsDTO,
    SkillDTO,
    WorkspaceDTO,
)

settings_state = SettingsDTO(
    approval_mode=ApprovalMode.sensitive,
    chat_provider=ChatProviderDTO(
        base_url="https://api.openai.com/v1",
        api_key_configured=False,
        model="gpt-4.1-mini",
    ),
    embedding_provider=EmbeddingProviderDTO(
        base_url="https://api.openai.com/v1",
        api_key_configured=False,
        model="text-embedding-3-small",
    ),
    milvus=MilvusDTO(
        uri="http://localhost:19530",
        database="default",
        status=MilvusStatus.unknown,
    ),
    workspace=WorkspaceDTO(
        id=uuid4(),
        name="Default Workspace",
        root_path=".",
    ),
)

memories_state: list[MemoryDTO] = []
skills_state: list[SkillDTO] = []
