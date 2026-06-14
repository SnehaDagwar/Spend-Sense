# Backend Implementation Roadmap

Last updated: 2026-05-27

This roadmap keeps backend work phased so Spend Sense can move from local-first storage to server-backed persistence without breaking the current product.

## Current Baseline

Done:

- FastAPI app factory boots successfully.
- Swagger/OpenAPI docs are available.
- CORS settings are configurable.
- API v1 router exists.
- Health route exists.
- SQLAlchemy session/base and Alembic are scaffolded.
- Authentication routes, schemas, repositories, services, SQLAlchemy models, and first auth migration exist.

Not started:

- Business-domain models beyond authentication.
- Alembic migrations beyond authentication.
- CRUD APIs.
- LocalStorage import.

## Phase 0 - Planning And Contract Lock

Goal: establish shared backend direction before feature implementation.

Deliverables:

- `CODEX.md`
- `AGENTS.md`
- `docs/postgresql-schema.md`
- `docs/api-contracts.md`
- `docs/backend-roadmap.md`

Exit criteria:

- Backend schema target is documented.
- API contracts are documented.
- Agents have clear instructions not to implement business features prematurely.

Status: complete when these docs are committed.

## Phase 1 - Database Foundation

Goal: make the database schema real without exposing product APIs yet.

Deliverables:

- SQLAlchemy models for all Phase 1 tables.
- First Alembic migration matching `docs/postgresql-schema.md`.
- Seed data for system categories and initial badge catalog.
- Updated `app/db/base.py` imports so Alembic sees all models.
- Test database configuration.
- Basic migration tests or smoke checks.

Suggested verification:

- `alembic upgrade head`
- `alembic downgrade base`
- `python -m compileall app`

Exit criteria:

- A fresh PostgreSQL database can migrate from empty to current schema.
- System categories are present after setup.
- No HTTP business routes are required yet.

## Phase 2 - Auth, Profile, And Preferences

Goal: support real users while preserving the local-first frontend until migration is ready. The auth subset is implemented; profile and preference endpoints remain pending.

Deliverables:

- Password hashing and JWT access token creation. Done.
- Refresh token rotation and revocation. Done.
- `POST /auth/register`. Done.
- `POST /auth/login`. Done.
- `POST /auth/refresh`. Done.
- `POST /auth/logout`. Done.
- `GET /auth/me`. Done.
- `GET /me`
- `PATCH /me/profile`
- `PATCH /me/preferences`
- `PATCH /me/notifications`
- Integration tests for auth success and failure paths.

Exit criteria:

- A user can create an account, authenticate, refresh, and revoke a session.
- Preferences can be read and updated through authenticated APIs.
- OpenAPI shows stable schemas for auth and profile flows.

## Phase 3 - Budgets, Categories, Expenses, And Import

Goal: move the core tracker from local-only data toward backend persistence.

Deliverables:

- Category APIs.
- Budget month APIs.
- Expense APIs.
- Receipt metadata/upload APIs if file storage is enabled.
- `POST /sync/import-local-store` for `spend-sense-store-v1`.
- Import mapping for default category slugs and custom categories.
- Repository/service tests for budget and expense operations.
- Frontend integration can remain behind a feature flag or adapter.

Exit criteria:

- Existing local data can be imported for a new backend account.
- Expenses can be created, edited, listed, searched, and deleted.
- Monthly budgets can be upserted without losing category allocations.
- API responses can hydrate the current frontend domain shape.

## Phase 4 - Savings Goals, Analytics, Insights, And Reports

Goal: support the app's planning and intelligence features from server data.

Deliverables:

- Savings goal CRUD.
- Goal contribution APIs.
- Monthly analytics endpoint.
- Insights endpoint using the existing frontend logic as a reference.
- Monthly report data endpoint.
- CSV/PDF export endpoints or server-generated report data for frontend export.
- Tests around calculations and date boundaries.

Exit criteria:

- Goal progress and contribution history survive refresh/login.
- Analytics match current local calculations for representative fixtures.
- Reports can be generated from server data for a month.

## Phase 5 - Family Wallet And Settlements

Goal: make shared spending real and auditable.

Deliverables:

- Family wallet create/read/update.
- Family member CRUD with admin protection.
- Expense split persistence.
- Pending balance computation.
- Manual settlement creation and status updates.
- Tests for split math and settlement edge cases.

Exit criteria:

- Family expenses can record payer and participants.
- Pending balances are deterministic.
- Settlements update balances without deleting historical expenses.

## Phase 6 - Gamification (Superseded by Phase 9)

> **Note**: This phase has been superseded by Phase 9 which implements a full
> event-driven gamification engine. See Phase 9 below.

Goal: persist and verify achievements, daily challenges, XP, level, and streaks.

Status: superseded by Phase 9.

## Phase 7 - Hardening And Deployment

Goal: make the backend production-ready.

Status: **complete** (Phase 13).

Deliverables:

- Structured JSON logging (`app/core/logging.py`) — JSON in production, text locally.
- `LOG_LEVEL` configurable via environment variable.
- Sentry error monitoring (`sentry-sdk[fastapi]`) — optional, enabled via `SENTRY_DSN`.
- Rate limiting for auth endpoints (SlowAPI — already present from Phase 2).
- CORS reviewed — configured via `BACKEND_CORS_ORIGINS` env var on Render.
- Secret management — `SECRET_KEY` validation enforces 32+ chars outside local/test.
- Database connection pool with `pool_pre_ping=True` (already present).
- `alembic upgrade head` runs on every Render deploy before uvicorn starts.
- `docs/deployment.md` — full deployment and rollback runbook.
- `.github/workflows/ci.yml` — CI blocks on lint, test, build, and migration regressions.
- `.github/workflows/db-backup.yml` — weekly `pg_dump` to GitHub Actions artifacts.
- `vercel.json` — SPA routing, security headers, asset caching for Vercel frontend.
- `backend/render.yaml` — Render Blueprint for one-click backend deployment.
- `/api/v1/health` enhanced with real DB ping and structured response.

Exit criteria: met.

## Phase 8 - AI Insights And Financial Intelligence

Goal: add provider-agnostic AI-powered financial insights with graceful rule-based fallback.

Status: implemented.

Deliverables:

- Provider abstraction interface (`AIProvider` ABC) with Gemini, OpenAI, Claude, and Mock implementations.
- AI service layer (`AIService`) that compiles financial data from ORM models, manages rate limiting, caching, and provider orchestration.
- Rule-based fallback engine (`fallback.py`) generating deterministic insights from raw financial data when the AI provider is unavailable.
- Prompt templates (`prompts.py`) with privacy guardrails, currency awareness, and conciseness directives.
- Five authenticated insight endpoints:
  - `GET /insights/summary` — financial health score, budget status, overspending alerts, savings opportunities.
  - `GET /insights/spending-patterns` — dominant categories, payment methods, time-of-month analysis, subscription detection.
  - `GET /insights/recommendations` — budget adjustment suggestions, savings actions, goal milestones.
  - `GET /insights/anomalies` — statistical outliers, duplicate detection, budget spike alerts.
  - `GET /insights/monthly-review` — net savings, savings rate, top drivers, achievements, next-month opportunities.
- Pydantic response schemas with `source` field indicating insight origin (`ai`, `rule_engine`, `mock`).
- Production-grade rate limiting: 10 requests/day and 5 requests/minute per user.
- SHA256 state-hash caching with 1-hour TTL and bounded LRU eviction (500 entries).
- Retry logic (1 retry with 2s backoff) on transient provider failures.
- Configurable settings: `AI_PROVIDER`, `AI_REQUEST_TIMEOUT`, `AI_MAX_RESPONSE_TOKENS`, `AI_BURST_RATE_LIMIT`, `AI_FALLBACK_ENABLED`, `AI_CACHE_MAX_SIZE`.
- `Retry-After` header on 429 responses.
- OpenAPI response documentation for error codes (429, 502).
- Updated `docs/api-contracts.md` with implementation status and `source` field.

Exit criteria:

- All 5 insight endpoints return valid responses with `AI_PROVIDER=mock`.
- Rate limiting correctly rejects requests past daily or burst threshold.
- Fallback engine produces structured insights when the AI provider is unavailable.
- No new database tables or migrations required.
- Compile check passes (`python -m compileall app`).

## Phase 9 - Gamification And Achievements

Goal: deliver a scalable, event-driven gamification engine with badges, streaks, challenges, XP/levels, and progress tracking.

Status: implemented.

Deliverables:

- Two new SQLAlchemy models: `gamification_events` (event log) and `user_streaks` (incremental streak counters).
- Two new enums: `GamificationEventType`, `StreakType`.
- `GamificationRepository` — events, streaks, progress, badges, challenges.
- `GamificationService` facade with sub-engines:
  - `XPEngine` — XP rewards, level formula (`floor(sqrt(xp/100)) + 1`).
  - `StreakEngine` — daily/weekly/monthly streak tracking with O(1) updates.
  - `BadgeEngine` — declarative rule registry with 20 badge rules (count, streak, completion, challenge-count, consecutive-budget).
  - `ChallengeEngine` — idempotent daily challenge generation from templates.
  - `EventDispatcher` — orchestrates event recording → badge evaluation → streak update → XP grant.
- Badge catalog expanded to 20 badges across 4 categories (discipline, savings, streaks, social).
- Five authenticated endpoints under `/gamification/`:
  - `GET /gamification/profile` — XP, level, progress, recent badges, current streaks.
  - `GET /gamification/badges` — full badge catalog with per-user unlock state.
  - `GET /gamification/streaks` — all streak counters.
  - `GET /gamification/challenges` — challenge list with auto-generation.
  - `POST /gamification/challenges/{id}/join` — join an active challenge.
- Pydantic schemas for all request/response shapes.
- Updated `docs/api-contracts.md` with full endpoint documentation.

Exit criteria:

- Compile check passes (`python -m compileall app`).
- Badge rules are idempotent — re-evaluating the same event produces no duplicates.
- Event recording is idempotent — duplicate events are no-ops.
- XP grants use `SELECT ... FOR UPDATE` to prevent concurrent double-counting.
- Daily challenge generation is idempotent for the same user/date.
- Streak updates are O(1) per event (no full history scans).
- All 5 endpoints are JWT-protected and documented in OpenAPI.

## Cross-Phase Rules

- Update `docs/api-contracts.md` before or alongside API changes.
- Update `docs/postgresql-schema.md` before or alongside schema changes.
- Keep Pydantic schemas, SQLAlchemy models, and frontend TypeScript types aligned.
- Add tests at the same phase as implementation.
- Preserve user-owned localStorage data until import and sync flows are proven.
