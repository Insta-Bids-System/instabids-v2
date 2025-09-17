# InstaBids Project Map (Initial Onboarding)

This is a concise, navigable map of the repository to reduce cognitive load and accelerate work.

## High-level architecture

- Monorepo with NodeJS workspaces and a Python FastAPI backend:
  - Workspaces: web, mobile, shared
  - Backend: ai-agents (FastAPI + multiple routers)
- Infrastructure/dev services defined via docker-compose.yml:
  - Frontend (Vite): 5173
  - Backend (FastAPI/Uvicorn): 8008
  - Postgres (Supabase-compatible local): 5432
  - Redis: 6379
  - MailHog: 1025 (SMTP), 8080 (UI)
  - Playwright test container for web (profile: testing)

## How to run locally

Option A — Direct dev (no Docker)
- Backend (FastAPI):
  - From repo root: npm run dev:ai
    - Equivalent: cd ai-agents && python -m uvicorn main:app --reload
  - Serves at http://localhost:8008
  - Env vars pulled from .env and OS (dotenv load in ai-agents/main.py)
- Web frontend (Vite):
  - From repo root: npm run dev:web
  - Serves at http://localhost:5173
  - Requires VITE_API_URL (e.g. http://localhost:8008) and Supabase envs for auth if used
- Mobile:
  - From repo root: npm run dev:mobile (delegates to mobile workspace start)
  - Details depend on mobile/package.json (to be indexed in the next pass)

Option B — Docker Compose
- docker compose up (or specify services: instabids-frontend, instabids-backend, supabase, redis, mailhog)
- Required environment (from docker-compose.yml):
  - SUPABASE_URL, SUPABASE_ANON_KEY (for both frontend and backend)
  - OPENAI_API_KEY, ANTHROPIC_API_KEY (backend optional but enables CIA agent)
- Ports:
  - Frontend: 5173, Backend: 8008, Postgres: 5432, Redis: 6379, MailHog: 1025/8080
- Volumes mount ./web and ./ai-agents into containers for live reload

## Backend entrypoint (ai-agents)

- Main: ai-agents/main.py (FastAPI app, CORS*, router composition, static mounting)
- Health root: GET / returns service metadata and a high-level endpoints list
- Static: mounts ai-agents/static at /static if present; /messaging-demo serves a demo HTML when present
- Admin:
  - /api/admin/session — simple mock session check
  - /api/admin/login — mock admin login (hardcoded) for local dev workflows
  - /api/admin/dashboard — attempts to read counts via database_simple (Supabase client)
- Routers included (prefix varies by file):
  - CIA: /api/cia/ (Customer Interface Agent)
  - COIA: /api/coia/ (Contractor-Oriented Interface Agent; fixed router variant)
  - Bid cards: /api/bid-cards/
  - Contractor management: /api/contractor-management/
  - Agent monitoring: /api/agents/
  - Intelligent messaging: /api/intelligent-messages/ (exact subpaths in router)
  - Campaign management: /api/campaign-management/
  - Admin enhanced routes: enhanced admin endpoints (prefix defined in file)
  - Bid card lifecycle: lifecycle operations
  - WebSocket routes: ws endpoints for realtime
  - Demo routes, homeowner routes, contractor routes
  - Unified conversation API: /api/conversations/ (prefix defined in router)
  - Streaming chat: SSE streaming
  - Leonardo image generation: /api/leonardo/
  - Iris chat: /api/iris/
  - Property API
  - Connection fee APIs (user and admin)
  - Agent context: /api/agent-context/
- CIA Agent initialization:
  - Prefers OPENAI_API_KEY for GPT-4o path; falls back to ANTHROPIC_API_KEY; otherwise uses fallback responses.

## Data layer

- Local Postgres via docker-compose service named supabase (plain Postgres image, Supabase-compatible developer flow)
- Supabase client usage in ai-agents (e.g., database_simple)
- supabase/ folder exists (migrations/config TBD in next pass)
- Redis provided via docker-compose for caching and realtime patterns

## JS/TS and Python tooling

- Node v18+ and npm v9+ (enforced via package.json engines)
- Prettier configured in root (format script)
- Husky + lint-staged:
  - web: biome check and run web tests on staged changes
  - python: ruff check with a curated ruleset on staged changes
  - json/md: prettier
- Python:
  - Target Python 3.12 (ruff config)
  - Ruff covers E/W/F/I/B/C4/PIE/SIM/TCH/TID/Q/UP/PT/RUF with pragmatic ignores
  - Formatting preferences (double quotes, line length 100, docstring formatting)

## Tests and quality

- Many scenario/system-level Python tests at repo root (e.g., test_* files: messaging, iris, contractor flows, etc.)
- Playwright container for web E2E (Dockerfile.playwright under web)
- quality-monitor.js and check-all.js scripts present (to be indexed in next pass)

## Directory map (top-level)

- web/ — Vite-based frontend (Dockerfile exists; Playwright infra present)
- mobile/ — React Native (or similar) mobile app (scripts TBD; to be indexed)
- shared/ — Shared JS/TS code between web/mobile
- ai-agents/ — FastAPI backend with routers, agents, api, database, memory, models, routes, services, static, templates, tests, etc.
- supabase/ — Supabase-related config/migrations (details to confirm)
- scripts/ — Utility scripts
- docs/ — Documentation (this file under docs/meta)
- database/, data/ — Data helpers/artifacts
- assets/, test-images/, test-sites/, demos/ — Various assets and demo/test sites
- deepagents-system/, knowledge/, archived_files/, archive-pre-aug4-2025/ — historical/contextual materials

## Known env vars

- Frontend (web):
  - VITE_API_URL (e.g. http://localhost:8008)
  - VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY
- Backend (ai-agents):
  - SUPABASE_URL, SUPABASE_KEY/SUPABASE_ANON_KEY
  - OPENAI_API_KEY, ANTHROPIC_API_KEY
  - REDIS_URL (defaults to redis://redis:6379 in docker-compose)
- Local Postgres in compose uses hardcoded POSTGRES_* envs

## Quick start (suggested)

- Direct dev:
  - cp .env.example .env and fill required keys
  - In one terminal: npm run dev:ai
  - In another terminal: npm run dev:web
- Docker:
  - Ensure required env vars (SUPABASE_URL, SUPABASE_ANON_KEY, OPENAI_API_KEY/ANTHROPIC_API_KEY as needed)
  - docker compose up -d
  - Frontend: http://localhost:5173, Backend: http://localhost:8008, MailHog UI: http://localhost:8080

## Next onboarding artifacts (to be generated)

- Entrypoints.md — exact commands per service (with environment notes), including mobile
- Endpoints.md — enumerated API endpoints with method/paths from routers
- DataFlow.md — how data moves (frontend → backend → Postgres/Supabase/Redis), key models/tables
- TestSuiteGuide.md — categorized list of tests and how to run fast loops
- QuickTasks.md — prioritized fixes/hotspots (based on your pain points)

If you want these generated next, I will index web/package.json, mobile/package.json, key routers under ai-agents, and supabase config to produce the next docs.
