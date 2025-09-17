# Entrypoints and Developer Commands

This document summarizes how to run services, build, test, and develop across the InstaBids monorepo.

Repo structure of interest:
- Root package.json (workspaces): web, mobile, shared
- Backend (FastAPI): ai-agents
- Infra/dev stack: docker-compose.yml

## Prerequisites

- Node.js >= 18, npm >= 9 (enforced via engines in package.json)
- Python 3.12 for backend (ruff config targets py312)
- Docker & Docker Compose (optional but recommended)
- Copy envs: cp .env.example .env then fill keys (SUPABASE, OpenAI/Anthropic if needed)

Environment variables commonly used:
- Frontend (web): VITE_API_URL (e.g., http://localhost:8008), VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY
- Backend (ai-agents): SUPABASE_URL, SUPABASE_KEY/SUPABASE_ANON_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, REDIS_URL

---

## Quick Start: Local Dev (no Docker)

Terminal A — Backend (FastAPI + Uvicorn)
- From repo root:
  - npm run dev:ai
  - Equivalent: cd ai-agents && python -m uvicorn main:app --reload
- Default local URL: http://localhost:8008
- Auto-loads environment via dotenv in ai-agents/main.py

Terminal B — Frontend (Vite)
- From repo root:
  - npm run dev:web
- Default local URL: http://localhost:5173
- Ensure VITE_API_URL points to the backend (e.g., http://localhost:8008)

Terminal C — Mobile (if applicable)
- From repo root:
  - npm run dev:mobile
- Note: The mobile directory contains android/ and ios/; if this is a React Native app without a workspace-level package.json, follow the platform-specific steps inside mobile/ (to be documented in a later pass if package.json is present).

---

## Using Docker Compose

Start the stack:
- docker compose up -d
  - Services: instabids-frontend (5173), instabids-backend (8008), supabase (5432), redis (6379), mailhog (1025/8080)
  - Volumes mount ./web and ./ai-agents for live reload inside containers
  - Ensure env vars are available to Docker (e.g., via .env or environment)

Stop the stack:
- docker compose down

View logs:
- docker compose logs -f instabids-backend
- docker compose logs -f instabids-frontend

Playwright testing container (E2E, optional profile):
- docker compose --profile testing up --build playwright-tests

---

## Root Scripts (Workspaces-aware)

Defined in package.json:

Development:
- npm run dev:web                      # runs web workspace dev server (Vite)
- npm run dev:mobile                   # runs mobile workspace (start)
- npm run dev:ai                       # cd ai-agents && uvicorn main:app --reload

Build:
- npm run build:web                    # build web workspace
- npm run build:mobile                 # build mobile workspace

Quality:
- npm run test                         # run tests for all workspaces
- npm run lint                         # lint across workspaces
- npm run format                       # prettier on js/ts/json/md
- npm run prepare                      # husky install

Setup:
- npm run setup                        # npm install && supabase init && supabase start
- npm run setup:supabase               # supabase init && supabase start

Custom checks (to be explored later):
- npm run check-all
- npm run check-all:fix
- npm run check-all:web
- npm run check-all:python
- npm run quality:monitor
- npm run quality:watch
- npm run quality:report

---

## Web Workspace Scripts

From web/package.json:

- npm run dev                          # vite dev server
- npm run build                        # vite build
- npm run preview                      # vite preview
- npm run lint                         # eslint with TS/React plugins
- npm run type-check                   # tsc --noEmit
- npm run test                         # vitest
- npm run test:ui                      # vitest UI
- npm run test:run                     # vitest run (non-watch)
- npm run test:coverage                # vitest with coverage
- npm run test:watch                   # vitest watch

---

## Backend (FastAPI) Entrypoints

- Dev (hot-reload): npm run dev:ai
  - Equivalent: cd ai-agents && python -m uvicorn main:app --reload
  - Exposes: http://localhost:8008
- Production-like (without reload):
  - cd ai-agents && uvicorn main:app --host 0.0.0.0 --port 8008

Health/Index:
- GET / returns service metadata (including a list of notable endpoints)

Routers (high-level, prefixes set in code):
- /api/cia, /api/coia, /api/bid-cards, /api/contractor-management, /api/agents
- /api/intelligent-messages, /api/campaign-management, /api/admin
- /api/conversations, /api/leonardo, /api/iris, /api/agent-context
- WebSockets routes and demo endpoints
- See docs/meta/ProjectMap.md for details; a full Endpoints.md will be generated in a later pass.

---

## Testing

Web:
- From repo root: npm run test --workspace=web
- Or inside web/: npm run test (or test:run, test:watch, test:coverage)

Backend / Python:
- Multiple scenario/system tests exist at the repo root (test_*.py).
- Suggested pattern:
  - python -m pytest -q test_...py           # direct pytest runs for specific files
  - Or create a venv in ai-agents/ and run targeted tests tied to backend concerns.

Playwright (E2E) via Docker (optional):
- docker compose --profile testing up --build playwright-tests

---

## Linting and Formatting

- JavaScript/TypeScript:
  - npm run lint --workspaces
  - web uses Biome in lint-staged for staged files
- Python:
  - Ruff checks (configured in ai-agents/pyproject.toml)
  - lint-staged applies ruff to changed Python files in ai-agents
- Formatting:
  - npm run format (prettier for js/ts/json/md)

---

## Troubleshooting

- CORS: Backend enables permissive CORS for dev; adjust in production.
- Supabase/Postgres:
  - docker-compose uses a plain Postgres image with developer credentials
  - Ensure SUPABASE_URL and SUPABASE_ANON_KEY are consistent between frontend/backend
- OpenAI/Anthropic keys:
  - Optional but enable richer CIA agent behavior
  - Without these, CIA returns fallback responses
- Ports conflicts:
  - 5173 (web), 8008 (backend), 5432 (postgres), 6379 (redis), 8080 (mailhog ui)
  - Stop conflicting local services or adjust ports as needed
- Node version:
  - Ensure Node >= 18; use nvm if necessary

---

## Next

Planned next artifacts:
- docs/meta/Endpoints.md (enumerated API endpoints)
- docs/meta/DataFlow.md (frontend → backend → Postgres/Supabase/Redis)
- docs/meta/TestSuiteGuide.md (categorization of root test_*.py & any backend tests)
- docs/meta/QuickTasks.md (prioritized pain points once identified)
