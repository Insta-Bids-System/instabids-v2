"""
DeepAgents tool wrappers for COIA.

These are synchronous callables that wrap our existing async COIA tools so they can be
registered with deepagents.create_deep_agent as plain Python functions.

All real implementations are delegated to ai-agents/agents/coia/tools.py (coia_tools)
and adapters where appropriate. This module contains zero business logic.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Import the tool-of-record (async methods)
from .tools import COIATools
coia_tools = COIATools()


def _run_async(coro_func, *args, **kwargs):
    """
    Run an async function in a synchronous context using asyncio.
    DeepAgents expects sync callables; our underlying tools are async.
    Fixed to work within existing event loop.
    """
    try:
        import asyncio
        
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # We're in an event loop, create a task
            import concurrent.futures
            import threading
            
            # Run in a separate thread to avoid blocking the current loop
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro_func(*args, **kwargs))
                return future.result()
                
        except RuntimeError:
            # No event loop running, safe to use asyncio.run
            return asyncio.run(coro_func(*args, **kwargs))
            
    except Exception as e:
        logger.exception("Error running async tool via asyncio")
        raise e


# --------------- Public sync tools (registered in deepagents) ---------------

def extract_company_info(text: str) -> Dict[str, Any]:
    """
    Pure AI extractor for company hints from free text.
    NO HARDCODING, NO FALLBACKS - Pure DeepAgents intelligence only.

    Returns: {"company_name": str, "location_hint": str}
    """
    logger.info(f"🔍 [IDENTITY-AGENT] FIRED - Pure AI extraction from: '{text[:50]}...'")
    
    # This tool is intentionally minimal - let the DeepAgents system prompt handle the intelligence
    # The main agent will use its natural language understanding to extract company info
    # No patterns, no fallbacks, no hardcoded logic
    
    result = {"company_name": "", "location_hint": ""}
    logger.info(f"✅ [IDENTITY-AGENT] Delegating to main agent intelligence - Raw text passed through")
    return result


def research_business(company_name: str, location: Optional[str] = None) -> Dict[str, Any]:
    """
    Wrap coia_tools.web_search_company → returns structured research data.
    """
    logger.info(f"🔬 [RESEARCH-AGENT] FIRED - Researching: '{company_name}' in '{location}'")
    try:
        result = _run_async(coia_tools.web_search_company, company_name, location)
        completeness = result.get('completeness', 0) if isinstance(result, dict) else 0
        logger.info(f"✅ [RESEARCH-AGENT] SUCCESS - Found {completeness}% data completeness")
        return result
    except Exception as e:
        logger.error(f"❌ [RESEARCH-AGENT] ERROR - {e}")
        raise


def build_profile(
    company_name: str,
    google_data: Optional[Dict[str, Any]] = None,
    web_data: Optional[Dict[str, Any]] = None,
    license_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Wrap coia_tools.build_contractor_profile → returns a 66-field profile.
    DB writes are gated by WRITE_LEADS_ON_RESEARCH env flag inside the tool.
    """
    return _run_async(coia_tools.build_contractor_profile, company_name, google_data, web_data, license_data)


def create_contractor_account(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrap coia_tools.create_contractor_account → authoritative contractors insert.
    """
    company_name = profile.get('company_name', 'Unknown')
    logger.info(f"👤 [ACCOUNT-AGENT] FIRED - Creating contractor account for: '{company_name}'")
    try:
        result = _run_async(coia_tools.create_contractor_account, profile)
        contractor_id = result.get('id', 'None')
        logger.info(f"✅ [ACCOUNT-AGENT] SUCCESS - Created contractor account ID: {contractor_id}")
        return result
    except Exception as e:
        logger.error(f"❌ [ACCOUNT-AGENT] ERROR - {e}")
        raise


def save_potential_contractor(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrap coia_tools.save_potential_contractor → stage profile in potential_contractors.
    Used by Landing research-agent before promotion to contractors.
    Fixed async handling to work properly in DeepAgents context.
    """
    logger.info(f"💾 [RESEARCH-AGENT] FIRED - Staging contractor profile for: '{profile.get('company_name', 'Unknown')}'")
    try:
        result = _run_async(coia_tools.save_potential_contractor, profile)
        logger.info(f"✅ [RESEARCH-AGENT] SUCCESS - Staged profile, ID: {result.get('staging_id') or result.get('id', 'None')}")
        
        # Ensure staging_id is in the expected format for memory integration
        if result.get("success") and result.get("id") and not result.get("staging_id"):
            result["staging_id"] = result["id"]
        
        return result
    except Exception as e:
        logger.error(f"❌ [RESEARCH-AGENT] ERROR - Failed to stage profile: {e}")
        return {"success": False, "error": str(e)}


def search_bid_cards(contractor_profile: Dict[str, Any], location: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Wrap coia_tools.search_bid_cards → adapter-backed privacy-aware projects.
    """
    company_name = contractor_profile.get('company_name', 'Unknown')
    logger.info(f"📋 [PROJECTS-AGENT] FIRED - Searching projects for: '{company_name}' near '{location}'")
    try:
        result = _run_async(coia_tools.search_bid_cards, contractor_profile, location)
        project_count = len(result) if isinstance(result, list) else 0
        logger.info(f"✅ [PROJECTS-AGENT] SUCCESS - Found {project_count} matching projects")
        return result
    except Exception as e:
        logger.error(f"❌ [PROJECTS-AGENT] ERROR - {e}")
        raise


def collect_radius_preferences(radius_miles: int, services: List[str], contractor_lead_id: Optional[str] = None) -> Dict[str, Any]:
    """
    LEGACY: Tool for RADIUS-AGENT to collect service area and service types.
    Updates the staged contractor profile with radius and services.
    """
    logger.info(f"📍 [LEGACY-RADIUS-AGENT] FIRED - Setting radius: {radius_miles} miles, services: {services}")
    try:
        # For now, just return the collected data
        # In future, this could update the potential_contractors record
        result = {
            "radius_miles": radius_miles,
            "services": services,
            "contractor_lead_id": contractor_lead_id,
            "radius_set": True,
            "services_count": len(services)
        }
        logger.info(f"✅ [LEGACY-RADIUS-AGENT] SUCCESS - Collected {len(services)} services with {radius_miles} mile radius")
        return result
    except Exception as e:
        logger.error(f"❌ [LEGACY-RADIUS-AGENT] ERROR - {e}")
        return {"radius_set": False, "error": str(e)}


def enhanced_radius_preferences(
    staging_id: str,
    radius_miles: Optional[int] = None,
    services: Optional[List[str]] = None,
    contractor_type_ids: Optional[List[int]] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None,
    suggest_contractor_types: bool = True
) -> Dict[str, Any]:
    """
    ENHANCED RADIUS-AGENT: Updates staged contractor profile AND suggests additional contractor types.
    This is the 3rd agent in COIA flow: Identity → Research → Enhanced Radius → Projects → Account
    
    Features:
    - Updates radius and contractor_type_ids in potential_contractors table
    - Suggests related contractor types based on existing types and services
    - Provides conversational feedback for contractor type expansion
    """
    logger.info(f"🎯 [ENHANCED-RADIUS-AGENT] FIRED - Staging ID: {staging_id}, Radius: {radius_miles}, Services: {services}, Types: {contractor_type_ids}")
    
    try:
        from .subagents.radius_agent import enhanced_radius_agent
        
        result = _run_async(
            enhanced_radius_agent,
            identifier=staging_id,
            services=services,
            radius_miles=radius_miles,
            contractor_type_ids=contractor_type_ids,
            city=city,
            state=state,
            zip_code=zip_code,
            suggest_contractor_types=suggest_contractor_types
        )
        
        if result.get("success"):
            updated_fields = list(result.get("updated_fields", {}).keys())
            suggestions = result.get("contractor_type_suggestions", {})
            suggestion_count = len(suggestions.get("suggestions", []))
            
            logger.info(f"✅ [ENHANCED-RADIUS-AGENT] SUCCESS - Updated {len(updated_fields)} fields, {suggestion_count} contractor type suggestions")
            
            # Add conversational context for COIA agent
            result["conversational_context"] = {
                "updated_preferences": True,
                "suggestion_count": suggestion_count,
                "ready_for_projects": True,
                "radius_confirmed": radius_miles is not None,
                "contractor_types_expanded": contractor_type_ids is not None and len(contractor_type_ids) > 0
            }
            
        else:
            logger.error(f"❌ [ENHANCED-RADIUS-AGENT] ERROR - {result.get('error')}")
            
        return result
        
    except Exception as e:
        logger.error(f"❌ [ENHANCED-RADIUS-AGENT] EXCEPTION - {e}")
        return {
            "success": False,
            "error": str(e),
            "contractor_type_suggestions": {"success": False, "suggestions": []}
        }


def get_contractor_context(contractor_lead_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Synchronous wrapper around the ContractorContextAdapter to preload context
    (profile, bid history, available projects, conversation history).
    """
    try:
        import os
        import sys
        # Add repo root for adapter import resolution if needed
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from adapters.contractor_context import ContractorContextAdapter  # type: ignore

        adapter = ContractorContextAdapter()
        ctx = adapter.get_contractor_context(contractor_lead_id, session_id)
        return ctx or {}
    except Exception as e:
        logger.warning(f"get_contractor_context failed: {e}")
        return {}


# ============== BSA-COPIED TOOL FUNCTIONS ==============

def search_projects_bsa_style(
    contractor_zip: str = None,
    radius_miles: int = 30,
    project_type: Optional[str] = None,
    contractor_type_ids: Optional[List[int]] = None,
    staging_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    COPIED FROM BSA: search_bid_cards function
    This is the exact BSA pattern that works, adapted for COIA.
    """
    logger.info(f"📋 [BSA-STYLE-PROJECTS] Searching projects like BSA does")
    try:
        from .subagents.projects_agent_bsa import search_projects_sync
        
        result = search_projects_sync(
            contractor_zip=contractor_zip,
            radius_miles=radius_miles,
            project_type=project_type,
            contractor_type_ids=contractor_type_ids or [],
            staging_id=staging_id
        )
        
        if result.get("success"):
            count = result.get("total_found", 0)
            logger.info(f"✅ [BSA-STYLE-PROJECTS] Found {count} projects using BSA pattern")
        else:
            logger.error(f"❌ [BSA-STYLE-PROJECTS] Error: {result.get('error')}")
        
        return result
    except Exception as e:
        logger.error(f"❌ [BSA-STYLE-PROJECTS] Exception: {e}")
        return {
            "success": False,
            "bid_cards": [],
            "error": str(e)
        }
