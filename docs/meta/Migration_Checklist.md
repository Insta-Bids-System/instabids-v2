# Unified Messaging/Image Migration Checklist (Actionable)

Goal: Eliminate legacy messaging/image paths and make ALL agents + APIs consistently use:
- unified_conversations
- unified_messages
- unified_conversation_memory
- unified_message_attachments
- Storage buckets: project-images (conversation media) and iris-images (long-term inspiration)

This checklist lists exact files to change, what to replace, and the target code shapes.

Last updated: 2025-08-12

---

## 0) High-signal deltas (fix these first)

1) ai-agents/routers/intelligent_messaging_api.py
- Current:
  - send_with_image:
    - Uploads image to project-images
    - Saves message via Unified API (GOOD)
    - Inserts image into message_attachments (legacy, non-unified)
  - resolve_conversation_id: uses legacy conversations table
  - Several endpoints still reference legacy conversations/messages in joins
- Change:
  - Replace message_attachments insert with unified_message_attachments insert:
    - supabase.table("unified_message_attachments").insert({
        "message_id": <returned unified message id>,
        "type": "image",
        "url": <bucket URL>,
        "name": <filename>,
        "size": <bytes>,
        "metadata": {"source": "intelligent_messaging", "analyzed_by_agent": True, "analysis_result": agent_result.get("image_analysis", {})}
      })
  - Keep resolve_conversation_id short term (uses conversations) only to identify the conversation id used by the Unified API. Medium-term: add a small resolver for unified_conversations by session_id or map conversations → unified_conversations id.
  - Replace any remaining reads from legacy messages with unified_messages (+ unified_message_attachments join).

2) ai-agents/agents/cia/agent.py (homeowner agent)
- Current:
  - Stores base64 images directly to photo_storage (DB) and puts “photo_id:…” into state
  - Does not upload to bucket or create unified_message_attachments
  - Saves text to unified_conversations/unified_messages (GOOD)
- Change:
  - Remove photo_storage writes. For each base64 image:
    - Upload to project-images path: unified/{conversation_id}/{timestamp}_{uuid}_{filename}
    - Insert unified_message_attachments referencing the unified_messages row for that user turn
  - Add helpers:
    - _ensure_unified_conversation(user_id, session_id) → conversation_id
    - _save_unified_message(conversation_id, sender_type, sender_id, content, metadata) → message_id
    - _upload_and_attach_images(conversation_id, message_id, images[]) → urls
  - Guard against double-insert: if we saved the user message early (to attach images), don’t reinsert same message in _save_to_unified_conversations().

3) ai-agents/api/iris_chat_unified_fixed.py (IRIS)
- Current:
  - Correct unified text + memory writes (GOOD)
  - Conversation images aren’t consistently normalized as unified_message_attachments
  - Long-term inspiration persistence goes to iris-images + inspiration_images (GOOD)
- Change:
  - When an image is part of the chat turn:
    - If generated/curated inspiration: persist (iris-images) and update inspiration_images (as today)
    - ALSO insert unified_message_attachments with the iris-images URL for the message that references it
  - If user uploads an image to the IRIS conversation: upload to project-images/unified/{conversation_id}/... and insert unified_message_attachments

---

## 1) Legacy image endpoints (unify or mirror)

File: ai-agents/routers/image_upload_api.py
- Current:
  - /upload/conversation → messaging_system_messages (attachments JSON) and legacy reader enumerates from messages
  - /upload/bid-card → bid_cards.bid_document.images (embedded JSON)
  - DELETE removes storage only (no DB reference cleanup)
- Change:
  - For conversation images:
    - Write to unified_messages via Unified API (text “Shared an image: …”)
    - Insert unified_message_attachments for each image
    - Optional: temporary mirror into messaging_system_messages if old UI still needs it (plan to remove)
  - For bid card photos:
    - Keep embedded JSON for now OR move to a normalized table later (see AttachmentMatrix)
    - Add validator/cleanup script to detect orphaned storage refs
  - Update reader endpoints to get conversation images from unified_message_attachments (not legacy messages)

---

## 2) Messaging routers still on legacy

Files:
- ai-agents/routers/messaging_api.py
- ai-agents/routers/messaging_simple.py
- ai-agents/routers/messaging_fixed.py
- ai-agents/routers/bid_card_api.py (message counts, bid_card_messages)
- ai-agents/routers/bid_card_lifecycle_routes.py (legacy message lookups)

Action:
- Replace inserts/reads of legacy messages with unified API or direct unified_* tables
- Conversations: prefer unified_conversations; if not possible immediately, keep using conversations only to locate the conversation_id consumed by the Unified API, while unified_messages becomes the source of truth

---

## 3) Attachment consolidation

- Stop writing to:
  - message_attachments (non-unified table)
  - messaging_system_messages.attachments (embedded JSON)
  - contractor_proposals.attachments (embedded JSON) — keep temporarily but plan a normalized per-scope attachment table or “attachments + attachment_links”
- Start writing:
  - unified_message_attachments for all conversation media across agents
- Migration (background job):
  - Convert old message_attachments rows to unified_message_attachments when a corresponding unified_messages entry exists
  - Optionally normalize bid_cards.bid_document.images into a bid_card_images table or generic attachments + links model

---

## 4) Specific code snippets to replace (guide)

A) intelligent_messaging_api.py (send_with_image)
- Replace:
  db.table("message_attachments").insert(attachment_data).execute()
- With:
  supabase = database_simple.get_client()
  supabase.table("unified_message_attachments").insert({
      "message_id": message_id,
      "type": "image",
      "url": image_url,
      "name": image.filename or "image.jpg",
      "size": len(image_data),
      "metadata": {"source":"intelligent_messaging","analyzed_by_agent":True,"analysis_result": agent_result.get("image_analysis", {})}
  }).execute()

B) CIA image block (photo_storage removal)
- Replace the photo_storage insert loop with:
  conversation_id = await self._ensure_unified_conversation(user_id, session_id)
  msg_id = await self._save_unified_message(
      conversation_id, "user", user_uuid, message or "", {"agent":"CIA","has_images": bool(images)}
  )
  urls = await self._upload_and_attach_images(conversation_id, msg_id, images)

C) IRIS attach (after generating/persisting an image)
- After you have persistent_url (iris-images) or freshly uploaded project-images URL:
  supabase.table("unified_message_attachments").insert({
    "message_id": agent_msg_id,
    "type": "image",
    "url": persistent_url,
    "name": img_name,
    "size": img_size,
    "metadata": {"source":"IRIS","inspiration": True}
  }).execute()

---

## 5) Readers/adapters

- Ensure adapters render attachments from unified_message_attachments joined to unified_messages
- Avoid legacy reads:
  - messaging_system_messages
  - messages (legacy)
  - embedded JSON arrays except in bid_card gallery contexts

---

## 6) Tests to run (already present in repo)

- test_unified_image_system_complete.py — end-to-end unified image pipeline
- test_cia_unified_images.py — CIA uploads create unified_message_attachments and bucket files
- test_messages_with_attachments_api.py — API returns unified attachments for a conversation
- test_messaging_agent_unified.py — verifies unified agent message path
- test_frontend_unified_complete.py — UI reads from unified model
- IRIS: test_iris_* where images flow through conversations; add asserts on unified_message_attachments

---

## 7) Order of operations (safe, incremental)

1) Change intelligent_messaging_api.py (stop writing message_attachments; write unified_message_attachments)
2) Fix CIA to upload to project-images + unified_message_attachments (remove photo_storage)
3) Add IRIS unified attachments for conversation images
4) Update adapters/readers to unified attachments
5) (Optional) Add normalizer job for embedded JSON → normalized table
6) Remove legacy reads and stop mirroring
7) Drop legacy tables only when code + tests no longer reference them

---

## 8) Known blockers and mitigations

- Mode flips interrupted my scans earlier. This checklist is written from inspected code and prior mapping to let your team proceed even without automated grep output.
- If buckets move to private, replace get_public_url with signed URL creation and update clients accordingly.

---

## 9) Reference maps

- docs/meta/PhotoMap.md — buckets, endpoints, DB touches, risks
- docs/meta/UnifiedMemoryMap.md — unified tables, producers/consumers, join keys
- docs/meta/AttachmentMatrix.md — attachment flows and consolidation plan
