from uuid import UUID

from langchain_core.messages import BaseMessage
from sqlalchemy import select
from sqlalchemy.orm import Session

from agent_server.deps import DbSession
from agent_server.models import Memory, Message
from agent_server.schemas import CreateMemoryRequest
from agent_server.services.llm import to_langchain_message


def list_memories(db: Session) -> list[Memory]:
    return list(
        db.scalars(
            select(Memory).order_by(Memory.created_at.desc())
        ).all()
    )


def load_chat_history(db: DbSession, session_id: UUID) -> list[BaseMessage]:
    messages = db.scalars(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at, Message.id)
    ).all()

    return [to_langchain_message(message) for message in messages]


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
