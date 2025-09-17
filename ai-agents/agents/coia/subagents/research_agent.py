import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Import LangFuse for observability (safe import)
try:
    from langfuse import get_client
    langfuse = get_client()
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False

# Reuse existing DeepAgents sync wrappers and tool instance
from ..deepagents_tools import research_business as _research_business, build_profile as _build_profile
import anyio

def research_company_basic(company_name: str, location: Optional[str] = None) -> Dict[str, Any]:
    """
    Research subagent tool:
    - Returns comprehensive contractor research data (google + tavily + extraction + social + BI)
    - Wraps coia_tools.web_search_company via DeepAgents wrapper (sync)
    """
    # Wrap research with LangFuse span
    if LANGFUSE_AVAILABLE:
        try:
            with langfuse.start_as_current_observation(
                name="coia-subagent-research-basic",
                as_type="span",
                input={
                    "company_name": company_name,
                    "location": location,
                    "subagent": "research_agent"
                }
            ) as span:
                result = _research_business_impl(company_name, location)
                span.update(output={
                    "success": isinstance(result, dict) and "error" not in result,
                    "data_sources": result.get("data_sources", []) if isinstance(result, dict) else [],
                    "tavily_used": "tavily_discovery" in (result.get("data_sources", []) if isinstance(result, dict) else [])
                })
                return result
        except Exception as e:
            logger.warning(f"LangFuse research basic span failed: {e}")
            return _research_business_impl(company_name, location)
    else:
        return _research_business_impl(company_name, location)

def _research_business_impl(company_name: str, location: Optional[str] = None) -> Dict[str, Any]:
    """Implementation of research business - extracted for LangFuse wrapping"""
    try:
        result = _research_business(company_name, location)
        logger.info(f"[landing][subagent=research] research_company_basic company={company_name} "
                    f"tavily_used={ 'tavily_discovery' in (result.get('data_sources') or []) } "
                    f"success_keys={list(result.keys())[:6] if isinstance(result, dict) else 'not_dict'}")
        return result if isinstance(result, dict) else {"error": "unexpected_result_type"}
    except Exception as e:
        logger.warning(f"[landing][subagent=research] research_company_basic error: {e}")
        return {"error": str(e), "company_name": company_name, "data_sources": []}


def extract_contractor_profile(company_name: str, research_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Research subagent tool:
    - Takes raw research data (184K chars) and uses GPT-4o to extract all 66 contractor fields
    - Includes intelligent synthesis for summary fields, USPs, competitive advantages
    - Returns structured profile ready for staging
    """
    # Wrap profile extraction with LangFuse span
    if LANGFUSE_AVAILABLE:
        try:
            with langfuse.start_as_current_observation(
                name="coia-subagent-profile-extraction",
                as_type="span",
                input={
                    "company_name": company_name,
                    "data_sources": research_data.get('data_sources', []),
                    "subagent": "research_agent",
                    "extraction_target": "66_field_contractor_profile"
                }
            ) as span:
                result = _extract_contractor_profile_impl(company_name, research_data)
                span.update(output={
                    "extraction_success": "error" not in result,
                    "fields_extracted": result.get("fields_extracted", 0),
                    "extraction_method": result.get("extraction_method", "unknown")
                })
                return result
        except Exception as e:
            logger.warning(f"LangFuse profile extraction span failed: {e}")
            return _extract_contractor_profile_impl(company_name, research_data)
    else:
        return _extract_contractor_profile_impl(company_name, research_data)

def _extract_contractor_profile_impl(company_name: str, research_data: Dict[str, Any]) -> Dict[str, Any]:
    """Implementation of profile extraction - extracted for LangFuse wrapping"""
    try:
        logger.info(f"[landing][subagent=research] extract_profile starting for {company_name}")
        
        # Extract the different data components from research
        google_data = research_data.get('google_data', {})
        web_data = {
            'tavily_discovery': research_data.get('tavily_discovery_data', {}),
            'website_data': research_data.get('website_data', {}),
            'social_media': research_data.get('social_media_data', {}),
            'extracted_info': research_data.get('extracted_info', {})
        }
        license_data = research_data.get('license_data', {})
        
        # Call GPT-4o for intelligent extraction of all 66 fields
        # Use async bridge
        async def _extract():
            from ..tools.ai_extraction.gpt4o_contractor_extractor import extract_profile_with_gpt4o
            return await extract_profile_with_gpt4o(company_name, google_data, web_data, license_data)
        
        import asyncio
        try:
            # Check if we're already in an event loop
            loop = asyncio.get_running_loop()
            # We're in an event loop, create a task in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _extract())
                profile = future.result()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run
            profile = asyncio.run(_extract())
        
        # Log what we extracted
        fields_extracted = len([k for k, v in profile.items() if v])
        logger.info(f"[landing][subagent=research] extract_profile completed - "
                   f"extracted {fields_extracted} fields with GPT-4o intelligence")
        
        # Add extraction metadata
        profile['extraction_method'] = 'gpt-4o-intelligent'
        profile['fields_extracted'] = fields_extracted
        profile['data_sources_used'] = research_data.get('data_sources', [])
        
        return profile
        
    except Exception as e:
        logger.error(f"[landing][subagent=research] extract_profile error: {e}")
        return {
            "error": str(e), 
            "company_name": company_name,
            "extraction_failed": True
        }


def stage_profile(profile: Dict[str, Any], contractor_lead_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Research subagent tool:
    - Stages (upserts) a contractor profile into potential_contractors
    - Uses coia_tools.save_potential_contractor (async) with optional post-verify read-back
    Returns:
      { "success": bool, "staging_id": "...", "company_name": "..." }
    """
    try:
        # Prefer a stable id for staging if provided
        if contractor_lead_id and "id" not in profile and "contractor_lead_id" not in profile:
            profile["contractor_lead_id"] = contractor_lead_id

        # Use the fixed async bridge from deepagents_tools
        from ..deepagents_tools import save_potential_contractor
        
        # This uses the fixed asyncio handling that avoids "Already running asyncio" error
        out = save_potential_contractor(profile)
        ok = bool(out.get("success"))
        # The save_potential_contractor returns 'id', not 'staging_id'
        staging_id = out.get("staging_id") or out.get("id")
        logger.info(f"[landing][subagent=research] stage_profile success={ok} staging_id={staging_id} "
                    f"company={out.get('company_name', profile.get('company_name') or profile.get('business_name'))}")
        
        # Ensure we return staging_id in the expected format
        if staging_id and "staging_id" not in out:
            out["staging_id"] = staging_id

        # Optional: verify row exists (best-effort; do not fail flow)
        try:
            if staging_id:
                import sys, os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                from database_simple import db  # type: ignore
                verify = db.client.table("potential_contractors").select("id").eq("id", staging_id).execute()
                if getattr(verify, "data", None):
                    logger.info(f"[landing][subagent=research] stage_profile verify_ok id={staging_id}")
                else:
                    logger.warning(f"[landing][subagent=research] stage_profile verify_miss id={staging_id}")
        except Exception as verr:
            logger.debug(f"[landing][subagent=research] stage_profile verify skipped: {verr}")

        return out
    except Exception as e:
        logger.exception("[landing][subagent=research] stage_profile error")
        return {"success": False, "error": str(e)}
