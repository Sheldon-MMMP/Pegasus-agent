from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select

from agent_server.deps import DbSession
from agent_server.models import Session, Message, Run
from agent_server.schemas import (
    ApprovalMode,
    ErrorDTO,
    GetSessionResponse,
    ListSessionsResponse,
    MessageDTO,
    Role,
    RunDTO,
    RunStatus,
    SessionDTO,
)
from agent_server.services.exceptions import ServiceError


def session_to_dto(session: Session) -> SessionDTO:
    return SessionDTO(
        id=session.id,
        title=session.title,
        workspace_id=session.workspace_id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        last_message_at=session.last_message_at,
    )

def message_to_dto(message: Message) -> MessageDTO:
    return MessageDTO(
        id=message.id,
        session_id=message.session_id,
        run_id=message.run_id,
        role=Role(message.role),
        content=message.content,
        metadata=message.message_metadata,
        created_at=message.created_at,
    )

def run_to_dto(run: Run) -> RunDTO:
    return RunDTO(
        id=run.id,
        session_id=run.session_id,
        status=RunStatus(run.status),
        approval_mode=ApprovalMode(run.approval_mode),
        model=run.model,
        error=ErrorDTO.model_validate(run.error) if run.error is not None else None,
        created_at=run.created_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
    )

def list_sessions(db: DbSession) -> ListSessionsResponse:
    sessions = db.execute(
        select(Session)
        .order_by(Session.updated_at.desc())
    ).scalars().all()
    return ListSessionsResponse(
        sessions=[session_to_dto(session) for session in sessions]
    )


def get_session(session_id: UUID,db: DbSession) -> GetSessionResponse:
    session = db.get(Session, session_id)
    if session is None:
        raise ServiceError("session_not_found", "Session not found.")

    messages = db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    ).scalars().all()

    runs = db.execute(
        select(Run)
        .where(Run.session_id == session_id)
        .order_by(Run.created_at)
    ).scalars().all()

    return GetSessionResponse(
        session=session_to_dto(session),
        messages=[message_to_dto(message) for message in messages],
        runs=[run_to_dto(run) for run in runs],
    )
