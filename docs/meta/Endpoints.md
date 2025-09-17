# API Endpoints (Initial Index)

This document enumerates discovered API endpoints and router prefixes. It will expand as more routers are indexed.

Legend:
- METHOD PATH — Description
- [prefix] indicates router-level prefix

Last indexed: Intelligent Messaging API and root/admin endpoints.

---

## Root service (FastAPI app)

- GET / — Service metadata and notable endpoints
- GET /messaging-demo — Serve demo HTML if present (ai-agents/static/messaging-ui-demo.html)

### Admin (from main.py)
- GET /api/admin/session — Check admin session (mock)
- POST /api/admin/login — Mock admin login
- GET /api/admin/dashboard — Dashboard summary (uses Supabase client)

---

## Intelligent Messaging API
[prefix] /api/intelligent-messages  
(file: ai-agents/routers/intelligent_messaging_api.py)

- GET /api/intelligent-messages/health — Health check (DB + agent reachability)
- POST /api/intelligent-messages/send — Process message via intelligent agent and route/save
- POST /api/intelligent-messages/send-with-image — Process with image; store to storage on approval
- GET /api/intelligent-messages/agent-comments/{user_type}/{user_id} — List agent comments visible to a user (optional bid_card_id filter)
- GET /api/intelligent-messages/security-analysis/{bid_card_id} — Summary stats and threat patterns for a bid card
- POST /api/intelligent-messages/notify-contractors-scope-change — Notify all contractors on a bid card about scope changes
- POST /api/intelligent-messages/respond-to-scope-change-question — Handle homeowner response to agent’s scope-change question (notify or not)
- GET /api/intelligent-messages/scope-change-notifications/{contractor_id} — Fetch scope change notifications (optional bid_card_id filter)
- POST /api/intelligent-messages/test-security — Dev-only test path for agent analysis

Notes:
- Uses database_simple.get_client() (Supabase) extensively
- Approved messages write to messaging_system_messages, blocked to blocked_messages_log
- Conversation resolution logic creates conversations on-demand when needed

---

## Router prefixes discovered (to be enumerated next)

From ai-agents/main.py (router include list; details TBC per file):

- [prefix] /api/cia — Customer Interface Agent (cia_routes)
- [prefix] /api/coia — Contractor-Oriented Interface Agent (coia_api_fixed)
- [prefix] /api/bid-cards — Bid card API (bid_card_api)
- [prefix] /api/contractor-management — Contractor management API
- [prefix] /api/agents — Agent monitoring API
- [prefix] /api/campaign-management — Campaign management
- [prefix] /api/admin — Admin routes (admin_routes plus enhanced variant)
- [prefix] (TBD) — Bid card lifecycle routes
- [prefix] (TBD) — WebSocket routes
- [prefix] (TBD) — Demo routes
- [prefix] (TBD) — Homeowner routes
- [prefix] (TBD) — Contractor routes
- [prefix] /api/conversations — Unified conversation API
- [prefix] (TBD) — Streaming chat (SSE) 
- [prefix] /api/leonardo — Image generation
- [prefix] /api/iris — Iris chat system
- [prefix] (TBD) — Property API
- [prefix] (TBD) — Connection fee API (user)
- [prefix] (TBD) — Admin connection fee API
- [prefix] /api/agent-context — Agent context with privacy filtering

---

## Next indexing targets

- Enumerate endpoints for CIA, COIA, Bid Cards, Contractor Management, Agent Monitoring, Campaign Management
- WebSocket routes (paths, events)
- Property and Connection Fee APIs
- Unified Conversation and Streaming Chat
- Confirm prefixes inside each router file and list methods/paths

When you’re ready, I will index the next routers and expand this document.
