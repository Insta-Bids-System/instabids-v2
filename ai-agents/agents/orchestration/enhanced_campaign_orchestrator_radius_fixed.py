#!/usr/bin/env python3
"""
Enhanced Campaign Orchestrator with BSA's Radius Search System
Implements 15-mile radius constraint and contractor size filtering
"""

import asyncio
import math
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from supabase import Client, create_client

# Import BSA's radius search system
from utils.radius_search_fixed import filter_by_radius

# Import database for contractor type mappings
from database_simple import db

from .campaign_orchestrator import OutreachCampaignOrchestrator
from .check_in_manager import CampaignCheckInManager  
from .timing_probability_engine import ContractorOutreachCalculator, OutreachStrategy

# Import the new intelligent contractor discovery system
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Contractor Outreach System', 'tools'))
from intelligent_contractor_discovery import IntelligentContractorDiscovery


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
    contractor_size_preference: Optional[int] = None  # 1-5 size preference
    # NEW: Exact date fields
    project_completion_deadline: datetime = None
    bid_collection_deadline: datetime = None
    deadline_hard: bool = False
    deadline_context: str = None


class EnhancedCampaignOrchestratorRadiusFixed:
    """
    Enhanced Campaign Orchestrator with 15-mile radius constraint using BSA's system
    """

    def __init__(self):
        """Initialize with all required components"""
        load_dotenv(override=True)
        
        # Supabase connection
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Initialize components
        self.calculator = ContractorOutreachCalculator()
        self.orchestrator = OutreachCampaignOrchestrator()
        self.check_in_manager = CampaignCheckInManager()
        
        # Initialize the intelligent contractor discovery system
        self.intelligent_discovery = IntelligentContractorDiscovery()

    def _get_contractor_size_name(self, size_number: int) -> str:
        """Convert size number (1-5) to contractor_size field value"""
        size_map = {
            1: "solo_handyman",
            2: "owner_operator", 
            3: "small_business",
            4: "regional_company",
            5: "enterprise"  # May need to be added to database
        }
        return size_map.get(size_number, "small_business")

    async def _select_tier_contractors_with_radius(self,
                                           tier: int,
                                           count: int,
                                           project_type: str,
                                           location: dict[str, Any],
                                           contractor_size_preference: Optional[int] = None) -> list[dict[str, Any]]:
        """
        Select contractors from a tier using 15-mile radius constraint (BSA system)
        """
        try:
            project_zip = location.get("zip", location.get("location_zip", "32801"))
            
            print(f"[Enhanced Orchestrator] Selecting Tier {tier} contractors")
            print(f"   Location: ZIP {project_zip} (15-mile radius)")
            print(f"   Project Type: {project_type}")
            print(f"   Contractor Size: {contractor_size_preference}")
            print(f"   Count Needed: {count}")
            
            if tier == 1:
                # Tier 1: contractor_leads (highest quality)
                result = self.supabase.table("contractor_leads")\
                    .select("id, company_name, email, phone, specialties, city, state, zip_code, contractor_size")\
                    .gte("lead_score", 80)\
                    .execute()
                
                all_contractors = result.data if result.data else []
                print(f"   Found {len(all_contractors)} Tier 1 contractors before radius filtering")
                
            elif tier == 2:
                # Tier 2: potential_contractors with "enriched" status
                result = self.supabase.table("potential_contractors")\
                    .select("id, company_name, email, phone, specialties, city, state, zip_code")\
                    .eq("lead_status", "enriched")\
                    .execute()
                
                all_contractors = result.data if result.data else []
                print(f"   Found {len(all_contractors)} Tier 2 contractors before radius filtering")
                
            else:  # tier == 3
                # Tier 3: potential_contractors with "new" or "qualified" status
                result = self.supabase.table("potential_contractors")\
                    .select("id, company_name, email, phone, specialties, city, state, zip_code")\
                    .in_("lead_status", ["new", "qualified"])\
                    .execute()
                
                all_contractors = result.data if result.data else []
                print(f"   Found {len(all_contractors)} Tier 3 contractors before radius filtering")

            # Step 1: Apply 15-mile radius constraint using BSA's system
            contractors_in_radius = filter_by_radius(
                items=all_contractors,
                center_zip=project_zip,
                radius_miles=15,  # Hard-coded 15-mile radius per business requirement
                zip_field="zip_code"
            )
            
            print(f"   After 15-mile radius filtering: {len(contractors_in_radius)} contractors")
            
            # Step 2: Apply contractor size filtering if specified
            if contractor_size_preference:
                target_size = self._get_contractor_size_name(contractor_size_preference)
                size_filtered = [
                    c for c in contractors_in_radius 
                    if c.get("contractor_size") == target_size
                ]
                print(f"   After size filtering ({target_size}): {len(size_filtered)} contractors")
                contractors_in_radius = size_filtered
            
            # Step 3: Apply project type specialty filtering using proper database mappings
            specialty_matched = []
            valid_contractor_types = await self._get_valid_contractor_types(project_type)
            
            for contractor in contractors_in_radius:
                if contractor.get("specialties"):
                    # Convert specialties to a searchable format
                    contractor_specialties = [str(s).strip().lower() for s in contractor["specialties"]]
                    
                    # Check if any contractor specialty matches valid contractor types
                    # Use bidirectional matching for better coverage
                    is_match = False
                    for specialty in contractor_specialties:
                        for valid_type in valid_contractor_types:
                            # Check both directions: valid_type in specialty OR specialty in valid_type
                            if (valid_type.lower() in specialty or 
                                specialty in valid_type.lower() or
                                self._fuzzy_match(specialty, valid_type)):
                                is_match = True
                                break
                        if is_match:
                            break
                    
                    if is_match:
                        specialty_matched.append(contractor)
                        print(f"     [MATCH] {contractor.get('company_name', 'Unknown')} - specialties: {contractor_specialties}")
                    else:
                        print(f"     [NO MATCH] {contractor.get('company_name', 'Unknown')} - specialties: {contractor_specialties}")
            
            print(f"   After proper database specialty filtering: {len(specialty_matched)} contractors")
            print(f"   Valid contractor types for '{project_type}': {valid_contractor_types}")
            
            # Step 4: Add tier information and return requested count
            final_contractors = []
            for contractor in specialty_matched[:count]:
                contractor["tier"] = tier
                # Ensure contractor has an id
                if not contractor.get("id"):
                    contractor["id"] = str(uuid.uuid4())
                final_contractors.append(contractor)
            
            print(f"   Final selection: {len(final_contractors)} contractors for Tier {tier}")
            return final_contractors
            
        except Exception as e:
            print(f"[Enhanced Orchestrator ERROR] Failed to select Tier {tier} contractors: {e}")
            return []

    def _fuzzy_match(self, specialty: str, valid_type: str) -> bool:
        """Fuzzy matching for contractor types and specialties"""
        # Common contractor type matching patterns
        patterns = {
            "general contracting": ["general contractor", "general", "contractor", "gc"],
            "plumbing": ["plumber", "plumb", "pipe", "water"],
            "handyman": ["handyperson", "handy", "maintenance", "repair"],
            "electrical": ["electrician", "electric", "wiring"],
            "landscaping": ["landscape", "lawn", "garden", "yard"],
            "roofing": ["roof", "roofer", "shingle"],
            "hvac": ["heating", "cooling", "air conditioning", "furnace"]
        }
        
        specialty = specialty.lower().strip()
        valid_type = valid_type.lower().strip()
        
        # Direct matching
        if specialty == valid_type:
            return True
            
        # Pattern-based matching
        for category, keywords in patterns.items():
            if valid_type in category or category in valid_type:
                if any(keyword in specialty for keyword in keywords):
                    return True
            if specialty in category or category in specialty:
                if any(keyword in valid_type for keyword in keywords):
                    return True
                    
        return False

    async def _get_valid_contractor_types(self, project_type: str) -> List[str]:
        """Get valid contractor types for project type using proper database mappings"""
        try:
            # First, find the project type ID
            project_type_result = db.client.table('project_types').select('id').ilike('name', f'%{project_type}%').execute()
            
            if not project_type_result.data:
                # Fallback to basic project type name matching
                print(f"[WARNING] No project type found for '{project_type}', using fallback")
                return [project_type.title(), "General Contracting", "Handyman"]
            
            project_type_id = project_type_result.data[0]['id']
            
            # Get mapped contractor type IDs
            mappings_result = db.client.table('project_type_contractor_mappings').select('contractor_type_id').eq('project_type_id', project_type_id).execute()
            
            if not mappings_result.data:
                print(f"[WARNING] No contractor type mappings found for project_type_id {project_type_id}")
                return [project_type.title(), "General Contracting", "Handyman"]
            
            contractor_type_ids = [m['contractor_type_id'] for m in mappings_result.data]
            
            # Get contractor type names
            contractor_types_result = db.client.table('contractor_types').select('name').in_('id', contractor_type_ids).execute()
            
            valid_contractor_types = [ct['name'] for ct in contractor_types_result.data]
            
            print(f"[MATCHING] Project '{project_type}' accepts contractor types: {valid_contractor_types}")
            return valid_contractor_types
            
        except Exception as e:
            print(f"[ERROR] Failed to get contractor types for '{project_type}': {e}")
            # Fallback to basic matching
            return [project_type.title(), "General Contracting", "Handyman"]

    async def _discover_tier3_contractors_intelligent(self, 
                                                    project_type: str, 
                                                    location: dict[str, Any], 
                                                    needed_count: int,
                                                    contractor_size_preference: Optional[int] = None) -> List[dict[str, Any]]:
        """
        Discover Tier 3 contractors using the intelligent discovery system
        Combines Google Business search with website analysis for company size detection
        """
        try:
            print(f"[INTELLIGENT DISCOVERY] Starting intelligent discovery for {project_type} in {location}")
            print(f"[INTELLIGENT DISCOVERY] Target count: {needed_count}, Size preference: {contractor_size_preference}")
            
            # Convert size preference to string format
            size_preference = None
            if contractor_size_preference:
                size_map = {
                    1: "solo_handyman",
                    2: "owner_operator", 
                    3: "small_business",
                    4: "regional_company",
                    5: "enterprise"
                }
                size_preference = size_map.get(contractor_size_preference)
            
            # Use the intelligent discovery system
            discovery_result = await self.intelligent_discovery.discover_and_validate_contractors(
                project_type=project_type,
                location=location,
                target_count=needed_count,
                company_size_preference=size_preference
            )
            
            discovered_contractors = []
            
            if discovery_result.get("success", False):
                raw_contractors = discovery_result.get("contractors", [])
                
                for contractor_data in raw_contractors:
                    # Convert to the format expected by the orchestrator
                    contractor = {
                        "id": str(uuid.uuid4()),
                        "company_name": contractor_data.get("company_name", "Unknown"),
                        "phone": contractor_data.get("phone", ""),
                        "email": contractor_data.get("email", ""),
                        "website": contractor_data.get("website", ""),
                        "address": contractor_data.get("address", ""),
                        "city": location.get("city", "Orlando"),
                        "state": location.get("state", "FL"),
                        "zip_code": location.get("zip", "32801"),
                        "specialties": contractor_data.get("specialties", [project_type]),
                        "contractor_size": contractor_data.get("company_size", "small_business"),
                        "google_rating": contractor_data.get("google_rating", 0),
                        "google_review_count": contractor_data.get("google_review_count", 0),
                        "google_maps_url": contractor_data.get("google_maps_url", ""),
                        "google_place_id": contractor_data.get("google_place_id", ""),
                        "tier": 3,  # Intelligent discoveries are Tier 3
                        "lead_status": "new",
                        "discovery_source": "intelligent_discovery",
                        
                        # Additional intelligent discovery data
                        "website_analysis": contractor_data.get("website_analysis", {}),
                        "validation_score": contractor_data.get("validation_score", 0),
                        "size_confidence": contractor_data.get("size_confidence", "low"),
                        "years_in_business": contractor_data.get("years_in_business"),
                        "employee_count": contractor_data.get("employee_count"),
                        "certifications": contractor_data.get("certifications", []),
                        "license_verified": contractor_data.get("license_verified", False),
                        "insurance_verified": contractor_data.get("insurance_verified", False)
                    }
                    
                    discovered_contractors.append(contractor)
                    
                    # Save to potential_contractors table for future use
                    await self._save_discovered_contractor(contractor, project_type)
                    
                    print(f"[INTELLIGENT SUCCESS] Found: {contractor['company_name']} "
                          f"(Rating: {contractor['google_rating']}/5, "
                          f"Size: {contractor['contractor_size']}, "
                          f"Validation: {contractor['validation_score']}/100)")
            
            print(f"[INTELLIGENT DISCOVERY] Total discovered: {len(discovered_contractors)} contractors")
            print(f"[INTELLIGENT DISCOVERY] Discovery stats: {discovery_result.get('discovery_stats', {})}")
            
            return discovered_contractors
            
        except Exception as e:
            print(f"[INTELLIGENT DISCOVERY ERROR] Failed to discover contractors: {e}")
            # Fallback to empty list - let the orchestrator handle escalation
            return []

    async def _save_discovered_contractor(self, contractor: dict[str, Any], project_type: str):
        """Save discovered contractor to potential_contractors table with intelligent discovery data"""
        try:
            # Prepare contractor data for database storage
            contractor_record = {
                "company_name": contractor["company_name"],
                "phone": contractor["phone"],
                "email": contractor["email"],
                "website": contractor["website"],
                "address": contractor["address"],
                "city": contractor["city"],
                "state": contractor["state"],
                "zip_code": contractor["zip_code"],
                "specialties": contractor["specialties"],
                "lead_status": "new",
                "discovery_source": contractor.get("discovery_source", "intelligent_discovery"),
                "project_type": project_type,
                "google_rating": contractor.get("google_rating"),
                "google_review_count": contractor.get("google_review_count"),
                "google_maps_url": contractor.get("google_maps_url"),
                "google_place_id": contractor.get("google_place_id"),
                
                # Additional intelligent discovery fields
                "contractor_size": contractor.get("contractor_size", "small_business"),
                "years_in_business": contractor.get("years_in_business"),
                "employee_count": contractor.get("employee_count"),
                "certifications": contractor.get("certifications", []),
                "license_verified": contractor.get("license_verified", False),
                "insurance_verified": contractor.get("insurance_verified", False),
                "validation_score": contractor.get("validation_score", 0),
                "size_confidence": contractor.get("size_confidence", "low"),
                "website_analysis": contractor.get("website_analysis", {})
            }
            
            # Insert into potential_contractors table
            result = self.supabase.table("potential_contractors").insert(contractor_record).execute()
            
            if result.data:
                print(f"[DATABASE] Saved intelligent contractor: {contractor['company_name']} to potential_contractors")
                print(f"[DATABASE]   Size: {contractor.get('contractor_size', 'unknown')}, "
                      f"Validation: {contractor.get('validation_score', 0)}/100, "
                      f"Source: {contractor.get('discovery_source', 'unknown')}")
            else:
                print(f"[DATABASE WARNING] Could not save contractor: {contractor['company_name']}")
                
        except Exception as e:
            print(f"[DATABASE ERROR] Failed to save contractor {contractor.get('company_name', 'Unknown')}: {e}")
            # If specific fields cause issues, try with basic fields only
            try:
                basic_record = {
                    "company_name": contractor["company_name"],
                    "phone": contractor.get("phone", ""),
                    "email": contractor.get("email", ""),
                    "website": contractor.get("website", ""),
                    "address": contractor.get("address", ""),
                    "city": contractor["city"],
                    "state": contractor["state"],
                    "zip_code": contractor["zip_code"],
                    "specialties": contractor["specialties"],
                    "lead_status": "new",
                    "discovery_source": contractor.get("discovery_source", "intelligent_discovery"),
                    "project_type": project_type
                }
                result = self.supabase.table("potential_contractors").insert(basic_record).execute()
                if result.data:
                    print(f"[DATABASE] Saved basic contractor record: {contractor['company_name']}")
            except Exception as fallback_error:
                print(f"[DATABASE ERROR] Even basic save failed: {fallback_error}")

    async def create_intelligent_campaign(self, request: CampaignRequest) -> dict[str, Any]:
        """
        Create an intelligent campaign with 15-mile radius constraint and escalation logic
        """
        try:
            print(f"\n[Enhanced Orchestrator] Creating intelligent campaign")
            print(f"   Bid Card ID: {request.bid_card_id}")
            print(f"   Project Type: {request.project_type}")
            print(f"   Location: {request.location}")
            print(f"   Timeline: {request.timeline_hours} hours")
            print(f"   Bids Needed: {request.bids_needed}")
            
            # Step 1: Calculate optimal outreach strategy
            strategy = self.calculator.calculate_outreach_strategy(
                bids_needed=request.bids_needed,
                timeline_hours=request.timeline_hours,
                project_type=request.project_type,
                location=request.location
            )
            
            print(f"\n[Strategy] Need to contact {strategy.total_to_contact} total contractors:")
            print(f"   Tier 1: {strategy.tier1_strategy.to_contact}")
            print(f"   Tier 2: {strategy.tier2_strategy.to_contact}")
            print(f"   Tier 3: {strategy.tier3_strategy.to_contact}")
            
            # Step 2: Select contractors from each tier with 15-mile radius constraint
            selected_contractors = []
            
            # Try Tier 1 first
            if strategy.tier1_strategy.to_contact > 0:
                tier1_contractors = await self._select_tier_contractors_with_radius(
                    tier=1,
                    count=strategy.tier1_strategy.to_contact,
                    project_type=request.project_type,
                    location=request.location,
                    contractor_size_preference=request.contractor_size_preference
                )
                selected_contractors.extend(tier1_contractors)
            
            # Try Tier 2 if needed
            if strategy.tier2_strategy.to_contact > 0:
                tier2_contractors = await self._select_tier_contractors_with_radius(
                    tier=2,
                    count=strategy.tier2_strategy.to_contact,
                    project_type=request.project_type,
                    location=request.location,
                    contractor_size_preference=request.contractor_size_preference
                )
                selected_contractors.extend(tier2_contractors)
            
            # Try Tier 3 if needed
            if strategy.tier3_strategy.to_contact > 0:
                tier3_contractors = await self._select_tier_contractors_with_radius(
                    tier=3,
                    count=strategy.tier3_strategy.to_contact,
                    project_type=request.project_type,
                    location=request.location,
                    contractor_size_preference=request.contractor_size_preference
                )
                selected_contractors.extend(tier3_contractors)
            
            print(f"\n[Selection Results] Found {len(selected_contractors)} contractors within 15-mile radius")
            
            # Step 3: Escalation logic - if not enough contractors found
            if len(selected_contractors) < 4:  # Minimum viable campaign
                print(f"[ESCALATION] Only found {len(selected_contractors)} contractors within 15 miles")
                print(f"[ESCALATION] Expanding outreach to ensure we reach 15 contractors total")
                
                # Expand the outreach strategy to reach 15 contractors
                escalated_strategy = self.calculator.calculate_outreach_strategy(
                    bids_needed=request.bids_needed,
                    timeline_hours=request.timeline_hours,
                    project_type=request.project_type,
                    location=request.location,
                    tier1_available=50,  # Assume more available for escalation
                    tier2_available=100,
                    tier3_available=200
                )
                
                # Re-select with expanded numbers but still 15-mile radius
                selected_contractors = []
                
                # Get more from each tier
                for tier_num, tier_strategy in [(1, escalated_strategy.tier1_strategy), 
                                              (2, escalated_strategy.tier2_strategy),
                                              (3, escalated_strategy.tier3_strategy)]:
                    if tier_strategy.to_contact > 0:
                        tier_contractors = await self._select_tier_contractors_with_radius(
                            tier=tier_num,
                            count=tier_strategy.to_contact,
                            project_type=request.project_type,
                            location=request.location,
                            contractor_size_preference=request.contractor_size_preference
                        )
                        selected_contractors.extend(tier_contractors)
                
                print(f"[ESCALATION] After escalation: {len(selected_contractors)} contractors selected")
                
                # If still not enough, trigger Google Maps discovery for Tier 3
                # Calculate how many Tier 3 contractors we need based on their response rate (33%)
                # For 4 bids with 33% response rate, we need about 12 contractors
                tier3_response_rate = 0.33
                tier3_needed_for_bids = math.ceil(request.bids_needed / tier3_response_rate)
                
                # We want at least tier3_needed_for_bids total contractors
                minimum_total_contractors = max(tier3_needed_for_bids, 12)  # At least 12 for 4 bids
                
                if len(selected_contractors) < minimum_total_contractors:
                    print(f"[ESCALATION] Still need more contractors - triggering Google Maps discovery")
                    print(f"[ESCALATION] Current: {len(selected_contractors)}, Target: {minimum_total_contractors} (for {request.bids_needed} bids at 33% response rate)")
                    
                    # Use the intelligent discovery system (initialized in __init__)
                    # Calculate how many more we need to discover
                    additional_needed = minimum_total_contractors - len(selected_contractors)
                    
                    # Discover additional contractors using intelligent discovery system
                    discovered_contractors = await self._discover_tier3_contractors_intelligent(
                        project_type=request.project_type,
                        location=request.location,
                        needed_count=additional_needed,
                        contractor_size_preference=request.contractor_size_preference
                    )
                    
                    if discovered_contractors:
                        print(f"[INTELLIGENT DISCOVERY] Found {len(discovered_contractors)} additional contractors")
                        selected_contractors.extend(discovered_contractors)
                    else:
                        print(f"[INTELLIGENT DISCOVERY] No additional contractors found")
            
            # Step 4: Create the campaign
            if selected_contractors:
                # Determine optimal channels
                optimal_channels = self._determine_optimal_channels(request.urgency_level, selected_contractors)
                
                # Create campaign using the orchestrator
                contractor_ids = [c.get('id') for c in selected_contractors if c.get('id')]
                
                campaign_result = self.orchestrator.create_campaign(
                    name=f"Campaign-{request.bid_card_id}",
                    bid_card_id=request.bid_card_id,
                    contractor_ids=contractor_ids,
                    channels=optimal_channels,
                    schedule=None
                )
                
                # Schedule check-ins
                if campaign_result.get("success") and campaign_result.get("campaign_id"):
                    await self.check_in_manager.schedule_campaign_check_ins(
                        campaign_id=campaign_result["campaign_id"],
                        bid_card_id=request.bid_card_id,
                        strategy=strategy
                    )
                
                return {
                    "success": True,
                    "campaign_id": campaign_result.get("campaign_id"),
                    "contractors_selected": len(selected_contractors),
                    "strategy": {
                        "total_contractors": len(selected_contractors),
                        "expected_responses": sum([
                            len([c for c in selected_contractors if c.get("tier") == 1]) * 0.9,
                            len([c for c in selected_contractors if c.get("tier") == 2]) * 0.5,
                            len([c for c in selected_contractors if c.get("tier") == 3]) * 0.33
                        ]),
                        "radius_constraint": "15 miles",
                        "escalated": len(selected_contractors) >= 15
                    },
                    "contractors": selected_contractors
                }
            else:
                return {
                    "success": False,
                    "error": "No contractors found within 15-mile radius matching criteria",
                    "suggestion": "Consider expanding service radius or adjusting project requirements"
                }
                
        except Exception as e:
            print(f"[Enhanced Orchestrator ERROR] Failed to create campaign: {e}")
            return {
                "success": False,
                "error": str(e),
                "contractors_selected": 0
            }

    def _determine_optimal_channels(self, urgency: str, contractors: list[dict[str, Any]]) -> list[str]:
        """Determine optimal outreach channels based on urgency"""
        if urgency in ["emergency", "urgent"]:
            return ["email", "website_form", "sms"]
        else:
            return ["email", "website_form"]