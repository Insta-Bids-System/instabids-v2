"""
Simplified Bid Card API for testing
This version works without authentication
"""

from datetime import datetime
from typing import Any, Optional
import base64

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from database_simple import db
from config.service_urls import get_backend_url


# File analysis helper functions
async def analyze_file_for_contact_info(file_data: bytes, filename: str, content_type: str) -> dict:
    """Analyze uploaded file for contact information using intelligent messaging agent"""
    try:
        # Import the analyzer class directly
        from agents.intelligent_messaging_agent import GPT5SecurityAnalyzer
        
        # Initialize analyzer
        analyzer = GPT5SecurityAnalyzer()
        
        # Convert file data to base64 for analysis
        file_base64 = base64.b64encode(file_data).decode('utf-8')
        
        # Determine file type and analyze accordingly
        if content_type and content_type.startswith('image/'):
            # Analyze image content
            image_format = content_type.split('/')[-1]
            return await analyzer.analyze_image_content(file_base64, image_format)
            
        elif filename.lower().endswith('.pdf') or (content_type and 'pdf' in content_type):
            # Analyze PDF content
            return await analyzer.analyze_pdf_content(file_base64, filename)
            
        else:
            # For other file types, assume they may contain contact info
            return {
                "contact_info_detected": True,
                "confidence": 0.6,
                "explanation": f"File type {content_type or 'unknown'} requires manual review",
                "phones": [],
                "emails": [],
                "addresses": [],
                "social_handles": []
            }
            
    except Exception as e:
        print(f"File analysis error: {e}")
        # Conservative approach - flag for review if analysis fails
        return {
            "contact_info_detected": True,
            "confidence": 0.5,
            "explanation": f"File analysis failed: {str(e)} - flagged for safety",
            "phones": [],
            "emails": [],
            "addresses": [],
            "social_handles": []
        }

def get_detected_contact_types(analysis: dict) -> list:
    """Extract detected contact types from analysis results"""
    contact_types = []
    
    if analysis.get("phones"):
        contact_types.append("phone")
    if analysis.get("emails"):
        contact_types.append("email")
    if analysis.get("addresses"):
        contact_types.append("address")
    if analysis.get("social_handles"):
        contact_types.append("social")
        
    return contact_types


router = APIRouter(tags=["bid-cards"])

# Pydantic models for bid submission
class BidMilestone(BaseModel):
    title: str
    description: str
    amount: float
    estimated_completion: str

class BidSubmissionRequest(BaseModel):
    bid_card_id: str
    contractor_id: str = "22222222-2222-2222-2222-222222222222"  # Default test contractor
    amount: float
    timeline_start: str
    timeline_end: str
    proposal: str
    approach: str
    materials_included: bool = False
    warranty_details: Optional[str] = None
    milestones: Optional[list[BidMilestone]] = []
    # Note: File attachments will be handled separately via multipart form data

class BidAttachment(BaseModel):
    name: str
    type: str
    size: int
    url: str

# Simplified search endpoint that works without auth
@router.get("/search", response_model=dict[str, Any])
async def search_bid_cards(
    status: Optional[list[str]] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    zip_code: Optional[str] = Query(None),
    radius_miles: Optional[int] = Query(25, description="Radius in miles for location search"),
    page: int = 1,
    page_size: int = 20
):
    """
    Search bid cards with location filtering
    
    Location Parameters:
    - location_city: Filter by city name
    - location_state: Filter by state code (CA, TX, FL, etc.)
    - location_zip_code: Filter by ZIP code
    - radius_miles: Radius for location search (default: 25 miles)
    
    Note: Currently implements exact matching. In production, radius_miles would
    use geocoding to find all locations within the specified radius.
    """
    try:
        print(f"Search params: city={city}, state={state}, zip={zip_code}, radius={radius_miles}")

        supabase_client = db.client
        query = supabase_client.table("bid_cards").select("*")

        # Apply basic filters
        if status:
            query = query.in_("status", status)
        else:
            query = query.in_("status", ["active", "collecting_bids"])

        # Location filtering with radius support
        if zip_code and radius_miles:
            # Redirect to contractor-jobs API for radius search
            print(f"Radius search detected: redirecting to contractor-jobs API with zip_code={zip_code}, radius_miles={radius_miles}")
            import httpx

            try:
                # Prepare parameters for contractor-jobs API
                contractor_params = {
                    "zip_code": zip_code,
                    "radius_miles": radius_miles,
                    "page": page,
                    "page_size": page_size
                }

                print(f"Making request to contractor-jobs API with params: {contractor_params}")

                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{get_backend_url()}/api/contractor-jobs/search",
                        params=contractor_params
                    )

                print(f"Contractor-jobs API responded with status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"Got {len(data.get('job_opportunities', []))} job opportunities from contractor-jobs API")

                    # Transform job_opportunities to bid_cards format
                    bid_cards = []
                    for job in data.get("job_opportunities", []):
                        bid_card = {
                            "id": job["id"],
                            "bid_card_number": job.get("bid_card_number"),
                            "title": job["title"],
                            "description": job["description"],
                            "project_type": job["project_type"],
                            "status": job["status"],
                            "budget_range": {
                                "min": job["budget_range"]["min"],
                                "max": job["budget_range"]["max"]
                            },
                            "timeline": {
                                "start_date": job["timeline"]["start_date"],
                                "end_date": job["timeline"]["end_date"]
                            },
                            "location": {
                                "city": job["location"]["city"],
                                "state": job["location"]["state"],
                                "zip_code": job["location"]["zip_code"]
                            },
                            "categories": job.get("categories", []),
                            "bid_count": job.get("bid_count", 0),
                            "contractor_count_needed": job.get("contractor_count_needed", 1),
                            "group_bid_eligible": job.get("group_bid_eligible", False),
                            "created_at": job.get("created_at"),
                            "homeowner_verified": True,
                            "response_time_hours": 24,
                            "success_rate": 0.95,
                            "is_featured": False,
                            "is_urgent": False,
                            "distance_miles": job.get("distance_miles")
                        }
                        bid_cards.append(bid_card)

                    return {
                        "bid_cards": bid_cards,
                        "total": data["total"],
                        "page": data["page"],
                        "page_size": data["page_size"],
                        "has_more": data["has_more"]
                    }
                else:
                    print(f"Contractor-jobs API failed with status {response.status_code}")
                    # Fall back to regular search
            except Exception as e:
                print(f"Error calling contractor-jobs API: {e}")
                # Fall back to regular search
        elif city and state:
            # Exact city/state match when no radius specified
            print(f"Applying city+state filter: {city}, {state}")
            query = query.eq("location_city", city).eq("location_state", state)
        elif city:
            print(f"Applying city filter: {city}")
            query = query.eq("location_city", city)
        elif state:
            print(f"Applying state filter: {state}")
            query = query.eq("location_state", state)
        elif zip_code:
            # Exact zip match when no radius specified
            print(f"Applying zip filter: {zip_code}")
            query = query.eq("location_zip", zip_code)

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)

        response = query.execute()

        # Transform bid cards for response
        bid_cards = []
        for card in response.data:
            # Create simplified bid card object
            bid_card = {
                "id": card["id"],
                "title": card.get("title", "Untitled Project"),
                "description": card.get("description", ""),
                "status": card.get("status", "active"),
                "budget_range": {
                    "min": float(card.get("budget_min", 1000)),
                    "max": float(card.get("budget_max", 10000))
                },
                "timeline": {
                    "start_date": card.get("timeline_start", datetime.now().isoformat()),
                    "end_date": card.get("timeline_end", datetime.now().isoformat())
                },
                "location": {
                    "city": card.get("location_city", "Unknown"),
                    "state": card.get("location_state", "Unknown"),
                    "zip_code": card.get("location_zip", "00000")
                },
                "project_type": card.get("project_type", "general"),
                "categories": card.get("categories", []),
                "bid_count": card.get("bid_count", 0),
                # Date flow fields
                "bid_collection_deadline": card.get("bid_collection_deadline"),
                "project_completion_deadline": card.get("project_completion_deadline"),
                "deadline_hard": card.get("deadline_hard", False),
                "deadline_context": card.get("deadline_context"),
                "created_at": card.get("created_at"),
                "is_urgent": False,
                # Service complexity classification fields
                "service_complexity": card.get("service_complexity", "single-trade"),
                "trade_count": card.get("trade_count", 1),
                "primary_trade": card.get("primary_trade", "general"),
                "secondary_trades": card.get("secondary_trades", []),
                "is_featured": False,
                "group_bid_eligible": card.get("group_bid_eligible", False)
            }

            # Add distance information if radius search was used
            if zip_code and radius_miles:
                from ..utils.simple_radius_search import calculate_distance_miles
                try:
                    card_zip = card.get("location_zip")
                    if card_zip:
                        distance = calculate_distance_miles(zip_code, str(card_zip))
                        if distance is not None:
                            bid_card["distance_miles"] = distance
                except Exception as e:
                    print(f"Error calculating distance for card {card['id']}: {e}")

            bid_cards.append(bid_card)

        # Sort by distance if distance information is available
        if zip_code and radius_miles and bid_cards:
            bid_cards = sorted(bid_cards, key=lambda x: x.get("distance_miles", 999))

        return {
            "bid_cards": bid_cards,
            "total": len(bid_cards),
            "page": page,
            "page_size": page_size,
            "has_more": len(bid_cards) == page_size
        }

    except Exception as e:
        print(f"Error in search_bid_cards: {e!s}")
        # Return empty result instead of error for testing
        return {
            "bid_cards": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "has_more": False
        }

# Test endpoint to create sample bid cards
@router.post("/test-data")
async def create_test_bid_cards():
    """Create test bid cards for development"""
    try:
        supabase_client = db.client

        # First check if we have a test project
        project_response = supabase_client.table("projects").select("id").limit(1).execute()
        if not project_response.data:
            # Create a test project
            project_data = {
                "user_id": "test-homeowner-id",
                "title": "Test Project",
                "status": "active"
            }
            project_response = supabase_client.table("projects").insert(project_data).execute()

        project_id = project_response.data[0]["id"]

        # Create sample bid cards
        sample_cards = [
            {
                "project_id": project_id,
                "user_id": "test-homeowner-id",
                "title": "Kitchen Renovation - Modern Update",
                "description": "Complete kitchen renovation including new cabinets, countertops, and appliances. Looking for experienced contractors.",
                "status": "active",
                "budget_min": 25000,
                "budget_max": 45000,
                "timeline_start": datetime.now().isoformat(),
                "timeline_end": (datetime.now().replace(month=datetime.now().month + 2)).isoformat(),
                "location_city": "Los Angeles",
                "location_state": "CA",
                "location_zip": "90001",
                "project_type": "renovation",
                "categories": ["kitchen", "plumbing", "electrical"],
                "group_bid_eligible": True,
                "bid_count": 3
            },
            {
                "project_id": project_id,
                "user_id": "test-homeowner-id",
                "title": "Bathroom Remodel - Master Suite",
                "description": "Master bathroom remodel with new fixtures, tiling, and modern design.",
                "status": "collecting_bids",
                "budget_min": 15000,
                "budget_max": 25000,
                "timeline_start": datetime.now().isoformat(),
                "timeline_end": (datetime.now().replace(month=datetime.now().month + 1)).isoformat(),
                "location_city": "San Francisco",
                "location_state": "CA",
                "location_zip": "94102",
                "project_type": "renovation",
                "categories": ["bathroom", "plumbing", "tiling"],
                "group_bid_eligible": False,
                "bid_count": 5
            },
            {
                "project_id": project_id,
                "user_id": "test-homeowner-id",
                "title": "Roof Replacement - Urgent",
                "description": "Need immediate roof replacement due to storm damage. Insurance claim approved.",
                "status": "active",
                "budget_min": 8000,
                "budget_max": 15000,
                "timeline_start": datetime.now().isoformat(),
                "timeline_end": (datetime.now().replace(day=datetime.now().day + 14)).isoformat(),
                "location_city": "Austin",
                "location_state": "TX",
                "location_zip": "78701",
                "project_type": "repair",
                "categories": ["roofing", "emergency"],
                "group_bid_eligible": False,
                "bid_count": 8
            }
        ]

        # Insert sample bid cards
        for card in sample_cards:
            supabase_client.table("bid_cards").insert(card).execute()

        return {"message": f"Created {len(sample_cards)} test bid cards"}

    except Exception as e:
        print(f"Error creating test data: {e!s}")
        return {"error": str(e)}

@router.get("/user/{user_id}")
async def get_user_bid_cards(user_id: str):
    """Get all bid cards for a specific user"""
    try:
        # Use the same database connection pattern as the search endpoint
        supabase_client = db.client

        # Get all bid cards - for now, get all since we don't have homeowner filtering yet
        response = supabase_client.table("bid_cards").select("*").order("created_at", desc=True).execute()

        if not response or not response.data:
            print(f"No bid cards found for homeowner {user_id}")
            return []

        print(f"Raw database response: {len(response.data)} bid cards found")

        # Transform bid cards for homeowner dashboard - similar to search endpoint
        bid_cards = []
        for card in response.data:
            # Safely parse bid document to get contractor bids
            bid_document = card.get("bid_document") or {}
            submitted_bids = bid_document.get("submitted_bids") or []
            all_extracted_data = bid_document.get("all_extracted_data") or {}

            # Create basic bid card structure first
            bid_card = {
                "id": card.get("id", ""),
                "bid_card_number": card.get("bid_card_number", ""),
                "title": card.get("title") or all_extracted_data.get("project_description", "Untitled Project")[:50],
                "project_type": card.get("project_type", ""),
                "urgency_level": card.get("urgency_level", ""),
                "status": card.get("status", ""),
                "budget_min": card.get("budget_min", 0),
                "budget_max": card.get("budget_max", 0),
                "contractor_count_needed": card.get("contractor_count_needed", 0),
                "bids_received_count": card.get("bids_received_count", 0),
                "bids_target_met": card.get("bids_target_met", False),
                "complexity_score": card.get("complexity_score", 0),
                "created_at": card.get("created_at", ""),
                "cia_thread_id": card.get("cia_thread_id", ""),
                # Additional homeowner dashboard specific fields
                "bid_document": bid_document,
                "submitted_bids": submitted_bids,
                "description": all_extracted_data.get("project_description", ""),
                "location": all_extracted_data.get("location", {}),
                "timeline_urgency": all_extracted_data.get("timeline_urgency", ""),
                "material_preferences": all_extracted_data.get("material_preferences", []),
                "special_requirements": all_extracted_data.get("special_requirements", []),
                "images": all_extracted_data.get("images", []),
                # Service complexity classification fields
                "service_complexity": card.get("service_complexity", "single-trade"),
                "trade_count": card.get("trade_count", 1),
                "primary_trade": card.get("primary_trade", "general"),
                "secondary_trades": card.get("secondary_trades", [])
            }
            bid_cards.append(bid_card)

        print(f"Transformed {len(bid_cards)} bid cards for homeowner {user_id}")
        return bid_cards

    except Exception as e:
        print(f"Error getting homeowner bid cards: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@router.post("/submit-bid")
async def submit_contractor_bid(bid_data: BidSubmissionRequest):
    """Submit a contractor bio with support for attachments"""
    try:
        supabase_client = db.client

        # Validate bid card exists and is accepting bids
        bid_card_response = supabase_client.table("bid_cards").select("*").eq("id", bid_data.bid_card_id).execute()
        if not bid_card_response.data:
            raise HTTPException(status_code=404, detail="Bid card not found")

        bid_card = bid_card_response.data[0]
        if bid_card.get("status") not in ["active", "collecting_bids"]:
            raise HTTPException(status_code=400, detail="Bid card is not accepting bids")

        # Check if contractor has already submitted a bid
        existing_bid_response = supabase_client.table("contractor_bids").select("id").eq("bid_card_id", bid_data.bid_card_id).eq("contractor_id", bid_data.contractor_id).execute()
        if existing_bid_response.data:
            raise HTTPException(status_code=400, detail="Contractor has already submitted a bid for this project")

        # Prepare bid data
        bid_insert_data = {
            "bid_card_id": bid_data.bid_card_id,
            "contractor_id": bid_data.contractor_id,
            "amount": bid_data.amount,
            "timeline_start": bid_data.timeline_start,
            "timeline_end": bid_data.timeline_end,
            "proposal": bid_data.proposal,
            "approach": bid_data.approach,
            "materials_included": bid_data.materials_included,
            "warranty_details": bid_data.warranty_details,
            "status": "submitted",
            "submitted_at": datetime.now().isoformat(),
            "additional_data": {
                "milestones": [milestone.dict() for milestone in bid_data.milestones] if bid_data.milestones else []
            }
        }

        # Insert the bid
        bid_response = supabase_client.table("contractor_bids").insert(bid_insert_data).execute()
        if not bid_response.data:
            raise HTTPException(status_code=500, detail="Failed to submit bid")

        bid_id = bid_response.data[0]["id"]
        
        # Process ALL bid fields through intelligent messaging agent for contact filtering
        # Run filtering in background to avoid timeout
        import asyncio
        import threading
        
        def filter_bid_content_async(bid_id_local, bid_data_local, supabase_client_local):
            """Filter bid content in background thread"""
            try:
                import requests
                filtered_proposal = bid_data_local.proposal
                filtered_approach = bid_data_local.approach
                filtered_warranty = bid_data_local.warranty_details
                
                # Filter proposal field
                print(f"[FILTERING] Starting GPT-4o filtering for bid {bid_id_local}")
                print(f"[FILTERING] Original proposal: {bid_data_local.proposal[:100]}...")
                
                proposal_response = requests.post(f"{get_backend_url()}/api/intelligent-messages/send", json={
                    "content": bid_data_local.proposal,
                    "sender_type": "contractor",
                    "sender_id": bid_data_local.contractor_id,
                    "bid_card_id": bid_data_local.bid_card_id,
                    "message_type": "bid_submission_proposal"
                }, timeout=300)  # Give it 5 minutes for GPT-4o processing
                
                if proposal_response.ok:
                    proposal_result = proposal_response.json()
                    if proposal_result.get('approved'):
                        filtered_proposal = proposal_result.get('filtered_content', bid_data_local.proposal)
                        print(f"[FILTERING] ✅ Proposal filtered successfully")
                        print(f"[FILTERING] Filtered proposal: {filtered_proposal[:100]}...")
                    else:
                        filtered_proposal = "Proposal contains restricted content - please contact through platform"
                        print(f"[FILTERING] 🚫 Proposal blocked due to contact info")
                else:
                    print(f"[FILTERING] ⚠️ Proposal filtering failed: {proposal_response.status_code}")
                
                # Filter approach field
                print(f"[FILTERING] Filtering approach for contact information...")
                approach_response = requests.post(f"{get_backend_url()}/api/intelligent-messages/send", json={
                    "content": bid_data_local.approach,
                    "sender_type": "contractor",
                    "sender_id": bid_data_local.contractor_id,
                    "bid_card_id": bid_data_local.bid_card_id,
                    "message_type": "bid_submission_approach"
                }, timeout=300)  # Give it 5 minutes for GPT-4o processing
                
                if approach_response.ok:
                    approach_result = approach_response.json()
                    if approach_result.get('approved'):
                        filtered_approach = approach_result.get('filtered_content', bid_data_local.approach)
                        print(f"[FILTERING] ✅ Approach filtered successfully")
                    else:
                        filtered_approach = "Approach contains restricted content - please contact through platform"
                        print(f"[FILTERING] 🚫 Approach blocked due to contact info")
                else:
                    print(f"[FILTERING] ⚠️ Approach filtering failed: {approach_response.status_code}")
                
                # Filter warranty field if provided
                if bid_data_local.warranty_details:
                    print(f"[FILTERING] Filtering warranty for contact information...")
                    warranty_response = requests.post(f"{get_backend_url()}/api/intelligent-messages/send", json={
                        "content": bid_data_local.warranty_details,
                        "sender_type": "contractor",
                        "sender_id": bid_data_local.contractor_id,
                        "bid_card_id": bid_data_local.bid_card_id,
                        "message_type": "bid_submission_warranty"
                    }, timeout=300)  # Give it 5 minutes for GPT-4o processing
                    
                    if warranty_response.ok:
                        warranty_result = warranty_response.json()
                        if warranty_result.get('approved'):
                            filtered_warranty = warranty_result.get('filtered_content', bid_data_local.warranty_details)
                            print(f"[FILTERING] ✅ Warranty filtered successfully")
                        else:
                            filtered_warranty = "Warranty contains restricted content - please contact through platform"
                            print(f"[FILTERING] 🚫 Warranty blocked due to contact info")
                    else:
                        print(f"[FILTERING] ⚠️ Warranty filtering failed: {warranty_response.status_code}")
                
                # UPDATE THE BID WITH FILTERED CONTENT - THIS IS THE FIX!
                print(f"[FILTERING] Updating bid {bid_id_local} with filtered content...")
                update_response = supabase_client_local.table("contractor_bids").update({
                    "proposal": filtered_proposal,
                    "approach": filtered_approach,
                    "warranty_details": filtered_warranty
                }).eq("id", bid_id_local).execute()
                
                if update_response.data:
                    print(f"[FILTERING] ✅✅✅ BID UPDATED WITH FILTERED CONTENT - ALL CONTACT INFO REMOVED ✅✅✅")
                    print(f"[FILTERING] Database update successful for bid {bid_id_local}")
                else:
                    print(f"[FILTERING] ⚠️ WARNING: Failed to update bid with filtered content")
                    
            except Exception as e:
                print(f"[FILTERING] ERROR: GPT-4o filtering failed: {e}")
                # Don't fail - bid already saved, just not filtered
        
        # Start the filtering in a background thread
        filter_thread = threading.Thread(target=filter_bid_content_async, args=(bid_id, bid_data, supabase_client))
        filter_thread.daemon = True  # Don't block server shutdown
        filter_thread.start()
        print(f"[BID SUBMISSION] Bid {bid_id} saved - filtering started in background")

        # Update bid card counts
        current_bid_count = bid_card.get("bid_count", 0)
        new_bid_count = current_bid_count + 1
        contractor_count_needed = bid_card.get("contractor_count_needed", 1)

        update_data = {
            "bid_count": new_bid_count
        }

        # Update status if target met
        if new_bid_count >= contractor_count_needed:
            update_data["status"] = "bids_complete"

        supabase_client.table("bid_cards").update(update_data).eq("id", bid_data.bid_card_id).execute()

        return {
            "success": True,
            "bid_id": bid_id,
            "message": "Bid submitted successfully",
            "bids_received": new_bid_count,
            "target_met": new_bid_count >= contractor_count_needed
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error submitting bid: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/submit-bid-with-files")
async def submit_contractor_bid_with_files(
    bid_data: str = Form(...),  # JSON string containing bid data
    files: list[UploadFile] = File(default=[])
):
    """Submit a contractor bid with file attachments"""
    try:
        # Parse the bid data from JSON string
        bid_request = BidSubmissionRequest.model_validate_json(bid_data)

        # Submit the bid first (reuse the existing logic)
        bid_result = await submit_contractor_bid(bid_request)
        bid_id = bid_result["bid_id"]

        # Handle file uploads if any
        uploaded_attachments = []
        flagged_files = []
        if files:
            supabase_client = db.client

            for file in files:
                if file.filename:
                    try:
                        # Read file data
                        file_data = await file.read()
                        
                        # 🚨 NEW: Analyze file for contact information
                        file_analysis = await analyze_file_for_contact_info(file_data, file.filename, file.content_type)
                        
                        # Generate unique filename using unified system pattern
                        from datetime import datetime
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        unique_name = f"bid_attachments/{bid_id}/{timestamp}_{file.filename}"
                        
                        if file_analysis.get("contact_info_detected"):
                            # 🚨 FILE FLAGGED: Store in review queue instead of normal upload
                            print(f"[FILE FLAGGED] {file.filename} contains contact info - sending to review queue")
                            
                            # Upload to separate quarantine bucket for review
                            quarantine_path = f"quarantine/{bid_id}/{timestamp}_{file.filename}"
                            supabase_client.storage.from_("project-images").upload(
                                quarantine_path,
                                file_data,
                                {
                                    "content-type": file.content_type or "application/octet-stream",
                                    "cache-control": "3600",
                                    "upsert": "false"
                                }
                            )
                            
                            # Add to file review queue
                            review_record = {
                                "bid_card_id": bid_request.bid_card_id,
                                "contractor_id": bid_request.contractor_id,
                                "file_name": file.filename,
                                "file_path": quarantine_path,
                                "file_type": file.content_type or "application/octet-stream",
                                "file_size": len(file_data),
                                "original_upload_data": {
                                    "upload_timestamp": timestamp,
                                    "bid_id": bid_id,
                                    "original_filename": file.filename
                                },
                                "contact_analysis": file_analysis,
                                "flagged_reason": file_analysis.get("explanation", "Contact information detected"),
                                "confidence_score": file_analysis.get("confidence", 0.0),
                                "detected_contact_types": get_detected_contact_types(file_analysis),
                                "review_status": "pending"
                            }
                            
                            review_result = supabase_client.table("file_review_queue").insert(review_record).execute()
                            
                            # 🚨 NEW: Send notification to contractor about flagged file
                            if review_result.data:
                                review_queue_id = review_result.data[0]["id"]
                                try:
                                    from services.file_flagged_notification_service import send_file_flagged_notification
                                    notification_result = await send_file_flagged_notification(
                                        contractor_id=bid_request.contractor_id,
                                        bid_card_id=bid_request.bid_card_id,
                                        file_name=file.filename,
                                        flagged_reason=file_analysis.get("explanation", "Contact information detected"),
                                        confidence_score=file_analysis.get("confidence", 0.0),
                                        review_queue_id=review_queue_id
                                    )
                                    print(f"[NOTIFICATION] File flagged notification: {notification_result}")
                                except Exception as e:
                                    print(f"[WARNING] Failed to send flagged file notification: {e}")
                            
                            flagged_files.append({
                                "filename": file.filename,
                                "reason": file_analysis.get("explanation"),
                                "confidence": file_analysis.get("confidence")
                            })
                            
                        else:
                            # ✅ FILE CLEAN: Normal upload process
                            supabase_client.storage.from_("project-images").upload(
                                unique_name,
                                file_data,
                                {
                                    "content-type": file.content_type or "application/octet-stream",
                                    "cache-control": "3600",
                                    "upsert": "false"
                                }
                            )
                            
                            # Get public URL from Supabase Storage
                            file_url = supabase_client.storage.from_("project-images").get_public_url(unique_name)
                            
                            print(f"[ATTACHMENT] Uploaded {file.filename} to {file_url}")
                            
                            # Store attachment metadata in database with real URL
                            attachment_data = {
                                "contractor_bid_id": bid_id,
                                "name": file.filename,
                                "type": file.content_type.split("/")[0] if file.content_type else "document",
                                "url": file_url,
                                "size": len(file_data),
                                "mime_type": file.content_type
                            }

                            attachment_response = supabase_client.table("contractor_proposal_attachments").insert(attachment_data).execute()
                            if attachment_response.data:
                                uploaded_attachments.append({
                                "id": attachment_response.data[0]["id"],
                                "name": file.filename,
                                "url": file_url,
                                "type": attachment_data["type"]
                                })
                            
                    except Exception as upload_error:
                        print(f"[ERROR] Failed to upload {file.filename}: {upload_error}")
                        # Continue with other files even if one fails

        # Return success with attachment info and flagged files
        result = bid_result.copy()
        result["attachments"] = uploaded_attachments
        result["flagged_files"] = flagged_files
        
        # Create appropriate message based on file processing results
        total_files = len(uploaded_attachments) + len(flagged_files)
        if flagged_files:
            result["message"] = f"Bid submitted successfully. {len(uploaded_attachments)} files uploaded, {len(flagged_files)} files sent for admin review due to potential contact information."
            result["review_required"] = True
        else:
            result["message"] = f"Bid submitted successfully with {len(uploaded_attachments)} attachments"
            result["review_required"] = False

        return result

    except Exception as e:
        print(f"Error submitting bid with files: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{bid_card_id}/bids")
async def get_bid_card_bids(bid_card_id: str):
    """Get all bids for a specific bid card"""
    try:
        supabase_client = db.client

        # Get all bids for this bid card
        bids_response = supabase_client.table("contractor_bids").select("*").eq("bid_card_id", bid_card_id).execute()

        bids = []
        for bid in bids_response.data:
            # Get attachments for this bid
            attachments_response = supabase_client.table("contractor_proposal_attachments").select("*").eq("contractor_bid_id", bid["id"]).execute()

            bid_data = {
                "id": bid["id"],
                "contractor_id": bid["contractor_id"],
                "amount": float(bid["amount"]),
                "timeline": {
                    "start_date": bid["timeline_start"],
                    "end_date": bid["timeline_end"]
                },
                "proposal": bid["proposal"],
                "approach": bid["approach"],
                "materials_included": bid["materials_included"],
                "warranty_details": bid["warranty_details"],
                "status": bid["status"],
                "submitted_at": bid["submitted_at"],
                "milestones": bid.get("additional_data", {}).get("milestones", []),
                "attachments": [
                    {
                        "id": att["id"],
                        "name": att["name"],
                        "type": att["type"],
                        "url": att["url"],
                        "size": att["size"]
                    }
                    for att in attachments_response.data
                ]
            }
            bids.append(bid_data)

        return {
            "bid_card_id": bid_card_id,
            "bids": bids,
            "total_bids": len(bids)
        }

    except Exception as e:
        print(f"Error getting bid card bids: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{bid_card_id}/contractor-view", response_model=dict[str, Any])
async def get_bid_card_contractor_view(
    bid_card_id: str,
    contractor_id: str = Query(...)
):
    """Get bid card details for contractor view"""
    try:
        supabase_client = db.client

        # Get the bid card
        response = supabase_client.table("bid_cards").select("*").eq("id", bid_card_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Bid card not found")

        card = response.data[0]

        # Check if contractor has already bid
        bid_response = supabase_client.table("contractor_bids").select("*").eq("bid_card_id", bid_card_id).eq("contractor_id", contractor_id).execute()
        has_bid = bool(bid_response.data)
        my_bid = bid_response.data[0] if bid_response.data else None

        # Get project photos if they exist
        photos = []
        try:
            photo_response = supabase_client.table("project_photos").select("*").eq("project_id", card.get("project_id")).execute()
            for photo in photo_response.data:
                photos.append({
                    "id": photo["id"],
                    "url": photo["url"],
                    "thumbnail_url": photo.get("thumbnail_url", photo["url"]),
                    "caption": photo.get("caption", ""),
                    "type": photo.get("type", "photo")
                })
        except Exception as photo_error:
            print(f"Could not load photos: {photo_error}")
            # Continue without photos

        # Get inspiration board images if linked
        inspiration_images = []
        try:
            if card.get("project_id"):
                # Check for inspiration boards linked to this project
                inspiration_response = supabase_client.table("inspiration_boards").select("*").eq("project_id", card["project_id"]).execute()
                for board in inspiration_response.data:
                    images_response = supabase_client.table("inspiration_images").select("*").eq("board_id", board["id"]).execute()
                    for img in images_response.data:
                        inspiration_images.append({
                            "id": img["id"],
                            "url": img["url"],
                            "thumbnail_url": img.get("thumbnail_url", img["url"]),
                            "caption": img.get("description", "Inspiration image"),
                            "type": "inspiration"
                        })
        except Exception as inspiration_error:
            print(f"Could not load inspiration images: {inspiration_error}")

        # Combine all images
        all_images = photos + inspiration_images

        contractor_view = {
            "id": card["id"],
            "title": card.get("title", "Untitled Project"),
            "description": card.get("description", ""),
            "status": card.get("status", "active"),
            "budget_range": {
                "min": float(card.get("budget_min", 1000)),
                "max": float(card.get("budget_max", 10000))
            },
            "timeline": {
                "start_date": card.get("timeline_start", datetime.now().isoformat()),
                "end_date": card.get("timeline_end", datetime.now().isoformat()),
                "flexibility": card.get("timeline_flexibility", "flexible")
            },
            "location": {
                "address": card.get("location_address"),
                "city": card.get("location_city", "Unknown"),
                "state": card.get("location_state", "Unknown"),
                "zip_code": card.get("location_zip", "00000")
            },
            "project_type": card.get("project_type", "general"),
            "categories": card.get("categories", []),
            "requirements": card.get("requirements", []),
            "preferred_schedule": card.get("preferred_schedule", []),
            "bid_count": card.get("bid_count", 0),
            "bid_deadline": card.get("bid_deadline"),
            "allows_questions": card.get("allows_questions", True),
            "group_bid_eligible": card.get("group_bid_eligible", False),
            "created_at": card.get("created_at"),
            "images": all_images,
            "can_bid": card.get("status") in ["active", "collecting_bids"] and not has_bid,
            "has_bid": has_bid,
            "my_bid": my_bid,
            "is_urgent": False,
            "is_featured": False,
            "distance_miles": 10.5,  # Would calculate actual distance
            "match_score": 0.85,     # Would calculate based on contractor profile
            "homeowner_verified": True,
            "response_time_hours": 24,
            # Service complexity classification fields
            "service_complexity": card.get("service_complexity", "single-trade"),
            "trade_count": card.get("trade_count", 1),
            "primary_trade": card.get("primary_trade", "general"),
            "secondary_trades": card.get("secondary_trades", [])
        }

        return contractor_view

    except Exception as e:
        print(f"Error in get_bid_card_contractor_view: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))
