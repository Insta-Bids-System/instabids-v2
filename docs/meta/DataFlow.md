# Data Flow and Storage Map (Initial)

Goal: clarify where data lives, how it moves between frontend ↔ backend ↔ storage (Postgres/Supabase, Redis), and what tables are touched by critical paths.

Last indexed components:
- Backend FastAPI app (ai-agents/main.py)
- Intelligent Messaging API (ai-agents/routers/intelligent_messaging_api.py)
- Messaging APIs (messaging_api.py, messaging_fixed.py, messaging_simple.py)
- Contractor/COIA/Conversation routers (partial)
- Database wrapper (ai-agents/database_simple.py → database.SupabaseDB)

---

## High-Level Flow

Frontend (web Vite) → Backend (FastAPI) → Data layer
- Web uses VITE_API_URL to talk to FastAPI on 8008
- Backend uses Supabase Python client (via database_simple.get_client()) to read/write tables
- Redis is available (redis://redis:6379 via compose) for caching/realtime (usage to be confirmed per router)
- Static assets/storage: images uploaded to Supabase Storage buckets (e.g., "project-images")

Environment:
- Backend loads env via dotenv (ai-agents/main.py): SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, REDIS_URL
- Docker compose exposes Postgres (as “supabase” service) and Redis
- Frontend config: VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY for auth flows, if used

---

## Database Access Layer

Module: ai-agents/database_simple.py
- Thin compatibility wrapper exposing:
  - db = SupabaseDB()    # singleton around actual database module
  - get_client() → db.client
- All routers call database_simple.get_client() then db.table("...") … execute()

Implication:
- Centralize Supabase configuration in database.SupabaseDB
- If credentials or URL differ across envs, only this initialization needs change

---

## Messaging System (Business Critical)

Routers: intelligent_messaging_api.py, messaging_api.py, messaging_fixed.py, messaging_simple.py

Key tables referenced (via db.table("...")):
- conversations
- messaging_system_messages
- message_attachments
- blocked_messages_log
- agent_comments

Core lifecycle:
1) Intelligent message POST arrives → process_intelligent_message(...) (agents/intelligent_messaging_agent)
   - Returns: approved/blocked, filtered_content, threats_detected, agent_decision, comments, confidence_score
2) Target resolution:
   - Resolve/create conversation_id for the right homeowner/contractor pair tied to bid_card_id
3) Persistence:
   - If approved → insert into messaging_system_messages
     - Update conversations.last_message_at
     - Insert attachments into message_attachments as needed
   - If blocked → insert into blocked_messages_log for audit
4) Queries:
   - Agent comments retrieved from agent_comments (visibility filters)
   - Security analysis aggregates from blocked_messages_log + messaging_system_messages joined to conversations

Important joins/filters:
- messaging_system_messages.conversation_id ↔ conversations.id
- Blocked vs filtered message logic drives reporting and “security score”

Uploads:
- send-with-image: uploads bytes to Supabase Storage bucket "project-images" under intelligent_messages/ prefix, returns public URL stored alongside message

---

## Bid Cards and Campaigns (Selected)

Tables referenced across routers (non-exhaustive):
- bid_cards
- contractor_bids
- conversations
- outreach_campaigns
- campaign_check_ins
- campaign_contractors
- contractor_leads / potential_contractors (varies by context)
- contractor_outreach_attempts
- notifications
- connection_fees (+ admin_connection_fees API)
- admin_users, admin_sessions, admin_activity_log (admin services)

Patterns:
- Many admin/monitoring endpoints compute dashboards from aggregate queries
- Some modules use tables that might differ across environments (e.g., contractor_leads vs potential_contractors in admin watchers) — watch for schema drift

---

## Supabase Storage

- Bucket: "project-images"
- Paths: intelligent_messages/{timestamp}_{uuid}_{original_filename}
- Access: public URL fetched via get_public_url after upload

---

## Redis

- Service available at redis://redis:6379
- Used by backend (planned/indicated in env), actual usage to be enumerated by scanning services (e.g., websocket routes, streaming/chat, caching)
- Next step: index routers/services to document Redis-backed features (if any)

---

## Authentication & Sessions

- Admin auth in main.py is mocked (email/password hardcoded) for local dev convenience
- admin_routes / admin_* services refer to admin_users/admin_sessions tables for proper auth/session in production-like flows
- Web uses Supabase JS client for auth when configured (VITE_SUPABASE_*)
  - Next step: index web/src for Supabase-auth usage paths

---

## Data Model Snapshot (from code references)

The following tables are referenced by name in backend code (sample, not exhaustive):
- conversations
- messaging_system_messages
- message_attachments
- blocked_messages_log
- agent_comments
- bid_cards
- contractors, contractor_bids, contractor_leads, potential_contractors
- outreach_campaigns, campaign_check_ins, campaign_contractors, contractor_outreach_attempts
- notifications, broadcast_messages, broadcast_read_receipts
- connection_fees, referral_tracking
- admin_users, admin_sessions, admin_activity_log
- followup_logs
- projects, homeowners (in tests/utilities)

Action: compare against actual Postgres schema/migrations in supabase/ to resolve mismatches and add migrations if missing.

---

## Risks and Hotspots

- Schema drift: multiple modules reference varied table names (contractor_leads vs potential_contractors)
- Conversation resolution logic is duplicated across messaging_* routers; ensure uniform behavior and indexes on conversations (bid_card_id, contractor_id, homeowner_id)
- Large joins and ORDER BY created_at likely need indexes for performance (messages by conversation_id, timeline by bid_card_id)
- Security analysis depends on consistent logging of blocked messages; verify triggers and retention
- Supabase Storage permissions: ensure public URL policy matches product needs

---

## Next Steps

- Inventory supabase/ migrations to confirm tables and constraints exist
- Document concrete ERD (entities + relationships) based on live schema and code references
- Add index recommendations:
  - conversations(bid_card_id, contractor_id, homeowner_id)
  - messaging_system_messages(conversation_id, created_at DESC)
  - blocked_messages_log(bid_card_id, blocked_at DESC)
  - message_attachments(message_id)
- Trace Redis usage across routers/services; add to this doc
- Add Data Contracts: define payloads and invariants per critical endpoints

Once you want deeper detail, I’ll scan supabase config/migrations and generate an ERD-style map plus concrete index DDL recommendations.
