from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from agent_server.db import get_db
from agent_server.models import Memory
from agent_server.schemas import CreateMemoryRequest, ListMemoriesResponse, MemoryDTO
from agent_server.services.memories import create_memory as create_memory_service
from agent_server.services.memories import list_memories as list_memories_service

router = APIRouter(prefix="/api/memories", tags=["memories"])

DbSession = Annotated[Session, Depends(get_db)]


def memory_to_dto(memory: Memory) -> MemoryDTO:
    return MemoryDTO(
        id=memory.id,
        kind=memory.kind,
        content=memory.content,
        source_run_id=memory.source_run_id,
        source_message_id=memory.source_message_id,
        created_at=memory.created_at,
        updated_at=memory.updated_at,
    )


@router.get("", response_model=ListMemoriesResponse)
def list_memories(db:DbSession) -> ListMemoriesResponse:
    memories = list_memories_service(db)

    return ListMemoriesResponse(
        memories = [memory_to_dto(memory) for memory in memories]
    )


@router.post("", response_model=MemoryDTO)
def create_memory(request: CreateMemoryRequest,db:DbSession) -> MemoryDTO:
    memory = create_memory_service(db, request)
    return memory_to_dto(memory)
