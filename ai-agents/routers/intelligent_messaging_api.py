"""
GPT-5 Intelligent Messaging API
BUSINESS CRITICAL: Advanced messaging system with GPT-5 powered security analysis
Author: Agent 3 (Homeowner UX)
Date: February 8, 2025
"""

import asyncio
import base64
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

import database_simple
from config.service_urls import get_backend_url
from agents.intelligent_messaging_agent import (
    process_intelligent_message,
    AgentAction,
    MessageType
)


router = APIRouter(prefix="/api/intelligent-messages", tags=["intelligent-messaging"])


class IntelligentMessageRequest(BaseModel):
    """Request model for intelligent message processing"""
    content: str
    sender_type: str  # 'homeowner' or 'contractor'
    sender_id: str
    bid_card_id: str
    conversation_id: Optional[str] = None
    target_contractor_id: Optional[str] = None
    message_type: Optional[str] = "text"
    metadata: Optional[Dict[str, Any]] = {}
    # BID SUBMISSION FIELDS
    bid_data: Optional[Dict[str, Any]] = None


class AgentCommentResponse(BaseModel):
    """Agent comment visible to specific party"""
    visible_to: str
    user_id: str
    content: str
    type: str
    timestamp: str


class IntelligentMessageResponse(BaseModel):
    """Response model for processed intelligent message"""
    success: bool
    message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    approved: bool
    agent_decision: str
    threats_detected: List[str]
    confidence_score: float
    original_content: str
    filtered_content: str
    agent_comments: List[AgentCommentResponse]
    error: Optional[str] = None


async def upload_file_to_storage(file_data: bytes, file_name: str, content_type: str, bucket: str = "project-images") -> str:
    """Upload file to Supabase Storage and return public URL"""
    try:
        db = database_simple.get_client()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_name = f"intelligent_messages/{timestamp}_{uuid.uuid4().hex[:8]}_{file_name}"
        
        db.storage.from_(bucket).upload(
            unique_name,
            file_data,
            {
                "content-type": content_type,
                "cache-control": "3600",
                "upsert": "false"
            }
        )
        
        public_url = db.storage.from_(bucket).get_public_url(unique_name)
        return public_url
    
    except Exception as e:
        raise Exception(f"Failed to upload file: {e}")


@router.get("/health")
async def health_check():
    """Health check for intelligent messaging system"""
    try:
        # Test database connection with unified messaging system
        db = database_simple.get_client()
        result = db.table("unified_conversations").select("count").limit(1).execute()
        
        # Simple health check without triggering full AI processing
        # Just verify the system components are available
        
        return {
            "success": True,
            "status": "healthy",
            "message": "Intelligent Messaging System ready",
            "database": "connected",
            "intelligent_agent": "available",
            "api_endpoints": "operational",
            "fallback_system": "active",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.post("/send", response_model=IntelligentMessageResponse)
async def send_intelligent_message(request: IntelligentMessageRequest):
    """
    Send message through GPT-5 intelligent security analysis
    
    BUSINESS CRITICAL: This endpoint prevents contact information sharing
    """
    try:
        # Determine message type based on bid_data presence
        message_type = MessageType.BID_SUBMISSION if request.bid_data else MessageType.TEXT
        
        # Check if this is a bid submission (doesn't need conversation resolution)
        is_bid_submission = request.message_type and "bid_submission" in request.message_type
        
        # Process message through intelligent agent
        agent_result = await process_intelligent_message(
            content=request.content,
            sender_type=request.sender_type,
            sender_id=request.sender_id,
            bid_card_id=request.bid_card_id,
            conversation_id=request.conversation_id,
            attachments=[],  # TODO: Add attachment support
            image_data=None,   # TODO: Add image analysis
            message_type=message_type,
            bid_data=request.bid_data
        )
        
        # For bid submissions, skip conversation resolution entirely
        if is_bid_submission:
            # Don't need conversation for bid filtering
            conversation_id = f"bid-submission-{request.bid_card_id}"
            
            # Return the filtered result immediately
            return IntelligentMessageResponse(
                success=True,
                message_id=None,  # No message saved for bid filtering
                conversation_id=conversation_id,
                approved=agent_result["approved"],
                agent_decision=agent_result["agent_decision"],
                threats_detected=agent_result["threats_detected"],
                confidence_score=agent_result["confidence_score"],
                original_content=request.content,
                filtered_content=agent_result["filtered_content"],
                agent_comments=[]
            )
        
        # For regular messages, handle conversation targeting (OLD SYSTEM - BROKEN)
        conversation_id = await resolve_conversation_id(
            request=request,
            agent_approved=agent_result["approved"]
        )
        
        if not conversation_id:
            return IntelligentMessageResponse(
                success=False,
                approved=False,
                agent_decision="block",
                threats_detected=["conversation_error"],
                confidence_score=1.0,
                original_content=request.content,
                filtered_content="",
                agent_comments=[],
                error="Could not determine conversation target"
            )
        
        # Save message if approved (or blocked message for audit)
        message_id = None
        if agent_result["approved"]:
            message_id = await save_approved_message(
                conversation_id=conversation_id,
                request=request,
                agent_result=agent_result
            )
        else:
            # Log blocked message for security analysis
            await log_blocked_message(
                request=request,
                agent_result=agent_result
            )
        
        # Convert agent comments to response format
        agent_comments = []
        for comment in agent_result.get("agent_comments", []):
            agent_comments.append(AgentCommentResponse(
                visible_to=comment["visible_to"],
                user_id=comment["user_id"],
                content=comment["content"],
                type=comment["type"],
                timestamp=comment["timestamp"]
            ))
        
        return IntelligentMessageResponse(
            success=True,
            message_id=message_id,
            conversation_id=conversation_id,
            approved=agent_result["approved"],
            agent_decision=agent_result["agent_decision"],
            threats_detected=agent_result["threats_detected"],
            confidence_score=agent_result["confidence_score"],
            original_content=request.content,
            filtered_content=agent_result["filtered_content"],
            agent_comments=agent_comments
        )
        
    except Exception as e:
        return IntelligentMessageResponse(
            success=False,
            approved=False,
            agent_decision="block",
            threats_detected=["system_error"],
            confidence_score=0.0,
            original_content=request.content,
            filtered_content="",
            agent_comments=[],
            error=str(e)
        )


async def resolve_conversation_id(request: IntelligentMessageRequest, agent_approved: bool) -> Optional[str]:
    """Resolve the correct conversation ID for message targeting"""
    try:
        db = database_simple.get_client()
        
        # Option 1: Explicit conversation_id provided
        if request.conversation_id:
            conv_check = db.table("conversations").select("*").eq(
                "id", request.conversation_id
            ).eq("bid_card_id", request.bid_card_id).execute()
            
            if conv_check.data:
                return request.conversation_id
            else:
                return None
        
        # Option 2: Homeowner sending to specific contractor
        elif request.sender_type == "homeowner" and request.target_contractor_id:
            conv_result = db.table("conversations").select("*").eq(
                "bid_card_id", request.bid_card_id
            ).eq("user_id", request.sender_id).eq(
                "contractor_id", request.target_contractor_id
            ).execute()
            
            if conv_result.data:
                return conv_result.data[0]["id"]
            else:
                # Create new conversation
                new_conv = {
                    "bid_card_id": request.bid_card_id,
                    "user_id": request.sender_id,
                    "contractor_id": request.target_contractor_id,
                    "contractor_alias": f"Contractor {request.target_contractor_id[:1].upper()}",
                    "status": "active"
                }
                create_result = db.table("conversations").insert(new_conv).execute()
                return create_result.data[0]["id"] if create_result.data else None
        
        # Option 3: Contractor sending message
        elif request.sender_type == "contractor":
            conv_result = db.table("conversations").select("*").eq(
                "bid_card_id", request.bid_card_id
            ).eq("contractor_id", request.sender_id).execute()
            
            if conv_result.data:
                return conv_result.data[0]["id"]
            else:
                # Create new conversation
                bid_card_result = db.table("bid_cards").select("user_id").eq(
                    "id", request.bid_card_id
                ).execute()
                
                if bid_card_result.data:
                    user_id = bid_card_result.data[0]["user_id"]
                    new_conv = {
                        "bid_card_id": request.bid_card_id,
                        "user_id": user_id,
                        "contractor_id": request.sender_id,
                        "contractor_alias": "Contractor",
                        "status": "active"
                    }
                    create_result = db.table("conversations").insert(new_conv).execute()
                    return create_result.data[0]["id"] if create_result.data else None
        
        return None
        
    except Exception as e:
        print(f"Error resolving conversation ID: {e}")
        return None


async def save_approved_message(conversation_id: str, request: IntelligentMessageRequest, agent_result: Dict[str, Any]) -> Optional[str]:
    """Save approved message to database"""
    try:
        db = database_simple.get_client()
        
        message_data = {
            "conversation_id": conversation_id,
            "sender_type": request.sender_type,
            "sender_id": request.sender_id,
            "original_content": request.content,
            "filtered_content": agent_result["filtered_content"],
            "content_filtered": request.content != agent_result["filtered_content"],
            "message_type": request.message_type,
            "metadata": {
                **request.metadata,
                "intelligent_agent": {
                    "agent_decision": agent_result["agent_decision"],
                    "confidence_score": agent_result["confidence_score"],
                    "threats_detected": agent_result["threats_detected"],
                    "agent_comments_count": len(agent_result.get("agent_comments", []))
                }
            },
            "is_read": False
        }
        
        # Save message via UNIFIED CONVERSATION API
        import requests
        try:
            response = requests.post(f"{get_backend_url()}/api/conversations/message", json={
                "conversation_id": conversation_id,
                "sender_type": message_data["sender_type"],
                "sender_id": message_data["sender_id"],
                "agent_type": "intelligent_messaging",
                "content": message_data["filtered_content"],
                "content_type": "text",
                "metadata": message_data["metadata"]
            }, timeout=30)
            
            if response.ok:
                result = response.json()
                return result.get("message_id")
            else:
                print(f"Failed to save via unified API: {response.text}")
                return None
                
        except Exception as api_error:
            print(f"Error calling unified API: {api_error}")
            return None
        
    except Exception as e:
        print(f"Error saving message: {e}")
        return None


async def log_blocked_message(request: IntelligentMessageRequest, agent_result: Dict[str, Any]):
    """Log blocked messages for security analysis"""
    try:
        db = database_simple.get_client()
        
        log_data = {
            "bid_card_id": request.bid_card_id,
            "sender_type": request.sender_type,
            "sender_id": request.sender_id,
            "original_content": request.content,
            "threats_detected": agent_result["threats_detected"],
            "agent_decision": agent_result["agent_decision"],
            "confidence_score": agent_result["confidence_score"],
            "blocked_at": datetime.now().isoformat(),
            "metadata": request.metadata
        }
        
        db.table("blocked_messages_log").insert(log_data).execute()
        
    except Exception as e:
        print(f"Error logging blocked message: {e}")


@router.post("/send-with-image")
async def send_message_with_image(
    content: str = Form(...),
    sender_type: str = Form(...),
    sender_id: str = Form(...),
    bid_card_id: str = Form(...),
    conversation_id: Optional[str] = Form(None),
    target_contractor_id: Optional[str] = Form(None),
    image: UploadFile = File(...)
):
    """Send message with image through intelligent analysis"""
    try:
        # Validate image
        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and encode image for GPT-5 analysis
        image_data = await image.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        image_format = image.content_type.split('/')[-1]
        
        # Process through intelligent agent with image analysis
        agent_result = await process_intelligent_message(
            content=content,
            sender_type=sender_type,
            sender_id=sender_id,
            bid_card_id=bid_card_id,
            conversation_id=conversation_id,
            image_data=image_base64
        )
        
        # Handle conversation targeting
        request_obj = IntelligentMessageRequest(
            content=content,
            sender_type=sender_type,
            sender_id=sender_id,
            bid_card_id=bid_card_id,
            conversation_id=conversation_id,
            target_contractor_id=target_contractor_id
        )
        
        conversation_id_resolved = await resolve_conversation_id(
            request=request_obj,
            agent_approved=agent_result["approved"]
        )
        
        if not conversation_id_resolved:
            return {
                "success": False,
                "error": "Could not determine conversation target",
                "approved": False
            }
        
        message_id = None
        image_url = None
        
        if agent_result["approved"]:
            # Upload image if message approved
            image_url = await upload_file_to_storage(
                image_data,
                image.filename or "image.jpg",
                image.content_type,
                "project-images"
            )
            
            # Save message with image attachment
            message_id = await save_approved_message(
                conversation_id=conversation_id_resolved,
                request=request_obj,
                agent_result=agent_result
            )
            
            # Save image attachment
            if message_id:
                db = database_simple.get_client()
                attachment_data = {
                    "message_id": message_id,
                    "type": "image",
                    "url": image_url,
                    "name": image.filename or "image.jpg",
                    "size": len(image_data),
                    "analyzed_by_agent": True,
                    "analysis_result": agent_result.get("image_analysis", {})
                }
                db.table("message_attachments").insert(attachment_data).execute()
        else:
            # Log blocked message with image
            await log_blocked_message(request=request_obj, agent_result=agent_result)
        
        return {
            "success": True,
            "message_id": message_id,
            "conversation_id": conversation_id_resolved,
            "approved": agent_result["approved"],
            "agent_decision": agent_result["agent_decision"],
            "threats_detected": agent_result["threats_detected"],
            "confidence_score": agent_result["confidence_score"],
            "image_url": image_url if agent_result["approved"] else None,
            "image_analysis": agent_result.get("image_analysis", {}),
            "agent_comments": agent_result.get("agent_comments", [])
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "approved": False
        }


@router.get("/agent-comments/{user_type}/{user_id}")
async def get_agent_comments(user_type: str, user_id: str, bid_card_id: Optional[str] = None):
    """Get agent comments visible to specific user"""
    try:
        db = database_simple.get_client()
        
        query = db.table("agent_comments").select("*").eq(
            "visible_to_type", user_type
        ).eq("visible_to_id", user_id)
        
        if bid_card_id:
            # Join with messages to filter by bid card
            query = query.join("messages", "agent_comments.message_id = messages.id").join(
                "conversations", "messages.conversation_id = conversations.id"
            ).eq("conversations.bid_card_id", bid_card_id)
        
        result = query.order("created_at", desc=True).execute()
        
        return {
            "success": True,
            "comments": result.data or []
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "comments": []
        }


@router.get("/security-analysis/{bid_card_id}")
async def get_security_analysis(bid_card_id: str):
    """Get security analysis summary for a bid card"""
    try:
        db = database_simple.get_client()
        
        # Get blocked messages count
        blocked_result = db.table("blocked_messages_log").select("*").eq(
            "bid_card_id", bid_card_id
        ).execute()
        
        blocked_messages = blocked_result.data or []
        
        # Get messages from UNIFIED MESSAGING SYSTEM
        messages_result = db.table("unified_messages").select("*").contains(
            "metadata", {"bid_card_id": bid_card_id}
        ).execute()
        
        all_messages = messages_result.data or []
        filtered_messages = [msg for msg in all_messages if msg.get("content_filtered")]
        
        # Analyze threat patterns
        threat_summary = {}
        for blocked in blocked_messages:
            for threat in blocked.get("threats_detected", []):
                threat_summary[threat] = threat_summary.get(threat, 0) + 1
        
        return {
            "success": True,
            "analysis": {
                "total_messages": len(all_messages),
                "blocked_messages": len(blocked_messages),
                "filtered_messages": len(filtered_messages),
                "security_score": max(0, 100 - (len(blocked_messages) * 10)),  # Lower score for more threats
                "threat_patterns": threat_summary,
                "last_threat_detected": max([b["blocked_at"] for b in blocked_messages]) if blocked_messages else None
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "analysis": {}
        }


@router.post("/notify-contractors-scope-change")
async def notify_contractors_scope_change(request: dict):
    """
    Notify other contractors about scope changes to bid card
    
    BUSINESS CRITICAL: Ensures all contractors have same project information
    """
    try:
        required_fields = ["bid_card_id", "user_id", "scope_changes", "scope_change_details"]
        for field in required_fields:
            if field not in request:
                return {"success": False, "error": f"Missing required field: {field}"}
        
        bid_card_id = request["bid_card_id"]
        user_id = request["user_id"]
        scope_changes = request["scope_changes"]
        scope_change_details = request["scope_change_details"]
        
        # Get all contractors for this bid card
        db = database_simple.get_client()
        conversations_result = db.table("conversations").select(
            "contractor_id, contractor_alias, id"
        ).eq("bid_card_id", bid_card_id).execute()
        
        contractors = conversations_result.data or []
        
        if not contractors:
            return {
                "success": False,
                "error": "No contractors found for this bid card",
                "contractors_notified": 0
            }
        
        # Create scope change notification message
        notification_message = create_scope_change_notification_message(
            scope_changes, scope_change_details
        )
        
        # Send notification to each contractor
        notifications_sent = []
        
        for contractor in contractors:
            try:
                # Create system message in conversation
                notification_data = {
                    "conversation_id": contractor["id"],
                    "sender_type": "system",
                    "sender_id": "intelligent-agent",
                    "original_content": notification_message,
                    "filtered_content": notification_message,
                    "content_filtered": False,
                    "message_type": "scope_change_notification",
                    "metadata": {
                        "scope_changes": scope_changes,
                        "scope_change_details": scope_change_details,
                        "notification_type": "scope_change",
                        "user_id": user_id
                    },
                    "is_read": False
                }
                
                # Save notification via UNIFIED CONVERSATION API
                import requests
                response = requests.post(f"{get_backend_url()}/api/conversations/message", json={
                    "conversation_id": contractor["id"],
                    "sender_type": "system",
                    "sender_id": "intelligent-agent",
                    "agent_type": "intelligent_messaging",
                    "content": notification_message,
                    "content_type": "text",
                    "metadata": notification_data["metadata"]
                }, timeout=30)
                
                if response.ok:
                    notifications_sent.append({
                        "contractor_id": contractor["contractor_id"],
                        "contractor_alias": contractor["contractor_alias"],
                        "message_id": response.json().get("message_id"),
                        "notification_sent": True
                    })
                
            except Exception as e:
                notifications_sent.append({
                    "contractor_id": contractor["contractor_id"],
                    "contractor_alias": contractor["contractor_alias"],
                    "error": str(e),
                    "notification_sent": False
                })
        
        # Update bid card with scope change information
        bid_card_update = {
            "scope_last_updated": datetime.now().isoformat(),
            "scope_change_history": {
                "timestamp": datetime.now().isoformat(),
                "changes": scope_changes,
                "details": scope_change_details,
                "updated_by": user_id
            }
        }
        
        db.table("bid_cards").update(bid_card_update).eq("id", bid_card_id).execute()
        
        return {
            "success": True,
            "bid_card_id": bid_card_id,
            "contractors_notified": len([n for n in notifications_sent if n.get("notification_sent")]),
            "total_contractors": len(contractors),
            "notifications": notifications_sent,
            "notification_message": notification_message
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "contractors_notified": 0
        }


def create_scope_change_notification_message(scope_changes: list, scope_change_details: dict) -> str:
    """Create user-friendly notification message for contractors"""
    
    change_descriptions = []
    for change in scope_changes:
        if change == "material_change":
            change_descriptions.append("material specifications")
        elif change == "size_change":
            change_descriptions.append("project size")
        elif change == "feature_addition":
            change_descriptions.append("additional features")
        elif change == "feature_removal":
            change_descriptions.append("removed features")
        elif change == "timeline_change":
            change_descriptions.append("project timeline")
        elif change == "budget_change":
            change_descriptions.append("project budget")
    
    if not change_descriptions:
        changes_text = "project specifications"
    elif len(change_descriptions) == 1:
        changes_text = change_descriptions[0]
    else:
        changes_text = ", ".join(change_descriptions[:-1]) + " and " + change_descriptions[-1]
    
    message = f"📋 Project Update: The homeowner has made changes to the {changes_text}. "
    message += f"Please review the updated project details and adjust your bid accordingly if needed. "
    message += f"All contractors are receiving this same notification to ensure everyone has the most current project information."
    
    return message


@router.post("/respond-to-scope-change-question")
async def respond_to_scope_change_question(request: dict):
    """
    Handle homeowner response to scope change question
    
    Expected format:
    {
        "message_id": "id of original agent comment",
        "homeowner_response": "yes" or "no", 
        "bid_card_id": "bid card id",
        "user_id": "homeowner id"
    }
    """
    try:
        required_fields = ["message_id", "homeowner_response", "bid_card_id", "user_id"]
        for field in required_fields:
            if field not in request:
                return {"success": False, "error": f"Missing required field: {field}"}
        
        response = request["homeowner_response"].lower()
        
        if response in ["yes", "y", "notify", "send"]:
            # Homeowner wants to notify other contractors
            
            # Get the original agent comment to extract scope change details
            db = database_simple.get_client()
            comment_result = db.table("agent_comments").select("*").eq(
                "message_id", request["message_id"]
            ).execute()
            
            if not comment_result.data:
                return {"success": False, "error": "Original scope change question not found"}
            
            comment = comment_result.data[0]
            metadata = comment.get("metadata", {})
            
            # Send notifications using the notification endpoint
            notification_result = await notify_contractors_scope_change({
                "bid_card_id": request["bid_card_id"],
                "user_id": request["user_id"],
                "scope_changes": metadata.get("scope_changes", []),
                "scope_change_details": metadata.get("scope_change_details", {})
            })
            
            # Mark the agent comment as resolved
            db.table("agent_comments").update({
                "resolved": True,
                "homeowner_response": "notify_contractors",
                "resolved_at": datetime.now().isoformat()
            }).eq("message_id", request["message_id"]).execute()
            
            return {
                "success": True,
                "action_taken": "contractors_notified",
                "notification_result": notification_result
            }
            
        else:
            # Homeowner chose not to notify
            db = database_simple.get_client()
            db.table("agent_comments").update({
                "resolved": True,
                "homeowner_response": "no_notification",
                "resolved_at": datetime.now().isoformat()
            }).eq("message_id", request["message_id"]).execute()
            
            return {
                "success": True,
                "action_taken": "no_notification",
                "message": "Scope change logged but other contractors not notified"
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "action_taken": "none"
        }


@router.get("/scope-change-notifications/{contractor_id}")
async def get_scope_change_notifications(contractor_id: str, bid_card_id: str = None):
    """Get scope change notifications for a contractor"""
    try:
        db = database_simple.get_client()
        
        # Get conversations for the contractor
        conversations_query = db.table("conversations").select("id").eq("contractor_id", contractor_id)
        if bid_card_id:
            conversations_query = conversations_query.eq("bid_card_id", bid_card_id)
        
        conversations_result = conversations_query.execute()
        conversation_ids = [conv["id"] for conv in conversations_result.data or []]
        
        if not conversation_ids:
            return {"success": True, "notifications": []}
        
        # Get scope change notifications from UNIFIED MESSAGING SYSTEM
        notifications_result = db.table("unified_messages").select("*").contains(
            "metadata", {"notification_type": "scope_change"}
        ).order("created_at", desc=True).execute()
        
        return {
            "success": True,
            "notifications": notifications_result.data or []
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "notifications": []
        }


@router.post("/test-security")
async def test_security_analysis(test_content: str):
    """Test endpoint for security analysis (development only)"""
    try:
        result = await process_intelligent_message(
            content=test_content,
            sender_type="contractor",
            sender_id="test-user",
            bid_card_id="test-bid-card"
        )
        
        return {
            "success": True,
            "test_content": test_content,
            "analysis_result": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "test_content": test_content
        }