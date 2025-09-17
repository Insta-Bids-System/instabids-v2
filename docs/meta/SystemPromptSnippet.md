# Minimal Persistent Context for InstaBids Sessions (paste into system prompt)

Use this as the always-on guardrails and context. Keep it short to avoid prompt bloat; detailed docs live in docs/meta/.

- Repo root: c:/Users/Not John Or Justin/Documents/instabids
- Monorepo: workspaces web/, mobile/, shared/ plus backend ai-agents/ (FastAPI)
- Backend entrypoint: ai-agents/main.py (single FastAPI app)
  - Port 8008 is owned by Docker backend. Do not start new local servers. Do not call uvicorn.run()/asyncio.run() in new processes.
  - Add features to existing routers in ai-agents/routers/ or to app in main.py (no new FastAPI apps).
- Test-first discipline (never claim success without proof):
  1) API: call running backend (GET /, GET /api/admin/dashboard, then feature endpoints)
  2) DB: verify Supabase writes/reads via database_simple.get_client() tables
  3) UI: verify with Playwright (real pages, real data)
  4) End-to-end: multi-turn agent interactions; real tool/API calls; real data persisted
  5) Errors: send invalid inputs; confirm expected error handling
- Data layer: Supabase via ai-agents/database_simple.py → database.SupabaseDB (db.client)
  - Messaging-critical tables referenced: conversations, messaging_system_messages, message_attachments, blocked_messages_log, agent_comments
- Env essentials:
  - Backend: SUPABASE_URL, SUPABASE_ANON_KEY (and/or SUPABASE_KEY), optional OPENAI_API_KEY / ANTHROPIC_API_KEY, REDIS_URL
  - Frontend: VITE_API_URL (→ http://localhost:8008), VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY
- Debug order of operations:
  1) Health: GET http://localhost:8008/ and /api/admin/dashboard
  2) Inspect logs/data/auth; loading spinners usually indicate data/auth issues, not a dead backend
  3) Only then code changes (in existing routers/main.py)
- Do not modify working systems unless required by task; no competing servers, no duplicate ports
- Living project docs live in:
  - docs/meta/ProjectMap.md, Entrypoints.md, Endpoints.md (+ Expanded), DataFlow.md, TestSuiteGuide.md, QuickTasks.md, ContextSnapshot.json
