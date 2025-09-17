"""
Outreach Campaign Orchestrator
Manages multi-channel contractor outreach campaigns
Coordinates Email, SMS, WFA, and manual follow-ups
"""

import json
import os

# Import service role database client and error handler
import sys
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from dotenv import load_dotenv


sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from .error_handler import ErrorSeverity, error_handler


class OutreachChannel(Enum):
    """Available outreach channels"""
    EMAIL = "email"
    SMS = "sms"
    WEBSITE_FORM = "website_form"
    PHONE = "phone"
    MANUAL = "manual"


class CampaignStatus(Enum):
    """Campaign status tracking"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class OutreachCampaignOrchestrator:
    """Orchestrates multi-channel outreach campaigns"""

    def __init__(self):
        """Initialize orchestrator with connections to all systems"""
        load_dotenv(override=True)
        # Initialize service role client for backend operations that need to bypass RLS
        from database_service import SupabaseService
        self.db_service = SupabaseService(use_service_role=True)
        self.supabase = self.db_service.client

        # Keep regular client reference if needed
        self.supabase_url = os.getenv("SUPABASE_URL")

        # Import other agents dynamically to avoid circular imports
        self._email_agent = None
        self._wfa_agent = None
        self._bid_tracker = None

        print("[Orchestrator] Initialized Outreach Campaign Orchestrator")

    @property
    def email_agent(self):
        """Lazy load email extraction agent"""
        if not self._email_agent:
            from agents.email_extraction.agent import EmailExtractionAgent
            self._email_agent = EmailExtractionAgent()
        return self._email_agent

    @property
    def wfa_agent(self):
        """Lazy load WFA agent"""
        if not self._wfa_agent:
            from agents.wfa.agent import WebsiteFormAutomationAgent
            self._wfa_agent = WebsiteFormAutomationAgent()
        return self._wfa_agent

    @property
    def bid_tracker(self):
        """Lazy load bid distribution tracker"""
        if not self._bid_tracker:
            from agents.tracking.bid_distribution_tracker import BidDistributionTracker
            self._bid_tracker = BidDistributionTracker()
        return self._bid_tracker

    def create_campaign(self,
                       name: str,
                       bid_card_id: str,
                       contractor_ids: list[str],
                       channels: list[str],
                       schedule: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        Create a new outreach campaign

        Args:
            name: Campaign name
            bid_card_id: ID of the bid card to distribute
            contractor_ids: List of contractor IDs to contact
            channels: List of channels to use (email, sms, website_form)
            schedule: Optional scheduling config

        Returns:
            Campaign creation result
        """
        try:
            campaign_id = str(uuid.uuid4())

            # Create campaign record
            campaign_data = {
                "id": campaign_id,
                "name": name,
                "bid_card_id": bid_card_id,
                "contractors_targeted": len(contractor_ids),  # This is the actual column name
                "status": CampaignStatus.DRAFT.value,
                "created_at": datetime.now().isoformat()
            }

            # Add schedule data if provided
            if schedule:
                campaign_data["scheduled_start"] = schedule.get("start_time", datetime.now().isoformat())

            # Store campaign
            result = self.supabase.table("outreach_campaigns").insert(campaign_data).execute()

            if result.data:
                # First, create campaign_contractors records to track campaign membership
                campaign_contractors = []
                for contractor_id in contractor_ids:
                    campaign_contractors.append({
                        "id": str(uuid.uuid4()),
                        "campaign_id": campaign_id,
                        "contractor_id": contractor_id,
                        "assigned_at": datetime.now().isoformat(),
                        "status": "scheduled"  # Use scheduled instead of assigned
                    })
                
                # Bulk insert campaign contractors
                if campaign_contractors:
                    self.supabase.table("campaign_contractors").insert(campaign_contractors).execute()
                
                # Create outreach attempts for each contractor and channel
                # This tracks the campaign-contractor relationship
                outreach_attempts = []
                for contractor_id in contractor_ids:
                    for channel in channels:
                        outreach_attempts.append({
                            "contractor_lead_id": contractor_id,
                            "bid_card_id": bid_card_id,
                            "campaign_id": campaign_id,
                            "channel": channel,
                            "status": "queued",
                            "message_content": f"Placeholder message for {channel}",  # Will be replaced by actual message
                            "sent_at": None,  # Not sent yet
                            "created_at": datetime.now().isoformat()
                        })

                # Bulk insert outreach attempts
                if outreach_attempts:
                    self.supabase.table("contractor_outreach_attempts").insert(outreach_attempts).execute()

                print(f"[Orchestrator] Created campaign '{name}' with {len(contractor_ids)} contractors")
                return {
                    "success": True,
                    "campaign_id": campaign_id,
                    "campaign": result.data[0]
                }
            else:
                return {"success": False, "error": "Failed to create campaign"}

        except Exception as e:
            print(f"[Orchestrator ERROR] Failed to create campaign: {e}")

            # Categorize and handle the error
            category = error_handler.categorize_error(e)
            severity = ErrorSeverity.HIGH if "row-level security" in str(e) else ErrorSeverity.MEDIUM

            error_response = error_handler.handle_error(
                error=e,
                context={
                    "operation": "create_campaign",
                    "campaign_name": name,
                    "bid_card_id": bid_card_id,
                    "contractor_count": len(contractor_ids)
                },
                severity=severity,
                category=category
            )

            return error_response

    def execute_campaign(self, campaign_id: str) -> dict[str, Any]:
        """
        Execute an outreach campaign across all channels

        Returns summary of execution results
        """
        try:
            print(f"\n[Orchestrator] EXECUTING CAMPAIGN: {campaign_id}")
            print("=" * 60)

            # Get campaign details
            campaign = self._get_campaign(campaign_id)
            if not campaign:
                return {"success": False, "error": "Campaign not found"}

            # Update status to active
            self.supabase.table("outreach_campaigns").update({
                "status": CampaignStatus.ACTIVE.value,
                "started_at": datetime.now().isoformat()
            }).eq("id", campaign_id).execute()

            # Get contractors for this campaign
            contractors = self._get_campaign_contractors(campaign_id)

            # Get bid card details
            bid_card = self._get_bid_card(campaign["bid_card_id"])

            # Track results
            results = {
                "total_attempts": 0,
                "successful_contacts": 0,
                "by_channel": {},
                "contractors": []
            }

            # Process each contractor
            for contractor in contractors:
                contractor_result = self._process_contractor_outreach(
                    contractor,
                    bid_card,
                    campaign_id
                )

                results["contractors"].append(contractor_result)
                results["total_attempts"] += contractor_result["attempts"]
                results["successful_contacts"] += 1 if contractor_result["contacted"] else 0

                # Update channel stats
                for channel, success in contractor_result["channels"].items():
                    if channel not in results["by_channel"]:
                        results["by_channel"][channel] = {"attempts": 0, "successes": 0}
                    results["by_channel"][channel]["attempts"] += 1
                    if success:
                        results["by_channel"][channel]["successes"] += 1

            # Update campaign with metrics
            self.supabase.table("outreach_campaigns").update({
                "messages_sent": results["total_attempts"],
                "messages_delivered": results["successful_contacts"],
                "responses_received": 0,  # Will be updated later as responses come in
                "updated_at": datetime.now().isoformat()
            }).eq("id", campaign_id).execute()

            # Mark campaign as completed
            self.supabase.table("outreach_campaigns").update({
                "status": CampaignStatus.COMPLETED.value,
                "completed_at": datetime.now().isoformat(),
                "results": results
            }).eq("id", campaign_id).execute()

            print("\n[Orchestrator] CAMPAIGN COMPLETE")
            print(f"Total Contractors: {len(contractors)}")
            print(f"Successfully Contacted: {results['successful_contacts']}")
            print(f"Success Rate: {(results['successful_contacts'] / len(contractors) * 100):.1f}%")

            return {
                "success": True,
                "campaign_id": campaign_id,
                "results": results
            }

        except Exception as e:
            print(f"[Orchestrator ERROR] Campaign execution failed: {e}")
            # Mark campaign as failed
            self.supabase.table("outreach_campaigns").update({
                "status": CampaignStatus.FAILED.value,
                "error": str(e)
            }).eq("id", campaign_id).execute()

            return {"success": False, "error": str(e)}

    def _process_contractor_outreach(self,
                                   contractor_data: dict[str, Any],
                                   bid_card: dict[str, Any],
                                   campaign_id: str) -> dict[str, Any]:
        """
        Process outreach for a single contractor across channels

        Returns results of all outreach attempts
        """
        contractor_id = contractor_data["contractor_id"]
        channels = contractor_data.get("channels", [])

        print(f"\n[Orchestrator] Processing: {contractor_data.get('company_name', 'Unknown')}")
        print(f"  Channels: {', '.join(channels)}")

        result = {
            "contractor_id": contractor_id,
            "company_name": contractor_data.get("company_name", "Unknown"),
            "attempts": 0,
            "contacted": False,
            "channels": {},
            "primary_method": None
        }

        # Get contractor details
        contractor = self._get_contractor_details(contractor_id)

        # Try each channel in priority order
        channel_priority = ["email", "website_form", "sms", "phone"]

        for channel in channel_priority:
            if channel not in channels:
                continue

            result["attempts"] += 1

            # Attempt outreach via channel
            success = False

            if channel == "email" and contractor.get("primary_email"):
                success = self._send_email_outreach(contractor, bid_card)

            elif channel == "website_form" and contractor.get("website"):
                success = self._submit_website_form(contractor, bid_card)

            elif channel == "sms" and contractor.get("phone"):
                success = self._send_sms_outreach(contractor, bid_card)

            elif channel == "phone":
                # Log for manual follow-up
                success = self._log_phone_followup(contractor, bid_card)

            result["channels"][channel] = success

            if success:
                result["contacted"] = True
                if not result["primary_method"]:
                    result["primary_method"] = channel

                # Record in bid tracker
                self.bid_tracker.record_distribution(
                    bid_card_id=bid_card["id"],
                    contractor_id=contractor_id,
                    distribution_method=channel,
                    match_score=contractor.get("match_score"),
                    campaign_id=campaign_id
                )

                # Don't try other channels if successful
                break

        return result

    def _send_email_outreach(self, contractor: dict[str, Any], bid_card: dict[str, Any]) -> bool:
        """Send email outreach to contractor"""
        try:
            # TODO: Integrate with actual email service (SendGrid/SES)
            # For now, simulate email sending

            print(f"  [EMAIL] Sending to: {contractor['primary_email']}")

            # Create email content
            self._create_email_content(contractor, bid_card)

            # Record the attempt
            self.supabase.table("contractor_outreach_attempts").insert({
                "contractor_id": contractor["id"],
                "bid_card_id": bid_card["id"],
                "method": "email",
                "contact_info": contractor["primary_email"],
                "status": "sent",
                "attempt_date": datetime.now().isoformat(),
                "notes": "Campaign email sent"
            }).execute()

            print("  [EMAIL] Success - Email queued for delivery")
            return True

        except Exception as e:
            print(f"  [EMAIL] Failed: {e}")
            return False

    def _submit_website_form(self, contractor: dict[str, Any], bid_card: dict[str, Any]) -> bool:
        """Submit bid card via contractor's website form"""
        try:
            print(f"  [WFA] Submitting to: {contractor['website']}")

            # Use WFA agent to submit form
            submission_data = {
                "name": "Instabids Platform",
                "email": "opportunities@instabids.com",
                "phone": "(555) 123-4567",
                "message": self._create_form_message(contractor, bid_card),
                "project_type": bid_card.get("project_type", "General Contract")
            }

            result = self.wfa_agent.submit_form(
                contractor["website"],
                submission_data,
                contractor["id"],
                bid_card["id"]
            )

            if result.get("success"):
                print("  [WFA] Success - Form submitted")
                return True
            else:
                print(f"  [WFA] Failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"  [WFA] Failed: {e}")
            return False

    def _send_sms_outreach(self, contractor: dict[str, Any], bid_card: dict[str, Any]) -> bool:
        """Send SMS outreach to contractor"""
        try:
            # TODO: Integrate with Twilio
            print(f"  [SMS] Sending to: {contractor['phone']}")

            # Create SMS content (shorter)
            self._create_sms_content(contractor, bid_card)

            # Record the attempt
            self.supabase.table("contractor_outreach_attempts").insert({
                "contractor_id": contractor["id"],
                "bid_card_id": bid_card["id"],
                "method": "sms",
                "contact_info": contractor["phone"],
                "status": "sent",
                "attempt_date": datetime.now().isoformat(),
                "notes": "Campaign SMS sent"
            }).execute()

            print("  [SMS] Success - SMS queued for delivery")
            return True

        except Exception as e:
            print(f"  [SMS] Failed: {e}")
            return False

    def _log_phone_followup(self, contractor: dict[str, Any], bid_card: dict[str, Any]) -> bool:
        """Log contractor for manual phone follow-up"""
        try:
            print("  [PHONE] Logging for manual follow-up")

            # Create follow-up task
            self.supabase.table("manual_followup_tasks").insert({
                "contractor_id": contractor["id"],
                "bid_card_id": bid_card["id"],
                "task_type": "phone_call",
                "priority": "medium",
                "due_date": (datetime.now() + timedelta(days=1)).isoformat(),
                "notes": f"Call {contractor['company_name']} about {bid_card.get('project_type', 'project')}",
                "status": "pending"
            }).execute()

            print("  [PHONE] Success - Added to follow-up queue")
            return True

        except Exception as e:
            print(f"  [PHONE] Failed: {e}")
            return False

    def _create_email_content(self, contractor: dict[str, Any], bid_card: dict[str, Any]) -> str:
        """Create personalized email content"""
        project_type = bid_card.get("project_type", "project")
        location = bid_card.get("location", {})
        budget = bid_card.get("bid_document", {}).get("budget_information", {})

        content = f"""
Hi {contractor['company_name']},

We have a new {project_type} opportunity in {location.get('city', 'your area')} that matches your expertise.

Project Details:
- Type: {project_type}
- Location: {location.get('city', '')}, {location.get('state', '')}
- Budget Range: ${budget.get('budget_min', 0):,} - ${budget.get('budget_max', 0):,}
- Timeline: {bid_card.get('bid_document', {}).get('timeline', {}).get('urgency_level', 'Flexible')}

This homeowner is ready to move forward and is looking for quality contractors like you.

View full project details and submit your bid:
https://instabids.com/bid/{bid_card['id']}

Best regards,
The Instabids Team
"""
        return content

    def _create_form_message(self, contractor: dict[str, Any], bid_card: dict[str, Any]) -> str:
        """Create message for website form submission"""
        project_type = bid_card.get("project_type", "project")
        location = bid_card.get("location", {})

        message = f"""New {project_type} opportunity from Instabids:

Location: {location.get('city', '')}, {location.get('state', '')}
Timeline: {bid_card.get('bid_document', {}).get('timeline', {}).get('urgency_level', 'Flexible')}

Homeowner is ready to review bids. Please visit:
https://instabids.com/bid/{bid_card['id']}

Or reply to this message for more details."""

        return message

    def _create_sms_content(self, contractor: dict[str, Any], bid_card: dict[str, Any]) -> str:
        """Create SMS content (160 char limit)"""
        project_type = bid_card.get("project_type", "project")[:20]  # Truncate if needed
        city = bid_card.get("location", {}).get("city", "your area")[:15]

        # Keep under 160 characters
        content = f"New {project_type} in {city}. Homeowner ready to hire. View: instabids.com/bid/{bid_card['id'][:8]}"

        return content[:160]  # Ensure we don't exceed SMS limit

    def _get_campaign(self, campaign_id: str) -> Optional[dict[str, Any]]:
        """Get campaign details"""
        try:
            result = self.supabase.table("outreach_campaigns").select("*").eq("id", campaign_id).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception:
            return None

    def _get_campaign_contractors(self, campaign_id: str) -> list[dict[str, Any]]:
        """Get all contractors for a campaign with their details"""
        try:
            # Get outreach attempts for this campaign with contractor details
            result = self.supabase.table("contractor_outreach_attempts").select(
                "*, potential_contractors(*)"
            ).eq("campaign_id", campaign_id).execute()

            # Group by contractor to get all channels
            contractors_dict = {}
            for attempt in result.data:
                contractor_id = attempt["contractor_lead_id"]
                if contractor_id not in contractors_dict:
                    contractor_data = attempt.get("potential_contractors", {})
                    contractors_dict[contractor_id] = {
                        "contractor_id": contractor_id,
                        "company_name": contractor_data.get("company_name", "Unknown"),
                        "channels": [],
                        **contractor_data
                    }
                if attempt["channel"] not in contractors_dict[contractor_id]["channels"]:
                    contractors_dict[contractor_id]["channels"].append(attempt["channel"])

            return list(contractors_dict.values())

        except Exception as e:
            print(f"[Orchestrator ERROR] Failed to get campaign contractors: {e}")
            return []

    def _get_contractor_details(self, contractor_id: str) -> dict[str, Any]:
        """Get full contractor details"""
        try:
            result = self.supabase.table("potential_contractors").select("*").eq("id", contractor_id).limit(1).execute()
            return result.data[0] if result.data else {}
        except Exception:
            return {}

    def _get_bid_card(self, bid_card_id: str) -> dict[str, Any]:
        """Get bid card details"""
        try:
            result = self.supabase.table("bid_cards").select("*").eq("id", bid_card_id).limit(1).execute()
            return result.data[0] if result.data else {}
        except Exception:
            return {}

    def _update_campaign_metrics(self, campaign_id: str, results: dict[str, Any]):
        """Update campaign metrics"""
        try:
            metrics = {
                "contacted": results["successful_contacts"],
                "total_attempts": results["total_attempts"],
                "channel_breakdown": results["by_channel"],
                "last_updated": datetime.now().isoformat()
            }

            self.supabase.table("outreach_campaigns").update({
                "metrics": metrics
            }).eq("id", campaign_id).execute()

        except Exception as e:
            print(f"[Orchestrator ERROR] Failed to update metrics: {e}")

    def get_campaign_status(self, campaign_id: str) -> dict[str, Any]:
        """Get detailed campaign status and metrics"""
        try:
            # Get campaign
            campaign = self._get_campaign(campaign_id)
            if not campaign:
                return {"success": False, "error": "Campaign not found"}

            # Get distribution records
            dist_result = self.supabase.table("bid_card_distributions").select("*").eq(
                "campaign_id", campaign_id
            ).execute()

            distributions = dist_result.data if dist_result.data else []

            # Calculate metrics
            total_sent = len(distributions)
            opened = sum(1 for d in distributions if d.get("opened_at"))
            responded = sum(1 for d in distributions if d.get("responded_at"))
            interested = sum(1 for d in distributions if d.get("response_type") == "interested")

            return {
                "success": True,
                "campaign": {
                    "id": campaign_id,
                    "name": campaign["name"],
                    "status": campaign["status"],
                    "created_at": campaign["created_at"],
                    "started_at": campaign.get("started_at"),
                    "completed_at": campaign.get("completed_at")
                },
                "metrics": {
                    "total_contractors": campaign.get("contractor_count", 0),
                    "contacted": total_sent,
                    "opened": opened,
                    "responded": responded,
                    "interested": interested,
                    "open_rate": (opened / total_sent * 100) if total_sent > 0 else 0,
                    "response_rate": (responded / total_sent * 100) if total_sent > 0 else 0,
                    "interest_rate": (interested / total_sent * 100) if total_sent > 0 else 0
                },
                "channels": campaign.get("metrics", {}).get("channel_breakdown", {})
            }

        except Exception as e:
            print(f"[Orchestrator ERROR] Failed to get campaign status: {e}")
            return {"success": False, "error": str(e)}


# Create required tables
CREATE_TABLES_SQL = """
-- Outreach campaigns table
CREATE TABLE IF NOT EXISTS outreach_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    bid_card_id UUID REFERENCES bid_cards(id),
    contractor_count INTEGER,
    channels TEXT[],
    status TEXT DEFAULT 'draft',
    schedule JSONB,
    metrics JSONB,
    results JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error TEXT
);

-- Campaign-contractor mapping
CREATE TABLE IF NOT EXISTS campaign_contractors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES outreach_campaigns(id),
    contractor_id UUID REFERENCES potential_contractors(id),
    channel TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    scheduled_at TIMESTAMP WITH TIME ZONE,
    attempted_at TIMESTAMP WITH TIME ZONE,
    result JSONB,
    UNIQUE(campaign_id, contractor_id, channel)
);

-- Manual follow-up tasks
CREATE TABLE IF NOT EXISTS manual_followup_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_id UUID REFERENCES potential_contractors(id),
    bid_card_id UUID REFERENCES bid_cards(id),
    task_type TEXT NOT NULL,
    priority TEXT DEFAULT 'medium',
    due_date TIMESTAMP WITH TIME ZONE,
    assigned_to TEXT,
    status TEXT DEFAULT 'pending',
    notes TEXT,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON outreach_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_bid_card ON outreach_campaigns(bid_card_id);
CREATE INDEX IF NOT EXISTS idx_campaign_contractors_campaign ON campaign_contractors(campaign_id);
CREATE INDEX IF NOT EXISTS idx_followup_tasks_status ON manual_followup_tasks(status);
"""


# Test the orchestrator
if __name__ == "__main__":
    orchestrator = OutreachCampaignOrchestrator()

    print("\nTesting Outreach Campaign Orchestrator...")

    # Create a test campaign
    test_campaign = orchestrator.create_campaign(
        name="Test Multi-Channel Campaign",
        bid_card_id="test-bid-123",
        contractor_ids=["contractor-1", "contractor-2", "contractor-3"],
        channels=["email", "website_form", "sms"],
        schedule={"start_time": datetime.now().isoformat()}
    )

    print(f"\nCampaign Creation Result: {json.dumps(test_campaign, indent=2)}")

    print("\nNote: Run the CREATE TABLES SQL in Supabase to set up the required tables")
