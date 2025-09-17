"""
Contractor job search API with radius-based filtering.
Dedicated endpoints for contractor agents and manual contractor search.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from database_simple import SupabaseDB

# Import our radius search utilities (using fixed uszipcode implementation)
from utils.radius_search_fixed import calculate_distance_miles, get_zip_codes_in_radius


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/contractor-jobs", tags=["contractor-jobs"])

@router.get("/search")
async def search_jobs_by_radius(
    zip_code: str = Query(..., description="Contractor's home zip code"),
    radius_miles: int = Query(25, ge=1, le=200, description="Search radius in miles"),
    project_types: Optional[list[str]] = Query(None, description="Filter by project types"),
    min_budget: Optional[int] = Query(None, description="Minimum budget filter"),
    max_budget: Optional[int] = Query(None, description="Maximum budget filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Search for job opportunities within a radius of contractor's location.
    
    This endpoint is designed for:
    1. Manual contractor search UI (with radius slider)
    2. Contractor agent automated job matching
    """

    try:
        logger.info(f"Contractor job search: zip={zip_code}, radius={radius_miles}mi")

        # Initialize database
        db = SupabaseDB()

        # Get zip codes within radius
        try:
            zip_codes_in_radius = get_zip_codes_in_radius(zip_code, radius_miles)
            logger.info(f"Found {len(zip_codes_in_radius)} zip codes in {radius_miles}mi radius")
            logger.info(f"First 5 zip codes: {zip_codes_in_radius[:5]}")
        except Exception as e:
            logger.error(f"Error getting zip codes in radius: {e}")
            zip_codes_in_radius = [zip_code]  # Fallback to single zip

        # Build query for bid cards
        query = db.client.table("bid_cards").select("*")

        # Filter by active statuses (available for bidding)
        query = query.in_("status", ["active", "collecting_bids", "ready"])

        # Apply radius filtering
        if zip_codes_in_radius:
            logger.info(f"Applying radius filter with {len(zip_codes_in_radius)} zip codes")
            query = query.in_("location_zip", zip_codes_in_radius)
        else:
            logger.warning(f"No zip codes in radius, using fallback to exact zip: {zip_code}")
            # Fallback to exact zip if radius search fails
            query = query.eq("location_zip", zip_code)

        # Apply additional filters
        if project_types and isinstance(project_types, list) and len(project_types) > 0:
            logger.info(f"Filtering by project types: {project_types}")
            query = query.in_("project_type", project_types)

        if min_budget and isinstance(min_budget, int):
            logger.info(f"Filtering by min budget: ${min_budget:,}")
            query = query.gte("budget_min", min_budget)

        if max_budget and isinstance(max_budget, int):
            logger.info(f"Filtering by max budget: ${max_budget:,}")
            query = query.lte("budget_max", max_budget)

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)

        # Execute query
        logger.info("Executing database query...")
        response = query.execute()
        logger.info(f"Database returned {len(response.data)} bid cards")

        # Process results with distance calculation
        job_opportunities = []
        for card in response.data:
            # Calculate distance from contractor's location
            card_zip = card.get("location_zip")
            distance_miles = None

            if card_zip:
                distance_miles = calculate_distance_miles(zip_code, str(card_zip))

            # Build job opportunity object
            job = {
                "id": card["id"],
                "bid_card_number": card.get("bid_card_number"),
                "title": card.get("title", "Untitled Project"),
                "description": card.get("description", ""),
                "project_type": card.get("project_type", "general"),
                "status": card.get("status", "active"),
                "budget_range": {
                    "min": card.get("budget_min", 0),
                    "max": card.get("budget_max", 0)
                },
                "location": {
                    "city": card.get("location_city"),
                    "state": card.get("location_state"),
                    "zip_code": card.get("location_zip")
                },
                "timeline": {
                    "start_date": card.get("timeline_start"),
                    "end_date": card.get("timeline_end")
                },
                "contractor_count_needed": card.get("contractor_count_needed", 1),
                "bid_count": card.get("bid_count", 0),
                "categories": card.get("categories", []),
                "group_bid_eligible": card.get("group_bid_eligible", False),
                "created_at": card.get("created_at"),
                "distance_miles": distance_miles,
                # Service complexity classification
                "service_complexity": card.get("service_complexity", "single-trade"),
                "trade_count": card.get("trade_count", 1),
                "primary_trade": card.get("primary_trade", "general"),
                "secondary_trades": card.get("secondary_trades", [])
            }

            job_opportunities.append(job)

        # Sort by distance (closest first)
        job_opportunities.sort(key=lambda x: x.get("distance_miles") or 999)

        # Get total count for pagination
        count_query = db.client.table("bid_cards").select("id", count="exact")
        count_query = count_query.in_("status", ["active", "collecting_bids", "ready"])

        if zip_codes_in_radius:
            count_query = count_query.in_("location_zip", zip_codes_in_radius)
        else:
            count_query = count_query.eq("location_zip", zip_code)

        if project_types:
            count_query = count_query.in_("project_type", project_types)
        if min_budget:
            count_query = count_query.gte("budget_min", min_budget)
        if max_budget:
            count_query = count_query.lte("budget_max", max_budget)

        count_response = count_query.execute()
        total_count = count_response.count if hasattr(count_response, "count") else len(job_opportunities)

        return {
            "job_opportunities": job_opportunities,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "radius_miles": radius_miles,
            "contractor_zip": zip_code,
            "zip_codes_searched": len(zip_codes_in_radius),
            "has_more": len(job_opportunities) == page_size
        }

    except Exception as e:
        logger.error(f"Error in contractor job search: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {e!s}")

@router.get("/supported-areas")
async def get_supported_search_areas():
    """
    Get information about supported search areas.
    With uszipcode, ALL US zip codes are supported.
    """
    try:
        return {
            "supported": "all_us_zip_codes",
            "message": "All US zip codes are supported via uszipcode database",
            "coverage": {
                "states": 50,
                "territories": "US territories included",
                "zip_codes": "40,000+ zip codes supported"
            },
            "examples": {
                "Florida": ["33442", "33431", "33060", "33064"],
                "California": ["90210", "94102", "95014"],
                "New York": ["10001", "11201", "10003"],
                "Texas": ["77001", "78701"],
                "Illinois": ["60601", "60602"]
            }
        }

    except Exception as e:
        logger.error(f"Error getting supported areas: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get supported areas: {e!s}")

@router.get("/agent-search")
async def agent_job_search(
    contractor_zip: str = Query(..., description="Agent's contractor zip code"),
    project_keywords: Optional[str] = Query(None, description="Keywords like 'artificial turf'"),
    radius_miles: int = Query(40, ge=5, le=100, description="Search radius"),
    limit: int = Query(10, ge=1, le=50, description="Max results to return")
):
    """
    Specialized endpoint for contractor agent to search jobs programmatically.
    
    Example: "Find artificial turf jobs in 40 mile radius from 90210"
    """

    try:
        logger.info(f"Agent job search: contractor_zip={contractor_zip}, keywords='{project_keywords}', radius={radius_miles}mi")

        # Use the main search but with agent-specific parameters
        results = await search_jobs_by_radius(
            zip_code=contractor_zip,
            radius_miles=radius_miles,
            page=1,
            page_size=limit
        )

        # Filter by keywords if provided
        if project_keywords:
            keywords = project_keywords.lower().split()
            filtered_jobs = []

            for job in results["job_opportunities"]:
                # Search in title, description, project_type, and categories
                search_text = " ".join([
                    job.get("title", "").lower(),
                    job.get("description", "").lower(),
                    job.get("project_type", "").lower(),
                    " ".join(job.get("categories", [])).lower()
                ])

                # Check if any keyword matches
                if any(keyword in search_text for keyword in keywords):
                    filtered_jobs.append(job)

            results["job_opportunities"] = filtered_jobs
            results["total"] = len(filtered_jobs)
            results["filtered_by_keywords"] = project_keywords

        # Add agent-specific metadata
        results["agent_search"] = True
        results["search_summary"] = f"Found {len(results['job_opportunities'])} jobs within {radius_miles} miles"

        if project_keywords:
            results["search_summary"] += f" matching '{project_keywords}'"

        return results

    except Exception as e:
        logger.error(f"Error in agent job search: {e}")
        raise HTTPException(status_code=500, detail=f"Agent search failed: {e!s}")
