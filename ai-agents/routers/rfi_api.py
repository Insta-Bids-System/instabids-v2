"""
Request for Information (RFI) API
Allows contractors to request additional information from homeowners
Triggers notifications and agent-assisted information gathering
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from enum import Enum
from database_simple import db
from config.service_urls import get_backend_url

logger = logging.getLogger(__name__)
router = APIRouter()


# Enums matching database
class RFIRequestType(str, Enum):
    PICTURES = "pictures"
    MEASUREMENTS = "measurements"
    CLARIFICATION = "clarification"
    TECHNICAL = "technical"
    ACCESS = "access"


class RFIPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class RFIStatus(str, Enum):
    PENDING = "pending"
    HOMEOWNER_NOTIFIED = "homeowner_notified"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RFIResponseType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    MEASUREMENT = "measurement"
    DOCUMENT = "document"


# Request/Response models
class RFISubmissionRequest(BaseModel):
    bid_card_id: str
    contractor_id: str
    request_type: RFIRequestType
    specific_items: List[str] = Field(default_factory=list)
    priority: RFIPriority = RFIPriority.MEDIUM
    custom_message: Optional[str] = None


class RFIResponse(BaseModel):
    rfi_request_id: str
    response_type: RFIResponseType
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_by: str
    created_by_type: str = "homeowner"


class RFICancellation(BaseModel):
    reason: Optional[str] = None


# Helper functions
async def get_bid_card_info(bid_card_id: str) -> Dict[str, Any]:
    """Get bid card information including homeowner details"""
    try:
        # First get bid card
        result = db.client.table("bid_cards").select(
            "*, homeowner:homeowners(id, user_id, address, preferences)"
        ).eq("id", bid_card_id).single().execute()
        
        if not result.data:
            # Try without the homeowner join in case it's causing issues
            result = db.client.table("bid_cards").select("*").eq("id", bid_card_id).single().execute()
        
        return result.data if result.data else None
    except Exception as e:
        logger.error(f"Error getting bid card info: {e}")
        # Try simpler query
        try:
            result = db.client.table("bid_cards").select("*").eq("id", bid_card_id).single().execute()
            return result.data if result.data else None
        except:
            return None


async def get_contractor_info(contractor_id: str) -> Dict[str, Any]:
    """Get contractor information"""
    try:
        result = db.client.table("contractors").select(
            "id, company_name, contact_name, email, phone"
        ).eq("id", contractor_id).single().execute()
        return result.data if result.data else None
    except Exception as e:
        logger.error(f"Error getting contractor info: {e}")
        return None


async def create_homeowner_notification(
    user_id: str,
    rfi_id: str,
    contractor_name: str,
    request_type: str,
    specific_items: List[str],
    bid_card_id: str
) -> bool:
    """Create notification for homeowner about RFI - routes to CIA agent"""
    try:
        # Format the notification message
        items_text = "\n".join(f"• {item}" for item in specific_items[:5])
        if len(specific_items) > 5:
            items_text += f"\n• ... and {len(specific_items) - 5} more items"
        
        notification = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "notification_type": "rfi_request",
            "title": f"📋 Information Request from {contractor_name}",
            "message": f"A contractor needs additional {request_type} for your project:\n\n{items_text}\n\nClick to chat with your assistant who will help you gather this information.",
            "action_url": f"/homeowner/chat?rfi={rfi_id}",  # Route to CIA chat with RFI context
            "is_read": False,
            "is_archived": False,
            "channels": {
                "email": True,
                "in_app": True,
                "sms": request_type == "urgent"
            },
            "metadata": {
                "rfi_id": rfi_id,
                "contractor_name": contractor_name,
                "request_type": request_type,
                "bid_card_id": bid_card_id,
                "cia_routing": True  # Flag for frontend to route to CIA with RFI context
            },
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = db.client.table("notifications").insert(notification).execute()
        
        if result.data:
            logger.info(f"Created homeowner notification for RFI {rfi_id}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error creating homeowner notification: {e}")
        return False


# API Endpoints
@router.post("/api/rfi/submit")
async def submit_rfi(request: RFISubmissionRequest):
    """Submit a new Request for Information"""
    try:
        # Validate bid card exists and get homeowner info
        bid_card = await get_bid_card_info(request.bid_card_id)
        if not bid_card:
            raise HTTPException(status_code=404, detail="Bid card not found")
        
        # Get contractor info
        contractor = await get_contractor_info(request.contractor_id)
        if not contractor:
            raise HTTPException(status_code=404, detail="Contractor not found")
        
        # Create RFI request
        rfi_id = str(uuid.uuid4())
        rfi_request = {
            "id": rfi_id,
            "bid_card_id": request.bid_card_id,
            "contractor_id": request.contractor_id,
            "request_type": request.request_type.value,
            "specific_items": request.specific_items,
            "priority": request.priority.value,
            "status": RFIStatus.PENDING.value,
            "custom_message": request.custom_message,
            "metadata": {
                "contractor_name": contractor.get("company_name", "Unknown Contractor"),
                "project_type": bid_card.get("project_type", "General")
            }
        }
        
        result = db.client.table("rfi_requests").insert(rfi_request).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create RFI request")
        
        # Create homeowner notification
        homeowner = bid_card.get("homeowner", {})
        if homeowner and homeowner.get("id"):
            notification_sent = await create_homeowner_notification(
                user_id=homeowner["id"],
                rfi_id=rfi_id,
                contractor_name=contractor.get("company_name", "Contractor"),
                request_type=request.request_type.value,
                specific_items=request.specific_items,
                bid_card_id=request.bid_card_id
            )
            
            # Update RFI status if notification was sent
            if notification_sent:
                db.client.table("rfi_requests").update({
                    "status": RFIStatus.HOMEOWNER_NOTIFIED.value,
                    "notified_at": datetime.utcnow().isoformat()
                }).eq("id", rfi_id).execute()
        
        # Send real-time notification if WebSocket connected
        try:
            from routers.homeowner_websocket_routes import notify_homeowner_realtime
            await notify_homeowner_realtime(
                user_id=homeowner.get("id"),
                notification_type="rfi_request",
                data={
                    "rfi_id": rfi_id,
                    "contractor_name": contractor.get("company_name"),
                    "request_type": request.request_type.value
                }
            )
        except Exception as ws_error:
            logger.warning(f"Could not send WebSocket notification: {ws_error}")
        
        return {
            "success": True,
            "rfi_id": rfi_id,
            "status": result.data[0]["status"],
            "message": "Request for information submitted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting RFI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/rfi/templates/{job_type}")
async def get_rfi_templates(job_type: str):
    """Get RFI templates for a specific job type"""
    try:
        # Get templates for the job type
        result = db.client.table("rfi_templates").select("*").eq("job_type", job_type).execute()
        
        # Also get general templates
        general_result = db.client.table("rfi_templates").select("*").eq("job_type", "general_contractor").execute()
        
        templates = result.data if result.data else []
        general_templates = general_result.data if general_result.data else []
        
        # Increment usage count
        for template in templates:
            db.client.table("rfi_templates").update({
                "usage_count": template.get("usage_count", 0) + 1
            }).eq("id", template["id"]).execute()
        
        return {
            "success": True,
            "job_type": job_type,
            "templates": templates,
            "general_templates": general_templates
        }
        
    except Exception as e:
        logger.error(f"Error getting RFI templates: {e}")
        return {
            "success": False,
            "error": str(e),
            "templates": [],
            "general_templates": []
        }


@router.get("/api/rfi/contractor/{contractor_id}")
async def get_contractor_rfis(contractor_id: str, status: Optional[str] = None):
    """Get all RFI requests submitted by a contractor"""
    try:
        query = db.client.table("rfi_requests").select(
            "*, bid_card:bid_cards(id, project_type, address, status)"
        ).eq("contractor_id", contractor_id).order("created_at", desc=True)
        
        if status:
            query = query.eq("status", status)
        
        result = query.execute()
        
        return {
            "success": True,
            "rfi_requests": result.data if result.data else [],
            "total": len(result.data) if result.data else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting contractor RFIs: {e}")
        return {
            "success": False,
            "error": str(e),
            "rfi_requests": []
        }


@router.get("/api/rfi/{rfi_id}")
async def get_rfi_details(rfi_id: str):
    """Get detailed information about an RFI including responses"""
    try:
        # Get RFI request with bid card and contractor info
        rfi_result = db.client.table("rfi_requests").select(
            "*, bid_card:bid_cards(*, homeowner:homeowners(id, name, email)), contractor:contractors(id, company_name, contact_name)"
        ).eq("id", rfi_id).single().execute()
        
        if not rfi_result.data:
            raise HTTPException(status_code=404, detail="RFI not found")
        
        # Get responses
        responses_result = db.client.table("rfi_responses").select("*").eq("rfi_request_id", rfi_id).order("created_at").execute()
        
        return {
            "success": True,
            "rfi": rfi_result.data,
            "responses": responses_result.data if responses_result.data else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting RFI details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/rfi/{rfi_id}/cancel")
async def cancel_rfi(rfi_id: str, cancellation: RFICancellation):
    """Cancel an RFI request"""
    try:
        # Check if RFI exists and is not already completed
        rfi_result = db.client.table("rfi_requests").select("*").eq("id", rfi_id).single().execute()
        
        if not rfi_result.data:
            raise HTTPException(status_code=404, detail="RFI not found")
        
        if rfi_result.data["status"] in [RFIStatus.COMPLETED.value, RFIStatus.CANCELLED.value]:
            raise HTTPException(status_code=400, detail=f"Cannot cancel RFI with status: {rfi_result.data['status']}")
        
        # Update RFI status
        update_result = db.client.table("rfi_requests").update({
            "status": RFIStatus.CANCELLED.value,
            "cancelled_at": datetime.utcnow().isoformat(),
            "cancelled_reason": cancellation.reason
        }).eq("id", rfi_id).execute()
        
        if not update_result.data:
            raise HTTPException(status_code=500, detail="Failed to cancel RFI")
        
        # TODO: Notify homeowner of cancellation if they were already notified
        
        return {
            "success": True,
            "message": "RFI request cancelled successfully",
            "rfi_id": rfi_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling RFI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Homeowner endpoints
@router.get("/api/rfi/homeowner/{user_id}")
async def get_homeowner_rfis(user_id: str, status: Optional[str] = None):
    """Get all RFI requests for a homeowner's bid cards"""
    try:
        # First get all bid cards for the homeowner
        bid_cards_result = db.client.table("bid_cards").select("id").eq("user_id", user_id).execute()
        
        if not bid_cards_result.data:
            return {
                "success": True,
                "rfi_requests": [],
                "total": 0
            }
        
        bid_card_ids = [bc["id"] for bc in bid_cards_result.data]
        
        # Get RFI requests for those bid cards with contractor info
        query = db.client.table("rfi_requests").select(
            "*, bid_card:bid_cards(id, project_type, location_address)"
        ).in_("bid_card_id", bid_card_ids).order("created_at", desc=True)
        
        if status:
            query = query.eq("status", status)
        
        result = query.execute()
        
        return {
            "success": True,
            "rfi_requests": result.data if result.data else [],
            "total": len(result.data) if result.data else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting homeowner RFIs: {e}")
        return {
            "success": False,
            "error": str(e),
            "rfi_requests": []
        }


@router.post("/api/rfi/{rfi_id}/acknowledge")
async def acknowledge_rfi(rfi_id: str):
    """Mark RFI as acknowledged by homeowner"""
    try:
        # Update status to in_progress
        result = db.client.table("rfi_requests").update({
            "status": RFIStatus.IN_PROGRESS.value,
            "responded_at": datetime.utcnow().isoformat()
        }).eq("id", rfi_id).eq("status", RFIStatus.HOMEOWNER_NOTIFIED.value).execute()
        
        if not result.data:
            return {
                "success": False,
                "message": "RFI not found or already acknowledged"
            }
        
        return {
            "success": True,
            "message": "RFI acknowledged",
            "rfi_id": rfi_id
        }
        
    except Exception as e:
        logger.error(f"Error acknowledging RFI: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/api/rfi/{rfi_id}/response")
async def submit_rfi_response(rfi_id: str, response: RFIResponse):
    """Submit a response to an RFI"""
    try:
        # Verify RFI exists
        rfi_result = db.client.table("rfi_requests").select("*").eq("id", rfi_id).single().execute()
        
        if not rfi_result.data:
            raise HTTPException(status_code=404, detail="RFI not found")
        
        # Create response
        response_data = {
            "id": str(uuid.uuid4()),
            "rfi_request_id": rfi_id,
            "response_type": response.response_type.value,
            "content": response.content,
            "metadata": response.metadata,
            "created_by": response.created_by,
            "created_by_type": response.created_by_type
        }
        
        result = db.client.table("rfi_responses").insert(response_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create response")
        
        # Check if all items have been addressed to mark as completed
        # This is a simplified check - in production would be more sophisticated
        responses_count = db.client.table("rfi_responses").select("id", count="exact").eq("rfi_request_id", rfi_id).execute()
        specific_items_count = len(rfi_result.data.get("specific_items", []))
        
        if responses_count.count >= specific_items_count:
            # Mark RFI as completed
            db.client.table("rfi_requests").update({
                "status": RFIStatus.COMPLETED.value,
                "completed_at": datetime.utcnow().isoformat()
            }).eq("id", rfi_id).execute()
            
            # Notify contractor of completion
            await notify_contractor_of_rfi_completion(rfi_result.data)
        
        return {
            "success": True,
            "response_id": result.data[0]["id"],
            "message": "Response submitted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting RFI response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def notify_contractor_of_rfi_completion(rfi_data: Dict[str, Any]):
    """Notify contractor that their RFI has been completed"""
    try:
        contractor_id = rfi_data["contractor_id"]
        
        # Create notification
        notification = {
            "id": str(uuid.uuid4()),
            "user_id": contractor_id,
            "notification_type": "rfi_completed",
            "title": "✅ Information Request Completed",
            "message": f"The homeowner has provided the information you requested for the {rfi_data.get('request_type', 'project')}.",
            "action_url": f"/contractor/rfi/{rfi_data['id']}",
            "is_read": False,
            "metadata": {
                "rfi_id": rfi_data["id"],
                "bid_card_id": rfi_data["bid_card_id"]
            },
            "created_at": datetime.utcnow().isoformat()
        }
        
        db.client.table("notifications").insert(notification).execute()
        
        # Send WebSocket notification if connected
        try:
            from routers.contractor_websocket_routes import notify_contractor_realtime
            await notify_contractor_realtime(
                contractor_id=contractor_id,
                notification=notification
            )
        except Exception as ws_error:
            logger.warning(f"Could not send WebSocket notification: {ws_error}")
            
    except Exception as e:
        logger.error(f"Error notifying contractor of RFI completion: {e}")


@router.get("/api/rfi/{rfi_id}/context")
async def get_rfi_context_for_agent(rfi_id: str):
    """Get RFI context for CIA agent to help homeowner gather information"""
    try:
        # Get RFI details with bid card
        rfi_result = db.client.table("rfi_requests").select(
            "*, bid_card:bid_cards(*)"
        ).eq("id", rfi_id).single().execute()
        
        if not rfi_result.data:
            raise HTTPException(status_code=404, detail="RFI not found")
        
        rfi_data = rfi_result.data
        
        # Get contractor info separately
        contractor_id = rfi_data.get("contractor_id")
        contractor_data = {}
        if contractor_id:
            contractor_result = db.client.table("contractors").select(
                "company_name, specialties"
            ).eq("id", contractor_id).single().execute()
            if contractor_result.data:
                contractor_data = contractor_result.data
        
        # Format context for agent
        context = {
            "rfi_id": rfi_id,
            "contractor_name": contractor_data.get("company_name", rfi_data.get("metadata", {}).get("contractor_name", "Contractor")),
            "request_type": rfi_data["request_type"],
            "specific_items": rfi_data["specific_items"],
            "priority": rfi_data["priority"],
            "custom_message": rfi_data.get("custom_message"),
            "project_details": {
                "type": rfi_data.get("bid_card", {}).get("project_type"),
                "address": rfi_data.get("bid_card", {}).get("address"),
                "description": rfi_data.get("bid_card", {}).get("description"),
                "budget": rfi_data.get("bid_card", {}).get("budget"),
                "timeline": rfi_data.get("bid_card", {}).get("timeline")
            },
            "guidance": generate_agent_guidance(rfi_data["request_type"], rfi_data["specific_items"])
        }
        
        return {
            "success": True,
            "context": context
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting RFI context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def generate_agent_guidance(request_type: str, specific_items: List[str]) -> Dict[str, Any]:
    """Generate guidance for the agent to help homeowner"""
    guidance = {
        "introduction": f"A contractor needs {request_type} for your project. I'll help you gather this information step by step.",
        "steps": [],
        "tips": []
    }
    
    if request_type == "pictures":
        guidance["steps"] = [
            "First, let's make sure you have good lighting for the photos",
            "Take wide shots to show the overall area",
            "Take close-ups of specific details mentioned",
            "Include something for scale (ruler, coin, etc.) when relevant"
        ]
        guidance["tips"] = [
            "Natural daylight usually works best",
            "Take multiple angles of the same area",
            "Clear any clutter that might obstruct the view"
        ]
    
    elif request_type == "measurements":
        guidance["steps"] = [
            "Gather a tape measure or measuring app",
            "Start with the largest dimensions first",
            "Measure at multiple points if surfaces are uneven",
            "Record measurements clearly with units"
        ]
        guidance["tips"] = [
            "Measure twice to ensure accuracy",
            "Include ceiling heights for room measurements",
            "Note any obstacles or irregularities"
        ]
    
    elif request_type == "clarification":
        guidance["steps"] = [
            "Review the specific questions carefully",
            "Gather any relevant documents or information",
            "Provide clear, detailed responses",
            "Ask for clarification if anything is unclear"
        ]
        guidance["tips"] = [
            "Be as specific as possible",
            "Include any constraints or preferences",
            "Mention your timeline or urgency"
        ]
    
    elif request_type == "technical":
        guidance["steps"] = [
            "Locate technical documentation if available",
            "Check model numbers and specifications",
            "Note the age and condition of systems",
            "Identify any recent repairs or modifications"
        ]
        guidance["tips"] = [
            "Take photos of nameplates and labels",
            "Check for manuals or warranty information",
            "Note any unusual sounds or behaviors"
        ]
    
    elif request_type == "access":
        guidance["steps"] = [
            "Determine available time windows",
            "Identify any access restrictions",
            "Note parking availability",
            "Mention any safety considerations"
        ]
        guidance["tips"] = [
            "Be flexible with scheduling if possible",
            "Provide gate codes or special instructions",
            "Mention pets or security systems"
        ]
    
    # Add specific items guidance
    guidance["specific_items_guidance"] = {}
    for item in specific_items:
        guidance["specific_items_guidance"][item] = generate_item_specific_guidance(item)
    
    return guidance


def generate_item_specific_guidance(item: str) -> str:
    """Generate guidance for specific request items"""
    item_lower = item.lower()
    
    if "picture" in item_lower or "photo" in item_lower:
        return "Take clear, well-lit photos from multiple angles"
    elif "measurement" in item_lower or "dimension" in item_lower:
        return "Measure accurately and include units (feet, inches, etc.)"
    elif "age" in item_lower or "year" in item_lower:
        return "Check installation dates, purchase receipts, or manufacturer labels"
    elif "model" in item_lower or "brand" in item_lower:
        return "Look for nameplates, stickers, or documentation with model information"
    elif "color" in item_lower or "preference" in item_lower:
        return "Specify your preferences clearly, provide examples if possible"
    elif "budget" in item_lower or "cost" in item_lower:
        return "Provide a realistic range you're comfortable with"
    elif "timeline" in item_lower or "schedule" in item_lower:
        return "Include start date preferences and any deadline constraints"
    else:
        return "Provide clear, detailed information about this item"


class RFIResponseNotification(BaseModel):
    rfi_id: str
    bid_card_id: str
    photos_added: int
    response_message: Optional[str] = None


@router.post("/api/rfi/notify-response")
async def notify_rfi_response(notification: RFIResponseNotification):
    """
    Notify contractor when homeowner responds to RFI with photos/message
    """
    try:
        # Get RFI details for notification using Supabase client
        rfi_result = db.client.table("rfi_requests").select(
            "*, bid_card:bid_cards(project_type, homeowner_name, location_address)"
        ).eq("id", notification.rfi_id).single().execute()
        
        if not rfi_result.data:
            raise HTTPException(status_code=404, detail="RFI request not found")
        
        rfi_data = rfi_result.data
        bid_card_data = rfi_data.get("bid_card", {})
        
        # Get contractor details
        contractor_result = db.client.table("contractors").select(
            "company_name, email, phone"
        ).eq("id", rfi_data["contractor_id"]).single().execute()
        
        contractor_data = contractor_result.data if contractor_result.data else None
        
        if not contractor_data:
            # Try contractor_leads table
            lead_result = db.client.table("contractor_leads").select(
                "company_name, email, phone"
            ).eq("id", rfi_data["contractor_id"]).single().execute()
            contractor_data = lead_result.data if lead_result.data else None
        
        # Create contractor notification content
        notification_content = f"""Homeowner Response Received!

Project: {bid_card_data.get('project_type', 'Project')} at {bid_card_data.get('location_address', 'Project Location')}
Homeowner: {bid_card_data.get('homeowner_name', 'Homeowner')}

Response Details:
- {notification.photos_added} new photos added to bid card"""
        
        if notification.response_message:
            notification_content += f"\n- Message: {notification.response_message}"
        
        notification_content += """

You can now view the updated bid card with the new photos and information.
Log in to your contractor portal to see the complete project details.

InstaBids Team"""
        
        # Send email notification to contractor if we have their email
        email_sent = False
        if contractor_data and contractor_data.get('email'):
            try:
                # Use the email MCP tool to send notification
                import requests
                email_response = requests.post(f"{get_backend_url()}/api/send-email", json={
                    "to": contractor_data['email'],
                    "subject": f"Homeowner Response: {bid_card_data.get('project_type', 'Project')} Project",
                    "body": notification_content,
                    "from": "noreply@instabids.com"
                }, timeout=10)
                
                email_sent = email_response.status_code == 200
                logger.info(f"[RFI] Email notification sent to contractor: {email_response.status_code}")
            except Exception as email_error:
                logger.error(f"[RFI] Email notification failed: {email_error}")
                # Don't fail the whole request for email issues
        
        # Log the notification in the database using Supabase client
        try:
            response_log = {
                "id": str(uuid.uuid4()),
                "bid_card_id": notification.bid_card_id,
                "contractor_id": rfi_data["contractor_id"],
                "response_type": "rfi_response_received",
                "response_content": f"Homeowner added {notification.photos_added} photos in response to RFI",
                "responded_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "rfi_id": notification.rfi_id,
                    "photos_added": notification.photos_added,
                    "email_sent": email_sent
                }
            }
            
            db.client.table("contractor_responses").insert(response_log).execute()
            logger.info(f"[RFI] Response logged for RFI {notification.rfi_id}")
        except Exception as log_error:
            logger.error(f"[RFI] Failed to log response: {log_error}")
            # Don't fail the request for logging issues
        
        # Update the bid card with the new photos in the JSONB field
        try:
            # Get current bid card data
            bid_card_result = db.client.table("bid_cards").select(
                "bid_document"
            ).eq("id", notification.bid_card_id).single().execute()
            
            if bid_card_result.data:
                bid_document = bid_card_result.data.get("bid_document", {})
                
                # Ensure all_extracted_data exists
                if "all_extracted_data" not in bid_document:
                    bid_document["all_extracted_data"] = {}
                
                # Ensure images array exists
                if "images" not in bid_document["all_extracted_data"]:
                    bid_document["all_extracted_data"]["images"] = []
                
                # Add a note about the RFI photos (actual photo URLs would be added by the frontend)
                rfi_photo_entry = {
                    "source": "rfi_response",
                    "rfi_id": notification.rfi_id,
                    "photos_count": notification.photos_added,
                    "added_at": datetime.utcnow().isoformat(),
                    "description": f"Photos provided in response to contractor RFI request"
                }
                
                bid_document["all_extracted_data"]["images"].append(rfi_photo_entry)
                
                # Update the bid card
                db.client.table("bid_cards").update({
                    "bid_document": bid_document,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", notification.bid_card_id).execute()
                
                logger.info(f"[RFI] Updated bid card {notification.bid_card_id} with RFI photo metadata")
        except Exception as update_error:
            logger.error(f"[RFI] Failed to update bid card: {update_error}")
            # Don't fail the request for bid card update issues
        
        return {
            "success": True,
            "message": "Contractor notification sent",
            "contractor_notified": email_sent,
            "photos_added": notification.photos_added,
            "bid_card_updated": True
        }
        
    except Exception as e:
        logger.error(f"[RFI] Notification error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")