#!/usr/bin/env python3
"""
Admin Search API Router
Comprehensive search functionality for bid cards and homeowners
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from database_simple import db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/search", tags=["admin-search"])


class SearchResult(BaseModel):
    """Unified search result model"""
    bid_cards: List[Dict[str, Any]]
    homeowners: List[Dict[str, Any]]
    total_bid_cards: int
    total_homeowners: int
    search_query: str
    search_type: str


class HomeownerInfo(BaseModel):
    """Homeowner information model"""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    total_bid_cards: int
    total_spent: Optional[float] = None
    created_at: Optional[str] = None


@router.get("/bid-cards/by-homeowner")
async def search_bid_cards_by_homeowner(
    user_id: Optional[str] = Query(None, description="Homeowner UUID"),
    homeowner_name: Optional[str] = Query(None, description="Homeowner name (partial match)"),
    limit: int = Query(50, description="Maximum results to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    Search bid cards by homeowner ID or name
    Returns all bid cards associated with a homeowner
    """
    try:
        query = db.client.table("bid_cards").select("*")
        
        # Filter by user_id if provided
        if user_id:
            query = query.eq("user_id", user_id)
        
        # Filter by homeowner_name if provided (case-insensitive partial match)
        if homeowner_name:
            query = query.ilike("homeowner_name", f"%{homeowner_name}%")
        
        # Order by creation date and apply pagination
        query = query.order("created_at", desc=True).limit(limit).offset(offset)
        
        result = query.execute()
        
        # Get total count for pagination
        count_query = db.client.table("bid_cards").select("id", count="exact")
        if user_id:
            count_query = count_query.eq("user_id", user_id)
        if homeowner_name:
            count_query = count_query.ilike("homeowner_name", f"%{homeowner_name}%")
        
        count_result = count_query.execute()
        total_count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
        
        return {
            "bid_cards": result.data,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count,
            "search_params": {
                "user_id": user_id,
                "homeowner_name": homeowner_name
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/homeowners")
async def search_homeowners(
    search_term: Optional[str] = Query(None, description="Search by ID, name, email, or phone"),
    name: Optional[str] = Query(None, description="Search by name (first or last)"),
    email: Optional[str] = Query(None, description="Search by email"),
    phone: Optional[str] = Query(None, description="Search by phone"),
    limit: int = Query(50, description="Maximum results to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    Search homeowners by various criteria
    Returns homeowner information with bid card counts
    """
    try:
        # First, get unique homeowners from bid_cards
        homeowner_query = """
        SELECT DISTINCT
            user_id,
            homeowner_name,
            COUNT(*) as bid_card_count,
            MIN(created_at) as first_bid_card,
            MAX(created_at) as last_bid_card
        FROM bid_cards
        WHERE user_id IS NOT NULL
        """
        
        conditions = []
        
        # Add search conditions
        if search_term:
            # Search across multiple fields
            conditions.append(f"""
                (homeowner_name ILIKE '%{search_term}%' 
                OR user_id::text ILIKE '%{search_term}%')
            """)
        
        if name:
            conditions.append(f"homeowner_name ILIKE '%{name}%'")
        
        # Use direct query (Supabase doesn't support execute_sql RPC)
        query = db.client.table("bid_cards").select(
            "user_id, homeowner_name"
        ).not_.is_("user_id", "null")
        
        if search_term:
            # Handle UUID search separately from name search
            if is_valid_uuid(search_term):
                # If it's a valid UUID, search both name and exact UUID match
                query = query.or_(
                    f"homeowner_name.ilike.%{search_term}%,user_id.eq.{search_term}"
                )
            else:
                # If not UUID, only search name
                query = query.ilike("homeowner_name", f"%{search_term}%")
        
        if name:
            query = query.ilike("homeowner_name", f"%{name}%")
        
        result = query.execute()
        
        # Process results to get unique homeowners with counts
        homeowner_map = {}
        for row in result.data:
            hw_id = row.get("user_id")
            hw_name = row.get("homeowner_name", "Unknown")
            
            if hw_id and hw_id not in homeowner_map:
                homeowner_map[hw_id] = {
                    "user_id": hw_id,
                    "homeowner_name": hw_name,
                    "bid_card_count": 0
                }
            if hw_id:
                homeowner_map[hw_id]["bid_card_count"] += 1
        
        homeowners = list(homeowner_map.values())
        homeowners.sort(key=lambda x: x["bid_card_count"], reverse=True)
        
        # Apply pagination
        homeowners = homeowners[offset:offset + limit]
        
        # Try to get additional profile information if available
        if homeowners and email or phone:
            # Get profile data if searching by email/phone
            profile_query = db.client.table("profiles").select("*")
            
            if email:
                profile_query = profile_query.ilike("email", f"%{email}%")
            if phone:
                profile_query = profile_query.ilike("phone", f"%{phone}%")
            
            profiles = profile_query.execute()
            
            # Merge profile data with homeowner data
            profile_map = {p["id"]: p for p in profiles.data} if profiles.data else {}
            
            for hw in homeowners:
                if hw.get("user_id") in profile_map:
                    profile = profile_map[hw["user_id"]]
                    hw["email"] = profile.get("email")
                    hw["phone"] = profile.get("phone")
                    hw["full_name"] = profile.get("full_name", hw.get("homeowner_name"))
        
        return {
            "homeowners": homeowners,
            "total": len(homeowners),
            "limit": limit,
            "offset": offset,
            "search_params": {
                "search_term": search_term,
                "name": name,
                "email": email,
                "phone": phone
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/unified")
async def unified_search(
    query: str = Query(..., description="Search query"),
    search_type: str = Query("all", description="Type: all, bid_cards, homeowners, contractors"),
    limit: int = Query(20, description="Maximum results per type")
):
    """
    Unified search across bid cards, homeowners, and contractors
    Searches multiple fields and returns combined results
    """
    try:
        results = {
            "bid_cards": [],
            "homeowners": [],
            "contractors": [],
            "total_bid_cards": 0,
            "total_homeowners": 0,
            "total_contractors": 0,
            "search_query": query,
            "search_type": search_type
        }
        
        # Search bid cards
        if search_type in ["all", "bid_cards"]:
            # Build search conditions for bid cards
            search_conditions = [
                f"bid_card_number.ilike.%{query}%",
                f"homeowner_name.ilike.%{query}%",
                f"project_type.ilike.%{query}%",
                f"title.ilike.%{query}%"
            ]
            
            # Only add UUID search if query is a valid UUID
            if is_valid_uuid(query):
                search_conditions.append(f"user_id.eq.{query}")
            
            bid_card_query = db.client.table("bid_cards").select("*").or_(
                ",".join(search_conditions)
            ).limit(limit)
            
            bid_cards_result = bid_card_query.execute()
            results["bid_cards"] = bid_cards_result.data
            results["total_bid_cards"] = len(bid_cards_result.data)
        
        # Search homeowners
        if search_type in ["all", "homeowners"]:
            # Get unique homeowners matching the query
            homeowner_query = db.client.table("bid_cards").select(
                "user_id, homeowner_name"
            ).not_.is_("user_id", "null")
            
            if is_valid_uuid(query):
                homeowner_query = homeowner_query.or_(
                    f"user_id.eq.{query},"
                    f"homeowner_name.ilike.%{query}%"
                )
            else:
                homeowner_query = homeowner_query.ilike("homeowner_name", f"%{query}%")
            
            hw_result = homeowner_query.execute()
            
            # Process to get unique homeowners with counts
            homeowner_map = {}
            for row in hw_result.data:
                hw_id = row.get("user_id")
                hw_name = row.get("homeowner_name", "Unknown")
                
                if hw_id and hw_id not in homeowner_map:
                    # Get bid card count for this homeowner
                    count_result = db.client.table("bid_cards").select(
                        "id", count="exact"
                    ).eq("user_id", hw_id).execute()
                    
                    homeowner_map[hw_id] = {
                        "user_id": hw_id,
                        "homeowner_name": hw_name,
                        "bid_card_count": count_result.count if hasattr(count_result, 'count') else len(count_result.data)
                    }
            
            results["homeowners"] = list(homeowner_map.values())[:limit]
            results["total_homeowners"] = len(homeowner_map)
        
        # Search contractors
        if search_type in ["all", "contractors"]:
            # Use the same contractor search logic as the contractors endpoint
            contractor_query = db.client.table("contractors").select(
                "*, profiles!inner(full_name, email, phone)"
            ).or_(f"company_name.ilike.%{query}%,specialties.cs.{{{query}}}")
            
            contractor_result = contractor_query.limit(limit).execute()
            
            # Format contractors data
            contractors_data = []
            for contractor in contractor_result.data:
                profile = contractor.get("profiles", {})
                contractors_data.append({
                    "id": contractor.get("id"),
                    "name": profile.get("full_name", "Unknown"),
                    "company": contractor.get("company_name"),
                    "location": contractor.get("service_areas", {}).get("areas", ["Unknown"])[0] if isinstance(contractor.get("service_areas", {}), dict) else "Unknown",
                    "specialties": ", ".join(contractor.get("specialties", [])) if contractor.get("specialties") else "",
                    "email": profile.get("email"),
                    "phone": profile.get("phone"),
                    "tier": contractor.get("tier"),
                    "rating": float(contractor.get("rating", 0)) if contractor.get("rating") else 0,
                    "verified": contractor.get("verified", False)
                })
            
            results["contractors"] = contractors_data
            results["total_contractors"] = len(contractors_data)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unified search failed: {str(e)}")


@router.get("/homeowner/{user_id}/summary")
async def get_homeowner_summary(user_id: str):
    """
    Get detailed summary for a specific homeowner
    Including all bid cards, total spending, project history
    """
    try:
        # Get all bid cards for this homeowner
        bid_cards_result = db.client.table("bid_cards").select("*").eq(
            "user_id", user_id
        ).order("created_at", desc=True).execute()
        
        bid_cards = bid_cards_result.data
        
        if not bid_cards:
            raise HTTPException(status_code=404, detail="No bid cards found for this homeowner")
        
        # Calculate summary statistics
        total_bid_cards = len(bid_cards)
        homeowner_name = bid_cards[0].get("homeowner_name", "Unknown")
        
        # Get status breakdown
        status_counts = {}
        total_budget_min = 0
        total_budget_max = 0
        project_types = set()
        
        for card in bid_cards:
            status = card.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Sum up budgets
            if card.get("budget_min"):
                total_budget_min += card["budget_min"]
            if card.get("budget_max"):
                total_budget_max += card["budget_max"]
            
            # Collect project types
            if card.get("project_type"):
                project_types.add(card["project_type"])
        
        # Try to get profile information
        profile_info = None
        try:
            profile_result = db.client.table("profiles").select("*").eq(
                "id", user_id
            ).single().execute()
            
            if profile_result.data:
                profile_info = {
                    "email": profile_result.data.get("email"),
                    "phone": profile_result.data.get("phone"),
                    "full_name": profile_result.data.get("full_name"),
                    "created_at": profile_result.data.get("created_at")
                }
        except:
            pass
        
        return {
            "user_id": user_id,
            "homeowner_name": homeowner_name,
            "profile": profile_info,
            "statistics": {
                "total_bid_cards": total_bid_cards,
                "status_breakdown": status_counts,
                "total_budget_range": {
                    "min": total_budget_min,
                    "max": total_budget_max
                },
                "project_types": list(project_types),
                "first_bid_card": bid_cards[-1].get("created_at") if bid_cards else None,
                "latest_bid_card": bid_cards[0].get("created_at") if bid_cards else None
            },
            "recent_bid_cards": bid_cards[:5],  # Show 5 most recent
            "all_bid_cards": bid_cards
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get homeowner summary: {str(e)}")


@router.get("/contractors")
async def search_contractors(
    search_term: str = Query("", description="Search term for contractors"),
    name: str = Query(None, description="Filter by contractor name"),
    location: str = Query(None, description="Filter by location"),
    specialty: str = Query(None, description="Filter by specialty"),
    limit: int = Query(50, description="Results per page"),
    offset: int = Query(0, description="Pagination offset")
):
    """
    Search for contractors by name, location, or specialty
    Returns contractor information with engagement history
    """
    try:
        # Join contractors with profiles to get user names
        query = db.client.table("contractors").select(
            "*, profiles!inner(full_name, email, phone)"
        )
        
        # Apply search filters
        if search_term:
            # Search across company_name and specialties
            query = query.or_(f"company_name.ilike.%{search_term}%,specialties.cs.{{{search_term}}}")
        
        if name:
            # This would search in the profiles.full_name - more complex query needed
            pass  # For now, skip complex profile name filtering
            
        if location:
            # Search in service_areas JSONB - would need custom query
            pass  # For now, skip service area filtering
            
        if specialty:
            # Search in specialties array
            query = query.contains("specialties", [specialty])
        
        # Add pagination
        query = query.range(offset, offset + limit - 1)
        
        response = query.execute()
        
        # Format the response to match expected structure
        contractors_data = []
        for contractor in response.data:
            profile = contractor.get("profiles", {})
            contractors_data.append({
                "id": contractor.get("id"),
                "name": profile.get("full_name", "Unknown"),
                "company": contractor.get("company_name"),
                "location": contractor.get("service_areas", {}).get("areas", ["Unknown"])[0] if isinstance(contractor.get("service_areas", {}), dict) else "Unknown",
                "specialties": ", ".join(contractor.get("specialties", [])) if contractor.get("specialties") else "",
                "email": profile.get("email"),
                "phone": profile.get("phone"),
                "tier": contractor.get("tier"),
                "response_rate": None,  # Would need separate calculation
                "rating": float(contractor.get("rating", 0)) if contractor.get("rating") else 0,
                "total_jobs": contractor.get("total_jobs", 0),
                "verified": contractor.get("verified", False)
            })
        
        # Simple count for now
        total_count = len(contractors_data)
        
        return {
            "contractors": contractors_data,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "search_term": search_term
        }
        
    except Exception as e:
        logger.error(f"Contractor search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Contractor search failed: {str(e)}")


@router.get("/autocomplete")
async def search_autocomplete(
    field: str = Query(..., description="Field to search: homeowner_name, bid_card_number, contractor_name"),
    term: str = Query(..., description="Search term"),
    limit: int = Query(10, description="Maximum suggestions")
):
    """
    Autocomplete suggestions for search fields
    """
    try:
        if field == "homeowner_name":
            # Get unique homeowner names
            query = db.client.table("bid_cards").select(
                "homeowner_name"
            ).not_.is_("homeowner_name", "null").ilike(
                "homeowner_name", f"{term}%"
            ).limit(limit)
            
            result = query.execute()
            
            # Get unique names
            names = list(set([r["homeowner_name"] for r in result.data if r.get("homeowner_name")]))
            return {"suggestions": names[:limit]}
        
        elif field == "bid_card_number":
            # Get bid card numbers
            query = db.client.table("bid_cards").select(
                "bid_card_number"
            ).ilike("bid_card_number", f"{term}%").limit(limit)
            
            result = query.execute()
            return {"suggestions": [r["bid_card_number"] for r in result.data]}
        
        elif field == "contractor_name":
            # Get contractor names from profiles joined with contractors
            query = db.client.table("contractors").select(
                "profiles!inner(full_name)"
            ).not_.is_("profiles.full_name", "null").limit(limit)
            
            result = query.execute()
            
            # Get unique names that match the term
            names = []
            for r in result.data:
                profile = r.get("profiles", {})
                full_name = profile.get("full_name", "")
                if full_name and term.lower() in full_name.lower():
                    names.append(full_name)
            
            return {"suggestions": list(set(names))[:limit]}
        
        else:
            return {"suggestions": []}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autocomplete failed: {str(e)}")


def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID"""
    try:
        import uuid
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False