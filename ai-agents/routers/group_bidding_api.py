"""
Group Bidding API Routes
Handles Quick-Start Group Bidding with pre-defined service categories
"""

import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from database_simple import get_client

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic Models
class ServiceCategory(BaseModel):
    id: str
    category_code: str
    display_name: str
    description: str
    service_type: str
    frequency: Optional[str]
    typical_price_min: float
    typical_price_max: float
    icon_name: str
    sort_order: int
    is_active: bool
    service_complexity: str
    primary_trade: str
    group_discount_tiers: Dict[str, float]

class GroupPool(BaseModel):
    id: str
    category_id: str
    zip_code: str
    city: Optional[str]
    state: Optional[str]
    pool_status: str
    member_count: int
    target_member_count: int
    start_date: Optional[date]
    end_date: Optional[date]
    estimated_savings_percentage: Optional[float]
    created_at: datetime

class PoolMember(BaseModel):
    id: str
    pool_id: str
    homeowner_id: str
    join_status: str
    property_address: Optional[str]
    property_details: Optional[Dict[str, Any]]
    preferred_schedule: Optional[Dict[str, Any]]
    budget_range: Optional[Dict[str, Any]]
    joined_at: datetime

class CreatePoolRequest(BaseModel):
    category_id: str
    zip_code: str
    city: Optional[str] = None
    state: Optional[str] = None
    homeowner_id: str
    property_address: Optional[str] = None
    property_details: Optional[Dict[str, Any]] = None
    preferred_schedule: Optional[Dict[str, Any]] = None
    budget_range: Optional[Dict[str, Any]] = None

class JoinPoolRequest(BaseModel):
    homeowner_id: str
    property_address: Optional[str] = None
    property_details: Optional[Dict[str, Any]] = None
    preferred_schedule: Optional[Dict[str, Any]] = None
    budget_range: Optional[Dict[str, Any]] = None

@router.get("/api/group-categories", response_model=List[ServiceCategory])
async def get_service_categories(
    active_only: bool = Query(True, description="Return only active categories")
):
    """Get all available service categories for group bidding"""
    try:
        supabase = get_client()
        
        query = supabase.table("group_bidding_categories").select("*")
        if active_only:
            query = query.eq("is_active", True)
        
        response = query.order("sort_order").execute()
        
        if response.data:
            categories = []
            for cat in response.data:
                categories.append(ServiceCategory(
                    id=cat["id"],
                    category_code=cat["category_code"],
                    display_name=cat["display_name"],
                    description=cat["description"] or "",
                    service_type=cat["service_type"],
                    frequency=cat["frequency"],
                    typical_price_min=float(cat["typical_price_min"] or 0),
                    typical_price_max=float(cat["typical_price_max"] or 0),
                    icon_name=cat["icon_name"] or "",
                    sort_order=cat["sort_order"] or 0,
                    is_active=cat["is_active"],
                    service_complexity=cat["service_complexity"] or "single-trade",
                    primary_trade=cat["primary_trade"] or "",
                    group_discount_tiers=cat["group_discount_tiers"] or {}
                ))
            
            logger.info(f"Retrieved {len(categories)} service categories")
            return categories
        
        return []
    
    except Exception as e:
        logger.error(f"Error retrieving service categories: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve service categories")

@router.get("/api/group-pools/local")
async def get_local_pools(
    zip_code: str = Query(..., description="ZIP code to search for pools"),
    category_id: Optional[str] = Query(None, description="Filter by category")
):
    """Get existing pools in a specific area"""
    try:
        supabase = get_client()
        
        query = supabase.table("group_bidding_pools").select("""
            *,
            group_bidding_categories!inner(display_name, icon_name, primary_trade)
        """).eq("zip_code", zip_code).eq("pool_status", "forming")
        
        if category_id:
            query = query.eq("category_id", category_id)
        
        response = query.execute()
        
        pools = []
        if response.data:
            for pool in response.data:
                pool_data = {
                    **pool,
                    "category_name": pool["group_bidding_categories"]["display_name"],
                    "category_icon": pool["group_bidding_categories"]["icon_name"],
                    "primary_trade": pool["group_bidding_categories"]["primary_trade"]
                }
                pools.append(pool_data)
        
        logger.info(f"Found {len(pools)} local pools for ZIP {zip_code}")
        return {"pools": pools, "zip_code": zip_code}
    
    except Exception as e:
        logger.error(f"Error retrieving local pools: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve local pools")

@router.post("/api/group-pools/create")
async def create_pool(request: CreatePoolRequest):
    """Create a new group pool or join an existing one"""
    try:
        supabase = get_client()
        
        # Check if pool already exists for this category and ZIP code
        existing_pool = supabase.table("group_bidding_pools").select("*").eq(
            "category_id", request.category_id
        ).eq("zip_code", request.zip_code).eq("pool_status", "forming").execute()
        
        if existing_pool.data:
            # Join existing pool
            pool = existing_pool.data[0]
            pool_id = pool["id"]
            
            # Check if user already joined this pool
            existing_member = supabase.table("group_pool_members").select("*").eq(
                "pool_id", pool_id
            ).eq("homeowner_id", request.homeowner_id).execute()
            
            if existing_member.data:
                raise HTTPException(status_code=400, detail="You have already joined this pool")
            
            # Add member to existing pool
            member_data = {
                "id": str(uuid4()),
                "pool_id": pool_id,
                "homeowner_id": request.homeowner_id,
                "join_status": "interested",
                "property_address": request.property_address,
                "property_details": request.property_details,
                "preferred_schedule": request.preferred_schedule,
                "budget_range": request.budget_range
            }
            
            supabase.table("group_pool_members").insert(member_data).execute()
            
            # Update member count
            new_member_count = pool["member_count"] + 1
            supabase.table("group_bidding_pools").update({
                "member_count": new_member_count
            }).eq("id", pool_id).execute()
            
            logger.info(f"Homeowner {request.homeowner_id} joined existing pool {pool_id}")
            return {
                "action": "joined_existing",
                "pool_id": pool_id,
                "member_count": new_member_count,
                "message": f"You've joined {new_member_count} neighbors for group savings!"
            }
        
        else:
            # Create new pool
            pool_id = str(uuid4())
            pool_data = {
                "id": pool_id,
                "category_id": request.category_id,
                "zip_code": request.zip_code,
                "city": request.city,
                "state": request.state,
                "pool_status": "forming",
                "member_count": 1,
                "target_member_count": 3,
                "start_date": datetime.now().date().isoformat(),
                "estimated_savings_percentage": 15.0
            }
            
            supabase.table("group_bidding_pools").insert(pool_data).execute()
            
            # Add creator as first member
            member_data = {
                "id": str(uuid4()),
                "pool_id": pool_id,
                "homeowner_id": request.homeowner_id,
                "join_status": "interested",
                "property_address": request.property_address,
                "property_details": request.property_details,
                "preferred_schedule": request.preferred_schedule,
                "budget_range": request.budget_range
            }
            
            supabase.table("group_pool_members").insert(member_data).execute()
            
            logger.info(f"Created new pool {pool_id} with homeowner {request.homeowner_id}")
            return {
                "action": "created_new",
                "pool_id": pool_id,
                "member_count": 1,
                "message": "Group started! We'll notify you when 2 more neighbors join."
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating/joining pool: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create or join pool")

@router.post("/api/group-pools/{pool_id}/join")
async def join_pool(pool_id: str, request: JoinPoolRequest):
    """Join an existing pool"""
    try:
        supabase = get_client()
        
        # Check if pool exists and is accepting members
        pool = supabase.table("group_bidding_pools").select("*").eq("id", pool_id).execute()
        
        if not pool.data:
            raise HTTPException(status_code=404, detail="Pool not found")
        
        pool_data = pool.data[0]
        if pool_data["pool_status"] != "forming":
            raise HTTPException(status_code=400, detail="Pool is no longer accepting members")
        
        # Check if user already joined this pool
        existing_member = supabase.table("group_pool_members").select("*").eq(
            "pool_id", pool_id
        ).eq("homeowner_id", request.homeowner_id).execute()
        
        if existing_member.data:
            raise HTTPException(status_code=400, detail="You have already joined this pool")
        
        # Add member to pool
        member_data = {
            "id": str(uuid4()),
            "pool_id": pool_id,
            "homeowner_id": request.homeowner_id,
            "join_status": "interested",
            "property_address": request.property_address,
            "property_details": request.property_details,
            "preferred_schedule": request.preferred_schedule,
            "budget_range": request.budget_range
        }
        
        supabase.table("group_pool_members").insert(member_data).execute()
        
        # Update member count
        new_member_count = pool_data["member_count"] + 1
        supabase.table("group_bidding_pools").update({
            "member_count": new_member_count
        }).eq("id", pool_id).execute()
        
        # Check if pool should be activated
        if new_member_count >= pool_data["target_member_count"]:
            supabase.table("group_bidding_pools").update({
                "pool_status": "active",
                "activated_at": datetime.now().isoformat()
            }).eq("id", pool_id).execute()
            
            logger.info(f"Pool {pool_id} activated with {new_member_count} members")
            return {
                "joined": True,
                "pool_activated": True,
                "member_count": new_member_count,
                "message": f"Great news! Your group is ready with {new_member_count} members. Contractors are being notified now."
            }
        
        logger.info(f"Homeowner {request.homeowner_id} joined pool {pool_id}")
        return {
            "joined": True,
            "pool_activated": False,
            "member_count": new_member_count,
            "message": f"You've joined {new_member_count} neighbors! Need {pool_data['target_member_count'] - new_member_count} more for group discount."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining pool: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to join pool")

@router.get("/api/group-pools/{pool_id}/members")
async def get_pool_members(pool_id: str):
    """Get members of a specific pool"""
    try:
        supabase = get_client()
        
        response = supabase.table("group_pool_members").select("""
            *,
            homeowners(company_name)
        """).eq("pool_id", pool_id).execute()
        
        members = []
        if response.data:
            for member in response.data:
                member_data = {
                    **member,
                    "homeowner_name": member.get("homeowners", {}).get("company_name", "Anonymous")
                }
                members.append(member_data)
        
        return {"pool_id": pool_id, "members": members, "member_count": len(members)}
    
    except Exception as e:
        logger.error(f"Error retrieving pool members: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pool members")

@router.get("/api/group-categories/{category_id}/local-stats")
async def get_category_local_stats(
    category_id: str,
    zip_code: str = Query(..., description="ZIP code for local statistics")
):
    """Get local statistics for a specific service category"""
    try:
        supabase = get_client()
        
        # Get active pools for this category and ZIP
        pools = supabase.table("group_bidding_pools").select("*").eq(
            "category_id", category_id
        ).eq("zip_code", zip_code).eq("pool_status", "forming").execute()
        
        # Get completed pools for this category and ZIP (for success rate)
        completed_pools = supabase.table("group_bidding_pools").select("*").eq(
            "category_id", category_id
        ).eq("zip_code", zip_code).eq("pool_status", "fulfilled").execute()
        
        total_active_members = sum(pool["member_count"] for pool in pools.data) if pools.data else 0
        completed_count = len(completed_pools.data) if completed_pools.data else 0
        
        # Calculate potential savings based on member count
        potential_savings = 15  # Base discount
        if total_active_members >= 6:
            potential_savings = 20
        elif total_active_members >= 11:
            potential_savings = 25
        
        return {
            "category_id": category_id,
            "zip_code": zip_code,
            "active_pools": len(pools.data) if pools.data else 0,
            "total_active_members": total_active_members,
            "completed_pools": completed_count,
            "potential_savings_percentage": potential_savings,
            "next_group_starts": "Within 48 hours" if total_active_members > 0 else "Be the first!",
            "spots_remaining": max(0, 3 - total_active_members) if total_active_members < 3 else 0
        }
    
    except Exception as e:
        logger.error(f"Error retrieving category statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve category statistics")