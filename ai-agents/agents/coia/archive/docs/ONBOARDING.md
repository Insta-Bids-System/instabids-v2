# Agent 4 – COIA Onboarding and Runtime Contract

Purpose
- Make COIA self-sufficient. All critical references, structure, and rules live inside the agent folder.
- Provide a single “bootstrap doc” the slash command points to so the agent loads its own context and stays on track.

Authoritative Locations (inside agent)
- This file (bootstrap): ai-agents/agents/coia/docs/ONBOARDING.md
- Runtime README (curated): ai-agents/agents/coia/README.md
- Orchestrator/state/nodes:
  - ai-agents/agents/coia/unified_graph.py
  - ai-agents/agents/coia/unified_state.py
  - ai-agents/agents/coia/langgraph_nodes.py
  - ai-agents/agents/coia/extraction_node.py
  - ai-agents/agents/coia/bid_card_search_node_fixed.py
  - ai-agents/agents/coia/bid_submission_node.py
- Tools/prompts:
  - ai-agents/agents/coia/tools.py (export: coia_tools)
  - ai-agents/agents/coia/prompts.py
- Memory/checkpoint:
  - ai-agents/agents/coia/state_management/state_manager.py
  - ai-agents/agents/coia/mcp_supabase_checkpointer.py
- Router:
  - ai-agents/routers/unified_coia_api.py

External docs (kept in docs/meta; referenced here)
- docs/meta/COIA_Selected_Set.yaml (kept LEGO blocks)
- docs/meta/COIA_File_Inventory.md (roles, runtime usage, keep/archive)
- docs/meta/COIA_Tooling_Comparison.md (best-of tools)
- docs/meta/COIA_Memory_Paths.md (checkpoint/unified memory)
- docs/meta/COIA_SlashCommand.md (HTTP mapping; superseded by agent-facing spec below)

Bootstrap Steps (on every agent start)
1) Load identity and scope
   - I am Agent 4 – COIA. I own contractor onboarding and contractor-facing flows.
   - My runtime contract is defined by the files listed above.

2) Load curated README
   - Read ai-agents/agents/coia/README.md fully.

3) Load orchestrator/state/nodes
   - Read unified_graph.py
   - Read unified_state.py
   - Read langgraph_nodes.py, extraction_node.py, bid_card_search_node_fixed.py, bid_submission_node.py

4) Load tools and memory
   - Read tools.py, prompts.py
   - Read state_management/state_manager.py and mcp_supabase_checkpointer.py

5) Validate flags and env
   - USE_TAVILY, WRITE_LEADS_ON_RESEARCH
   - ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_ANON_KEY
   - Optional: OPENAI_API_KEY, GOOGLE_MAPS_API_KEY (if Places enabled)

6) Update internal memory (MCP/cipher suggested pattern)
   - mcp__cipher__ask_cipher("COIA bootstrap complete. Loaded curated README, runtime files, and memory rules. Commit identity and file map to working memory.")
   - mcp__cipher__ask_cipher("Record runtime locations and flags: USE_TAVILY, WRITE_LEADS_ON_RESEARCH, checkpointer ns conventions.")

7) Enforce consent and single-write paths
   - Never create accounts without explicit confirmation.
   - bid_submission_node delegates to tools.create_contractor_account (single path).
   - landing must restore unified memory via state_manager; other entrypoints optional.

8) Zip search and research usage (for other agents)
   - Zip-radius bid search: from agents.coia.bid_card_search_node_fixed import bid_card_search_node
   - Tavily research: from agents.coia.tools import coia_tools; await coia_tools.web_search_company("Acme", "FL")

Agent-Facing Slash Command (Self-Onboarding Spec)
Command: /coia.run
Behavioral Guardrails (in addition to HTTP mapping)
- Stay on track:
  - Read ai-agents/agents/coia/README.md and this ONBOARDING.md before acting.
  - Use the curated orchestrator/state/nodes/tools only.
  - Restore/merge memory appropriately per entrypoint.
  - Enforce consent for account creation; set contractor_created only after success.
  - Use the single contractors write path (tools.create_contractor_account).

Parameters
- entry: landing | chat | bidcard | research | intelligence
- message: string
- session_id: string
- contractor_lead_id: string (recommended; required for bidcard)
- options:
  - use_tavily: boolean (fallback to env if omitted)
  - write_leads_on_research: boolean (fallback to env)
  - bootstrap: boolean (default true) – when true, execute “Bootstrap Steps” above before invoke

Entry Behavior (high-level)
- landing:
  - Ensure contractor_lead_id; restore unified memory; invoke invoke_coia_landing_page
- chat:
  - Thread = contractor_lead_id or session_id; invoke invoke_coia_chat
- bidcard:
  - Require contractor_lead_id & verification_token (router requires token); preload ContractorContextAdapter; invoke invoke_coia_bid_card_link
- research:
  - Provide company_data with name/website/city/state; invoke invoke_coia_research
- intelligence:
  - Provide contractor_data; invoke invoke_coia_intelligence

Checkpoint/Memory Conventions (must respect)
- chat: ns=coia_chat, checkpoint_id=chat_{thread}
- research: ns=coia_research, checkpoint_id=research_{session_id}
- intelligence: ns=coia_intelligence, checkpoint_id=intelligence_{session_id}
- landing: ns=coia_landing (thread=contractor_lead_id)
- bidcard: ns=coia_bidcard, checkpoint_id=bidcard_{thread}

Full Scope of Work (recap)
- Extract business → confirm → deep research → service expansion & radius → show matching bids → account creation (with consent)
- Ensure:
  - account_creation_confirmed set before creation; contractor_created set True after success
  - progressive research (fast initial, deeper later)
  - performance: < 10s initial response
  - zip search uses fixed node; research uses tools facade with flags

Runbook (quick smoke)
- Landing test: POST /landing with a new session and message like “Hi I run JM Holiday Lighting”
- Chat test: POST /chat with contractor_lead_id
- Bidcard test: POST /bid-card-link with real contractor_lead_id + token
- Research test: POST /research with { name, website, city, state }
- Verify unified memory save/restore and checkpointer IDs per ONBOARDING

Notes
- Legacy and backups are quarantined under archived_files/coia to avoid import collisions.
- If you add Google Places, gate it via USE_GOOGLE_PLACES and optional API key.
