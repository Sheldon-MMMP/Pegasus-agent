from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import update
from sqlalchemy.orm import Session as DbSession

from agent_server.db import SessionLocal
from agent_server.models import Session, Run, Message, Workspace
from agent_server.schemas import (AssistantDeltaEvent, CreateRunRequest, CreateRunResponse, MessageCompletedEvent,
                                  MessageDTO, Role, RunCompletedEvent, RunStartedEvent, RunStatus, RunFailedEvent,
                                  ErrorDTO, )
from agent_server.services.exceptions import ServiceError
from agent_server.services.llm import create_chat_model
from agent_server.services.memories import load_chat_history
from agent_server.services.run_broker import run_event_broker
from agent_server.services.settings import get_raw_settings
from agent_server.services.settings import get_settings


def create_run(request: CreateRunRequest, db: DbSession) -> CreateRunResponse:
    now = datetime.now(UTC)
    settings = get_settings(db)
    session_id = request.session_id if request.session_id else uuid4()
    if request.session_id:
        session = db.get(Session, request.session_id)
        if not session: raise ServiceError("session_not_found", "Session not found.")
        if session.workspace_id != request.workspace_id:
            raise ServiceError("workspace_mismatch", "Session workspace does not match request workspace.", )

    else:
        workspace = db.get(Workspace, request.workspace_id)
        if not workspace:
            raise ServiceError("workspace_not_found", "Workspace not found.")
        session = Session(id=session_id, title=request.message[:80], workspace_id=request.workspace_id,
            last_message_at=now, )

        db.add(session)

    session.last_message_at = now

    run = Run(id=uuid4(), session_id=session_id, status=RunStatus.queued.value,
        approval_mode=request.approval_mode or settings.approval_mode,
        model=request.model or settings.chat_provider.model, error=None, created_at=datetime.now(UTC),
        started_at=None, )

    message = Message(id=uuid4(), session_id=session_id, run_id=run.id, role=Role.user.value, content=request.message,
        message_metadata=None, )
    db.add(message)

    db.add(run)
    db.commit()
    db.refresh(session)
    db.refresh(run)

    return CreateRunResponse(run_id=run.id, session_id=run.session_id, status=run.status,
        stream_url=f"/api/chat/runs/{run.id}/stream", )


async def execute_run(run_id: UUID) -> None:
    with SessionLocal() as db:
        try:
            await execute_run_with_db(run_id, db)
        except Exception as exc:
            db.rollback()

            error = ErrorDTO(
                code="run_execution_failed",
                message="Run execution failed.",
                details={"reason": str(exc)},
            )

            run = db.get(Run, run_id)
            if run is not None:
                run.status = RunStatus.failed.value
                run.error = error.model_dump(mode="json")
                run.completed_at = datetime.now(UTC)
                db.commit()

            await run_event_broker.publish(
                run_id,
                RunFailedEvent(run_id=run_id, error=error),
                terminal=True,
            )


async def execute_run_with_db(run_id: UUID, db: DbSession) -> None:
    run = db.get(Run, run_id)
    if not run:
        await run_event_broker.publish(
            run_id,
            RunFailedEvent(
                run_id=run_id,
                error=ErrorDTO(code="run_not_found", message="Run not found."),
            ),
            terminal=True,
        )
        return

    started_at = datetime.now(UTC)
    result = db.execute(update(Run).where(Run.id == run_id, Run.status == RunStatus.queued.value, ).values(
        status=RunStatus.running.value, started_at=started_at, ))
    db.commit()

    # 检查真正修改了多少行
    if result.rowcount == 0:
        db.refresh(run)
        error = ErrorDTO(
            code="run_already_started",
            message=f"Run cannot start from status '{run.status}'.",
        )

        await run_event_broker.publish(
            run_id,
            RunFailedEvent(run_id=run_id, error=error),
            terminal=True,
        )
        return

    db.refresh(run)
    session_id = run.session_id

    # 发送消息告诉前端run开始执行了
    await run_event_broker.publish(
        run_id,
        RunStartedEvent(
            run_id=run_id,
            session_id=session_id,
            created_at=started_at,
        ),
    )

    # 大模型执行的地方
    raw_settings = get_raw_settings(db)
    model = create_chat_model(raw_settings, model=run.model)
    history = load_chat_history(db, session_id)

    full_content = ""
    message_id = uuid4()
    async for chunk in model.astream(history):
        delta = chunk.content
        if not isinstance(delta, str) or not delta:
            continue

        full_content += delta
        await run_event_broker.publish(
            run_id,
            AssistantDeltaEvent(
                run_id=run_id,
                message_id=message_id,
                delta=delta,
            ),
        )

    assistant_message = Message(
        id=message_id,
        session_id=session_id,
        run_id=run_id,
        role=Role.assistant.value,
        content=full_content,
        message_metadata=None,
    )

    db.add(assistant_message)
    run.session.last_message_at = datetime.now(UTC)
    db.commit()
    db.refresh(assistant_message)

    await run_event_broker.publish(
        run_id,
        MessageCompletedEvent(
            run_id=run_id,
            message=MessageDTO(
                id=assistant_message.id,
                session_id=assistant_message.session_id,
                run_id=assistant_message.run_id,
                role=Role.assistant,
                content=assistant_message.content,
                metadata=assistant_message.message_metadata,
                created_at=assistant_message.created_at,
            ),
        ),
    )

    completed_at = datetime.now(UTC)
    run.status = RunStatus.completed.value
    run.completed_at = completed_at
    db.commit()

    await run_event_broker.publish(
        run_id,
        RunCompletedEvent(run_id=run_id, completed_at=completed_at),
        terminal=True,
    )
