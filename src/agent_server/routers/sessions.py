from uuid import UUID

from fastapi import APIRouter

from agent_server.schemas import GetSessionResponse, ListSessionsResponse
from agent_server.services.sessions import get_session as get_session_service
from agent_server.services.sessions import list_sessions as list_sessions_service

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=ListSessionsResponse)
def list_sessions() -> ListSessionsResponse:
    return list_sessions_service()


@router.get("/{session_id}", response_model=GetSessionResponse)
def get_session(session_id: UUID) -> GetSessionResponse:
    return get_session_service(session_id)
