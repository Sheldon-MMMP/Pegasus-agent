from uuid import UUID

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import StreamingResponse

from agent_server.deps import DbSession
from agent_server.routers.errors import raise_http_error_from_service_error
from agent_server.schemas import CreateRunRequest, CreateRunResponse
from agent_server.services.chat import create_run as create_run_service
from agent_server.services.chat import execute_run
from agent_server.services.exceptions import ServiceError
from agent_server.services.run_broker import run_event_broker

router = APIRouter(prefix="/api/chat", tags=["chat"])

def to_sse(event) -> str:
    return f"data: {event.model_dump_json()}\n\n"

@router.post("/runs", response_model=CreateRunResponse)
def create_run(
    request: CreateRunRequest,
    background_tasks: BackgroundTasks,
    db: DbSession,
) -> CreateRunResponse:
    try:
        response = create_run_service(request, db)
        background_tasks.add_task(execute_run, response.run_id)
        return response
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
def stream_run(run_id: UUID) -> StreamingResponse:
    async def event_generator():
        async for event in run_event_broker.subscribe(run_id):
            yield to_sse(event)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
