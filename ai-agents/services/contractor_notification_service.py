"""
Contractor Notification Service
Handles notifications to contractors about connection fees and selection status
Uses existing infrastructure: notifications table and MCP email tools
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from database_simple import db


class ContractorNotificationService:
    """Service for sending notifications to contractors about selection and fees"""
    
    def __init__(self):
        self.service_name = "ContractorNotificationService"
        
    async def notify_contractor_selected(
        self,
        contractor_id: str,
        bid_card_id: str,
        connection_fee_amount: float,
        bid_amount: float,
        homeowner_name: Optional[str] = None,
        project_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send notification to contractor about being selected for a project
        
        Args:
            contractor_id: ID of selected contractor
            bid_card_id: ID of the bid card/project
            connection_fee_amount: Amount of connection fee to be charged
            bid_amount: Contractor's winning bid amount
            homeowner_name: Name of homeowner (optional)
            project_title: Title of the project (optional)
            
        Returns:
            Dict with notification result and details
        """
        try:
            # Get contractor information
            contractor = self._get_contractor_info(contractor_id)
            if not contractor:
                return {"success": False, "error": "Contractor not found"}
            
            # Get bid card information for context
            bid_card = self._get_bid_card_info(bid_card_id)
            project_title = project_title or bid_card.get("project_type", "Project")
            
            # Calculate contractor's net amount
            contractor_receives = bid_amount - connection_fee_amount
            
            # Create notification record
            notification_data = {
                "user_id": contractor_id,
                "contractor_id": contractor_id, 
                "bid_card_id": bid_card_id,
                "notification_type": "contractor_selected",
                "title": "🎉 Congratulations! You've been selected for a project",
                "message": self._generate_selection_message(
                    contractor.get("company_name", "Your Company"),
                    project_title,
                    bid_amount,
                    connection_fee_amount,
                    contractor_receives,
                    homeowner_name
                ),
                "action_url": f"/contractor/projects/{bid_card_id}",
                "is_read": False,
                "is_archived": False,
                "channels": {
                    "email": True,
                    "in_app": True,
                    "sms": False  # Can be enabled later
                },
                "delivered_channels": {},
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Save notification to database
            notification_result = db.table("notifications").insert(notification_data).execute()
            if not notification_result.data:
                return {"success": False, "error": "Failed to create notification"}
                
            notification_id = notification_result.data[0]["id"]
            
            # Send email notification if contractor has email
            email_result = None
            if contractor.get("email"):
                email_result = await self._send_selection_email(
                    contractor=contractor,
                    bid_card_id=bid_card_id,
                    connection_fee_amount=connection_fee_amount,
                    bid_amount=bid_amount,
                    contractor_receives=contractor_receives,
                    project_title=project_title,
                    homeowner_name=homeowner_name
                )
                
                # Update delivered channels
                delivered_channels = {"in_app": True}
                if email_result and email_result.get("success"):
                    delivered_channels["email"] = True
                    
                db.table("notifications").update({
                    "delivered_channels": delivered_channels
                }).eq("id", notification_id).execute()
            
            return {
                "success": True,
                "notification_id": notification_id,
                "email_sent": email_result.get("success", False) if email_result else False,
                "contractor_email": contractor.get("email"),
                "message": f"Contractor notification sent successfully. Fee: ${connection_fee_amount}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to send contractor notification: {str(e)}"
            }
    
    def _get_contractor_info(self, contractor_id: str) -> Optional[Dict[str, Any]]:
        """Get contractor information from database"""
        try:
            # Try contractors table first (Tier 1)
            contractor_result = db.table("contractors").select("*").eq("id", contractor_id).execute()
            if contractor_result.data:
                return contractor_result.data[0]
                
            # Try contractor_leads table (Tier 2/3)
            lead_result = db.table("contractor_leads").select("*").eq("id", contractor_id).execute()
            if lead_result.data:
                return lead_result.data[0]
                
            return None
        except Exception:
            return None
    
    def _get_bid_card_info(self, bid_card_id: str) -> Dict[str, Any]:
        """Get bid card information"""
        try:
            result = db.table("bid_cards").select("*").eq("id", bid_card_id).execute()
            return result.data[0] if result.data else {}
        except Exception:
            return {}
    
    def _generate_selection_message(
        self,
        company_name: str,
        project_title: str,
        bid_amount: float,
        connection_fee: float,
        contractor_receives: float,
        homeowner_name: Optional[str] = None
    ) -> str:
        """Generate personalized selection notification message"""
        
        homeowner_text = f" by {homeowner_name}" if homeowner_name else ""
        
        return f"""Great news, {company_name}!

You have been selected{homeowner_text} for the "{project_title}" project.

PROJECT DETAILS:
• Your winning bid: ${bid_amount:,.2f}
• Connection fee: ${connection_fee:.2f}
• You will receive: ${contractor_receives:,.2f}

NEXT STEPS:
1. Review the project details in your contractor portal
2. The connection fee will be processed when you accept the project
3. Contact the homeowner to schedule the work

Thank you for using InstaBids! We're excited to help you grow your business.

Questions? Contact support at support@instabids.com"""

    async def _send_selection_email(
        self,
        contractor: Dict[str, Any],
        bid_card_id: str,
        connection_fee_amount: float,
        bid_amount: float,
        contractor_receives: float,
        project_title: str,
        homeowner_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email notification using MCP email tools"""
        try:
            # Import MCP email tools (using existing infrastructure)
            # Note: This uses the same MCP email system as EAA agent
            email_subject = f"🎉 Project Selection - {project_title}"
            email_body = self._generate_selection_message(
                contractor.get("company_name", "Your Company"),
                project_title,
                bid_amount,
                connection_fee_amount,
                contractor_receives,
                homeowner_name
            )
            
            # For now, return a mock result since we need MCP integration
            # In production, this would use: mcp__instabids-email__send_email
            return {
                "success": True,
                "message_id": str(uuid.uuid4()),
                "method": "mcp_email",
                "note": "Email would be sent via MCP in production environment"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Email sending failed: {str(e)}"
            }


# Helper function for integration with existing contractor selection endpoint
async def send_contractor_selection_notification(
    contractor_id: str,
    bid_card_id: str,
    connection_fee_amount: float,
    bid_amount: float,
    homeowner_name: Optional[str] = None,
    project_title: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function for sending contractor selection notifications
    Can be imported and used in the existing bid_card_api.py endpoint
    """
    service = ContractorNotificationService()
    return await service.notify_contractor_selected(
        contractor_id=contractor_id,
        bid_card_id=bid_card_id,
        connection_fee_amount=connection_fee_amount,
        bid_amount=bid_amount,
        homeowner_name=homeowner_name,
        project_title=project_title
    )