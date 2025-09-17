"""
Contractor Context Adapter for Privacy Framework
Provides privacy-filtered context for contractor-side agents (COIA)
Uses direct Supabase queries to avoid server timeouts
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from supabase import Client, create_client
from dotenv import load_dotenv

load_dotenv(override=True)
logger = logging.getLogger(__name__)

class ContractorContextAdapter:
    """Context adapter for contractor-side agents with privacy filtering"""
    
    def __init__(self):
        """Initialize with Supabase connection"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase not available - context will be limited")
            self.supabase = None
        else:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Contractor context adapter initialized with Supabase")

    def get_contractor_context(
        self, 
        contractor_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive context for contractor agents with privacy filtering"""
        
        context = {
            # Core contractor data
            "contractor_profile": self._get_contractor_profile(contractor_id),
            
            # Bid card and project data
            "available_projects": self._get_available_projects(contractor_id),
            "bid_history": self._get_bid_history(contractor_id),
            "submitted_bids": self.get_contractor_bids(contractor_id),
            
            # Communication and messaging
            "conversation_history": self._get_conversation_history(contractor_id, session_id),
            "contractor_messages": self.get_contractor_messages(contractor_id),
            "contractor_responses": self.get_contractor_responses(contractor_id),
            
            # Campaign and outreach data
            "campaign_data": self._get_campaign_data(contractor_id),
            "outreach_history": self._get_outreach_history(contractor_id),
            
            # Discovery and networking - removed (not relevant for contractor context)
            
            # Performance metrics
            "engagement_summary": self._get_engagement_summary(contractor_id),
            
            # AI-extracted insights (NEW)
            "ai_memory": self._get_ai_memory(contractor_id),
            "bidding_patterns": self._get_bidding_patterns(contractor_id),
            "relationship_insights": self._get_relationship_insights(contractor_id),
            
            # Privacy metadata
            "privacy_level": "contractor_side_filtered",
            "adapter_version": "2.1_with_ai_memory"
        }
        
        logger.info(f"Retrieved comprehensive contractor context for contractor {contractor_id} - {len(context)} data sources")
        return context
    
    def _is_valid_uuid(self, uuid_string: str) -> bool:
        """Check if string is a valid UUID format"""
        try:
            uuid.UUID(uuid_string)
            return True
        except (ValueError, TypeError):
            return False

    def _get_contractor_profile(self, contractor_id: str) -> Dict[str, Any]:
        """Get contractor profile information"""
        if not self.supabase:
            return {"contractor_id": contractor_id, "profile_available": False}
        
        # Quick UUID validation to prevent database errors
        if not self._is_valid_uuid(contractor_id):
            return {"contractor_id": contractor_id, "profile_available": False, "error": "Invalid UUID format"}
            
        try:
            # Try contractors table first
            result = self.supabase.table("contractors").select("*").eq("id", contractor_id).execute()
            
            if result.data:
                contractor = result.data[0]
                return {
                    "contractor_id": contractor_id,
                    "company_name": contractor.get("company_name"),
                    "rating": contractor.get("rating"),
                    "verified": contractor.get("verified", False),
                    "tier": contractor.get("tier", 3),
                    "total_jobs": contractor.get("total_jobs", 0),
                    "profile_available": True
                }
            else:
                # Try contractor_leads table
                result = self.supabase.table("contractor_leads").select("*").eq("id", contractor_id).execute()
                
                if result.data:
                    lead = result.data[0]
                    return {
                        "contractor_id": contractor_id,
                        "company_name": lead.get("company_name"),
                        "contact_name": lead.get("contact_name"),
                        "specialties": lead.get("specialties", []),
                        "years_in_business": lead.get("years_in_business"),
                        "profile_available": True
                    }
                    
        except Exception as e:
            logger.error(f"Error getting contractor profile: {e}")
            
        return {"contractor_id": contractor_id, "profile_available": False}

    def _get_available_projects(self, contractor_id: str) -> list:
        """Get projects THIS CONTRACTOR has interacted with (viewed, bid on, or invited to)"""
        if not self.supabase:
            return []
        
        if not self._is_valid_uuid(contractor_id):
            return []
            
        try:
            projects = []
            
            # 1. Get bid cards where this contractor has submitted bids
            bid_cards_with_bids = self.supabase.table("bid_cards").select("*").execute()
            
            for bid_card in bid_cards_with_bids.data or []:
                bid_document = bid_card.get("bid_document")
                if bid_document and isinstance(bid_document, dict):
                    submitted_bids = bid_document.get("submitted_bids", [])
                    # Check if this contractor has bid on this card
                    for bid in submitted_bids:
                        if bid.get("contractor_id") == contractor_id:
                            projects.append({
                                "bid_card_id": bid_card["id"],
                                "project_type": bid_card.get("project_type"),
                                "budget_range": f"${bid_card.get('budget_min', 0)}-${bid_card.get('budget_max', 0)}",
                                "timeline": bid_card.get("timeline"),
                                "location": bid_card.get("location_city", "Not specified"),
                                "description": bid_card.get("project_description", ""),
                                "interaction_type": "bid_submitted",
                                "homeowner": "Project Owner",  # Privacy filter
                                "privacy_filtered": True
                            })
                            break
            
            # 2. Get bid cards this contractor has viewed
            viewed = self.supabase.table("bid_card_views").select("bid_card_id").eq("contractor_id", contractor_id).execute()
            viewed_ids = [v["bid_card_id"] for v in viewed.data or []]
            
            if viewed_ids:
                viewed_cards = self.supabase.table("bid_cards").select("*").in_("id", viewed_ids).execute()
                for bid_card in viewed_cards.data or []:
                    # Don't duplicate if already added from bids
                    if not any(p["bid_card_id"] == bid_card["id"] for p in projects):
                        projects.append({
                            "bid_card_id": bid_card["id"],
                            "project_type": bid_card.get("project_type"),
                            "budget_range": f"${bid_card.get('budget_min', 0)}-${bid_card.get('budget_max', 0)}",
                            "timeline": bid_card.get("timeline"),
                            "location": bid_card.get("location_city", "Not specified"),
                            "description": bid_card.get("project_description", ""),
                            "interaction_type": "viewed",
                            "homeowner": "Project Owner",  # Privacy filter
                            "privacy_filtered": True
                        })
            
            # 3. Get bid cards from campaigns this contractor is part of
            campaigns = self.supabase.table("campaign_contractors").select("*, outreach_campaigns(bid_card_id)").eq("contractor_id", contractor_id).execute()
            campaign_bid_card_ids = [c["outreach_campaigns"]["bid_card_id"] for c in campaigns.data or [] if c.get("outreach_campaigns")]
            
            if campaign_bid_card_ids:
                campaign_cards = self.supabase.table("bid_cards").select("*").in_("id", campaign_bid_card_ids).execute()
                for bid_card in campaign_cards.data or []:
                    # Don't duplicate
                    if not any(p["bid_card_id"] == bid_card["id"] for p in projects):
                        projects.append({
                            "bid_card_id": bid_card["id"],
                            "project_type": bid_card.get("project_type"),
                            "budget_range": f"${bid_card.get('budget_min', 0)}-${bid_card.get('budget_max', 0)}",
                            "timeline": bid_card.get("timeline"),
                            "location": bid_card.get("location_city", "Not specified"),
                            "description": bid_card.get("project_description", ""),
                            "interaction_type": "invited",
                            "homeowner": "Project Owner",  # Privacy filter
                            "privacy_filtered": True
                        })
            
            return projects
            
        except Exception as e:
            logger.error(f"Error getting contractor's interacted projects: {e}")
            return []

    def _get_bid_history(self, contractor_id: str) -> list:
        """Get contractor's bidding history"""
        if not self.supabase:
            return []
        
        if not self._is_valid_uuid(contractor_id):
            return []
            
        try:
            # Get bids from bid_cards where contractor submitted
            result = self.supabase.table("bid_cards").select("*").execute()
            
            bids = []
            for bid_card in result.data or []:
                bid_document = bid_card.get("bid_document")
                if not bid_document or not isinstance(bid_document, dict):
                    continue
                submitted_bids = bid_document.get("submitted_bids", [])
                
                for bid in submitted_bids:
                    if bid.get("contractor_id") == contractor_id:
                        bids.append({
                            "bid_card_id": bid_card["id"],
                            "project_type": bid_card.get("project_type"),
                            "bid_amount": bid.get("bid_amount"),
                            "timeline": bid.get("timeline"),
                            "selected": bid.get("selected", False),
                            "submitted_at": bid.get("submitted_at"),
                            "homeowner": "Project Owner"  # Privacy filter
                        })
            
            return bids
            
        except Exception as e:
            logger.error(f"Error getting bid history: {e}")
            return []

    def _get_conversation_history(self, contractor_id: str, session_id: Optional[str]) -> list:
        """Get contractor's conversation history with privacy filtering"""
        if not self.supabase:
            return []
        
        if not self._is_valid_uuid(contractor_id):
            return []
            
        try:
            # Get conversations from both COIA and BSA agents
            query = self.supabase.table("unified_conversations").select("*").eq("created_by", contractor_id)
            # Filter for contractor-relevant agents (COIA, BSA)
            query = query.in_("metadata->>agent_type", ["COIA", "BSA"])
            
            if session_id:
                query = query.eq("metadata->>session_id", session_id)
                
            result = query.order("created_at", desc=True).limit(10).execute()
            
            conversations = []
            for conv in result.data or []:
                metadata = conv.get("metadata", {})
                state = metadata.get("state", {})
                conversations.append({
                    "thread_id": metadata.get("session_id", conv["id"]),
                    "created_at": conv["created_at"],
                    "summary": self._extract_conversation_summary(state),
                    "agent_type": metadata.get("agent_type"),  # Include agent_type for BSA context endpoint
                    "privacy_filtered": True
                })
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []

    def _extract_conversation_summary(self, state_data: Dict[str, Any]) -> str:
        """Extract a summary from conversation state"""
        if not state_data:
            return "No summary available"
            
        current_stage = state_data.get("current_stage", "unknown")
        message_count = len(state_data.get("messages", []))
        
        return f"Stage: {current_stage}, Messages: {message_count}"

    def _get_potential_contractors(self, contractor_id: str) -> list:
        """Get potential contractors for campaigns"""
        if not self.supabase:
            return []
            
        try:
            # Get potential contractors (for campaign suggestions)
            result = self.supabase.table("potential_contractors").select("*").limit(10).execute()
            
            contractors = []
            for contractor in result.data or []:
                contractors.append({
                    "id": contractor.get("id"),
                    "company_name": contractor.get("contractor_data", {}).get("company_name"),
                    "match_score": contractor.get("match_score"),
                    "specialties": contractor.get("contractor_data", {}).get("specialties", []),
                    "discovery_source": contractor.get("source_url")
                })
            
            return contractors
            
        except Exception as e:
            logger.error(f"Error getting potential contractors: {e}")
            return []

    def _get_campaign_data(self, contractor_id: str) -> list:
        """Get campaign participation data"""
        if not self.supabase:
            return []
        
        if not self._is_valid_uuid(contractor_id):
            return []
            
        try:
            # Get campaigns this contractor is part of
            result = self.supabase.table("campaign_contractors").select(
                "*, outreach_campaigns(*)"
            ).eq("contractor_id", contractor_id).execute()
            
            campaigns = []
            for campaign_contractor in result.data or []:
                campaign = campaign_contractor.get("outreach_campaigns", {})
                campaigns.append({
                    "campaign_id": campaign.get("id"),
                    "bid_card_id": campaign.get("bid_card_id"),
                    "assigned_at": campaign_contractor.get("assigned_at"),
                    "status": campaign.get("status"),
                    "max_contractors": campaign.get("max_contractors"),
                    "responses_received": campaign.get("responses_received")
                })
            
            return campaigns
            
        except Exception as e:
            logger.error(f"Error getting campaign data: {e}")
            return []

    def _get_outreach_history(self, contractor_id: str) -> list:
        """Get outreach attempts directed at this contractor"""
        if not self.supabase:
            return []
        
        if not self._is_valid_uuid(contractor_id):
            return []
            
        try:
            # First check if contractor_id is in contractor_leads
            lead_result = self.supabase.table("contractor_leads").select("id").eq("id", contractor_id).execute()
            
            if lead_result.data:
                # Get outreach attempts
                result = self.supabase.table("contractor_outreach_attempts").select("*").eq(
                    "contractor_lead_id", contractor_id
                ).order("sent_at", desc=True).limit(10).execute()
                
                outreach = []
                for attempt in result.data or []:
                    outreach.append({
                        "bid_card_id": attempt.get("bid_card_id"),
                        "campaign_id": attempt.get("campaign_id"),
                        "channel": attempt.get("channel"),
                        "status": attempt.get("status"),
                        "sent_at": attempt.get("sent_at"),
                        "message_preview": attempt.get("message_content", "")[:100]
                    })
                
                return outreach
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting outreach history: {e}")
            return []

    def _get_engagement_summary(self, contractor_id: str) -> Dict[str, Any]:
        """Get contractor engagement metrics"""
        if not self.supabase:
            return {}
        
        if not self._is_valid_uuid(contractor_id):
            return {}
            
        try:
            # Get engagement summary
            result = self.supabase.table("contractor_engagement_summary").select("*").eq(
                "contractor_lead_id", contractor_id
            ).execute()
            
            if result.data:
                summary = result.data[0]
                return {
                    "total_campaigns": summary.get("total_campaigns", 0),
                    "response_rate": summary.get("response_rate", 0),
                    "avg_response_time": summary.get("avg_response_time"),
                    "total_bids_submitted": summary.get("total_bids_submitted", 0),
                    "win_rate": summary.get("win_rate", 0),
                    "last_engagement": summary.get("last_engagement_date")
                }
            
            return {
                "total_campaigns": 0,
                "response_rate": 0,
                "total_bids_submitted": 0
            }
            
        except Exception as e:
            logger.error(f"Error getting engagement summary: {e}")
            return {}
    
    def get_contractor_bids(self, contractor_id: str) -> list:
        """Get all bids submitted by this contractor"""
        if not self.supabase:
            return []
        
        if not self._is_valid_uuid(contractor_id):
            return []
            
        try:
            # Get from contractor_bids table
            result = self.supabase.table("contractor_bids").select(
                "*, bid_cards(*)"
            ).eq("contractor_id", contractor_id).execute()
            
            bids = []
            for bid in result.data or []:
                bid_card = bid.get("bid_cards", {}) if bid.get("bid_cards") else {}
                bid_amount = bid.get("bid_amount")
                if bid_amount is None:
                    bid_amount = 0
                bids.append({
                    "bid_id": bid.get("id"),
                    "bid_card_id": bid.get("bid_card_id"),
                    "project_type": bid_card.get("project_type") if bid_card else None,
                    "bid_amount": bid_amount,
                    "timeline": bid.get("timeline"),
                    "status": bid.get("status"),
                    "submitted_at": bid.get("created_at"),
                    "location": f"{bid_card.get('location_city', '')}, {bid_card.get('location_state', '')}" if bid_card else "",
                    "privacy_filtered": True
                })
            
            return bids
            
        except Exception as e:
            logger.error(f"Error getting contractor bids: {e}")
            return []
    
    def get_contractor_responses(self, contractor_id: str) -> list:
        """Get contractor's responses to outreach"""
        if not self.supabase:
            return []
        
        if not self._is_valid_uuid(contractor_id):
            return []
            
        try:
            result = self.supabase.table("contractor_responses").select("*").eq(
                "contractor_id", contractor_id
            ).order("received_at", desc=True).limit(10).execute()
            
            responses = []
            for response in result.data or []:
                responses.append({
                    "bid_card_id": response.get("bid_card_id"),
                    "response_type": response.get("response_type"),
                    "responded_at": response.get("received_at"),  # Map to received_at
                    "response_content": response.get("message"),  # Map to message field
                    "interested": response.get("interest_level", 0) > 5,  # Convert interest level
                    "is_hot_lead": response.get("is_hot_lead", False),
                    "urgency_detected": response.get("urgency_detected", False)
                })
            
            return responses
            
        except Exception as e:
            logger.error(f"Error getting contractor responses: {e}")
            return []
    
    def get_contractor_messages(self, contractor_id: str) -> list:
        """Get messages between contractor and homeowners"""
        if not self.supabase:
            return []
        
        if not self._is_valid_uuid(contractor_id):
            return []
            
        try:
            # Get messages where contractor is sender or recipient
            result = self.supabase.table("messages").select("*").or_(
                f"sender_id.eq.{contractor_id},recipient_id.eq.{contractor_id}"
            ).order("created_at", desc=True).limit(20).execute()
            
            messages = []
            for msg in result.data or []:
                # Privacy filter - don't expose homeowner identity
                messages.append({
                    "message_id": msg.get("id"),
                    "bid_card_id": msg.get("bid_card_id"),
                    "content": msg.get("content"),
                    "sent_at": msg.get("created_at"),
                    "is_from_contractor": msg.get("sender_id") == contractor_id,
                    "homeowner": "Project Owner"  # Privacy filtered
                })
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting contractor messages: {e}")
            return []
    
    def search_bid_cards_for_contractor(self, contractor_id: str, filters: Dict[str, Any] = None) -> list:
        """Search bid cards relevant to contractor with privacy filtering"""
        if not self.supabase:
            return []
            
        try:
            # Build query for bid cards
            query = self.supabase.table("bid_cards").select("*")
            
            # Apply status filter - only active/collecting bids
            query = query.in_("status", ["active", "collecting_bids", "generated"])
            
            # Apply additional filters if provided
            if filters:
                if filters.get("project_type"):
                    query = query.eq("project_type", filters["project_type"])
                if filters.get("location_city"):
                    query = query.eq("location_city", filters["location_city"])
                if filters.get("budget_min"):
                    query = query.gte("budget_max", filters["budget_min"])
                if filters.get("budget_max"):
                    query = query.lte("budget_min", filters["budget_max"])
            
            result = query.order("created_at", desc=True).limit(20).execute()
            
            bid_cards = []
            for card in result.data or []:
                # Apply privacy filtering
                bid_cards.append({
                    "bid_card_id": card.get("id"),
                    "bid_card_number": card.get("bid_card_number"),
                    "project_type": card.get("project_type"),
                    "budget_range": f"${card.get('budget_min', 0)}-${card.get('budget_max', 0)}",
                    "timeline": card.get("timeline"),
                    "location": f"{card.get('location_city', '')}, {card.get('location_state', '')}",
                    "urgency_level": card.get("urgency_level"),
                    "description": card.get("project_description", ""),
                    "contractor_count_needed": card.get("contractor_count_needed", 4),
                    "bids_received_count": card.get("bids_received_count", 0),
                    "homeowner": "Project Owner",  # Privacy filtered
                    "privacy_filtered": True
                })
            
            return bid_cards
            
        except Exception as e:
            logger.error(f"Error searching bid cards: {e}")
            return []
    
    # ============== WRITE OPERATIONS ==============
    
    def save_conversation(self, contractor_id: str, session_id: str, conversation_data: Dict[str, Any]) -> bool:
        """Save conversation to unified_conversations table"""
        if not self.supabase:
            return False
            
        try:
            # Prepare conversation record
            record = {
                "id": str(uuid.uuid4()) if not conversation_data.get("id") else conversation_data["id"],
                "created_by": contractor_id,
                "conversation_type": "contractor_chat",  # Required field
                "metadata": {
                    "session_id": session_id,
                    "agent_type": "COIA",
                    "state": conversation_data.get("state", {}),
                    "current_mode": conversation_data.get("current_mode", "conversation"),
                    "contractor_profile": conversation_data.get("contractor_profile", {})
                },
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Upsert conversation
            result = self.supabase.table("unified_conversations").upsert(record).execute()
            
            if result.data:
                logger.info(f"Saved conversation for contractor {contractor_id}, session {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            return False
    
    def submit_bid(self, contractor_id: str, bid_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a bid for a project"""
        if not self.supabase:
            return {"success": False, "error": "Database not available"}
            
        try:
            # Create bid record
            bid_record = {
                "id": str(uuid.uuid4()),
                "contractor_id": contractor_id,
                "bid_card_id": bid_data["bid_card_id"],
                "bid_amount": bid_data.get("bid_amount"),
                "timeline": bid_data.get("timeline"),
                "proposal_text": bid_data.get("proposal"),
                "status": "submitted",
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Insert into contractor_bids
            result = self.supabase.table("contractor_bids").insert(bid_record).execute()
            
            if result.data:
                logger.info(f"Submitted bid for contractor {contractor_id} on bid card {bid_data['bid_card_id']}")
                
                # Also update bid_cards table bid_document
                self._update_bid_card_with_bid(bid_data["bid_card_id"], contractor_id, bid_data)
                
                return {"success": True, "bid_id": bid_record["id"]}
            
            return {"success": False, "error": "Failed to submit bid"}
            
        except Exception as e:
            logger.error(f"Error submitting bid: {e}")
            return {"success": False, "error": str(e)}
    
    def _update_bid_card_with_bid(self, bid_card_id: str, contractor_id: str, bid_data: Dict[str, Any]):
        """Update bid_cards.bid_document with new bid"""
        try:
            # Get current bid card
            result = self.supabase.table("bid_cards").select("bid_document").eq("id", bid_card_id).execute()
            
            if result.data:
                bid_document = result.data[0].get("bid_document", {})
                if not bid_document:
                    bid_document = {"submitted_bids": []}
                
                # Add new bid
                new_bid = {
                    "contractor_id": contractor_id,
                    "bid_amount": bid_data.get("bid_amount"),
                    "timeline": bid_data.get("timeline"),
                    "proposal": bid_data.get("proposal"),
                    "submitted_at": datetime.utcnow().isoformat()
                }
                
                bid_document.setdefault("submitted_bids", []).append(new_bid)
                bid_document["bids_received_count"] = len(bid_document["submitted_bids"])
                
                # Update bid card
                self.supabase.table("bid_cards").update({
                    "bid_document": bid_document,
                    "bids_received_count": bid_document["bids_received_count"]
                }).eq("id", bid_card_id).execute()
                
                logger.info(f"Updated bid card {bid_card_id} with new bid")
                
        except Exception as e:
            logger.error(f"Error updating bid card: {e}")
    
    def save_contractor_response(self, contractor_id: str, response_data: Dict[str, Any]) -> bool:
        """Save contractor response to outreach"""
        if not self.supabase:
            return False
            
        try:
            record = {
                "id": str(uuid.uuid4()),
                "contractor_id": contractor_id,
                "bid_card_id": response_data.get("bid_card_id"),
                "response_type": response_data.get("response_type", "interested"),
                "message": response_data.get("message", ""),
                "interest_level": response_data.get("interest_level", 5),
                "received_at": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("contractor_responses").insert(record).execute()
            
            if result.data:
                logger.info(f"Saved response from contractor {contractor_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error saving contractor response: {e}")
            return False
    
    def update_contractor_profile(self, contractor_id: str, profile_data: Dict[str, Any]) -> bool:
        """Update contractor profile information"""
        if not self.supabase:
            return False
            
        try:
            # Update contractors table
            update_data = {
                "company_name": profile_data.get("company_name"),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            result = self.supabase.table("contractors").update(update_data).eq("id", contractor_id).execute()
            
            if result.data:
                logger.info(f"Updated profile for contractor {contractor_id}")
                
                # Also update contractor_leads if exists
                self._update_contractor_lead_profile(contractor_id, profile_data)
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating contractor profile: {e}")
            return False
    
    def _update_contractor_lead_profile(self, contractor_id: str, profile_data: Dict[str, Any]):
        """Update contractor_leads table with profile data"""
        try:
            # Check if contractor exists in contractor_leads
            result = self.supabase.table("contractor_leads").select("id").eq("id", contractor_id).execute()
            
            if result.data:
                # Update contractor_leads
                update_data = {
                    "company_name": profile_data.get("company_name"),
                    "phone": profile_data.get("phone"),
                    "email": profile_data.get("email"),
                    "website": profile_data.get("website"),
                    "specialties": profile_data.get("specialties"),
                    "years_in_business": profile_data.get("years_in_business"),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                # Remove None values
                update_data = {k: v for k, v in update_data.items() if v is not None}
                
                self.supabase.table("contractor_leads").update(update_data).eq("id", contractor_id).execute()
                logger.info(f"Updated contractor_leads profile for {contractor_id}")
                
        except Exception as e:
            logger.error(f"Error updating contractor_leads: {e}")
    
    def _get_ai_memory(self, contractor_id: str) -> Dict[str, Any]:
        """Get AI-extracted memory insights for contractor"""
        if not self.supabase:
            return {}
        
        if not self._is_valid_uuid(contractor_id):
            return {}
            
        try:
            result = self.supabase.table("contractor_ai_memory").select("memory_data").eq(
                "contractor_id", contractor_id
            ).execute()
            
            if result.data:
                return result.data[0].get("memory_data", {})
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting AI memory: {e}")
            return {}
    
    def _get_bidding_patterns(self, contractor_id: str) -> Dict[str, Any]:
        """Get contractor bidding patterns from AI analysis"""
        if not self.supabase:
            return {}
        
        if not self._is_valid_uuid(contractor_id):
            return {}
            
        try:
            result = self.supabase.table("contractor_bidding_patterns").select("*").eq(
                "contractor_id", contractor_id
            ).execute()
            
            if result.data:
                pattern = result.data[0]
                return {
                    "avg_bid_amount": pattern.get("avg_bid_amount"),
                    "bid_frequency": pattern.get("bid_frequency"),
                    "preferred_project_types": pattern.get("preferred_project_types", []),
                    "typical_timeline": pattern.get("typical_timeline"),
                    "pricing_strategy": pattern.get("pricing_strategy"),
                    "competitive_positioning": pattern.get("competitive_positioning")
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting bidding patterns: {e}")
            return {}
    
    def _get_relationship_insights(self, contractor_id: str) -> Dict[str, Any]:
        """Get contractor relationship insights from AI analysis"""
        if not self.supabase:
            return {}
        
        if not self._is_valid_uuid(contractor_id):
            return {}
            
        try:
            result = self.supabase.table("contractor_relationship_memory").select("*").eq(
                "contractor_id", contractor_id
            ).execute()
            
            if result.data:
                insights = result.data[0]
                return {
                    "communication_style": insights.get("communication_style"),
                    "work_preferences": insights.get("work_preferences", []),
                    "relationship_quality": insights.get("relationship_quality"),
                    "personality_traits": insights.get("personality_traits", []),
                    "engagement_level": insights.get("engagement_level"),
                    "trust_indicators": insights.get("trust_indicators", [])
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting relationship insights: {e}")
            return {}