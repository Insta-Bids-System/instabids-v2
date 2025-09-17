# Photo Storage and Data Flow Map

Scope: Complete map of where photos/files are saved, which buckets are used, which endpoints/services write them, and how they connect to database tables in Instabids.

Last verified: 2025-08-12

---

## Buckets

- project-images (public)
  - Purpose: Conversation images, bid card project photos, contractor proposal attachments, intelligent messaging uploads.
  - Access: Public URL via get_public_url; no signed URL flow currently enforced.

- iris-images (public)
  - Purpose: IRIS/inspiration/vision images persisted from temporary (e.g., OpenAI) links.
  - Creation: Auto-created as public if missing by ImagePersistenceService.
  - Access: Public URL via get_public_url.

---

## Write Paths and Endpoints/Services

1) Conversation images (user messaging)
- Endpoint: POST /api/images/upload/conversation
  - File: ai-agents/routers/image_upload_api.py
- Bucket path:
  - project-images/conversations/{conversation_id}/{timestamp}_{uuid}.{ext}
- DB writes:
  - messaging_system_messages: insert message with attachments: [{ url, type=image/*, name, size }]
  - conversations: update unread counts and last_message_at
- Delete:
  - DELETE /api/images/{image_path} → removes file from storage (project-images) only; DB references are not scrubbed.

2) Bid card project photos
- Endpoint: POST /api/images/upload/bid-card
  - File: ai-agents/routers/image_upload_api.py
- Bucket path:
  - project-images/bid-cards/{bid_card_id}/{timestamp}_{uuid}.{ext}
- DB writes:
  - bid_cards.bid_document.images (JSON array) ← appended with:
    - { url, description, uploaded_by, uploaded_by_type, uploaded_at }

3) Contractor proposal attachments (documents and images)
- Endpoint: POST /api/contractor-proposals/upload-attachment
  - File: ai-agents/routers/contractor_proposals_api.py
- Bucket path:
  - project-images/proposals/{proposal_id}/{timestamp}_{original_filename}
- DB writes:
  - contractor_proposals.attachments (JSON array) ← appended with:
    - { name, url, type, size, uploaded_at }
- MIME: Accepts PDFs, Office docs, and common images.

4) Intelligent messaging (with image)
- Endpoint: POST /api/intelligent-messages/send-with-image
  - File: ai-agents/routers/intelligent_messaging_api.py
  - Helper: upload_file_to_storage(...)
- Bucket path:
  - project-images/intelligent_messages/{timestamp}_{uuid}_{file_name}
- DB writes (if agent approves):
  - messaging_system_messages: message saved
  - message_attachments: normalized image record:
    - { message_id, type="image", url, name, size, analyzed_by_agent, analysis_result }
- If blocked by the agent: upload is skipped; blocked_messages_log records details.

5) IRIS/inspiration persistent storage (AI-generated images)
- Service: ai-agents/services/image_persistence_service.py (ImagePersistenceService)
- Bucket:
  - iris-images (created public if missing)
- Bucket path:
  - iris_visions/{timestamp}_{image_id}.{ext}
- Flow:
  - Downloads temporary (e.g., DALL·E) URLs and persists them in iris-images
  - Updates inspiration_images.image_url and thumbnail_url
  - fix_all_expired_images() batch-migrates temp links → permanent URLs

---

## Read/Retrieval

- Conversation images (legacy)
  - Endpoint: GET /api/images/conversation/{conversation_id}
    - File: ai-agents/routers/image_upload_api.py
    - Reads from messages with attachments (legacy table).
    - Note: Writer now uses messaging_system_messages, so legacy reader will miss new images (mismatch).

- Bid card images
  - Endpoint: GET /api/images/bid-card/{bid_card_id}
    - Reads bid_cards.bid_document.images JSON list.

- Intelligent messaging
  - Images referenced from message_attachments and messaging_system_messages.attachments.

---

## Database Tables Touched

- messaging_system_messages
  - Fields: original_content, filtered_content, is_read, message_type, attachments (array)
  - Triggers: after-insert triggers update conversation last_message_at/unread counts.

- conversations
  - Unread counter fields, last_message_at.

- bid_cards
  - JSON field: bid_document.images (embedded metadata of project photos).

- contractor_proposals
  - JSON field: attachments (mixed docs/images).

- message_attachments
  - Normalized attachment table used by intelligent messaging with image.

- inspiration_images
  - Updated by ImagePersistenceService with permanent iris-images URLs.

---

## Storage API Usage Patterns

- project-images:
  - db.client.storage.from_("project-images").upload(...)
  - .get_public_url(...)
  - .remove([...])

- iris-images:
  - supabase.storage.from_("iris-images").upload(...)
  - .get_public_url(...)

Additional bucket usage patterns through abstraction:
- intelligent_messaging_api.py, messaging_simple.py, messaging_fixed.py use db.storage.from_(bucket).get_public_url(...)

---

## Policies/Triggers (For Awareness)

- Triggers:
  - messages, messaging_system_messages: AFTER INSERT update unread counters; update_conversation_last_message
- RLS (selected):
  - inspiration_* tables have demo homeowner allowances; general tables open to authenticated role per pg_policies snapshot.

Refer to docs/meta/db/public_policies.json and docs/meta/db/public_triggers.json for complete details.

---

## Inconsistencies / Risks

- Reader/Writer mismatch:
  - Writer: /api/images/upload/conversation → messaging_system_messages
  - Reader: GET /api/images/conversation/{id} → legacy messages table
  - Impact: New conversation images won’t appear in legacy reader.

- Orphaned references on delete:
  - DELETE endpoint removes file from storage only; references remain in:
    - messaging_system_messages.attachments
    - bid_cards.bid_document.images
    - contractor_proposals.attachments

- Public buckets:
  - project-images and iris-images are public; if stricter privacy required, consider signed URLs/private buckets + storage policies.

- Attachments duplication:
  - message_attachments used by intelligent messaging; unified_message_attachments exists per docs and schema — consolidation recommended.

---

## Recommendations

1) Unify conversation image retrieval to read from messaging_system_messages (and message_attachments) rather than legacy messages.
2) Implement a reference cleanup on delete: remove storage object and scrub all DB references.
3) Consider migration to signed URLs/private buckets if privacy needs increase.
4) Consolidate attachment storage pattern:
   - Prefer normalized attachment tables (message_attachments or unified_message_attachments) over embedded JSON arrays, or add a background process to mirror embedded lists into a normalized table.

---

## Quick Reference Table

| Source | Endpoint/Service | Bucket | Path Template | DB Tables/Columns | Notes |
|-------|-------------------|--------|---------------|-------------------|-------|
| Conversation image | POST /api/images/upload/conversation | project-images | conversations/{conversation_id}/{ts}_{uuid}.{ext} | messaging_system_messages.attachments; conversations | Legacy reader mismatch |
| Bid card photo | POST /api/images/upload/bid-card | project-images | bid-cards/{bid_card_id}/{ts}_{uuid}.{ext} | bid_cards.bid_document.images | Embedded JSON list |
| Proposal attachment | POST /api/contractor-proposals/upload-attachment | project-images | proposals/{proposal_id}/{ts}_{filename} | contractor_proposals.attachments | Docs + images |
| Intelligent message image | POST /api/intelligent-messages/send-with-image | project-images | intelligent_messages/{ts}_{uuid}_{file} | messaging_system_messages; message_attachments | Agent approval gate |
| IRIS persistent vision | ImagePersistenceService | iris-images | iris_visions/{ts}_{image_id}.{ext} | inspiration_images.(image_url, thumbnail_url) | Converts temp → permanent |
