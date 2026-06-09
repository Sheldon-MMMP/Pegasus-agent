# Agent Server

TypeScript implementation of the agent API. The service uses Express, PostgreSQL,
the OpenAI SDK, and server-sent events.

## Architecture

The backend follows a traditional layered architecture:

```text
src/
├── domain/              Shared business types
├── infrastructure/      PostgreSQL, OpenAI, and SSE implementations
├── interfaces/http/     Routes, controllers, request schemas, middleware
├── repositories/        Database access and SQL
├── services/            Business rules and use-case orchestration
├── shared/              Cross-layer errors and utilities
├── scripts/             Operational scripts such as database migration
└── server.ts            Backend composition root
```

HTTP controllers depend on services, services depend on repositories and
infrastructure, and repositories own all SQL statements.

## Requirements

- Node.js 22+
- PostgreSQL 17 (or the included Docker Compose service)

## Run

```bash
docker compose up -d
npm install
npm run migrate
npm run dev
```

The API listens on `http://localhost:8000` by default. Override it with `PORT`
and configure PostgreSQL with `DATABASE_URL`.

OpenAPI documentation is available while the server is running:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Commands

```bash
npm run dev        # development server with reload
npm run build      # compile backend to dist/
npm start          # run compiled backend
npm run typecheck  # validate backend TypeScript
npm run migrate    # create/update database tables
```
