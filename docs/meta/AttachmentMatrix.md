# Attachment Matrix and Consolidation Plan

Scope: Canonical mapping of where attachments (images/files) are stored and referenced across the system, with a consolidation plan toward a single unified attachment model.

Last verified: 2025-08-12

---

## Current Attachment Sources

| Source / Flow | Endpoint / Service | Bucket / Storage | Storage Path | DB Write Location | Schema Type | Notes |
|---|---|---|---|---|---|---|
| Conversation image (user messaging) | POST /api/images/upload/conversation | project-images | conversations/{conversation_id}/{ts}_{uuid}.{ext} | messaging_system_messages.attachments (array) | Embedded JSON | Triggers update unread/last_message_at; delete only removes storage file |
| Bid card project photo | POST /api/images/upload/bid-card | project-images | bid-cards/{bid_card_id}/{ts}_{uuid}.{ext} | bid_cards.bid_document.images (array) | Embedded JSON | Embedded metadata; no normalized rows |
| Contractor proposal attachment | POST /api/contractor-proposals/upload-attachment | project-images | proposals/{proposal_id}/{ts}_{filename} | contractor_proposals.attachments (array) | Embedded JSON | Accepts docs/images; public URL |
| Intelligent message image (approved) | POST /api/intelligent-messages/send-with-image | project-images | intelligent_messages/{ts}_{uuid}_{filename} | message_attachments (rows); messaging_system_messages row | Normalized + message row | Image is normalized in message_attachments; message row is in messaging_system_messages |
| IRIS inspiration / vision image (persistence) | ImagePersistenceService | iris-images | iris_visions/{ts}_{image_id}.{ext} | inspiration_images.(image_url, thumbnail_url) | Columns | Converts temp URLs to permanent |

---

## Attachment Tables (DB)

- message_attachments (in-use)
  - Columns: id, message_id (FK→ messaging_system_messages.id), type, url, name, size, analyzed_by_agent, analysis_result, created_at
  - Producers: intelligent_messaging_api when image approved
  - Pros: Normalized, easy to query, easy to enforce cleanup
  - Cons: Not the “unified” table used by unified_messages

- unified_message_attachments (documented, target)
  - Intended FK: message_id (FK→ unified_messages.id)
  - Pros: Aligns to unified_* stack (CIA/IRIS/COIA)
  - Cons: Not currently written by the main intelligent messaging path

- Embedded JSON arrays
  - messaging_system_messages.attachments
  - bid_cards.bid_document.images
  - contractor_proposals.attachments
  - Pros: Easy to append small metadata
  - Cons: Hard to search, dedupe, enforce referential integrity, or clean up on storage delete

---

## Inconsistencies and Risks

1) Parallel attachment models
- Non-unified normalized table (message_attachments) vs unified target (unified_message_attachments).
- Embedded arrays mixed with normalized rows.

2) Delete orphaning
- Storage DELETE call (image_upload_api.py) removes the object but does not scrub JSON arrays or normalized attachments referencing it.

3) Reader/writer mismatch for conversation images
- Writer: messaging_system_messages
- Reader endpoint GET /api/images/conversation/{id}: queries legacy messages instead of messaging_system_messages → newly saved images can be invisible.

---

## Consolidation Plan (Phased)

Phase 1: Read-path unification (safe, no data moves)
- Update APIs/UI readers to:
  - Prefer normalized attachments where they exist (message_attachments and later unified_message_attachments).
  - When reading conversation images, pull from:
    - messaging_system_messages.attachments (JSON array) AND
    - message_attachments (joined on message id) AND
    - unified_message_attachments (future)

Phase 2: Normalization for new writes
- For new conversation/media writes:
  - If writing into messaging_system_messages, also write a row in message_attachments (current behavior for intelligent messaging).
  - For unified conversations, write to unified_message_attachments when the message lives in unified_messages.

Phase 3: Migration of legacy embedded JSON → normalized rows
- Transform embedded arrays into normalized rows:
  - For each item in messaging_system_messages.attachments:
    - INSERT INTO message_attachments (message_id, type, url, name, size, metadata)
  - For bid_cards.bid_document.images:
    - Consider creating a dedicated table (bid_card_images) or reuse a generic attachments table with a polymorphic reference:
      - attachment_links: { id, scope_type, scope_id, attachment_id } (scope_type = 'bid_card', scope_id = bid_card_id)
    - Alternatively, keep embedded JSON but add a background validator that ensures storage reference is valid.

Phase 4: Unified target adoption
- For agents using unified_messages, write attachments to unified_message_attachments only.
- Optionally mirror message_attachments → unified_message_attachments where the same logical message exists in unified_messages.

---

## Proposed Schemas (if introducing a general attachment table)

A) Keep specialized attachment tables per domain (current pattern):
- message_attachments (conversation messages)
- unified_message_attachments (unified messages)
- (Optional) bid_card_images (bid card project photos)
- (Optional) proposal_attachments (if normalized)

B) Or introduce a generic attachments table with scope links:
- attachments: { id, url, type, name, size, metadata, created_at }
- attachment_links: { id, scope_type, scope_id, message_id (nullable), created_at }
  - Pros: Searchability, dedupe, easy cleanup
  - Cons: Requires link logic; migration complexity

---

## Cleanup Strategy (Orphan and Reference Hygiene)

- Orphan detector (background job or script):
  - List storage objects under project-images/* and iris-images/*.
  - Cross-check against:
    - message_attachments.url
    - unified_message_attachments.url
    - messaging_system_messages.attachments[].url
    - bid_cards.bid_document.images[].url
    - contractor_proposals.attachments[].url
  - Report:
    - Storage-only files (no DB references)
    - DB references pointing to missing storage objects

- Safe deletion flow (future):
  - API to “delete attachment”:
    - Transactionally remove rows/references first
    - Then remove storage file
    - If storage removal fails, retry with compensating logic
  - For embedded JSON, rewrite JSON without the deleted object entry.

---

## Minimal Migration Checklist

1) Add readers that include both normalized rows and JSON arrays.
2) For new unified messages: write unified_message_attachments rows.
3) Add a scheduled job:
   - Move messaging_system_messages.attachments → message_attachments (idempotent)
   - Validate rows against storage; log anomalies
4) (Optional) Normalize bid_card images and proposal attachments into separate tables or a generic attachments + links model.
5) Add “delete attachment” endpoint that:
   - Accepts {scope, ids, url}
   - Scrubs DB references then removes storage.

---

## References (Code + Docs)

- messaging attachments
  - ai-agents/routers/intelligent_messaging_api.py (send-with-image logic)
  - ai-agents/agents/intelligent_messaging_agent.py (filtering + approval)
- legacy image upload
  - ai-agents/routers/image_upload_api.py (conversation / bid-card)
  - ai-agents/routers/contractor_proposals_api.py (proposal attachments)
- unified system
  - ai-agents/routers/unified_conversation_api.py
  - ai-agents/agents/cia/agent.py
  - ai-agents/api/iris_chat_unified_fixed.py
  - ai-agents/agents/coia/persistent_memory.py
- IRIS image persistence
  - ai-agents/services/image_persistence_service.py
- documentation
  - docs/meta/PhotoMap.md
  - docs/meta/UnifiedMemoryMap.md
  - ai-agents/CROSS_AGENT_LOGIC_DOCUMENTATION.md
  - UNIFIED_CONVERSATION_MIGRATION_PLAN.md
