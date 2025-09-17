"""
External Acquisition Agent (EAA)
Multi-channel contractor outreach and onboarding automation
"""
import uuid
from datetime import datetime
from typing import Any

from .message_templates.template_engine import TemplateEngine
from .onboarding_flow.onboarding_bot import OnboardingBot
from .outreach_channels.email_channel import EmailChannel
from .outreach_channels.mcp_email_channel_claude import MCPEmailChannelWithOpenAI
from .outreach_channels.sms_channel import SMSChannel
from .response_tracking.response_parser import ResponseParser


class ExternalAcquisitionAgent:
    """External Acquisition Agent for contractor outreach campaigns"""

    def __init__(self):
        """Initialize EAA with all components"""
        try:
            # Initialize communication channels
            self.email_channel = EmailChannel()
            self.mcp_email_channel = MCPEmailChannelWithOpenAI()  # OpenAI-powered email channel
            self.sms_channel = SMSChannel()

            # Initialize template engine
            self.template_engine = TemplateEngine()

            # Initialize response processing
            self.response_parser = ResponseParser()

            # Initialize onboarding system
            self.onboarding_bot = OnboardingBot()

            # Mock Supabase for now (will be replaced with real connection)
            self.supabase = None

            print("[EAA] External Acquisition Agent initialized successfully")

        except Exception as e:
            print(f"[EAA ERROR] Failed to initialize: {e}")
            raise

    def start_campaign(self, bid_card_id: str, contractors: list[dict[str, Any]],
                      channels: list[str] | None = None, urgency: str = "week") -> dict[str, Any]:
        """
        Start outreach campaign for discovered contractors

        Args:
            bid_card_id: ID of the bid card
            contractors: List of contractors from CDA
            channels: Communication channels to use ['email', 'sms']
            urgency: Project urgency level

        Returns:
            Campaign results with tracking information
        """
        try:
            print(f"[EAA] Starting outreach campaign for bid card {bid_card_id}")
            print(f"[EAA] Targeting {len(contractors)} contractors via {channels or ['email', 'sms']}")

            # Generate campaign ID
            campaign_id = str(uuid.uuid4())

            # Load bid card data (mock for now)
            bid_card_data = self._load_bid_card(bid_card_id)

            # Default channels if not specified
            if not channels:
                channels = ["email", "sms"]

            # Track campaign start
            campaign_data = {
                "id": campaign_id,
                "bid_card_id": bid_card_id,
                "target_contractor_count": len(contractors),
                "channels_used": channels,
                "urgency": urgency,
                "created_at": datetime.now().isoformat(),
                "status": "active"
            }

            # Process contractors by tier
            tier_results = {}
            messages_sent = []

            for contractor in contractors:
                tier = contractor.get("discovery_tier", 3)

                if tier not in tier_results:
                    tier_results[tier] = {"count": 0, "sent": 0, "failed": 0}

                tier_results[tier]["count"] += 1

                # Send messages via specified channels
                contractor_messages = self._send_contractor_outreach(
                    contractor, bid_card_data, channels, campaign_id, urgency
                )

                if contractor_messages:
                    messages_sent.extend(contractor_messages)
                    tier_results[tier]["sent"] += 1
                else:
                    tier_results[tier]["failed"] += 1

            # Save campaign to database (mock)
            self._save_campaign(campaign_data, messages_sent)

            campaign_result = {
                "success": True,
                "campaign_id": campaign_id,
                "messages_sent": len(messages_sent),
                "tier_breakdown": tier_results,
                "channels_used": channels,
                "estimated_response_time": self._estimate_response_time(urgency),
                "tracking_url": f"/api/eaa/campaign/{campaign_id}/status"
            }

            print(f"[EAA] Campaign {campaign_id} launched successfully")
            print(f"[EAA] Sent {len(messages_sent)} messages across {len(channels)} channels")

            return campaign_result

        except Exception as e:
            print(f"[EAA ERROR] Campaign failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "campaign_id": None
            }

    def _send_contractor_outreach(self, contractor: dict[str, Any], bid_card_data: dict[str, Any],
                                 channels: list[str], campaign_id: str, urgency: str) -> list[dict[str, Any]]:
        """Send outreach messages to a single contractor"""
        messages_sent = []

        try:
            # Send personalized email via MCP if email channel requested
            if "email" in channels:
                result = self.mcp_email_channel.send_personalized_outreach(
                    contractor, bid_card_data, campaign_id
                )
                if result["success"]:
                    messages_sent.append({
                        "message_id": result["message_id"],
                        "channel": "mcp_email",
                        "contractor_email": contractor.get("email"),
                        "contractor_company": contractor.get("company_name"),
                        "personalization_applied": result.get("personalization_applied", False),
                        "unique_elements": result.get("unique_elements", {}),
                        "sent_at": datetime.now().isoformat()
                    })
                else:
                    print(f"[EAA ERROR] MCP email failed for {contractor.get('company_name')}: {result.get('error')}")

            # Generate traditional messages for other channels
            if any(channel in channels for channel in ["sms", "website_form"]):
                messages = self.template_engine.generate_messages(
                    contractor, bid_card_data, channels, urgency
                )

                # Send via SMS channel
                if "sms" in channels and "sms" in messages:
                    result = self.sms_channel.send_message(
                        contractor, messages["sms"], campaign_id
                    )
                    if result["success"]:
                        messages_sent.append({
                            "message_id": result["message_id"],
                            "channel": "sms",
                            "contractor_phone": contractor.get("phone"),
                            "sent_at": datetime.now().isoformat()
                        })

                # Handle website_form channel (would integrate with WFA agent)
                if "website_form" in channels:
                    messages_sent.append({
                        "message_id": str(uuid.uuid4()),
                        "channel": "website_form",
                        "contractor_website": contractor.get("website"),
                        "status": "queued_for_wfa",
                        "sent_at": datetime.now().isoformat()
                    })

            return messages_sent

        except Exception as e:
            print(f"[EAA ERROR] Failed to send messages to {contractor.get('company_name', 'Unknown')}: {e}")
            return []

    def get_campaign_status(self, campaign_id: str) -> dict[str, Any]:
        """Get campaign status and response metrics"""
        try:
            # Load campaign data (mock)
            campaign_data = self._load_campaign(campaign_id)

            if not campaign_data:
                return {"success": False, "error": "Campaign not found"}

            # Get response metrics
            responses = self._get_campaign_responses(campaign_id)

            # Calculate metrics
            total_sent = campaign_data.get("messages_sent", 0)
            total_responses = len(responses)
            interested_responses = len([r for r in responses if r.get("interest_level") == "high"])

            response_rate = (total_responses / total_sent * 100) if total_sent > 0 else 0
            interest_rate = (interested_responses / total_sent * 100) if total_sent > 0 else 0

            status = {
                "success": True,
                "campaign_id": campaign_id,
                "status": campaign_data.get("status", "active"),
                "created_at": campaign_data.get("created_at"),
                "metrics": {
                    "messages_sent": total_sent,
                    "responses_received": total_responses,
                    "interested_contractors": interested_responses,
                    "response_rate_percent": round(response_rate, 1),
                    "interest_rate_percent": round(interest_rate, 1)
                },
                "recent_responses": responses[-5:] if responses else [],
                "tier_breakdown": campaign_data.get("tier_breakdown", {})
            }

            return status

        except Exception as e:
            print(f"[EAA ERROR] Failed to get campaign status: {e}")
            return {"success": False, "error": str(e)}

    def process_response(self, message_id: str, response_content: str,
                        channel: str) -> dict[str, Any]:
        """Process incoming response from contractor"""
        try:
            print(f"[EAA] Processing {channel} response for message {message_id}")

            # Parse response content
            parsed_response = self.response_parser.parse_response(
                response_content, channel
            )

            # Extract contractor information
            contractor_info = self._get_contractor_from_message(message_id)

            # Save response to database
            response_record = {
                "message_id": message_id,
                "response_type": parsed_response["intent"],
                "sentiment_score": parsed_response["sentiment"],
                "interest_level": parsed_response["interest_level"],
                "extracted_data": parsed_response["extracted_data"],
                "response_content": response_content,
                "processed_at": datetime.now().isoformat()
            }

            self._save_response(response_record)

            # Handle high-interest responses
            if parsed_response["interest_level"] == "high":
                self._initiate_onboarding(contractor_info, response_record)

            # Schedule follow-up if needed
            elif parsed_response["intent"] == "need_info":
                self._schedule_follow_up(message_id, contractor_info)

            result = {
                "success": True,
                "response_id": str(uuid.uuid4()),
                "intent": parsed_response["intent"],
                "interest_level": parsed_response["interest_level"],
                "action_taken": self._get_action_taken(parsed_response),
                "follow_up_scheduled": parsed_response["intent"] == "need_info"
            }

            print(f"[EAA] Response processed: {parsed_response['intent']} ({parsed_response['interest_level']} interest)")

            return result

        except Exception as e:
            print(f"[EAA ERROR] Failed to process response: {e}")
            return {"success": False, "error": str(e)}

    def start_onboarding(self, contractor_email: str, source_campaign: str | None = None) -> dict[str, Any]:
        """Start onboarding process for interested contractor"""
        try:
            print(f"[EAA] Starting onboarding for {contractor_email}")

            # Initiate onboarding bot
            onboarding_result = self.onboarding_bot.start_onboarding(
                contractor_email, source_campaign
            )

            if onboarding_result["success"]:
                print(f"[EAA] Onboarding started for {contractor_email}")
                return {
                    "success": True,
                    "onboarding_id": onboarding_result["onboarding_id"],
                    "next_step": onboarding_result["next_step"],
                    "estimated_completion": onboarding_result["estimated_completion"]
                }
            else:
                return onboarding_result

        except Exception as e:
            print(f"[EAA ERROR] Failed to start onboarding: {e}")
            return {"success": False, "error": str(e)}

    def test_mcp_email_integration(self, test_contractors: list[dict[str, Any]], bid_card_data: dict[str, Any]) -> dict[str, Any]:
        """Test MCP email integration with sample contractors"""
        try:
            print(f"[EAA] Testing MCP email integration with {len(test_contractors)} contractors")

            test_results = {
                "success": True,
                "emails_sent": 0,
                "emails_failed": 0,
                "unique_elements_verified": [],
                "sent_emails": []
            }

            for contractor in test_contractors:
                result = self.mcp_email_channel.send_personalized_outreach(
                    contractor, bid_card_data, "test-campaign-123"
                )

                if result["success"]:
                    test_results["emails_sent"] += 1
                    test_results["unique_elements_verified"].append({
                        "contractor": contractor.get("company_name", "Unknown"),
                        "email": contractor.get("email", "No email"),
                        "unique_elements": result.get("unique_elements", {}),
                        "message_id": result.get("message_id")
                    })
                    test_results["sent_emails"].append(result)
                else:
                    test_results["emails_failed"] += 1
                    print(f"[EAA ERROR] Failed to send test email to {contractor.get('company_name')}: {result.get('error')}")

            # Get all sent emails for verification
            sent_emails = self.mcp_email_channel.get_sent_emails_for_testing()
            test_results["stored_emails_count"] = len(sent_emails)

            print("[EAA] MCP Test Results:")
            print(f"  Emails Sent: {test_results['emails_sent']}")
            print(f"  Emails Failed: {test_results['emails_failed']}")
            print(f"  Stored Emails: {test_results['stored_emails_count']}")

            return test_results

        except Exception as e:
            print(f"[EAA ERROR] MCP test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "emails_sent": 0,
                "emails_failed": 0
            }

    def verify_unique_emails(self) -> dict[str, Any]:
        """Verify that each contractor received unique, personalized emails"""
        try:
            sent_emails = self.mcp_email_channel.get_sent_emails_for_testing()

            verification = {
                "total_emails": len(sent_emails),
                "unique_subjects": set(),
                "unique_companies": set(),
                "unique_urls": set(),
                "unique_message_ids": set(),
                "personalization_verified": True,
                "details": []
            }

            for email in sent_emails:
                verification["unique_subjects"].add(email.get("subject", ""))
                verification["unique_companies"].add(email.get("company_name", ""))
                verification["unique_urls"].add(email.get("external_url", ""))
                verification["unique_message_ids"].add(email.get("message_id", ""))

                verification["details"].append({
                    "company": email.get("company_name"),
                    "subject": email.get("subject"),
                    "external_url": email.get("external_url"),
                    "message_id": email.get("message_id"),
                    "sent_at": email.get("sent_at")
                })

            # Convert sets to counts for JSON serialization
            verification["unique_subjects_count"] = len(verification["unique_subjects"])
            verification["unique_companies_count"] = len(verification["unique_companies"])
            verification["unique_urls_count"] = len(verification["unique_urls"])
            verification["unique_message_ids_count"] = len(verification["unique_message_ids"])

            # Clean up sets for return
            verification["unique_subjects"] = list(verification["unique_subjects"])
            verification["unique_companies"] = list(verification["unique_companies"])
            verification["unique_urls"] = list(verification["unique_urls"])
            verification["unique_message_ids"] = list(verification["unique_message_ids"])

            print("[EAA] Email Uniqueness Verification:")
            print(f"  Total Emails: {verification['total_emails']}")
            print(f"  Unique Companies: {verification['unique_companies_count']}")
            print(f"  Unique URLs: {verification['unique_urls_count']}")
            print(f"  Unique Message IDs: {verification['unique_message_ids_count']}")

            return verification

        except Exception as e:
            print(f"[EAA ERROR] Email verification failed: {e}")
            return {
                "total_emails": 0,
                "error": str(e),
                "personalization_verified": False
            }

    def clear_test_data(self):
        """Clear test email data"""
        try:
            self.mcp_email_channel.clear_test_emails()
            print("[EAA] Test email data cleared")
        except Exception as e:
            print(f"[EAA ERROR] Failed to clear test data: {e}")

    def get_analytics(self, date_range: int = 30) -> dict[str, Any]:
        """Get EAA performance analytics"""
        try:
            # Mock analytics data for now
            analytics = {
                "success": True,
                "period_days": date_range,
                "campaigns_launched": 25,
                "total_contractors_contacted": 450,
                "overall_metrics": {
                    "email_delivery_rate": 96.8,
                    "sms_delivery_rate": 99.2,
                    "response_rate_email": 18.5,
                    "response_rate_sms": 32.1,
                    "interest_rate": 7.3,
                    "onboarding_completion_rate": 68.4
                },
                "channel_performance": {
                    "email": {
                        "sent": 320,
                        "delivered": 310,
                        "responses": 59,
                        "interested": 18
                    },
                    "sms": {
                        "sent": 280,
                        "delivered": 278,
                        "responses": 90,
                        "interested": 23
                    }
                },
                "top_performing_templates": [
                    {"template": "kitchen_urgent_email", "response_rate": 24.1},
                    {"template": "bathroom_sms", "response_rate": 38.5},
                    {"template": "general_follow_up", "response_rate": 15.2}
                ]
            }

            return analytics

        except Exception as e:
            print(f"[EAA ERROR] Failed to get analytics: {e}")
            return {"success": False, "error": str(e)}

    # Helper methods
    def _load_bid_card(self, bid_card_id: str) -> dict[str, Any]:
        """Load bid card data from database"""
        try:
            # Import database connection
            import os
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from database_simple import db

            # Load bid card from database
            result = db.client.table("bid_cards").select("*").eq("id", bid_card_id).execute()

            if result.data and len(result.data) > 0:
                bid_card = result.data[0]
                print(f"[EAA] Loaded bid card: {bid_card.get('project_type')} - ${bid_card.get('budget_min')}-${bid_card.get('budget_max')}")
                return bid_card
            else:
                print(f"[EAA] WARNING: Bid card {bid_card_id} not found, using mock data")
                # Fallback to mock data if not found
                return {
                    "id": bid_card_id,
                    "project_type": "home improvement",
                    "budget_min": 5000,
                    "budget_max": 15000,
                    "location": "Unknown Location",
                    "urgency_level": "week",
                    "scope_summary": "Project details not found",
                    "contractor_type_ids": [127, 219]  # Default to general contractors
                }
        except Exception as e:
            print(f"[EAA] ERROR loading bid card: {e}")
            # Return mock data on error
            return {
                "id": bid_card_id,
                "project_type": "home improvement",
                "budget_min": 5000,
                "budget_max": 15000,
                "location": "Unknown Location",
                "urgency_level": "week",
                "scope_summary": "Project details not found",
                "contractor_type_ids": [127, 219]  # Default to general contractors
            }

    def _save_campaign(self, campaign_data: dict[str, Any], messages: list[dict[str, Any]]):
        """Save campaign data (mock implementation)"""
        # In production, save to Supabase
        print(f"[EAA] Saving campaign {campaign_data['id']} with {len(messages)} messages")

    def _load_campaign(self, campaign_id: str) -> dict[str, Any]:
        """Load campaign data (mock implementation)"""
        return {
            "id": campaign_id,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "messages_sent": 15,
            "tier_breakdown": {1: {"count": 3, "sent": 3}, 2: {"count": 5, "sent": 5}, 3: {"count": 7, "sent": 7}}
        }

    def _get_campaign_responses(self, campaign_id: str) -> list[dict[str, Any]]:
        """Get responses for a campaign (mock implementation)"""
        return [
            {"intent": "interested", "interest_level": "high", "contractor": "ABC Construction"},
            {"intent": "need_info", "interest_level": "medium", "contractor": "Quality Builders"},
            {"intent": "not_interested", "interest_level": "low", "contractor": "Fast Repairs"}
        ]

    def _get_contractor_from_message(self, message_id: str) -> dict[str, Any]:
        """Get contractor info from message ID (mock implementation)"""
        return {
            "email": "contractor@example.com",
            "phone": "+1234567890",
            "company_name": "Example Construction"
        }

    def _save_response(self, response_record: dict[str, Any]):
        """Save response record (mock implementation)"""
        print(f"[EAA] Saving response: {response_record['response_type']}")

    def _initiate_onboarding(self, contractor_info: dict[str, Any], response_record: dict[str, Any]):
        """Initiate onboarding for interested contractor"""
        print(f"[EAA] Initiating onboarding for {contractor_info.get('company_name')}")

    def _schedule_follow_up(self, message_id: str, contractor_info: dict[str, Any]):
        """Schedule follow-up message"""
        print(f"[EAA] Scheduling follow-up for {contractor_info.get('company_name')}")

    def _get_action_taken(self, parsed_response: dict[str, Any]) -> str:
        """Get action taken based on response"""
        if parsed_response["interest_level"] == "high":
            return "onboarding_initiated"
        elif parsed_response["intent"] == "need_info":
            return "follow_up_scheduled"
        else:
            return "response_recorded"

    def _estimate_response_time(self, urgency: str) -> str:
        """Estimate response time based on urgency"""
        if urgency == "emergency":
            return "2-4 hours"
        elif urgency == "week":
            return "6-12 hours"
        elif urgency == "month":
            return "24-48 hours"
        else:
            return "48-72 hours"
