import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


async def get_all_contractor_types_mapping() -> Dict[int, str]:
    """
    Query database for ALL contractor types and return ID -> Name mapping
    Used for intelligent contractor type expansion suggestions
    """
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from database_simple import db
        
        # Query ALL contractor types from database
        result = db.client.table("contractor_types").select("id, name").order("id").execute()
        
        if result.data:
            # Build ID -> Name mapping
            type_mapping = {}
            for contractor_type in result.data:
                name = contractor_type.get('name', '').strip()
                type_id = contractor_type.get('id')
                if name and type_id:
                    type_mapping[type_id] = name
            
            logger.info(f"Retrieved {len(type_mapping)} contractor types from database")
            return type_mapping
        else:
            logger.warning("No contractor types found in database")
            return {}
            
    except Exception as e:
        logger.error(f"Failed to query contractor types: {e}")
        return {}


async def suggest_additional_contractor_types(
    current_contractor_types: List[int], 
    services_mentioned: List[str],
    all_contractor_types: Dict[int, str]
) -> Dict[str, Any]:
    """
    Suggest additional contractor types based on current types and services mentioned
    Uses intelligent matching to expand contractor type coverage
    """
    try:
        suggestions = []
        current_type_names = [all_contractor_types.get(type_id, f"Type {type_id}") 
                             for type_id in current_contractor_types]
        
        # Use GPT-4o intelligent analysis to suggest contractor types
        # Get the contractor's complete business profile for analysis
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from database_simple import db
            from .intelligent_contractor_analysis import intelligent_contractor_type_analysis
            
            # Try to get contractor profile for intelligent analysis
            # First try to find a contractor with these types to get their business profile
            contractor_profile = None
            # Convert contractor type IDs to strings for Supabase contains query
            contractor_type_ids_str = [str(cid) for cid in current_contractor_types]
            potential_contractor = db.client.table("potential_contractors").select(
                "company_name, ai_business_summary, ai_capability_description, services, specialties, years_in_business, capabilities"
            ).contains("contractor_type_ids", contractor_type_ids_str).limit(1).execute()
            
            if potential_contractor.data:
                contractor_profile = potential_contractor.data[0]
                logger.info(f"Found contractor profile for intelligent analysis: {contractor_profile.get('company_name')}")
                
                # Use GPT-4o intelligent analysis
                intelligent_result = await intelligent_contractor_type_analysis(
                    contractor_profile,
                    current_contractor_types,
                    all_contractor_types
                )
                
                if intelligent_result.get('success'):
                    suggestions.extend(intelligent_result.get('suggestions', []))
                    logger.info(f"GPT-4o suggested {len(intelligent_result.get('suggestions', []))} contractor types")
                else:
                    logger.warning(f"GPT-4o analysis failed: {intelligent_result.get('error')}")
            else:
                logger.info("No contractor profile found for intelligent analysis, using service-based suggestions")
                
        except ImportError as e:
            logger.warning(f"Could not import intelligent analysis: {e}")
        except Exception as e:
            logger.error(f"Error in intelligent contractor analysis: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Service-based suggestions (if services mentioned)
        service_mappings = {
            "plumbing": [33, 206, 207, 208],
            "electrical": [34],
            "landscaping": [31, 128, 221, 222],
            "lawn": [222, 31, 221],
            "turf": [225, 31, 221],
            "concrete": [39],
            "fencing": [40],
            "roofing": [36],
            "hvac": [35],
            "flooring": [37]
        }
        
        for service in services_mentioned:
            service_lower = service.lower()
            for service_key, type_ids in service_mappings.items():
                if service_key in service_lower:
                    for type_id in type_ids:
                        if type_id not in current_contractor_types and type_id in all_contractor_types:
                            suggestions.append({
                                "contractor_type_id": type_id,
                                "contractor_type_name": all_contractor_types[type_id],
                                "reason": f"Matches service '{service}'"
                            })
        
        # Remove duplicates
        unique_suggestions = []
        seen_ids = set()
        for suggestion in suggestions:
            if suggestion["contractor_type_id"] not in seen_ids:
                unique_suggestions.append(suggestion)
                seen_ids.add(suggestion["contractor_type_id"])
        
        return {
            "success": True,
            "current_contractor_types": current_contractor_types,
            "current_type_names": current_type_names,
            "suggestions": unique_suggestions[:5],  # Limit to top 5 suggestions
            "total_suggestions": len(unique_suggestions)
        }
        
    except Exception as e:
        logger.error(f"Error in suggest_additional_contractor_types: {e}")
        return {
            "success": False,
            "error": str(e),
            "suggestions": []
        }


async def enhanced_radius_agent(
    identifier: str,
    services: Optional[Union[List[str], str]] = None,
    radius_miles: Optional[int] = None,
    contractor_type_ids: Optional[List[int]] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None,
    suggest_contractor_types: bool = True
) -> Dict[str, Any]:
    """
    ENHANCED Radius subagent tool:
    - Updates staged profile preferences in potential_contractors
    - identifier should be the staging id (preferred) or contractor_lead_id used as id during staging
    - services may be a list or a single string
    - radius_miles updates search_radius_miles
    - contractor_type_ids updates contractor types (NEW FUNCTIONALITY)
    - optional city/state/zip_code update basic location metadata
    - suggest_contractor_types: if True, suggests additional contractor types (NEW)

    Returns:
      { 
        "success": bool, 
        "updated_fields": {...}, 
        "id": identifier,
        "contractor_type_suggestions": [...] (if suggest_contractor_types=True)
      }
    """
    try:
        import os
        import sys
        import uuid
        from datetime import datetime

        # Ensure identifier is valid UUID format
        if identifier and not identifier.startswith(('test-', 'staging-')):
            # Already a proper UUID, use as-is
            pass
        else:
            # Convert test identifier to proper UUID format
            if identifier and identifier.startswith('test-'):
                # Create deterministic UUID from test string
                identifier_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, identifier))
                logger.info(f"[enhanced_radius] Converting test ID {identifier} to UUID: {identifier_uuid}")
                identifier = identifier_uuid
            elif not identifier:
                # Generate new UUID
                identifier = str(uuid.uuid4())
                logger.info(f"[enhanced_radius] Generated new UUID: {identifier}")

        # Normalize services to list
        if isinstance(services, str) and services.strip():
            services = [services.strip()]
        if services is None:
            services = []

        # Normalize contractor_type_ids to list
        if contractor_type_ids is None:
            contractor_type_ids = []

        # Get all contractor types for suggestions
        all_contractor_types = await get_all_contractor_types_mapping() if suggest_contractor_types else {}

        # Prepare update payload
        payload: Dict[str, Any] = {"updated_at": datetime.utcnow().isoformat()}
        if services:
            payload["services"] = services
        if isinstance(radius_miles, int):
            payload["search_radius_miles"] = radius_miles
        if contractor_type_ids:
            payload["contractor_type_ids"] = contractor_type_ids
        if city:
            payload["city"] = city
        if state:
            payload["state"] = state
        if zip_code:
            payload["zip_code"] = zip_code

        if len(payload) == 1:  # only updated_at present
            logger.info("[landing][subagent=enhanced_radius] No preference fields provided to update")
            result = {"success": True, "updated_fields": {}, "id": identifier}
        else:
            # DB client
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from database_simple import db  # type: ignore

            # Update by id
            update_result = (
                db.client
                .table("potential_contractors")
                .update(payload)
                .eq("id", identifier)
                .execute()
            )

            # Verify update (best effort)
            verify = (
                db.client
                .table("potential_contractors")
                .select("id, services, search_radius_miles, contractor_type_ids, city, state, zip_code")
                .eq("id", identifier)
                .execute()
            )

            if getattr(verify, "data", None):
                logger.info(f"[landing][subagent=enhanced_radius] preferences updated id={identifier} fields={list(payload.keys())}")
                result = {
                    "success": True,
                    "updated_fields": payload,
                    "id": identifier,
                    "current": verify.data[0],
                }
            else:
                logger.warning(f"[landing][subagent=enhanced_radius] update verify_miss id={identifier}")
                result = {"success": True, "updated_fields": payload, "id": identifier}

        # Add contractor type suggestions if requested
        if suggest_contractor_types and contractor_type_ids and all_contractor_types:
            suggestion_result = await suggest_additional_contractor_types(
                contractor_type_ids, 
                services, 
                all_contractor_types
            )
            result["contractor_type_suggestions"] = suggestion_result

        return result

    except Exception as e:
        logger.exception("[landing][subagent=enhanced_radius] enhanced_radius_agent error")
        return {"success": False, "error": str(e), "id": identifier}


def update_preferences(
    identifier: str,
    services: Optional[Union[List[str], str]] = None,
    radius_miles: Optional[int] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Radius subagent tool:
    - Updates staged profile preferences in potential_contractors
    - identifier should be the staging id (preferred) or contractor_lead_id used as id during staging
    - services may be a list or a single string
    - radius_miles updates search_radius_miles
    - optional city/state/zip_code update basic location metadata

    Returns:
      { "success": bool, "updated_fields": {...}, "id": identifier }
    """
    try:
        import os
        import sys
        from datetime import datetime

        # Normalize services to list
        if isinstance(services, str) and services.strip():
            services = [services.strip()]
        if services is None:
            services = []

        # Prepare update payload
        payload: Dict[str, Any] = {"updated_at": datetime.utcnow().isoformat()}
        if services:
            payload["services"] = services
        if isinstance(radius_miles, int):
            payload["search_radius_miles"] = radius_miles
        if city:
            payload["city"] = city
        if state:
            payload["state"] = state
        if zip_code:
            payload["zip_code"] = zip_code

        if len(payload) == 1:  # only updated_at present
            logger.info("[landing][subagent=radius] No preference fields provided to update")
            return {"success": True, "updated_fields": {}, "id": identifier}

        # DB client
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from database_simple import db  # type: ignore

        # Update by id
        result = (
            db.client
            .table("potential_contractors")
            .update(payload)
            .eq("id", identifier)
            .execute()
        )

        # Verify update (best effort)
        verify = (
            db.client
            .table("potential_contractors")
            .select("id, services, search_radius_miles, city, state, zip_code")
            .eq("id", identifier)
            .execute()
        )

        if getattr(verify, "data", None):
            logger.info(f"[landing][subagent=radius] preferences updated id={identifier} fields={list(payload.keys())}")
            return {
                "success": True,
                "updated_fields": payload,
                "id": identifier,
                "current": verify.data[0],
            }

        logger.warning(f"[landing][subagent=radius] update verify_miss id={identifier}")
        return {"success": True, "updated_fields": payload, "id": identifier}

    except Exception as e:
        logger.exception("[landing][subagent=radius] update_preferences error")
        return {"success": False, "error": str(e), "id": identifier}
