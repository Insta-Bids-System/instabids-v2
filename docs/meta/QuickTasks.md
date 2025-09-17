# QuickTasks (Prioritized, Test-First)

This is a living, execution-focused checklist aligned with the project's mandatory testing and backend coordination rules.

Status: initial seed. Execution order optimized for fast wins and guardrails.

---

## P0 — Verification Guardrails (always first)

- Backend health check routine (never restart, never spawn new servers):
  - GET http://localhost:8008/
  - GET http://localhost:8008/api/admin/dashboard
  - Confirm 200 OK and JSON payload. If failing, inspect data/auth first, not process state.

- Test-first discipline (never claim success without proof):
  - For any feature: 1) API response, 2) DB verification (Supabase), 3) UI verification (Playwright), 4) End-to-end scenario, 5) Error handling.
  - Record actual outputs (responses, DB rows, screenshots). No placeholders/hardcoded data.

- Router edit rules:
  - Extend existing routers in ai-agents/routers/ or app in ai-agents/main.py.
  - No new FastAPI apps, no uvicorn.run(), no competing Python processes (port 8008 is owned by Docker backend).

---

## P1 — API Inventory Completion

- Expand Endpoints index to full coverage
  - Source: search inventory (233 handlers).
  - Output: docs/meta/EndpointsExpanded.md with all methods/paths grouped by router, including observed prefixes.
  - Cross-check main.py include_router lines for expected prefixes.

- Tag “business critical” endpoints
  - Messaging, COIA/CIA, Bid Cards, Unified Conversation, Property, Connection Fees.
  - Add notes on auth/inputs/side-effects per route where determinable from code.

Deliverables:
- docs/meta/EndpointsExpanded.md (full coverage)
- Update docs/meta/Endpoints.md to reference Expanded version

---

## P2 — Data Schema & Indexes

- Reconcile table usage vs schema
  - From code: conversations, messaging_system_messages, message_attachments, blocked_messages_log, agent_comments, bid_cards, outreach_campaigns, etc.
  - Inspect supabase/ migrations, derive ERD snapshot.

- Propose/confirm indexes for hot paths
  - conversations(bid_card_id, contractor_id, homeowner_id)
  - messaging_system_messages(conversation_id, created_at desc)
  - blocked_messages_log(bid_card_id, blocked_at desc)
  - message_attachments(message_id)

Deliverables:
- docs/meta/SchemaERD.md (diagram/relations)
- supabase/sql/index_recommendations.sql (DDL)

---

## P3 — Golden E2E Test Loops (real systems only)

Define and run 3 “golden paths” with full verification (API + DB + UI):

1) Intelligent Messaging approval path
  - Steps:
    - POST /api/intelligent-messages/send with benign content
    - Verify: conversation created/resolved, message written to messaging_system_messages
    - UI: load messaging UI page (Playwright) and assert message presence
  - Negative: send content that should be blocked; verify blocked_messages_log row

2) COIA chat stream path
  - Steps:
    - POST /api/coia/chat (or /coia/chat/stream)
    - Verify: response payload, any persisted artifacts, logs
    - UI: appropriate web screen renders chat response (if applicable)

3) Bid Card lifecycle insights
  - Steps:
    - Exercise endpoints under /api/bid-cards and lifecycle routes
    - Verify: expected joins and counts, timeline endpoints
    - UI: Admin/Contractor view reflects data

Deliverables:
- docs/meta/E2EPlans.md (scripts/commands)
- Saved artifacts: API responses, DB query results, screenshots

Note: Do not run/claim until configured with real keys and DB reachable.

---

## P4 — Conversation Targeting Deduplication

- Unify conversation resolution logic (currently repeated across messaging_* and intelligent_messaging_api)
  - Extract helper in shared module (e.g., services/conversation_service.py) with single source of truth
  - Add unit tests + integrate across routers

Deliverables:
- ai-agents/services/conversation_service.py
- docs/meta/RefactorNotes.md (before/after, guarantees)
- Tests covering homeowner→contractor, contractor→homeowner, explicit conversation_id

---

## P5 — Context Snapshot for Fast Cold-Starts

- Machine-readable, minimal context for future sessions
  - services, ports, env keys, invariants (backend do-not-restart rule)
  - Router list and known prefixes
  - Path anchors for critical code

Deliverables:
- docs/meta/ContextSnapshot.json

---

## P6 — Developer UX

- Script shims for common commands with health checks:
  - e.g., scripts/dev-health.ps1 (pings / and /api/admin/dashboard)
  - npm scripts for targeted pytest groups (messaging, iris, coia)

Deliverables:
- scripts/dev-health.ps1
- package.json: “test:messaging”, “test:coia”, “test:iris” shims

---

## Execution Notes

- No Docker lifecycle management unless explicitly requested
- All tests against the already-running backend at port 8008
- All changes confined to existing routers/main.py; no new servers
- Always attach proof artifacts with each task marked complete
