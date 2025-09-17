# Schema Drift Analysis (Code vs Supabase Migrations)

Scope
- Codebase scanned: ai-agents/* (routers, services, admin, api) and prior search results
- Migrations scanned:
  - supabase/migrations/20250126_initial_schema.sql
  - supabase/migrations/20250126_row_level_security.sql
  - supabase/migrations/20250127_dev_testing_policies.sql

Authoritative truth for DB = migrations. This file lists mismatches with code references and proposes reconciliation actions.

---

## A) Tables referenced in code but NOT present in migrations

Messaging and Conversations (code-centric)
- messaging_system_messages
- message_attachments
- blocked_messages_log
- broadcast_messages
- broadcast_read_receipts
- agent_comments

Bid Cards and Contractor Lifecycle
- bid_cards
- contractor_bids (also used; may overlap with bids table conceptually)
- referral_tracking
- notifications
- potential_contractors
- contractor_leads
- contractor_outreach_attempts
- outreach_campaigns
- campaign_check_ins
- campaign_contractors

Payments/Fees
- connection_fees

Admin/Monitoring
- admin_users
- admin_sessions
- admin_activity_log

Property system (API present, schema missing)
- properties
- rooms
- property_assets
- property_photos

Analytics/Logs (various)
- followup_logs
- contractor_discovery_cache (PRESENT in migrations) — OK
- projects (PRESENT) — OK

Proposed action
- Decide canonical domain model:
  - Either adopt “projects/bids/messages/conversations/payments” (migrations) OR “bid_cards/messaging_system_messages/*” (code).
  - If “bid_cards” model is canonical, draft migrations to create all missing tables with needed columns and constraints.
  - If “projects” model is canonical, refactor code to stop using bid_cards/messaging_system_messages family and converge on messages/conversations tables.

---

## B) Tables present in migrations but RARELY/NOT referenced by current routers

- messages (present, used minimally by some routes/policies; primary code currently uses messaging_system_messages)
- payments (present; code focuses on connection_fees)
- reviews (present; limited direct code references found)
- profiles/contractors/projects/bids (present; code uses projects in some areas but often pivots to bid_cards)

Proposed action
- If these are legacy, mark as deprecated and migrate code off them.
- If these are intended future canonical tables, prioritize refactor tasks to route code to them and remove parallel tables from the “missing” list.

---

## C) Field-level mismatches and assumptions

Conversations (migrations)
- Columns: project_id, homeowner_id, contractor_id, last_message_at
- Code often uses conversations linked to bid_card_id (not project_id) and augments message counts/unread flags
- Code expects last_message_at updates (consistent) and often derives homeowner_id from bid_cards

Messaging
- Code assumes message_attachments, content_filtered flag, metadata with agent decisions and comments count
- Migrations’ messages table does not include filtered_content, content_filtered, metadata JSONB, or agent analysis details

Broadcasting
- Code references broadcast_messages and broadcast_read_receipts for messaging campaigns/broadcasts
- No broadcast_* tables in migrations

Payments/Fees
- connection_fees used heavily in code with statuses, relationships to bid_cards, referral payouts
- Migrations include payments (project/bid oriented) but no connection_fees or referral_tracking

Admin
- admin_users/admin_sessions/admin_activity_log used for admin auth/logging in several modules
- Not present in migrations

Property API
- property_api endpoints expect properties, rooms, assets, photos tables
- Not present in migrations

Proposed action
- Decide whether to:
  - Extend current migrations to match code reality (add missing columns/tables), OR
  - Converge code onto simpler canonical schema (e.g., messages/conversations) and deprecate the bespoke tables

---

## D) Recommended reconciliation plan

1) Pick canonical domain:
   - Option A (Code-first): Adopt bid_cards/messaging_system_messages/etc. → Write full migrations for all “missing in migrations” tables (see section A).
   - Option B (Schema-first): Adopt projects/messages/conversations/payments → Systematically refactor routers/services to map bid_card concepts to projects; replace messaging_system_messages with messages; add only minimal columns needed (filtered_content, metadata) to messages.

2) Draft migration set (if Option A):
   - Create tables:
     - bid_cards (with homeowner_id, token, project_type, status, metadata, created_at/updated_at)
     - messaging_system_messages (conversation_id, sender_type, sender_id, original_content, filtered_content, content_filtered, message_type, metadata JSONB, is_read, created_at)
     - message_attachments (message_id, type, url, name, size, analyzed_by_agent, analysis_result JSONB)
     - blocked_messages_log (bid_card_id, sender_type, sender_id, original_content, threats_detected JSONB, agent_decision, confidence_score, blocked_at, metadata JSONB)
     - agent_comments (message_id, visible_to_type, visible_to_id, content, type, timestamp, resolved, homeowner_response, metadata JSONB)
     - broadcast_messages, broadcast_read_receipts
     - connection_fees (id, bid_card_id, contractor_id, amounts, status, timestamps, metadata)
     - outreach_campaigns, campaign_contractors, campaign_check_ins, contractor_outreach_attempts
     - referral_tracking, notifications
     - admin_users, admin_sessions, admin_activity_log
     - properties, rooms, property_assets, property_photos
   - Add RLS aligned with code expectations.

3) Indexes
   - Use docs/meta/SchemaERD.md “Recommended Indexes” for existing tables
   - Generate supabase/sql/index_recommendations.sql for both existing and new tables

4) Iterative cutover
   - For each module group (Messaging, COIA/CIA, Bid Cards, Fees, Admin, Property):
     - Wire tests to the new/updated schema
     - Backfill/seed where necessary
     - Remove dead code paths to legacy tables

---

## E) Risk notes

- Maintaining two parallel domain models (projects/bids vs bid_cards/contractor_bids) will increase complexity and break test-first guarantees.
- Unified schema is essential to support your “never claim success without real proof” requirement across API, DB, and UI.

---

## F) Decision needed

Please confirm preferred direction:
- Option A (Code-first): migrate DB to match code (likely fastest for immediate E2E testing)
- Option B (Schema-first): refactor code to match existing migrations (leaner schema, larger code rewrite)

Once confirmed, I will:
- Generate the concrete migration files for the chosen path
- Fill supabase/sql/index_recommendations.sql with the needed indexes
- Update DataFlow.md and ERD accordingly
