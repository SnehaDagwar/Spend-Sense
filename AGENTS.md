# Agent Instructions

Last updated: 2026-05-27

This repository may be worked on by Codex or other coding agents. Read this file before making changes.

## Current State

Spend Sense is a React/Vite personal finance app with a FastAPI backend. The frontend is local-first today and persists data in browser localStorage. The backend scaffold is working, Swagger docs are available, Phase 1 authentication is implemented, and business functionality beyond auth has not been implemented yet.

Primary references:

- [CODEX.md](CODEX.md) for commands and repository conventions.
- [docs/postgresql-schema.md](docs/postgresql-schema.md) for the PostgreSQL schema plan.
- [docs/api-contracts.md](docs/api-contracts.md) for endpoint contracts.
- [docs/backend-roadmap.md](docs/backend-roadmap.md) for phased backend work.

## Agent Guardrails

- Do not implement backend business features unless the user explicitly requests implementation.
- Do not replace the frontend localStorage model until a migration/import path is implemented.
- Do not make unrelated UI refactors while working on backend planning or infrastructure.
- Do not commit generated secrets, local `.env` files, database dumps, or receipt uploads.
- Do not use floats for money in backend models or migrations.
- Do not store raw passwords or raw refresh tokens.
- Do not delete user work or revert changes you did not make.

## Expected Workflow

1. Inspect the existing code before editing.
2. Keep changes scoped to the request.
3. Update docs when schema, contracts, or phase boundaries change.
4. Prefer existing project patterns over introducing new abstractions.
5. Run the smallest meaningful verification command for the change.
6. Report what changed, what was verified, and any remaining risk.

## Backend Boundaries

Backend code should follow this shape:

- `app/api/v1/routes`: HTTP route definitions.
- `app/schemas`: Pydantic request and response models.
- `app/models`: SQLAlchemy ORM models.
- `app/repositories`: persistence-oriented database access.
- `app/services`: domain workflows and calculations.
- `app/core`: settings, auth/security, shared infrastructure.
- `app/db`: engine, session, base metadata.

Keep route handlers thin. Put database access in repositories and cross-entity workflows in services.

## Contract Discipline

When changing an endpoint:

- Update `docs/api-contracts.md`.
- Add or update Pydantic schemas.
- Preserve `/api/v1` versioning.
- Keep date formats stable: `YYYY-MM` for months and `YYYY-MM-DD` for dates.
- Return consistent errors using the documented error shape.

When changing the schema:

- Update `docs/postgresql-schema.md`.
- Add an Alembic migration when implementation begins.
- Keep model definitions, migration DDL, and API response fields aligned.

## Verification

Use the relevant checks for the files touched:

- Frontend: `npm run build`, `npm test`, `npm run lint`.
- Backend: `python -m compileall app`, backend tests, Alembic upgrade checks.
- Docs-only: inspect changed files for broken links, stale paths, and conflicting guidance.

If a command cannot be run, explain why in the final response.
