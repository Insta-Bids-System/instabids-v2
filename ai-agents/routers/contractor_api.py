"""
Contractor API - Simple contractor data endpoints
"""

import logging
from fastapi import APIRouter, HTTPException
from database import SupabaseDB

router = APIRouter(prefix="/api/contractors", tags=["Contractors"])
logger = logging.getLogger(__name__)

db = SupabaseDB()

@router.get("/{contractor_id}")
async def get_contractor(contractor_id: str):
    """Get contractor details by ID"""
    try:
        # Try contractor_leads table first (most data is here)
        result = db.client.table("contractor_leads").select("*").eq("id", contractor_id).execute()
        
        if result.data:
            contractor = result.data[0]
            # Format the response
            return {
                "id": contractor.get("id"),
                "company_name": contractor.get("company_name"),
                "contact_name": contractor.get("contact_name"),
                "email": contractor.get("email"),
                "phone": contractor.get("phone"),
                "website": contractor.get("website"),
                "address": contractor.get("address"),
                "city": contractor.get("city"),
                "state": contractor.get("state"),
                "zip": contractor.get("zip_code") or contractor.get("zip"),
                "specialties": contractor.get("specialties", []),
                "years_in_business": contractor.get("years_in_business"),
                "license_number": contractor.get("license_number"),
                "insurance_verified": contractor.get("insurance_verified"),
                "bonded": contractor.get("bonded"),
                "rating": contractor.get("rating"),
                "verified": contractor.get("license_verified", False),
                "business_details": contractor.get("business_details"),
                "certifications": contractor.get("certifications", []),
                "employees": contractor.get("employees"),
                "profile_completeness": 75,  # Calculate based on filled fields
                "data_source": "contractor_leads"
            }
        
        # Try contractors table as fallback
        result = db.client.table("contractors").select("*").eq("id", contractor_id).execute()
        
        if result.data:
            contractor = result.data[0]
            return {
                "id": contractor.get("id"),
                "company_name": contractor.get("company_name"),
                "email": contractor.get("email"),
                "phone": contractor.get("phone"),
                "license_number": contractor.get("license_number"),
                "rating": contractor.get("rating"),
                "verified": contractor.get("verified", False),
                "tier": contractor.get("tier"),
                "total_jobs": contractor.get("total_jobs"),
                "total_earned": contractor.get("total_earned"),
                "profile_completeness": 50,
                "data_source": "contractors"
            }
        
        raise HTTPException(status_code=404, detail=f"Contractor {contractor_id} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching contractor {contractor_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{contractor_id}/context")
async def get_contractor_context(contractor_id: str):
    """Get contractor context for BSA"""
    try:
        # Get contractor profile
        contractor_result = db.client.table("contractor_leads").select("*").eq("id", contractor_id).execute()
        has_profile = bool(contractor_result.data)
        
        # Get COIA conversations count
        coia_result = db.client.table("unified_conversations").select("id").eq(
            "created_by", contractor_id
        ).eq("conversation_type", "COIA").execute()
        
        coia_conversations = len(coia_result.data) if coia_result.data else 0
        
        # Get BSA conversations count
        bsa_result = db.client.table("unified_conversations").select("id").eq(
            "created_by", contractor_id
        ).eq("conversation_type", "BSA").execute()
        
        bsa_conversations = len(bsa_result.data) if bsa_result.data else 0
        
        return {
            "total_context_items": coia_conversations + bsa_conversations,
            "has_profile": has_profile,
            "coia_conversations": coia_conversations,
            "bsa_conversations": bsa_conversations,
            "enhanced_profile": has_profile and (coia_conversations > 0 or bsa_conversations > 0)
        }
        
    except Exception as e:
        logger.error(f"Error fetching contractor context: {e}")
        return {
            "total_context_items": 0,
            "has_profile": False,
            "coia_conversations": 0,
            "bsa_conversations": 0,
            "enhanced_profile": False
        }