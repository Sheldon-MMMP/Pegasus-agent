import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel

from agent_server.schemas import (
    ApprovalDTO,
    ApprovalRequiredEvent,
    ApprovalStatus,
    AssistantDeltaEvent,
    CreateRunRequest,
    CreateRunResponse,
    MessageCompletedEvent,
    MessageDTO,
    RequestedActionDTO,
    Role,
    RunCompletedEvent,
    RunStartedEvent,
    RunStatus,
    ToolCallCreatedEvent,
    ToolCallDTO,
    ToolCallStatus,
    ToolCallUpdatedEvent,
)


def create_run(request: CreateRunRequest) -> CreateRunResponse:
    session_id = request.session_id or uuid4()
    run_id = uuid4()

    return CreateRunResponse(
        run_id=run_id,
        session_id=session_id,
        status=RunStatus.queued,
        stream_url=f"/api/chat/runs/{run_id}/stream",
    )


async def stream_run_events(run_id: UUID) -> AsyncIterator[BaseModel]:
    now = datetime.now(UTC)
    session_id = uuid4()
    message_id = uuid4()

    yield RunStartedEvent(
        run_id=run_id,
        session_id=session_id,
        created_at=now,
    )

    tool_call_id = uuid4()

    tool_call = ToolCallDTO(
        id=tool_call_id,
        run_id=run_id,
        name="memory_search",
        status=ToolCallStatus.running,
        input={"query": "用户最近在做什么 agent 项目？"},
        output=None,
        error=None,
        requires_approval=False,
        approval_id=None,
        created_at=datetime.now(UTC),
        started_at=datetime.now(UTC),
        completed_at=None,
    )

    yield ToolCallCreatedEvent(
        run_id=run_id,
        tool_call=tool_call,
    )

    await asyncio.sleep(0.4)

    tool_call.status = ToolCallStatus.succeeded
    tool_call.output = {
        "matches": [
            {
                "content": "用户正在实现一个 Hermes-like agent。",
                "score": 0.91,
            }
        ]
    }
    tool_call.completed_at = datetime.now(UTC)

    yield ToolCallUpdatedEvent(
        run_id=run_id,
        tool_call=tool_call,
    )

    approval_id = uuid4()
    file_tool_call_id = uuid4()

    file_tool_call = ToolCallDTO(
        id=file_tool_call_id,
        run_id=run_id,
        name="file_write",
        status=ToolCallStatus.waiting_approval,
        input={
            "path": "README.md",
            "content": "Add a short project summary.",
        },
        output=None,
        error=None,
        requires_approval=True,
        approval_id=approval_id,
        created_at=datetime.now(UTC),
        started_at=None,
        completed_at=None,
    )

    approval = ApprovalDTO(
        id=approval_id,
        run_id=run_id,
        tool_call_id=file_tool_call_id,
        status=ApprovalStatus.pending,
        reason="file_write 会修改 workspace 内的文件，需要用户确认。",
        requested_action=RequestedActionDTO(
            tool_name="file_write",
            input=file_tool_call.input,
        ),
        created_at=datetime.now(UTC),
        resolved_at=None,
    )

    yield ApprovalRequiredEvent(
        run_id=run_id,
        approval=approval,
        tool_call=file_tool_call,
    )

    for delta in ["你好", "，", "我是", " agent", "。"]:
        await asyncio.sleep(0.3)
        yield AssistantDeltaEvent(
            run_id=run_id,
            message_id=message_id,
            delta=delta,
        )

    message = MessageDTO(
        id=message_id,
        session_id=session_id,
        run_id=run_id,
        role=Role.assistant,
        content="你好，我是 agent。",
        metadata={"streamed": True},
        created_at=datetime.now(UTC),
    )

    yield MessageCompletedEvent(
        run_id=run_id,
        message=message,
    )

    yield RunCompletedEvent(
        run_id=run_id,
        completed_at=datetime.now(UTC),
    )
