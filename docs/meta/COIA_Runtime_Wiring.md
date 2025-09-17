# COIA Runtime Wiring Map (What actually runs vs legacy/duplicates)

Goal
- Provide a definitive, file-by-file map of the COIA (Contractor Onboarding & Intelligence Agent) implementation under ai-agents/agents/coia
- Call out what the running agent uses at runtime, what is indirectly required, and what looks legacy/duplicate/backups
- Identify the “tool of record” and which “tool” variants are not in use

Last updated: 2025-08-16

---

Primary runtime: Unified COIA (LangGraph)
- Entry orchestration: ai-agents/agents/coia/unified_graph.py
  - Builds the LangGraph and wires the nodes that actually execute
  - Imports and adds nodes (confirmed by code):
    - extraction_node (extraction_node.py)
    - mode_detector_node, conversation_node, research_node, intelligence_node (all in langgraph_nodes.py)
    - bid_card_search (bid_card_search_node_fixed.py) ← fixed version is used
    - bid_submission and account_creation (imported from bid_submission_node.py)
  - Uses checkpointer:
    - Preferred: mcp_supabase_checkpointer.create_mcp_supabase_checkpointer() (mcp_supabase_checkpointer.py)
    - Fallback: in-memory MemorySaver
  - Unified state: UnifiedCoIAState (unified_state.py)
  - Landing/bid-card flows: invokes state manager to persist/restore (state_management/state_manager.py)
  - Public invokers (what routers/UI should call): 
    - create_unified_coia_system()
    - invoke_coia_landing_page(), invoke_coia_chat(), invoke_coia_research(), invoke_coia_intelligence(), invoke_coia_bid_card_link()

Core runtime modules (directly required)
- unified_graph.py (orchestrator) [USED]
- langgraph_nodes.py (nodes: mode_detector_node, conversation_node, research_node, intelligence_node) [USED]
  - Uses fast_mode_detector.py (fast_detect_mode) [USED]
  - Uses prompts.py via from agents.coia.prompts import get_prompt_for_interface [USED]
  - Uses tools.py via from .tools import coia_tools [USED]
- unified_state.py (UnifiedCoIAState + create_initial_state) [USED]
- extraction_node.py (wired as “extraction” node) [USED]
- bid_card_search_node_fixed.py (wired as “bid_card_search” node) [USED]
  - Note: replaces bid_card_search_node.py (legacy)
- bid_submission_node.py (wired as “bid_submission” and “account_creation” nodes via unified_graph imports) [USED]
  - Note: langgraph_nodes.py also defines an account_creation_node; unified_graph.py imports the one from bid_submission_node.py → the langgraph_nodes’ account_creation_node is likely redundant/unused
- mcp_supabase_checkpointer.py (preferred persistence) [USED]
- state_management/state_manager.py (persistent state across turns via unified_conversation_memory) [USED]
- tools.py (COIATools; coia_tools global singleton is the tool-of-record) [USED]

Streaming-related (likely used via routers)
- streaming_chat_router.py [LIKELY USED]
  - Imports UnifiedCoIAGraph, UnifiedCoIAState, and coia_tools; integrates with streaming/SSE layer
- streaming_handler.py [LIKELY USED]
  - Helper used by streaming router; imports unified_state.create_initial_state

Indirect runtime support
- fast_mode_detector.py [USED indirectly by langgraph_nodes]
- prompts.py [USED indirectly by langgraph_nodes]
- __init__.py [package marker; implicitly used]

Legacy / duplicate / backups (not used by unified runtime)
- bid_card_search_node.py [LEGACY] 
  - Superseded by bid_card_search_node_fixed.py (which unified_graph uses)
- tools_real.py, tools_real_extraction.py [LEGACY/EXPERIMENTAL]
  - Not imported by unified runtime; tool-of-record is tools.py (coia_tools)
- openai_o3_agent.py [LEGACY]
  - References persistent_memory and state.CoIAConversationState; not wired into unified_graph
- intelligent_research_agent.py [LEGACY]
  - Same pattern; legacy approach not used by unified_graph
- account_creation_fallback.py [LEGACY]
  - Alternative flow; unified flow uses bid_submission_node/account_creation_node wired in unified_graph
- mode_detector_fix.py [LEGACY/EXPERIMENTAL]
  - Unused; unified runtime uses fast_mode_detector.py via langgraph_nodes
- state.py [LEGACY]
  - Defines CoIAConversationState used by legacy modules; unified uses unified_state.py
- persistent_memory.py.backup [BACKUP]
- supabase_checkpointer_* (rest/simple/.backup) [LEGACY/BACKUPS]
  - unified_graph prefers mcp_supabase_checkpointer.py
- unified_state_fixed.py, unified_state_backup.py.backup [BACKUPS]
- account_creation_design.md, README.md [DOCS]
- signup_link_generator.py [UTILITY/UNREFERENCED]
  - Not imported by unified runtime; treat as auxiliary utility

File-by-file classification
- __init__.py → Package marker [USED implicitly]
- unified_graph.py → Core orchestrator [USED]
- langgraph_nodes.py → Core nodes provider [USED]
- unified_state.py → Core state schema [USED]
- extraction_node.py → Node [USED]
- bid_card_search_node_fixed.py → Node of record [USED]
- bid_card_search_node.py → Legacy node [NOT USED]
- bid_submission_node.py → Node impl for bid submission/account creation [USED]
  - Note: Duplicate account_creation_node also exists in langgraph_nodes.py [LIKELY UNUSED]
- mcp_supabase_checkpointer.py → Checkpointer of record [USED]
- supabase_checkpointer_simple.py / supabase_checkpointer_rest.py.backup / supabase_checkpointer.py.backup → Legacy/backup [NOT USED]
- tools.py → Tool of record (coia_tools) [USED]
- tools_real.py / tools_real_extraction.py → Alternative/experimental [NOT USED]
- fast_mode_detector.py → Mode routing helper [USED]
- mode_detector_fix.py → Experimental/legacy [NOT USED]
- prompts.py → Prompt selection [USED]
- streaming_chat_router.py → Streaming entry [LIKELY USED]
- streaming_handler.py → Streaming helper [LIKELY USED]
- state_management/state_manager.py → Persistent unified memory glue [USED]
- state.py → Legacy state model [NOT USED by unified]
- openai_o3_agent.py → Legacy agent [NOT USED]
- intelligent_research_agent.py → Legacy agent [NOT USED]
- account_creation_fallback.py → Legacy fallback [NOT USED]
- persistent_memory.py.backup → Backup [NOT USED]
- unified_state_fixed.py / unified_state_backup.py.backup → Backup [NOT USED]
- account_creation_design.md / README.md → Documentation
- signup_link_generator.py → Utility (unreferenced by unified runtime)

How we determined “USED”
- Direct imports in unified_graph.py define the runtime wiring:
  - extraction_node, bid_card_search_node_fixed, bid_submission_node/account_creation_node
  - langgraph_nodes provides the four core nodes and is explicitly imported
  - unified_state is the declared graph state
  - mcp_supabase_checkpointer is attempted at compile time, MemorySaver fallback is present
- langgraph_nodes.py shows:
  - fast_mode_detector.py: fast_detect_mode [USED]
  - prompts.py: get_prompt_for_interface [USED]
  - tools.py: coia_tools [USED]
- unified_graph’s entry methods (invoke_* and create_*) confirm state_management/state_manager usage for landing/bidcard flows

Which “tools” file is actually used?
- Tool of record: tools.py (exports coia_tools = COIATools())
  - Used by langgraph_nodes and streaming_chat_router
- tools_real.py and tools_real_extraction.py are not referenced by unified runtime (safe to consider legacy/experiments)

Single-source-of-truth (runtime entrypoints)
- create_unified_coia_system(checkpointer=None) → compiles graph and returns app
- invoke_coia_landing_page / invoke_coia_chat / invoke_coia_research / invoke_coia_intelligence / invoke_coia_bid_card_link → runtime flows the routers should call

Quick verification checklist
- Grep for relative imports already shows what unified_graph wires:
  - from .bid_card_search_node_fixed import bid_card_search_node (fixed path used)
  - from .bid_submission_node import bid_submission_node, account_creation_node (node-of-record)
  - from .langgraph_nodes import conversation_node, intelligence_node, mode_detector_node, research_node (active)
- Inspect langgraph_nodes:
  - from .tools import coia_tools (tool-of-record)
  - from .fast_mode_detector import fast_detect_mode (active)
  - from agents.coia.prompts import get_prompt_for_interface (active)
- Confirm non-references:
  - openai_o3_agent.py, intelligent_research_agent.py, tools_real*.py, mode_detector_fix.py, bid_card_search_node.py, state.py, *_backup files (no imports from unified_graph path)

Recommended cleanup (non-breaking)
- Remove/Archive clearly unused: tools_real*.py, mode_detector_fix.py, bid_card_search_node.py, openai_o3_agent.py, intelligent_research_agent.py, legacy backups
- Resolve duplicate account_creation_node:
  - Keep account_creation_node in bid_submission_node.py (used by unified_graph)
  - Delete or comment the duplicate in langgraph_nodes.py to avoid confusion
- Ensure routers call the unified entrypoints (create_unified_coia_system + invoke_* helpers)
- Keep mcp_supabase_checkpointer as default and document MemorySaver fallback in README.md

Appendix: file tree snapshot
ai-agents/agents/coia/
- __init__.py
- unified_graph.py [USED]
- langgraph_nodes.py [USED; has unused duplicate account_creation_node]
- unified_state.py [USED]
- extraction_node.py [USED]
- bid_card_search_node_fixed.py [USED]
- bid_card_search_node.py [LEGACY/NOT USED]
- bid_submission_node.py [USED]
- mcp_supabase_checkpointer.py [USED]
- supabase_checkpointer_rest.py.backup / supabase_checkpointer_simple.py / supabase_checkpointer.py.backup [LEGACY/BACKUP]
- tools.py [USED]
- tools_real.py / tools_real_extraction.py [LEGACY/NOT USED]
- fast_mode_detector.py [USED]
- mode_detector_fix.py [LEGACY/NOT USED]
- streaming_chat_router.py [LIKELY USED]
- streaming_handler.py [LIKELY USED]
- state_management/state_manager.py [USED]
- state.py [LEGACY/NOT USED]
- openai_o3_agent.py [LEGACY/NOT USED]
- intelligent_research_agent.py [LEGACY/NOT USED]
- persistent_memory.py.backup / unified_state_fixed.py / unified_state_backup.py.backup [BACKUPS]
- account_creation_fallback.py [LEGACY/NOT USED]
- account_creation_design.md / README.md / signup_link_generator.py [DOCS/UTILITY]
