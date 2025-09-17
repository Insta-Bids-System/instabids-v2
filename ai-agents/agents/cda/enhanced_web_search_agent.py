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
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        self.google_api_key = os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")
        logger.info(f"[EnhancedWebSearch] Initialized with 66-field profile builder")

    async def discover_contractors_with_profiles(self, 
                                                bid_card_id: str,
                                                project_type: str,
                                                location: Dict[str, str],
                                                contractors_needed: int = 10,
                                                radius_miles: int = 15) -> Dict[str, Any]:
        """
        Discover contractors and build complete 66-field profiles
        
        Args:
            bid_card_id: ID of the bid card
            project_type: Type of project
            location: Location dict with city, state, zip
            contractors_needed: Number of contractors to find
            radius_miles: Search radius
        
        Returns:
            Dict with discovered contractors with 66-field profiles
        """
        logger.info(f"[EnhancedWebSearch] Starting discovery for {project_type} in {location.get('city', '')}")
        
        try:
            # Step 1: Google Places Discovery
            from google_places_optimized import GooglePlacesOptimized
            google_tool = GooglePlacesOptimized()
            
            google_discovery = await google_tool.discover_contractors(
                service_type=project_type,
                location=location,
                target_count=contractors_needed * 2,  # Get extra for filtering
                radius_miles=radius_miles,
                cost_mode="CHEAPEST",
                include_sabs=True,
                min_rating=3.0
            )
            
            if not google_discovery.get("success"):
                return {
                    "success": False,
                    "error": "Google Places discovery failed",
                    "contractors": []
                }
            
            # Step 2: Build 66-field profiles
            profiles = []
            for google_contractor in google_discovery.get("contractors", []):
                try:
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
                        
                        if tavily_result and tavily_result.get("discovered_pages"):
                            web_data = self._process_tavily_content(tavily_result)
                    
                    # Build complete profile
                    profile = await self.profile_builder.build_contractor_profile(
                        company_name=google_contractor.get("name", ""),
                        google_data=google_contractor,
                        web_data=web_data,
                        license_data=None  # TODO: Add license verification
                    )
                    
                    # Add discovery metadata
                    profile["discovery_source"] = "enhanced_web_search"
                    profile["bid_card_id"] = bid_card_id
                    profile["discovery_tier"] = 3
                    
                    profiles.append(profile)
                    
                    # Save to database
                    await self._save_to_database(profile)
                    
                    if len(profiles) >= contractors_needed:
                        break
                        
                except Exception as e:
                    logger.error(f"Error building profile: {e}")
                    continue
            
            return {
                "success": True,
                "contractors": profiles,
                "total_discovered": len(profiles),
                "google_api_calls": google_discovery.get("api_calls", {}),
                "profiles_built": len(profiles)
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
            # Prepare database record
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
                "contractor_size": profile.get("contractor_size", ""),
                "lead_status": "new",
                "discovery_source": "enhanced_web_search"
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