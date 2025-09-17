#!/usr/bin/env python3
"""
Contractor Management API
Real-time contractor overview with 3-tier classification and campaign management
"""

from datetime import datetime
from typing import Any, Optional, Dict, List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database_simple import db
from utils.redis_cache import cache


router = APIRouter(prefix="/api/contractor-management", tags=["contractor-management"])


def get_contractor_bid_statistics(contractor_id: str, is_tier1: bool = False) -> Dict[str, Any]:
    """Get comprehensive bid statistics for a contractor"""
    try:
        stats = {
            "bids_submitted": 0,
            "bids_won": 0,
            "total_connection_fees": 0.0,
            "active_bid_cards": 0
        }
        
        if is_tier1:
            # For Tier 1 contractors, check the bids table and bid_cards
            bids_result = db.client.table("bids")\
                .select("id, bid_card_id, status")\
                .eq("contractor_id", contractor_id)\
                .execute()
            
            if bids_result.data:
                stats["bids_submitted"] = len(bids_result.data)
                
                # Count won bids (where contractor was selected)
                for bid in bids_result.data:
                    if bid.get("status") == "accepted" or bid.get("status") == "won":
                        stats["bids_won"] += 1
                
                # Count active bid cards (status in generating, collecting_bids)
                bid_card_ids = [bid["bid_card_id"] for bid in bids_result.data]
                if bid_card_ids:
                    active_cards = db.client.table("bid_cards")\
                        .select("id")\
                        .in_("id", bid_card_ids)\
                        .in_("status", ["generating", "collecting_bids"])\
                        .execute()
                    stats["active_bid_cards"] = len(active_cards.data) if active_cards.data else 0
            
            # Get connection fees for Tier 1 contractors
            fees_result = db.client.table("connection_fees")\
                .select("fee_amount")\
                .eq("contractor_id", contractor_id)\
                .eq("status", "paid")\
                .execute()
            
            if fees_result.data:
                stats["total_connection_fees"] = sum(fee.get("fee_amount", 0) for fee in fees_result.data)
        else:
            # For Tier 2/3 contractors, check bid_cards.bid_document for submitted bids
            # Get all bid cards this contractor has bid on through outreach attempts
            outreach_result = db.client.table("contractor_outreach_attempts")\
                .select("bid_card_id")\
                .eq("contractor_lead_id", contractor_id)\
                .execute()
            
            if outreach_result.data:
                bid_card_ids = list(set([attempt["bid_card_id"] for attempt in outreach_result.data if attempt.get("bid_card_id")]))
                
                if bid_card_ids:
                    # Check bid_document for submitted bids
                    bid_cards_result = db.client.table("bid_cards")\
                        .select("id, bid_document, status")\
                        .in_("id", bid_card_ids)\
                        .execute()
                    
                    for bid_card in bid_cards_result.data:
                        bid_document = bid_card.get("bid_document", {})
                        
                        # Parse bid_document to check for this contractor's bids
                        if isinstance(bid_document, dict):
                            submitted_bids = bid_document.get("submitted_bids", [])
                        elif isinstance(bid_document, str):
                            try:
                                import json
                                parsed_doc = json.loads(bid_document)
                                submitted_bids = parsed_doc.get("submitted_bids", [])
                            except:
                                submitted_bids = []
                        else:
                            submitted_bids = []
                        
                        # Check if this contractor has submitted a bid
                        if isinstance(submitted_bids, list):
                            for bid in submitted_bids:
                                if isinstance(bid, dict) and bid.get("contractor_id") == contractor_id:
                                    stats["bids_submitted"] += 1
                                    
                                    # Check if this bid was accepted
                                    if bid.get("status") == "accepted" or bid_document.get("selected_contractor_id") == contractor_id:
                                        stats["bids_won"] += 1
                        
                        # Count active bid cards
                        if bid_card.get("status") in ["generating", "collecting_bids"]:
                            stats["active_bid_cards"] += 1
        
        return stats
        
    except Exception as e:
        print(f"Error getting contractor bid statistics: {e}")
        return {
            "bids_submitted": 0,
            "bids_won": 0,
            "total_connection_fees": 0.0,
            "active_bid_cards": 0
        }


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


class ContractorDetail(BaseModel):
    """Detailed contractor information"""
    # Basic info
    id: str
    company_name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    
    # Location
    city: str
    state: str
    address: Optional[str] = None
    zip_code: Optional[str] = None
    service_radius_miles: Optional[int] = None
    
    # Business details
    contractor_size: Optional[str] = None
    years_in_business: Optional[int] = None
    specialties: List[str]
    certifications: List[str]
    license_number: Optional[str] = None
    
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
    
    # Campaign history
    recent_campaigns: List[Dict[str, Any]]
    outreach_history: List[Dict[str, Any]]


@router.get("/contractors", response_model=Dict[str, Any])
async def get_all_contractors(
    tier: Optional[int] = None,
    city: Optional[str] = None,
    specialty: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Get all contractors with 3-tier classification and real-time status
    
    Tier 1: Official InstaBids contractors with accounts
    Tier 2: Contractors contacted multiple times (2+ campaigns)
    Tier 3: New contractors (first-time contact)
    """
    try:
        # Try to get from cache first
        cache_params = {
            "tier": tier,
            "city": city,
            "specialty": specialty,
            "status": status,
            "limit": limit,
            "offset": offset
        }
        cached_result = cache.get("contractors", cache_params)
        if cached_result:
            print(f"[CONTRACTORS] Cache hit, returning cached data")
            return cached_result
        contractors = []
        
        # Get Tier 1 contractors (official InstaBids contractors)
        # Using table API instead of raw SQL
        try:
            tier1_result = db.client.table("contractors")\
                .select("*")\
                .execute()
            print(f"DEBUG: Tier 1 query returned {len(tier1_result.data) if tier1_result.data else 0} contractors")
            if tier1_result.data:
                print(f"DEBUG: First Tier 1 contractor: {tier1_result.data[0].get('company_name', 'Unknown')}")
        except Exception as e:
            print(f"Error fetching Tier 1 contractors: {e}")
            tier1_result = type('obj', (object,), {'data': []})
        
        for contractor in tier1_result.data:
            # Get profile data separately to avoid join issues
            profile_result = None
            if contractor.get("user_id"):
                try:
                    profile_result = db.client.table("profiles")\
                        .select("full_name, email, phone")\
                        .eq("id", contractor["user_id"])\
                        .single()\
                        .execute()
                except:
                    pass
                    
            profile = profile_result.data if profile_result and profile_result.data else {}
            contact_name = profile.get("full_name") or "N/A"
            email = profile.get("email") or "N/A"
            phone = profile.get("phone") or "N/A"
            
            # Get campaign participation for Tier 1
            campaign_count = db.client.table("campaign_contractors")\
                .select("campaign_id", count="exact")\
                .eq("contractor_id", contractor["id"])\
                .execute()
            
            # Get comprehensive bid statistics
            bid_stats = get_contractor_bid_statistics(contractor["id"], is_tier1=True)
            
            # Calculate response rate for Tier 1 (simplified)
            response_rate = 85.0  # Default high response rate for official contractors
            
            # Determine status
            status = "active"
            if contractor.get("availability_status"):
                status = contractor["availability_status"]
            elif contractor.get("verified"):
                status = "verified"
                
            tier1_contractor = ContractorSummary(
                id=contractor["id"],
                company_name=contractor["company_name"] or "Unknown Company",
                contact_name=contact_name,
                email=email,
                phone=phone,
                city="Unknown",  # Will be updated when location data is available
                state="Unknown",
                specialties=contractor.get("specialties") or [],
                tier=1,
                tier_description="Official InstaBids Contractor",
                rating=float(contractor["rating"]) if contractor.get("rating") else None,
                status=status,
                last_contact=contractor.get("updated_at"),
                campaigns_participated=campaign_count.count if campaign_count.count else 0,
                bids_submitted=bid_stats["bids_submitted"],
                bids_won=bid_stats["bids_won"],
                total_connection_fees=bid_stats["total_connection_fees"],
                active_bid_cards=bid_stats["active_bid_cards"],
                response_rate=response_rate,
                availability_status=contractor.get("availability_status")
            )
            contractors.append(tier1_contractor)
            print(f"DEBUG: Added Tier 1 contractor: {tier1_contractor.company_name} (ID: {tier1_contractor.id})")
        
        print(f"DEBUG: Total contractors after Tier 1 processing: {len(contractors)}")

        # Get Tier 2 & 3 contractors from contractor_leads
        # Using table API instead of raw SQL
        tier23_result = db.client.table("contractor_leads")\
            .select("*")\
            .order("created_at", desc=True)\
            .execute()
        
        for contractor in tier23_result.data:
            # Get outreach attempts for this contractor to determine tier and response rate
            outreach_attempts = db.client.table("contractor_outreach_attempts")\
                .select("campaign_id, responded_at, sent_at")\
                .eq("contractor_lead_id", contractor["id"])\
                .execute()
            
            # Determine tier based on campaign participation
            unique_campaigns = set()
            response_count = 0
            last_contact = None
            
            for attempt in outreach_attempts.data:
                if attempt.get("campaign_id"):
                    unique_campaigns.add(attempt["campaign_id"])
                if attempt.get("responded_at"):
                    response_count += 1
                if attempt.get("sent_at"):
                    if not last_contact or attempt["sent_at"] > last_contact:
                        last_contact = attempt["sent_at"]
            
            campaign_count = len(unique_campaigns)
            tier = 2 if campaign_count >= 2 else 3
            tier_description = "Multiple Campaigns (Previous Contact)" if tier == 2 else "New Discovery (First Contact)"
            
            # Calculate response rate
            total_outreach = len(outreach_attempts.data)
            response_rate = (response_count / total_outreach * 100) if total_outreach > 0 else 0
            
            # Get comprehensive bid statistics for Tier 2/3
            bid_stats = get_contractor_bid_statistics(contractor["id"], is_tier1=False)
            
            # Determine status
            status = "active"
            if contractor.get("lead_status"):
                status = contractor["lead_status"]
            elif contractor.get("disqualification_reason"):
                status = "disqualified"
                
            tier23_contractor = ContractorSummary(
                id=contractor["id"],
                company_name=contractor["company_name"] or "Unknown Company",
                contact_name=contractor.get("contact_name"),
                email=contractor.get("email"),
                phone=contractor.get("phone"),
                city=contractor.get("city") or "Unknown",
                state=contractor.get("state") or "Unknown", 
                specialties=contractor.get("specialties") or [],
                tier=tier,
                tier_description=tier_description,
                rating=float(contractor["rating"]) if contractor.get("rating") else None,
                status=status,
                last_contact=last_contact,
                campaigns_participated=campaign_count,
                bids_submitted=bid_stats["bids_submitted"],
                bids_won=bid_stats["bids_won"],
                total_connection_fees=bid_stats["total_connection_fees"],
                active_bid_cards=bid_stats["active_bid_cards"],
                response_rate=round(response_rate, 1),
                availability_status=None
            )
            contractors.append(tier23_contractor)
            print(f"DEBUG: Added Tier {tier} contractor: {tier23_contractor.company_name} (ID: {tier23_contractor.id})")

        print(f"DEBUG: Total contractors after Tier 2&3 processing: {len(contractors)}")
        print(f"DEBUG: Breakdown by tier in contractors list: Tier 1: {len([c for c in contractors if c.tier == 1])}, Tier 2: {len([c for c in contractors if c.tier == 2])}, Tier 3: {len([c for c in contractors if c.tier == 3])}")

        # Apply filters
        print(f"DEBUG: Before applying filters - Total contractors: {len(contractors)}")
        print(f"DEBUG: Filter parameters - tier: {tier}, city: {city}, specialty: {specialty}, status: {status}")
        
        # Show status distribution
        status_counts = {}
        for c in contractors:
            status_val = c.status
            status_counts[status_val] = status_counts.get(status_val, 0) + 1
        print(f"DEBUG: Status distribution: {status_counts}")
        
        # Calculate tier stats BEFORE any filters are applied (using original unfiltered contractors)
        all_contractors_before_filters = contractors  # Get all contractors before filters
        
        # Apply filters AFTER calculating tier stats
        filtered_contractors = contractors
        if tier:
            before_tier_filter = len(filtered_contractors)
            filtered_contractors = [c for c in filtered_contractors if c.tier == tier]
            print(f"DEBUG: Tier filter applied: {before_tier_filter} → {len(filtered_contractors)} contractors")
        if city:
            before_city_filter = len(filtered_contractors)
            filtered_contractors = [c for c in filtered_contractors if city.lower() in c.city.lower()]
            print(f"DEBUG: City filter applied: {before_city_filter} → {len(filtered_contractors)} contractors")
        if specialty:
            before_specialty_filter = len(filtered_contractors)
            filtered_contractors = [c for c in filtered_contractors if any(specialty.lower() in s.lower() for s in c.specialties)]
            print(f"DEBUG: Specialty filter applied: {before_specialty_filter} → {len(filtered_contractors)} contractors")
        if status and status != "qualified":
            # Skip the default "qualified" filter to show all contractors
            before_status_filter = len(filtered_contractors)
            filtered_contractors = [c for c in filtered_contractors if c.status == status]
            print(f"DEBUG: Status filter applied: {before_status_filter} → {len(filtered_contractors)} contractors")
        elif status == "qualified":
            print(f"DEBUG: Skipping default 'qualified' status filter to show all contractors")
        
        print(f"DEBUG: Final contractors after all filters: {len(filtered_contractors)}")

        # Calculate tier stats using ORIGINAL unfiltered contractor list
        tier_stats = {
            "tier_1": len([c for c in all_contractors_before_filters if c.tier == 1]),
            "tier_2": len([c for c in all_contractors_before_filters if c.tier == 2]), 
            "tier_3": len([c for c in all_contractors_before_filters if c.tier == 3]),
            "total": len(all_contractors_before_filters)
        }
        
        # Use filtered contractors for final response
        contractors = filtered_contractors

        # Apply pagination
        total_count = len(contractors)
        contractors = contractors[offset:offset + limit]

        result = {
            "contractors": [c.dict() for c in contractors],
            "total_count": total_count,
            "tier_stats": tier_stats,
            "filters_applied": {
                "tier": tier,
                "city": city,
                "specialty": specialty,
                "status": status
            }
        }
        
        # Cache the result for 60 seconds
        cache_params = {
            "tier": tier,
            "city": city,
            "specialty": specialty,
            "status": status,
            "limit": limit,
            "offset": offset
        }
        cache.set("contractors", result, cache_params, ttl_seconds=60)
        print(f"[CONTRACTORS] Cached result for 60 seconds")
        
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving contractors: {str(e)}")


@router.get("/contractors/{contractor_id}", response_model=ContractorDetail)
async def get_contractor_detail(contractor_id: str):
    """Get detailed information about a specific contractor"""
    try:
        # Try to find contractor in tier 1 first
        tier1_result = db.client.table("contractors")\
            .select("*, profiles!inner(*)")\
            .eq("id", contractor_id)\
            .execute()
        
        if tier1_result.data:
            # Tier 1 contractor
            contractor = tier1_result.data[0]
            profile = contractor["profiles"]
            
            # Get campaign history
            campaigns = db.client.table("campaign_contractors")\
                .select("*, outreach_campaigns!inner(name, status, created_at, bid_cards!inner(bid_card_number, project_type))")\
                .eq("contractor_id", contractor_id)\
                .execute()
            
            recent_campaigns = []
            for campaign in campaigns.data[:5]:  # Last 5 campaigns
                camp_data = campaign["outreach_campaigns"]
                recent_campaigns.append({
                    "campaign_id": campaign["campaign_id"],
                    "campaign_name": camp_data["name"],
                    "project_type": camp_data["bid_cards"]["project_type"],
                    "bid_card_number": camp_data["bid_cards"]["bid_card_number"],
                    "status": camp_data["status"],
                    "date": camp_data["created_at"]
                })
            
            # Get detailed bid statistics for Tier 1
            detailed_bid_stats = get_contractor_bid_statistics(contractor["id"], is_tier1=True)
            
            return ContractorDetail(
                id=contractor["id"],
                company_name=contractor["company_name"],
                contact_name=profile["full_name"],
                email=profile["email"],
                phone=profile["phone"],
                website=None,
                city="Unknown",
                state="Unknown", 
                address=None,
                zip_code=None,
                service_radius_miles=None,
                contractor_size=None,
                years_in_business=None,
                specialties=contractor["specialties"] or [],
                certifications=[],
                license_number=contractor["license_number"],
                tier=1,
                tier_description="Official InstaBids Contractor",
                rating=float(contractor["rating"]) if contractor["rating"] else None,
                review_count=None,
                lead_score=None,
                campaigns_participated=len(campaigns.data),
                bids_submitted=detailed_bid_stats["bids_submitted"],
                bids_won=detailed_bid_stats["bids_won"],
                total_connection_fees=detailed_bid_stats["total_connection_fees"],
                active_bid_cards=detailed_bid_stats["active_bid_cards"],
                response_rate=100.0,  # Tier 1 assumed high response rate
                last_contact=contractor["updated_at"],
                availability_status=contractor["availability_status"],
                recent_campaigns=recent_campaigns,
                outreach_history=[]
            )
        
        # Try to find in contractor_leads (Tier 2-3)
        tier23_result = db.client.table("contractor_leads")\
            .select("*")\
            .eq("id", contractor_id)\
            .single()\
            .execute()
            
        if not tier23_result.data:
            raise HTTPException(status_code=404, detail="Contractor not found")
        
        contractor = tier23_result.data
        
        # Get outreach history
        outreach_history = db.client.table("contractor_outreach_attempts")\
            .select("*, outreach_campaigns!inner(name, bid_cards!inner(bid_card_number, project_type))")\
            .eq("contractor_lead_id", contractor_id)\
            .order("sent_at", desc=True)\
            .execute()
        
        formatted_history = []
        for attempt in outreach_history.data:
            campaign_data = attempt["outreach_campaigns"]
            formatted_history.append({
                "attempt_id": attempt["id"],
                "channel": attempt["channel"],
                "status": attempt["status"],
                "sent_at": attempt["sent_at"],
                "responded_at": attempt["responded_at"],
                "campaign_name": campaign_data["name"],
                "project_type": campaign_data["bid_cards"]["project_type"],
                "bid_card_number": campaign_data["bid_cards"]["bid_card_number"]
            })
        
        # Determine tier
        campaign_count = len(set([h["campaign_name"] for h in formatted_history]))
        tier = 2 if campaign_count >= 2 else 3
        tier_description = "Multiple Campaigns (Previous Contact)" if tier == 2 else "New Discovery (First Contact)"
        
        # Calculate response rate
        total_attempts = len(formatted_history)
        responses = len([h for h in formatted_history if h["responded_at"]])
        response_rate = (responses / total_attempts * 100) if total_attempts > 0 else 0
        
        # Get detailed bid statistics for Tier 2/3
        detailed_bid_stats = get_contractor_bid_statistics(contractor["id"], is_tier1=False)
        
        return ContractorDetail(
            id=contractor["id"],
            company_name=contractor["company_name"] or "Unknown Company",
            contact_name=contractor["contact_name"],
            email=contractor["email"],
            phone=contractor["phone"],
            website=contractor["website"],
            city=contractor["city"] or "Unknown",
            state=contractor["state"] or "Unknown",
            address=contractor["address"],
            zip_code=contractor["zip_code"],
            service_radius_miles=contractor["service_radius_miles"],
            contractor_size=contractor["contractor_size"],
            years_in_business=contractor["years_in_business"],
            specialties=contractor["specialties"] or [],
            certifications=contractor["certifications"] or [],
            license_number=contractor["license_number"],
            tier=tier,
            tier_description=tier_description,
            rating=float(contractor["rating"]) if contractor["rating"] else None,
            review_count=contractor["review_count"],
            lead_score=contractor["lead_score"],
            campaigns_participated=campaign_count,
            bids_submitted=detailed_bid_stats["bids_submitted"],
            bids_won=detailed_bid_stats["bids_won"],
            total_connection_fees=detailed_bid_stats["total_connection_fees"],
            active_bid_cards=detailed_bid_stats["active_bid_cards"],
            response_rate=round(response_rate, 1),
            last_contact=formatted_history[0]["sent_at"] if formatted_history else None,
            availability_status=None,
            recent_campaigns=[],
            outreach_history=formatted_history[:10]  # Last 10 attempts
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving contractor details: {str(e)}")


@router.post("/contractors/{contractor_id}/assign-to-campaign")
async def assign_contractor_to_campaign(
    contractor_id: str,
    campaign_data: dict
):
    """
    Manually assign a contractor to an outreach campaign
    This will be the big picture functionality for manual campaign management
    """
    try:
        campaign_id = campaign_data.get("campaign_id")
        bid_card_id = campaign_data.get("bid_card_id")
        
        if not campaign_id:
            raise HTTPException(status_code=400, detail="Campaign ID required")
        
        # Check if contractor is already in this campaign
        existing = db.client.table("campaign_contractors")\
            .select("id")\
            .eq("campaign_id", campaign_id)\
            .eq("contractor_id", contractor_id)\
            .execute()
        
        if existing.data:
            raise HTTPException(status_code=400, detail="Contractor already in this campaign")
        
        # Add contractor to campaign
        assignment = {
            "id": str(uuid4()),
            "campaign_id": campaign_id,
            "contractor_id": contractor_id,
            "assigned_at": datetime.now().isoformat(),
            "assigned_by": "admin",  # Could be actual admin user ID
            "status": "assigned"
        }
        
        db.client.table("campaign_contractors").insert(assignment).execute()
        
        # Create outreach attempt record
        outreach_attempt = {
            "id": str(uuid4()),
            "bid_card_id": bid_card_id,
            "campaign_id": campaign_id,
            "contractor_lead_id": contractor_id,
            "channel": "manual_assignment",  # Mark as manual
            "status": "pending",
            "sent_at": datetime.now().isoformat(),
            "message_content": "Manually assigned to campaign by admin"
        }
        
        db.client.table("contractor_outreach_attempts").insert(outreach_attempt).execute()
        
        # Update campaign contractor count
        db.client.table("outreach_campaigns")\
            .update({"contractors_targeted": db.client.table("campaign_contractors").select("id").eq("campaign_id", campaign_id).execute().count})\
            .eq("id", campaign_id)\
            .execute()
        
        return {
            "success": True,
            "message": f"Contractor assigned to campaign successfully",
            "assignment_id": assignment["id"],
            "outreach_attempt_id": outreach_attempt["id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error assigning contractor to campaign: {str(e)}")


@router.get("/dashboard-stats")
async def get_contractor_dashboard_stats():
    """Get real-time stats for contractor dashboard"""
    try:
        # Count contractors by tier
        tier1_count = db.client.table("contractors").select("id", count="exact").execute().count
        
        # Get contractor leads with campaign participation
        # Using table API to get all contractor leads
        contractor_leads = db.client.table("contractor_leads")\
            .select("id")\
            .execute()
        
        tier2_count = 0
        tier3_count = 0
        
        # Calculate tier counts by checking campaign participation for each lead
        for lead in contractor_leads.data:
            outreach_attempts = db.client.table("contractor_outreach_attempts")\
                .select("campaign_id")\
                .eq("contractor_lead_id", lead["id"])\
                .execute()
            
            # Count unique campaigns
            unique_campaigns = set()
            for attempt in outreach_attempts.data:
                if attempt.get("campaign_id"):
                    unique_campaigns.add(attempt["campaign_id"])
            
            campaign_count = len(unique_campaigns)
            if campaign_count >= 2:
                tier2_count += 1
            else:
                tier3_count += 1
        
        # Get active campaigns
        active_campaigns = db.client.table("outreach_campaigns")\
            .select("id", count="exact")\
            .eq("status", "active")\
            .execute().count
        
        # Get recent activity
        recent_outreach = db.client.table("contractor_outreach_attempts")\
            .select("id", count="exact")\
            .gte("sent_at", datetime.now().replace(hour=0, minute=0, second=0).isoformat())\
            .execute().count
        
        return {
            "tier_breakdown": {
                "tier_1": tier1_count,
                "tier_2": tier2_count, 
                "tier_3": tier3_count,
                "total": tier1_count + tier2_count + tier3_count
            },
            "active_campaigns": active_campaigns,
            "outreach_today": recent_outreach,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dashboard stats: {str(e)}")