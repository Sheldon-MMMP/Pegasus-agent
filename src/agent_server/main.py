from contextlib import asynccontextmanager

from fastapi import FastAPI

from agent_server.db import SessionLocal
from agent_server.routers import approvals, chat, memories, sessions, settings, skills
from agent_server.skills.loader import get_skills_root
from agent_server.skills.sync import sync_skills


@asynccontextmanager
async def lifespan(app: FastAPI):
    skills_root = get_skills_root()
    project_root = skills_root.parent

    with SessionLocal() as db:
        sync_skills(db=db, skills_root=skills_root, project_root=project_root)

    yield
app = FastAPI(title="Hermes-like Agent API", version="0.1.0", lifespan=lifespan)
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(approvals.router)
app.include_router(settings.router)
app.include_router(memories.router)
app.include_router(skills.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
