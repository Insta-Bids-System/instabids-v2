"""
Follow-up Automation System
Intelligent re-engagement of contractors who haven't responded
Uses Opus 4 to craft personalized follow-up messages
"""

import json
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from openai import OpenAI
from dotenv import load_dotenv
from supabase import create_client


class FollowUpStrategy(Enum):
    """Follow-up strategies based on contractor behavior"""
    GENTLE_REMINDER = "gentle_reminder"      # First follow-up
    VALUE_PROPOSITION = "value_proposition"  # Emphasize benefits
    URGENCY = "urgency"                      # Project starting soon
    FINAL_CHANCE = "final_chance"           # Last attempt
    DIFFERENT_CHANNEL = "different_channel"  # Try SMS if email failed
    PERSONALIZED = "personalized"           # Opus 4 crafted message


class FollowUpAutomation:
    """Automates intelligent follow-up campaigns"""

    def __init__(self):
        """Initialize follow-up automation"""
        load_dotenv(override=True)
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.anthropic_key = os.getenv("OPENAI_API_KEY")

        self.supabase = create_client(self.supabase_url, self.supabase_key)
        self.anthropic = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Import dependencies
        self._bid_tracker = None
        self._orchestrator = None
        self._response_monitor = None

        print("[FollowUp] Initialized Follow-up Automation System")

    @property
    def bid_tracker(self):
        """Lazy load bid tracker"""
        if not self._bid_tracker:
            from agents.tracking.bid_distribution_tracker import BidDistributionTracker
            self._bid_tracker = BidDistributionTracker()
        return self._bid_tracker

    @property
    def orchestrator(self):
        """Lazy load campaign orchestrator"""
        if not self._orchestrator:
            from agents.orchestration.campaign_orchestrator import OutreachCampaignOrchestrator
            self._orchestrator = OutreachCampaignOrchestrator()
        return self._orchestrator

    @property
    def response_monitor(self):
        """Lazy load response monitor"""
        if not self._response_monitor:
            from agents.monitoring.response_monitor import ResponseMonitor
            self._response_monitor = ResponseMonitor()
        return self._response_monitor

    def run_followup_campaign(self,
                            days_since_sent: int = 3,
                            max_follow_ups: int = 2,
                            batch_size: int = 20) -> dict[str, Any]:
        """
        Run automated follow-up campaign

        Args:
            days_since_sent: Days to wait before first follow-up
            max_follow_ups: Maximum follow-ups per contractor
            batch_size: Number of contractors to process

        Returns:
            Campaign results
        """
        try:
            print("\n[FollowUp] RUNNING FOLLOW-UP CAMPAIGN")
            print("=" * 60)

            # Get candidates for follow-up
            candidates_result = self.bid_tracker.get_follow_up_candidates(
                days_since_sent=days_since_sent,
                max_follow_ups=max_follow_ups
            )

            if not candidates_result["success"] or not candidates_result["candidates"]:
                print("[FollowUp] No candidates for follow-up")
                return {
                    "success": True,
                    "message": "No contractors need follow-up",
                    "candidates_found": 0
                }

            candidates = candidates_result["candidates"][:batch_size]
            print(f"[FollowUp] Found {len(candidates)} contractors for follow-up")

            # Process each candidate
            results = {
                "total_processed": 0,
                "follow_ups_sent": 0,
                "strategies_used": {},
                "contractors": []
            }

            for candidate in candidates:
                result = self._process_followup(candidate)
                results["contractors"].append(result)
                results["total_processed"] += 1

                if result["success"]:
                    results["follow_ups_sent"] += 1
                    strategy = result["strategy"]
                    results["strategies_used"][strategy] = results["strategies_used"].get(strategy, 0) + 1

            # Summary
            print("\n[FollowUp] CAMPAIGN COMPLETE")
            print(f"Processed: {results['total_processed']}")
            print(f"Follow-ups Sent: {results['follow_ups_sent']}")
            print(f"Success Rate: {(results['follow_ups_sent'] / results['total_processed'] * 100):.1f}%")

            return {
                "success": True,
                "results": results
            }

        except Exception as e:
            print(f"[FollowUp ERROR] Campaign failed: {e}")
            return {"success": False, "error": str(e)}

    def _process_followup(self, candidate: dict[str, Any]) -> dict[str, Any]:
        """Process follow-up for a single contractor"""
        try:
            contractor_id = candidate["contractor_id"]
            company_name = candidate["company_name"]

            print(f"\n[FollowUp] Processing: {company_name}")

            # Determine follow-up strategy
            strategy = self._determine_strategy(candidate)
            print(f"  Strategy: {strategy.value}")

            # Get contractor and bid details
            contractor = self._get_contractor_details(contractor_id)
            bid_card = self._get_bid_card_details(candidate["bid_card_id"])

            # Generate follow-up content based on strategy
            if strategy == FollowUpStrategy.PERSONALIZED:
                # Use Opus 4 for intelligent personalization
                content = self._generate_opus4_followup(contractor, bid_card, candidate)
            else:
                # Use template-based approach
                content = self._generate_template_followup(contractor, bid_card, candidate, strategy)

            # Determine channel
            channel = self._determine_channel(candidate, contractor)

            # Send follow-up
            success = False
            if channel == "email" and contractor.get("primary_email"):
                success = self._send_email_followup(contractor, content["email"])
            elif channel == "sms" and contractor.get("phone"):
                success = self._send_sms_followup(contractor, content["sms"])
            elif channel == "website_form" and contractor.get("website"):
                success = self._send_form_followup(contractor, content["form"])

            if success:
                # Record follow-up
                self.bid_tracker.record_follow_up(candidate["distribution_id"], channel)

                # Log follow-up details
                self._log_followup(candidate, strategy, channel, content)

                print(f"  ✓ Follow-up sent via {channel}")

                return {
                    "success": True,
                    "contractor_id": contractor_id,
                    "company_name": company_name,
                    "strategy": strategy.value,
                    "channel": channel
                }
            else:
                print("  ✗ Failed to send follow-up")
                return {
                    "success": False,
                    "contractor_id": contractor_id,
                    "company_name": company_name,
                    "error": "Failed to send"
                }

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return {
                "success": False,
                "contractor_id": candidate["contractor_id"],
                "error": str(e)
            }

    def _determine_strategy(self, candidate: dict[str, Any]) -> FollowUpStrategy:
        """Determine best follow-up strategy based on contractor behavior"""
        follow_up_count = candidate.get("follow_up_count", 0)
        match_score = candidate.get("match_score", 0)
        days_since = candidate.get("days_since_sent", 0)

        # High match score gets personalized treatment
        if match_score >= 85:
            return FollowUpStrategy.PERSONALIZED

        # Based on follow-up count
        if follow_up_count == 0:
            # First follow-up
            if days_since <= 3:
                return FollowUpStrategy.GENTLE_REMINDER
            else:
                return FollowUpStrategy.VALUE_PROPOSITION
        elif follow_up_count == 1:
            # Second follow-up
            if days_since >= 7:
                return FollowUpStrategy.URGENCY
            else:
                return FollowUpStrategy.DIFFERENT_CHANNEL
        else:
            # Final attempt
            return FollowUpStrategy.FINAL_CHANCE

    def _generate_opus4_followup(self,
                               contractor: dict[str, Any],
                               bid_card: dict[str, Any],
                               candidate: dict[str, Any]) -> dict[str, str]:
        """Use Claude Opus 4 to generate intelligent follow-up"""
        try:
            # Prepare context for Opus 4
            prompt = f"""You are crafting a follow-up message to a contractor who hasn't responded to a project opportunity.

Contractor Details:
- Company: {contractor['company_name']}
- Type: {contractor.get('contractor_type', 'General Contractor')}
- Location: {contractor.get('city', '')}, {contractor.get('state', '')}
- Match Score: {candidate['match_score']}/100
- Days Since Contact: {candidate['days_since_sent']}
- Previous Method: {candidate['last_method']}

Project Details:
- Type: {bid_card.get('project_type', 'Unknown')}
- Location: {bid_card.get('location', {}).get('city', '')}, {bid_card.get('location', {}).get('state', '')}
- Budget: ${bid_card.get('bid_document', {}).get('budget_information', {}).get('budget_min', 0):,} - ${bid_card.get('bid_document', {}).get('budget_information', {}).get('budget_max', 0):,}
- Timeline: {bid_card.get('bid_document', {}).get('timeline', {}).get('urgency_level', 'Flexible')}
- Customer Notes: {bid_card.get('bid_document', {}).get('project_overview', {}).get('description', '')[:200]}

Generate a personalized follow-up that:
1. References something specific about their company (use company name creatively)
2. Highlights why this project is perfect for them
3. Creates urgency without being pushy
4. Mentions the homeowner is ready to move forward
5. Includes a clear call-to-action

Provide the message in three formats:
1. Email (professional but friendly, 150 words max)
2. SMS (casual and urgent, 140 characters max)
3. Form message (brief and to the point, 100 words max)

Format as JSON with keys: email, sms, form"""

            # Call Opus 4
            response = self.openai.chat.completions.create(
                model="claude-opus-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse response
            content = response.choices[0].message.content

            # Try to parse as JSON
            try:
                messages = json.loads(content)
            except:
                # Fallback parsing
                messages = {
                    "email": content.split("Email:")[1].split("SMS:")[0].strip() if "Email:" in content else content[:500],
                    "sms": content.split("SMS:")[1].split("Form:")[0].strip() if "SMS:" in content else f"Still interested in the {bid_card.get('project_type', 'project')}? Customer ready to hire: instabids.com/bid/{bid_card['id'][:8]}",
                    "form": content.split("Form:")[1].strip() if "Form:" in content else f"Following up on {bid_card.get('project_type', 'project')} opportunity. Customer ready to review bids."
                }

            print("  [Opus 4] Generated personalized follow-up")
            return messages

        except Exception as e:
            print(f"  [Opus 4 ERROR] {e}")
            # Fallback to template
            return self._generate_template_followup(contractor, bid_card, candidate, FollowUpStrategy.VALUE_PROPOSITION)

    def _generate_template_followup(self,
                                  contractor: dict[str, Any],
                                  bid_card: dict[str, Any],
                                  candidate: dict[str, Any],
                                  strategy: FollowUpStrategy) -> dict[str, str]:
        """Generate template-based follow-up messages"""
        company_name = contractor["company_name"]
        project_type = bid_card.get("project_type", "project")
        location = bid_card.get("location", {})
        bid_id = bid_card["id"]

        templates = {
            FollowUpStrategy.GENTLE_REMINDER: {
                "email": f"""Hi {company_name},

Just wanted to make sure you saw our {project_type} opportunity in {location.get('city', 'your area')}.

The homeowner is reviewing bids this week and we'd hate for you to miss out.

View details: https://instabids.com/bid/{bid_id}

Best regards,
Instabids Team""",
                "sms": f"Hi {company_name[:20]}, did you see the {project_type[:15]} project? Homeowner reviewing bids soon: instabids.com/bid/{bid_id[:8]}",
                "form": f"Following up on {project_type} opportunity sent earlier this week. Homeowner ready to hire."
            },

            FollowUpStrategy.VALUE_PROPOSITION: {
                "email": f"""Hi {company_name},

We noticed you haven't responded to the {project_type} opportunity yet.

Why this is perfect for you:
✓ In your service area ({location.get('city', 'local')})
✓ Matches your expertise
✓ Homeowner pre-qualified and ready
✓ No sales meetings needed

Don't miss out: https://instabids.com/bid/{bid_id}

Best regards,
Instabids Team""",
                "sms": f"{project_type[:20]} in {location.get('city', 'your area')[:15]}. Pre-qualified customer ready. Get details: instabids.com/bid/{bid_id[:8]}",
                "form": f"Great {project_type} opportunity matching your expertise. Pre-qualified homeowner ready to hire. No sales meetings required."
            },

            FollowUpStrategy.URGENCY: {
                "email": f"""Hi {company_name},

The homeowner for the {project_type} project is making their decision soon.

They've already received several bids and are impressed with the quality of contractors.

This is your last chance to be considered: https://instabids.com/bid/{bid_id}

Submit your bid today!

Best regards,
Instabids Team""",
                "sms": f"FINAL NOTICE: {project_type[:20]} homeowner deciding soon. Submit bid now: instabids.com/bid/{bid_id[:8]}",
                "form": f"URGENT: Homeowner making decision on {project_type} soon. Several bids already received. Submit yours today!"
            },

            FollowUpStrategy.FINAL_CHANCE: {
                "email": f"""Hi {company_name},

Final opportunity for the {project_type} project in {location.get('city', 'your area')}.

The homeowner is closing bidding tomorrow.

Last chance: https://instabids.com/bid/{bid_id}

Best regards,
Instabids Team""",
                "sms": f"Last chance: {project_type[:20]} closing tomorrow. View now: instabids.com/bid/{bid_id[:8]}",
                "form": f"Final notice: {project_type} bidding closes tomorrow. Don't miss out!"
            }
        }

        # Default to value proposition if strategy not in templates
        return templates.get(strategy, templates[FollowUpStrategy.VALUE_PROPOSITION])

    def _determine_channel(self, candidate: dict[str, Any], contractor: dict[str, Any]) -> str:
        """Determine best channel for follow-up"""
        last_method = candidate.get("last_method", "")
        follow_up_count = candidate.get("follow_up_count", 0)

        # Try different channel on second attempt
        if follow_up_count >= 1 and last_method == "email":
            if contractor.get("phone"):
                return "sms"
            elif contractor.get("website"):
                return "website_form"

        # Default priority
        if contractor.get("primary_email"):
            return "email"
        elif contractor.get("phone"):
            return "sms"
        elif contractor.get("website"):
            return "website_form"

        return "email"  # Fallback

    def _send_email_followup(self, contractor: dict[str, Any], content: str) -> bool:
        """Send email follow-up"""
        try:
            # TODO: Integrate with email service
            print(f"    Sending email to: {contractor['primary_email']}")

            # Record attempt
            self.supabase.table("followup_attempts").insert({
                "contractor_id": contractor["id"],
                "method": "email",
                "content": content,
                "sent_at": datetime.now().isoformat()
            }).execute()

            return True
        except Exception:
            return False

    def _send_sms_followup(self, contractor: dict[str, Any], content: str) -> bool:
        """Send SMS follow-up"""
        try:
            # TODO: Integrate with Twilio
            print(f"    Sending SMS to: {contractor['phone']}")

            # Record attempt
            self.supabase.table("followup_attempts").insert({
                "contractor_id": contractor["id"],
                "method": "sms",
                "content": content,
                "sent_at": datetime.now().isoformat()
            }).execute()

            return True
        except Exception:
            return False

    def _send_form_followup(self, contractor: dict[str, Any], content: str) -> bool:
        """Submit follow-up via website form"""
        try:
            # TODO: Use WFA agent
            print(f"    Submitting form on: {contractor['website']}")

            # Record attempt
            self.supabase.table("followup_attempts").insert({
                "contractor_id": contractor["id"],
                "method": "website_form",
                "content": content,
                "sent_at": datetime.now().isoformat()
            }).execute()

            return True
        except Exception:
            return False

    def _get_contractor_details(self, contractor_id: str) -> dict[str, Any]:
        """Get contractor details"""
        try:
            result = self.supabase.table("potential_contractors").select("*").eq(
                "id", contractor_id
            ).limit(1).execute()
            return result.data[0] if result.data else {}
        except Exception:
            return {}

    def _get_bid_card_details(self, bid_card_id: str) -> dict[str, Any]:
        """Get bid card details"""
        try:
            result = self.supabase.table("bid_cards").select("*").eq(
                "id", bid_card_id
            ).limit(1).execute()
            return result.data[0] if result.data else {}
        except Exception:
            return {}

    def _log_followup(self,
                     candidate: dict[str, Any],
                     strategy: FollowUpStrategy,
                     channel: str,
                     content: dict[str, str]):
        """Log follow-up details for analysis"""
        try:
            log_entry = {
                "distribution_id": candidate["distribution_id"],
                "contractor_id": candidate["contractor_id"],
                "bid_card_id": candidate["bid_card_id"],
                "strategy": strategy.value,
                "channel": channel,
                "follow_up_number": candidate["follow_up_count"] + 1,
                "content_preview": content.get(channel, "")[:100],
                "created_at": datetime.now().isoformat()
            }

            self.supabase.table("followup_logs").insert(log_entry).execute()

        except Exception as e:
            print(f"[FollowUp ERROR] Failed to log: {e}")

    def get_followup_analytics(self, days_back: int = 30) -> dict[str, Any]:
        """Get analytics on follow-up effectiveness"""
        try:
            since_date = (datetime.now() - timedelta(days=days_back)).isoformat()

            # Get follow-up logs
            logs_result = self.supabase.table("followup_logs").select("*").gte(
                "created_at", since_date
            ).execute()

            logs = logs_result.data if logs_result.data else []

            # Analyze by strategy
            strategy_stats = {}
            for log in logs:
                strategy = log["strategy"]
                if strategy not in strategy_stats:
                    strategy_stats[strategy] = {
                        "count": 0,
                        "responses": 0,
                        "conversions": 0
                    }
                strategy_stats[strategy]["count"] += 1

            # Get response data for these follow-ups
            # This would need to join with response data

            return {
                "success": True,
                "period_days": days_back,
                "total_followups": len(logs),
                "by_strategy": strategy_stats,
                "most_effective_strategy": max(
                    strategy_stats.items(),
                    key=lambda x: x[1]["count"]
                )[0] if strategy_stats else None
            }

        except Exception as e:
            print(f"[FollowUp ERROR] Failed to get analytics: {e}")
            return {"success": False, "error": str(e)}


# Create required tables
CREATE_TABLES_SQL = """
-- Follow-up attempts table
CREATE TABLE IF NOT EXISTS followup_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_id UUID REFERENCES potential_contractors(id),
    bid_card_id UUID REFERENCES bid_cards(id),
    method TEXT NOT NULL,
    content TEXT,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Follow-up logs for analytics
CREATE TABLE IF NOT EXISTS followup_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distribution_id UUID REFERENCES bid_card_distributions(id),
    contractor_id UUID REFERENCES potential_contractors(id),
    bid_card_id UUID REFERENCES bid_cards(id),
    strategy TEXT NOT NULL,
    channel TEXT NOT NULL,
    follow_up_number INTEGER,
    content_preview TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add follow-up fields to bid_card_distributions if not exists
ALTER TABLE bid_card_distributions
ADD COLUMN IF NOT EXISTS last_follow_up_method TEXT;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_followup_attempts_contractor ON followup_attempts(contractor_id);
CREATE INDEX IF NOT EXISTS idx_followup_logs_strategy ON followup_logs(strategy);
CREATE INDEX IF NOT EXISTS idx_followup_logs_created ON followup_logs(created_at);
"""


# Test the automation
if __name__ == "__main__":
    automation = FollowUpAutomation()

    print("\nTesting Follow-up Automation System...")
    print("This will identify contractors who haven't responded and send intelligent follow-ups")
    print()

    # Run follow-up campaign
    result = automation.run_followup_campaign(
        days_since_sent=0,  # For testing, check immediately
        max_follow_ups=2,
        batch_size=5
    )

    print(f"\nCampaign Result: {json.dumps(result, indent=2)}")

    # Get analytics
    analytics = automation.get_followup_analytics(days_back=7)
    print(f"\nFollow-up Analytics: {json.dumps(analytics, indent=2)}")

    print("\nNote: Run the CREATE TABLES SQL in Supabase to set up required tables")
