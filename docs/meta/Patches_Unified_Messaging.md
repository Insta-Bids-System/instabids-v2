# Unified Messaging/Image Patches (Copy/Paste Ready)

Purpose: Provide precise, minimal changes you can apply immediately without running any long scans or scripts. These bring the homeowner-facing API router and CIA agent into full alignment with the unified messaging + unified attachments model.

Last updated: 2025-08-12

Important
- These are surgical code edits you can paste into existing files.
- They avoid any long-running commands that have been getting stuck.
- After applying, run your existing unified tests (see the list at the end).

---

## 1) intelligent_messaging_api.py — stop writing legacy message_attachments; write unified_message_attachments

File: ai-agents/routers/intelligent_messaging_api.py

Context
- send_message_with_image currently:
  - uploads image to project-images (good)
  - saves the message via unified API (good)
  - then writes the image to legacy message_attachments (bad; non-unified)

Change (only the attachment insert)
- Find this block inside send_message_with_image (near the end, after message_id is returned):

```python
# Save image attachment
if message_id:
    db = database_simple.get_client()
    attachment_data = {
        "message_id": message_id,
        "type": "image",
        "url": image_url,
        "name": image.filename or "image.jpg",
        "size": len(image_data),
        "analyzed_by_agent": True,
        "analysis_result": agent_result.get("image_analysis", {})
    }
    db.table("message_attachments").insert(attachment_data).execute()
```

- Replace it with unified attachment write:

```python
# Save image attachment (UNIFIED)
if message_id:
    supabase = database_simple.get_client()
    supabase.table("unified_message_attachments").insert({
        "message_id": message_id,
        "type": "image",
        "url": image_url,
        "name": image.filename or "image.jpg",
        "size": len(image_data),
        "metadata": {
            "source": "intelligent_messaging",
            "analyzed_by_agent": True,
            "analysis_result": agent_result.get("image_analysis", {})
        }
    }).execute()
```

Notes
- No other behavior change required in this file to unify attachments.
- Keep resolve_conversation_id for now (it still uses conversations to get a conversation_id that your Unified API consumes). We can revisit that in a later pass.

---

## 2) CIA (homeowner agent) — replace base64/photo_storage with bucket upload + unified_message_attachments

File: ai-agents/agents/cia/agent.py

Problem
- CIA stores base64 blobs to a DB table (photo_storage) and never creates unified_message_attachments, so images do not live in the unified model.

High-level fix
- Remove photo_storage writes.
- For any images provided in a turn:
  1) Ensure unified_conversations exists (by session_id).
  2) Insert a unified_messages row for the user’s turn (before attachment handling).
  3) Upload each image to project-images at unified/{conversation_id}/{timestamp}_{uuid}_{filename}.
  4) Insert one unified_message_attachments row per image.

Step-by-step edits

A) Add helpers (place near other private helpers in the class):

```python
import base64
import uuid

async def _ensure_unified_conversation(self, user_id: str, session_id: str) -> str:
    # Reuse pattern from _save_to_unified_conversations but only to fetch/create the conversation id
    import uuid as _uuid
    supabase = self.supabase
    # Try get
    existing = supabase.table("unified_conversations").select("id").eq("metadata->>session_id", session_id).execute()
    if existing.data:
        return existing.data[0]["id"]
    # Create
    try:
        user_uuid = str(_uuid.UUID(user_id))
    except ValueError:
        user_uuid = str(_uuid.uuid5(_uuid.NAMESPACE_DNS, user_id))
    conversation_data = {
        "tenant_id": "00000000-0000-0000-0000-000000000000",
        "created_by": user_uuid,
        "conversation_type": "project_setup",
        "entity_type": "homeowner",
        "entity_id": user_uuid,
        "title": f"CIA Session - {self.sessions.get(session_id,{}).get('collected_info',{}).get('project_type','Project')}",
        "metadata": {"session_id": session_id},
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    result = supabase.table("unified_conversations").insert(conversation_data).execute()
    if not result.data:
        raise Exception("Failed to create unified_conversations")
    return result.data[0]["id"]

async def _save_unified_message(self, conversation_id: str, sender_type: str, sender_id: str, content: str, metadata: dict) -> str:
    supabase = self.supabase
    message_data = {
        "conversation_id": conversation_id,
        "sender_type": sender_type,
        "sender_id": sender_id,
        "agent_type": "cia" if sender_type == "agent" else None,
        "content": content or "",
        "content_type": "text",
        "metadata": metadata or {},
        "created_at": datetime.now().isoformat()
    }
    msg_result = supabase.table("unified_messages").insert(message_data).execute()
    if not msg_result.data:
        raise Exception("Failed to insert unified_messages")
    # bump conversation last_message_at
    supabase.table("unified_conversations").update({
        "last_message_at": message_data["created_at"]
    }).eq("id", conversation_id).execute()
    return msg_result.data[0]["id"]

async def _upload_and_attach_images(self, conversation_id: str, message_id: str, images: list[str]) -> list[str]:
    supabase = self.supabase
    urls = []
    for idx, image_data in enumerate(images or []):
        # If old reference like "photo_id:..." skip (no URL to attach)
        if image_data.startswith("photo_id:"):
            continue
        # Base64 data URI → bytes
        if image_data.startswith("data:"):
            try:
                header, b64 = image_data.split(",", 1)
                mime = header.split(":")[1].split(";")[0]
            except Exception:
                mime = "image/jpeg"
                b64 = image_data
            raw = base64.b64decode(b64)
            ext = (mime.split("/")[-1] or "jpg").lower()
            fname = f"cia_{uuid.uuid4().hex[:8]}.{ext}"
            path = f"unified/{conversation_id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}_{fname}"
            supabase.storage.from_("project-images").upload(path, raw, {"content-type": mime, "upsert": False})
            url = supabase.storage.from_("project-images").get_public_url(path)
            urls.append(url)
            supabase.table("unified_message_attachments").insert({
                "message_id": message_id,
                "type": "image",
                "url": url,
                "name": fname,
                "size": len(raw),
                "metadata": {"source": "CIA", "uploaded_index": idx}
            }).execute()
        else:
            # If it's already a URL, just link it
            url = image_data
            urls.append(url)
            supabase.table("unified_message_attachments").insert({
                "message_id": message_id,
                "type": "image",
                "url": url,
                "name": url.split("/")[-1][:120],
                "size": None,
                "metadata": {"source": "CIA", "hint": "pre-provided URL"}
            }).execute()
    return urls
```

B) Replace the old photo_storage block in handle_conversation
- Find this section (approx. “# Store images directly in database to bypass storage RLS issues”):

```python
# Store images directly in database to bypass storage RLS issues
if images and len(images) > 0:
    try:
        # Store each image in the database
        stored_image_ids = []
        for idx, base64_image in enumerate(images):
            ...
        # Store photo IDs in collected_info ...
        ...
    except Exception as e:
        ...
```

- Replace it with unified flow:

```python
# Unified image flow (bucket + unified attachments)
if images and len(images) > 0:
    try:
        # Ensure unified conversation and save the user turn first (so we can FK attachments)
        conversation_id = await self._ensure_unified_conversation(user_id, session_id)
        # Convert user_id to deterministic UUID the same way as _save_to_unified_conversations
        try:
            user_uuid = str(uuid.UUID(user_id))
        except ValueError:
            user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, user_id))

        user_msg_id = await self._save_unified_message(
            conversation_id=conversation_id,
            sender_type="user",
            sender_id=user_uuid,
            content=message or "",
            metadata={"agent": "CIA", "has_images": True}
        )

        uploaded_urls = await self._upload_and_attach_images(conversation_id, user_msg_id, images)

        # Update state with URLs (not base64)
        if uploaded_urls:
            state["collected_info"]["uploaded_photos"] = uploaded_urls
            print(f"[CIA] Uploaded {len(uploaded_urls)} images to project-images and linked to unified_message_attachments")

    except Exception as e:
        print(f"[CIA] Error in unified image flow: {e}")
```

C) Prevent double insertion in _save_to_unified_conversations
- If you keep saving the last two messages again there, add a simple guard:
  - Track message ids you already created (e.g., on state or a local set) and skip re-inserting the same user turn you just saved above.

---

## 3) Tests to run after these two edits

- test_unified_image_system_complete.py
- test_cia_unified_images.py
- test_messages_with_attachments_api.py
- test_messaging_agent_unified.py
- test_frontend_unified_complete.py

Expected
- The router no longer writes legacy message_attachments; it writes unified_message_attachments instead.
- CIA no longer writes to photo_storage; images are uploaded to project-images/unified/... and unified_message_attachments rows are created and linked to the correct unified_messages row.

---

## 4) Optional IRIS attachment add-on (quick)

When IRIS references inspiration images in a chat turn, create unified_message_attachments referencing the iris-images URL for that message:

```python
# After obtaining agent_msg_id for the IRIS assistant turn and a persistent_url in iris-images
supabase.table("unified_message_attachments").insert({
  "message_id": agent_msg_id,
  "type": "image",
  "url": persistent_url,
  "name": safe_name,
  "size": size_or_None,
  "metadata": {"source":"IRIS","inspiration": True}
}).execute()
```

This keeps inspiration persistence (iris-images + inspiration_images) and ensures the chat itself has normalized attachments.

---

## 5) Why this is safe

- No schema changes, no deletes.
- Only small, targeted code edits.
- Aligns all attachments to unified_message_attachments while keeping your existing unified message creation intact.

If you want, I can prepare these exact edits as replace_in_file operations next. For now, this doc gives your team precise blocks to paste so you’re not blocked by any stuck commands.
