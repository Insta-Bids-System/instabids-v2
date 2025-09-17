"""
Google Places API (NEW v1) - Optimized Implementation
Based on user's research for efficient contractor discovery
"""

import logging
import os
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GooglePlacesOptimized:
    """
    Optimized Google Places API implementation
    Uses pageSize: 20 instead of maxResultCount: 1 for massive efficiency
    """
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not self.api_key:
            logger.warning("GOOGLE_PLACES_API_KEY not found in environment")
        
        # NEW Google Places API v1 endpoint
        self.base_url = "https://places.googleapis.com/v1/places:searchText"
        
        # Field masks for different cost modes (corrected field names)
        self.field_masks = {
            "CHEAPEST": "places.id,places.displayName,places.primaryType,places.formattedAddress,places.rating,places.userRatingCount,places.nationalPhoneNumber,places.websiteUri,places.googleMapsUri,places.businessStatus,places.types",
            
            "ONE_PASS_RICH": "places.id,places.displayName,places.primaryType,places.formattedAddress,places.rating,places.userRatingCount,places.nationalPhoneNumber,places.websiteUri,places.googleMapsUri,places.businessStatus,places.types,places.regularOpeningHours,places.currentOpeningHours,places.priceLevel"
        }
    
    async def discover_contractors(self,
                                  service_type: str,
                                  location: Dict[str, Any],
                                  target_count: int = 20,
                                  radius_miles: float = 10,
                                  cost_mode: str = "CHEAPEST",
                                  include_sabs: bool = True,
                                  min_rating: Optional[float] = None) -> Dict[str, Any]:
        """
        Discover contractors using optimized Google Places API
        
        Args:
            service_type: Type of service (plumbing, electrical, etc.)
            location: Dict with city, state, zip
            target_count: Number of contractors to find (up to 60)
            radius_miles: Search radius in miles
            cost_mode: "CHEAPEST" or "ONE_PASS_RICH"
            include_sabs: Include Service Area Businesses
            min_rating: Minimum rating filter
        
        Returns:
            Dict with contractors and API call stats
        """
        
        if not self.api_key:
            return {"success": False, "error": "No API key configured"}
        
        # Build search query
        query = f"{service_type} contractors near {location.get('zip', '')} {location.get('city', '')} {location.get('state', '')}"
        
        # Convert miles to meters for API
        radius_meters = radius_miles * 1609.34
        
        # LocationBias for soft preference (locationRestriction has different format)
        lat, lng = self._get_lat_lng_for_zip(location.get('zip', '33442'))
        location_bias = {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lng
                },
                "radius": radius_meters
            }
        }
        
        # Build request body
        # Map service types to Google Place types
        type_mapping = {
            "plumbing": "plumber",
            "electrical": "electrician",
            "roofing": "roofing_contractor",
            "hvac": "hvac",
            "general": "general_contractor"
        }
        included_type = type_mapping.get(service_type.lower(), "plumber")
        
        body = {
            "textQuery": query,
            "includedType": included_type,  # Use valid Google place type
            "strictTypeFiltering": False,  # Allow related types
            "includePureServiceAreaBusinesses": include_sabs,
            "pageSize": 20,  # CRITICAL: Get 20 at once, not 1!
            "locationBias": location_bias,  # Use locationBias instead of restriction
            "rankPreference": "RELEVANCE"
        }
        
        if min_rating:
            body["minRating"] = min_rating
        
        # Headers with field mask
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": self.field_masks[cost_mode]
        }
        
        contractors = []
        api_calls = 0
        next_page_token = None
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get up to 3 pages (60 results max)
                for page_num in range(3):
                    if len(contractors) >= target_count:
                        break
                    
                    # Add page token for pagination
                    if next_page_token:
                        body["pageToken"] = next_page_token
                    
                    # Make API call
                    async with session.post(self.base_url, json=body, headers=headers) as response:
                        api_calls += 1
                        
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"Google API error: {error_text}")
                            return {"success": False, "error": f"API error: {response.status}"}
                        
                        data = await response.json()
                        
                        # Process places
                        places = data.get("places", [])
                        for place in places:
                            contractor = self._parse_place_to_contractor(place)
                            contractors.append(contractor)
                            
                            if len(contractors) >= target_count:
                                break
                        
                        # Check for next page
                        next_page_token = data.get("nextPageToken")
                        if not next_page_token:
                            break
                        
                        # Small delay between pages
                        await asyncio.sleep(0.5)
                
                logger.info(f"[GOOGLE OPTIMIZED] Found {len(contractors)} contractors in {api_calls} API calls")
                
                return {
                    "success": True,
                    "contractors": contractors,
                    "api_calls": {
                        "searches": api_calls,
                        "details": 0  # No separate detail calls needed!
                    }
                }
                
        except Exception as e:
            logger.error(f"Google Places discovery error: {e}")
            return {"success": False, "error": str(e)}
    
    def _parse_place_to_contractor(self, place: Dict) -> Dict[str, Any]:
        """Parse Google Place data to contractor format"""
        
        # Extract display name
        display_name = place.get("displayName", {})
        name = display_name.get("text", "Unknown") if isinstance(display_name, dict) else "Unknown"
        
        # Extract address
        formatted_address = place.get("formattedAddress", "")
        address_parts = formatted_address.split(",") if formatted_address else []
        
        return {
            "name": name,
            "google_place_id": place.get("id", ""),
            "address": address_parts[0].strip() if address_parts else "",
            "city": address_parts[1].strip() if len(address_parts) > 1 else "",
            "state": address_parts[2].strip()[:2] if len(address_parts) > 2 else "",
            "rating": place.get("rating", 0),
            "reviews": place.get("userRatingCount", 0),
            "phone": place.get("nationalPhoneNumber", ""),
            "website": place.get("websiteUri", ""),
            "google_maps_url": place.get("googleMapsUri", ""),
            "business_status": place.get("businessStatus", ""),
            "types": place.get("types", []),
            "is_service_area_business": place.get("pureServiceAreaBusiness", False),
            "price_level": place.get("priceLevel", ""),
            "photos": [p.get("name", "") for p in place.get("photos", [])[:3]],
            "discovered_at": datetime.now().isoformat()
        }
    
    def _get_lat_lng_for_zip(self, zip_code: str) -> tuple:
        """Get approximate lat/lng for ZIP code"""
        # For testing, using Boca Raton 33442 coordinates
        # In production, would use geocoding API
        zip_coords = {
            "33442": (26.3683, -80.1289),  # Boca Raton, FL
            "33432": (26.3587, -80.0831),  # Boca Raton, FL
            "33434": (26.3881, -80.1281),  # Boca Raton, FL
        }
        return zip_coords.get(zip_code, (26.3683, -80.1289))