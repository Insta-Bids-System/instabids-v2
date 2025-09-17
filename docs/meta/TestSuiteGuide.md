# Test Suite Guide (Initial Inventory + Fast Loops)

Goal: provide a quick way to run the right tests fast, understand coverage areas, and iterate confidently.

This guide will expand as we index more tests and wire up focused run scripts.

---

## Test Runners

- Backend (Python)
  - Recommended: pytest
  - Example:
    - python -m pytest -q test_messaging_integration_simple.py
    - python -m pytest -q ai-agents/tests/test_api_response.py
- Web (Vite + Vitest)
  - From web/: npm run test (or test:watch, test:coverage)

Note: Some Python tests live at repo root; others under ai-agents/tests/.

---

## Root-level Python Tests (indexed)

Functional/system scenario tests that exercise messaging, Iris, contractor flows, and end-to-end app flows:

- test_anonymous_to_authenticated_flow.py — session migration / auth transition
- test_cia_memory_quick.py — CIA memory checks
- test_contractor_anonymous_flow.py — contractor anon flow
- test_contractor_flow.py — contractor flow
- test_contractor_landing_enhanced.py — landing experience
- test_frontend_unified_complete.py — frontend unified E2E
- test_homeowner_experience.py — homeowner UX scenarios
- test_homeowner_messaging_unified.py — unified homeowner messaging
- test_iris_database_save.py — iris persistence
- test_iris_memory_quick.py — iris memory checks
- test_iris_working.py — iris working path
- test_messaging_agent_unified.py — intelligent agent messaging
- test_messaging_filter_debug.py — messaging filter behavior
- test_messaging_integration_simple.py — messaging fundamentals
- test_performance_fix.py — perf regression check
- test_unified_api_direct.py — unified API validations
- test_bid_document.txt, test_kitchen.txt — textual references (not Python)

Run examples:
- python -m pytest -q test_messaging_integration_simple.py
- python -m pytest -q test_homeowner_messaging_unified.py

---

## ai-agents/tests/ (indexed)

Focused backend/agent tests (subset discovered):

- test_api_response.py — API response sanity
- test_coia_real_complete.py — COIA end-to-end
- test_coia_streaming_interrupts.py — streaming/interrupt handling
- test_messaging_ui_simple.py — messaging UI path
- test_messaging_with_real_data.py — messaging with seeded data
- test_react_messaging_integration_fixed.py — React integration (fixed)
- test_react_messaging_integration.py — React integration

Run examples:
- python -m pytest -q ai-agents/tests/test_api_response.py
- python -m pytest -q ai-agents/tests/test_coia_real_complete.py

---

## Suggested Fast Loops

- Messaging Core:
  - python -m pytest -q test_messaging_integration_simple.py
  - python -m pytest -q ai-agents/tests/test_messaging_with_real_data.py
- Iris:
  - python -m pytest -q test_iris_memory_quick.py
  - python -m pytest -q test_iris_working.py
- Contractor Flows:
  - python -m pytest -q test_contractor_flow.py
  - python -m pytest -q ai-agents/tests/test_coia_real_complete.py
- Frontend:
  - cd web && npm run test:watch

Tip: use -q for quieter output, drop -q when debugging.

---

## Environment Requirements for Tests

- Backend tests often require:
  - SUPABASE_URL, SUPABASE_ANON_KEY (and/or SUPABASE_KEY)
  - Optional: OPENAI_API_KEY, ANTHROPIC_API_KEY (agent behaviors)
- Local infra via Docker can simplify DB/Redis:
  - docker compose up -d
- For messaging/image tests:
  - Supabase Storage bucket (“project-images”) expected (upload paths under intelligent_messages/)

---

## Troubleshooting

- Missing tables/columns:
  - Compare referenced tables in docs/meta/DataFlow.md to your DB schema
  - Ensure supabase migrations are applied; consider temporary seeds for local runs
- Agent/key issues:
  - Without OpenAI/Anthropic keys, some agent features fallback; tests may assert fallback paths
- Port conflicts / services:
  - Backend on 8008, web on 5173, Postgres 5432, Redis 6379
  - Stop conflicting services or adjust compose ports
- Web tests (Vitest):
  - Ensure Node >= 18, deps installed (npm i at repo root or web/)

---

## Next (to be automated)

- Curate pytest markers by domain (e.g., -m messaging, -m iris, -m coia)
- Add a Makefile or npm scripts for common test groups:
  - scripts: test:messaging, test:iris, test:coia, test:fast
- Wire CI to run critical smoke tests on push

If you want, I can scaffold Makefile and/or npm scripts to run these focused groups next.
