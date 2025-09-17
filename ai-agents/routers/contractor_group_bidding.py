from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from uuid import uuid4
from database_simple import get_client
from utils.radius_search import get_zip_codes_in_radius, filter_by_radius

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic Models
class ContractorGroupPool(BaseModel):
    id: str
    category_id: str
    category_name: str
    category_icon: str
    zip_code: str
    city: Optional[str] = None
    state: Optional[str] = None
    member_count: int
    target_member_count: int
    pool_status: str
    created_at: str
    estimated_savings_percentage: float
    distance_miles: Optional[float] = None

class PoolProject(BaseModel):
    id: str
    homeowner_id: str
    pool_id: str
    property_address: Optional[str] = None
    property_details: Optional[Dict[str, Any]] = None
    preferred_schedule: Optional[Dict[str, Any]] = None
    budget_range: Optional[Dict[str, Any]] = None
    join_status: str
    joined_at: str

class GroupPackageRequest(BaseModel):
    pool_id: str
    selected_project_ids: List[str]
    package_name: str
    discount_percentage: float
    estimated_schedule: Optional[Dict[str, Any]] = None
    contractor_notes: Optional[str] = None

@router.get("/api/contractor/group-pools")
async def get_available_pools(
    category: str = Query("all", description="Service category filter"),
    radius: int = Query(10, description="Search radius in miles"),
    min_members: int = Query(3, description="Minimum pool members"),
    zip_code: Optional[str] = Query(None, description="Center ZIP code for search"),
    contractor_id: Optional[str] = Query(None, description="Contractor ID for personalization")
):
    """Get available group bidding pools for contractors"""
    try:
        supabase = get_client()
        
        # Get target ZIP codes based on radius and center ZIP code
        target_zip_codes = [zip_code] if zip_code else None
        if zip_code and radius > 0:
            try:
                # Use existing radius search utilities to get all ZIP codes in radius
                zip_codes_in_radius = get_zip_codes_in_radius(zip_code, radius)
                if zip_codes_in_radius:
                    target_zip_codes = zip_codes_in_radius
                    logger.info(f"Geographic search: Found {len(target_zip_codes)} ZIP codes within {radius} miles of {zip_code}")
                else:
                    logger.warning(f"No ZIP codes found within {radius} miles of {zip_code}, using exact match")
            except Exception as e:
                logger.warning(f"Radius search failed for {zip_code}: {e}, falling back to exact match")
                target_zip_codes = [zip_code]
        
        # Base query for active pools
        query = supabase.table("group_bidding_pools").select("""
            *,
            group_bidding_categories!inner(
                display_name,
                icon_name,
                category_code,
                service_complexity,
                typical_price_min,
                typical_price_max
            )
        """).eq("pool_status", "forming").gte("member_count", min_members)
        
        # Apply geographic filtering if ZIP codes specified
        if target_zip_codes:
            query = query.in_("zip_code", target_zip_codes)
        
        # Filter by category if specified
        if category != "all":
            # Map frontend category names to database category codes
            category_mapping = {
                "lawn-care": "lawn_maintenance",
                "pool-service": "pool_maintenance", 
                "ac-replacement": "hvac_repair",
                "roof-replacement": "roofing",
                "artificial-turf": "artificial_turf"
            }
            
            if category in category_mapping:
                query = query.eq("group_bidding_categories.category_code", category_mapping[category])
        
        # Execute query
        response = query.order("member_count", desc=True).execute()
        
        pools = []
        if response.data:
            for pool in response.data:
                category_data = pool["group_bidding_categories"]
                
                # Determine savings percentage based on pool size
                savings_percentage = 15.0  # Base discount
                if pool["member_count"] >= 8:
                    savings_percentage = 25.0
                elif pool["member_count"] >= 5:
                    savings_percentage = 20.0
                
                pool_data = ContractorGroupPool(
                    id=pool["id"],
                    category_id=pool["category_id"],
                    category_name=category_data["display_name"],
                    category_icon=category_data["icon_name"] or "🏠",
                    zip_code=pool["zip_code"],
                    city=pool.get("city"),
                    state=pool.get("state"),
                    member_count=pool["member_count"],
                    target_member_count=pool.get("target_member_count", 5),
                    pool_status=pool["pool_status"],
                    created_at=pool.get("created_at", datetime.now().isoformat()),
                    estimated_savings_percentage=savings_percentage
                )
                pools.append(pool_data)
        
        # Apply radius-based sorting if center ZIP code provided
        if zip_code and pools:
            try:
                # Convert pools to dict format for radius filtering
                pool_dicts = []
                for pool in pools:
                    pool_dict = {
                        "zip_code": pool.zip_code,
                        "pool_data": pool
                    }
                    pool_dicts.append(pool_dict)
                
                # Apply radius filtering and distance calculation
                filtered_pools = filter_by_radius(pool_dicts, zip_code, radius, "zip_code")
                
                # Extract sorted pools with distance information
                pools = []
                for item in filtered_pools:
                    pool_data = item["pool_data"]
                    # Add distance information if available
                    if "distance_miles" in item:
                        pool_data.distance_miles = item["distance_miles"]
                    pools.append(pool_data)
                
                logger.info(f"Geographic filtering: {len(pools)} pools within {radius} miles of {zip_code}")
                
            except Exception as e:
                logger.warning(f"Failed to apply geographic sorting: {e}")
                # Fall back to standard sorting
                pools.sort(key=lambda x: (x.member_count, x.estimated_savings_percentage), reverse=True)
        else:
            # Standard sorting when no geographic center specified
            pools.sort(key=lambda x: (x.member_count, x.estimated_savings_percentage), reverse=True)
        
        logger.info(f"Found {len(pools)} available pools for contractor browsing")
        return {
            "pools": pools,
            "total_count": len(pools),
            "filters": {
                "category": category,
                "radius": radius,
                "min_members": min_members,
                "zip_code": zip_code
            },
            "geographic_search": {
                "enabled": bool(zip_code and radius > 0),
                "center_zip": zip_code,
                "radius_miles": radius,
                "zip_codes_searched": len(target_zip_codes) if target_zip_codes else 0
            }
        }
    
    except Exception as e:
        logger.error(f"Error retrieving contractor pools: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve available pools")

@router.get("/api/contractor/group-pools/{pool_id}/projects")
async def get_pool_projects(
    pool_id: str,
    contractor_id: Optional[str] = Query(None, description="Contractor ID for audit trail")
):
    """Get detailed projects in a specific pool and auto-generate bid cards"""
    try:
        supabase = get_client()
        
        # Get pool details first
        pool_response = supabase.table("group_bidding_pools").select("""
            *,
            group_bidding_categories!inner(display_name, category_code)
        """).eq("id", pool_id).execute()
        
        if not pool_response.data:
            raise HTTPException(status_code=404, detail="Pool not found")
        
        pool = pool_response.data[0]
        
        # Get pool members (interested homeowners)
        members_response = supabase.table("group_pool_members").select("""
            *,
            homeowners!inner(id, address)
        """).eq("pool_id", pool_id).eq("join_status", "interested").execute()
        
        projects = []
        if members_response.data:
            for member in members_response.data:
                project = PoolProject(
                    id=member["id"],
                    homeowner_id=member["homeowner_id"],
                    pool_id=pool_id,
                    property_address=member.get("property_address") or member["homeowners"]["address"],
                    property_details=member.get("property_details"),
                    preferred_schedule=member.get("preferred_schedule"),
                    budget_range=member.get("budget_range"),
                    join_status=member["join_status"],
                    joined_at=member.get("joined_at", datetime.now().isoformat())
                )
                projects.append(project)
        
        # Sort projects by join date (most recent first)  
        projects.sort(key=lambda x: x.joined_at, reverse=True)
        
        # Mark that projects have been viewed by contractor (for analytics)
        if contractor_id:
            supabase.table("group_bidding_pools").update({
                "bid_cards_generated": True,
                "bid_cards_generated_at": datetime.now().isoformat()
            }).eq("id", pool_id).execute()
        
        logger.info(f"Generated {len(projects)} project details for pool {pool_id}")
        return {
            "pool_id": pool_id,
            "pool_info": {
                "category_name": pool["group_bidding_categories"]["display_name"],
                "zip_code": pool["zip_code"],
                "member_count": pool["member_count"],
                "pool_status": pool["pool_status"]
            },
            "projects": projects,
            "statistics": {
                "total_projects": len(projects),
                "recommended_group_discount": calculate_recommended_discount(len(projects))
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving pool projects: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pool projects")

@router.post("/api/contractor/group-packages")
async def create_group_package(package_request: GroupPackageRequest):
    """Create a group package offer for selected projects"""
    try:
        supabase = get_client()
        
        # Validate pool exists and is active
        pool_response = supabase.table("group_bidding_pools").select("*").eq(
            "id", package_request.pool_id
        ).eq("pool_status", "forming").execute()
        
        if not pool_response.data:
            raise HTTPException(status_code=404, detail="Pool not found or not accepting packages")
        
        # Validate selected projects exist in the pool
        selected_projects = supabase.table("group_pool_members").select("*").eq(
            "pool_id", package_request.pool_id
        ).in_("id", package_request.selected_project_ids).execute()
        
        if len(selected_projects.data) != len(package_request.selected_project_ids):
            raise HTTPException(status_code=400, detail="Some selected projects are invalid")
        
        # Create the group package
        package_id = str(uuid4())
        package_data = {
            "id": package_id,
            "pool_id": package_request.pool_id,
            "package_name": package_request.package_name,
            "selected_bid_cards": package_request.selected_project_ids,
            "discount_percentage": package_request.discount_percentage,
            "package_status": "draft",
            "estimated_schedule": package_request.estimated_schedule,
            "contractor_notes": package_request.contractor_notes,
            "created_at": datetime.now().isoformat(),
            "acceptance_deadline": (datetime.now() + timedelta(days=3)).isoformat()
        }
        
        # Insert package
        supabase.table("contractor_group_packages").insert(package_data).execute()
        
        # Create individual response tracking records
        for project_id in package_request.selected_project_ids:
            response_data = {
                "id": str(uuid4()),
                "package_id": package_id,
                "bid_card_id": project_id,
                "response": "pending"
            }
            supabase.table("package_member_responses").insert(response_data).execute()
        
        logger.info(f"Created group package {package_id} with {len(package_request.selected_project_ids)} projects")
        return {
            "success": True,
            "package_id": package_id,
            "package_details": {
                "name": package_request.package_name,
                "selected_projects": len(package_request.selected_project_ids),
                "discount_percentage": package_request.discount_percentage
            },
            "next_steps": "Package created and ready to send to homeowners"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating group package: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create group package")

@router.post("/api/contractor/group-packages/{package_id}/generate-bid-cards")
async def generate_bid_cards_from_package(package_id: str):
    """Convert group package into actual bid cards in the bid_cards table"""
    try:
        supabase = get_client()
        
        # Get the group package details
        package_response = supabase.table("contractor_group_packages").select("""
            *,
            group_bidding_pools!inner(
                zip_code,
                city,
                state,
                group_bidding_categories!inner(display_name, category_code)
            )
        """).eq("id", package_id).execute()
        
        if not package_response.data:
            raise HTTPException(status_code=404, detail="Group package not found")
        
        package = package_response.data[0]
        pool = package["group_bidding_pools"]
        category = pool["group_bidding_categories"]
        
        # Get the selected projects from group_pool_members
        selected_projects = supabase.table("group_pool_members").select("""
            *,
            homeowners!inner(user_id, address, phone, email)
        """).eq("pool_id", package["pool_id"]).in_(
            "id", package["selected_bid_cards"]
        ).execute()
        
        if not selected_projects.data:
            raise HTTPException(status_code=400, detail="No valid projects found in package")
        
        # Create individual bid cards for each selected project
        bid_cards_created = []
        
        for project in selected_projects.data:
            homeowner = project["homeowners"]
            
            # Generate unique bid card number with group identifier
            bid_card_number = f"BC-GROUP-{str(uuid4())[:8].upper()}"
            
            # Create bid card with group bidding context
            bid_card_data = {
                "id": str(uuid4()),
                "bid_card_number": bid_card_number,
                "homeowner_id": homeowner["user_id"],
                "project_type": category["category_code"],
                "project_description": f"Group {category['display_name']} project - {package['package_name']}",
                "location": {
                    "address": homeowner.get("address", ""),
                    "city": pool.get("city", ""),
                    "state": pool.get("state", ""),
                    "zip_code": pool["zip_code"]
                },
                "urgency_level": "group_bidding",
                "timeline_preference": package.get("estimated_schedule") or {
                    "type": "coordinated_group", 
                    "notes": "Flexible timing to coordinate with other group members"
                },
                "budget_range": {
                    "type": "group_discount", 
                    "discount_percentage": package["discount_percentage"],
                    "notes": f"Group package offers {package['discount_percentage']}% savings"
                },
                "contractor_count_needed": 1,  # Group bidding targets one contractor
                "status": "group_package_created",
                "bid_document": {
                    "group_package_id": package_id,
                    "pool_id": package["pool_id"],
                    "discount_percentage": package["discount_percentage"],
                    "is_group_bid": True,
                    "group_coordinator_notes": package.get("contractor_notes", ""),
                    "homeowner_requirements": project.get("property_details", {}),
                    "acceptance_deadline": package.get("acceptance_deadline"),
                    "submitted_bids": [],
                    "group_members_count": len(selected_projects.data),
                    "package_name": package["package_name"]
                },
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Insert bid card into the main bid_cards table
            result = supabase.table("bid_cards").insert(bid_card_data).execute()
            
            if result.data:
                bid_cards_created.append({
                    "bid_card_id": result.data[0]["id"],
                    "bid_card_number": bid_card_number,
                    "homeowner_id": homeowner["user_id"],
                    "project_id": project["id"],
                    "homeowner_contact": {
                        "email": homeowner.get("email"),
                        "phone": homeowner.get("phone")
                    }
                })
        
        # Update the group package status to indicate bid cards were created
        supabase.table("contractor_group_packages").update({
            "package_status": "bid_cards_generated",
            "bid_cards_generated_at": datetime.now().isoformat(),
            "actual_bid_card_ids": [card["bid_card_id"] for card in bid_cards_created],
            "updated_at": datetime.now().isoformat()
        }).eq("id", package_id).execute()
        
        # Update package_member_responses to link to actual bid cards
        for card in bid_cards_created:
            supabase.table("package_member_responses").update({
                "actual_bid_card_id": card["bid_card_id"],
                "response_status": "bid_card_created"
            }).eq("package_id", package_id).eq("bid_card_id", card["project_id"]).execute()
        
        logger.info(f"Generated {len(bid_cards_created)} bid cards from group package {package_id}")
        
        return {
            "success": True,
            "package_id": package_id,
            "bid_cards_created": bid_cards_created,
            "integration_details": {
                "bid_cards_table": "All projects now have entries in main bid_cards table",
                "group_context": "Each bid card contains group package information",
                "contractor_workflow": "Contractors can now bid on individual projects or entire package",
                "homeowner_notifications": "Homeowners can be notified of group participation opportunity"
            },
            "next_steps": {
                "contractor_bidding": "Group package is now integrated with bid card system",
                "homeowner_approval": "Individual homeowners can approve/decline participation",
                "bid_submission": "Contractor can submit coordinated bids through BSA agent"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating bid cards from package {package_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate bid cards from package")

@router.get("/api/contractor/group-packages/{package_id}/status")
async def get_group_package_status(package_id: str):
    """Get the current status of a group package and its bid cards"""
    try:
        supabase = get_client()
        
        # Get package details with bid card information
        package_response = supabase.table("contractor_group_packages").select("*").eq(
            "id", package_id
        ).execute()
        
        if not package_response.data:
            raise HTTPException(status_code=404, detail="Group package not found")
        
        package = package_response.data[0]
        
        # Get bid cards if they were generated
        bid_cards = []
        if package.get("actual_bid_card_ids"):
            bid_cards_response = supabase.table("bid_cards").select("""
                id, bid_card_number, status, homeowner_id, 
                bid_document, created_at, updated_at
            """).in_("id", package["actual_bid_card_ids"]).execute()
            bid_cards = bid_cards_response.data or []
        
        # Get response status from homeowners
        responses = supabase.table("package_member_responses").select("*").eq(
            "package_id", package_id
        ).execute()
        
        response_summary = {
            "pending": 0,
            "approved": 0,
            "declined": 0,
            "bid_card_created": 0
        }
        
        for response in responses.data or []:
            status = response.get("response_status", "pending")
            response_summary[status] = response_summary.get(status, 0) + 1
        
        return {
            "package_id": package_id,
            "package_status": package["package_status"],
            "package_name": package["package_name"],
            "discount_percentage": package["discount_percentage"],
            "created_at": package["created_at"],
            "bid_cards_generated": len(bid_cards),
            "bid_cards": bid_cards,
            "homeowner_responses": response_summary,
            "integration_status": {
                "connected_to_bid_system": len(bid_cards) > 0,
                "ready_for_bsa_agent": package["package_status"] == "bid_cards_generated",
                "can_submit_bids": all(card["status"] in ["group_package_created", "collecting_bids"] for card in bid_cards)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting group package status {package_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get package status")

@router.get("/api/contractor/group-eligible-bid-cards")
async def get_group_eligible_bid_cards(
    category: str = Query("all", description="Service category filter"),
    radius: int = Query(10, description="Search radius in miles"),
    zip_code: Optional[str] = Query(None, description="Center ZIP code for search"),
    contractor_id: Optional[str] = Query(None, description="Contractor ID for personalization")
):
    """Get all bid cards that have group bidding enabled - searches actual bid_cards table"""
    try:
        supabase = get_client()
        
        # Build query for group-eligible bid cards
        query = supabase.table("bid_cards").select("""
            id,
            bid_card_number,
            project_type,
            title,
            description,
            location_city,
            location_state,
            location_zip,
            urgency_level,
            group_bid_eligible,
            status,
            budget_min,
            budget_max,
            bid_document,
            created_at,
            updated_at,
            homeowner_id,
            contractor_count_needed
        """).eq("group_bid_eligible", True).in_("status", ["active", "pending", "generated", "collecting_bids"])
        
        # Apply geographic filtering if ZIP code specified
        if zip_code and radius > 0:
            try:
                # Get ZIP codes within radius
                nearby_zips = get_zip_codes_in_radius(zip_code, radius)
                if nearby_zips:
                    query = query.in_("location_zip", nearby_zips)
                    logger.info(f"Searching {len(nearby_zips)} ZIP codes within {radius} miles of {zip_code}")
            except Exception as e:
                logger.warning(f"Radius search failed: {e}, using exact ZIP match")
                query = query.eq("location_zip", zip_code)
        elif zip_code:
            query = query.eq("location_zip", zip_code)
        
        # Apply category filtering
        if category != "all":
            category_mapping = {
                "lawn-care": ["lawn", "grass", "turf"],
                "landscaping": ["landscap", "garden", "yard"],
                "pool-service": ["pool"],
                "ac-replacement": ["hvac", "ac", "air condition"],
                "roof-replacement": ["roof"],
                "artificial-turf": ["turf", "artificial", "synthetic"]
            }
            
            if category in category_mapping:
                search_terms = category_mapping[category]
                # Create OR condition for multiple search terms
                or_conditions = []
                for term in search_terms:
                    or_conditions.append(f"project_type.ilike.%{term}%")
                if or_conditions:
                    query = query.or_(",".join(or_conditions))
        
        # Execute query
        response = query.order("created_at", desc=True).execute()
        
        # Process results to create virtual "pools" from bid cards
        bid_cards = response.data or []
        
        # Group bid cards by location and type for pool creation
        location_groups = {}
        for card in bid_cards:
            # Create location key
            location_key = f"{card.get('location_city', 'Unknown')}, {card.get('location_state', 'Unknown')} {card.get('location_zip', '')}"
            project_type = card.get('project_type', 'general')
            
            # Create group key combining location and type
            group_key = f"{location_key}|{project_type}"
            
            if group_key not in location_groups:
                location_groups[group_key] = {
                    "location": location_key,
                    "project_type": project_type,
                    "bid_cards": []
                }
            location_groups[group_key]["bid_cards"].append(card)
        
        # Calculate distance for each bid card if center ZIP provided
        if zip_code:
            for card in bid_cards:
                card_zip = card.get("location_zip")
                if card_zip:
                    try:
                        # Simple distance calculation placeholder
                        # In production, use proper geocoding
                        card["distance_miles"] = 5.0  # Placeholder
                    except:
                        card["distance_miles"] = None
        
        logger.info(f"Found {len(bid_cards)} group-eligible bid cards")
        
        return {
            "bid_cards": bid_cards,
            "total_count": len(bid_cards),
            "location_groups": list(location_groups.values()),
            "filters": {
                "category": category,
                "radius": radius,
                "zip_code": zip_code
            },
            "summary": {
                "total_bid_cards": len(bid_cards),
                "unique_locations": len(set(card.get("location_zip", "") for card in bid_cards)),
                "potential_savings": "15-25% with group bidding"
            }
        }
    
    except Exception as e:
        logger.error(f"Error retrieving group-eligible bid cards: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve group-eligible bid cards")

# Helper Functions
def calculate_recommended_discount(project_count: int) -> float:
    """Calculate recommended group discount based on project count"""
    if project_count >= 10:
        return 25.0
    elif project_count >= 7:
        return 20.0
    elif project_count >= 5:
        return 17.5
    elif project_count >= 3:
        return 15.0
    else:
        return 10.0