-- InstaBids Index Recommendations
-- Safe to run multiple times (IF NOT EXISTS). Targets only tables present in migrations.
-- Source: docs/meta/SchemaERD.md and code access patterns.

-- Conversations: frequently filtered by project/homeowner/contractor and sorted by activity.
CREATE INDEX IF NOT EXISTS idx_conversations_project_id
  ON public.conversations(project_id);
CREATE INDEX IF NOT EXISTS idx_conversations_homeowner_id
  ON public.conversations(homeowner_id);
CREATE INDEX IF NOT EXISTS idx_conversations_contractor_id
  ON public.conversations(contractor_id);
CREATE INDEX IF NOT EXISTS idx_conversations_last_message_at
  ON public.conversations(last_message_at);

-- Messages: timeline queries within a conversation benefit from composite index.
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id_created_at_desc
  ON public.messages(conversation_id, created_at DESC);

-- Payments: filtered by relationships and status; common for dashboards and lookups.
CREATE INDEX IF NOT EXISTS idx_payments_project_id
  ON public.payments(project_id);
CREATE INDEX IF NOT EXISTS idx_payments_bid_id
  ON public.payments(bid_id);
CREATE INDEX IF NOT EXISTS idx_payments_payer_id
  ON public.payments(payer_id);
CREATE INDEX IF NOT EXISTS idx_payments_recipient_contractor_id
  ON public.payments(recipient_contractor_id);
CREATE INDEX IF NOT EXISTS idx_payments_status
  ON public.payments(status);

-- Contractor discovery cache: cleanup and retrieval by expiry.
CREATE INDEX IF NOT EXISTS idx_contractor_discovery_cache_expires_at
  ON public.contractor_discovery_cache(expires_at);

-- Reviews: retrieval by contractor/project/user.
CREATE INDEX IF NOT EXISTS idx_reviews_contractor_id
  ON public.reviews(contractor_id);
CREATE INDEX IF NOT EXISTS idx_reviews_project_id
  ON public.reviews(project_id);
CREATE INDEX IF NOT EXISTS idx_reviews_reviewer_id
  ON public.reviews(reviewer_id);

-- Existing indexes (from initial migration) for reference:
-- profiles(role)
-- contractors(verified), contractors USING GIN(service_areas), contractors USING GIN(specialties)
-- projects(homeowner_id), projects(status)
-- bids(project_id), bids(contractor_id), bids(status)
-- messages(conversation_id), messages(created_at)
-- ai_conversations(user_id), ai_conversations(thread_id)

-- Optional: If the project adopts the "code-first" schema (see docs/meta/SchemaDrift.md Option A),
-- add indexes for those new tables after their migrations are created.
-- Example (COMMENTED OUT - do not run until tables exist):
/*
CREATE INDEX IF NOT EXISTS idx_messaging_system_messages_conversation_created
  ON public.messaging_system_messages(conversation_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_blocked_messages_log_bid_card_blocked_at
  ON public.blocked_messages_log(bid_card_id, blocked_at DESC);

CREATE INDEX IF NOT EXISTS idx_message_attachments_message_id
  ON public.message_attachments(message_id);

CREATE INDEX IF NOT EXISTS idx_bid_cards_homeowner_status
  ON public.bid_cards(homeowner_id, status);

CREATE INDEX IF NOT EXISTS idx_connection_fees_contractor_status
  ON public.connection_fees(contractor_id, status);
*/
