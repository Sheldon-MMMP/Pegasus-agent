from sqlalchemy import select
from sqlalchemy.orm import Session

from agent_server.models import Memory
from agent_server.schemas import CreateMemoryRequest


def list_memories(db: Session) -> list[Memory]:
    return list(
        db.scalars(
            select(Memory).order_by(Memory.created_at.desc())
        ).all()
    )


def create_memory(db: Session, request: CreateMemoryRequest) -> Memory:
    memory = Memory(
        kind=request.kind.value,
        content=request.content,
        source_run_id=None,
        source_message_id=None,
    )

    db.add(memory)
    db.commit()
    db.refresh(memory)

    return memory
