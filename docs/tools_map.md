# COIA Tools Inventory and Subagent Mapping (Landing)

Purpose
- Inventory the working functions inside ai-agents/agents/coia/tools.py
- Map each function to a clean subagent (identity, research, radius, projects, account)
- Capture dependencies, side-effects, and notes for extraction/refactor

Legend
- API: external API usage (Tavily, Google)
- DB: database usage (Supabase tables)
- Side effects: persistence, network IO, etc.

Core functions in tools.py (selected for Landing)

1) research_business(company_name, location="")
- Role: quick business research via search_google_business
- API: web scraping based (not Google Places API at present)
- Side effects: None
- Subagent: research-agent
- Notes: Keep as “fast footprint” for confirmation; use research_company_basic for deeper work

2) web_search_company(company_name, location=None)
- Role: comprehensive research aggregator (Google, Tavily discovery, extraction, social, biz intelligence)
- API: Tavily (discover + extract), OpenAI (analysis) when keys present; falls back otherwise
- Side effects: None (returns comprehensive_data dict)
- Subagent: research-agent (research_company_basic)
- Notes: Ensure USE_TAVILY=true + TAVILY_API_KEY; explicit logging on fallback

3) search_google_business(company_name, location=None)
- Role: current “minimal footprint” path; uses _search_business_web (Tavily search) or fallback minimal data
- API: Tavily search (when available)
- Side effects: None
- Subagent: identity-agent for confirmation card; research-agent can re-use for bootstrap

4) _tavily_discover_contractor_pages(company_name, website_url, location=None)
- Role: Tavily discovery of relevant pages + extract API full content
- API: Tavily
- Side effects: network IO
- Subagent: research-agent (internal helper)

5) _process_tavily_content(tavily_data, company_name)
- Role: merging and analysis of discovered content; runs AI extraction; falls back to regex
- API: OpenAI (ai analysis) if key present
- Side effects: none
- Subagent: research-agent (internal helper)

6) _extract_website_intelligence(page_content, website_url, company_name)
- Role: BeautifulSoup parsing for signals; fills contractor fields
- API: none (HTML parsing)
- Side effects: none
- Subagent: research-agent (internal helper)

7) _search_social_media_profiles(company_name, location=None)
- Role: fetch social media links/metadata (currently stubbed)
- API: intended to use Playwright/web search
- Side effects: network IO when implemented
- Subagent: research-agent (internal helper)

8) _analyze_business_intelligence(comprehensive_data, company_name)
- Role: simple scoring from collected data
- API: none
- Side effects: none
- Subagent: research-agent (internal helper)

9) build_contractor_profile(company_name, google_data, web_data, license_data)
- Role: 66-field profile aggregation with scoring; optional DB write to contractor_leads behind flag WRITE_LEADS_ON_RESEARCH
- API: none (aggregation)
- DB: contractor_leads (if WRITE_LEADS_ON_RESEARCH=true)
- Side effects: DB insert when flag set
- Subagent: research-agent (optional aggregator)
- Notes: For Landing, prefer staged write via save_potential_contractor to potential_contractors; keep this as optional aggregator, not core

10) save_potential_contractor(profile)
- Role: staging upsert for potential_contractors (staging); returns staging_id
- API: none
- DB: potential_contractors upsert/insert
- Side effects: persistence
- Subagent: research-agent (stage_profile)
- Notes: Use upsert with on_conflict="id" when supported, then read-back to verify

11) create_contractor_account(contractor_profile)
- Role: create final contractor in contractors table; returns account data
- API: none
- DB: contractors insert
- Side effects: persistence
- Subagent: account-agent (create_account_from_staging)

12) search_bid_cards(contractor_profile, location=None)
- Role: fetch available projects for contractor via ContractorContextAdapter; filters by specialty
- API: none
- DB: reads via adapter (privacy-aware)
- Side effects: none
- Subagent: projects-agent (find_matching_projects)

13) _check_existing_contractor(company_name)
- Role: check existing records in contractors/contractor_leads
- API: none
- DB: read
- Side effects: none
- Subagent: research-agent (optional pre-check)

14) _search_business_web(query)
- Role: Tavily search to find official website; returns minimal business data
- API: Tavily
- Side effects: network IO
- Subagent: identity-agent (validate_company_exists minimal) and research-agent bootstrap

15) _extract_specialties(company_name), _extract_service_type(company_name), _create_minimal_business_data(...)
- Role: helpers to generate minimal footprint and default specializations
- API: none
- Side effects: none
- Subagent: identity-agent helpers

Proposed clean subagent tool surface (Landing)

identity-agent
- extract_company_info(text) -> {"company_name", "location_hint"}
- validate_company_exists(company_name, location_hint=None) -> {"exists": bool, "footprint": {address, phone, website}}
  - Uses search_google_business/_search_business_web minimal path

research-agent
- research_company_basic(company_name, location=None) -> Dict (comprehensive_data)
  - Uses web_search_company (Tavily-first; fallback logged)
- stage_profile(profile) -> {"success": True, "staging_id": "..."}
  - Calls save_potential_contractor; enforces upsert; read-back verification
- (Optional) build_profile_aggregate(...) -> Dict (if needed)

radius-agent
- update_preferences(staging_id or contractor_lead_id, services, radius) -> {"success": True}
  - Writes minimal updates to potential_contractors

projects-agent
- find_matching_projects(staging_or_profile, radius) -> List[Dict]
  - Calls search_bid_cards with tight filter rules

account-agent
- create_account_from_staging(staging_profile_or_id) -> {"success": True, "account": {...}}
  - Calls create_contractor_account; mark staging converted in potential_contractors

Extraction/refactor notes
- Keep legacy COIATools for non-Landing consumers; Landing subagents should use focused functions with explicit inputs/outputs.
- Add structured logs in each subagent (e.g., [landing][subagent=research] stage_profile ok staging_id=...).
- After deployment, switch landing_deepagent.py tools list to import functions from subagents/* modules.

Verification plan
- Supabase: confirm potential_contractors row upserted (id=contractor_lead_id or returned staging_id), fields populated.
- Streaming: /landing/stream yields events while agent.astream runs.
- Latency: target <10s first response; stream deeper work.
