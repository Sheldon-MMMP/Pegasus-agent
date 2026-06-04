from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from agent_server.deps import DbSession
from agent_server.routers.errors import raise_http_error_from_service_error
from agent_server.schemas import CreateRunRequest, CreateRunResponse
from agent_server.services.chat import create_run as create_run_service
from agent_server.services.chat import stream_run_events
from agent_server.services.exceptions import ServiceError

router = APIRouter(prefix="/api/chat", tags=["chat"])

def to_sse(event) -> str:
    return f"data: {event.model_dump_json()}\n\n"

@router.post("/runs", response_model=CreateRunResponse)
def create_run(request: CreateRunRequest, db: DbSession) -> CreateRunResponse:
    try:
        return create_run_service(request, db)
    except ServiceError as error:
        raise_http_error_from_service_error(
            error,
            {
                "session_not_found": 404,
                "workspace_not_found": 404,
                "workspace_mismatch": 409,
            },
        )

@router.get("/runs/{run_id}/stream")
def stream_run(run_id: UUID,db:DbSession) -> StreamingResponse:
    async def event_generator():
        async for event in stream_run_events(run_id,db):
            yield to_sse(event)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
