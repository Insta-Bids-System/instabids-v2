"""
Bid Card Change Notification Service
Notifies contractors who have engaged with bid cards when changes occur
Integrated with JAA service for automatic notifications
"""

import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from database import SupabaseDB
db = SupabaseDB()

logger = logging.getLogger(__name__)


class BidCardChangeNotificationService:
    """Service for notifying contractors about bid card changes"""
    
    def __init__(self):
        self.service_name = "BidCardChangeNotificationService"
    
    async def get_engaged_contractors(self, bid_card_id: str) -> List[Dict[str, Any]]:
        """Get contractors who have actually engaged with a bid card"""
        
        engaged_contractors = []
        
        try:
            # 1. Contractors who submitted formal bids (PRIMARY)
            bid_result = db.client.table("contractor_bids").select(
                "contractor_id, amount, submitted_at, status"
            ).eq("bid_card_id", bid_card_id).execute()
            
            for bid in bid_result.data or []:
                engaged_contractors.append({
                    "contractor_id": bid["contractor_id"],
                    "engagement_type": "bid_submission",
                    "engagement_data": {
                        "bid_amount": float(bid["amount"]),
                        "submitted_at": bid["submitted_at"],
                        "status": bid["status"]
                    }
                })
            
            # 2. Contractors who messaged about this bid card
            message_result = db.client.table("bid_card_messages").select(
                "sender_id, created_at"
            ).eq("bid_card_id", bid_card_id).eq("sender_type", "contractor").execute()
            
            for message in message_result.data or []:
                engaged_contractors.append({
                    "contractor_id": message["sender_id"],
                    "engagement_type": "messaging",
                    "engagement_data": {
                        "last_message_at": message["created_at"]
                    }
                })
            
            # 3. Contractors who viewed bid card (if you want this)
            view_result = db.client.table("bid_card_views").select(
                "contractor_id, viewed_at, duration_seconds"
            ).eq("bid_card_id", bid_card_id).not_.is_("contractor_id", "null").execute()
            
            for view in view_result.data or []:
                engaged_contractors.append({
                    "contractor_id": view["contractor_id"],
                    "engagement_type": "viewed",
                    "engagement_data": {
                        "viewed_at": view["viewed_at"],
                        "duration_seconds": view["duration_seconds"]
                    }
                })
            
            # 4. Contractors from unified messaging system bid submissions
            unified_result = db.client.table("unified_messages").select(
                "metadata, created_at"
            ).contains("metadata", {"message_type": "bid_submission"}).execute()
            
            for message in unified_result.data or []:
                metadata = message.get("metadata", {})
                bid_data = metadata.get("bid_data", {})
                if bid_data.get("bid_card_id") == bid_card_id:
                    contractor_id = bid_data.get("contractor_id")
                    if contractor_id:
                        engaged_contractors.append({
                            "contractor_id": contractor_id,
                            "engagement_type": "unified_bid_submission",
                            "engagement_data": {
                                "amount": bid_data.get("amount"),
                                "submitted_at": message["created_at"]
                            }
                        })
            
            # Remove duplicates - contractor could have multiple engagement types
            unique_contractors = {}
            for contractor in engaged_contractors:
                contractor_id = contractor["contractor_id"]
                if contractor_id not in unique_contractors:
                    unique_contractors[contractor_id] = {
                        "contractor_id": contractor_id,
                        "engagement_types": [],
                        "engagement_data": {}
                    }
                
                unique_contractors[contractor_id]["engagement_types"].append(
                    contractor["engagement_type"]
                )
                unique_contractors[contractor_id]["engagement_data"][
                    contractor["engagement_type"]
                ] = contractor["engagement_data"]
            
            return list(unique_contractors.values())
            
        except Exception as e:
            print(f"Error getting engaged contractors: {e}")
            return []
    
    async def notify_engaged_contractors(
        self, 
        bid_card_id: str, 
        change_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Notify contractors who have engaged with the bid card about changes"""
        
        try:
            # Get engaged contractors
            engaged_contractors = await self.get_engaged_contractors(bid_card_id)
            
            if not engaged_contractors:
                return {
                    "success": True,
                    "contractors_notified": 0,
                    "message": "No engaged contractors to notify"
                }
            
            # Get bid card info for context
            bid_card = await self._get_bid_card_info(bid_card_id)
            
            notifications = []
            for contractor in engaged_contractors:
                # Try to get contractor_leads ID, but proceed even if not found
                contractor_lead_id = await self._get_contractor_lead_id(contractor["contractor_id"])
                
                notification = {
                    "id": str(uuid.uuid4()),
                    "user_id": contractor["contractor_id"],
                    "contractor_id": contractor_lead_id,  # May be null - that's OK
                    "bid_card_id": bid_card_id,
                    "notification_type": "bid_card_change",
                    "title": self._generate_change_title(change_details["change_type"]),
                    "message": self._generate_change_message(
                        change_details,
                        bid_card.get("project_type", "Project"),
                        contractor["engagement_types"]
                    ),
                    "action_url": f"/contractor/bid-cards/{bid_card_id}",
                    "is_read": False,
                    "is_archived": False,
                    "channels": {
                        "email": True,
                        "in_app": True,
                        "sms": False
                    },
                    "delivered_channels": {"in_app": True},
                    "created_at": datetime.utcnow().isoformat()
                }
                notifications.append(notification)
            
            # Batch insert notifications
            result = db.client.table("notifications").insert(notifications).execute()
            
            if not result.data:
                return {
                    "success": False,
                    "error": "Failed to create notifications"
                }
            
            # Send real-time WebSocket notifications if contractors are connected
            try:
                from routers.contractor_websocket_routes import broadcast_bid_card_change_to_contractors
                contractor_ids = [c["contractor_id"] for c in engaged_contractors]
                await broadcast_bid_card_change_to_contractors(
                    bid_card_id=bid_card_id,
                    engaged_contractors=contractor_ids,
                    change_details=change_details
                )
                logger.info(f"Sent real-time notifications for bid card {bid_card_id}")
            except Exception as ws_error:
                logger.warning(f"Could not send WebSocket notifications: {ws_error}")
            
            # TODO: Add email notifications via MCP tools
            
            return {
                "success": True,
                "contractors_notified": len(engaged_contractors),
                "notification_ids": [n["id"] for n in notifications],
                "engagement_breakdown": {
                    "bid_submissions": len([c for c in engaged_contractors 
                                         if "bid_submission" in c["engagement_types"]]),
                    "messaging": len([c for c in engaged_contractors 
                                   if "messaging" in c["engagement_types"]]),
                    "views": len([c for c in engaged_contractors 
                                if "viewed" in c["engagement_types"]])
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to notify contractors: {str(e)}"
            }
    
    def _generate_change_title(self, change_type: str) -> str:
        """Generate notification title based on change type"""
        titles = {
            "budget_change": "💰 Project Budget Updated",
            "scope_change": "🔧 Project Scope Changed", 
            "deadline_change": "⏰ Project Timeline Updated",
            "location_change": "📍 Project Location Changed",
            "requirements_change": "📋 Project Requirements Updated",
            "general_update": "📢 Project Updated"
        }
        return titles.get(change_type, "📢 Project Updated")
    
    def _generate_change_message(
        self, 
        change_details: Dict[str, Any],
        project_type: str,
        engagement_types: List[str]
    ) -> str:
        """Generate personalized notification message"""
        
        change_type = change_details["change_type"]
        description = change_details.get("description", "Project has been updated")
        previous_value = change_details.get("previous_value")
        new_value = change_details.get("new_value")
        
        # Personalize based on engagement type
        if "bid_submission" in engagement_types:
            engagement_context = "Since you submitted a bid for this project, "
        elif "messaging" in engagement_types:
            engagement_context = "Since you've been in communication about this project, "
        elif "viewed" in engagement_types:
            engagement_context = "Since you viewed this project, "
        else:
            engagement_context = ""
        
        message = f"""{engagement_context}we wanted to notify you of an important update:

PROJECT: {project_type}
CHANGE: {change_type.replace('_', ' ').title()}

{description}"""
        
        # Add before/after details if available
        if previous_value and new_value:
            message += f"""

PREVIOUS: {previous_value}
NEW: {new_value}"""
        
        message += f"""

You can view the updated project details in your contractor portal. If you have questions about how this change affects your bid or interest in the project, please reach out.

Thank you for your continued interest in InstaBids projects!"""
        
        return message
    
    async def _get_contractor_lead_id(self, contractor_id: str) -> Optional[str]:
        """Get contractor_leads ID for a contractor (handles contractors vs contractor_leads table issue)"""
        try:
            # First try contractor_leads table directly
            result = db.client.table("contractor_leads").select("id").eq("id", contractor_id).execute()
            if result.data:
                return result.data[0]["id"]
            
            # If not found, try to find matching contractor_lead via company name or other data
            # This is a workaround until Agent 4 unifies the tables
            contractor_result = db.client.table("contractors").select("company_name, email").eq("id", contractor_id).execute()
            if contractor_result.data:
                contractor_data = contractor_result.data[0]
                company_name = contractor_data.get("company_name")
                
                if company_name:
                    # Try to find matching contractor_lead by company name
                    lead_result = db.client.table("contractor_leads").select("id").eq("company_name", company_name).execute()
                    if lead_result.data:
                        return lead_result.data[0]["id"]
            
            return None
        except Exception as e:
            print(f"Error getting contractor_leads ID: {e}")
            return None
    
    async def _get_bid_card_info(self, bid_card_id: str) -> Dict[str, Any]:
        """Get bid card information for context"""
        try:
            result = db.client.table("bid_cards").select("*").eq("id", bid_card_id).execute()
            return result.data[0] if result.data else {}
        except Exception:
            return {}


# Integration function for JAA service
async def notify_contractors_of_bid_card_change(
    bid_card_id: str,
    change_type: str,
    description: str,
    previous_value: Optional[str] = None,
    new_value: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function for notifying contractors of bid card changes
    Designed for integration with JAA service
    """
    service = BidCardChangeNotificationService()
    
    change_details = {
        "change_type": change_type,
        "description": description,
        "previous_value": previous_value,
        "new_value": new_value
    }
    
    return await service.notify_engaged_contractors(bid_card_id, change_details)


# Test function to check engagement
async def test_engagement_detection(bid_card_id: str) -> Dict[str, Any]:
    """Test function to see what contractors are engaged with a bid card"""
    service = BidCardChangeNotificationService()
    engaged = await service.get_engaged_contractors(bid_card_id)
    
    return {
        "bid_card_id": bid_card_id,
        "total_engaged_contractors": len(engaged),
        "engagement_breakdown": engaged
    }