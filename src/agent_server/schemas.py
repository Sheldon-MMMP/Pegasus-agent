from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


SKILL_NAME_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"
SKILL_NAME_MAX_LENGTH = 80


class Role(StrEnum):
    user = "user"
    assistant = "assistant"
    system = "system"
    tool = "tool"


class RunStatus(StrEnum):
    queued = "queued"
    running = "running"
    waiting_approval = "waiting_approval"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"

class ApprovalMode(StrEnum):
    sensitive= "sensitive"
    auto = "auto"


class ErrorDTO(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class SessionDTO(BaseModel):
    id: UUID
    title: str
    workspace_id: UUID
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None = None

class ListSessionsResponse(BaseModel):
    sessions: list[SessionDTO]


class MessageDTO(BaseModel):
    id: UUID
    session_id: UUID
    run_id: UUID | None = None
    role: Role
    content: str
    metadata: dict[str, Any] | None = None
    created_at: datetime


class RunDTO(BaseModel):
    id: UUID
    session_id: UUID
    status: RunStatus
    approval_mode: ApprovalMode
    model: str
    error: ErrorDTO | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class GetSessionResponse(BaseModel):
    session: SessionDTO
    messages: list[MessageDTO]
    runs: list[RunDTO]

class CreateRunRequest(BaseModel):
    session_id: UUID | None = None
    workspace_id: UUID
    message: str
    approval_mode: ApprovalMode | None = None
    model: str | None = None


class CreateRunResponse(BaseModel):
    run_id: UUID
    session_id: UUID
    status: RunStatus
    stream_url: str


class RunStartedEvent(BaseModel):
    type: Literal["run_started"] = "run_started"
    run_id: UUID
    session_id: UUID
    created_at: datetime


class AssistantDeltaEvent(BaseModel):
    type: Literal["assistant_delta"] = "assistant_delta"
    run_id: UUID
    message_id: UUID
    delta: str


class MessageCompletedEvent(BaseModel):
    type: Literal["message_completed"] = "message_completed"
    run_id: UUID
    message: MessageDTO


class RunCompletedEvent(BaseModel):
    type: Literal["run_completed"] = "run_completed"
    run_id: UUID
    status: Literal["completed"] = "completed"
    completed_at: datetime


class RunFailedEvent(BaseModel):
    type: Literal["run_failed"] = "run_failed"
    run_id: UUID
    error: ErrorDTO



class ToolCallStatus(StrEnum):
    pending = "pending"
    waiting_approval = "waiting_approval"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    rejected = "rejected"

class ApprovalStatus(StrEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"

class ToolCallDTO(BaseModel):
    id: UUID
    run_id: UUID
    name: str
    status: ToolCallStatus
    input: dict[str, Any]
    output: dict[str, Any] | str | None = None
    error: ErrorDTO | None = None
    requires_approval: bool
    approval_id: UUID | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

class RequestedActionDTO(BaseModel):
    tool_name: str
    input: dict[str, Any]

class ApprovalDTO(BaseModel):
    id: UUID
    run_id: UUID
    tool_call_id: UUID
    status: ApprovalStatus
    reason: str
    requested_action: RequestedActionDTO
    created_at: datetime
    resolved_at: datetime | None = None

class ApprovalRequiredEvent(BaseModel):
    type: Literal["approval_required"] = "approval_required"
    run_id: UUID
    approval: ApprovalDTO
    tool_call: ToolCallDTO

class ToolCallCreatedEvent(BaseModel):
    type: Literal["tool_call_created"] = "tool_call_created"
    run_id: UUID
    tool_call: ToolCallDTO


class ToolCallUpdatedEvent(BaseModel):
    type: Literal["tool_call_updated"] = "tool_call_updated"
    run_id: UUID
    tool_call: ToolCallDTO


class ResolveApprovalRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    comment: str | None = None


class ResolveApprovalResponse(BaseModel):
    approval: ApprovalDTO
    tool_call: ToolCallDTO
    run: RunDTO

class MilvusStatus(StrEnum):
    unknown = "unknown"
    connected = "connected"
    error = "error"


class ChatProviderDTO(BaseModel):
    base_url: str
    api_key_configured: bool
    model: str


class ChatProvider(BaseModel):
    base_url: str
    api_key: str | None = None
    model: str


class EmbeddingProviderDTO(BaseModel):
    base_url: str
    api_key_configured: bool
    model: str

class EmbeddingProvider(BaseModel):
    base_url: str
    api_key: bool | None = None
    model: str
    model: str



class MilvusDTO(BaseModel):
    uri: str
    database: str | None = None
    status: MilvusStatus | None = None


class WorkspaceDTO(BaseModel):
    id: UUID
    name: str
    root_path: str


class SettingsDTO(BaseModel):
    approval_mode: ApprovalMode
    chat_provider: ChatProviderDTO
    embedding_provider: EmbeddingProviderDTO
    milvus: MilvusDTO
    workspace: WorkspaceDTO


class Settings(BaseModel):
    approval_mode: ApprovalMode
    chat_provider: ChatProvider
    embedding_provider: EmbeddingProvider
    milvus: MilvusDTO
    workspace: WorkspaceDTO

class UpdateProviderRequest(BaseModel):
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None


class UpdateMilvusRequest(BaseModel):
    uri: str | None = None
    database: str | None = None


class UpdateWorkspaceRequest(BaseModel):
    name: str | None = None
    root_path: str | None = None


class UpdateSettingsRequest(BaseModel):
    approval_mode: ApprovalMode | None = None
    chat_provider: UpdateProviderRequest | None = None
    embedding_provider: UpdateProviderRequest | None = None
    milvus: UpdateMilvusRequest | None = None
    workspace: UpdateWorkspaceRequest | None = None


class MemoryKind(StrEnum):
    #关于用户长期偏好的信息
    user_profile = "user_profile"
    #agent 自己总结出来的运行经验
    agent_memory = "agent_memory"
    #关于当前项目的事实
    project_fact = "project_fact"

class MemoryDTO(BaseModel):
    id: UUID
    kind: MemoryKind
    content: str
    source_run_id: UUID | None = None
    source_message_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

class CreateMemoryRequest(BaseModel):
    kind: MemoryKind
    content: str


class ListMemoriesResponse(BaseModel):
    memories: list[MemoryDTO]

class SkillStatus(StrEnum):
    active = "active" #数据库有记录，文件也存在，可以被 agent 使用。
    missing = "missing" #数据库有记录，但文件不存在。
    disabled = "disabled" #用户禁用，不参与 skill selection。
    error = "error" #文件存在，但解析失败或内容不合法。

class SkillDTO(BaseModel):
    id: UUID
    name: str
    description: str
    file_path: str
    content_hash: str
    status: SkillStatus
    version: int
    source_run_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    last_checked_at: datetime | None = None

class GetSkillResponse(BaseModel):
    skill: SkillDTO
    content: str | None = None

class CreateSkillRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=SKILL_NAME_MAX_LENGTH,
        pattern=SKILL_NAME_PATTERN,
    )
    description: str = Field(min_length=1)
    content: str

class UpdateSkillRequest(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=SKILL_NAME_MAX_LENGTH,
        pattern=SKILL_NAME_PATTERN,
    )
    description: str | None = Field(default=None, min_length=1)
    content: str | None = None
    status: Literal["active", "disabled"] | None = None

class ListSkillsResponse(BaseModel):
    skills: list[SkillDTO]
