# COIA (Contractor Interface Agent) — Curated Runtime (2025-08)
Note: This is a duplicate of ai-agents/agents/coia/README.md for easier discovery in docs/meta. The authoritative README lives at ai-agents/agents/coia/README.md.

This README describes the single, curated runtime we are keeping for COIA, how to use the key nodes/tools, and which environment flags/variables control behavior. All legacy/backup variants are being archived to avoid import collisions.

## Kept Runtime (authoritative)

- Orchestrator/State
  - ai-agents/agents/coia/unified_graph.py
  - ai-agents/agents/coia/unified_state.py (reducers include unique+cap list handling)

- Nodes (wired in unified_graph)
  - ai-agents/agents/coia/extraction_node.py
  - ai-agents/agents/coia/langgraph_nodes.py (mode_detector, conversation, research, intelligence)
  - ai-agents/agents/coia/bid_card_search_node_fixed.py (ZIP radius logic)
  - ai-agents/agents/coia/bid_submission_node.py (delegates account creation to tools)

- Tools (facade)
  - ai-agents/agents/coia/tools.py (export: coia_tools)
    - web_search_company (Tavily discovery + extraction fallback)
    - search_bid_cards (adapter-backed helper)
    - build_contractor_profile (DB write behind flag)
    - create_contractor_account (authoritative contractors insert)

- Memory/Persistence
  - ai-agents/agents/coia/mcp_supabase_checkpointer.py (langgraph_checkpoints)
  - ai-agents/agents/coia/state_management/state_manager.py (unified_conversation_memory + unified_conversations)
  - Landing entrypoint pre-merges unified memory via state manager; others can opt-in

- Helpers
  - ai-agents/agents/coia/prompts.py
  - ai-agents/agents/coia/fast_mode_detector.py

For diagrams, wiring, and the component matrix, see:
- docs/meta/COIA_Selected_Set.yaml
- docs/meta/COIA_Tooling_Comparison.md
- docs/meta/COIA_Memory_Paths.md

## How to use the key capabilities

### 1) ZIP‑radius Bid Card Search (LangGraph node)
Use the fixed node wired by the unified graph.

```python
from agents.coia.bid_card_search_node_fixed import bid_card_search_node

# In unified_graph.py (already wired):
# graph.add_node("bid_card_search", bid_card_search_node)
```

Notes:
- Queries Supabase bid_cards and performs ZIP radius expansion internally.
- Treat this node’s DB query as the source of truth for search results.

If you need a plain helper (outside the node), the tools facade also offers:
```python
from agents.coia.tools import coia_tools
projects = await coia_tools.search_bid_cards(contractor_profile, location=None)
# Adapter-backed, privacy-aware, specialty filters; does not replicate the ZIP-radius logic.
```

### 2) Website Research (Tavily discovery path)
Call the tools facade. Tavily is gated by env variables/flags.

```python
from agents.coia.tools import coia_tools

data = await coia_tools.web_search_company("Acme Electric", "FL")
# Uses Tavily discovery if TAVILY_API_KEY present and USE_TAVILY=true.
# Falls back to synthesized/site extraction pathways if not available.
```

## Environment variables and flags

Required (runtime/persistence):
- ANTHROPIC_API_KEY
- SUPABASE_URL
- SUPABASE_ANON_KEY

Recommended:
- TAVILY_API_KEY (enable real Tavily discovery)

Optional:
- OPENAI_API_KEY (optional GPT extraction + streaming helper)
- GOOGLE_MAPS_API_KEY (if you later enable Places in tools.search_google_business)

Feature flags (string booleans: "true"/"false"):
- USE_TAVILY=true      # enable Tavily discovery in tools.web_search_company
- WRITE_LEADS_ON_RESEARCH=false  # gate contractor_leads insert in build_contractor_profile (default off)

## Memory and checkpoint conventions

- Checkpointer (mcp_supabase_checkpointer.py):
  - chat:     ns=coia_chat,        checkpoint_id=chat_{thread_id}
  - research: ns=coia_research,    checkpoint_id=research_{session_id}
  - intel:    ns=coia_intelligence, checkpoint_id=intelligence_{session_id}
  - landing:  ns=coia_landing,     thread_id=landing-{uuid12} if missing
  - bidcard:  ns=coia_bidcard,     checkpoint_id=bidcard_{thread_id}

- Unified memory (state_manager):
  - Ensures unified_conversations
  - Saves/restores per-field state in unified_conversation_memory
  - Landing pre-merges saved memory before first turn (others optional)

## Account creation (single source of truth)

- Node delegates to tools.create_contractor_account and then marks contractor_leads converted:
  - ai-agents/agents/coia/bid_submission_node.py
- The tools path performs the contractors insert and returns normalized success.

## What was archived (to prevent import drift)

- Legacy/experiments/backups (examples): bid_card_search_node.py, tools_real*.py, openai_o3_agent.py, intelligent_research_agent.py, mode_detector_fix.py, account_creation_fallback.py, state.py, *.backup.

These are moved into archived_files/coia (or will be, if not yet moved on your branch).

## Quick smoke checklist

- Landing → ensure unified_conversations and unified_conversation_memory upserts; checkpointer ns=coia_landing
- Chat/Research/Intelligence → ensure checkpointing works; optionally enable unified memory pre-merge
- Research → with TAVILY_API_KEY + USE_TAVILY=true, discovery runs; otherwise fallback path
- Bid card search → fixed node returns ZIP‑radius candidates and respects DB schema
- Account creation → node delegates to tools; contractors insert succeeds; contractor_leads conversion flag set

## Contacts and references

- Curated set index: docs/meta/COIA_Selected_Set.yaml
- Tooling comparison: docs/meta/COIA_Tooling_Comparison.md
- Memory/DB paths: docs/meta/COIA_Memory_Paths.md
