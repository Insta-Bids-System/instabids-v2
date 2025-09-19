"""
Traced CDA Agent - Contractor Discovery Agent with Langfuse Tracing
"""
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Optional, Dict, List

from dotenv import load_dotenv
from supabase import create_client

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from agents.cda.service_specific_matcher import ServiceSpecificMatcher
from agents.cda.tier1_matcher_v2 import Tier1Matcher
from agents.cda.tier2_reengagement import Tier2Reengagement
from agents.cda.web_search_agent import WebSearchContractorAgent
from agents.cda.enhanced_web_search_agent import EnhancedWebSearchAgent
from agents.cda.adaptive_discovery import AdaptiveDiscoverySystem
from agents.cda.geocoding_service import GeocodingService
from agents.cda.complete_profile_builder import CompleteProfileBuilder
from agents.cda.tavily_search import TavilySearchTool

# Import tracing utilities
from utils.langfuse_config import (
    tracing, track_contractor_discovery, log_geocoding_result,
    log_contractor_search, log_profile_enrichment, trace_cda_operation
)


class TracedContractorDiscoveryAgent:
    """CDA with comprehensive Langfuse tracing for visual monitoring"""

    def __init__(self):
        """Initialize CDA with tracing capabilities"""
        load_dotenv(override=True)
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase = create_client(self.supabase_url, self.supabase_key)

        # Initialize components
        try:
            self.service_matcher = ServiceSpecificMatcher()
            print("[Traced CDA] Initialized with GPT-4 service-specific matching")
        except Exception as e:
            print(f"[Traced CDA] Service matcher unavailable: {e}")
            self.service_matcher = None

        self.web_search = WebSearchContractorAgent(self.supabase)
        self.enhanced_web_search = EnhancedWebSearchAgent(self.supabase)
        self.tier1_matcher = Tier1Matcher(self.supabase)
        self.tier2_reengagement = Tier2Reengagement(self.supabase)
        self.adaptive_discovery = AdaptiveDiscoverySystem()
        self.geocoding_service = GeocodingService()
        self.profile_builder = CompleteProfileBuilder()
        self.tavily_search = TavilySearchTool()

        print("[Traced CDA] Initialized with comprehensive tracing and adaptive discovery")

    @trace_cda_operation("Contractor Discovery")
    async def discover_contractors(self, bid_card_id: str, contractors_needed: int = 4,
                                  radius_miles: int = 15, project_type: str = None,
                                  location: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Discover contractors with full tracing and monitoring
        """
        # Create main trace for the entire discovery workflow
        trace = track_contractor_discovery(
            bid_card_id=bid_card_id,
            project_type=project_type or "unknown",
            location=location or {}
        )

        try:
            print(f"[Traced CDA] Starting intelligent contractor discovery for bid card: {bid_card_id} (radius: {radius_miles} miles)")
            
            # Step 1: Get bid card data (with tracing)
            bid_card_data = await self._get_bid_card_data_traced(trace, bid_card_id)
            if not bid_card_data:
                error_msg = "Bid card not found"
                tracing.log_event(trace, "Discovery Failed", 
                                input_data={"bid_card_id": bid_card_id},
                                output_data={"error": error_msg},
                                level="ERROR")
                return {"success": False, "error": error_msg, "contractors": []}

            # Step 2: Adaptive discovery with radius expansion
            discovery_result = await self._adaptive_discovery_traced(
                trace, bid_card_data, contractors_needed, radius_miles
            )

            # Step 3: Profile enrichment
            enriched_contractors = await self._enrich_contractor_profiles_traced(
                trace, discovery_result.get("contractors", [])
            )

            # Step 4: Final results
            final_result = {
                "success": True,
                "contractors": enriched_contractors,
                "total_found": len(enriched_contractors),
                "search_radius_used": discovery_result.get("final_radius", radius_miles),
                "discovery_stages": discovery_result.get("stages_used", []),
                "trace_id": getattr(trace, 'id', None) if trace else None
            }

            # Log final result
            tracing.log_event(trace, "Discovery Complete",
                            input_data={
                                "bid_card_id": bid_card_id,
                                "target_contractors": contractors_needed,
                                "initial_radius": radius_miles
                            },
                            output_data={
                                "contractors_found": len(enriched_contractors),
                                "final_radius": discovery_result.get("final_radius"),
                                "success": True
                            })

            return final_result

        except Exception as e:
            error_msg = str(e)
            tracing.log_event(trace, "Discovery Error",
                            input_data={"bid_card_id": bid_card_id},
                            output_data={"error": error_msg},
                            level="ERROR")
            return {"success": False, "error": error_msg, "contractors": []}

    async def _get_bid_card_data_traced(self, trace, bid_card_id: str) -> Optional[Dict]:
        """Get bid card data with tracing"""
        span = tracing.create_span(trace, "Get Bid Card Data",
                                 input_data={"bid_card_id": bid_card_id})
        
        start_time = time.time()
        try:
            response = self.supabase.table("bid_cards").select("*").eq("id", bid_card_id).execute()
            duration = time.time() - start_time
            
            if response.data:
                bid_card = response.data[0]
                tracing.end_span(span, {
                    "bid_card_found": True,
                    "project_type": bid_card.get("project_type"),
                    "duration_seconds": duration
                }, "DEFAULT", "Bid card found")
                return bid_card
            else:
                tracing.end_span(span, {
                    "bid_card_found": False,
                    "duration_seconds": duration
                }, "ERROR", "Bid card not found")
                return None
                
        except Exception as e:
            duration = time.time() - start_time
            tracing.end_span(span, {
                "error": str(e),
                "duration_seconds": duration
            }, "ERROR", f"Database error: {str(e)}")
            raise

    async def _adaptive_discovery_traced(self, trace, bid_card_data: Dict, 
                                       contractors_needed: int, initial_radius: int) -> Dict:
        """Perform adaptive discovery with radius expansion and tracing"""
        span = tracing.create_span(trace, "Adaptive Discovery",
                                 input_data={
                                     "contractors_needed": contractors_needed,
                                     "initial_radius": initial_radius
                                 })
        
        try:
            # Extract location from bid card
            location = {
                "city": bid_card_data.get("location_city", "Unknown"),
                "state": bid_card_data.get("location_state", "Unknown"),
                "zip": bid_card_data.get("location_zip", ""),
            }

            # Stage 1: Geocoding
            geocoding_start = time.time()
            zip_code = location.get("zip") or "33301"  # Default ZIP
            coordinates = self.geocoding_service.get_coordinates(zip_code)
            geocoding_duration = time.time() - geocoding_start
            
            log_geocoding_result(trace, zip_code, coordinates, geocoding_duration)

            # Stage 2: Internal database search (Tier 1)
            tier1_start = time.time()
            tier1_results = await self._search_tier1_traced(trace, location, initial_radius)
            tier1_duration = time.time() - tier1_start
            
            log_contractor_search(trace, location, len(tier1_results), "Tier 1 - Internal DB", tier1_duration)

            contractors = tier1_results
            current_radius = initial_radius
            stages_used = ["Tier 1 - Internal DB"]

            # Stage 3: Radius expansion if needed
            if len(contractors) < contractors_needed:
                expansion_results = await self._radius_expansion_traced(
                    trace, location, contractors_needed - len(contractors), current_radius
                )
                contractors.extend(expansion_results.get("contractors", []))
                current_radius = expansion_results.get("final_radius", current_radius)
                stages_used.extend(expansion_results.get("stages", []))

            result = {
                "contractors": contractors,
                "final_radius": current_radius,
                "stages_used": stages_used
            }

            tracing.end_span(span, {
                "contractors_found": len(contractors),
                "final_radius": current_radius,
                "stages_used": stages_used
            }, "DEFAULT", f"Found {len(contractors)} contractors")

            return result

        except Exception as e:
            tracing.end_span(span, {"error": str(e)}, "ERROR", f"Discovery failed: {str(e)}")
            raise

    async def _search_tier1_traced(self, trace, location: Dict, radius: int) -> List[Dict]:
        """Search internal database with tracing"""
        span = tracing.create_span(trace, "Tier 1 Search",
                                 input_data={"location": location, "radius": radius})
        
        start_time = time.time()
        try:
            # Search internal contractors table
            city = location.get("city", "")
            state = location.get("state", "")
            
            response = self.supabase.table("contractor_leads").select(
                "id, company_name, email, phone, specialties, city, state, zip_code"
            ).eq("state", state).eq("city", city).limit(15).execute()
            
            duration = time.time() - start_time
            contractors = response.data or []
            
            tracing.end_span(span, {
                "contractors_found": len(contractors),
                "search_location": f"{city}, {state}",
                "duration_seconds": duration
            }, "DEFAULT", f"Found {len(contractors)} internal contractors")
            
            return contractors
            
        except Exception as e:
            duration = time.time() - start_time
            tracing.end_span(span, {
                "error": str(e),
                "duration_seconds": duration
            }, "ERROR", f"Tier 1 search failed: {str(e)}")
            return []

    async def _radius_expansion_traced(self, trace, location: Dict, 
                                     contractors_still_needed: int, current_radius: int) -> Dict:
        """Perform radius expansion with tracing"""
        span = tracing.create_span(trace, "Radius Expansion",
                                 input_data={
                                     "location": location,
                                     "contractors_needed": contractors_still_needed,
                                     "current_radius": current_radius
                                 })
        
        try:
            contractors = []
            stages_used = []
            final_radius = current_radius

            # Try expanding to 25, 40, 60, 100 miles
            for target_radius in [25, 40, 60, 100]:
                if len(contractors) >= contractors_still_needed:
                    break
                
                if target_radius <= current_radius:
                    continue
                
                # Enhanced web search at this radius
                search_start = time.time()
                search_results = await self._enhanced_web_search_traced(
                    trace, location, target_radius, contractors_still_needed - len(contractors)
                )
                search_duration = time.time() - search_start
                
                log_contractor_search(trace, 
                    {**location, "radius": target_radius}, 
                    len(search_results), 
                    f"Web Search - {target_radius}mi", 
                    search_duration
                )
                
                contractors.extend(search_results)
                stages_used.append(f"Web Search - {target_radius}mi")
                final_radius = target_radius
                
                if len(contractors) >= contractors_still_needed:
                    break

            result = {
                "contractors": contractors,
                "final_radius": final_radius,
                "stages": stages_used
            }

            tracing.end_span(span, {
                "contractors_found": len(contractors),
                "final_radius": final_radius,
                "stages_used": stages_used
            }, "DEFAULT", f"Expansion found {len(contractors)} additional contractors")

            return result

        except Exception as e:
            tracing.end_span(span, {"error": str(e)}, "ERROR", f"Radius expansion failed: {str(e)}")
            return {"contractors": [], "final_radius": current_radius, "stages": []}

    async def _enhanced_web_search_traced(self, trace, location: Dict, 
                                        radius: int, limit: int) -> List[Dict]:
        """Enhanced web search with tracing"""
        span = tracing.create_span(trace, f"Enhanced Web Search - {radius}mi",
                                 input_data={"location": location, "radius": radius, "limit": limit})
        
        start_time = time.time()
        try:
            # Use enhanced web search agent
            contractors = await self.enhanced_web_search.search_contractors(
                location=location,
                radius_miles=radius,
                limit=limit
            )
            
            duration = time.time() - start_time
            
            tracing.end_span(span, {
                "contractors_found": len(contractors),
                "search_radius": radius,
                "duration_seconds": duration
            }, "DEFAULT", f"Web search found {len(contractors)} contractors")
            
            return contractors
            
        except Exception as e:
            duration = time.time() - start_time
            tracing.end_span(span, {
                "error": str(e),
                "duration_seconds": duration
            }, "ERROR", f"Web search failed: {str(e)}")
            return []

    async def _enrich_contractor_profiles_traced(self, trace, contractors: List[Dict]) -> List[Dict]:
        """Enrich contractor profiles with tracing"""
        span = tracing.create_span(trace, "Profile Enrichment",
                                 input_data={"contractor_count": len(contractors)})
        
        start_time = time.time()
        enriched_contractors = []
        
        try:
            for contractor in contractors:
                try:
                    # Use profile builder for enrichment
                    profile_start = time.time()
                    enriched_profile = await self.profile_builder.build_contractor_profile(
                        company_name=contractor.get("company_name", ""),
                        google_data=contractor,
                        web_data=None
                    )
                    profile_duration = time.time() - profile_start
                    
                    if enriched_profile:
                        # Count populated fields
                        populated_fields = sum(1 for v in enriched_profile.values() 
                                             if v and v != "" and v != "Not set")
                        
                        log_profile_enrichment(trace, 
                            contractor.get("id", "unknown"),
                            "Profile Builder",
                            populated_fields,
                            profile_duration
                        )
                        
                        enriched_contractors.append(enriched_profile)
                    else:
                        enriched_contractors.append(contractor)  # Use original if enrichment fails
                        
                except Exception as e:
                    # If enrichment fails, use original contractor data
                    enriched_contractors.append(contractor)
                    tracing.log_event(trace, "Profile Enrichment Failed",
                                    input_data={"contractor": contractor.get("company_name", "unknown")},
                                    output_data={"error": str(e)},
                                    level="WARNING")
            
            duration = time.time() - start_time
            
            tracing.end_span(span, {
                "contractors_processed": len(contractors),
                "contractors_enriched": len(enriched_contractors),
                "duration_seconds": duration
            }, "DEFAULT", f"Enriched {len(enriched_contractors)} contractor profiles")
            
            return enriched_contractors
            
        except Exception as e:
            duration = time.time() - start_time
            tracing.end_span(span, {
                "error": str(e),
                "duration_seconds": duration
            }, "ERROR", f"Profile enrichment failed: {str(e)}")
            return contractors  # Return original data on failure

    @trace_cda_operation("Health Check")
    def health_check(self) -> Dict[str, Any]:
        """Health check with tracing"""
        return {
            "status": "healthy",
            "components": {
                "service_matcher": self.service_matcher is not None,
                "geocoding": True,
                "profile_builder": True,
                "tavily_search": self.tavily_search.use_tavily,
                "database": True
            },
            "tracing_enabled": tracing.enabled,
            "timestamp": datetime.now().isoformat()
        }

    def get_trace_url(self, trace_id: str) -> Optional[str]:
        """Get Langfuse trace URL for visual inspection"""
        if tracing.enabled and trace_id:
            host = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
            return f"{host}/trace/{trace_id}"
        return None