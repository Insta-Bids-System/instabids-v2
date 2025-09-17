"""
COIA Projects Agent - COPIED FROM BSA
======================================
This is a direct copy of BSA's search_bid_cards function adapted for COIA.
Following the exact pattern that works in BSA.
"""

import logging
from typing import Any, Dict, List, Optional
import asyncio

logger = logging.getLogger(__name__)


def search_projects_sync(staging_id: str = None, contractor_zip: str = None, radius_miles: int = 30) -> Dict[str, Any]:
    """
    Synchronous wrapper for BSA's search function - for COIA DeepAgents compatibility
    This is what gets imported as bsa_projects in landing_deepagent.py
    """
    try:
        # Run the async function synchronously
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        
        if loop and loop.is_running():
            # We're in an event loop, run in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    search_bid_cards_for_contractor(
                        contractor_zip=contractor_zip or "33442",
                        radius_miles=radius_miles,
                        staging_id=staging_id
                    )
                )
                return future.result()
        else:
            # No event loop, safe to use asyncio.run
            return asyncio.run(
                search_bid_cards_for_contractor(
                    contractor_zip=contractor_zip or "33442", 
                    radius_miles=radius_miles,
                    staging_id=staging_id
                )
            )
    except Exception as e:
        logger.error(f"search_projects_sync error: {e}")
        return {
            "error": str(e),
            "total_found": 0,
            "bid_cards": []
        }


async def search_bid_cards_for_contractor(
    contractor_zip: str,
    radius_miles: int = 30,
    project_type: Optional[str] = None,
    contractor_type_ids: List[int] = [],
    staging_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    COPIED FROM BSA's search_bid_cards function
    Search for bid cards with accurate radius filtering and contractor type matching
    Uses direct database access with proper distance calculation
    
    Added staging_id parameter for COIA's needs but core logic is identical to BSA
    """
    # Import required utilities (EXACTLY like BSA does it)
    from utils.radius_search_fixed import filter_by_radius
    from database_simple import db
    
    try:
        logger.info(f"COIA-BSA Tool: Starting bid card search")
        logger.info(f"Location: {contractor_zip}, Radius: {radius_miles} miles")
        logger.info(f"Project Type: {project_type}")
        logger.info(f"Contractor Type IDs: {contractor_type_ids}")
        logger.info(f"Staging ID: {staging_id}")
        
        # If staging_id provided, try to get contractor info from staging
        if staging_id and not contractor_zip:
            try:
                staging_result = db.client.table("potential_contractors").select("zip_code").eq("id", staging_id).single().execute()
                if staging_result.data and staging_result.data.get("zip_code"):
                    contractor_zip = staging_result.data["zip_code"]
                    logger.info(f"COIA-BSA: Got ZIP {contractor_zip} from staging profile")
            except:
                pass
        
        # If no contractor_zip provided, try to get it from contractor profile
        if not contractor_zip:
            logger.warning("COIA-BSA: No contractor ZIP provided, using default...")
            contractor_zip = "33442"  # Default ZIP for testing
        
        # Step 1: Get all bid cards from database (EXACTLY like BSA)
        query = db.client.table('bid_cards').select('*')
        result = query.execute()
        bid_cards = result.data if result.data else []
        
        logger.info(f"COIA-BSA Tool: Retrieved {len(bid_cards)} total bid cards from database")
        
        # Step 2: Apply EXACT contractor type filtering - NO FALLBACKS
        if contractor_type_ids:
            type_matched_cards = []
            for card in bid_cards:
                card_type_ids = card.get('contractor_type_ids', [])
                # ONLY include bid cards that have contractor_type_ids AND have overlap
                if card_type_ids:
                    contractor_id_set = set(contractor_type_ids)
                    bid_card_id_set = set(card_type_ids)
                    overlap = contractor_id_set & bid_card_id_set
                    if overlap:
                        type_matched_cards.append(card)
                # NO FALLBACK - skip bid cards without contractor_type_ids
                        
            logger.info(f"COIA-BSA Tool: Found {len(type_matched_cards)} bid cards with EXACT contractor type matches {contractor_type_ids}")
            bid_cards = type_matched_cards
        
        # Step 3: Apply accurate radius filtering (EXACTLY like BSA)
        matching_cards = filter_by_radius(
            items=bid_cards,
            center_zip=contractor_zip,
            radius_miles=radius_miles,
            zip_field="location_zip"
        )
        
        logger.info(f"COIA-BSA Tool: Found {len(matching_cards)} bid cards within {radius_miles} miles after accurate filtering")
        
        # Step 4: Apply project type filtering if specified (EXACTLY like BSA)
        if project_type:
            project_filtered_cards = [
                card for card in matching_cards 
                if card.get('project_type', '').lower() == project_type.lower()
            ]
            logger.info(f"COIA-BSA Tool: Found {len(project_filtered_cards)} bid cards matching project type '{project_type}'")
            final_cards = project_filtered_cards
        else:
            final_cards = matching_cards
        
        # Step 5: Filter for available bid cards (not completed) (EXACTLY like BSA)
        available_cards = [
            card for card in final_cards
            if card.get('status', '').lower() in ['generated', 'collecting_bids', 'active']
        ]
        
        logger.info(f"COIA-BSA Tool: Found {len(available_cards)} available bid cards after status filtering")
        
        # Step 6: Return results with proper format (EXACTLY like BSA)
        return {
            "success": True,
            "bid_cards": available_cards[:10],  # Limit to 10 results for performance
            "total_found": len(available_cards),
            "search_criteria": {
                "location": contractor_zip,
                "radius": radius_miles,
                "project_type": project_type,
                "contractor_type_ids": contractor_type_ids,
                "staging_id": staging_id  # Added for COIA
            },
            "filters_applied": {
                "radius_accurate": True,
                "contractor_type_matching": len(contractor_type_ids) > 0,
                "project_type_filtering": project_type is not None,
                "status_filtering": True
            },
            "search_method": "direct_database_with_accurate_radius"
        }
        
    except Exception as e:
        logger.error(f"COIA-BSA: Error in search_bid_cards: {e}")
        import traceback
        logger.error(f"COIA-BSA: Traceback: {traceback.format_exc()}")
        
        return {
            "success": False,
            "error": str(e),
            "bid_cards": [],
            "total_found": 0
        }


# Sync wrapper for DeepAgents (BSA doesn't have this but COIA needs it)
def search_projects_sync(
    contractor_zip: str = None,
    radius_miles: int = 30,
    project_type: Optional[str] = None,
    contractor_type_ids: List[int] = None,
    staging_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Synchronous wrapper for DeepAgents compatibility.
    This is what COIA's subagents will call.
    """
    # Handle None contractor_type_ids
    if contractor_type_ids is None:
        contractor_type_ids = []
    
    # Handle case where staging_id is provided but no ZIP
    if staging_id and not contractor_zip:
        # Let the async function handle getting ZIP from staging
        pass
    
    try:
        # Check if we're already in an event loop
        loop = asyncio.get_running_loop()
        # We're in an event loop, create a task in a thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run,
                search_bid_cards_for_contractor(
                    contractor_zip=contractor_zip or "",
                    radius_miles=radius_miles,
                    project_type=project_type,
                    contractor_type_ids=contractor_type_ids,
                    staging_id=staging_id
                )
            )
            return future.result()
    except RuntimeError:
        # No event loop running, safe to use asyncio.run
        return asyncio.run(
            search_bid_cards_for_contractor(
                contractor_zip=contractor_zip or "",
                radius_miles=radius_miles,
                project_type=project_type,
                contractor_type_ids=contractor_type_ids,
                staging_id=staging_id
            )
        )