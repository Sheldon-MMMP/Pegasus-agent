from copy import deepcopy

from sqlalchemy import select

from agent_server.models import Session, Setting, Workspace
from agent_server.schemas import SettingsDTO, UpdateSettingsRequest, ApprovalMode, ChatProviderDTO, MilvusDTO, \
    EmbeddingProviderDTO, MilvusStatus, WorkspaceDTO, Settings, ChatProvider, EmbeddingProvider

APP_SETTINGS_KEY = "app"

def ensure_default_workspace(db: Session) -> Workspace:
    workspace = db.scalar(select(Workspace).limit(1))

    if workspace is not None:
        return workspace

    workspace = Workspace(
        name="Default Workspace",
        root_path=".",
    )

    db.add(workspace)
    db.flush()

    return workspace

def default_settings(workspace: Workspace) -> Settings:
    return Settings(
        approval_mode=ApprovalMode.sensitive,
        chat_provider=ChatProvider(
            base_url="https://api.openai.com/v1",
            api_key=None,
            model="gpt-4.1-mini",
        ),
        embedding_provider=EmbeddingProvider(
            base_url="https://api.openai.com/v1",
            api_key=None,
            model="text-embedding-3-small",
        ),
        milvus=MilvusDTO(
            uri="http://localhost:19530",
            database="default",
            status=MilvusStatus.unknown,
        ),
        workspace=WorkspaceDTO(
            id=workspace.id,
            name=workspace.name,
            root_path=workspace.root_path,
        ),
    )

def settings_to_dict(settings: SettingsDTO) -> dict:
    data = settings.model_dump(mode="json")
    workspace = data.pop("workspace")
    data["default_workspace_id"] = workspace["id"]
    return data

def settings_to_DTO(settings: Settings) -> SettingsDTO:
    return SettingsDTO(
        approval_mode=settings.approval_mode,
        chat_provider=ChatProviderDTO(
            base_url=settings.chat_provider.base_url,
            api_key_configured=bool(settings.chat_provider.api_key),
            model=settings.chat_provider.model,
        ),
        embedding_provider=EmbeddingProviderDTO(
            base_url=settings.embedding_provider.base_url,
            api_key_configured=bool(settings.embedding_provider.api_key),
            model=settings.embedding_provider.model,
        ),
        milvus=settings.milvus,
        workspace=settings.workspace,
    )

def settings_from_dict(value: dict, workspace: Workspace) -> SettingsDTO:
    data = deepcopy(value)
    for provider_name in ("chat_provider", "embedding_provider"):
        provider = data.setdefault(provider_name, {})
        provider["api_key_configured"] = bool(provider.pop("api_key", None))

    data["workspace"] = {
        "id": str(workspace.id),
        "name": workspace.name,
        "root_path": workspace.root_path,
    }
    data.pop("default_workspace_id", None)

    return SettingsDTO.model_validate(data)



def get_settings(db: Session) -> SettingsDTO:
    setting = db.get(Setting,APP_SETTINGS_KEY)

    if setting is None:
        workspace = ensure_default_workspace(db)
        default_value = default_settings(workspace)
        setting = Setting(
            key=APP_SETTINGS_KEY,
            value=settings_to_dict(default_value),
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)

        return settings_to_DTO(default_value)



    workspace_id = setting.value.get("default_workspace_id")
    workspace = db.get(Workspace, workspace_id) if workspace_id else None
    if workspace is None:
        workspace = ensure_default_workspace(db)
        setting.value = {
            **setting.value,
            "default_workspace_id": str(workspace.id),
        }
        db.commit()
        db.refresh(setting)

    return settings_from_dict(setting.value, workspace)

def get_raw_settings(db: Session) -> dict:
    setting = db.get(Setting, APP_SETTINGS_KEY)

    if setting is None:
        get_settings(db)
        setting = db.get(Setting, APP_SETTINGS_KEY)

    return deepcopy(setting.value)

def apply_non_workspace_settings_update(
        settings: SettingsDTO,
        request: UpdateSettingsRequest,
) -> SettingsDTO:
    # exclude_unset=True：只提取用户实际传了的字段
    # exclude_none=True：如果用户显式传了 None，也过滤掉（取决于你的业务是否允许传 None 注销配置）
    update_data = request.model_dump(exclude_unset=True, exclude_none=True)

    # 1. 先处理非嵌套的顶级字段（如 approval_mode）
    if "approval_mode" in update_data:
        settings.approval_mode = update_data["approval_mode"]

    # 2. 动态遍历嵌套模块
    for provider_name in ["chat_provider", "embedding_provider", "milvus"]:
        provider_data = update_data.get(provider_name)
        # 容错：Request 里没传这个模块，或者 SettingsDTO 里根本没这个模块，直接跳过
        if not provider_data or not hasattr(settings, provider_name):
            continue

        target_obj = getattr(settings, provider_name)

        # 3. 遍历子字段更新
        for key, value in provider_data.items():
            if key == "api_key":
                # 容错：确保 DTO 上有这个特殊配置字段才赋值
                if hasattr(target_obj, "api_key_configured"):
                    target_obj.api_key_configured = True
            else:
                # 容错：只有当 SettingsDTO 的子对象确实有这个字段时，才做赋值
                if hasattr(target_obj, key):
                    setattr(target_obj, key, value)

    return settings

def apply_workspace_update(
    workspace: Workspace,
    request: UpdateSettingsRequest,
) -> None:
    if request.workspace is None:
        return

    if request.workspace.name is not None:
        workspace.name = request.workspace.name

    if request.workspace.root_path is not None:
        workspace.root_path = request.workspace.root_path

def update_settings(request: UpdateSettingsRequest,db:Session) -> SettingsDTO:
    current_settings = get_settings(db)

    setting = db.get(Setting, APP_SETTINGS_KEY)
    workspace = db.get(Workspace, current_settings.workspace.id)
    if workspace is None:
        workspace = ensure_default_workspace(db)
        setting.value = {
            **setting.value,
            "default_workspace_id": str(workspace.id),
        }

    updated_settings = apply_non_workspace_settings_update(current_settings,request)
    apply_workspace_update(workspace, request)
    setting = db.get(Setting,APP_SETTINGS_KEY)

    if setting is None:
        setting = Setting(
            key=APP_SETTINGS_KEY,
            value=settings_to_dict(updated_settings),
        )
        db.add(setting)
    else:
        new_value = settings_to_dict(updated_settings)
        old_api_key = setting.value.get("chat_provider", {}).get("api_key")

        if request.chat_provider and request.chat_provider.api_key is not None:
            new_value["chat_provider"]["api_key"] = request.chat_provider.api_key
        elif old_api_key is not None:
            new_value["chat_provider"]["api_key"] = old_api_key

        setting.value = new_value

    db.commit()
    db.refresh(setting)

    return settings_from_dict(setting.value, workspace)
