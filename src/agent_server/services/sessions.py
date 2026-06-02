from datetime import UTC, datetime
from uuid import UUID, uuid4

from agent_server.schemas import (
    ApprovalMode,
    GetSessionResponse,
    ListSessionsResponse,
    MessageDTO,
    Role,
    RunDTO,
    RunStatus,
    SessionDTO,
)


def list_sessions() -> ListSessionsResponse:
    now = datetime.now(UTC)
    workspace_id = uuid4()

    return ListSessionsResponse(
        sessions=[
            SessionDTO(
                id=uuid4(),
                title="First agent session",
                workspace_id=workspace_id,
                created_at=now,
                updated_at=now,
                last_message_at=None,
            )
        ]
    )


def get_session(session_id: UUID) -> GetSessionResponse:
    now = datetime.now(UTC)
    workspace_id = uuid4()
    run_id = uuid4()

    session = SessionDTO(
        id=session_id,
        title="First agent session",
        workspace_id=workspace_id,
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )

    user_message = MessageDTO(
        id=uuid4(),
        session_id=session_id,
        run_id=None,
        role=Role.user,
        content="Hello agent",
        metadata=None,
        created_at=now,
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

    assistant_message = MessageDTO(
        id=uuid4(),
        session_id=session_id,
        run_id=run_id,
        role=Role.assistant,
        content="Hello! I am ready.",
        metadata={"model": "gpt-4.1-mini"},
        created_at=now,
    )

    return GetSessionResponse(
        session=session,
        messages=[user_message, assistant_message],
        runs=[run],
    )
