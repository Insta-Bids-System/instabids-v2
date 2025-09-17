import logging
from typing import Any, Dict, Optional, Union

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
        logger.warning(f"[landing][subagent=account] load_staging_profile error: {e}")
        return None


def _to_contractor_profile(staging: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a staging row into the contractor_profile dict expected by create_contractor_account.
    """
    return {
        "company_name": staging.get("company_name") or staging.get("business_name"),
        "email": staging.get("email"),
        "phone": staging.get("phone"),
        "website": staging.get("website"),
        "address": staging.get("address"),
        "city": staging.get("city"),
        "state": staging.get("state"),
        "zip": staging.get("zip_code") or staging.get("zip"),
        "zip_code": staging.get("zip_code") or staging.get("zip"),
        "specializations": staging.get("services") or staging.get("specializations") or staging.get("specialties") or [],
        "years_in_business": staging.get("years_in_business"),
        "employees": staging.get("estimated_employees"),
        "service_areas": staging.get("service_areas") or [],
        "insurance_verified": staging.get("insurance_verified", False),
        "license_verified": staging.get("license_verified", False),
        "bonded": staging.get("bonded", False),
        "rating": staging.get("rating"),
        "review_count": staging.get("review_count"),
    }


def create_account_from_staging(staging_or_profile: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Account subagent tool:
    - Creates a contractor account ONLY after explicit consent.
    - Accepts either a staging identifier (preferred) or a full contractor profile dict.
    - On success, marks potential_contractors row converted=true and stores promoted_contractor_id.

    Returns:
      {
        "success": bool,
        "account": {...},              # when success
        "promoted_contractor_id": "...",
        "staging_id": "...",
      }
    """
    try:
        profile: Optional[Dict[str, Any]] = None
        staging_id: Optional[str] = None

        if isinstance(staging_or_profile, str):
            staging_id = staging_or_profile
            staging = _load_staging_profile(staging_id)
            if not staging:
                logger.warning(f"[landing][subagent=account] staging id not found: {staging_id}")
                return {"success": False, "error": "staging_not_found", "staging_id": staging_id}
            profile = _to_contractor_profile(staging)
        elif isinstance(staging_or_profile, dict):
            profile = staging_or_profile
            staging_id = profile.get("id") or profile.get("contractor_lead_id")
        else:
            return {"success": False, "error": "invalid_input_type"}

        # Basic validation
        if not profile or not profile.get("company_name"):
            return {"success": False, "error": "missing_company_name", "staging_id": staging_id}

        # Delegate to existing async tool
        import anyio
        from ..tools import coia_tools  # global instance

        async def _call():
            return await coia_tools.create_contractor_account(profile)

        out = anyio.run(_call)
        if not isinstance(out, dict) or not out.get("success"):
            logger.error(f"[landing][subagent=account] create_contractor_account failed: {out}")
            return {"success": False, "error": out.get("error", "account_creation_failed"), "staging_id": staging_id}

        account = out.get("account") or {}
        promoted_id = account.get("id")

        # Mark staging converted (best-effort)
        try:
            if staging_id and promoted_id:
                import os, sys
                from datetime import datetime
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                from database_simple import db  # type: ignore

                payload = {
                    "converted": True,
                    "promoted_contractor_id": promoted_id,
                    "converted_at": datetime.utcnow().isoformat(),
                }
                db.client.table("potential_contractors").update(payload).eq("id", staging_id).execute()
                logger.info(f"[landing][subagent=account] staging converted id={staging_id} -> contractor_id={promoted_id}")
        except Exception as mark_err:
            logger.warning(f"[landing][subagent=account] failed to mark staging converted: {mark_err}")

        return {
            "success": True,
            "account": account,
            "promoted_contractor_id": promoted_id,
            "staging_id": staging_id,
        }

    except Exception as e:
        logger.exception("[landing][subagent=account] create_account_from_staging error")
        return {"success": False, "error": str(e)}
