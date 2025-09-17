# COIA Slash Command Spec (Agent 4 – Contractor Onboarding Intelligence Assistant)

Purpose
- One canonical slash-command interface to invoke the curated COIA runtime with the correct context, memory, and mode.
- Maps cleanly to our FastAPI router (ai-agents/routers/unified_coia_api.py) which calls unified_graph invoke_* helpers.
- Keeps the agent on-task with the proper flags and state conventions.

Authoritative runtime references
- Orchestrator/State/Nodes: ai-agents/agents/coia/unified_graph.py, unified_state.py, langgraph_nodes.py, extraction_node.py, bid_card_search_node_fixed.py, bid_submission_node.py
- Tools: ai-agents/agents/coia/tools.py (export: coia_tools)
- Memory: ai-agents/agents/coia/state_management/state_manager.py, ai-agents/agents/coia/mcp_supabase_checkpointer.py
- Router: ai-agents/routers/unified_coia_api.py
- Runtime README: ai-agents/agents/coia/README.md
- Selected set and inventory: docs/meta/COIA_Selected_Set.yaml, docs/meta/COIA_File_Inventory.md

---

## Commands

### /coia.run
Invoke the COIA agent in a specific entry flow.

Parameters
- entry: landing | chat | bidcard | research | intelligence
- message: string (the user’s message; omit for research/intelligence if not needed)
- session_id: string (per conversation context)
- contractor_lead_id: string (optional; required for bidcard flow; recommended for persistent memory in chat)
- options (optional object):
  - use_tavily: boolean (default via USE_TAVILY env)
  - write_leads_on_research: boolean (default via WRITE_LEADS_ON_RESEARCH env)

Behavior (router mapping)
- landing → POST /landing (CoIAResponse)
  - Ensures contractor_lead_id (landing-xxxxxxxxxxxx) if not provided
  - Restores unified memory via state_manager before invoke
  - Checkpointer ns=coia_landing
- chat → POST /chat (CoIAResponse)
  - Thread: contractor_lead_id if present, else session_id
  - Checkpointer ns=coia_chat, checkpoint_id=chat_{thread_id}
  - (Optional) Memory restore could be added similarly if desired
- bidcard → POST /bid-card-link (CoIAResponse)
  - Requires: contractor_lead_id, verification_token
  - Thread: contractor_lead_id, ns=coia_bidcard, checkpoint_id=bidcard_{thread_id}
  - Preloads ContractorContextAdapter data into initial state
- research → POST /research (CoIAResponse)
  - Thread: session_id, ns=coia_research
  - company_data required (see payload example below)
- intelligence → POST /intelligence (CoIAResponse)
  - Thread: session_id, ns=coia_intelligence
  - contractor_data required (see payload example below)

Consent and state rules
- Never auto-create accounts; account creation requires explicit user confirmation (conversation node sets account_creation_confirmed; bid_submission_node/account_creation_node check it).
- contractor_created must be set True by the account creation node (already wired).
- Progressive research: fast initial response; deep research only after confirmation.
- Memory: landing restores unified memory; other flows may optionally pre-merge.

Environment and flags
- Required: ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_ANON_KEY
- Recommended: TAVILY_API_KEY (enable real Tavily discovery)
- Optional: OPENAI_API_KEY (optional GPT extraction/streaming), GOOGLE_MAPS_API_KEY (if Places is re-enabled later)
- Feature flags:
  - USE_TAVILY=true/false
  - WRITE_LEADS_ON_RESEARCH=true/false

---

## Examples

Base URL
- Let BACKEND = http://localhost:8008 (router is typically mounted under a service backend)

1) Landing (onboarding)
```
curl -X POST "$BACKEND/landing" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hi, I run JM Holiday Lighting",
    "session_id": "sess-12345",
    "contractor_lead_id": "landing-abc123def456",
    "conversation_id": "3f3f0a9a-1111-2222-3333-abcdef123456"
  }'
```
- Restores unified memory (if any) for contractor_lead_id and saves after response.
- Returns CoIAResponse with contractor_lead_id for persistence.

2) Chat (authenticated flow)
```
curl -X POST "$BACKEND/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you show me available projects?",
    "session_id": "chat-55",
    "contractor_lead_id": "contractor-uuid-or-lead-id",
    "user_id": "user-abc"
  }'
```
- Thread ID = contractor_lead_id if set, else session_id.
- Checkpointer ns=coia_chat, checkpoint_id=chat_{thread_id}.

3) Bid card link (email entry)
```
curl -X POST "$BACKEND/bid-card-link" \
  -H "Content-Type: application/json" \
  -d '{
    "bid_card_id": "bid-xyz-123",
    "contractor_lead_id": "contractor-uuid",
    "verification_token": "secure-token-xyz",
    "session_id": "bidcard-session-11"
  }'
```
- Preloads contractor context (profile, history, available projects) via ContractorContextAdapter.
- Checkpointer ns=coia_bidcard, checkpoint_id=bidcard_{thread_id}.

4) Research (portal)
```
curl -X POST "$BACKEND/research" \
  -H "Content-Type: application/json" \
  -d '{
    "company_data": {
      "name": "Acme Electric",
      "website": "https://acmeelectric.com",
      "city": "Fort Lauderdale",
      "state": "FL"
    },
    "session_id": "research-777"
  }'
```

5) Intelligence (dashboard)
```
curl -X POST "$BACKEND/intelligence" \
  -H "Content-Type: application/json" \
  -d '{
    "contractor_data": {
      "company_name": "Acme Electric",
      "specialties": ["Electrical", "Lighting"],
      "service_areas": ["Broward County", "Palm Beach County"],
      "business_info": {"google_rating": 4.9, "review_count": 225},
      "research_data": {"status": "done"}
    },
    "session_id": "intel-333"
  }'
```

---

## Optional wrapper command (for a CLI or chat front-end)

Command: /coia.run
```
/coia.run entry=landing \
  message="Hi I run JM Holiday Lighting" \
  session_id="sess-12345" \
  contractor_lead_id="landing-abc123def456" \
  options.use_tavily=true \
  options.write_leads_on_research=false
```

Front-end or orchestrator should translate to the corresponding HTTP call above based on entry:
- landing → POST /landing
- chat → POST /chat
- bidcard → POST /bid-card-link
- research → POST /research (use company_data instead of message)
- intelligence → POST /intelligence (use contractor_data instead of message)

---

## Return shape

All flows return CoIAResponse:
- success: bool
- response: AI message text (first meaningful response)
- current_mode: e.g., conversation, research, intelligence, bid_card_search
- interface: landing_page | chat | research_portal | intelligence_dashboard | bid_card_link
- session_id, contractor_lead_id
- contractor_profile, profile_completeness, completion_ready
- contractor_created, contractor_id
- research_completed, research_findings, business_info, company_name, intelligence_data
- last_updated, transition_reason, error_details
- bidCards (camelCase array), aiRecommendation (if present)

---

## Guardrails (enforced by nodes)

- Consent: Account creation only after explicit user confirmation (conversation node sets account_creation_confirmed; account_creation_node checks flags and is interrupt-protected).
- State safety: UnifiedCoIAState reducers prevent unbounded growth and duplicate lists (available_capabilities, active_tools, bid_cards_attached, marketplace_links).
- Memory: Landing restores unified memory; checkpointer keeps graph state across turns for all flows.

---

## Troubleshooting

- “No results / no state saved” on landing:
  - Ensure Supabase env is set and state_manager is reachable; logs will show restore/save paths.
- “Bidcard entry has no context”:
  - Verify contractor_lead_id is a real lead (not prefixed bidcard-); adapter preloading uses that to pull context.
- “Research doesn’t call Tavily”:
  - Ensure TAVILY_API_KEY set and USE_TAVILY=true; tools.py gates discovery accordingly.
- “Duplicate contractor inserts”:
  - Use tools.create_contractor_account as the only contractors insert path; nodes should delegate to it (already implemented).
