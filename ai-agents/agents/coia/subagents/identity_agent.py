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

# Reuse existing sync tool wrapper for lightweight parsing
from ..deepagents_tools import extract_company_info as _extract_company_info

def extract_company_info(text: str) -> Dict[str, Any]:
    """
    Identity subagent tool:
    - Minimal extractor for company hints from free text
    - Delegates to existing heuristic (kept stable for now)
    """
    return _extract_company_info(text)


def validate_company_exists(company_name: str, location_hint: Optional[str] = None) -> Dict[str, Any]:
    """
    Identity subagent tool:
    - Minimal confirmation using the fast footprint path
    - Calls coia_tools.search_google_business (via anyio) to avoid adding a new deepagents wrapper
    Returns:
      {
        "exists": bool,
        "footprint": {address, phone, website, ...},
        "source": "tavily_search" | "fallback_minimal" | "...",
      }
    """
    # Wrap company validation with LangFuse span
    if LANGFUSE_AVAILABLE:
        try:
            with langfuse.start_as_current_observation(
                name="coia-subagent-company-validation",
                as_type="span",
                input={
                    "company_name": company_name,
                    "location_hint": location_hint,
                    "subagent": "identity_agent"
                }
            ) as span:
                result = _validate_company_exists_impl(company_name, location_hint)
                span.update(output={
                    "company_exists": result.get("exists", False),
                    "data_source": result.get("source", "unknown"),
                    "has_footprint": bool(result.get("footprint", {}))
                })
                return result
        except Exception as e:
            logger.warning(f"LangFuse company validation span failed: {e}")
            return _validate_company_exists_impl(company_name, location_hint)
    else:
        return _validate_company_exists_impl(company_name, location_hint)

def _validate_company_exists_impl(company_name: str, location_hint: Optional[str] = None) -> Dict[str, Any]:
    """Implementation of company validation - extracted for LangFuse wrapping"""
    try:
        import anyio
        from ..deepagents_tools import coia_tools  # Use the global instance

        def _run() -> Dict[str, Any]:
            # anyio.run expects a function not coroutine, so bridge using from anyio import run
            # but we will run the async method in a nested function
            async def _call():
                result = await coia_tools.search_google_business(company_name, location_hint)
                if not result:
                    return {"exists": False, "footprint": {}, "source": "no_result"}
                # Mark exists if we have at least a website or phone or address
                exists = bool(result.get("website") or result.get("phone") or result.get("address"))
                return {
                    "exists": exists,
                    "footprint": {
                        "company_name": result.get("company_name") or company_name,
                        "address": result.get("address"),
                        "website": result.get("website"),
                        "phone": result.get("phone"),
                        "rating": result.get("rating"),
                        "review_count": result.get("review_count"),
                        "google_maps_url": result.get("google_maps_url"),
                        "location": result.get("location"),
                        "verified": result.get("verified"),
                    },
                    "source": result.get("source", "unknown"),
                }
            return anyio.run(_call)

        out = _run()
        logger.info(f"[landing][subagent=identity] validate_company_exists exists={out.get('exists')} source={out.get('source')}")
        return out
    except Exception as e:
        logger.warning(f"[landing][subagent=identity] validate_company_exists error: {e}")
        return {"exists": False, "footprint": {}, "source": "error", "error": str(e)}
