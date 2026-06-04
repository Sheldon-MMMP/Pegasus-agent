import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from agent_server.models import Session, Run, Message, Workspace
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
    ToolCallUpdatedEvent, RunDTO, RunFailedEvent, ErrorDTO,
)
from agent_server.services.exceptions import ServiceError
from agent_server.services.settings import get_settings


def create_run(request: CreateRunRequest,db: DbSession) -> CreateRunResponse:
    now = datetime.now(UTC)
    settings = get_settings(db)
    session_id = request.session_id if request.session_id else uuid4()
    if request.session_id:
        session = db.get(Session, request.session_id)
        if not session: raise ServiceError("session_not_found", "Session not found.")
        if session.workspace_id != request.workspace_id:
            raise ServiceError(
        "workspace_mismatch",
     "Session workspace does not match request workspace.",
            )

    else :
        workspace = db.get(Workspace, request.workspace_id)
        if not workspace:
            raise ServiceError("workspace_not_found", "Workspace not found.")
        session = Session(
            id = session_id,
            title=request.message[:80],
            workspace_id=request.workspace_id,
            last_message_at=now,
        )

        db.add(session)

    session.last_message_at = now


    run = Run(
        id = uuid4(),
        session_id = session_id,
        status = RunStatus.queued.value,
        approval_mode= request.approval_mode or settings.approval_mode,
        model = request.model or settings.chat_provider.model,
        error=None,
        created_at = datetime.now(UTC),
        started_at = None,
    )

    message = Message(
        id=uuid4(),
        session_id=session_id,
        run_id=run.id,
        role=Role.user.value,
        content=request.message,
        message_metadata=None,
    )
    db.add(message)

    db.add(run)
    db.commit()
    db.refresh(session)
    db.refresh(run)

    return CreateRunResponse(
        run_id= run.id,
        session_id=run.session_id,
        status= run.status,
        stream_url=f"/api/chat/runs/{run.id}/stream",
    )



async def stream_run_events(run_id: UUID,db: DbSession) -> AsyncIterator[BaseModel]:
    run = db.get(Run, run_id)
    if not run:
        yield RunFailedEvent(
            run_id=run_id,
            error=ErrorDTO(
                code="run_not_found",
                message="Run not found.",
            ),
        )
        return

    run.status = RunStatus.running.value
    run.started_at = datetime.now(UTC)
    db.add(run)
    db.commit()


    session_id = run.session_id
    message_id = uuid4()
    yield RunStartedEvent(
        run_id=run_id,
        session_id=session_id,
        created_at=datetime.now(UTC),
    )

    completed_at = datetime.now(UTC)

    run.status = RunStatus.completed.value
    run.completed_at = completed_at
    db.commit()

    yield RunCompletedEvent(
        run_id=run_id,
        completed_at=completed_at,
    )
