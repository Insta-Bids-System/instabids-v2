# COIA Memory Paths (Checkpointing, Unified Memory, Direct DB Writes)

Purpose
- Document every place the COIA agent persists or restores state/data.
- Clarify identifiers (thread_id, checkpoint_ns, checkpoint_id), tables, and field shapes.
- Identify the single state manager of record and where it is invoked.
- Surface side-effect writes (contractor_leads, contractors) done by tools.

Sources
- ai-agents/agents/coia/unified_graph.py (invoke_* helpers, config)
- ai-agents/agents/coia/state_management/state_manager.py (UnifiedStateManager)
- ai-agents/agents/coia/mcp_supabase_checkpointer.py (LangGraph checkpoint persistence)
- ai-agents/agents/coia/tools.py (DB writes in profile/account flows)
- ai-agents/agents/coia/bid_submission_node.py (DB updates on conversion)
- ai-agents/agents/coia/bid_card_search_node_fixed.py (DB reads)

---

## 1) LangGraph Checkpointing (State snapshots per thread)

Component
- ai-agents/agents/coia/mcp_supabase_checkpointer.py

Table
- langgraph_checkpoints

Operations (via Supabase client)
- select("*").eq("thread_id", thread_id)
- upsert(data) ← save checkpoint data/values/metadata
- update({"metadata": ...}) ← augment metadata on existing checkpoint

Identifiers
- thread_id: set in config["configurable"]["thread_id"] (per invoke_* helper)
- checkpoint_ns: namespacing per interface
- checkpoint_id: optional explicit id in some flows

By entry flow (from unified_graph.py configs)
- Chat (invoke_coia_chat):
  - thread_id = contractor_lead_id or session_id
  - checkpoint_ns = "coia_chat"
  - checkpoint_id = f"chat_{thread_id}"
- Research (invoke_coia_research):
  - thread_id = session_id
  - checkpoint_ns = "coia_research"
  - checkpoint_id = f"research_{session_id}"
- Intelligence (invoke_coia_intelligence):
  - thread_id = session_id
  - checkpoint_ns = "coia_intelligence"
  - checkpoint_id = f"intelligence_{session_id}"
- Landing (invoke_coia_landing_page):
  - thread_id = contractor_lead_id (always generated if missing; "landing-{uuid12}")
  - checkpoint_ns = "coia_landing"
  - checkpoint_id = (not explicitly set in code)
- Bid card link (invoke_coia_bid_card_link):
  - thread_id = contractor_lead_id (generated if missing; "bidcard-{uuid12}")
  - checkpoint_ns = "coia_bidcard"
  - checkpoint_id = f"bidcard_{thread_id}"

Fallback behavior
- unified_graph.compile() tries create_mcp_supabase_checkpointer(); on failure logs a warning and falls back to MemorySaver (in-memory only).

Notes
- Checkpointer persists LangGraph state diffs; it does not replace unified memory persistence below.
- Ensure Supabase DB env is present for persistence, else MemorySaver will be used (ephemeral across restarts).

---

## 2) Unified Conversation Memory (Cross-turn restoration for landing/bid-card)

Component
- ai-agents/agents/coia/state_management/state_manager.py (UnifiedStateManager)
  - get_state_manager() used by invoke_coia_landing_page and invoke_coia_bid_card_link to restore/merge state before first turn
  - save_state() called elsewhere to persist fields between visits

Tables
- unified_conversation_memory
  - Keys/fields:
    - conversation_id: deterministic UUID derived from contractor_lead_id (UUIDv5 namespace)
    - memory_type: "coia_state" (for fields) or "checkpoint" (for lightweight checkpoint)
    - memory_key: field name (e.g., "messages", "company_name", ...)
    - memory_value: string or JSON (messages serialized)
    - importance_score: numeric priority
    - created_at, updated_at: timestamps
- unified_conversations
  - Ensures a conversation record exists for the conversation_id
  - Fields include: id (UUID), conversation_type ("COIA_LANDING"), entity_type ("contractor_lead"), title, status, contractor_lead_id, metadata JSON (journey_stage, interface, company_name, research_completed), created_at/updated_at/last_message_at

Operations (Supabase client)
- save_state:
  - upsert into unified_conversation_memory one record per field in the PERSISTENT_STATE_FIELDS list
  - special case "messages": serialize to [{"content": "...", "type": "ai|human"}, ...]
  - upsert "last_state_update" timestamp record
  - when conversation_id provided: map contractor_lead_id in a "contractor_mapping" memory record (secondary link)
  - ensure unified_conversations record exists (insert on first save) via _ensure_conversation_exists
- restore_state:
  - select("*").eq("conversation_id", memory_conversation_id).eq("memory_type","coia_state")
  - deserialize messages back to AI/Human messages; JSON-decode other values
- create_checkpoint (lightweight):
  - upsert memory_type="checkpoint", memory_key="state_checkpoint" with snapshot (current_mode, flags, timestamps)
- restore_checkpoint:
  - select checkpoint record by conversation_id/memory_type/memory_key

Persistent field set (PERSISTENT_STATE_FIELDS)
- messages (serialized)
- company_name, contractor_profile, business_info, research_findings, specialties, certifications
- years_in_business, extraction_completed, research_completed, intelligence_completed
- website_summary, online_presence, service_areas, project_types, budget_range
- contact_name/contact_email/contact_phone, business_address, license_number
- insurance_info, employee_count, annual_revenue, growth_trajectory
- competitive_advantages, target_customer, pricing_strategy, marketing_channels
- recent_projects, customer_reviews, social_media_presence
- bid_history, submitted_bids

Notes
- UnifiedStateManager also upserts to contractor_leads when company_name is present (see section 3 below).
- conversation_id strategy: v5 UUID based on contractor_lead_id; prevents collisions and stabilizes retrieval across sessions.

---

## 3) Direct DB Writes from Tools/Nodes (Business data and conversion)

Tools (ai-agents/agents/coia/tools.py)
- build_contractor_profile():
  - Writes to contractor_leads (insert)
  - Enrichment merges (social links, scores, data_sources)
  - Converts some numeric fields to ints; strips None values; captures discovered_at
- create_contractor_account():
  - Writes to contractors (insert)
  - Sets default availability_status, tier, verified flags, specialties, etc.
  - Strips None; logs success
- search_bid_cards():
  - No DB writes; pulls context via adapters.ContractorContextAdapter.get_contractor_context()

Nodes
- bid_card_search_node_fixed.py:
  - Reads bid_cards (select), performs ZIP radius logic
- bid_submission_node.py:
  - Inserts into contractors on submission path (overlaps with tools.create_contractor_account)
  - Updates contractor_leads {"converted_to_contractor": True} on conversion

Implications
- There are two pathways writing to contractors: via tools.create_contractor_account and via bid_submission_node. Choose one authoritative path or ensure they do not conflict (prefer tools façade for consistency; node can invoke it).
- contractor_leads appear in both UnifiedStateManager (lead upsert on save) and tools.build_contractor_profile (insert). Ensure schema alignment.

---

## 4) Entry Helpers and State Merge (Where restoration happens)

In unified_graph.py
- invoke_coia_landing_page():
  - Imports get_state_manager() from agents.coia.state_management.state_manager
  - state_manager.restore_state(contractor_lead_id) merges into initial_state when present (and preserves interface="landing_page")
- invoke_coia_bid_card_link():
  - No state_manager here, but preloads contractor context via adapters.ContractorContextAdapter
  - Still uses checkpointer config (coia_bidcard)
- invoke_coia_chat/research/intelligence():
  - No explicit unified memory restore; rely on checkpointer (thread_id & checkpoint_id) and pass business/company context via initial state

Recommendation
- If you want unified memory across all entrypoints, call state_manager in Chat/Research/Intelligence too (optional). Currently only Landing pre-merges with unified memory.

---

## 5) Environment / Keys (for persistence and external IO)

- Supabase DB: used by state_manager and checkpointer; supplied through database/SupabaseDB wrapper
- Anthropic (ANTHROPIC_API_KEY): used by langgraph_nodes and extraction_node for messaging
- OpenAI (OPENAI_API_KEY): optional for GPT‑based extraction or streaming router
- Tavily (TAVILY_API_KEY): required for real Tavily discovery; currently hard-coded dev key in _tavily_discover_contractor_pages (should be moved to env)
- MCP Playwright: referenced but not executed in tools (commented placeholders)

---

## 6) Single State Manager of Record

- Keep: ai-agents/agents/coia/state_management/state_manager.py
- Everywhere else should import: from agents.coia.state_management.state_manager import get_state_manager
- Remove/redirect any alternative state manager modules if found elsewhere.

---

## 7) Gaps / Fixes

- Tavily key: move hard-coded key to env (TAVILY_API_KEY) and gate its usage by presence.
- Consistent conversion path:
  - Prefer tools.create_contractor_account; update bid_submission_node to call it, then perform any node-specific messaging.
- Unified memory coverage:
  - Decide whether non-landing entrypoints should also pre-merge unified memory (consistency vs speed).
- Schema drift:
  - Validate contractor_leads and contractors field mappings against current DB (Supabase) schema; adjust mappings in tools and state_manager if needed.

---

## 8) Quick Validation Plan

1) Landing flow
- Start new landing session (no contractor_lead_id):
  - Verify unified_conversations insertion and unified_conversation_memory upserts on save_state
  - Verify checkpoint created with thread_id="landing-..." and ns="coia_landing"

2) Chat flow with contractor_lead_id
- Use same contractor_lead_id; confirm restored state (if opting to call state_manager), and checkpoint usage (coia_chat ns, chat_{thread_id} id)

3) Bid card link
- Provide contractor_lead_id; ensure contractor context preloads; checkpoint uses ns=coia_bidcard; verify no unified memory corruption

4) Profile/account writes
- After research, ensure contractor_leads upsert from UnifiedStateManager or build_contractor_profile()
- On account creation, ensure contractors insert; verify any conversion flag update on contractor_leads (single path, not conflicting)

This document enumerates every persistence path so we can confidently select and keep a single, correct set of components, and quarantine the rest.
