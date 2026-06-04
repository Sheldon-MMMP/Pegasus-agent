from uuid import UUID

from fastapi import APIRouter

from agent_server.deps import DbSession
from agent_server.routers.errors import raise_http_error_from_service_error
from agent_server.schemas import GetSessionResponse, ListSessionsResponse
from agent_server.services.exceptions import ServiceError
from agent_server.services.sessions import get_session as get_session_service
from agent_server.services.sessions import list_sessions as list_sessions_service

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=ListSessionsResponse)
def list_sessions(db:DbSession) -> ListSessionsResponse:
    return list_sessions_service(db)


@router.get("/{session_id}", response_model=GetSessionResponse)
def get_session(session_id: UUID, db: DbSession) -> GetSessionResponse:
    try:
        return get_session_service(session_id, db)
    except ServiceError as error:
        raise_http_error_from_service_error(
            error,
            {"session_not_found": 404},
        )
