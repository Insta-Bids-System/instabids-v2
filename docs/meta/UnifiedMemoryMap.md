# Unified Conversation + Memory: End-to-End Map

Scope: Authoritative map of the unified conversation system (data model, producers/consumers, attachment strategy, privacy hooks), tying backend code and existing docs together.

Last verified: 2025-08-12

---

## Core Tables (Public Schema)

1) unified_conversations
- Purpose: Root record per conversation/session across agents (CIA, IRIS, COIA, Messaging).
- Common columns used by code:
  - id (uuid, PK)
  - created_by (uuid) – owner/creator (homeowner/contractor)
  - last_message_at (timestamptz) – updated by writers
  - metadata (jsonb) – frequently includes:
    - session_id (string) ← cross-agent join key
    - agent_type (string) ← "CIA" / "IRIS" / "COIA" / etc.
    - conversation_type, context_id (optional)
  - updated_at/created_at
- Relationships:
  - 1 → many unified_messages (FK: conversation_id)
  - 1 → many unified_conversation_memory (FK: conversation_id)
  - 1 → many unified_conversation_participants (FK: conversation_id)

2) unified_messages
- Purpose: All message content (user/agent/system) with metadata.
- Common columns used by code:
  - id (uuid, PK)
  - conversation_id (uuid, FK → unified_conversations.id)
  - sender_type ("user" | "agent" | "system")
  - sender_id (uuid/string)
  - content (text/json depending on producer)
  - metadata (jsonb) – includes message_type e.g., "bid_submission"
  - parent_id (nullable FK → unified_messages.id) – threading
  - created_at
- Indexes/Constraints: conversation FK, parent FK (see docs/meta/db/public_foreign_keys.json)

3) unified_conversation_memory
- Purpose: Cross-agent shared facts/preferences/state derived from messages or external flows.
- Common columns used by code:
  - id (uuid, PK)
  - conversation_id (uuid, FK → unified_conversations.id)
  - memory_key (text) – optional tag (e.g., "design_preferences", "coia_conversation_state")
  - memory_value (jsonb) – arbitrary structured state
  - updated_at/created_at
- Behavior in code:
  - Upsert/update pattern when memory exists for conversation_id
  - Store IRIS preferences (design context), COIA persistent state, CIA context summaries

4) unified_conversation_participants
- Purpose: Multi-party membership + read tracking.
- Common columns used by code/docs:
  - id (uuid, PK)
  - conversation_id (uuid, FK)
  - participant_id (uuid)
  - last_read_cursor (uuid, FK → unified_messages.id)
  - joined_at
- Used by: read/unread logic for unified UX (adapters)

5) unified_message_attachments (documented target)
- Purpose: Normalized attachments associated with unified_messages.
- Columns:
  - id (uuid, PK)
  - message_id (uuid, FK → unified_messages.id)
  - type (e.g., "image", "pdf")
  - url, name, size, metadata (jsonb)
- Note: Current intelligent messaging router writes to message_attachments (non-unified table). See AttachmentMatrix for consolidation plan.

Related/adjacent:
- user_memories (documented as global, not per-conversation)
- blocked_messages_log (security audit)
- conversations / messaging_system_messages (legacy/parallel messaging stack)

References:
- FKs: docs/meta/db/public_foreign_keys.json
- Indexes: docs/meta/db/public_indexes.json
- Catalog: docs/meta/DBCatalog.json

---

## Data Producers (Who writes)

- CIA agent (ai-agents/agents/cia/agent.py)
  - Creates/updates unified_conversations by metadata->>session_id
  - Inserts unified_messages (user/assistant/system) with rich metadata
  - Inserts/updates unified_conversation_memory (state and extracted facts)
  - Queries unified_messages for "bid_submission" via metadata filter

- IRIS flows
  - api/iris_chat_unified_fixed.py and docs/actual-agents/IRIS-DesignInspirationAssistant.md
  - Creates unified_conversations; writes user + agent messages into unified_messages
  - Persists design preferences into unified_conversation_memory
  - Uses session_id in metadata for cross-agent join

- COIA (Contractor Onboarding/Intelligence)
  - agents/coia/persistent_memory.py, agents/coia/unified_graph.py, routers/coia_api.py
  - Ensures unified_conversations for session; saves messages to unified_messages
  - Persists onboarding/state into unified_conversation_memory

- Unified Conversation API (ai-agents/routers/unified_conversation_api.py)
  - Direct API endpoints to create/read conversations/messages/memory
  - Used by tests and cross-agent adapters

- Intelligent Messaging Agent (ai-agents/routers/intelligent_messaging_api.py + agents/intelligent_messaging_agent.py)
  - Primary write path today uses messaging_system_messages (security-gated)
  - Normalized image attachments go to message_attachments (not unified)
  - Some flows log into unified_messages in the agent layer for analytics (see references)

---

## Data Consumers (Who reads)

- Adapters (cross-agent context assembly)
  - ai-agents/adapters/messaging_context.py
  - ai-agents/adapters/homeowner_context.py
  - ai-agents/adapters/contractor_context.py
  - Pattern: Query unified_conversations by created_by or session_id; aggregate unified_messages and memory into a privacy-filtered context dictionary

- Services and tests
  - ai-agents/services/context_policy.py – describes intended use of unified tables
  - Widespread tests confirm unified_* activity:
    - test_cia_unified_final.py, test_real_homeowner_full_workflow.py, test_three_agents_cross_sharing.py, test_coia_100_percent_verified.py, test_bid_submission_context_all_agents.py, check_unified_tables.py, etc.

- Docs asserting canonical use:
  - CROSS_AGENT_LOGIC_DOCUMENTATION.md
  - IRIS/HOMEOWNER unified integration documentation
  - UNIFIED_CONVERSATION_MIGRATION_PLAN.md

---

## Identity & Join Keys

- metadata->>session_id (string)
  - Most common cross-agent join used to locate/continue a conversation
  - Heavily used by CIA/IRIS/COIA code paths
  - Recommendation: Add a partial index on (metadata->>session_id) if high cardinality usage persists

- created_by (uuid)
  - Used in adapters to list all unified_conversations for a user
  - Combined with participants for shared-access scenarios

- conversation_id
  - Primary key for message/memory joins
  - last_message_at updated by writers; participants.last_read_cursor tracks unread

---

## Attachments Strategy (Images & Files)

Current state:
- Intelligent messaging (approved) → message_attachments (non-unified)
- Legacy conversation image writes → messaging_system_messages.attachments (embedded JSON array)
- Unified target table exists: unified_message_attachments

Recommendation:
- Canonicalize on unified_message_attachments for conversation-related media
  - Mirror message_attachments → unified_message_attachments in a background migration job
  - Stop writing embedded arrays where possible; use normalized tables for searchability and clean deletes
- See docs/meta/AttachmentMatrix.md (to be generated alongside this map)

---

## Privacy / Policy “Rules” touchpoints

- Intelligent filter (agents/intelligent_messaging_agent.py + router)
  - Prevents PII/contact sharing; sets content_filtered; blocks when necessary
  - blocked_messages_log stores audits of blocked content

- RLS/Policies
  - public policies snapshot in docs/meta/db/public_policies.json
  - Many “authenticated allow all” patterns; demo homeowner UUID allowed for inspiration_* tables
  - Consider tightening for messaging artifacts if needed

- Triggers
  - messages / messaging_system_messages after-insert triggers (unread counts + last_message_at)
  - Unified tables rely on application logic to update last_message_at

---

## Known Gaps/Drift

- Parallel stacks:
  - messaging_system_messages vs unified_messages for “conversation”
  - Reader mismatch for conversation images (legacy endpoint reads from messages rather than messaging_system_messages)
- Attachment duplication:
  - message_attachments used in production flows; unified_message_attachments preferred per unified design
- Delete orphaning:
  - Storage deletes do not scrub DB attachment references

---

## Action Items / Acceptance Criteria

1) Reader unification:
  - Update conversation image retrieval to use messaging_system_messages (and/or unified_message_attachments), not legacy messages
2) Attachment consolidation:
  - Migrate message_attachments → unified_message_attachments
  - Introduce write path to unified_message_attachments for all new attachments
3) Storage reference hygiene:
  - “Delete” flow: remove storage object + remove all DB references in a single transaction (or reliable background job)
4) Index/session optimizations:
  - Add partial index on (metadata->>session_id) for unified_conversations if needed
5) Documentation invariants:
  - Photo map (docs/meta/PhotoMap.md) – now the single source of truth for buckets and paths
  - Attachment matrix (docs/meta/AttachmentMatrix.md) – to be used for consolidation/migration planning

---

## Verification Queries (Manual)

- Find latest unified conversations by session:
  SELECT id, metadata->>'session_id', last_message_at
  FROM unified_conversations
  WHERE metadata->>'session_id' IS NOT NULL
  ORDER BY last_message_at DESC
  LIMIT 20;

- Messages for a conversation:
  SELECT id, sender_type, created_at
  FROM unified_messages
  WHERE conversation_id = '<conv_id>'
  ORDER BY created_at;

- Memory records for a conversation:
  SELECT id, memory_key, updated_at
  FROM unified_conversation_memory
  WHERE conversation_id = '<conv_id>'
  ORDER BY updated_at DESC;

- Attachments for a unified message (post-consolidation):
  SELECT *
  FROM unified_message_attachments
  WHERE message_id = '<message_id>';

---

## Files/Paths Referenced

- Producers
  - ai-agents/agents/cia/agent.py
  - ai-agents/api/iris_chat_unified_fixed.py
  - ai-agents/agents/coia/persistent_memory.py
  - ai-agents/routers/unified_conversation_api.py
  - ai-agents/agents/intelligent_messaging_agent.py (security filter core)

- Adapters/Consumers
  - ai-agents/adapters/messaging_context.py
  - ai-agents/adapters/homeowner_context.py
  - ai-agents/adapters/contractor_context.py

- Photo storage map (buckets/paths)
  - docs/meta/PhotoMap.md

- Docs asserting unified system:
  - ai-agents/CROSS_AGENT_LOGIC_DOCUMENTATION.md
  - docs/HOMEOWNER_AGENT_UNIFIED_INTEGRATION_COMPLETE.md
  - docs/actual-agents/IRIS-DesignInspirationAssistant.md
  - UNIFIED_CONVERSATION_MIGRATION_PLAN.md
