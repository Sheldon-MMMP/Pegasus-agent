from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter

from agent_server.schemas import CreateMemoryRequest, ListMemoriesResponse, MemoryDTO
from agent_server.state import memories_state

router = APIRouter(prefix="/api/memories", tags=["memories"])


@router.get("", response_model=ListMemoriesResponse)
def list_memories() -> ListMemoriesResponse:
    return ListMemoriesResponse(memories=memories_state)


@router.post("", response_model=MemoryDTO)
def create_memory(request: CreateMemoryRequest) -> MemoryDTO:
    now = datetime.now(UTC)

    memory = MemoryDTO(
        id=uuid4(),
        kind=request.kind,
        content=request.content,
        source_run_id=None,
        source_message_id=None,
        created_at=now,
        updated_at=now,
    )

    memories_state.append(memory)

    return memory
