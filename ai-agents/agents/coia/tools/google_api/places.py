"""
Google Places API Tool for COIA
Handles Google Places API searches for business information
"""

import logging
import os
from typing import Dict, Any, Optional
import httpx

from ..base import BaseTool

logger = logging.getLogger(__name__)


class GooglePlacesTool(BaseTool):
    """Google Places API integration for business search"""
    
    def __init__(self):
        super().__init__()
        self.google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if self.google_api_key:
            logger.info(f"Google Places API initialized with key: {self.google_api_key[:20]}...")
        else:
            logger.warning("Google Places API initialized without API key")
    
    async def search_google_business(self, company_name: str, location: Optional[str] = None) -> Dict[str, Any]:
        """
        Search Google Places API for business information with real API calls
        """
        logger.info(f"Searching Google Places API for business: {company_name} in {location}")
        
        # First try Google Places API if available
        if self.google_api_key:
            try:
                query = company_name
                if location:
                    query = f"{company_name} {location}"
                
                # Use Google Places API (New) Text Search
                url = "https://places.googleapis.com/v1/places:searchText"
                headers = {
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": self.google_api_key,
                    "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.websiteUri,places.nationalPhoneNumber,places.rating,places.userRatingCount,places.googleMapsUri,places.id,places.businessStatus,places.types"
                }
                
                data = {
                    "textQuery": query,
                    "maxResultCount": 1
                }
                
                logger.info(f"Making Google Places API call for: {query}")
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=data, headers=headers, timeout=30.0)
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result.get("places") and len(result["places"]) > 0:
                            place = result["places"][0]
                            
                            # Extract business data with proper Google API fields
                            business_data = {
                                "company_name": place.get("displayName", {}).get("text", company_name),
                                "address": place.get("formattedAddress", ""),
                                "website": place.get("websiteUri", ""),
                                "phone": place.get("nationalPhoneNumber", ""),
                                "google_rating": place.get("rating", 0),
                                "google_review_count": place.get("userRatingCount", 0),
                                "google_maps_url": place.get("googleMapsUri", ""),
                                "google_place_id": place.get("id", ""),
                                "google_business_status": place.get("businessStatus", ""),
                                "google_types": place.get("types", []),
                                "data_source": "google_places_api"
                            }
                            
                            logger.info(f"✅ Google API SUCCESS - Found {company_name}: rating={business_data.get('google_rating')}, reviews={business_data.get('google_review_count')}")
                            return business_data
                        else:
                            logger.info(f"No Google Places results found for {query}")
                    else:
                        logger.error(f"Google Places API error: {response.status_code} - {response.text}")
                        
            except Exception as e:
                logger.error(f"Error with Google Places API: {e}")
        
        # Fallback to web scraping if Google API fails or not available
        logger.info(f"Falling back to web search for: {company_name}")
        try:
            query = company_name
            if location:
                query = f"{company_name} {location}"
            
            business_data = await self._search_business_web(query)
            
            if business_data:
                logger.info(f"Found business data via web search: {company_name}")
                return business_data
            else:
                logger.info(f"No web results found for {query}")
                return self._create_minimal_business_data(company_name, location)
                
        except Exception as e:
            logger.error(f"Error with fallback web search: {e}")
            return self._create_minimal_business_data(company_name, location)
    
    async def _search_business_web(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Fallback web search method - placeholder for now
        TODO: Implement actual web search fallback
        """
        logger.info(f"Web search fallback not fully implemented for: {query}")
        return None
    
    def _create_minimal_business_data(self, company_name: str, location: Optional[str]) -> Dict[str, Any]:
        """Create minimal business data when API fails"""
        return {
            "company_name": company_name,
            "location": location,
            "data_source": "manual_entry",
            "verified": False
        }