"""
Contractor Signup API - Agent 4 (Contractor UX)
Handles contractor signup with pre-filled data from discovery system
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from database_simple import get_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/contractors", tags=["contractor_signup"])

class ContractorSignupRequest(BaseModel):
    """Request model for contractor signup"""
    firstName: str
    lastName: str
    email: str
    phone: str
    company: Optional[str] = None
    trade: str
    zipCode: str
    source: Optional[str] = "direct"
    bid_context: Optional[str] = None  # bid token if coming from bid card

class ContractorSignupResponse(BaseModel):
    """Response model for contractor signup"""
    success: bool
    contractor_id: str
    message: str
    pre_filled_data: Optional[Dict[str, Any]] = None

@router.post("/signup", response_model=ContractorSignupResponse)
async def contractor_signup(signup_data: ContractorSignupRequest):
    """
    Handle contractor signup - combines new signup data with discovered data
    
    Process:
    1. Look up existing data in contractor_leads table
    2. Merge with signup form data
    3. Create verified contractor in contractors table
    4. Return profile data for frontend
    """
    try:
        logger.info(f"Processing contractor signup: {signup_data.email}")
        
        db = get_client()
        
        # Step 1: Look for existing discovered data
        discovered_data = None
        contractor_lead_record = None
        
        # First try to find by email
        if signup_data.email:
            lead_response = db.table("contractor_leads").select("*").eq("email", signup_data.email).limit(1).execute()
            if lead_response.data and len(lead_response.data) > 0:
                contractor_lead_record = lead_response.data[0]
                discovered_data = contractor_lead_record
                logger.info(f"Found existing contractor lead by email: {contractor_lead_record['id']}")
        
        # If not found by email, try by company name + trade
        if not discovered_data and signup_data.company:
            lead_response = db.table("contractor_leads").select("*").ilike("company_name", f"%{signup_data.company}%").limit(5).execute()
            if lead_response.data:
                # Look for matching trade/specialty
                for lead in lead_response.data:
                    specialties = lead.get("specialties", [])
                    if signup_data.trade.lower() in [s.lower() for s in specialties if s]:
                        contractor_lead_record = lead
                        discovered_data = lead
                        logger.info(f"Found existing contractor lead by company+trade: {lead['id']}")
                        break
        
        # Step 2: Create contractor profile in contractors table
        contractor_id = str(uuid4())
        
        # Base contractor data from signup form
        contractor_profile = {
            "id": contractor_id,
            "user_id": contractor_id,  # For now, contractor_id = user_id
            "company_name": signup_data.company or f"{signup_data.firstName} {signup_data.lastName}",
            "email": signup_data.email,
            "phone": signup_data.phone,
            "specialties": [signup_data.trade],
            "service_areas": [signup_data.zipCode] if signup_data.zipCode else [],
            "tier": 1,  # New contractors start at Tier 1
            "availability_status": "available",
            "total_jobs": 0,
            "verified": False,  # Will be verified after profile completion
            "rating": 0.0,
            "review_count": 0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Step 3: Enhance with discovered data if available
        if discovered_data:
            logger.info("Enhancing profile with discovered data...")
            
            # Add website if found
            if discovered_data.get("website"):
                contractor_profile["website"] = discovered_data["website"]
            
            # Add years in business
            if discovered_data.get("years_in_business"):
                contractor_profile["total_jobs"] = max(0, discovered_data["years_in_business"] * 15)  # Estimate
            
            # Add service areas from discovered data
            if discovered_data.get("service_zip_codes"):
                contractor_profile["service_areas"] = discovered_data["service_zip_codes"]
            
            # Add specialties
            if discovered_data.get("specialties"):
                # Merge with signup trade
                all_specialties = list(set([signup_data.trade] + discovered_data["specialties"]))
                contractor_profile["specialties"] = all_specialties
            
            # Add rating if found
            if discovered_data.get("google_rating"):
                contractor_profile["rating"] = float(discovered_data["google_rating"])
            
            # Add review count
            if discovered_data.get("google_review_count"):
                contractor_profile["review_count"] = int(discovered_data["google_review_count"])
            
            # Mark as verified if we have rich data
            if discovered_data.get("website") or discovered_data.get("google_rating"):
                contractor_profile["verified"] = True
        
        # Step 4: Insert contractor into contractors table
        contractor_result = db.table("contractors").insert(contractor_profile).execute()
        
        if not contractor_result.data:
            raise HTTPException(status_code=500, detail="Failed to create contractor profile")
        
        created_contractor = contractor_result.data[0]
        logger.info(f"Created contractor profile: {created_contractor['id']}")
        
        # Step 5: Update contractor_leads record if found
        if contractor_lead_record:
            # Mark as converted
            update_data = {
                "contractor_id": contractor_id,
                "lead_status": "converted",
                "conversion_date": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            db.table("contractor_leads").update(update_data).eq("id", contractor_lead_record["id"]).execute()
            logger.info(f"Updated contractor lead {contractor_lead_record['id']} as converted")
        
        # Step 6: Prepare response with pre-filled data
        pre_filled_data = None
        if discovered_data:
            pre_filled_data = {
                "website": discovered_data.get("website"),
                "years_in_business": discovered_data.get("years_in_business"),
                "google_rating": discovered_data.get("google_rating"),
                "google_reviews": discovered_data.get("google_review_count"),
                "certifications": discovered_data.get("certifications", []),
                "service_areas": discovered_data.get("service_zip_codes", []),
                "specialties": discovered_data.get("specialties", []),
                "business_size": discovered_data.get("contractor_size"),
                "lead_score": discovered_data.get("lead_score"),
                "data_completeness": discovered_data.get("data_completeness")
            }
        
        return ContractorSignupResponse(
            success=True,
            contractor_id=contractor_id,
            message="Contractor profile created successfully",
            pre_filled_data=pre_filled_data
        )
        
    except Exception as e:
        logger.error(f"Error in contractor signup: {e}")
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")

@router.get("/profile-data/{email}")
async def get_discovered_profile_data(email: str):
    """
    Get discovered profile data for an email before signup
    Used to pre-populate signup forms with discovered data
    """
    try:
        db = get_client()
        
        # Look up discovered data
        lead_response = db.table("contractor_leads").select("*").eq("email", email).limit(1).execute()
        
        if not lead_response.data:
            return {"found": False}
        
        discovered_data = lead_response.data[0]
        
        # Return sanitized data for form pre-population
        return {
            "found": True,
            "data": {
                "company": discovered_data.get("company_name"),
                "phone": discovered_data.get("phone"),
                "website": discovered_data.get("website"),
                "specialties": discovered_data.get("specialties", []),
                "service_areas": discovered_data.get("service_zip_codes", []),
                "years_experience": discovered_data.get("years_in_business"),
                "rating": discovered_data.get("google_rating"),
                "review_count": discovered_data.get("google_review_count"),
                "business_size": discovered_data.get("contractor_size"),
                "lead_score": discovered_data.get("lead_score")
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting profile data: {e}")
        return {"found": False, "error": str(e)}

@router.get("/profile-data-by-name/{company_name}")
async def get_discovered_profile_data_by_name(company_name: str):
    """
    Get discovered profile data by company name for COIA agent
    Used to pre-populate contractor conversations with discovered data
    """
    try:
        db = get_client()
        
        # Look up discovered data by company name
        lead_response = db.table("contractor_leads").select("*").ilike("company_name", f"%{company_name}%").limit(1).execute()
        
        if not lead_response.data:
            return {"found": False}
        
        discovered_data = lead_response.data[0]
        
        # Return detailed data for COIA conversation pre-loading
        return {
            "found": True,
            "data": {
                "company_name": discovered_data.get("company_name"),
                "email": discovered_data.get("email"),
                "phone": discovered_data.get("phone"),
                "website": discovered_data.get("website"),
                "specialties": discovered_data.get("specialties", []),
                "service_areas": discovered_data.get("service_zip_codes", []),
                "years_experience": discovered_data.get("years_in_business"),
                "rating": discovered_data.get("google_rating"),
                "review_count": discovered_data.get("google_review_count"),
                "business_size": discovered_data.get("contractor_size"),
                "lead_score": discovered_data.get("lead_score"),
                "data_completeness": discovered_data.get("data_completeness"),
                "tier": discovered_data.get("tier", 3),  # Default to Tier 3 for new contractors
                "certifications": discovered_data.get("certifications", []),
                "license_info": discovered_data.get("license_info"),
                "discovery_source": discovered_data.get("source", "manual"),
                "discovery_date": discovered_data.get("created_at")
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting profile data by company name: {e}")
        return {"found": False, "error": str(e)}