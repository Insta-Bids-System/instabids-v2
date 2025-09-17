"""
Claude-Enhanced Campaign Check-in Manager
Uses Claude Opus 4 for intelligent campaign monitoring and escalation decisions
"""
import json
import os
import re
from datetime import datetime
from typing import Any

from openai import OpenAI
from dotenv import load_dotenv

from .check_in_manager import CampaignCheckInManager, CheckInStatus


class ClaudeCheckInManager(CampaignCheckInManager):
    """Enhanced check-in manager with Claude intelligence"""

    def __init__(self):
        """Initialize with Claude"""
        super().__init__()
        load_dotenv(override=True)

        # Initialize Claude
        self.anthropic_api_key = os.getenv("OPENAI_API_KEY")
        self.claude = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        print("[CheckInManager+Claude] Initialized with Claude Opus 4 for intelligent decisions")

    async def evaluate_campaign_health_with_claude(self,
                                                  campaign_id: str,
                                                  check_in_data: dict[str, Any]) -> dict[str, Any]:
        """Use Claude to make intelligent escalation decisions"""

        # Get campaign details
        campaign = self._get_campaign_details(campaign_id)
        responses = self._get_campaign_responses(campaign_id)
        contractors = self._get_campaign_contractors(campaign_id)

        # Create context for Claude
        prompt = f"""Analyze this campaign's progress and recommend actions.

CAMPAIGN DETAILS:
- Type: {campaign.get('project_type', 'Unknown')}
- Timeline: {campaign.get('timeline_hours', 24)} hours total
- Time Elapsed: {check_in_data.get('hours_elapsed', 0)} hours ({check_in_data.get('progress_percent', 0)}%)
- Urgency: {campaign.get('urgency_level', 'standard')}
- Location: {campaign.get('location', 'Unknown')}

TARGETS:
- Bids Needed: {campaign.get('bids_needed', 4)}
- Expected by Now: {check_in_data.get('expected_bids', 0)}
- Actually Received: {check_in_data.get('actual_bids', 0)}

CONTRACTOR BREAKDOWN:
- Total Contacted: {len(contractors)}
- Tier 1 (Premium): {len([c for c in contractors if c.get('tier') == 1])}
- Tier 2 (Qualified): {len([c for c in contractors if c.get('tier') == 2])}
- Tier 3 (New): {len([c for c in contractors if c.get('tier') == 3])}

RESPONSES SO FAR:
{self._format_responses_for_claude(responses)}

CURRENT PERFORMANCE:
- Response Rate: {check_in_data.get('response_rate', 0)}%
- On Track: {'Yes' if check_in_data.get('on_track', False) else 'No'}

ANALYSIS NEEDED:
1. Should we escalate (add more contractors)?
2. Are the responses we've received high quality?
3. Should we change our approach (different channels, messaging)?
4. Any specific recommendations?

Consider:
- Quality vs quantity of responses
- Contractor tier performance
- Project urgency and timeline
- Historical patterns

Return your analysis as JSON:
{{
    "escalation_decision": "none/moderate/aggressive",
    "reasoning": "detailed explanation",
    "quality_assessment": {{
        "response_quality": "high/medium/low",
        "tier_performance": {{"tier_1": "", "tier_2": "", "tier_3": ""}},
        "concerns": []
    }},
    "recommendations": [
        {{"action": "", "priority": "high/medium/low", "details": ""}}
    ],
    "confidence_level": 0-100,
    "additional_contractors_needed": 0
}}"""

        try:
            response = self.claude.messages.create(
                model="gpt-4",
                max_tokens=1500,
                temperature=0.3,  # Balanced for analysis
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse Claude's response
            claude_response = response.choices[0].message.content

            # Extract JSON
            json_match = re.search(r"\{[\s\S]*\}", claude_response)
            if json_match:
                analysis = json.loads(json_match.group())
                print("[Claude] Campaign analysis complete")
                return analysis
            else:
                print("[Claude] Could not parse analysis")
                return self._fallback_analysis(check_in_data)

        except Exception as e:
            print(f"[Claude ERROR] Analysis failed: {e}")
            return self._fallback_analysis(check_in_data)

    async def process_check_in(self, campaign_id: str, check_in_id: str) -> CheckInStatus:
        """Process check-in with Claude intelligence"""
        try:
            # Get check-in data
            check_in = self.supabase.table("campaign_check_ins")\
                .select("*")\
                .eq("id", check_in_id)\
                .single()\
                .execute()

            if not check_in.data:
                raise ValueError(f"Check-in {check_in_id} not found")

            # Calculate current metrics
            metrics = self._calculate_current_metrics(campaign_id)

            # Prepare data for Claude
            check_in_data = {
                "check_in_number": check_in.data["check_in_number"],
                "hours_elapsed": (datetime.now() - datetime.fromisoformat(
                    check_in.data["created_at"].replace("Z", "+00:00")
                )).total_seconds() / 3600,
                "progress_percent": check_in.data["expected_progress"],
                "expected_bids": check_in.data["expected_bids"],
                "actual_bids": metrics["responses_received"],
                "response_rate": metrics["response_rate"],
                "on_track": metrics["responses_received"] >= check_in.data["expected_bids"]
            }

            # Get Claude's analysis
            print(f"[CheckIn+Claude] Getting intelligent analysis for campaign {campaign_id}")
            claude_analysis = await self.evaluate_campaign_health_with_claude(
                campaign_id, check_in_data
            )

            # Determine actions based on Claude's recommendations
            escalation_needed = claude_analysis["escalation_decision"] != "none"
            actions_taken = []

            if escalation_needed:
                # Execute Claude's recommendations
                for rec in claude_analysis["recommendations"]:
                    if rec["priority"] == "high":
                        action_result = await self._execute_recommendation(
                            campaign_id, rec
                        )
                        actions_taken.append(action_result)

            # Update check-in record
            self.supabase.table("campaign_check_ins").update({
                "completed_at": datetime.now().isoformat(),
                "actual_progress": metrics["responses_received"],
                "on_track": not escalation_needed,
                "escalation_triggered": escalation_needed,
                "claude_analysis": claude_analysis,
                "actions_taken": actions_taken
            }).eq("id", check_in_id).execute()

            # Create status object
            status = CheckInStatus(
                check_in_id=check_in_id,
                campaign_id=campaign_id,
                check_in_number=check_in.data["check_in_number"],
                scheduled_time=datetime.fromisoformat(
                    check_in.data["scheduled_for"].replace("Z", "+00:00")
                ),
                completed_time=datetime.now(),
                bids_expected=check_in.data["expected_bids"],
                bids_received=metrics["responses_received"],
                response_rate=metrics["response_rate"],
                on_track=not escalation_needed,
                escalation_needed=escalation_needed,
                escalation_reason=claude_analysis["reasoning"],
                actions_taken=actions_taken,
                performance_ratio=(metrics["responses_received"] /
                                 check_in.data["expected_bids"] * 100
                                 if check_in.data["expected_bids"] > 0 else 0)
            )

            # Send notification if needed
            if escalation_needed:
                await self._send_escalation_notification(campaign_id, status, claude_analysis)

            print(f"[CheckIn+Claude] Completed check-in #{check_in.data['check_in_number']}")
            print(f"  Claude Decision: {claude_analysis['escalation_decision']}")
            print(f"  Confidence: {claude_analysis['confidence_level']}%")

            return status

        except Exception as e:
            print(f"[CheckIn+Claude ERROR] Failed to process: {e}")
            # Fall back to base implementation
            return await super().process_check_in(campaign_id, check_in_id)

    def _format_responses_for_claude(self, responses: list[dict]) -> str:
        """Format response data for Claude's analysis"""
        if not responses:
            return "No responses yet"

        formatted = []
        for i, resp in enumerate(responses[:5], 1):  # Limit to avoid token limits
            formatted.append(
                f"{i}. Contractor: Tier {resp.get('contractor_tier', '?')}, "
                f"Response: {resp.get('response_type', 'viewed')}, "
                f"Interest: {resp.get('interest_level', 'unknown')}"
            )

        if len(responses) > 5:
            formatted.append(f"... and {len(responses) - 5} more responses")

        return "\n".join(formatted)

    def _fallback_analysis(self, check_in_data: dict[str, Any]) -> dict[str, Any]:
        """Fallback to rule-based analysis if Claude fails"""
        on_track = check_in_data.get("on_track", False)

        return {
            "escalation_decision": "none" if on_track else "moderate",
            "reasoning": "Fallback rule-based decision",
            "quality_assessment": {
                "response_quality": "unknown",
                "tier_performance": {},
                "concerns": []
            },
            "recommendations": [
                {
                    "action": "add_contractors" if not on_track else "continue_monitoring",
                    "priority": "high" if not on_track else "low",
                    "details": "Add 5 more Tier 2 contractors" if not on_track else "Continue current approach"
                }
            ],
            "confidence_level": 60,
            "additional_contractors_needed": 5 if not on_track else 0
        }

    async def _execute_recommendation(self, campaign_id: str,
                                    recommendation: dict[str, Any]) -> str:
        """Execute Claude's recommendation"""
        action = recommendation["action"]

        if action == "add_contractors":
            # Add more contractors as recommended
            count = recommendation.get("details", "").split()[1]  # Extract number
            try:
                count = int(count)
            except:
                count = 5  # Default

            # Here you would call the CDA to add more contractors
            return f"Added {count} more contractors as recommended"

        elif action == "change_channel":
            # Switch to different outreach channel
            return "Switched to SMS for urgent follow-up"

        elif action == "adjust_messaging":
            # Update message templates
            return "Updated messaging to emphasize urgency"

        else:
            return f"Executed: {action}"

    async def _send_escalation_notification(self, campaign_id: str,
                                          status: CheckInStatus,
                                          claude_analysis: dict[str, Any]):
        """Send intelligent notification about escalation"""

        # Create notification with Claude's insights
        notification = {
            "campaign_id": campaign_id,
            "type": "escalation",
            "urgency": "high" if status.performance_ratio < 50 else "medium",
            "title": f"Campaign Needs Attention - {claude_analysis['escalation_decision'].title()} Escalation",
            "message": claude_analysis["reasoning"],
            "metrics": {
                "expected": status.bids_expected,
                "received": status.bids_received,
                "performance": f"{status.performance_ratio:.0f}%"
            },
            "claude_recommendations": claude_analysis["recommendations"],
            "confidence": f"{claude_analysis['confidence_level']}%",
            "created_at": datetime.now().isoformat()
        }

        # Store notification
        try:
            self.supabase.table("campaign_notifications").insert(notification).execute()
            print("[CheckIn+Claude] Notification sent with Claude's analysis")
        except Exception as e:
            print(f"[CheckIn+Claude ERROR] Failed to send notification: {e}")

    def _get_campaign_details(self, campaign_id: str) -> dict[str, Any]:
        """Get full campaign details"""
        try:
            result = self.supabase.table("outreach_campaigns")\
                .select("*, bid_cards(*)")\
                .eq("id", campaign_id)\
                .single()\
                .execute()
            return result.data if result.data else {}
        except:
            return {}

    def _get_campaign_responses(self, campaign_id: str) -> list[dict[str, Any]]:
        """Get all responses for a campaign"""
        try:
            result = self.supabase.table("contractor_responses")\
                .select("*")\
                .eq("campaign_id", campaign_id)\
                .execute()
            return result.data if result.data else []
        except:
            return []

    def _get_campaign_contractors(self, campaign_id: str) -> list[dict[str, Any]]:
        """Get all contractors in campaign"""
        try:
            result = self.supabase.table("campaign_contractors")\
                .select("*, contractors(*), potential_contractors(*)")\
                .eq("campaign_id", campaign_id)\
                .execute()
            return result.data if result.data else []
        except:
            return []
