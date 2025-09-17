# COIA File Inventory (Roles, Runtime Usage, Keep/Archive)

Purpose
- Single authoritative index of all COIA-related files referenced in Agent 4 context.
- Role, runtime wiring, and decision (Keep/Archive) with rationale.
- Cross-links to curated docs and exact imports for other agents.

Legend
- Role: Orchestrator | Node | Tool | State | Router | Adapter | Helper | Test | Legacy
- Runtime: Wired (via unified_graph / router) | Helper used | Not wired
- Decision: Keep | Keep (helper) | Archive

Curated references
- COIA Selected Set: docs/meta/COIA_Selected_Set.yaml
- Tooling Comparison: docs/meta/COIA_Tooling_Comparison.md
- Memory Paths: docs/meta/COIA_Memory_Paths.md
- Runtime README: ai-agents/agents/coia/README.md (copy in docs/meta/COIA_Runtime_Readme.md)

---

## API / Router

1) ai-agents/routers/unified_coia_api.py
- Role: Router (FastAPI)
- Runtime: Wired (landing/chat/research/intelligence/bid-card-link)
- Uses:
  - get_unified_coia_app() → create_unified_coia_system(None)
  - invoke_coia_landing_page/chat/research/intelligence/bid_card_link
  - get_state_manager() for landing restore
- Decision: Keep
- Notes:
  - Chat endpoint currently not restoring unified memory; landing does. OK per design.

---

## Orchestrator and Nodes

2) ai-agents/agents/coia/unified_graph.py
- Role: Orchestrator
- Runtime: Wired (entry routing, nodes, checkpointer compile)
- Decision: Keep
- Notes:
  - Compiles with mcp_supabase_checkpointer; falls back to MemorySaver
  - Has invoke_* helpers with correct checkpoint_ns/id conventions

3) ai-agents/agents/coia/langgraph_nodes.py
- Role: Nodes (conversation, research, intelligence, mode_detector) + legacy bid/account versions
- Runtime: Wired (conversation/research/intelligence/mode_detector). For bid/account, unified_graph uses fixed node and bid_submission_node.py versions.
- Decision: Keep (as node implementations for conversation/research/intelligence/mode_detector)
- Notes:
  - Account creation here is redundant; unified_graph wires bid_submission_node.py::account_creation_node as node-of-record
  - Research node currently runs “fast research” (no external I/O) and returns “research_complete_with_real_data” flag; tools.py carries real paths

4) ai-agents/agents/coia/extraction_node.py
- Role: Node
- Runtime: Wired
- Decision: Keep

5) ai-agents/agents/coia/bid_card_search_node_fixed.py
- Role: Node (ZIP radius)
- Runtime: Wired
- Decision: Keep
- Note: Treat as source-of-truth for DB-driven bid search

6) ai-agents/agents/coia/bid_submission_node.py
- Role: Node (bid submission + account creation interrupts)
- Runtime: Wired
- Decision: Keep
- Notes:
  - Updated to delegate contractor creation to tools.create_contractor_account (single write path)
  - Marks contractor_leads converted afterward

---

## State / Memory

7) ai-agents/agents/coia/unified_state.py
- Role: State schema (TypedDict + dataclass)
- Runtime: Wired
- Decision: Keep
- Notes:
  - Added unique+cap reducers for list fields to prevent growth/dupes

8) ai-agents/agents/coia/state_management/state_manager.py (and submodules)
- Role: Unified memory persistence (unified_conversation_memory/unified_conversations, contractor_leads upsert)
- Runtime: Wired (landing restore, save_state async)
- Decision: Keep (state manager of record)
- Notes: Import via from agents.coia.state_management.state_manager import get_state_manager

9) ai-agents/agents/coia/mcp_supabase_checkpointer.py
- Role: Checkpointer (langgraph_checkpoints)
- Runtime: Wired (compile default)
- Decision: Keep

---

## Tools / Prompts

10) ai-agents/agents/coia/tools.py
- Role: Tools façade (export coia_tools)
- Runtime: Used by nodes and router helpers
- Decision: Keep
- Notes:
  - Tavily moved behind env (TAVILY_API_KEY) + flag (USE_TAVILY)
  - contractor_leads insert gated by WRITE_LEADS_ON_RESEARCH
  - create_contractor_account authoritative contractors insert

11) ai-agents/agents/coia/prompts.py
- Role: Helper (system prompts by interface)
- Runtime: Used by conversation node
- Decision: Keep

---

## Adapters / DB

12) ai-agents/adapters/contractor_context.py
- Role: Adapter (contractor context load, bid history, available projects)
- Runtime: Used by unified_graph (bid_card_link) and tools.search_bid_cards
- Decision: Keep

13) ai-agents/database_simple.py
- Role: DB access wrapper
- Runtime: Used by tools and nodes
- Decision: Keep

---

## Design / Requirements (Docs)

14) ai-agents/LANDING_PAGE_CONTRACTOR_FLOW_DESIGN.md
- Role: Design
- Runtime: N/A
- Decision: Keep (doc)

15) ai-agents/COIA_MAIN_FILES_LIST.md
- Role: Doc index
- Decision: Keep (doc) – may cross-check with this inventory

16) ai-agents/agents/coia/account_creation_design.md
- Role: Design (consent-based creation)
- Decision: Keep (doc) – aligns with confirmation in nodes

---

## Tests (Selected for entry expectations)

- ai-agents/test_coia_* (various)
- root-level test_coia_* (various)
- Decision: Keep (tests)

---

## Legacy / Archive (moved to archived_files/coia)

- ai-agents/agents/coia/bid_card_search_node.py
- ai-agents/agents/coia/tools_real.py
- ai-agents/agents/coia/tools_real_extraction.py
- ai-agents/agents/coia/openai_o3_agent.py
- ai-agents/agents/coia/intelligent_research_agent.py
- ai-agents/agents/coia/mode_detector_fix.py
- ai-agents/agents/coia/account_creation_fallback.py
- ai-agents/agents/coia/persistent_memory.py.backup
- ai-agents/agents/coia/supabase_checkpointer_rest.py.backup
- ai-agents/agents/coia/unified_state_backup.py.backup
- ai-agents/agents/coia/unified_state_fixed.py.backup
- ai-agents/agents/coia/state.py

---

## Slash-command mapping (overview; see dedicated doc)

- Command: /coia.run
- Params:
  - entry: landing | chat | bidcard | research | intelligence
  - message: string
  - session_id: string
  - contractor_lead_id: string (optional; required for bidcard)
  - options: use_tavily, write_leads_on_research (boolean flags)
- Behavior: builds correct thread_id/checkpoint_ns; landing restores unified memory via state_manager; routes to invoke_coia_* helper.
- See: docs/meta/COIA_SlashCommand.md

---

## Final notes

- Source-of-truth decisions:
  - bid search: node_db_query (bid_card_search_node_fixed) authoritative; tools.search_bid_cards is helper/enrichment
  - account creation: tools.create_contractor_account authoritative; nodes delegate to it
  - state manager: single import path, used for landing restore (others optional)
- If you add Google Places back, implement as an optional path in tools.search_google_business with USE_GOOGLE_PLACES flag.
