"""
Landing Onboarding DeepAgent for COIA

Creates a DeepAgents-powered agent focused on the unauthenticated landing page flow:
- Extract company hints from free text
- Perform fast, real research (Tavily/GPT via coia_tools.web_search_company)
- Optionally build initial profile (writes gated by WRITE_LEADS_ON_RESEARCH)
- Ask for explicit consent before creating a contractor account
- Return structured fields and provenance notes
"""

from __future__ import annotations

import logging
from typing import Any

try:
    from deepagents import create_deep_agent
except Exception as _e:  # Do not crash import-time
    create_deep_agent = None  # type: ignore

from .subagents.identity_agent import validate_company_exists
from .subagents.research_agent import research_company_basic, extract_contractor_profile, stage_profile
from .deepagents_tools import save_potential_contractor
from .subagents.radius_agent import update_preferences, enhanced_radius_agent
from .subagents.projects_agent import find_matching_projects
from .subagents.account_agent import create_account_from_staging

logger = logging.getLogger(__name__)

def complete_research_workflow(company_name: str, location: str):
    """
    Wrapped function that forces all 3 research steps to execute sequentially.
    This solves the DeepAgents coordination issue by wrapping the workflow in a single function.
    """
    import time
    
    try:
        logger.info(f"Starting complete research workflow for {company_name} in {location}")
        start_time = time.time()
        
        # Step 1: Research company basic info
        logger.info("Step 1: Researching company basic info...")
        step1_start = time.time()
        research_data = research_company_basic(company_name, location)
        step1_time = time.time() - step1_start
        logger.info(f"Step 1 completed in {step1_time:.1f}s")
        
        # Check if we got actual data (research_company_basic returns dict with data, not 'success' key)
        if not research_data:
            return {
                'success': False,
                'error': 'Company research failed - no data returned',
                'step_failed': 1
            }
        
        # Research succeeded if we have company_name and any data
        if not research_data.get('company_name'):
            return {
                'success': False,
                'error': 'Company research failed - no company found',
                'step_failed': 1
            }
        
        # Step 2: Extract contractor profile
        logger.info("Step 2: Extracting contractor profile...")
        step2_start = time.time()
        profile_data = extract_contractor_profile(company_name, research_data)
        step2_time = time.time() - step2_start
        logger.info(f"Step 2 completed in {step2_time:.1f}s")
        
        # extract_contractor_profile returns dict with extracted data, not 'success' key
        if not profile_data:
            return {
                'success': False,
                'error': 'Profile extraction failed - no data returned',
                'step_failed': 2,
                'research_data': research_data
            }
        
        # Check if we got extracted profile
        if not profile_data.get('company_name'):
            return {
                'success': False,
                'error': 'Profile extraction failed - no company profile extracted',
                'step_failed': 2,
                'research_data': research_data
            }
        
        # Step 3: Save potential contractor
        logger.info("Step 3: Saving potential contractor...")
        step3_start = time.time()
        save_result = save_potential_contractor(profile_data)
        step3_time = time.time() - step3_start
        logger.info(f"Step 3 completed in {step3_time:.1f}s")
        
        if not save_result or not save_result.get('success'):
            return {
                'success': False,
                'error': 'Contractor save failed',
                'step_failed': 3,
                'research_data': research_data,
                'profile_data': profile_data
            }
        
        total_time = time.time() - start_time
        logger.info(f"Complete research workflow finished in {total_time:.1f}s")
        
        return {
            'success': True,
            'staging_id': save_result.get('staging_id'),
            'company_name': company_name,
            'location': location,
            'research_data': research_data,
            'profile_data': profile_data,
            'save_result': save_result,
            'execution_time': total_time,
            'step_times': {
                'research': step1_time,
                'extraction': step2_time,
                'save': step3_time
            }
        }
        
    except Exception as e:
        logger.error(f"Complete research workflow error: {e}")
        return {
            'success': False,
            'error': str(e),
            'step_failed': 'exception'
        }

# Sync wrapper for enhanced radius agent
def enhanced_radius_preferences_sync(
    identifier: str,
    services: list = None,
    radius_miles: int = None,
    contractor_type_ids: list = None,
    city: str = None,
    state: str = None,
    zip_code: str = None,
    suggest_contractor_types: bool = True
):
    """
    Synchronous wrapper for enhanced_radius_agent for DeepAgents compatibility
    """
    import asyncio
    
    try:
        # Check if we're already in an event loop
        loop = asyncio.get_running_loop()
        # We're in an event loop, create a task in a thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run,
                enhanced_radius_agent(
                    identifier=identifier,
                    services=services,
                    radius_miles=radius_miles,
                    contractor_type_ids=contractor_type_ids,
                    city=city,
                    state=state,
                    zip_code=zip_code,
                    suggest_contractor_types=suggest_contractor_types
                )
            )
            return future.result()
    except RuntimeError:
        # No event loop running, safe to use asyncio.run
        return asyncio.run(
            enhanced_radius_agent(
                identifier=identifier,
                services=services,
                radius_miles=radius_miles,
                contractor_type_ids=contractor_type_ids,
                city=city,
                state=state,
                zip_code=zip_code,
                suggest_contractor_types=suggest_contractor_types
            )
        )

# Import BSA-copied tools
try:
    from .subagents.projects_agent_bsa import search_projects_sync as bsa_projects
    BSA_TOOLS_AVAILABLE = True
    logger.info("BSA-copied tools loaded successfully")
except ImportError as e:
    logger.warning(f"Could not import BSA-copied tools: {e}")
    BSA_TOOLS_AVAILABLE = False
    bsa_projects = None

_agent = None  # cached instance


def clear_agent_cache():
    """
    Clear the cached DeepAgents agent instance to force re-initialization.
    Use this when API keys or configuration changes.
    """
    global _agent
    _agent = None
    logger.info("DeepAgent cache cleared - will re-initialize on next call")


def _instructions() -> str:
    """
    System prompt for Landing Onboarding Agent.
    """
    return """
You are COIA (Contractor Onboarding Intelligence Agent) for InstaBids.

CRITICAL: CONTEXT RESTORATION AWARENESS
- If conversation context includes contractor_lead_id, company_name, staging_id, or research_findings, you are continuing a previous conversation
- When continuing: Reference the company name and previous information naturally
- When continuing: Skip steps already completed (like research if staging_id exists)
- When continuing: Acknowledge their business and continue where you left off

SOPHISTICATED CONVERSATIONAL FLOW - FOLLOW THIS EXACT SEQUENCE:

STEP 1: GREETING & COMPANY EXTRACTION WITH IMMEDIATE RESEARCH
- When contractor mentions BOTH company name AND location in first message, IMMEDIATELY delegate to research-agent
- The research-agent will execute the complete 3-step workflow automatically using complete_research_workflow()
- If contractor mentions company but NO location, ask: "Great! What city is your business located in?"
- When they provide location, IMMEDIATELY delegate to research-agent

STEP 2: BUSINESS CONFIRMATION (After research-agent completes)
- research-agent will return with Google Business data and staging_id
- Show business confirmation: "Awesome! Is this your business? [Show Google Business details]"
- Continue with InstaBids value proposition

If NO to Google Business:
- Ask: "No problem! Do you already have an established business or are you just getting started?"
- Get feel for their business maturity and location

STEP 3: BUSINESS CONFIRMATION & INSTABIDS VALUE PROP  
Once business is confirmed by research-agent:
- "Perfect! Let me tell you what makes InstaBids different:"
- "• Message homeowners for FREE - no upfront costs"
- "• Get apples-to-apples project comparisons"  
- "• You only pay if the homeowner selects you"
- "• Send soft quotes first - avoid time-wasting sales meetings"
- "• Save money you can pass on to homeowners"
- The research should already be complete with staging_id available

STEP 4: CONTRACTOR TYPE & SERVICES IDENTIFICATION
- "What type of contractor are you? (Roofing, landscaping, electrical, etc.)"
- "What's your typical service radius from [CITY]?"
- Use radius-agent to identify contractor type and set preferences
- WHILE doing this, start searching for matching bid cards in background

STEP 5: PROJECT PREVIEW (Show results from background search)
- "While we've been chatting, I found some projects that might be perfect for you:"
- Show 3-5 matching bid cards with distances and project details
- "These are live projects from homeowners in your area"

STEP 6: DEEPER RESEARCH (If interested)
- If they want to see more: "Let me do a deeper dive on your business profile..."
- NOW trigger the full research workflow (research_company_basic → extract_contractor_profile → save_potential_contractor)
- Show progress: "Analyzing your website... Building your profile... Almost done..."

STEP 7: ACCOUNT CREATION (ONLY IF THEY'RE EXCITED)
- Only if they're engaged: "Ready to start bidding on these projects?"
- Create account and show them how to submit their first bid

CRITICAL UX PRINCIPLES:
- FAST responses first (identity-agent takes 2-3 seconds)
- Sales conversation DURING background processing
- Show value proposition while tools run in background
- Multiple agents work concurrently (research + bid search + contractor typing)
- UI shows "Working in background..." indicators
- Full research only AFTER they're interested

BACKGROUND AGENT COORDINATION:
- identity-agent: Fast Google Business validation (2-3s)
- research-agent: Full profile building (50s) - RUN IN BACKGROUND
- radius-agent: Contractor type + radius collection (1s)  
- projects-agent: Bid card matching (5s) - RUN CONCURRENTLY
- Show progress indicators for all background operations

MEMORY MANAGEMENT:
- staging_id from research operation - THIS IS CRITICAL! Store it and pass to all subsequent agents
- When research-agent returns staging_id, ALWAYS store it in conversation memory
- ALWAYS pass staging_id (not company name!) to radius-agent, projects-agent, and account-agent
- contractor_type, radius, services for project matching
- conversation_stage to track where we are in the flow

CRITICAL DELEGATION RULES:
- IF user message contains BOTH company name AND location → IMMEDIATELY delegate to research-agent
- EXAMPLE: "JM Holiday Lighting in Fort Lauderdale" → delegate to research-agent NOW
- EXAMPLE: "We're ABC Roofing based in Miami Florida" → delegate to research-agent NOW
- DO NOT ask "Do you have Google Business listing?" if location is already provided
- DELEGATE FIRST, ask questions after research completes

CRITICAL PARAMETER PASSING:
- research-agent returns: {"success": true, "staging_id": "actual-uuid-value", ...}
- You MUST extract and store this staging_id
- radius-agent requires: identifier=staging_id (NOT company name!)
- projects-agent requires: staging_id parameter
- account-agent requires: staging_id parameter
"""


def get_agent() -> Any:
    """
    Returns a cached DeepAgents agent instance for the landing flow.
    Safe to call repeatedly.
    """
    global _agent
    if _agent is not None:
        return _agent

    if create_deep_agent is None:
        raise RuntimeError(
            "deepagents is not installed or import failed. "
            "Install with `pip install deepagents` and ensure environment is configured."
        )

    tools = [
        validate_company_exists,       # identity minimal confirmation
        complete_research_workflow,    # research - wrapped 3-step workflow (FIXED)
        update_preferences,            # radius (legacy)
        enhanced_radius_preferences_sync, # radius (enhanced with contractor type expansion)
        find_matching_projects,        # projects (legacy)
        create_account_from_staging,   # account promotion
    ]
    
    # Add BSA-copied tools if available
    if BSA_TOOLS_AVAILABLE:
        tools.append(bsa_projects)     # BSA's exact search_bid_cards logic
        logger.info("Using BSA-copied tools for project search")

    # Subagents: identity, research, radius, projects, account
    identity_subagent = {
        "name": "identity-agent",
        "description": "FAST Google Business validation (2-3 seconds) for immediate confirmation.",
        "prompt": (
            "You do FAST Google Business validation using validate_company_exists. "
            "This takes only 2-3 seconds and returns basic business info from Google. "
            "Your job: Call validate_company_exists(company_name, location) and return: "
            "- Business name, address, phone, rating, review count "
            "- Confirmation: 'Is this your business?' "
            "- DO NOT do deep research - that comes later if they're interested "
            "- Keep response fast and focused on validation only"
        ),
    }

    research_subagent = {
        "name": "research-agent", 
        "description": "Triggered when user provides company name AND location. Executes complete 3-step research workflow using wrapped function.",
        "prompt": (
            "TRIGGER CONDITIONS: When user mentions their company name AND provides a location (city/state).\n"
            "\n"
            "IMMEDIATE ACTION: Call complete_research_workflow(company_name, location)\n"
            "\n"
            "This single function executes ALL 3 research steps automatically:\n"
            "1. research_company_basic - Gets raw company data from web\n"
            "2. extract_contractor_profile - Uses GPT-4o to extract structured profile\n"
            "3. save_potential_contractor - Saves to database and returns staging_id\n"
            "\n"
            "EXECUTION EXAMPLE:\n"
            "User says: 'Fort Lauderdale, Florida'\n"
            "You respond: 'I'll research your company now...'\n"
            "\n"
            "Then execute:\n"
            "complete_research_workflow('JM Holiday Lighting', 'Fort Lauderdale, Florida')\n"
            "\n"
            "The function returns:\n"
            "- success: boolean\n"
            "- staging_id: UUID for subsequent agents\n" 
            "- company_name, location: confirmed details\n"
            "- research_data: Google Business info\n"
            "- profile_data: extracted contractor profile\n"
            "- execution_time: total time taken\n"
            "\n"
            "After completion, respond with:\n"
            "'Awesome! Is this your business? [Show Google Business details]'\n"
            "\n"
            "CRITICAL: Store the staging_id in conversation context for other agents!\n"
        ),
    }

    radius_subagent = {
        "name": "radius-agent",
        "description": "Collect services/radius preferences and update staged profile.",
        "prompt": (
            "Update contractor preferences in the staged profile.\n"
            "CRITICAL: You MUST receive a staging_id (UUID) from the research-agent first!\n"
            "\n"
            "WORKFLOW:\n"
            "1. Get staging_id from conversation context (should be a UUID like 'abc123-def456-...')\n"
            "2. Collect contractor's services and service radius\n" 
            "3. Call update_preferences(identifier=staging_id, services=[...], radius_miles=X)\n"
            "   - identifier MUST be the staging_id UUID, NOT the company name!\n"
            "4. If enhanced tools available, use enhanced_radius_preferences_sync with staging_id\n"
            "\n"
            "PARAMETER REQUIREMENTS:\n"
            "- identifier: The staging_id UUID from research-agent (REQUIRED)\n"
            "- services: List of services the contractor offers\n"
            "- radius_miles: Service radius in miles\n"
            "- city/state/zip_code: Optional location details\n"
        ),
    }

    projects_subagent = {
        "name": "projects-agent",
        "description": "Preview matching projects using BSA's superior search method with real bid cards.",
        "prompt": (
            "Find and show REAL projects for contractors using BSA's proven search.\n"
            "CRITICAL: You need the staging_id (UUID) from research-agent!\n"
            "\n"
            "PRIMARY WORKFLOW (Use BSA Tools):\n"
            "1. Get staging_id from conversation context (UUID format)\n"
            "2. Call search_projects_sync(staging_id=staging_id) - BSA's proven search\n"
            "3. BSA automatically gets contractor ZIP, specialties, and radius from staging profile\n"
            "4. Show actual bid cards with real project details, budgets, and distances\n"
            "\n"
            "FALLBACK WORKFLOW (If BSA unavailable):\n"
            "1. Use find_matching_projects(staging_id) as backup\n"
            "\n"
            "PRESENTATION:\n"
            "- Show project titles, budgets, locations, distances\n"
            "- Explain match quality based on contractor specialties\n"
            "- Include bid card numbers for reference\n"
            "- Mention timeline and urgency\n"
            "\n"
            "BSA tools provide REAL bid cards, not mock data!"
        ),
    }

    account_subagent = {
        "name": "account-agent",
        "description": "Create contractor account only after explicit consent (promotion step).",
        "prompt": (
            "Create contractor account ONLY after explicit consent.\n"
            "CRITICAL: You need the staging_id (UUID) from research-agent!\n"
            "\n"
            "WORKFLOW:\n"
            "1. Verify user explicitly consents to account creation\n"
            "2. Get staging_id from conversation context (should be a UUID)\n"
            "3. Call create_account_from_staging(staging_id) to promote profile\n"
            "   - The staging_id MUST be the UUID, NOT the company name!\n"
            "4. On success, return contractor_id and account details\n"
            "5. Mark staging as converted in database\n"
            "\n"
            "NEVER create account without explicit user consent!"
        ),
    }

    _agent = create_deep_agent(
        tools=tools,
        instructions=_instructions(),
        model="gpt-4o",  # Use OpenAI GPT-4o instead of default Claude/Anthropic
        subagents=[identity_subagent, research_subagent, radius_subagent, projects_subagent, account_subagent],
    )
    logger.info("Landing DeepAgent created")
    return _agent


# Usage example (caller responsibility):
# agent = get_agent()
# result = agent.invoke({"messages": [{"role": "user", "content": "I run JM Holiday Lighting in Fort Lauderdale"}]})
# The router should wrap this with state restore/save as needed.
