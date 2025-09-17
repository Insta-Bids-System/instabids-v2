import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def _load_staging_profile(identifier: str) -> Optional[Dict[str, Any]]:
    """
    Load staged profile from potential_contractors by id.
    """
    try:
        import os, sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from database_simple import db  # type: ignore

        res = db.client.table("potential_contractors").select("*").eq("id", identifier).single().execute()
        return res.data if getattr(res, "data", None) else None
    except Exception as e:
        logger.warning(f"[landing][subagent=projects] load_staging_profile error: {e}")
        return None


def _to_contractor_profile(staging: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a staging row into a contractor_profile dict expected by search_bid_cards.
    """
    return {
        "id": staging.get("id"),
        "company_name": staging.get("company_name"),
        "email": staging.get("email"),
        "phone": staging.get("phone"),
        "website": staging.get("website"),
        "address": staging.get("address"),
        "city": staging.get("city"),
        "state": staging.get("state"),
        "zip_code": staging.get("zip_code"),
        "specialties": staging.get("services") or staging.get("specializations") or [],
        "years_in_business": staging.get("years_in_business"),
        "service_areas": staging.get("service_areas") or [],
    }


def find_matching_projects(staging_or_profile: Union[str, Dict[str, Any]] = None, radius_miles: Optional[int] = None, staging_id: str = None) -> Dict[str, Any]:
    """
    Projects subagent tool:
    - Accepts either a staging identifier (str) or a contractor profile (dict)
    - Also accepts staging_id as named parameter for cleaner API
    - Delegates to coia_tools.search_bid_cards to get available projects
    - Applies light filtering by radius if provided (best-effort, depends on project payload)

    Returns: {"success": bool, "projects": list, "count": int}
    """
    try:
        profile: Optional[Dict[str, Any]] = None

        # Handle named parameter staging_id
        if staging_id:
            staging_or_profile = staging_id

        if isinstance(staging_or_profile, str):
            staging = _load_staging_profile(staging_or_profile)
            if not staging:
                logger.warning(f"[landing][subagent=projects] staging id not found: {staging_or_profile}")
                return {"success": False, "error": "Staging profile not found", "projects": [], "count": 0}
            profile = _to_contractor_profile(staging)
        elif isinstance(staging_or_profile, dict):
            profile = staging_or_profile
        else:
            logger.warning("[landing][subagent=projects] invalid input; expected str or dict")
            return {"success": False, "error": "Invalid input format", "projects": [], "count": 0}

        if not profile or not profile.get("company_name"):
            logger.warning("[landing][subagent=projects] missing contractor profile or company_name")
            return {"success": False, "error": "Missing contractor profile or company name", "projects": [], "count": 0}

        # Delegate to existing tool (sync wrapper via deepagents_tools)
        from ..deepagents_tools import search_bid_cards as _search_bid_cards
        projects = _search_bid_cards(profile, None) or []

        # Optional: light radius filtering if projects include distance metadata
        if isinstance(radius_miles, int) and radius_miles > 0:
            filtered = []
            for p in projects:
                dist = p.get("distance_miles") or p.get("distance")
                try:
                    if dist is None or float(dist) <= float(radius_miles):
                        filtered.append(p)
                except Exception:
                    filtered.append(p)  # if unknown format, keep
            projects = filtered

        logger.info(f"[landing][subagent=projects] found {len(projects)} projects for {profile.get('company_name')}")
        return {"success": True, "projects": projects, "count": len(projects)}
    except Exception as e:
        logger.exception("[landing][subagent=projects] find_matching_projects error")
        return {"success": False, "error": str(e), "projects": [], "count": 0}
