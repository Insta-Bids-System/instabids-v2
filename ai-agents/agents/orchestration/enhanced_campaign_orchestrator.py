#!/usr/bin/env python3
"""
Enhanced Campaign Orchestrator with Timing & Probability Engine Integration
Automatically calculates contractor outreach strategy based on timeline and bid requirements
"""

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from supabase import Client, create_client

from .campaign_orchestrator import OutreachCampaignOrchestrator
from .check_in_manager import CampaignCheckInManager
from .timing_probability_engine import ContractorOutreachCalculator, OutreachStrategy


@dataclass
class CampaignRequest:
    """Request to create an intelligent campaign"""
    bid_card_id: str
    project_type: str
    location: dict[str, Any]
    timeline_hours: int
    urgency_level: str
    bids_needed: int = 4  # Default business requirement
    channels: list[str] = None  # Will be auto-selected if not provided
    # NEW: Exact date fields
    project_completion_deadline: datetime = None
    bid_collection_deadline: datetime = None
    deadline_hard: bool = False
    deadline_context: str = None


class EnhancedCampaignOrchestrator:
    """
    Orchestrator that integrates timing engine with campaign execution
    Automatically determines how many contractors to contact based on:
    - Project timeline
    - Bid requirements
    - Contractor tier availability
    - Historical response rates
    """

    def __init__(self):
        """Initialize with all required components"""
        load_dotenv(override=True)

        # Database connection
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

        # Core components
        self.timing_calculator = ContractorOutreachCalculator()
        self.base_orchestrator = OutreachCampaignOrchestrator()
        self.check_in_manager = CampaignCheckInManager()

        print("[Enhanced Orchestrator] Initialized with timing engine integration")

    async def create_intelligent_campaign(self, request: CampaignRequest) -> dict[str, Any]:
        """
        Create a campaign with automatic contractor selection based on timing engine

        This is the main entry point that:
        1. Analyzes contractor availability by tier
        2. Calculates optimal outreach strategy (with date override if provided)
        3. Selects specific contractors
        4. Creates campaign with check-in schedule
        5. Starts execution with monitoring
        """
        try:
            print("\n[Enhanced Orchestrator] Creating Intelligent Campaign")
            print(f"Project: {request.project_type}")
            print(f"Timeline: {request.timeline_hours} hours")
            print(f"Bids Needed: {request.bids_needed}")
            
            # NEW: Check for exact dates and override timeline if provided
            timeline_hours = request.timeline_hours
            
            if request.project_completion_deadline:
                print(f"Exact deadline provided: {request.project_completion_deadline}")
                days_remaining = (request.project_completion_deadline - datetime.now()).days
                
                # Simple override logic based on deadline proximity
                if days_remaining <= 3:
                    timeline_hours = 6  # Rush mode: 6 hours
                    print(f"Rush mode activated: {days_remaining} days remaining, using 6 hours")
                elif days_remaining <= 7:
                    timeline_hours = 24  # Fast track: 1 day
                    print(f"Fast track activated: {days_remaining} days remaining, using 24 hours")
                elif days_remaining <= 14:
                    timeline_hours = 72  # Normal: 3 days
                    print(f"Normal timeline: {days_remaining} days remaining, using 72 hours")
                else:
                    timeline_hours = 120  # Relaxed: 5 days
                    print(f"Relaxed timeline: {days_remaining} days remaining, using 120 hours")

            # Step 1: Analyze contractor availability
            tier_availability = await self._analyze_contractor_availability(
                request.project_type,
                request.location
            )

            # Step 2: Calculate outreach strategy (using potentially overridden timeline)
            strategy = self.timing_calculator.calculate_outreach_strategy(
                bids_needed=request.bids_needed,
                timeline_hours=timeline_hours,
                tier1_available=tier_availability["tier_1"],
                tier2_available=tier_availability["tier_2"],
                tier3_available=tier_availability["tier_3"],
                project_type=request.project_type,
                location=request.location
            )

            # Display strategy
            self._display_strategy(strategy)

            # Step 3: Select specific contractors based on strategy
            selected_contractors = await self._select_contractors_by_strategy(
                strategy,
                request.project_type,
                request.location
            )

            # Step 4: Determine channels if not specified
            if not request.channels:
                request.channels = self._determine_optimal_channels(
                    strategy.urgency_level.value,
                    selected_contractors
                )

            # Step 5: Create the campaign
            campaign_name = f"{request.project_type} - {strategy.urgency_level.value} ({request.bids_needed} bids)"

            # Note: The base orchestrator expects channels, but the DB doesn't have this column
            # We'll store channels in the campaign_contractors table instead
            campaign_result = self.base_orchestrator.create_campaign(
                name=campaign_name,
                bid_card_id=request.bid_card_id,
                contractor_ids=[c["id"] for c in selected_contractors],
                channels=request.channels,  # This will be used for campaign_contractors, not outreach_campaigns
                schedule={
                    "start_time": datetime.now().isoformat(),
                    "urgency": strategy.urgency_level.value,
                    "strategy": {
                        "total_contractors": strategy.total_to_contact,
                        "expected_responses": strategy.expected_total_responses,
                        "confidence_score": strategy.confidence_score
                    }
                }
            )

            if not campaign_result.get("success"):
                return campaign_result

            campaign_id = campaign_result["campaign_id"]

            # Step 6: Schedule check-ins
            check_ins = await self.check_in_manager.schedule_campaign_check_ins(
                campaign_id=campaign_id,
                bid_card_id=request.bid_card_id,
                strategy=strategy
            )

            # Step 7: Store strategy details for monitoring
            self._store_campaign_strategy(campaign_id, strategy, selected_contractors)

            return {
                "success": True,
                "campaign_id": campaign_id,
                "strategy": {
                    "urgency": strategy.urgency_level.value,
                    "total_contractors": strategy.total_to_contact,
                    "tier_1": strategy.tier1_strategy.to_contact,
                    "tier_2": strategy.tier2_strategy.to_contact,
                    "tier_3": strategy.tier3_strategy.to_contact,
                    "expected_responses": strategy.expected_total_responses,
                    "confidence_score": strategy.confidence_score,
                    "risk_factors": strategy.risk_factors,
                    "recommendations": strategy.recommendations
                },
                "check_ins": [
                    {
                        "time": check_in["scheduled_time"],
                        "expected_bids": check_in["expected_bids"]
                    } for check_in in check_ins
                ]
            }

        except Exception as e:
            print(f"[Enhanced Orchestrator ERROR] Failed to create campaign: {e}")
            return {"success": False, "error": str(e)}

    async def execute_campaign_with_monitoring(self, campaign_id: str) -> dict[str, Any]:
        """
        Execute campaign and start monitoring for check-ins
        """
        try:
            # Start the base execution
            execution_result = self.base_orchestrator.execute_campaign(campaign_id)

            if execution_result.get("success"):
                # Start monitoring in background
                asyncio.create_task(
                    self._monitor_campaign_progress(campaign_id)
                )

            return execution_result

        except Exception as e:
            print(f"[Enhanced Orchestrator ERROR] Execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def _analyze_contractor_availability(self,
                                             project_type: str,
                                             location: dict[str, Any]) -> dict[str, int]:
        """
        Analyze how many contractors are available in each tier
        """
        try:
            # Get location details
            location.get("state", "")
            location.get("city", "")

            # Count Tier 1: Internal contractors (signed up for InstaBids)
            tier1_result = self.supabase.table("contractors")\
                .select("id")\
                .execute()
            tier1_count = len(tier1_result.data) if tier1_result.data else 0

            # Count Tier 2: Previously contacted contractors (have outreach history)
            tier2_result = self.supabase.rpc("count_contractors_with_outreach_history").execute()
            tier2_count = tier2_result.data if tier2_result.data else 0

            # Count Tier 3: Never contacted contractors (no outreach history)
            tier3_result = self.supabase.rpc("count_contractors_without_outreach_history").execute()
            tier3_count = tier3_result.data if tier3_result.data else 0

            print("\n[Contractor Availability]")
            print(f"  Tier 1 (Internal): {tier1_count}")
            print(f"  Tier 2 (Prospects): {tier2_count}")
            print(f"  Tier 3 (New/Cold): {tier3_count}")

            return {
                "tier_1": tier1_count,
                "tier_2": tier2_count,
                "tier_3": tier3_count
            }

        except Exception as e:
            print(f"[Enhanced Orchestrator ERROR] Failed to analyze availability: {e}")
            # Return conservative estimates
            return {"tier_1": 5, "tier_2": 20, "tier_3": 100}

    async def _select_contractors_by_strategy(self,
                                            strategy: OutreachStrategy,
                                            project_type: str,
                                            location: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Select specific contractors based on the calculated strategy
        """
        selected = []

        # Select Tier 1 contractors
        if strategy.tier1_strategy.to_contact > 0:
            tier1 = await self._select_tier_contractors(
                tier=1,
                count=strategy.tier1_strategy.to_contact,
                project_type=project_type,
                location=location
            )
            selected.extend(tier1)

        # Select Tier 2 contractors
        if strategy.tier2_strategy.to_contact > 0:
            tier2 = await self._select_tier_contractors(
                tier=2,
                count=strategy.tier2_strategy.to_contact,
                project_type=project_type,
                location=location
            )
            selected.extend(tier2)

        # Select Tier 3 contractors
        if strategy.tier3_strategy.to_contact > 0:
            tier3 = await self._select_tier_contractors(
                tier=3,
                count=strategy.tier3_strategy.to_contact,
                project_type=project_type,
                location=location
            )
            selected.extend(tier3)

        print("\n[Contractor Selection Complete]")
        print(f"  Total Selected: {len(selected)}")
        print(f"  Tier 1: {len([c for c in selected if c.get('tier') == 1])}")
        print(f"  Tier 2: {len([c for c in selected if c.get('tier') == 2])}")
        print(f"  Tier 3: {len([c for c in selected if c.get('tier') == 3])}")

        return selected

    def _get_project_keywords(self, project_type: str) -> list[str]:
        """
        Get relevant keywords for matching contractors to project types
        """
        keyword_map = {
            "kitchen_remodel": ["kitchen", "remodel", "cabinets", "countertop", "appliance"],
            "bathroom_remodel": ["bathroom", "bath", "shower", "tub", "plumbing"],
            "roofing": ["roof", "shingle", "gutter", "flashing"],
            "flooring": ["floor", "hardwood", "tile", "carpet", "laminate"],
            "painting": ["paint", "painter", "interior", "exterior", "wall"],
            "landscaping": ["landscape", "lawn", "garden", "yard", "irrigation"],
            "hvac": ["hvac", "heating", "cooling", "air", "furnace", "ac"],
            "plumbing": ["plumb", "pipe", "water", "drain", "fixture"],
            "electrical": ["electric", "wiring", "outlet", "panel", "lighting"],
            "general": ["general", "contractor", "remodel", "renovation"]
        }
        return keyword_map.get(project_type, [project_type])
    
    async def _select_tier_contractors(self,
                                     tier: int,
                                     count: int,
                                     project_type: str,
                                     location: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Select specific contractors from a tier
        """
        try:
            if tier == 1:
                # Select from contractor_leads for Tier 1 (highest quality leads)
                # These are verified contractors with good scores
                try:
                    # Build base query with all fields we need
                    query = self.supabase.table("contractor_leads")\
                        .select("id, company_name, email, phone, specialties, city, state, zip_code")\
                        .gte("lead_score", 80)
                    
                    # Filter by location if provided
                    if location and location.get("state"):
                        query = query.eq("state", location["state"])
                    if location and location.get("city"):
                        query = query.eq("city", location["city"])
                    
                    # Execute query
                    result = query.limit(count * 3).execute()  # Get extra to filter by specialties
                    all_contractors = result.data if result.data else []
                    
                    # Filter by project type matching specialties
                    contractors = []
                    for contractor in all_contractors:
                        if contractor.get("specialties"):
                            # Check if any specialty matches the project type
                            specialties_str = " ".join(str(s).lower() for s in contractor["specialties"])
                            if project_type and any(keyword in specialties_str for keyword in self._get_project_keywords(project_type)):
                                contractors.append(contractor)
                                if len(contractors) >= count:
                                    break
                    
                    # If not enough matches, get any high-score contractors as fallback
                    if len(contractors) < count:
                        for contractor in all_contractors:
                            if contractor not in contractors:
                                contractors.append(contractor)
                                if len(contractors) >= count:
                                    break

                    # Add tier info
                    for c in contractors[:count]:  # Ensure we don't exceed count
                        c["tier"] = 1
                    
                    contractors = contractors[:count]
                except Exception as e:
                    print(f"[Orchestrator ERROR] Failed to select Tier 1: {e}")
                    # Fallback: use potential_contractors as Tier 1
                    result = self.supabase.table("potential_contractors")\
                        .select("id, company_name, email, phone")\
                        .gte("lead_score", 80)\
                        .eq("lead_status", "contacted")\
                        .limit(count)\
                        .execute()
                    contractors = result.data if result.data else []
                    for c in contractors:
                        c["tier"] = 1

            elif tier == 2:
                # Select from prospects (enriched but not contacted)
                query = self.supabase.table("potential_contractors")\
                    .select("*")\
                    .eq("lead_status", "enriched")\
                    .order("lead_score", desc=True)
                
                # Filter by location if provided
                if location and location.get("state"):
                    query = query.eq("state", location["state"])
                
                # Filter by project type if provided
                if project_type:
                    query = query.eq("project_type", project_type)
                
                result = query.limit(count).execute()
                contractors = result.data if result.data else []
                
                # Add tier info and ensure we have required fields
                for c in contractors:
                    c["tier"] = 2
                    # Ensure required fields exist
                    if not c.get("id"):
                        c["id"] = c.get("contractor_lead_id", str(uuid.uuid4()))

            else:  # tier == 3
                # Select from new/cold (new or qualified status)
                query = self.supabase.table("potential_contractors")\
                    .select("*")\
                    .in_("lead_status", ["new", "qualified"])\
                    .order("lead_score", desc=True)
                
                # Filter by location if provided
                if location and location.get("state"):
                    query = query.eq("state", location["state"])
                
                # Filter by project type if provided  
                if project_type:
                    query = query.eq("project_type", project_type)
                
                result = query.limit(count).execute()
                contractors = result.data if result.data else []
                
                # Add tier info and ensure we have required fields
                for c in contractors:
                    c["tier"] = 3
                    # Ensure required fields exist
                    if not c.get("id"):
                        c["id"] = c.get("contractor_lead_id", str(uuid.uuid4()))

            return contractors

        except Exception as e:
            print(f"[Enhanced Orchestrator ERROR] Failed to select tier {tier} contractors: {e}")
            return []

    def _determine_optimal_channels(self,
                                  urgency: str,
                                  contractors: list[dict[str, Any]]) -> list[str]:
        """
        Determine optimal channels based on urgency and contractor data
        Updated: Email + Forms for ALL urgency levels (per business requirements)
        """
        if urgency in ["emergency", "urgent"]:
            # For urgent projects, use email, forms, and SMS
            return ["email", "website_form", "sms"]
        else:
            # All other projects: email and website forms (standard approach)
            return ["email", "website_form"]

    def _display_strategy(self, strategy: OutreachStrategy):
        """
        Display the calculated strategy in a readable format
        """
        print("\n[Outreach Strategy Calculated]")
        print(f"  Urgency: {strategy.urgency_level.value}")
        print(f"  Timeline: {strategy.timeline_hours} hours")
        print(f"  Bids Needed: {strategy.bids_needed}")
        print("\n  Contractor Distribution:")
        print(f"    Tier 1: {strategy.tier1_strategy.to_contact} contractors (expect {strategy.tier1_strategy.expected_responses:.1f} responses)")
        print(f"    Tier 2: {strategy.tier2_strategy.to_contact} contractors (expect {strategy.tier2_strategy.expected_responses:.1f} responses)")
        print(f"    Tier 3: {strategy.tier3_strategy.to_contact} contractors (expect {strategy.tier3_strategy.expected_responses:.1f} responses)")
        print(f"\n  Total: {strategy.total_to_contact} contractors")
        print(f"  Expected Responses: {strategy.expected_total_responses:.1f}")
        print(f"  Confidence Score: {strategy.confidence_score}%")

        if strategy.risk_factors:
            print("\n  Risk Factors:")
            for risk in strategy.risk_factors:
                print(f"    ! {risk}")

        if strategy.recommendations:
            print("\n  Recommendations:")
            for rec in strategy.recommendations:
                print(f"    -> {rec}")

    def _store_campaign_strategy(self,
                               campaign_id: str,
                               strategy: OutreachStrategy,
                               contractors: list[dict[str, Any]]):
        """
        Store the campaign strategy for future reference
        """
        try:
            strategy_data = {
                "campaign_id": campaign_id,
                "urgency_level": strategy.urgency_level.value,
                "timeline_hours": strategy.timeline_hours,
                "bids_needed": strategy.bids_needed,
                "total_contractors": strategy.total_to_contact,
                "expected_responses": strategy.expected_total_responses,
                "confidence_score": strategy.confidence_score,
                "tier_breakdown": {
                    "tier_1": {
                        "count": strategy.tier1_strategy.to_contact,
                        "expected": strategy.tier1_strategy.expected_responses
                    },
                    "tier_2": {
                        "count": strategy.tier2_strategy.to_contact,
                        "expected": strategy.tier2_strategy.expected_responses
                    },
                    "tier_3": {
                        "count": strategy.tier3_strategy.to_contact,
                        "expected": strategy.tier3_strategy.expected_responses
                    }
                },
                "risk_factors": strategy.risk_factors,
                "recommendations": strategy.recommendations,
                "contractor_ids": [c["id"] for c in contractors],
                "created_at": datetime.now().isoformat()
            }

            # Store in campaign metadata
            self.supabase.table("outreach_campaigns")\
                .update({"strategy_data": strategy_data})\
                .eq("id", campaign_id)\
                .execute()

        except Exception as e:
            print(f"[Enhanced Orchestrator ERROR] Failed to store strategy: {e}")

    async def _monitor_campaign_progress(self, campaign_id: str):
        """
        Background task to monitor campaign progress and trigger check-ins
        """
        try:
            print(f"\n[Campaign Monitor] Starting monitoring for campaign {campaign_id}")

            # Get check-in schedule
            check_ins = self.supabase.table("campaign_check_ins")\
                .select("*")\
                .eq("campaign_id", campaign_id)\
                .is_("completed_at", "null")\
                .order("scheduled_time")\
                .execute()

            if not check_ins.data:
                print("[Campaign Monitor] No check-ins scheduled")
                return

            for check_in in check_ins.data:
                # Wait until check-in time
                scheduled_time = datetime.fromisoformat(check_in["scheduled_time"])
                wait_seconds = (scheduled_time - datetime.now()).total_seconds()

                if wait_seconds > 0:
                    print(f"[Campaign Monitor] Waiting {wait_seconds/60:.1f} minutes until check-in #{check_in['check_in_number']}")
                    await asyncio.sleep(wait_seconds)

                # Perform check-in
                print(f"\n[Campaign Monitor] Performing check-in #{check_in['check_in_number']}")
                status = await self.check_in_manager.perform_check_in(
                    campaign_id,
                    check_in["id"]
                )

                # Display results
                print("[Check-in Results]")
                print(f"  Expected Bids: {status.bids_expected}")
                print(f"  Received Bids: {status.bids_received}")
                print(f"  Performance: {status.performance_ratio:.1f}%")
                print(f"  On Track: {'Yes' if status.on_track else 'No'}")

                if status.escalation_needed:
                    print("  ESCALATION TRIGGERED!")
                    print(f"  Actions Taken: {', '.join(status.actions_taken)}")

                # If critical performance, alert immediately
                if status.performance_ratio < 25:
                    await self._send_critical_alert(campaign_id, status)

            print(f"\n[Campaign Monitor] Monitoring complete for campaign {campaign_id}")

        except Exception as e:
            print(f"[Campaign Monitor ERROR] {e}")

    async def _send_critical_alert(self,
                                 campaign_id: str,
                                 status: Any):
        """
        Send critical alert when campaign is severely underperforming
        """
        # In production, this would send SMS/email to admin
        print("\n!!! CRITICAL ALERT !!!")
        print(f"Campaign {campaign_id} is severely underperforming")
        print(f"Only {status.bids_received} of {status.bids_expected} bids received")
        print("Manual intervention may be required")


# Example usage
async def test_enhanced_orchestrator():
    """Test the enhanced orchestrator with timing integration"""
    orchestrator = EnhancedCampaignOrchestrator()

    # Test scenario: Kitchen remodel with 24-hour timeline
    request = CampaignRequest(
        bid_card_id="test-kitchen-123",
        project_type="Kitchen Remodel",
        location={"city": "Austin", "state": "TX"},
        timeline_hours=24,
        urgency_level="urgent",
        bids_needed=4
    )

    print("\n" + "="*70)
    print("TESTING ENHANCED CAMPAIGN ORCHESTRATOR")
    print("="*70)

    # Create intelligent campaign
    result = await orchestrator.create_intelligent_campaign(request)

    if result.get("success"):
        print(f"\n[SUCCESS] Campaign created: {result['campaign_id']}")
        print("\nStrategy Summary:")
        print(f"  Total Contractors: {result['strategy']['total_contractors']}")
        print(f"  Expected Responses: {result['strategy']['expected_responses']:.1f}")
        print(f"  Confidence Score: {result['strategy']['confidence_score']:.1f}%")

        # Execute with monitoring
        print("\n[Starting Campaign Execution...]")
        execution_result = await orchestrator.execute_campaign_with_monitoring(
            result["campaign_id"]
        )

        if execution_result.get("success"):
            print("\n[Campaign Launched Successfully]")
            print("Monitoring will continue in background...")

            # Keep the script running to see monitoring results
            await asyncio.sleep(3600)  # Wait 1 hour for demo

    else:
        print(f"\n[FAILED] {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(test_enhanced_orchestrator())
