# Rebuilding COIA with deepagents (Architecture, Mapping, and Migration Plan)

Purpose
- Explain how our current COIA (LangGraph + custom nodes/tools/state) would look if rebuilt using deepagents.
- Map 1:1 components (nodes, tools, prompts, memory, streaming) to deepagents constructs.
- Provide a concrete scaffolding (copy/paste) to stand up a working deep agent that mirrors current behavior.

References
- Current COIA runtime wiring: docs/meta/COIA_Runtime_Wiring.md
- DeepAgents repo: https://github.com/hwchase17/deepagents
- DeepAgents usage (create_deep_agent): README usage + examples/research/research_agent.py

---

Executive summary

- DeepAgents builds a LangGraph agent for you from:
  - tools: list of functions (or LangChain @tool)
  - instructions: prompt prefix
  - subagents: optional list of named agents with specialized prompts + tool lists
  - model: optional LangChain chat model (default Claude Sonnet 4)
- Our current stack already uses LangGraph, custom nodes, and a tool layer. Rebuild with deepagents means:
  - Replace explicit StateGraph wiring (unified_graph.py) with deepagents.create_deep_agent
  - Convert our runtime nodes (conversation/research/intelligence/extraction/bid-search/submit) into either:
    - tools (callable operations), and/or
    - subagents (specialized prompts + focused tool subsets)
  - Replace prompts.py with one “instructions” string + optional subagent prompts
  - Memory: deepagents uses LangGraph state; we can persist via our unified_conversation API around agent.invoke calls (or wrap memory saves in tools)
  - Streaming/routers: unchanged pattern (agent.invoke / agent.astream in our FastAPI routes)

---

Current COIA → DeepAgents mapping

- Orchestrator (unified_graph.py)
  - Today: custom StateGraph + set_conditional_entry_point + conditional_edges
  - With deepagents: use create_deep_agent(tools, instructions, subagents=[]) to get a compiled LangGraph agent
  - Routing becomes “prompt-driven + tool selection + optional subagents” instead of explicit conditional edges

- Nodes (langgraph_nodes.py: mode_detector_node, conversation_node, research_node, intelligence_node)
  - Today: separate node functions with logic calls to tools + LLM
  - With deepagents:
    - conversation/intelligence behavior lives in instructions (main agent prompt) and subagent prompts
    - research logic becomes a tool or a subagent that calls tools
    - mode detection can be collapsed into instructions (LLM chooses tool/subagent) or a lightweight tool (heuristic)

- Runtime nodes (extraction_node.py, bid_card_search_node_fixed.py, bid_submission_node.py)
  - Today: explicit nodes
  - With deepagents:
    - extraction (company name, etc.) → tool (extract_company_info(text))
    - bid_card_search → tool (search_bid_cards(profile, filters))
    - bid_submission/account_creation → tools (prepare_bid, create_contractor_account)

- Tool layer (tools.py, coia_tools)
  - Today: COIATools class with methods for research, building profiles, account creation
  - With deepagents: expose free functions (wrapping existing class methods) so create_deep_agent can register them
  - Optionally keep the class but export function adapters

- Prompts (prompts.py)
  - Today: per-interface prompt selection
  - With deepagents: a single instructions string; optionally add subagent prompt(s)
  - e.g., “research-agent” subagent with research-specific instructions; “bid-agent” for matching

- State/memory (unified_state.py + state_manager.py)
  - Today: UnifiedCoIAState typed dict + unified_conversation_memory persistence
  - With deepagents: deepagents agent returns LangGraph state; persist around invocations via our existing state_manager (wrap agent.invoke with our save/restore)
  - Or add memory tools (save_state(field), load_state()) to write to unified_conversation_memory

- Streaming
  - Today: streaming_chat_router.py + handler
  - With deepagents: use agent.astream (values) and relay to SSE as before

---

Minimal scaffolding (copy/paste)

1) Install
```bash
pip install deepagents tavily-python langchain
# (and langchain-mcp-adapters if you want MCP tool access)
```

2) Define tools (wrap our existing tool methods as free functions)
```python
# ai-agents/agents/coia/deepagents_tools.py
from typing import Optional, Dict, Any, List
from ai-agents.agents.coia.tools import coia_tools

def extract_company_info(text: str) -> Dict[str, Any]:
    # Could reuse our LLM extraction or simple heuristics
    # For now, call our existing path if available
    # Return {"company_name": "...", "location": "..."} etc.
    # Stub example:
    name = text.strip().splitlines()[0][:120]
    return {"company_name": name}

def internet_search(query: str, max_results: int = 5, include_raw_content: bool = False) -> Dict[str, Any]:
    # Optionally wire Tavily here or call our _search_business_web
    # Return structure similar to tavily client search
    # Example delegating to our search:
    # data = await coia_tools.search_google_business(query)  # if made sync or wrapped
    return {"results": [], "query": query}

def research_business(company_name: str, location: Optional[str] = None) -> Dict[str, Any]:
    # Use our real tool route
    # In deepagents tools must be sync; if our implementation is async, wrap it with anyio
    import anyio
    return anyio.run(coia_tools.search_google_business, company_name, location)

def search_bid_cards(contractor_profile: Dict[str, Any], location: Optional[str] = None) -> List[Dict[str, Any]]:
    import anyio
    return anyio.run(coia_tools.search_bid_cards, contractor_profile, location)

def create_contractor_account(profile: Dict[str, Any]) -> Dict[str, Any]:
    import anyio
    return anyio.run(coia_tools.create_contractor_account, profile)
```

3) Compose the deep agent
```python
# ai-agents/agents/coia/deepagents_agent.py
from deepagents import create_deep_agent
from .deepagents_tools import (
    extract_company_info, internet_search, research_business,
    search_bid_cards, create_contractor_account
)

# Main instructions (fold in prompts.py logic here)
instructions = """
You are COIA, the Contractor Onboarding & Intelligence Agent.
- Extract company details from user messages (use extract_company_info)
- If company known, do research (research_business), then guide the user
- If asked for opportunities, search bid cards (search_bid_cards)
- When user confirms, create account (create_contractor_account)
"""

# Optional subagents (e.g., focused research)
research_subagent = {
    "name": "research-agent",
    "description": "Performs deeper company research and profile building",
    "prompt": "You are a specialized research agent. Use research_business and internet_search to gather verified data."
}

tools = [
    extract_company_info,
    internet_search,
    research_business,
    search_bid_cards,
    create_contractor_account
]

agent = create_deep_agent(
    tools=tools,
    instructions=instructions,
    subagents=[research_subagent]
)

# Usage:
# result = agent.invoke({"messages": [{"role": "user", "content": "JM Holiday Lighting in Fort Lauderdale"}]})
# (Wrap with our state_manager before/after to persist unified memory)
```

4) Persist unified memory around calls (unchanged approach)
- Before agent.invoke: load state via state_manager.restore_state(contractor_lead_id) and inject as files or into messages
- After agent.invoke: save messages and key fields via state_manager.save_state

5) Routers (unchanged)
- Replace unified_graph.compile + app.ainvoke calls with agent.invoke / agent.astream
- Keep streaming SSE exactly as today

---

Pros / Cons of deepagents vs current

Pros
- Far less custom LangGraph wiring; removes conditional routing code
- “Planning + subagents + tools” pattern encourages cleaner separation
- Built-in system prompt/patterns for deep tasks; quick to stand up variants
- Easy to bring MCP tools via langchain-mcp-adapters

Cons
- We lose our explicit mode graph and routing (now driven by prompt + tool calls)
- Complex multi-step flows (landing vs chat vs bid-card-link) become prompt/subagent design, not edges
- Our current unified state typing (UnifiedCoIAState) becomes less central; need discipline in state persistence
- Our current node-specific guardrails (loop protection) must be re-expressed in instructions/tool contracts

---

One-to-one mapping table

- unified_graph.py → deepagents.create_deep_agent(...)
- langgraph_nodes.py (conversation/research/intelligence/mode) → main agent prompt + subagents + tools selection
- extraction_node.py → extract_company_info tool
- bid_card_search_node_fixed.py → search_bid_cards tool
- bid_submission_node.py → create_contractor_account tool (+ optional prepare_bid tool if needed)
- tools.py → exported free functions (wrappers) used by deepagents
- prompts.py → single instructions string (+ optional subagent prompts)
- unified_state/state_manager → unchanged, wrapped around agent.invoke/astream
- streaming_chat_router → unchanged, use agent.astream

---

What to copy/paste first (MVP rebuild)

- Create deepagents_tools.py with wrappers for:
  - extract_company_info
  - research_business (wrap coia_tools.search_google_business)
  - search_bid_cards (wrap coia_tools.search_bid_cards)
  - create_contractor_account (wrap coia_tools.create_contractor_account)
- Create deepagents_agent.py with create_deep_agent(tools, instructions, [subagents])
- In router(s), replace unified_graph build/compile with import agent from deepagents_agent.py and call agent.invoke/astream
- Keep state_manager save/restore around invocations

---

Open items

- Tools sync vs async: deepagents tools are plain callables; wrap our async functions with anyio.run or refactor to sync wrappers.
- Subagents: Add a “bid-agent” for price guidance, “intelligence-agent” for business optimization if we want parity with our intelligence node.
- Memory schema: consider a thin helper to serialize/unserialize “messages” consistently to unified_conversation_memory.
- Safety/loop guards: encode loop-limits and stage checks in instructions and tool preconditions (e.g., only create account if research_completed).

---

Verdict

- Rebuilding COIA on deepagents is straightforward: convert runtime nodes to tools, fold prompts into one “instructions” + optional subagents, call create_deep_agent, and keep our existing state persistence and streaming.
- This reduces custom LangGraph code while preserving behavior, and opens door to easier subagent composition and MCP tool intake.
