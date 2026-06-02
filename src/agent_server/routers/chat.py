from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from agent_server.schemas import CreateRunRequest, CreateRunResponse
from agent_server.services.chat import create_run as create_run_service
from agent_server.services.chat import stream_run_events

router = APIRouter(prefix="/api/chat", tags=["chat"])

def to_sse(event) -> str:
    return f"data: {event.model_dump_json()}\n\n"

@router.post("/runs", response_model=CreateRunResponse)
def create_run(request: CreateRunRequest) -> CreateRunResponse:
    return create_run_service(request)

@router.get("/runs/{run_id}/stream")
def stream_run(run_id: UUID) -> StreamingResponse:
    async def event_generator():
        async for event in stream_run_events(run_id):
            yield to_sse(event)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
