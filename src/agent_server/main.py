from fastapi import FastAPI
from agent_server.routers import approvals, chat, memories, sessions, settings, skills

app = FastAPI(title="Hermes-like Agent API", version="0.1.0")
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(approvals.router)
app.include_router(settings.router)
app.include_router(memories.router)
app.include_router(skills.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
