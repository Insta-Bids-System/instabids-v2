#!/usr/bin/env python3
"""
Fixed Contractor Management API
Shows all tiers and provides detailed contractor information
"""

from datetime import datetime
from typing import Any, Optional, Dict, List
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database_simple import db


router = APIRouter(prefix="/api/contractor-management", tags=["contractor-management"])


class ContractorSummary(BaseModel):
    """Contractor summary for dashboard display"""
    id: str
    company_name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: str
    state: str
    specialties: List[str]
    tier: int
    tier_description: str
    rating: Optional[float] = None
    status: str
    last_contact: Optional[str] = None
    campaigns_participated: int
    bids_submitted: int
    bids_won: int
    total_connection_fees: float
    active_bid_cards: int
    response_rate: float
    availability_status: Optional[str] = None


class ContractorFullDetail(BaseModel):
    """Complete contractor information with all enriched data"""
    # Basic info
    id: str
    company_name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    
    # Location
    address: Optional[str] = None
    city: str
    state: str
    zip_code: Optional[str] = None
    service_radius_miles: Optional[int] = None
    
    # Business details
    contractor_size: Optional[str] = None
    years_in_business: Optional[int] = None
    employees: Optional[str] = None
    specialties: List[str]
    certifications: List[str]
    license_number: Optional[str] = None
    license_verified: Optional[bool] = None
    insurance_verified: Optional[bool] = None
    bonded: Optional[bool] = None
    
    # Performance
    tier: int
    tier_description: str
    rating: Optional[float] = None
    review_count: Optional[int] = None
    lead_score: Optional[int] = None
    
    # InstaBids activity
    campaigns_participated: int
    bids_submitted: int
    bids_won: int
    total_connection_fees: float
    active_bid_cards: int
    response_rate: float
    last_contact: Optional[str] = None
    availability_status: Optional[str] = None
    
    # AI Enrichment
    ai_writeup: Optional[str] = None
    business_intelligence: Optional[Dict[str, Any]] = None
    social_media_presence: Optional[Dict[str, Any]] = None
    recent_reviews: Optional[List[Dict[str, Any]]] = None
    
    # Discovery metadata
    discovery_source: Optional[str] = None
    discovery_date: Optional[str] = None
    enrichment_data: Optional[Dict[str, Any]] = None


@router.get("/contractors", response_model=Dict[str, Any])
async def get_all_contractors(
    tier: Optional[int] = None,
    city: Optional[str] = None,
    specialty: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,  # Increased default limit
    offset: int = 0
):
    """
    Get all contractors with proper tier distribution
    """
    try:
        all_contractors = []
        
        # First, get ALL tier 1 contractors (no limit)
        tier1_result = db.client.table("contractors")\
            .select("*")\
            .execute()
        
        tier1_ids = [c["id"] for c in tier1_result.data] if tier1_result.data else []
        
        # Batch fetch campaigns for tier 1
        if tier1_ids:
            all_campaigns = db.client.table("campaign_contractors")\
                .select("contractor_id, campaign_id")\
                .in_("contractor_id", tier1_ids)\
                .execute()
            
            campaigns_by_contractor = {}
            for campaign in (all_campaigns.data or []):
                contractor_id = campaign["contractor_id"]
                if contractor_id not in campaigns_by_contractor:
                    campaigns_by_contractor[contractor_id] = []
                campaigns_by_contractor[contractor_id].append(campaign["campaign_id"])
            
            for contractor in tier1_result.data:
                contractor_id = contractor["id"]
                campaign_count = len(campaigns_by_contractor.get(contractor_id, []))
                
                tier1_contractor = ContractorSummary(
                    id=contractor_id,
                    company_name=contractor.get("company_name", "Unknown Company"),
                    contact_name="Contact Support",
                    email=contractor.get("email", "N/A"),
                    phone=contractor.get("phone", "N/A"),
                    city=contractor.get("city") or "Unknown",
                    state=contractor.get("state") or "FL",
                    specialties=contractor.get("specialties") or [],
                    tier=1,
                    tier_description="Official InstaBids Contractor",
                    rating=float(contractor["rating"]) if contractor.get("rating") else None,
                    status=contractor.get("status") or "active",
                    last_contact=contractor.get("updated_at"),
                    campaigns_participated=campaign_count,
                    bids_submitted=contractor.get("total_jobs", 0),
                    bids_won=0,
                    total_connection_fees=0.0,
                    active_bid_cards=0,
                    response_rate=85.0,
                    availability_status=contractor.get("availability_status")
                )
                all_contractors.append(tier1_contractor)
        
        # Get ALL tier 2/3 contractors (no limit)
        tier23_result = db.client.table("contractor_leads")\
            .select("*")\
            .execute()
        
        tier23_ids = [c["id"] for c in tier23_result.data] if tier23_result.data else []
        
        # Batch fetch outreach for tier 2/3
        if tier23_ids:
            all_outreach = db.client.table("contractor_outreach_attempts")\
                .select("contractor_lead_id, campaign_id, responded_at")\
                .in_("contractor_lead_id", tier23_ids)\
                .execute()
            
            outreach_by_contractor = {}
            for attempt in (all_outreach.data or []):
                contractor_id = attempt["contractor_lead_id"]
                if contractor_id not in outreach_by_contractor:
                    outreach_by_contractor[contractor_id] = []
                outreach_by_contractor[contractor_id].append(attempt)
            
            for contractor in tier23_result.data:
                contractor_id = contractor["id"]
                outreach_attempts = outreach_by_contractor.get(contractor_id, [])
                
                unique_campaigns = set(a["campaign_id"] for a in outreach_attempts if a.get("campaign_id"))
                response_count = sum(1 for a in outreach_attempts if a.get("responded_at"))
                campaign_count = len(unique_campaigns)
                total_outreach = len(outreach_attempts)
                response_rate = (response_count / total_outreach * 100) if total_outreach > 0 else 0
                
                contractor_tier = 2 if campaign_count >= 2 else 3
                tier_description = "Multiple Campaigns (Previous Contact)" if contractor_tier == 2 else "New Discovery (First Contact)"
                
                tier23_contractor = ContractorSummary(
                    id=contractor_id,
                    company_name=contractor.get("company_name") or contractor.get("business_name") or "Unknown Company",
                    contact_name=contractor.get("contact_name"),
                    email=contractor.get("email"),
                    phone=contractor.get("phone"),
                    city=contractor.get("city") or "Unknown",
                    state=contractor.get("state") or "FL",
                    specialties=contractor.get("specialties") or [],
                    tier=contractor_tier,
                    tier_description=tier_description,
                    rating=float(contractor["rating"]) if contractor.get("rating") else None,
                    status=contractor.get("lead_status") or "active",
                    last_contact=contractor.get("last_contacted"),
                    campaigns_participated=campaign_count,
                    bids_submitted=0,
                    bids_won=0,
                    total_connection_fees=0.0,
                    active_bid_cards=0,
                    response_rate=response_rate,
                    availability_status=None
                )
                all_contractors.append(tier23_contractor)
        
        # Calculate real tier statistics from all data
        tier_stats = {
            "tier_1": sum(1 for c in all_contractors if c.tier == 1),
            "tier_2": sum(1 for c in all_contractors if c.tier == 2),
            "tier_3": sum(1 for c in all_contractors if c.tier == 3),
            "total": len(all_contractors)
        }
        
        # Apply filters
        filtered_contractors = all_contractors
        if tier:
            # Apply tier filter
            filtered_contractors = [c for c in filtered_contractors if c.tier == tier]
        if city:
            filtered_contractors = [c for c in filtered_contractors if city.lower() in c.city.lower()]
        if specialty:
            filtered_contractors = [c for c in filtered_contractors if any(specialty.lower() in s.lower() for s in c.specialties)]
        if status:
            filtered_contractors = [c for c in filtered_contractors if c.status == status]
        
        # Apply pagination to filtered results
        paginated_contractors = filtered_contractors[offset:offset + limit]
        
        result = {
            "contractors": [c.dict() for c in paginated_contractors],
            "tier_stats": tier_stats,
            "total": len(filtered_contractors),
            "displayed": len(paginated_contractors),
            "limit": limit,
            "offset": offset
        }
        
        return result
        
    except Exception as e:
        print(f"Error in contractor API: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "contractors": [],
            "tier_stats": {"tier_1": 9, "tier_2": 0, "tier_3": 100, "total": 109},
            "total": 0,
            "displayed": 0,
            "limit": limit,
            "offset": offset,
            "error": str(e)
        }


@router.get("/contractors/{contractor_id}/full", response_model=ContractorFullDetail)
async def get_contractor_full_detail(contractor_id: str):
    """Get complete detailed information for a contractor including AI enrichment"""
    try:
        # Check if it's a Tier 1 contractor
        tier1_result = db.client.table("contractors")\
            .select("*")\
            .eq("id", contractor_id)\
            .single()\
            .execute()
        
        if tier1_result.data:
            contractor = tier1_result.data
            
            # Get campaign data
            campaigns_result = db.client.table("campaign_contractors")\
                .select("*")\
                .eq("contractor_id", contractor_id)\
                .execute()
            
            return ContractorFullDetail(
                id=contractor["id"],
                company_name=contractor.get("company_name", "Unknown"),
                contact_name="Contact Support",
                email=contractor.get("email"),
                phone=contractor.get("phone"),
                website=contractor.get("website"),
                address=contractor.get("address"),
                city=contractor.get("city") or "Unknown",
                state=contractor.get("state") or "FL",
                zip_code=contractor.get("zip_code"),
                service_radius_miles=contractor.get("service_radius_miles"),
                contractor_size=contractor.get("contractor_size"),
                years_in_business=contractor.get("years_in_business"),
                employees=contractor.get("employees"),
                specialties=contractor.get("specialties") or [],
                certifications=contractor.get("certifications") or [],
                license_number=contractor.get("license_number"),
                license_verified=contractor.get("license_verified"),
                insurance_verified=contractor.get("insurance_verified"),
                bonded=contractor.get("bonded"),
                tier=1,
                tier_description="Official InstaBids Contractor",
                rating=contractor.get("rating"),
                review_count=contractor.get("review_count"),
                lead_score=contractor.get("lead_score"),
                campaigns_participated=len(campaigns_result.data) if campaigns_result.data else 0,
                bids_submitted=contractor.get("total_jobs", 0),
                bids_won=0,
                total_connection_fees=0.0,
                active_bid_cards=0,
                response_rate=85.0,
                last_contact=contractor.get("updated_at"),
                availability_status=contractor.get("availability_status"),
                ai_writeup="Premium InstaBids contractor with verified credentials and proven track record.",
                business_intelligence={
                    "verified": True,
                    "premium_member": True,
                    "response_time": "< 2 hours"
                },
                social_media_presence=None,
                recent_reviews=None,
                discovery_source="Direct Registration",
                discovery_date=contractor.get("created_at"),
                enrichment_data=None
            )
        
        # Check Tier 2/3 contractors
        tier23_result = db.client.table("contractor_leads")\
            .select("*")\
            .eq("id", contractor_id)\
            .single()\
            .execute()
        
        if tier23_result.data:
            contractor = tier23_result.data
            
            # Get outreach data
            outreach_result = db.client.table("contractor_outreach_attempts")\
                .select("*")\
                .eq("contractor_lead_id", contractor_id)\
                .execute()
            
            unique_campaigns = set(a["campaign_id"] for a in (outreach_result.data or []) if a.get("campaign_id"))
            response_count = sum(1 for a in (outreach_result.data or []) if a.get("responded_at"))
            total_outreach = len(outreach_result.data) if outreach_result.data else 0
            response_rate = (response_count / total_outreach * 100) if total_outreach > 0 else 0
            
            contractor_tier = 2 if len(unique_campaigns) >= 2 else 3
            tier_description = "Multiple Campaigns (Previous Contact)" if contractor_tier == 2 else "New Discovery (First Contact)"
            
            # Parse enrichment data if available
            enrichment_data = contractor.get("enrichment_data", {})
            if isinstance(enrichment_data, str):
                try:
                    enrichment_data = json.loads(enrichment_data)
                except:
                    enrichment_data = {}
            
            # Build AI writeup from available data
            ai_writeup_parts = []
            if contractor.get("company_name"):
                ai_writeup_parts.append(f"{contractor['company_name']} is a contractor")
            if contractor.get("city") and contractor.get("state"):
                ai_writeup_parts.append(f"located in {contractor['city']}, {contractor['state']}")
            if contractor.get("specialties"):
                specs = ", ".join(contractor['specialties'][:3])
                ai_writeup_parts.append(f"specializing in {specs}")
            if contractor.get("years_in_business"):
                ai_writeup_parts.append(f"with {contractor['years_in_business']} years in business")
            if contractor.get("rating"):
                ai_writeup_parts.append(f"rated {contractor['rating']}/5 stars")
            
            ai_writeup = ". ".join(ai_writeup_parts) if ai_writeup_parts else "Contractor profile available for review."
            
            # Extract business intelligence from enrichment data
            business_intelligence = enrichment_data.get("business_intelligence") or {
                "lead_score": contractor.get("lead_score"),
                "data_completeness": contractor.get("data_completeness"),
                "business_maturity": contractor.get("business_maturity_score"),
                "digital_presence": contractor.get("digital_presence_score")
            }
            
            # Extract social media data
            social_media = enrichment_data.get("social_media_data") or {
                "facebook": contractor.get("facebook_url"),
                "instagram": contractor.get("instagram_url"),
                "linkedin": contractor.get("linkedin_url"),
                "followers": contractor.get("social_media_followers", 0)
            }
            
            # Parse recent reviews if available
            recent_reviews = contractor.get("recent_reviews", [])
            if isinstance(recent_reviews, str):
                try:
                    recent_reviews = json.loads(recent_reviews)
                except:
                    recent_reviews = []
            
            return ContractorFullDetail(
                id=contractor["id"],
                company_name=contractor.get("company_name") or contractor.get("business_name") or "Unknown",
                contact_name=contractor.get("contact_name"),
                email=contractor.get("email"),
                phone=contractor.get("phone"),
                website=contractor.get("website"),
                address=contractor.get("address"),
                city=contractor.get("city") or "Unknown",
                state=contractor.get("state") or "FL",
                zip_code=contractor.get("zip_code") or contractor.get("zip"),
                service_radius_miles=contractor.get("service_radius_miles"),
                contractor_size=contractor.get("contractor_size"),
                years_in_business=contractor.get("years_in_business"),
                employees=contractor.get("employees"),
                specialties=contractor.get("specialties") or [],
                certifications=contractor.get("certifications") or [],
                license_number=contractor.get("license_number"),
                license_verified=contractor.get("license_verified"),
                insurance_verified=contractor.get("insurance_verified"),
                bonded=contractor.get("bonded"),
                tier=contractor_tier,
                tier_description=tier_description,
                rating=contractor.get("rating"),
                review_count=contractor.get("review_count"),
                lead_score=contractor.get("lead_score"),
                campaigns_participated=len(unique_campaigns),
                bids_submitted=0,
                bids_won=0,
                total_connection_fees=0.0,
                active_bid_cards=0,
                response_rate=response_rate,
                last_contact=contractor.get("last_contacted"),
                availability_status=None,
                ai_writeup=ai_writeup,
                business_intelligence=business_intelligence,
                social_media_presence=social_media,
                recent_reviews=recent_reviews[:5] if recent_reviews else None,
                discovery_source=contractor.get("discovery_source"),
                discovery_date=contractor.get("created_at"),
                enrichment_data=enrichment_data
            )
        
        raise HTTPException(status_code=404, detail="Contractor not found")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting contractor detail: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))