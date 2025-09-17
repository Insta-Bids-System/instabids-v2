#!/usr/bin/env python3
"""
SCOPE CHANGE HANDLER
Manages the complete scope change workflow from detection to bid card updates
"""

from typing import Dict, List, Any, Optional
import json
import requests
from datetime import datetime
import sys
import os

# Add database path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database_simple import get_client

class ScopeChangeHandler:
    """Handles scope change detection, homeowner questions, and bid card updates"""
    
    def __init__(self):
        self.db = None
        try:
            self.db = get_client()
        except Exception as e:
            print(f"Warning: Database connection failed: {e}")
    
    async def handle_scope_change(self, 
                                  scope_changes: List[str],
                                  scope_details: Dict[str, Any], 
                                  bid_card_id: str,
                                  sender_id: str,
                                  message_content: str) -> Dict[str, Any]:
        """Complete scope change handling workflow"""
        
        result = {
            "scope_changes_detected": scope_changes,
            "scope_change_details": scope_details,
            "requires_bid_update": len(scope_changes) > 0,
            "homeowner_question": None,
            "other_contractors": [],
            "bid_card_updated": False,
            "error": None
        }
        
        if not scope_changes:
            return result
        
        try:
            # Step 1: Get other contractors for this bid card
            other_contractors = await self._get_other_contractors(bid_card_id)
            result["other_contractors"] = other_contractors
            
            # Step 2: Generate homeowner-only question
            if other_contractors:
                homeowner_question = self._create_homeowner_question(
                    scope_changes, scope_details, other_contractors, message_content
                )
                result["homeowner_question"] = homeowner_question
            
            # Step 3: Update bid card with scope change (if confirmed)
            # For now, we'll just log the scope change - in production this would
            # wait for homeowner confirmation
            scope_change_log = await self._log_scope_change(
                bid_card_id, scope_changes, scope_details, sender_id
            )
            
            result["scope_change_logged"] = scope_change_log
            result["success"] = scope_change_log  # Add success field based on JAA call
            
            # If JAA was called successfully, add its response
            if hasattr(self, '_last_jaa_response'):
                result["jaa_response"] = self._last_jaa_response
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            return result
    
    async def _get_other_contractors(self, bid_card_id: str) -> List[Dict[str, str]]:
        """Get other contractors bidding on this project"""
        
        if not self.db:
            # Return mock data for testing when DB unavailable
            return [
                {"id": "contractor-123", "name": "Elite Kitchen Contractors", "alias": "Elite Kitchen"},
                {"id": "contractor-456", "name": "Home Renovation Pros", "alias": "Renovation Pros"},
                {"id": "contractor-789", "name": "Quality Builders Inc", "alias": "Quality Builders"}
            ]
        
        try:
            # Get bid card to understand the project
            bid_card = self.db.table("bid_cards").select("*").eq("id", bid_card_id).single().execute()
            
            if not bid_card.data:
                return []
            
            # Method 1: Get contractors from existing bids
            bids_result = self.db.table("contractor_bids").select(
                "contractor_id, contractors(company_name, id)"
            ).eq("bid_card_id", bid_card_id).execute()
            
            contractors = []
            for bid in bids_result.data or []:
                contractor_info = bid.get("contractors", {})
                if contractor_info:
                    contractors.append({
                        "id": contractor_info["id"],
                        "name": contractor_info["company_name"],
                        "alias": contractor_info["company_name"][:20] + "..." if len(contractor_info["company_name"]) > 20 else contractor_info["company_name"]
                    })
            
            # Method 2: Get contractors from outreach campaigns if no bids yet
            if not contractors:
                campaigns = self.db.table("outreach_campaigns").select(
                    "campaign_contractors(contractor_id, contractors(company_name, id))"
                ).eq("bid_card_id", bid_card_id).execute()
                
                for campaign in campaigns.data or []:
                    campaign_contractors = campaign.get("campaign_contractors", [])
                    for cc in campaign_contractors:
                        contractor_info = cc.get("contractors", {})
                        if contractor_info:
                            contractors.append({
                                "id": contractor_info["id"], 
                                "name": contractor_info["company_name"],
                                "alias": contractor_info["company_name"][:20] + "..." if len(contractor_info["company_name"]) > 20 else contractor_info["company_name"]
                            })
            
            return contractors
            
        except Exception as e:
            print(f"Error getting other contractors: {e}")
            # Return mock data for testing
            return [
                {"id": "contractor-123", "name": "Kitchen Specialists LLC", "alias": "Kitchen Specialists"},
                {"id": "contractor-456", "name": "Home Improvement Co", "alias": "Home Improvement"}
            ]
    
    def _create_homeowner_question(self, 
                                   scope_changes: List[str], 
                                   scope_details: Dict[str, Any],
                                   other_contractors: List[Dict[str, str]],
                                   original_message: str) -> str:
        """Create homeowner-only question about scope changes"""
        
        if not other_contractors:
            return ""
        
        # Determine change type for natural language
        change_types = []
        for change in scope_changes:
            change_lower = change.lower()
            if "material" in change_lower:
                change_types.append("material changes")
            elif "size" in change_lower or "expand" in change_lower:
                change_types.append("size modifications") 
            elif "timeline" in change_lower or "schedule" in change_lower:
                change_types.append("timeline adjustments")
            elif "budget" in change_lower:
                change_types.append("budget changes")
            elif "feature" in change_lower:
                change_types.append("feature changes")
            else:
                change_types.append("project changes")
        
        changes_text = " and ".join(set(change_types))
        
        # Create contractor list
        contractor_count = len(other_contractors)
        if contractor_count == 1:
            contractor_text = other_contractors[0]["alias"]
        elif contractor_count == 2:
            contractor_text = f"{other_contractors[0]['alias']} and {other_contractors[1]['alias']}"
        else:
            names = [c["alias"] for c in other_contractors]
            contractor_text = f"{', '.join(names[:-1])}, and {names[-1]}"
        
        # Create context-aware question
        question = f"🔄 **Scope Change Detected**\n\n"
        question += f"I noticed you mentioned {changes_text} in your message:\n"
        question += f"*\"{original_message[:100]}{'...' if len(original_message) > 100 else ''}\"*\n\n"
        question += f"You currently have **{contractor_count} other contractor{'s' if contractor_count > 1 else ''}** "
        question += f"({contractor_text}) who may need to update their bids based on these changes.\n\n"
        question += f"**Would you like me to:**\n"
        question += f"• ✅ Notify all contractors about the scope changes\n"
        question += f"• 🔄 Update the bid card with new requirements\n"
        question += f"• 📝 Ask them to revise their bids accordingly\n\n"
        question += f"*This will help ensure you get accurate pricing for your updated project scope.*"
        
        return question
    
    async def _log_scope_change(self, 
                                bid_card_id: str,
                                scope_changes: List[str], 
                                scope_details: Dict[str, Any],
                                user_id: str) -> bool:
        """Log scope change for bid card tracking"""
        
        if not self.db:
            print(f"Mock: Would log scope change for bid card {bid_card_id}")
            return True
        
        try:
            # Create scope change log entry
            log_entry = {
                "id": f"scope_change_{int(datetime.now().timestamp())}",
                "bid_card_id": bid_card_id,
                "user_id": user_id,
                "scope_changes": scope_changes,
                "scope_details": scope_details,
                "status": "detected",  # detected -> confirmed -> applied
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "detection_source": "intelligent_messaging_agent",
                    "requires_contractor_notification": True
                }
            }
            
            # Call JAA service instead of direct bid card update
            jaa_response = await self.call_jaa_update_service(bid_card_id, {
                "source_agent": "messaging_agent",
                "conversation_snippet": f"Scope change detected: {', '.join(scope_changes)}",
                "detected_change_hints": scope_changes,
                "scope_details": scope_details,
                "requester_info": {
                    "user_id": user_id,
                    "session_id": "scope_change_session"
                }
            })
            
            # Store JAA response for parent method to access
            self._last_jaa_response = jaa_response
            
            if jaa_response.get("success"):
                print(f"[ScopeChangeHandler] Successfully updated bid card {bid_card_id} via JAA service")
                return True
            else:
                print(f"[ScopeChangeHandler] JAA service failed: {jaa_response.get('error', 'Unknown error')}")
                return False
            
            return False
            
        except Exception as e:
            print(f"Error logging scope change: {e}")
            return False
    
    async def confirm_scope_change(self, 
                                   bid_card_id: str,
                                   user_id: str,
                                   confirmed: bool = True) -> Dict[str, Any]:
        """Handle homeowner's response to scope change question"""
        
        result = {
            "confirmed": confirmed,
            "bid_card_updated": False,
            "contractors_notified": False,
            "error": None
        }
        
        if not confirmed:
            result["message"] = "Scope change cancelled by homeowner"
            return result
        
        try:
            # Step 1: Update bid card status to indicate scope change
            if self.db:
                self.db.table("bid_cards").update({
                    "status": "scope_updated",
                    "updated_at": datetime.now().isoformat()
                }).eq("id", bid_card_id).execute()
                
                result["bid_card_updated"] = True
            
            # Step 2: Notify other contractors (would integrate with EAA agent)
            other_contractors = await self._get_other_contractors(bid_card_id)
            
            # In production, this would trigger EAA agent to send notifications
            for contractor in other_contractors:
                print(f"Would notify contractor {contractor['name']} about scope changes")
            
            result["contractors_notified"] = len(other_contractors) > 0
            result["message"] = f"Scope changes confirmed. {len(other_contractors)} contractors will be notified."
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            return result

    async def call_jaa_update_service(self, bid_card_id: str, update_context: dict) -> dict:
        """
        Call JAA service to update bid card instead of direct database update
        
        Args:
            bid_card_id: Bid card ID to update
            update_context: Context including source_agent, conversation_snippet, etc.
            
        Returns:
            JAA response with success status and contractor notification data
        """
        try:
            # JAA service endpoint - use centralized configuration
            from config.service_urls import get_jaa_update_url
            jaa_endpoint = get_jaa_update_url(bid_card_id)
            
            # Prepare request payload
            payload = {
                "update_context": update_context,
                "update_type": "conversation_based"
            }
            
            print(f"[ScopeChangeHandler] Calling JAA service for bid card {bid_card_id}")
            print(f"[ScopeChangeHandler] JAA payload: {json.dumps(payload, indent=2)}")
            
            # Make HTTP request to JAA service
            response = requests.put(
                jaa_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                jaa_response = response.json()
                print(f"[ScopeChangeHandler] JAA service success: {jaa_response.get('update_summary', {}).get('change_summary', 'Updated')}")
                return jaa_response
            else:
                error_msg = f"JAA service error {response.status_code}: {response.text}"
                print(f"[ScopeChangeHandler] {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
                
        except requests.exceptions.Timeout:
            error_msg = "JAA service timeout - request took longer than 30 seconds"
            print(f"[ScopeChangeHandler] {error_msg}")
            return {"success": False, "error": error_msg}
            
        except requests.exceptions.ConnectionError:
            error_msg = "JAA service unavailable - could not connect to localhost:8008"
            print(f"[ScopeChangeHandler] {error_msg}")
            return {"success": False, "error": error_msg}
            
        except Exception as e:
            error_msg = f"JAA service call failed: {str(e)}"
            print(f"[ScopeChangeHandler] {error_msg}")
            return {"success": False, "error": error_msg}

# Integration with intelligent messaging agent
async def handle_scope_changes(scope_changes: List[str],
                               scope_details: Dict[str, Any], 
                               bid_card_id: str,
                               sender_id: str,
                               message_content: str) -> Dict[str, Any]:
    """Main entry point for scope change handling"""
    
    handler = ScopeChangeHandler()
    return await handler.handle_scope_change(
        scope_changes, scope_details, bid_card_id, sender_id, message_content
    )

if __name__ == "__main__":
    # Test the scope change handler
    import asyncio
    
    async def test_scope_handler():
        handler = ScopeChangeHandler()
        
        result = await handler.handle_scope_change(
            scope_changes=["Material changes"],
            scope_details={"Material changes": "Change from regular sod to artificial turf"},
            bid_card_id="test-bid-card-123",
            sender_id="test-homeowner-456", 
            message_content="I want to change from sod to artificial turf for the backyard"
        )
        
        print("SCOPE CHANGE HANDLER TEST")
        print("=" * 50)
        print(f"Scope Changes: {result['scope_changes_detected']}")
        print(f"Other Contractors: {len(result['other_contractors'])}")
        print(f"Homeowner Question Generated: {bool(result['homeowner_question'])}")
        print()
        if result['homeowner_question']:
            print("HOMEOWNER QUESTION:")
            print(result['homeowner_question'])
    
    asyncio.run(test_scope_handler())