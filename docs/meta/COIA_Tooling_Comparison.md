# COIA Tooling Comparison (Best-of Selection Across All Variants)

Goal
- Compare all available “tool” capabilities used by COIA (not just the currently wired ones) to select the best, production-grade implementations per capability.
- Classify real vs simulated behavior, external side-effects, env key dependencies, and usage evidence (wired by nodes/tests).
- Produce a shortlist to drive a single canonical tools façade (keep) and an archive set (remove/confine).

Scope reviewed (code search evidence)
- Folder: ai-agents/agents/coia/
- Nodes: extraction_node.py, langgraph_nodes.py, bid_card_search_node_fixed.py, bid_submission_node.py (wired), bid_card_search_node.py (legacy)
- Tool façade: tools.py (tool-of-record today)
- Memory/state: mcp_supabase_checkpointer.py, state_management/state_manager.py
- Streaming/router: streaming_chat_router.py, streaming_handler.py
- Others/legacy: tools_real*.py, openai_o3_agent.py, intelligent_research_agent.py, mode_detector_fix.py, *.backup, signup_link_generator.py (utility)

Search signal (selected)
- External IO: requests/httpx, OpenAI/Anthropic, Tavily, SupabaseDB/db.client.table
- Memory: unified_conversation_memory, unified_conversations
- Persistence / adapters: ContractorContextAdapter
- State manager usage: get_state_manager

---

## Capability Matrix

Legend
- Side effects: HTTP, DB (Supabase), LLM (OpenAI/Anthropic), Tavily, MCP/Playwright, FS
- Status: Real/Stable | Real/Needs Polish | Sim/Fallback | Legacy
- Usage: WiredByNodes | ReferencedByTests | Unreferenced

### 1) Business Research / Web Intake

A) tools.py → COIATools.search_google_business(company_name, location)
- Side effects:
  - Currently “NOTE: Google API is not enabled – using web scraping instead”
  - Calls _search_business_web(query) → returns generated/heuristic business data (no HTTP to Google)
  - Falls back to _create_minimal_business_data on error
- Env keys: None (logs mention GOOGLE_MAPS_API_KEY but not used in path)
- Status: Sim/Fallback (works without external API; not authoritative)
- Usage: WiredByNodes indirectly via web_search_company/research path; logged by langgraph_nodes.research_node

B) tools.py → COIATools.web_search_company(company_name, location?)
- Side effects:
  - Intended: Tavily MCP + Playwright MCP “66 fields” path
  - Actual: Fetches google_data via search_google_business, then uses _tavily_discover_contractor_pages if website_url, but SKIPS Playwright (“for speed”), populates website_data from Tavily-only
  - Also calls _search_social_media_profiles (currently placeholder)
  - Calls _analyze_business_intelligence (computes scores from gathered data)
- Env keys: Tavily API key required, but code currently hard-codes a dev key; OpenAI API only in deeper GPT extraction method (_extract_website_intelligence) if invoked
- Status: Real/Needs Polish (uses Tavily if installed; no Playwright execution; social media and BI are partial)
- Usage: Not directly wired by nodes as a single call; parts are used in research flows

C) tools.py → COIATools._tavily_discover_contractor_pages(company_name, website_url, location)
- Side effects: REAL Tavily API calls (search + extract). Hard-coded API key (tvly-dev-...); robust try/catch, rate-limiting sleeps.
- Env keys: Tavily SDK install + (ideally) env key (but currently hard-coded)
- Status: Real/Needs Polish (should move key to env vars; good behavior otherwise)
- Usage: Called by web_search_company when website_url present

D) tools.py → COIATools._extract_website_intelligence(page_content, website_url, company_name)
- Side effects: BeautifulSoup HTML parse; no network (page_content provided by callers). Optional GPT-4o “intelligent extraction” path (requires OPENAI_API_KEY)
- Env keys: OPENAI_API_KEY (if GPT path used)
- Status: Real/Needs Polish (works via BS; GPT path optional)
- Usage: Called in web scraping fallback when Playwright/Tavily content present

E) tools.py → COIATools._search_business_web(query)
- Side effects: None; synthesizes data from company name and location
- Status: Sim/Fallback (fast, deterministic; not authoritative)
- Usage: Used by search_google_business (primary path today)

Decision for “Business Research”
- Keep:
  - _tavily_discover_contractor_pages (move API key to env; use if Tavily SDK present)
  - _extract_website_intelligence (BS path always available; GPT optional)
- Keep (fallback):
  - _search_business_web for quick bootstrapping when APIs unavailable
- Migrate:
  - search_google_business should first prefer Tavily pipeline if website present; else fallback to _search_business_web
- Archive:
  - Any redundant “tools_real*.py” research variants

### 2) Bid Card Search / Matching

A) tools.py → COIATools.search_bid_cards(contractor_profile, location?)
- Side effects:
  - Imports adapters.contractor_context.ContractorContextAdapter
  - Calls get_contractor_context(contractor_id) → returns available_projects; filters by specialties; returns slice
- Env keys: None
- Status: Real/Stable (adapter-based, privacy-aware)
- Usage: Called by nodes; good abstraction

B) bid_card_search_node_fixed.py (node)
- Side effects:
  - Direct DB query via db.client.table("bid_cards") select; comments indicate ZIP radius expansion
- Status: Real/Stable (wired by unified_graph); but mixing node logic and DB may duplicate capability with tools.py
- Usage: WiredByNodes (primary runtime search path)
- Note: Decide single source-of-truth: either keep node DB path or route node → tools facade for consistency

Decision for “Bid Search”
- Keep:
  - bid_card_search_node_fixed.py (wired)
  - ContractorContextAdapter path from tools.py (as helper)
- Normalize:
  - Consider routing node to call tools facade (single place for filtering/rules). If not, keep both but document precedence: node authoritatively queries DB, tools adapter provides context-prefetching enhancements.

### 3) Account Creation / Profile Build

A) tools.py → COIATools.create_contractor_account(profile)
- Side effects:
  - Supabase DB insert into contractors table
- Env keys: database_simple.SupabaseDB (implicit supabase config)
- Status: Real/Stable (structured data mapping; removes None; logs success)
- Usage: Called by langgraph_nodes.account_creation_node

B) tools.py → COIATools.build_contractor_profile(company_name, google_data, web_data, license_data)
- Side effects:
  - Computes scores; merges data; saves to contractor_leads table (DB insert), enriches with social data
- Env keys: Supabase DB; optional OpenAI API for GPT extraction (indirect)
- Status: Real/Needs Polish (big mapper; writes to DB; should confirm schema stays aligned)
- Usage: Used during research/intake flows (saves a contractor lead even before account creation)
- Recommendation: Keep; but ensure schema mapping matches latest DB; consider making DB-writing optional via flag

Decision for “Account/Profile”
- Keep:
  - create_contractor_account (authoritative creation)
  - build_contractor_profile (lead enrichment; write behind a configuration flag if needed)

### 4) Memory / State Persistence

A) state_management/state_manager.py → UnifiedStateManager
- Side effects (PROVEN by code search):
  - unified_conversation_memory: upsert/select multiple times (save_state, restore_state, checkpoint)
  - unified_conversations: ensure conversation record exists, insert if missing
  - contractor_leads: upsert contractor data if company_name present
- Env keys: SupabaseDB
- Status: Real/Stable (direct DB use with structured keys/fields; logs restored counts)
- Usage: Unified graph invoke helpers (landing/bid-card) call get_state_manager() to merge saved state pre-invoke
- Decision: This is the single state manager of record; keep

B) mcp_supabase_checkpointer.py
- Side effects (PROVEN by code search):
  - langgraph_checkpoints: select/upsert/update metadata
- Status: Real/Stable; preferred checkpointer with MemorySaver fallback in unified_graph.compile()
- Usage: Configured at compile time
- Decision: Keep

### 5) LLM Clients / Streaming

- langgraph_nodes.py: AsyncAnthropic (Claude), optional AsyncOpenAI
  - Real/Stable; used by conversation/research/intelligence/bid-search messaging
- streaming_chat_router.py: AsyncOpenAI streaming helper
  - Real/Stable (optional entry surface)
- Decision: Keep as-is; ensure env keys present. Prefer consistency (Claude vs OpenAI) per environment.

### 6) Legacy / Experiments (Archive)

- bid_card_search_node.py (legacy, superseded by _fixed)
- tools_real.py, tools_real_extraction.py (experimental)
- openai_o3_agent.py, intelligent_research_agent.py (legacy agent code)
- mode_detector_fix.py, account_creation_fallback.py (legacy)
- persistent_memory.py.backup, supabase_checkpointer_rest.py.backup, unified_state_*backup*
- state.py (legacy state)

### 7) Utilities

- signup_link_generator.py
  - Status: Utility/Unreferenced in runtime wiring; not imported by unified_graph or nodes
  - Action: Keep (pending) if referenced by routers/ops; otherwise archive or move to dedicated admin utilities

---

## Best-of Selection (shortlist)

Keep (Tools façade and helpers)
- tools.py (as the single façade), selecting:
  - search_bid_cards (adapter-backed) [Keep]
  - create_contractor_account [Keep]
  - build_contractor_profile [Keep, consider flag to control DB write]
  - _tavily_discover_contractor_pages [Keep, move API key to env]
  - _extract_website_intelligence [Keep; BS path always; GPT optional]
  - _search_business_web [Keep as fallback only; document non-authoritative]
- Consider normalizing nodes to call tools façade where duplication exists (e.g., bid card search) to reduce drift.

Keep (Memory)
- state_management/state_manager.py (single state manager of record)
- mcp_supabase_checkpointer.py (preferred checkpointer)

Keep (Nodes)
- extraction_node.py
- langgraph_nodes.py (4 nodes)
- bid_card_search_node_fixed.py
- bid_submission_node.py

Keep (Orchestrator/State)
- unified_graph.py
- unified_state.py

Keep (LLM/Streaming)
- langgraph_nodes (Anthropic/OpenAI)
- streaming_chat_router.py (optional)
- streaming_handler.py (optional)

Pending / Utility
- signup_link_generator.py (keep if router references exist; else archive or relocate)

Archive (Legacy/Backups)
- bid_card_search_node.py, tools_real*.py, openai_o3_agent.py, intelligent_research_agent.py, mode_detector_fix.py, account_creation_fallback.py, *.backup, state.py

---

## Action Items

1) Move Tavily API key to env (TAVILY_API_KEY) and remove hard-coded value in _tavily_discover_contractor_pages.
2) Confirm DB schema alignment for build_contractor_profile (contractor_leads) and create_contractor_account (contractors).
3) Decide single source-of-truth for bid search:
   - Option A: Keep node doing DB select; use ContractorContextAdapter to prefetch and enrich state
   - Option B: Route node to call tools.search_bid_cards for filtering consistency
4) Lock single state manager (state_management/state_manager.py) and update any stray imports.
5) Produce archive move plan (separate doc) and quarantine legacy/backup files to avoid accidental imports.
6) Add a simple configuration (env flags) to toggle:
   - Use_Tavily (prefer Tavily pipeline vs fallback)
   - Write_Leads_On_Research (true/false)
   - Use_Claude/Use_OpenAI (consistent across nodes/streaming)

---

## Quick Capability → Implementation Map

- Research (Primary): tools._tavily_discover_contractor_pages + _extract_website_intelligence
- Research (Fallback): tools._search_business_web (fast synthesized)
- Bid Search: bid_card_search_node_fixed (DB), tools.search_bid_cards (adapter-assisted)
- Profile Lead Build: tools.build_contractor_profile (DB write to contractor_leads)
- Account Creation: tools.create_contractor_account (DB insert to contractors)
- Memory: state_manager (unified_conversation_memory & unified_conversations), mcp_supabase_checkpointer (langgraph_checkpoints)
- Entry/Streaming: unified_graph invoke_* + streaming_chat_router/handler

This comparison selects the most robust and real implementations across all variants and highlights where we should normalize and clean up. After your review, I can generate COIA_Selected_Tools.yaml and COIA_Selected_Set.yaml and then apply the archive move plan.
