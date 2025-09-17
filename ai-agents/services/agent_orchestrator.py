#!/usr/bin/env python3
"""
Agent Orchestrator Service
Coordinates backend agents for contractor outreach
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4

from database_simple import db

# Import the actual agents
from agents.eaa.agent import ExternalAcquisitionAgent
try:
    from agents.wfa.agent import WebsiteFormAutomationAgent
    WFA_AVAILABLE = True
except ImportError:
    print("WFA agent not available - Playwright dependency missing")
    WebsiteFormAutomationAgent = None
    WFA_AVAILABLE = False

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates agent actions for contractor outreach"""
    
    def __init__(self):
        """Initialize the orchestrator with agent instances"""
        try:
            self.eaa = ExternalAcquisitionAgent()
            if WFA_AVAILABLE:
                self.wfa = WebsiteFormAutomationAgent()
                logger.info("Agent Orchestrator initialized with EAA and WFA")
            else:
                self.wfa = None
                logger.info("Agent Orchestrator initialized with EAA only (WFA disabled)")
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            self.eaa = None
            self.wfa = None
    
    async def get_contractor_details(self, contractor_id: str) -> Dict[str, Any]:
        """Get contractor details from database"""
        try:
            # Try contractors table first
            result = db.client.table("contractors").select("*").eq("id", contractor_id).single().execute()
            if result.data:
                return result.data
        except:
            pass
        
        try:
            # Try contractor_leads table
            result = db.client.table("contractor_leads").select("*").eq("id", contractor_id).single().execute()
            if result.data:
                return result.data
        except:
            pass
        
        logger.warning(f"Contractor {contractor_id} not found in either table")
        return {}
    
    async def get_campaign_details(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign and bid card details"""
        try:
            # Get campaign with bid card info
            result = db.client.table("outreach_campaigns")\
                .select("""
                    *,
                    bid_cards!inner(
                        bid_card_number,
                        project_type,
                        urgency_level,
                        budget_min,
                        budget_max,
                        project_description,
                        location_city,
                        location_state
                    )
                """)\
                .eq("id", campaign_id)\
                .single()\
                .execute()
            
            if result.data:
                return result.data
            
        except Exception as e:
            logger.error(f"Failed to get campaign details: {e}")
        
        return {}
    
    async def trigger_contractor_outreach(
        self,
        contractor_id: str,
        campaign_id: str,
        channel: str = "auto"
    ) -> Dict[str, Any]:
        """
        Trigger appropriate agent based on contractor data
        
        Args:
            contractor_id: ID of the contractor
            campaign_id: ID of the campaign
            channel: "auto", "email", "form", or "both"
            
        Returns:
            Dictionary with outreach results
        """
        logger.info(f"Triggering outreach for contractor {contractor_id} in campaign {campaign_id}")
        
        # Get contractor and campaign details
        contractor = await self.get_contractor_details(contractor_id)
        campaign = await self.get_campaign_details(campaign_id)
        
        if not contractor or not campaign:
            logger.error(f"Missing data - Contractor: {bool(contractor)}, Campaign: {bool(campaign)}")
            return {
                "contractor_id": contractor_id,
                "campaign_id": campaign_id,
                "status": "failed",
                "error": "Missing contractor or campaign data",
                "actions": []
            }
        
        results = {
            "contractor_id": contractor_id,
            "campaign_id": campaign_id,
            "contractor_name": contractor.get("company_name", "Unknown"),
            "campaign_name": campaign.get("name", "Unknown"),
            "status": "success",
            "actions": []
        }
        
        bid_card = campaign.get("bid_cards", {})
        
        # Email outreach
        if contractor.get("email") and channel in ["auto", "email", "both"]:
            try:
                if self.eaa:
                    logger.info(f"Sending email to {contractor['email']}")
                    
                    # Prepare email data
                    email_data = {
                        "contractor": contractor,
                        "bid_card": bid_card,
                        "project_type": bid_card.get("project_type", "general"),
                        "urgency": bid_card.get("urgency_level", "standard"),
                        "location": f"{bid_card.get('location_city', '')}, {bid_card.get('location_state', '')}",
                        "budget_range": f"${bid_card.get('budget_min', 0):,} - ${bid_card.get('budget_max', 0):,}"
                    }
                    
                    # Call EAA agent
                    email_result = await self.eaa.send_personalized_email(
                        contractor_email=contractor["email"],
                        contractor_name=contractor.get("company_name", "Contractor"),
                        project_details=email_data
                    )
                    
                    results["actions"].append({
                        "type": "email",
                        "status": "success" if email_result else "failed",
                        "recipient": contractor["email"],
                        "timestamp": datetime.now().isoformat(),
                        "details": str(email_result) if email_result else "Email send failed"
                    })
                else:
                    logger.warning("EAA agent not initialized")
                    results["actions"].append({
                        "type": "email",
                        "status": "skipped",
                        "reason": "EAA agent not available"
                    })
                    
            except Exception as e:
                logger.error(f"Email outreach failed: {e}")
                results["actions"].append({
                    "type": "email",
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Website form outreach
        if contractor.get("website") and channel in ["auto", "form", "both"]:
            try:
                if self.wfa:
                    logger.info(f"Filling form at {contractor['website']}")
                    
                    # Prepare form data
                    form_data = {
                        "project_type": bid_card.get("project_type", "general"),
                        "project_description": bid_card.get("project_description", ""),
                        "timeline": bid_card.get("urgency_level", "standard"),
                        "budget": f"${bid_card.get('budget_min', 0):,} - ${bid_card.get('budget_max', 0):,}",
                        "location": f"{bid_card.get('location_city', '')}, {bid_card.get('location_state', '')}",
                        "contact_name": "InstaBids Platform",
                        "contact_email": "projects@instabids.com",
                        "contact_phone": "1-800-INSTABID"
                    }
                    
                    # Call WFA agent
                    form_result = await self.wfa.fill_contractor_form(
                        website_url=contractor["website"],
                        form_data=form_data
                    )
                    
                    results["actions"].append({
                        "type": "form",
                        "status": "success" if form_result else "failed",
                        "website": contractor["website"],
                        "timestamp": datetime.now().isoformat(),
                        "details": str(form_result) if form_result else "Form fill failed"
                    })
                else:
                    logger.warning("WFA agent not initialized")
                    results["actions"].append({
                        "type": "form",
                        "status": "skipped",
                        "reason": "WFA agent not available"
                    })
                    
            except Exception as e:
                logger.error(f"Form outreach failed: {e}")
                results["actions"].append({
                    "type": "form",
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Store audit log
        await self.store_agent_action_log(results)
        
        return results
    
    async def store_agent_action_log(self, results: Dict[str, Any]):
        """Store agent action results for audit trail"""
        try:
            # Store in a new agent_action_logs table (or use existing tables)
            for action in results.get("actions", []):
                log_entry = {
                    "id": str(uuid4()),
                    "contractor_id": results["contractor_id"],
                    "campaign_id": results["campaign_id"],
                    "agent_type": "EAA" if action["type"] == "email" else "WFA",
                    "action_type": action["type"],
                    "status": action["status"],
                    "details": action.get("details", ""),
                    "error": action.get("error"),
                    "created_at": action.get("timestamp", datetime.now().isoformat())
                }
                
                # Try to store in contractor_outreach_attempts (existing table)
                outreach_attempt = {
                    "id": str(uuid4()),
                    "campaign_id": results["campaign_id"],
                    "contractor_lead_id": results["contractor_id"],
                    "channel": action["type"],
                    "status": "sent" if action["status"] == "success" else "failed",
                    "message_content": f"Agent: {action['type']} - Status: {action['status']}",
                    "sent_at": action.get("timestamp", datetime.now().isoformat())
                }
                
                # Add bid_card_id if available
                if "bid_card_id" in results:
                    outreach_attempt["bid_card_id"] = results["bid_card_id"]
                
                db.client.table("contractor_outreach_attempts").insert(outreach_attempt).execute()
                logger.info(f"Stored audit log for {action['type']} action")
                
        except Exception as e:
            logger.error(f"Failed to store audit log: {e}")
    
    async def batch_trigger_outreach(
        self,
        contractor_ids: List[str],
        campaign_id: str,
        channel: str = "auto"
    ) -> List[Dict[str, Any]]:
        """
        Trigger outreach for multiple contractors
        
        Args:
            contractor_ids: List of contractor IDs
            campaign_id: Campaign ID
            channel: Outreach channel preference
            
        Returns:
            List of results for each contractor
        """
        results = []
        
        for contractor_id in contractor_ids:
            try:
                result = await self.trigger_contractor_outreach(
                    contractor_id,
                    campaign_id,
                    channel
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to trigger outreach for {contractor_id}: {e}")
                results.append({
                    "contractor_id": contractor_id,
                    "campaign_id": campaign_id,
                    "status": "error",
                    "error": str(e),
                    "actions": []
                })
        
        return results


# Singleton instance
orchestrator = AgentOrchestrator()