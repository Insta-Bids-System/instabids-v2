"""
Contractor Database Tool for COIA
Handles contractor creation and potential contractor staging
"""

import logging
import os
import sys
import uuid
import json
from typing import Dict, Any, Optional
from datetime import datetime

from ..base import BaseTool

logger = logging.getLogger(__name__)


class ContractorDatabaseTool(BaseTool):
    """Database operations for contractor management"""
    
    async def create_contractor_account(self, contractor_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create official contractor account in contractors table
        """
        logger.info(f"Creating contractor account for: {contractor_profile.get('company_name', 'Unknown')}")
        
        try:
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            from database_simple import get_client
            
            supabase = get_client()
            
            # Prepare contractor account data
            contractor_data = {
                "id": str(uuid.uuid4()),
                "company_name": contractor_profile.get("company_name", ""),
                "contact_name": contractor_profile.get("contact_name", ""),
                "phone": contractor_profile.get("phone", ""),
                "email": contractor_profile.get("email", ""),
                "website": contractor_profile.get("website", ""),
                "address": contractor_profile.get("address", ""),
                "city": contractor_profile.get("city", ""),
                "state": contractor_profile.get("state", "FL"),
                "zip_code": contractor_profile.get("zip", ""),
                "specialties": contractor_profile.get("specialties", []),
                "years_in_business": contractor_profile.get("years_in_business"),
                "license_number": contractor_profile.get("license_number", ""),
                "insurance_verified": contractor_profile.get("insurance_verified", False),
                "bonded": contractor_profile.get("bonded", False),
                "verified": False,
                "tier": 3,  # New contractors start as Tier 3
                "contractor_type_ids": contractor_profile.get("contractor_type_ids", []),  # CRITICAL: For BSA bid matching
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Insert into contractors table
            result = supabase.table("contractors").insert(contractor_data).execute()
            
            if result and result.data and len(result.data) > 0:
                created_contractor = result.data[0]
                logger.info(f"✅ Created contractor account: {created_contractor['id']}")
                return {
                    "id": created_contractor["id"],
                    "company_name": created_contractor["company_name"],
                    "tier": created_contractor["tier"],
                    "created": True
                }
            else:
                logger.error("Failed to create contractor account - no data returned")
                return {"error": "Failed to create contractor account"}
                
        except Exception as e:
            logger.error(f"Error creating contractor account: {e}")
            return {"error": str(e)}

    async def save_potential_contractor(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage (upsert) a contractor profile into potential_contractors.
        EXTRACTED FROM LEGACY tools.py - REAL IMPLEMENTATION
        
        Intended for the Landing flow's research-agent. This does NOT promote to contractors.
        On account creation, account-agent should promote and mark this staging row converted.
        """
        try:
            import sys
            import os
            import uuid
            from datetime import datetime

            # Shape core staging record - ALWAYS generate proper UUID for database
            # contractor_lead_id from API might not be UUID format, so always generate new UUID for staging_id
            staging_id = str(uuid.uuid4())
            company_name = profile.get("company_name") or profile.get("business_name") or ""
            email = profile.get("email", "")
            phone = profile.get("phone", "")
            website = profile.get("website", "")
            address = profile.get("address", "")
            city = profile.get("city", "")
            state = profile.get("state", "")
            zip_code = profile.get("zip") or profile.get("zip_code", "")
            services = profile.get("services") or profile.get("specializations") or profile.get("specialties", [])
            years_in_business = profile.get("years_in_business")
            search_radius = profile.get("search_radius_miles") or profile.get("service_radius_miles")
            contractor_size_category = profile.get("contractor_size_category") or profile.get("contractor_size")
            
            # Validate contractor_size enum - only use valid values
            valid_contractor_sizes = ["solo_handyman", "owner_operator", "small_business", "regional_company"]
            if contractor_size_category not in valid_contractor_sizes:
                contractor_size_category = None  # Let database handle NULL instead of invalid enum

            # Build staging payload with ONLY fields that exist in potential_contractors table
            staging_data: Dict[str, Any] = {
                "id": staging_id,
                "contractor_lead_id": profile.get("contractor_lead_id"),  # Store original lead ID from API
                "company_name": company_name,
                "email": email,
                "phone": phone,
                "website": website,
                "address": address,
                "city": city,
                "state": state,
                "zip_code": zip_code,
                "years_in_business": years_in_business,
                "search_radius_miles": search_radius,
                "contractor_size_category": contractor_size_category,
                
                # Google API fields (CRITICAL FIX - these columns exist!)
                "google_rating": profile.get("google_rating"),
                "google_review_count": profile.get("google_review_count"),
                "google_place_id": profile.get("google_place_id"),
                "google_business_status": profile.get("google_business_status"),
                "google_types": profile.get("google_types", []),
                
                # Fields that exist in the table
                "license_number": profile.get("license_number"),
                "bonded": profile.get("bonded"),
                "specialties": profile.get("specialties", []) or profile.get("specializations", []),  # Use 'specialties' column
                "services": services if isinstance(services, list) else [services] if services else [],
                "insurance_verified": profile.get("insurance_verified", False),
                "ai_business_summary": profile.get("ai_business_summary", ""),
                "ai_capability_description": profile.get("ai_capability_description", ""),
                "lead_score": profile.get("lead_score", 0),
                
                # CRITICAL: Add contractor_type_ids for BSA bid card matching
                "contractor_type_ids": profile.get("contractor_type_ids", []),
                
                "raw_profile": profile,
                "updated_at": datetime.utcnow().isoformat(),
                "converted": False
            }

            # Remove None to avoid DB issues
            staging_data = {k: v for k, v in staging_data.items() if v is not None}

            # Supabase upsert
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            from database_simple import get_client
            
            supabase = get_client()

            # Use upsert to handle duplicates
            result = supabase.table("potential_contractors").upsert(staging_data).execute()
            if result and result.data:
                logger.info(f"✅ Staged potential contractor: {company_name} ({staging_id})")
                return {"success": True, "staging_id": staging_id, "company_name": company_name}
            else:
                logger.error(f"Failed to stage potential contractor: {company_name}")
                return {"error": "Failed to stage potential contractor"}
                
        except Exception as e:
            logger.error(f"Error staging potential contractor: {e}")
            return {"error": str(e)}

    async def check_existing_contractor(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Check if contractor already exists in contractors table
        """
        try:
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            from database_simple import get_client
            
            supabase = get_client()
            
            # Search for existing contractor by company name
            result = supabase.table("contractors").select("*").ilike("company_name", f"%{company_name}%").execute()
            
            if result and result.data:
                logger.info(f"Found existing contractor: {company_name}")
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking existing contractor: {e}")
            return None