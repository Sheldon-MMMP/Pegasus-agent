---
name: fastapi-local-dev
description: 如何在本项目中启动 FastAPI 后端。
version: 1
---

# FastAPI Local Dev

Use this skill when working on the local FastAPI backend.

## Steps

1. Enter the `agent_server` directory.
2. Run `uv run uvicorn --app-dir src agent_server.main:app --reload --port 8000`.
3. Open `http://127.0.0.1:8000/docs`.