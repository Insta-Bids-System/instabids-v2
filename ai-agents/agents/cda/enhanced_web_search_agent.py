"""
Enhanced Web Search Contractor Discovery Agent
Combines Google Places discovery with 66-field profile building
"""
import json
import os
from dataclasses import dataclass
from typing import Any, Optional, Dict, List
import logging
import asyncio

# CRITICAL: Load environment variables BEFORE any imports that need them
from dotenv import load_dotenv
load_dotenv(override=True)

from supabase import Client
from agents.cda.complete_profile_builder import CompleteProfileBuilder
from agents.cda.tavily_search import TavilySearchTool
from agents.cda.contractor_website_analyzer import ContractorWebsiteAnalyzer

logger = logging.getLogger(__name__)


class EnhancedWebSearchAgent:
    """Enhanced web search with 66-field profile building"""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.profile_builder = CompleteProfileBuilder()
        self.tavily_search = TavilySearchTool()
        self.website_analyzer = ContractorWebsiteAnalyzer()
        
        # Environment variables already loaded at module level
        self.google_api_key = os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")
        logger.info(f"[EnhancedWebSearch] Initialized with 66-field profile builder")

    async def get_bid_card_contractor_types(self, bid_card_id: str) -> Dict[str, Any]:
        """
        Retrieve bid card data including contractor_type_ids
        
        Args:
            bid_card_id: The bid card ID
            
        Returns:
            Dict with bid card data and contractor type information
        """
        try:
            # Get bid card data
            result = self.supabase.table("potential_bid_cards").select("*").eq("id", bid_card_id).execute()
            
            if result.data and len(result.data) > 0:
                bid_card = result.data[0]
                contractor_type_ids = bid_card.get("contractor_type_ids", [])
                
                # Get contractor type names
                contractor_types = []
                if contractor_type_ids:
                    type_result = self.supabase.table("contractor_types").select("id, name").in_("id", contractor_type_ids).execute()
                    if type_result.data:
                        contractor_types = type_result.data
                
                logger.info(f"[Classification] Bid card {bid_card_id} needs contractor types: {[t['name'] for t in contractor_types]}")
                
                return {
                    "success": True,
                    "bid_card": bid_card,
                    "contractor_type_ids": contractor_type_ids,
                    "contractor_types": contractor_types
                }
            else:
                logger.warning(f"[Classification] No bid card found with ID: {bid_card_id}")
                return {
                    "success": False,
                    "error": "Bid card not found",
                    "contractor_type_ids": [],
                    "contractor_types": []
                }
                
        except Exception as e:
            logger.error(f"[Classification] Error fetching bid card data: {e}")
            return {
                "success": False,
                "error": str(e),
                "contractor_type_ids": [],
                "contractor_types": []
            }
    
    async def discover_contractors_with_profiles(self, 
                                                bid_card_id: str,
                                                project_type: str,
                                                location: Dict[str, str],
                                                contractors_needed: int = 10,
                                                radius_miles: int = 15) -> Dict[str, Any]:
        """
        Discover contractors and build complete 66-field profiles
        NOW WITH CLASSIFICATION-DRIVEN DISCOVERY
        
        Args:
            bid_card_id: ID of the bid card
            project_type: Type of project (fallback if no classification)
            location: Location dict with city, state, zip
            contractors_needed: Number of contractors to find
            radius_miles: Search radius
        
        Returns:
            Dict with discovered contractors with 66-field profiles
        """
        logger.info(f"[EnhancedWebSearch] Starting classification-driven discovery for bid card {bid_card_id}")
        
        try:
            # NEW: Get contractor types from bid card classification
            bid_card_data = await self.get_bid_card_contractor_types(bid_card_id)
            contractor_types = bid_card_data.get("contractor_types", [])
            
            # Handle categorization failure gracefully
            if not bid_card_data.get("success"):
                logger.warning(f"[Classification] Failed to get contractor types: {bid_card_data.get('error')}")
                # Continue with project_type fallback
            
            # Build search terms from contractor types - prioritize specific types over categories
            search_terms = []
            if contractor_types:
                # Sort to prioritize more specific contractor types (like "Plumber") over categories (like "Plumbing")
                # Specific types usually have "Contractor", "er" endings, or are longer/more specific
                priority_terms = []
                category_terms = []
                
                for contractor_type in contractor_types:
                    name = contractor_type.get("name", "")
                    # Prioritize terms that are actual contractor types
                    if any(ending in name.lower() for ending in ["contractor", "er", "ist", "ian", "man"]):
                        priority_terms.append(name)
                    else:
                        category_terms.append(name)
                
                # Use priority terms first, then categories if needed
                search_terms = priority_terms + category_terms
                
                # If we have too many terms, prioritize the most specific ones
                if len(search_terms) > 3:
                    search_terms = search_terms[:3]  # Focus on top 3 most relevant
                    
                logger.info(f"[Classification] Using classified search terms: {search_terms} (prioritized from {len(contractor_types)} types)")
            else:
                # Fallback to project_type if no classification
                search_terms = [project_type]
                logger.warning(f"[Classification] No contractor types found, using fallback: {project_type}")
            
            # Step 1: Classification-Driven Google Places Discovery
            from agents.cda.google_places_optimized import GooglePlacesOptimized
            google_tool = GooglePlacesOptimized()
            
            all_discovered_contractors = []
            api_calls_summary = {"total": 0, "by_type": {}}
            
            # Search for each contractor type specifically
            for search_term in search_terms:
                logger.info(f"[Classification] Searching for: {search_term} contractors in {location.get('city', '')}")
                
                google_discovery = await google_tool.discover_contractors(
                    service_type=search_term,  # Use specific contractor type
                    location=location,
                    target_count=max(5, contractors_needed // len(search_terms) * 2),  # Distribute target count
                    radius_miles=radius_miles,
                    cost_mode="CHEAPEST",
                    include_sabs=True,
                    min_rating=3.0
                )
                
                if google_discovery.get("success"):
                    contractors = google_discovery.get("contractors", [])
                    # Tag contractors with their search classification
                    for contractor in contractors:
                        contractor["search_classification"] = search_term
                        contractor["classification_source"] = "targeted_search"
                    
                    all_discovered_contractors.extend(contractors)
                    api_calls_summary["by_type"][search_term] = len(contractors)
                    api_calls_summary["total"] += google_discovery.get("api_calls", {}).get("total", 0)
                    
                    logger.info(f"[Classification] Found {len(contractors)} {search_term} contractors")
            
            if not all_discovered_contractors:
                return {
                    "success": False,
                    "error": "No contractors found for any contractor type",
                    "contractors": [],
                    "classification_used": True,
                    "search_terms": search_terms
                }
            
            # Remove duplicates based on google_place_id
            unique_contractors = {}
            for contractor in all_discovered_contractors:
                place_id = contractor.get("google_place_id", contractor.get("name", ""))
                if place_id not in unique_contractors:
                    unique_contractors[place_id] = contractor
            
            all_discovered_contractors = list(unique_contractors.values())
            logger.info(f"[Classification] Total unique contractors found: {len(all_discovered_contractors)}")
            
            # Step 2: Build 66-field profiles with rate limiting
            profiles = []
            needed_contractor_types = bid_card_data.get("contractor_type_ids", [])
            
            for i, google_contractor in enumerate(all_discovered_contractors):
                try:
                    logger.info(f"[Profile Builder] Processing contractor {i+1}/{len(all_discovered_contractors)}")
                    
                    # Enrich with Tavily if website available
                    web_data = None
                    website = google_contractor.get("website", "")
                    if website:
                        logger.info(f"[Tavily] Enriching {google_contractor.get('name', 'Unknown')}")
                        tavily_result = await self.tavily_search.discover_contractor_pages(
                            company_name=google_contractor.get("name", ""),
                            website_url=website,
                            location=f"{location.get('city', '')}, {location.get('state', '')}"
                        )
                        
                        # Add delay after Tavily API call
                        logger.info("[Rate Limiting] Waiting 2 seconds after Tavily call...")
                        await asyncio.sleep(2)
                        
                        if tavily_result and tavily_result.get("discovered_pages"):
                            web_data = self._process_tavily_content(tavily_result)
                    
                    # Build complete profile
                    # First use basic profile builder for field mapping
                    basic_profile = await self.profile_builder.build_contractor_profile(
                        company_name=google_contractor.get("name", ""),
                        google_data=google_contractor,
                        web_data=web_data,
                        license_data=None  # TODO: Add license verification
                    )
                    
                    # Then use GPT-4o extractor for intelligent extraction including contractor_type_ids
                    try:
                        from agents.coia.tools.ai_extraction.gpt4o_contractor_extractor import GPT4oContractorExtractor
                        extractor = GPT4oContractorExtractor()
                        
                        # Extract comprehensive profile with contractor_type_ids
                        gpt4o_profile = await extractor.extract_contractor_profile(
                            company_name=google_contractor.get("name", ""),
                            google_data=google_contractor,
                            web_data=web_data,
                            license_data=None
                        )
                        
                        # Merge GPT-4o extracted data with basic profile
                        if "error" not in gpt4o_profile:
                            # Keep basic profile as base and overlay GPT-4o extractions
                            profile = {**basic_profile, **gpt4o_profile}
                            logger.info(f"[GPT-4o] Extracted contractor_type_ids: {gpt4o_profile.get('contractor_type_ids', [])}")
                        else:
                            logger.warning(f"[GPT-4o] Extraction failed, using basic profile: {gpt4o_profile.get('error')}")
                            profile = basic_profile
                            
                    except Exception as e:
                        logger.error(f"[GPT-4o] Failed to use GPT-4o extractor: {e}")
                        profile = basic_profile
                    
                    # Add delay after profile building (which calls OpenAI)
                    logger.info("[Rate Limiting] Waiting 1 second after profile building...")
                    await asyncio.sleep(1)
                    
                    # NEW: Verify classification match
                    contractor_type_ids = profile.get("contractor_type_ids", [])
                    match_score = self.calculate_classification_match(needed_contractor_types, contractor_type_ids)
                    
                    # Add discovery metadata
                    profile["discovery_source"] = "enhanced_web_search"
                    profile["bid_card_id"] = bid_card_id
                    profile["discovery_tier"] = 3
                    profile["search_classification"] = google_contractor.get("search_classification", "unknown")
                    profile["classification_match_score"] = match_score
                    profile["classification_match"] = "good" if match_score >= 0.7 else "partial" if match_score >= 0.4 else "poor"
                    
                    logger.info(f"[Classification] {profile.get('company_name')}: Match score {match_score:.2f} ({profile['classification_match']})")
                    
                    profiles.append(profile)
                    
                    # Save to database
                    await self._save_to_database(profile)
                    
                    if len(profiles) >= contractors_needed:
                        break
                        
                except Exception as e:
                    logger.error(f"Error building profile: {e}")
                    continue
            
            # Calculate classification effectiveness
            good_matches = len([p for p in profiles if p.get("classification_match") == "good"])
            partial_matches = len([p for p in profiles if p.get("classification_match") == "partial"])
            poor_matches = len([p for p in profiles if p.get("classification_match") == "poor"])
            
            return {
                "success": True,
                "contractors": profiles,
                "total_discovered": len(profiles),
                "google_api_calls": api_calls_summary,
                "profiles_built": len(profiles),
                "classification_used": True,
                "search_terms_used": search_terms,
                "contractor_types_needed": [{"id": t["id"], "name": t["name"]} for t in contractor_types],
                "classification_effectiveness": {
                    "good_matches": good_matches,
                    "partial_matches": partial_matches,
                    "poor_matches": poor_matches,
                    "effectiveness_rate": (good_matches / len(profiles) * 100) if profiles else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Enhanced discovery error: {e}")
            return {
                "success": False,
                "error": str(e),
                "contractors": []
            }
    
    def _process_tavily_content(self, tavily_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Tavily data for profile builder"""
        pages = tavily_data.get("discovered_pages", [])
        
        # Extract key information
        services_mentioned = []
        company_description = ""
        
        for page in pages[:3]:  # Process top 3 pages
            content = page.get("content", "")
            if "services" in page.get("url", "").lower():
                # Extract services from services page
                services_mentioned.extend(self._extract_services(content))
            if "about" in page.get("url", "").lower():
                company_description = content[:500]
        
        return {
            "services_mentioned": list(set(services_mentioned)),
            "company_description": company_description,
            "website_pages": [p.get("url", "") for p in pages],
            "has_website": True
        }
    
    def calculate_classification_match(self, needed_types: List[int], contractor_types: List[int]) -> float:
        """
        Calculate how well a contractor's types match the needed types
        
        Args:
            needed_types: List of contractor_type_ids needed for the project
            contractor_types: List of contractor_type_ids the contractor has
            
        Returns:
            Match score between 0.0 and 1.0
        """
        if not needed_types:
            return 1.0  # If no specific types needed, all contractors match
        
        if not contractor_types:
            return 0.0  # If contractor has no types, no match
        
        # Calculate intersection
        matching_types = set(needed_types).intersection(set(contractor_types))
        
        # Score based on percentage of needed types found
        match_score = len(matching_types) / len(needed_types)
        
        return match_score
    
    def _extract_services(self, content: str) -> List[str]:
        """Extract services from website content"""
        # Simple keyword extraction
        service_keywords = [
            "plumbing", "electrical", "hvac", "roofing", "painting",
            "landscaping", "remodeling", "installation", "repair",
            "maintenance", "emergency", "residential", "commercial"
        ]
        
        found_services = []
        content_lower = content.lower()
        for keyword in service_keywords:
            if keyword in content_lower:
                found_services.append(keyword)
        
        return found_services
    
    async def _save_to_database(self, profile: Dict[str, Any]):
        """Save contractor profile to potential_contractors table"""
        try:
            # Prepare database record - INCLUDING bid_card_id!
            record = {
                "company_name": profile.get("company_name", ""),
                "phone": profile.get("phone", ""),
                "email": profile.get("email", ""),
                "website": profile.get("website", ""),
                "address": profile.get("address", ""),
                "city": profile.get("city", ""),
                "state": profile.get("state", ""),
                "zip_code": profile.get("zip_code", ""),
                "google_place_id": profile.get("google_place_id", ""),
                "google_rating": profile.get("google_rating", 0),
                "google_review_count": profile.get("google_review_count", 0),
                "specialties": profile.get("specialties", []),
                "contractor_size_category": profile.get("contractor_size_category", "small"),
                "ai_business_summary": profile.get("ai_business_summary", ""),
                "ai_capability_description": profile.get("ai_capability_description", ""),
                "lead_status": "new",
                "discovery_source": "enhanced_web_search",
                "bid_card_id": profile.get("bid_card_id")  # CRITICAL: Include bid_card_id
            }
            
            # Remove None values
            record = {k: v for k, v in record.items() if v is not None}
            
            # Insert to database
            result = self.supabase.table("potential_contractors").insert(record).execute()
            
            if result.data:
                logger.info(f"[Database] Saved contractor: {profile.get('company_name', 'Unknown')}")
                return True
                
        except Exception as e:
            logger.error(f"Database save error: {e}")
            
        return False