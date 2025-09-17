# Landing Page Contractor Flow — DeepAgents Landing Agent (Updated)

Date: 2025-01-13
Owner: Agent 4 – COIA (Landing Onboarding)  
Status: FULLY OPERATIONAL with Memory Persistence
Location: ai-agents/agents/coia/docs/LANDING_FLOW.md

Purpose
- Make the Landing agent self-sufficient: this file describes exactly what the unauthenticated landing flow must do, which tools to call, what it saves, and when to promote to a full contractor account.
- This supersedes the older external doc for Landing; keep this in-agent so the agent can self-orient at runtime.

Key Updates vs legacy doc
- Business example updated to “JM Holiday Lighting” (instead of “Shame Holiday Lighting”)
- Progressive research strictly enforced (fast initial result → ask for confirmation → deeper research on request)
- Staging-first write policy:
  - Write research/profile results to potential_contractors (staging) during Landing flow
  - Promote to contractors only after explicit user consent at account creation
- Subagents defined for the Landing deep agent (see below)
- Streaming endpoint recommended: /landing/stream

User Story Example
User: “Hey, I’m Justin, I own JM Holiday Lighting. Do you guys have any bids for that?”

Complete Conversation Flow (Landing)

STAGE 1: Initial Contact & Business Identification
- SYSTEM:
  1) Extract business name: “JM Holiday Lighting”
  2) (Optional) Extract user name if present: “Justin”
  3) Extract service type keywords (e.g., “holiday lighting”)
- AGENT:
  “Hi Justin! I’d be happy to help. Let me quickly check JM Holiday Lighting so I have the right info.”
- TOOL (fast lookup for confirmation footprint):
  - research_business(company_name="JM Holiday Lighting", location_hint?) — fast mode, return minimal footprint (address/phone/website if available)
- RESULT:
  - Present a concise confirmation card with name, city/state (or zip), and phone

STAGE 2: Business Confirmation
- AGENT:
  “Great! I found JM Holiday Lighting. Is this you?
   - Location: [Address, City, State]
   - Phone: [Phone]
   - Website: [Website]
   Is this correct?”
- USER:
  “Yes, that’s me!”
- NOTE: If “No,” ask for correction and return to STAGE 1.

STAGE 3: Deeper Research & Profile Staging (potential_contractors)
- Preconditions: User confirms business identity
- SYSTEM:
  1) Call research_business (web_search_company) to gather verified data
  2) (Optional) Build a profile snapshot
  3) Save/update the staging record in potential_contractors with core fields (phone, email, website, services, years_in_business, city/state, etc.)
- AGENT:
  “Got it. I’ve pulled together your business info. Do you also offer any other services besides holiday lighting? And what radius should I use to find projects (10, 25, or 50 miles)?”

STAGE 4: Service Expansion & Radius Selection
- USER:
  “I also do outdoor lighting and landscape lighting. Check 25 miles.”
- SYSTEM:
  1) Update the staged profile with additional services
  2) Save updates to potential_contractors
  3) Search bid cards (ZIP radius / helper) for matching projects
- TOOL:
  - search_bid_cards(contractor_profile, location/radius)

STAGE 5: Bid Card Presentation (optional in Landing)
- AGENT:
  “Excellent! I found [X] projects within 25 miles:
   - Holiday Lighting Installation — $2,500–$4,000 (Boca Raton, FL)
   - Christmas Display Setup — $1,500–$3,000 (Delray Beach, FL)
   Would you like details, or should I help you get set up to bid?”
- NOTE:
  - Keep details concise; full detail after signup is fine
  - Landing can preview; full project experience is in portal

STAGE 6: Account Creation (Consent + Promotion)
- USER:
  “Yes, help me get set up!”
- AGENT:
  “I’ll create your InstaBids contractor account. I’ll use the info I’ve gathered. Confirm you’d like me to create your account now.”
- SYSTEM (only after explicit consent):
  1) create_contractor_account(profile_from_staging)
  2) On success:
     - Mark staging record in potential_contractors as converted (store promoted_contractor_id)
     - Set contractor_created=true and return normalized account data
- AGENT (success):
  “Your account is ready. I created it with:
   - Email: [email]
   - Temporary password: [generated]
   You can now view full project details, message homeowners directly, and submit quotes.”

Backend Implementation (Landing)

Tools (source of truth: ai-agents/agents/coia/tools.py)
- research_business → wraps coia_tools.web_search_company
- build_profile (optional snapshot) → wraps coia_tools.build_contractor_profile
- save_potential_contractor (recommended wrapper) → save/update staged profile into potential_contractors (if build_profile currently targets contractor_leads, add a dedicated save method)
- search_bid_cards → wraps coia_tools.search_bid_cards (adapter-backed)
- create_contractor_account → authoritative contractors insert (promotion step)

Data Destinations
- potential_contractors (staging):
  - Fields: company_name, phone, email, website, services[], years_in_business, city, state, zip, search_radius, extras (JSON), updated_at
  - Link: contractor_lead_id or staging_id
- contractors (production account):
  - Only after explicit consent via create_contractor_account
  - On promotion, write promoted_contractor_id back to staging

API Endpoints (FastAPI)
- POST /landing (already present)
  - Feature flag USE_DEEPAGENTS_LANDING=true to invoke Landing DeepAgent
  - Restore unified memory before invoke; save_state after
  - Conversation logging to backend supported if conversation_id provided
- POST /landing/stream (recommended)
  - Streaming version that forwards DeepAgents astream tokens (SSE)

Consent & Guardrails (must enforce)
- Never create accounts without explicit user confirmation
- Set contractor_created=true only after create_contractor_account success
- Prefer real verified data; if unknown, return “unknown,” do not hallucinate
- Fast initial response: keep Stage 1/2 lightweight

Subagents for the Landing DeepAgent

identity-agent (extract/confirm)
- Tools: extract_company_info (seed), research_business (minimal footprint for confirmation only)
- Prompt: Extract/confirm the business; present concise card with address/phone/website; do not do heavy research yet

research-agent (verified data + staging)
- Tools: research_business (full web search), optional build_profile, save_potential_contractor
- Prompt: Gather verified data; build snapshot; write to potential_contractors; no hallucination

radius-agent (preferences)
- Tools: none (state updates only)
- Prompt: Collect services/radius; update staging; keep it short

projects-agent (optional preview)
- Tools: search_bid_cards
- Prompt: Show a small set of matching projects with rationale; preview only

account-agent (promotion)
- Tools: create_contractor_account
- Prompt: Only act after explicit consent; then create account; on success set contractor_created=true and return normalized account data; ensure staging is marked converted (promoted_contractor_id)

Streaming & Conversation Logging

Streaming
- Add /landing/stream to stream astream tokens to the frontend
- Token cadence: fast initial confirmation, then research chunks as needed

Unified Conversations (Backend)
- If conversation_id present:
  - POST assistant messages to /api/conversations/message
  - Store contractor_profile/research_findings in /api/conversations/memory
- This path already exists in /landing router and continues to work with DeepAgents branch

Performance Targets
- Stage 1–2: < 10 seconds to first meaningful response
- Deeper research only after confirmation or user request
- Avoid running multiple heavy tools at once

Success Criteria (Landing)
- Feels natural and consultative
- Shows actual projects when asked
- Writes staging profile to potential_contractors
- Promotes to contractors on explicit consent
- Generates temporary credentials and returns normalized account data
- Saves unified memory for return visitors

Appendix: Quick curl test
Landing (DeepAgents on)
- Set USE_DEEPAGENTS_LANDING=true
- curl -X POST http://localhost:8008/landing \
  -H "Content-Type: application/json" \
  -d '{"message":"I run JM Holiday Lighting in Fort Lauderdale","session_id":"sess-landing-1","contractor_lead_id":"landing-test-001","conversation_id":"3f3f0a9a-1111-2222-3333-abcdef123456"}'
- Expect: confirmation → structured fields → (optional) staging save → consent prompt for account creation
