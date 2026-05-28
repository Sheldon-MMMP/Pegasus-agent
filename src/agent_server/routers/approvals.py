from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter

from agent_server.schemas import (
    ApprovalDTO,
    ApprovalMode,
    ApprovalStatus,
    RequestedActionDTO,
    ResolveApprovalRequest,
    ResolveApprovalResponse,
    RunDTO,
    RunStatus,
    ToolCallDTO,
    ToolCallStatus,
)

router = APIRouter(prefix="/api/tool-approvals", tags=["approvals"])


@router.post("/{approval_id}", response_model=ResolveApprovalResponse)
def resolve_approval(
    approval_id: UUID,
    request: ResolveApprovalRequest,
) -> ResolveApprovalResponse:
    now = datetime.now(UTC)
    run_id = uuid4()
    tool_call_id = uuid4()
    session_id = uuid4()

    approval_status = (
        ApprovalStatus.approved
        if request.decision == "approved"
        else ApprovalStatus.rejected
    )

    tool_call_status = (
        ToolCallStatus.succeeded
        if request.decision == "approved"
        else ToolCallStatus.rejected
    )

    approval = ApprovalDTO(
        id=approval_id,
        run_id=run_id,
        tool_call_id=tool_call_id,
        status=approval_status,
        reason="file_write 会修改 workspace 内的文件，需要用户确认。",
        requested_action=RequestedActionDTO(
            tool_name="file_write",
            input={
                "path": "README.md",
                "content": "Add a short project summary.",
            },
        ),
        created_at=now,
        resolved_at=now,
    )

    tool_call = ToolCallDTO(
        id=tool_call_id,
        run_id=run_id,
        name="file_write",
        status=tool_call_status,
        input=approval.requested_action.input,
        output=(
            {"path": "README.md", "bytes_written": 28}
            if request.decision == "approved"
            else None
        ),
        error=None,
        requires_approval=True,
        approval_id=approval_id,
        created_at=now,
        started_at=now if request.decision == "approved" else None,
        completed_at=now,
    )

    run = RunDTO(
        id=run_id,
        session_id=session_id,
        status=RunStatus.completed,
        approval_mode=ApprovalMode.sensitive,
        model="gpt-4.1-mini",
        error=None,
        created_at=now,
        started_at=now,
        completed_at=now,
    )

    return ResolveApprovalResponse(
        approval=approval,
        tool_call=tool_call,
        run=run,
    )
