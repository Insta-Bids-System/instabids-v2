# Agent Implementation Prompts: Unified Image Saving

Purpose: Give each responsible agent/team a copy/paste prompt that specifies exactly what to change so that ALL images are saved consistently into the unified messaging system with normalized attachments, while maintaining backward compatibility where needed.

Last updated: 2025-08-12

Global Goals (applies to all prompts)
- Every message that includes an image must:
  1) Create or reference a unified_conversations record (id, metadata->>session_id strongly recommended).
  2) Create a unified_messages row for the message text/metadata.
  3) Create a unified_message_attachments row for each image, FK → unified_messages.id.
  4) Store the file in a bucket (project-images or iris-images) and persist the public (or signed) URL in unified_message_attachments.url.
- Do NOT rely solely on embedded JSON arrays for images (e.g., messaging_system_messages.attachments, bid_cards.bid_document.images, contractor_proposals.attachments) for new writes. If you must write them for compatibility, also write the normalized unified_message_attachments row.
- If you currently write to messaging_system_messages/message_attachments, mirror to unified_* tables until the UI is migrated.

Required unified tables
- unified_conversations(id, created_by, last_message_at, metadata jsonb)
- unified_messages(id, conversation_id, sender_type, sender_id, content, metadata jsonb, created_at)
- unified_message_attachments(id, message_id, type, url, name, size, metadata jsonb, created_at)

Bucket conventions
- Use project-images for conversation images:
  - Path: unified/{conversation_id}/{timestamp}_{uuid}_{safe_filename}
- For IRIS inspiration/vision images, continue iris-images for persistence tasks, but when the image is part of a conversation, also create a unified_message_attachments row that references the conversation’s unified_messages record.

Security/policies
- Prefer service-role where RLS would block system writes.
- Buckets are currently public. If moving to private, switch to signed URLs and add necessary storage policies.

Verification
- After changes, run the verification queries in docs/meta/UnifiedMemoryMap.md and ensure each send-with-image flow produces rows in unified_messages + unified_message_attachments and that the storage file exists.

---

## Prompt 1 — Homeowner UX / Messaging (Intelligent Messaging System)

You are implementing image sending for homeowner/contractor conversations. Your task is to ensure every image is saved to the UNIFIED system with a normalized attachment. Keep legacy writes if necessary, but unified is the source of truth.

Acceptance criteria
- On image send:
  - Resolve/create unified_conversations (prefer metadata->>session_id).
  - Insert unified_messages for the message body (sender_type=user/agent, metadata includes any security flags).
  - Upload the image to project-images at unified/{conversation_id}/{ts}_{uuid}_{filename}.
  - Insert unified_message_attachments:
    - { message_id, type: "image", url, name, size, metadata: { analyzed_by_agent?:bool, analysis_result?:{} } }
- If you must still write messaging_system_messages/message_attachments for UI compatibility, ALSO write unified_* rows. The unified rows are mandatory.

Implementation notes
- Current endpoint: POST /api/intelligent-messages/send-with-image (ai-agents/routers/intelligent_messaging_api.py)
- Today it writes:
  - messaging_system_messages
  - message_attachments
- Change it to ALSO:
  - Create a unified_messages record for the same logical message
  - Create a unified_message_attachments record pointing to that unified message
- If agent blocks content, do NOT upload; log to blocked_messages_log as today.

Test steps
- Send a message with image through intelligent messaging.
- Expect:
  - unified_conversations row exists/updated (by session_id or created_by)
  - unified_messages row exists for this send
  - unified_message_attachments row created with the image URL
  - Storage path contains the file
- Confirm legacy paths continue to work if still needed, but UI should migrate reads to unified.

---

## Prompt 2 — CIA Agent (Contractor Intelligence Assistant)

You are responsible for contractor-focused conversational flows (CIA). Ensure that when a CIA flow generates or receives images (screenshots, attachments, visual confirmations), they are saved in the unified model.

Acceptance criteria
- For any CIA message with image intent:
  - Ensure unified_conversations exists, keyed by metadata->>session_id.
  - Insert unified_messages for the CIA/user message content (with metadata.message_type when relevant, e.g., "bid_submission").
  - Upload the image to project-images/unified/{conversation_id}/...
  - Insert unified_message_attachments with FK to unified_messages.id, capturing url/name/size/type.
- Do NOT rely on messaging_system_messages for CIA persistence; unified_* is canonical for CIA.

Implementation notes
- Primary files: ai-agents/agents/cia/agent.py (already writing unified_conversations/unified_messages/unified_conversation_memory)
- Add code path to persist image attachments to unified_message_attachments whenever CIA handles image payloads or inline content with image references.

Test steps
- Run CIA flows that mention or include images (e.g., submission/confirmation).
- Validate unified_messages and unified_message_attachments rows are created and linked; verify storage file presence.

---

## Prompt 3 — IRIS Agent (Design Inspiration/Room Vision)

IRIS manages inspiration images and design preferences. When images are part of a conversation or agent message, IRIS must store them in the unified attachment model in addition to (or separate from) long-term inspiration storage.

Acceptance criteria
- For conversation images produced/consumed in IRIS sessions:
  - Create/resolve unified_conversations via metadata->>session_id.
  - Insert unified_messages for user and agent turns.
  - Upload image to project-images/unified/{conversation_id}/...
  - Insert unified_message_attachments for the image URL.
- For long-term inspiration persistence:
  - Continue using ImagePersistenceService to persist to iris-images and update inspiration_images table.
  - When such an image is referenced in a conversation, ALSO create a unified_message_attachments row that points to the persisted iris-images URL.

Implementation notes
- Files:
  - ai-agents/api/iris_chat_unified_fixed.py
  - ai-agents/services/image_persistence_service.py (keep as-is for persistence)
- Add unified_message_attachments write when IRIS messages include images.

Test steps
- Execute IRIS chat that produces/uses images (vision compositions/inspiration).
- Verify:
  - unified_messages rows exist for both user and assistant
  - unified_message_attachments rows exist with image URLs
  - When ImagePersistenceService runs, inspiration_images updated; if the same image is referenced in chat, attachments are present in unified_message_attachments.

---

## Prompt 4 — COIA Agent (Contractor Onboarding/Intelligence)

COIA runs contractor onboarding and multi-step workflows that may include file/image uploads. Ensure these images are captured in unified attachments.

Acceptance criteria
- Any COIA flow that includes an image:
  - Resolve/create unified_conversations by session_id (metadata->>session_id).
  - Insert unified_messages for each step.
  - Upload image to project-images/unified/{conversation_id}/...
  - Insert unified_message_attachments with the image details.
- Avoid legacy-only writes; unified_* is the canonical store for COIA artifacts.

Implementation notes
- Files:
  - ai-agents/agents/coia/persistent_memory.py
  - ai-agents/agents/coia/unified_graph.py
  - ai-agents/routers/coia_api.py
- Ensure attachment writes target unified_message_attachments.

Test steps
- Run contractor onboarding or data capture flow including an image artifact.
- Confirm unified_messages + unified_message_attachments are created and linked.

---

## Optional Prompt 5 — Homeowner Legacy Endpoints (image_upload_api, proposals)

For legacy endpoints that currently write only embedded JSON (bid_cards, contractor_proposals) or messaging_system_messages.attachments:

Acceptance criteria
- Keep existing writes for backward compatibility.
- ALSO write unified rows:
  - Create/resolve unified_conversations (if a conversation context exists or can be inferred).
  - Insert unified_messages (capture basic metadata linking this upload to the context).
  - Insert unified_message_attachments for each image.
- If no conversation context exists (pure project asset), plan a separate normalized table (e.g., bid_card_images) or a generic attachments+links model.

Implementation notes
- Files:
  - ai-agents/routers/image_upload_api.py
  - ai-agents/routers/contractor_proposals_api.py
- Add unified mirror writes (messages + attachments) when requests have a conversation_id or enough info to anchor to a unified_conversations record.

---

## Shared Example (Pseudo-code)

```python
# given: conv_id (unified_conversations.id), db client, file bytes/name/type/size

# 1) Ensure unified_conversations exists (by session_id or created_by)
conv = supabase.table("unified_conversations").select("id").eq("id", conv_id).single().execute()

# 2) Insert unified_messages
msg_data = {
  "conversation_id": conv_id,
  "sender_type": sender_type,     # "user"/"agent"/"system"
  "sender_id": sender_id,
  "content": text_content,        # or ""
  "metadata": { "message_type": "image_share", **extra_meta }
}
msg = supabase.table("unified_messages").insert(msg_data).execute()
message_id = msg.data[0]["id"]

# 3) Store file to bucket
path = f"unified/{conv_id}/{timestamp}_{uuid}_{safe_filename}"
supabase.storage.from_("project-images").upload(path, file_bytes, {
  "content-type": mime,
  "upsert": False
})
url = supabase.storage.from_("project-images").get_public_url(path)

# 4) Insert unified_message_attachments
att = {
  "message_id": message_id,
  "type": "image",
  "url": url,
  "name": safe_filename,
  "size": file_size,
  "metadata": { "analyzed_by_agent": approved, "analysis_result": analysis or {} }
}
supabase.table("unified_message_attachments").insert(att).execute()
```

---

## Final Checklist (All Agents)

- [ ] Use unified_conversations (prefer metadata->>session_id); update last_message_at on new messages.
- [ ] Insert unified_messages for any message with or without image.
- [ ] Upload image to project-images/unified/{conversation_id}/... and write unified_message_attachments with FK to unified_messages.id.
- [ ] If legacy write is kept, also write unified_* mirror rows.
- [ ] Add tests that assert rows exist in unified_messages + unified_message_attachments and that storage files exist.
- [ ] Coordinate migration/cleanup per docs/meta/AttachmentMatrix.md.

See also
- docs/meta/PhotoMap.md
- docs/meta/UnifiedMemoryMap.md
- docs/meta/AttachmentMatrix.md
