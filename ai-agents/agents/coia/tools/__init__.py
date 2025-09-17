"""
COIA Tools - Refactored modular architecture
Main interface that delegates to specialized tool modules
"""

import logging
from typing import Dict, Any, Optional, List

from .google_api.places import GooglePlacesTool
from .web_research.tavily import TavilySearchTool
from .database.contractors import ContractorDatabaseTool
from .database.bid_cards import BidCardSearchTool
from .ai_extraction.profile_builder import ProfileBuilderTool
from .base import BaseTool

logger = logging.getLogger(__name__)


class COIATools(BaseTool):
    """
    Main COIA tools interface that delegates to specialized tools
    Maintains backward compatibility while using modular architecture
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize all specialized tools
        self.google_places = GooglePlacesTool()
        self.tavily_search = TavilySearchTool()
        self.contractor_db = ContractorDatabaseTool()
        self.bid_card_search = BidCardSearchTool()
        self.profile_builder = ProfileBuilderTool()
        
        logger.info("COIATools initialized with modular architecture")
    
    # Delegate to Google Places tool
    async def search_google_business(self, company_name: str, location: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Delegate to Google Places tool"""
        return await self.google_places.search_google_business(company_name, location)
    
    # Delegate to License Search tool
    async def search_contractor_licenses(self, company_name: str, state: str = "FL") -> Dict[str, Any]:
        """Delegate to License Search tool"""
        return await self.license_search.search_contractor_licenses(company_name, state)
    
    # Delegate to Tavily tool
    async def _tavily_discover_contractor_pages(self, company_name: str, website_url: str, location: Optional[str] = None) -> Dict[str, Any]:
        """Delegate to Tavily tool"""
        return await self.tavily_search.discover_contractor_pages(company_name, website_url, location)
    
    # Delegate to Database tool
    async def _check_existing_contractor(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Delegate to Database tool"""
        return await self.contractor_db.check_existing_contractor(company_name)
    
    # Keep complex methods that orchestrate multiple tools here temporarily
    # These will be refactored in phase 2
    async def research_business(self, company_name: str, location: str = "") -> Dict[str, Any]:
        """
        Comprehensive web research - orchestrates multiple tools
        TODO: This should be moved to a separate orchestration layer
        """
        logger.info(f"Starting comprehensive web research for {company_name}")
        
        comprehensive_data = {
            "company_name": company_name,
            "location": location,
            "google_data": {},
            "tavily_discovery_data": {},
            "website_data": {},
            "social_media_data": {},
            "business_intelligence": {},
            "data_sources": []
        }
        
        # 1. Google Business Search
        google_data = await self.search_google_business(company_name, location)
        if google_data:
            comprehensive_data["google_data"] = google_data
            comprehensive_data["data_sources"].append("google_business")
        
        # 2. Check for website in Google data
        website_url = google_data.get("website") if google_data else None
        
        if website_url:
            # 3. Use Tavily for comprehensive page discovery
            logger.info(f"🔍 Using Tavily API for comprehensive website content extraction: {website_url}")
            tavily_data = await self.tavily_search.discover_contractor_pages(company_name, website_url, location)
            comprehensive_data["tavily_discovery_data"] = tavily_data
            comprehensive_data["data_sources"].append("tavily_discovery")
        
        return comprehensive_data
    
    # Delegate to bid card search tool
    async def search_bid_cards(self, contractor_profile: Dict[str, Any], location: Optional[str] = None) -> List[Dict[str, Any]]:
        """Delegate to bid card search tool"""
        return await self.bid_card_search.search_bid_cards(contractor_profile, location)
    
    # Delegate to profile builder tool
    async def build_contractor_profile(self, company_name: str, 
                                      google_data: Optional[Dict] = None,
                                      web_data: Optional[Dict] = None,
                                      license_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Delegate to profile builder tool"""
        return await self.profile_builder.build_contractor_profile(company_name, google_data, web_data, license_data)
    
    # Delegate to contractor database tool
    async def create_contractor_account(self, contractor_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to contractor database tool"""
        return await self.contractor_db.create_contractor_account(contractor_profile)
    
    async def save_potential_contractor(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to contractor database tool"""
        return await self.contractor_db.save_potential_contractor(profile)
    
    # Web search company method - orchestrates research
    async def web_search_company(self, company_name: str, location: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Comprehensive web research for company information
        Returns structured data with completeness metrics
        """
        # Use research_business for now which orchestrates the tools
        result = await self.research_business(company_name, location or "")
        
        # Add completeness calculation
        total_fields = 66
        filled_fields = 0
        
        if result.get("google_data"):
            filled_fields += 6  # Basic Google data fields
        if result.get("tavily_discovery_data"):
            filled_fields += 10  # Web research fields
            
        completeness = int((filled_fields / total_fields) * 100)
        
        result["completeness"] = completeness
        result["field_completion_stats"] = {
            "filled": filled_fields,
            "total": total_fields,
            "percentage": completeness
        }
        
        return result


# Export the main class
__all__ = ['COIATools']