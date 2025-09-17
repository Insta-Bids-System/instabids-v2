# /coia.run — Agent-Facing Slash Command (Self-Onboarding + Invoke)

Purpose
- Keep Agent 4 (COIA) on track by making it load its own identity, structure, and rules before any run.
- All essential references live inside this agent folder so the agent can self-orient without chasing external paths.

Primary bootstrap doc
- ai-agents/agents/coia/docs/ONBOARDING.md  (read this first on every run)

File map (machine-readable)
- ai-agents/agents/coia/docs/FILE_MAP.json  (load and cache for quick path access)

Runtime README (curated)
- ai-agents/agents/coia/README.md

Router/Invoke (HTTP mapping lives in API; see also docs/meta/COIA_SlashCommand.md for external callers)
- FastAPI: ai-agents/routers/unified_coia_api.py
- Orchestrator invoke helpers: ai-agents/agents/coia/unified_graph.py

---

## Command

/coia.run

Parameters
- entry: landing | chat | bidcard | research | intelligence
- message: string
- session_id: string
- contractor_lead_id: string (recommended; required for bidcard)
- options (object)
  - bootstrap: boolean (default true) → if true, perform self-onboarding steps below
  - use_tavily: boolean (fallback to env)
  - write_leads_on_research: boolean (fallback to env)
  - verification_token: string (required for bidcard)

Self-onboarding steps (when options.bootstrap=true)
1) Read ai-agents/agents/coia/docs/ONBOARDING.md
2) Read ai-agents/agents/coia/docs/FILE_MAP.json
3) Read ai-agents/agents/coia/README.md
4) Read orchestrator/state/nodes/tools/memory files listed in FILE_MAP.json
5) Validate env flags USE_TAVILY, WRITE_LEADS_ON_RESEARCH; log effective values
6) Record “bootstrap complete” in memory (e.g., via mcp__cipher__ask_cipher) with file map + flags
7) Enforce consent rules and single write path (delegate contractor creation to tools.create_contractor_account)
8) Proceed to invoke appropriate entry flow (see below)

Entry flow behavior (agent-internal)
- landing:
  - Ensure contractor_lead_id; restore unified memory; invoke invoke_coia_landing_page
- chat:
  - Thread = contractor_lead_id or session_id; invoke invoke_coia_chat
- bidcard:
  - Require contractor_lead_id & verification_token; preload ContractorContextAdapter; invoke invoke_coia_bid_card_link
- research:
  - expect company_data on HTTP side; this command will pass message as “Research company: …” when driving internally
- intelligence:
  - expect contractor_data on HTTP side; this command will pass message as “Enhance intelligence for: …” when driving internally

State/Checkpoint rules (must respect)
- chat: ns=coia_chat, checkpoint_id=chat_{thread}
- research: ns=coia_research, checkpoint_id=research_{session_id}
- intelligence: ns=coia_intelligence, checkpoint_id=intelligence_{session_id}
- landing: ns=coia_landing (thread=contractor_lead_id)
- bidcard: ns=coia_bidcard, checkpoint_id=bidcard_{thread}

Guardrails (enforced by nodes + orchestrator)
- Consent-based account creation only; set account_creation_confirmed before creating
- After success, contractor_created must be set True
- Unique+capped reducers in unified_state.py prevent runaway lists
- Node-of-record for bid search = bid_card_search_node_fixed (ZIP radius)
- Node-of-record for account creation = bid_submission_node.account_creation_node which delegates to tools.create_contractor_account

Examples (agent-internal semantics)
/coia.run entry=landing message="Hi I run JM Holiday Lighting" session_id="sess-123" contractor_lead_id="landing-abc123" options.bootstrap=true

/coia.run entry=chat message="Show me available projects near 33308" session_id="sess-456" contractor_lead_id="lead-uuid" options.bootstrap=true

/coia.run entry=bidcard message="I'm interested in this project" session_id="sess-789" contractor_lead_id="lead-uuid" options.verification_token="token-xyz" options.bootstrap=true

---

Implementation note (for orchestrator/chat front-end)
- This is the agent-facing spec. If you need HTTP mappings, use docs/meta/COIA_SlashCommand.md (external callers) which points to FastAPI endpoints in ai-agents/routers/unified_coia_api.py.
