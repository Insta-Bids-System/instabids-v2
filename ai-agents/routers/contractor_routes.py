"""
Contractor Routes - Contractor Portal and Communication API Endpoints
Owner: Agent 4 (Contractor UX)
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Import unified COIA API client for contractor communication
# Import database connection
from database_simple import db
# Import contractor bid matching API
from api.contractor_bid_matching import find_matching_projects
# Import HTTP client for unified COIA API calls
import httpx
from config.service_urls import get_backend_url


# Create router
router = APIRouter()

logger = logging.getLogger(__name__)

# Pydantic models
class BidCardContext(BaseModel):
    contractor_name: Optional[str] = None
    message_id: Optional[str] = None
    campaign_id: Optional[str] = None
    source: Optional[str] = None
    pre_loaded_data: Optional[dict[str, Any]] = None

class ContractorChatMessage(BaseModel):
    message: str
    session_id: str
    current_stage: Optional[str] = None
    profile_data: Optional[dict[str, Any]] = None
    bid_card_context: Optional[BidCardContext] = None

class ContractorChatResponse(BaseModel):
    response: str
    stage: str
    profile_progress: dict[str, Any]
    contractor_id: Optional[str] = None
    session_data: dict[str, Any]

# BidSubmissionRequest model removed - using bid_card_api_simple.py for bid submissions

# ContractorBidView model removed - using bid_card_api_simple.py for bid submissions

# Unified COIA API endpoint base URL
COIA_API_BASE = f"{get_backend_url()}/api/coia"

async def call_coia_api(endpoint: str, data: dict) -> dict:
    """Make HTTP call to unified COIA API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{COIA_API_BASE}/{endpoint}", json=data, timeout=30.0)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error calling COIA API {endpoint}: {e}")
        return {
            "success": False,
            "error": str(e),
            "response": "I'm having trouble connecting right now. Please try again in a moment."
        }

@router.post("/chat/message", response_model=ContractorChatResponse)
async def contractor_chat(chat_data: ContractorChatMessage):
    """Handle contractor onboarding chat messages via unified COIA API"""
    try:
        # Prepare request data for unified COIA API
        api_request = {
            "message": chat_data.message,
            "session_id": chat_data.session_id,
            "contractor_lead_id": None,  # Could be enhanced to track contractor leads
            "context": {
                "current_stage": chat_data.current_stage,
                "profile_data": chat_data.profile_data or {}
            }
        }
        
        # Add bid card context if available
        if chat_data.bid_card_context:
            api_request["context"]["bid_card_context"] = chat_data.bid_card_context.dict()
            logger.info(f"Processing contractor chat with bid card context: {chat_data.bid_card_context.contractor_name}")
        
        # Call unified COIA API
        result = await call_coia_api("chat", api_request)
        
        if not result.get("success", False):
            # API returned error
            return ContractorChatResponse(
                response=result.get("response", "I'm having trouble processing that right now. Please try again."),
                stage=chat_data.current_stage or "welcome",
                profile_progress={
                    "completeness": 0,
                    "stage": chat_data.current_stage or "welcome",
                    "collectedData": chat_data.profile_data or {},
                    "matchingProjects": 0
                },
                contractor_id=None,
                session_data={}
            )
        
        # Convert unified API response to contractor chat response format
        return ContractorChatResponse(
            response=result.get("response", "Thank you for your message."),
            stage=result.get("current_mode", chat_data.current_stage or "conversation"),
            profile_progress={
                "completeness": result.get("profile_completeness", 0) or 0,
                "stage": result.get("current_mode", "conversation"),
                "collectedData": result.get("contractor_profile", {}),
                "matchingProjects": 0  # Could be enhanced with bid card search results
            },
            contractor_id=result.get("contractor_id"),
            session_data={
                "completion_ready": result.get("completion_ready", False),
                "contractor_created": result.get("contractor_created", False),
                "research_completed": result.get("research_completed", False),
                "last_updated": result.get("last_updated")
            }
        )

    except Exception as e:
        import traceback
        logger.error(f"Error in contractor chat: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Fallback response
        return ContractorChatResponse(
            response="I apologize, but I'm having trouble processing that right now. Could you please try rephrasing your response?",
            stage=chat_data.current_stage or "welcome",
            profile_progress={
                "completeness": 0,
                "stage": chat_data.current_stage or "welcome",
                "collectedData": chat_data.profile_data or {},
                "matchingProjects": 0
            },
            contractor_id=None,
            session_data={}
        )


# Bid Card Endpoints for Contractor Marketplace

@router.get("/test-db")
async def test_database_connection():
    """Test database connection"""
    try:
        logger.info("Testing database connection")
        supabase_client = db.client
        logger.info(f"Got client: {type(supabase_client)}")

        # Simple query
        response = supabase_client.table("bid_cards").select("id, bid_card_number").limit(1).execute()
        logger.info(f"Query response: {response}")

        return {"status": "success", "data": response.data}
    except Exception as e:
        logger.error(f"Database test error: {e}")
        return {"status": "error", "error": str(e)}

@router.get("/bid-cards/{bid_card_id}/contractor-view")
async def get_contractor_bid_card_view(bid_card_id: str, contractor_id: str = Query(...)):
    """
    Get bid card details for contractor view - Simplified working version
    """
    try:
        supabase_client = db.client

        # Get bid card details using safe query
        result = supabase_client.table("bid_cards").select(
            "id, bid_card_number, project_type, status, budget_min, budget_max, "
            "created_at, urgency_level, contractor_count_needed, "
            "service_complexity, trade_count, primary_trade, secondary_trades"
        ).eq("id", bid_card_id).single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Bid card not found")

        bid_card = result.data

        # Return contractor view with safe field access
        return {
            "id": bid_card.get("id", ""),
            "bid_card_number": bid_card.get("bid_card_number", ""),
            "title": bid_card.get("project_type", "Project"),
            "description": f"Project: {bid_card.get('project_type', 'No description available')}",
            "project_type": bid_card.get("project_type", ""),
            "urgency_level": bid_card.get("urgency_level", "standard"),
            "budget_range": {
                "min": bid_card.get("budget_min", 0) or 0,
                "max": bid_card.get("budget_max", 0) or 0
            },
            "status": bid_card.get("status", "active"),
            "contractor_count_needed": bid_card.get("contractor_count_needed", 5) or 5,
            "has_submitted_bid": False,  # Simplified for now
            "can_bid": True,  # Simplified for now
            "created_at": bid_card.get("created_at", ""),
            "bids_received_count": 0,  # Simplified for now
            # Service complexity classification
            "service_complexity": bid_card.get("service_complexity", "single-trade"),
            "trade_count": bid_card.get("trade_count", 1),
            "primary_trade": bid_card.get("primary_trade", "general"),
            "secondary_trades": bid_card.get("secondary_trades", [])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in contractor view: {e!s}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Unused bid submission endpoint removed - using bid_card_api_simple.py for production bid submissions


@router.get("/contractors/{contractor_id}/profile")
async def get_contractor_profile(contractor_id: str):
    """Get contractor profile data"""
    try:
        # Always get from database - no more hardcoded demo data
        supabase_client = db.client
        result = supabase_client.table("contractors").select("*").eq("id", contractor_id).single().execute()

        if result.data:
            contractor = result.data
            return {
                "company_name": contractor.get("company_name", "Contractor"),
                "phone": contractor.get("phone", ""),
                "website": contractor.get("website", ""),
                "address": contractor.get("address", ""),
                "specialties": contractor.get("specialties", []),
                "service_areas": contractor.get("service_areas", []),
                "social_media": contractor.get("social_media", {}),
                "verified": contractor.get("verified", False),
                "rating": contractor.get("rating"),
                "tier": contractor.get("tier", 3),
                "research_source": "database",
            }
        else:
            # Try contractor_leads table as fallback
            leads_result = supabase_client.table("contractor_leads").select("*").eq("id", contractor_id).single().execute()
            
            if leads_result.data:
                lead = leads_result.data
                return {
                    "company_name": lead.get("company_name", "Contractor"),
                    "phone": lead.get("phone", ""),
                    "website": lead.get("website", ""),
                    "address": lead.get("address", ""),
                    "specialties": lead.get("specialties", []),
                    "service_areas": lead.get("service_areas", []),
                    "social_media": lead.get("social_media", {}),
                    "research_source": "contractor_leads",
                }
            else:
                # Return minimal fallback data
                return {
                    "company_name": f"Contractor {contractor_id[:8]}",
                    "phone": "Not available",
                    "website": "",
                    "address": "Not available",
                    "specialties": ["General contractor"],
                    "service_areas": ["Local area"],
                    "social_media": {},
                    "research_source": "fallback",
                }

    except Exception as e:
        logger.error(f"Error getting contractor profile: {e}")
        # Return fallback data on error
        return {
            "company_name": f"Contractor {contractor_id[:8]}",
            "phone": "Not available",
            "website": "",
            "address": "Not available",
            "specialties": ["General contractor"],
            "service_areas": ["Local area"],
            "social_media": {},
            "research_source": "fallback",
        }

@router.get("/contractors/{contractor_id}/projects")
async def get_contractor_projects(contractor_id: str):
    """Get contractor's projects and available bid cards"""
    try:
        # Get contractor's submitted bids (from my-bids endpoint logic)
        projects = []
        bidCards = []

        # For now, return empty arrays as the contractor portal will handle this
        return {
            "projects": projects,
            "bidCards": bidCards,
            "total_projects": len(projects),
            "total_bid_cards": len(bidCards)
        }

    except Exception as e:
        logger.error(f"Error getting contractor projects: {e}")
        return {
            "projects": [],
            "bidCards": [],
            "total_projects": 0,
            "total_bid_cards": 0
        }

@router.get("/contractor/test")
async def test_contractor_endpoint(contractor_id: str = Query(...)):
    """Test endpoint to verify contractor routes are working"""
    return {
        "message": f"Test successful for contractor {contractor_id}",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/contractor/my-bids")
async def get_contractor_bids(contractor_id: str = Query(...), status: Optional[str] = None):
    """
    Get all bids submitted by this contractor
    - Queries bid_cards table for bids in bid_document
    - Includes bid card details
    - Can filter by status
    """
    try:
        return {
            "bids": [],
            "total": 0,
            "contractor_id": contractor_id
        }

        supabase_client = db.client

        # Get all bid cards
        bid_cards_response = supabase_client.table("bid_cards").select("*").execute()

        if not bid_cards_response.data:
            return {
                "bids": [],
                "total": 0
            }

        my_bids = []

        # Search through bid cards for contractor's bids
        for i, bid_card in enumerate(bid_cards_response.data):
            try:
                if not bid_card:
                    continue

                bid_document = bid_card.get("bid_document")
                if not bid_document or not isinstance(bid_document, dict):
                    continue

                submitted_bids = bid_document.get("submitted_bids")
                if not submitted_bids or not isinstance(submitted_bids, list):
                    continue

                # Find contractor's bid in this bid card
                for j, bid in enumerate(submitted_bids):
                    try:
                        if not bid or not isinstance(bid, dict):
                            continue
                        if bid.get("contractor_id") != contractor_id:
                            continue

                        # If status filter applied, check it
                        if status and bid.get("status", "pending") != status:
                            continue

                        # Create simplified bid view
                        bid_view = {
                            "id": f"bid_{bid_card.get('id', 'unknown')}_{contractor_id}",
                            "bid_card_id": bid_card.get("id", ""),
                            "project_title": bid_card.get("title", "Untitled Project"),
                            "bid_amount": bid.get("bid_amount", 0),
                            "timeline_days": bid.get("timeline_days", 0),
                            "message": bid.get("message", ""),
                            "submitted_at": bid.get("submission_time", ""),
                            "status": bid.get("status", "pending")
                        }
                        my_bids.append(bid_view)
                    except Exception as bid_error:
                        logger.error(f"Error processing bid {j} in card {i}: {bid_error}")
                        continue

            except Exception as card_error:
                logger.error(f"Error processing bid card {i}: {card_error}")
                continue

        return {
            "bids": my_bids,
            "total": len(my_bids)
        }

    except Exception as e:
        import traceback
        logger.error(f"Error getting contractor bids: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# Contractor Bid Matching Endpoint
class ContractorMatchingRequest(BaseModel):
    contractor_id: Optional[str] = None
    main_service_type: str = "General Construction"
    specialties: list[str] = []
    zip_codes: list[str] = []
    service_radius_miles: int = 25
    contractor_size_category: str = "small_business"
    years_in_business: Optional[int] = None
    certifications: list[str] = []

@router.post("/matching-projects")
async def get_matching_projects(request: ContractorMatchingRequest):
    """
    Find bid cards that match contractor profile and specialties
    Returns personalized project matches with scores and reasons
    """
    try:
        logger.info(f"Finding matching projects for contractor: {request.contractor_id}")
        
        # Convert request to dict for the matching API
        contractor_data = {
            'contractor_id': request.contractor_id or 'unknown',
            'main_service_type': request.main_service_type,
            'specialties': request.specialties,
            'zip_codes': request.zip_codes,
            'service_radius_miles': request.service_radius_miles,
            'contractor_size_category': request.contractor_size_category,
            'years_in_business': request.years_in_business,
            'certifications': request.certifications
        }
        
        # Get matching projects using the bid matching API
        result = await find_matching_projects(contractor_data)
        
        logger.info(f"Found {result.get('total_matches', 0)} matching projects")
        return result
        
    except Exception as e:
        logger.error(f"Error finding matching projects: {e}")
        return {
            'success': False,
            'error': str(e),
            'matching_projects': [],
            'total_matches': 0
        }

@router.get("/profile-data-by-name/{contractor_name}")
async def get_contractor_profile_by_name(contractor_name: str):
    """
    Get contractor profile data by company name for pre-loading bid card email arrivals
    """
    try:
        logger.info(f"Looking up contractor profile by name: {contractor_name}")
        
        supabase_client = db.client
        
        # Search contractor_leads table for matching company names
        result = supabase_client.table("contractor_leads").select(
            "id, company_name, contact_name, phone, email, website, "
            "specialties, main_service_type, zip_code, service_radius_miles, "
            "contractor_size_category, years_in_business, certifications"
        ).ilike("company_name", f"%{contractor_name}%").limit(1).execute()
        
        if result.data and len(result.data) > 0:
            contractor_data = result.data[0]
            
            # Format the data for frontend use
            formatted_data = {
                'id': contractor_data.get('id'),
                'company_name': contractor_data.get('company_name'),
                'contact_name': contractor_data.get('contact_name'),
                'phone': contractor_data.get('phone'),
                'email': contractor_data.get('email'),
                'website': contractor_data.get('website'),
                'specialties': contractor_data.get('specialties', []),
                'main_service_type': contractor_data.get('main_service_type', ''),
                'zip_codes': [contractor_data.get('zip_code')] if contractor_data.get('zip_code') else [],
                'service_radius_miles': contractor_data.get('service_radius_miles', 25),
                'contractor_size_category': contractor_data.get('contractor_size_category', 'small_business'),
                'years_in_business': contractor_data.get('years_in_business'),
                'certifications': contractor_data.get('certifications', [])
            }
            
            return {
                'found': True,
                'data': formatted_data
            }
        else:
            logger.info(f"No contractor found with name matching: {contractor_name}")
            return {
                'found': False,
                'data': None
            }
            
    except Exception as e:
        logger.error(f"Error looking up contractor by name: {e}")
        return {
            'found': False,
            'data': None,
            'error': str(e)
        }
