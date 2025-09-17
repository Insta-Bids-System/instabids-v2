"""
Optimized Google Places API Tool for Contractor Discovery
Based on Google Places API (NEW, v1) with proper cost optimization
"""

import logging
import os
import httpx
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class GooglePlacesOptimized:
    """
    Optimized Google Places API client following CHEAPEST cost model
    Gets 20-60 contractors per search instead of 1
    """
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")
        self.base_url = "https://places.googleapis.com/v1"
        
        if self.api_key:
            logger.info(f"Google Places Optimized initialized with key: {self.api_key[:20]}...")
        else:
            logger.warning("Google Places API key not found")
    
    async def discover_contractors(self,
                                 service_type: str,
                                 location: Dict[str, Any],
                                 target_count: int = 10,
                                 radius_miles: float = 15,
                                 cost_mode: str = "CHEAPEST",
                                 include_sabs: bool = True,
                                 min_rating: float = 3.5) -> Dict[str, Any]:
        """
        Main discovery method following the master prompt strategy
        
        Args:
            service_type: e.g., "plumbing", "electrical", "hvac"
            location: Dict with zip, city, state, and optionally lat/lng
            target_count: Number of contractors needed
            radius_miles: Search radius in miles
            cost_mode: "CHEAPEST" or "ONE_PASS_RICH"
            include_sabs: Include service area businesses (mobile contractors)
            min_rating: Minimum rating threshold
        
        Returns:
            Dict with discovered contractors and metadata
        """
        logger.info(f"[OPTIMIZED DISCOVERY] Starting for {service_type} in {location.get('zip', 'unknown')}")
        
        # Map service to Google Places type
        service_to_type = {
            "plumbing": "plumber",
            "electrical": "electrician",
            "hvac": "hvac_contractor",
            "roofing": "roofing_contractor",
            "painting": "painter",
            "landscaping": "landscaper",
            "general": "general_contractor",
            "handyman": "handyman"
        }
        
        places_type = service_to_type.get(service_type.lower(), "contractor")
        
        # Calculate search area
        search_area = await self._calculate_search_area(location, radius_miles)
        
        if cost_mode == "CHEAPEST":
            return await self._discover_cheapest(
                service_type, places_type, location, search_area,
                target_count, include_sabs, min_rating
            )
        else:
            return await self._discover_rich(
                service_type, places_type, location, search_area,
                target_count, include_sabs, min_rating
            )
    
    async def _discover_cheapest(self, service_type: str, places_type: str,
                                location: Dict[str, Any], search_area: Dict[str, Any],
                                target_count: int, include_sabs: bool,
                                min_rating: float) -> Dict[str, Any]:
        """
        CHEAPEST mode: Get IDs first, then enrich only what we need
        """
        logger.info("[CHEAPEST MODE] Discovery pass for IDs only")
        
        # Step 1: Discovery pass (IDs only)
        all_place_ids = []
        next_page_token = None
        max_pages = 3  # Up to 60 results
        
        for page in range(max_pages):
            # Text Search for IDs only
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": "places.id,places.displayName,places.rating,places.userRatingCount,nextPageToken"
            }
            
            if page == 0:
                # First search
                query = f"{service_type} {location.get('city', '')} {location.get('state', '')}"
                body = {
                    "textQuery": query,
                    "includedType": places_type,
                    "strictTypeFiltering": True,
                    "includePureServiceAreaBusinesses": include_sabs,
                    "pageSize": 20
                }
                
                # Add location restriction if we have a rectangle
                if search_area.get("rectangle"):
                    body["locationRestriction"] = {"rectangle": search_area["rectangle"]}
                elif search_area.get("circle"):
                    body["locationBias"] = {"circle": search_area["circle"]}
            else:
                # Pagination
                if not next_page_token:
                    break
                body = {
                    "pageToken": next_page_token
                }
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/places:searchText",
                        json=body,
                        headers=headers,
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        places = data.get("places", [])
                        
                        # Quick filter by rating if available
                        for place in places:
                            if place.get("rating", 0) >= min_rating or not place.get("rating"):
                                all_place_ids.append({
                                    "id": place.get("id"),
                                    "name": place.get("displayName", {}).get("text", ""),
                                    "rating": place.get("rating"),
                                    "reviews": place.get("userRatingCount", 0)
                                })
                        
                        logger.info(f"[PAGE {page+1}] Found {len(places)} places, {len(all_place_ids)} total after filtering")
                        
                        next_page_token = data.get("nextPageToken")
                        if not next_page_token:
                            break
                    else:
                        logger.error(f"Search failed: {response.status_code} - {response.text}")
                        break
                        
            except Exception as e:
                logger.error(f"Error in discovery pass: {e}")
                break
            
            # Rate limiting
            if page < max_pages - 1:
                await asyncio.sleep(1)
        
        logger.info(f"[DISCOVERY COMPLETE] Found {len(all_place_ids)} candidates")
        
        # Step 2: Sort by rating/reviews and take top candidates
        all_place_ids.sort(key=lambda x: (x.get("rating", 0) * x.get("reviews", 0)), reverse=True)
        shortlist = all_place_ids[:min(len(all_place_ids), target_count * 2)]
        
        # Step 3: Enrich shortlist with details
        logger.info(f"[ENRICHMENT] Getting details for top {len(shortlist)} contractors")
        enriched_contractors = []
        
        for place_info in shortlist[:target_count * 2]:  # Get details for 2x target
            details = await self._get_place_details(place_info["id"])
            if details:
                enriched_contractors.append(details)
            
            # Stop if we have enough
            if len(enriched_contractors) >= target_count:
                break
            
            # Rate limiting
            await asyncio.sleep(0.5)
        
        return {
            "success": True,
            "contractors": enriched_contractors[:target_count],
            "total_discovered": len(all_place_ids),
            "search_pages": page + 1,
            "cost_mode": "CHEAPEST",
            "api_calls": {
                "searches": page + 1,
                "details": len(enriched_contractors)
            }
        }
    
    async def _discover_rich(self, service_type: str, places_type: str,
                            location: Dict[str, Any], search_area: Dict[str, Any],
                            target_count: int, include_sabs: bool,
                            min_rating: float) -> Dict[str, Any]:
        """
        ONE_PASS_RICH mode: Get all fields in one search
        """
        logger.info("[RICH MODE] Single pass with all fields")
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": (
                "places.id,places.displayName,places.formattedAddress,"
                "places.primaryType,places.types,places.businessStatus,"
                "places.pureServiceAreaBusiness,places.websiteUri,"
                "places.internationalPhoneNumber,places.nationalPhoneNumber,"
                "places.rating,places.userRatingCount,places.googleMapsUri,"
                "places.photos,nextPageToken"
            )
        }
        
        query = f"{service_type} {location.get('city', '')} {location.get('state', '')}"
        body = {
            "textQuery": query,
            "includedType": places_type,
            "strictTypeFiltering": True,
            "includePureServiceAreaBusinesses": include_sabs,
            "pageSize": 20
        }
        
        # Add location restriction
        if search_area.get("rectangle"):
            body["locationRestriction"] = {"rectangle": search_area["rectangle"]}
        elif search_area.get("circle"):
            body["locationBias"] = {"circle": search_area["circle"]}
        
        all_contractors = []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/places:searchText",
                    json=body,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    places = data.get("places", [])
                    
                    for place in places:
                        if place.get("rating", 0) >= min_rating or not place.get("rating"):
                            contractor = self._format_contractor(place)
                            all_contractors.append(contractor)
                    
                    logger.info(f"[RICH MODE] Found {len(all_contractors)} contractors in one call")
                else:
                    logger.error(f"Search failed: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error in rich mode: {e}")
        
        return {
            "success": True,
            "contractors": all_contractors[:target_count],
            "total_discovered": len(all_contractors),
            "cost_mode": "ONE_PASS_RICH",
            "api_calls": {"searches": 1, "details": 0}
        }
    
    async def _get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific place"""
        headers = {
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": (
                "displayName,formattedAddress,primaryType,types,"
                "businessStatus,pureServiceAreaBusiness,websiteUri,"
                "internationalPhoneNumber,nationalPhoneNumber,"
                "rating,userRatingCount,googleMapsUri,photos"
            )
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/places/{place_id}",
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    place = response.json()
                    return self._format_contractor(place)
                else:
                    logger.error(f"Details failed for {place_id}: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting details for {place_id}: {e}")
            return None
    
    async def _calculate_search_area(self, location: Dict[str, Any], 
                                    radius_miles: float) -> Dict[str, Any]:
        """Calculate search area rectangle or circle from location"""
        # Convert miles to meters
        radius_meters = radius_miles * 1609.34
        
        # If we have lat/lng, use it
        if location.get("lat") and location.get("lng"):
            return {
                "circle": {
                    "center": {
                        "latitude": location["lat"],
                        "longitude": location["lng"]
                    },
                    "radius": radius_meters
                }
            }
        
        # Otherwise, create a rough rectangle from ZIP
        # This is simplified - in production you'd use a geocoding service
        # For now, create a square around estimated center
        zip_code = location.get("zip", "")
        
        # Example for Florida ZIPs (simplified)
        if zip_code.startswith("334"):  # Boca Raton area
            center_lat = 26.3683
            center_lng = -80.1289
        elif zip_code.startswith("328"):  # Orlando area
            center_lat = 28.5383
            center_lng = -81.3792
        else:
            # Default fallback
            center_lat = 27.6648
            center_lng = -81.5158
        
        # Create rectangle (rough approximation)
        lat_offset = radius_miles / 69  # ~69 miles per degree latitude
        lng_offset = radius_miles / (69 * 0.86)  # Adjust for latitude
        
        return {
            "rectangle": {
                "low": {
                    "latitude": center_lat - lat_offset,
                    "longitude": center_lng - lng_offset
                },
                "high": {
                    "latitude": center_lat + lat_offset,
                    "longitude": center_lng + lng_offset
                }
            },
            "circle": {
                "center": {"latitude": center_lat, "longitude": center_lng},
                "radius": radius_meters
            }
        }
    
    def _format_contractor(self, place: Dict[str, Any]) -> Dict[str, Any]:
        """Format Google Place into contractor record"""
        return {
            "place_id": place.get("id", ""),
            "name": place.get("displayName", {}).get("text", ""),
            "address": place.get("formattedAddress", ""),
            "primary_type": place.get("primaryType", ""),
            "types": place.get("types", []),
            "is_service_area_business": place.get("pureServiceAreaBusiness", False),
            "website": place.get("websiteUri", ""),
            "phone": place.get("nationalPhoneNumber", "") or place.get("internationalPhoneNumber", ""),
            "rating": place.get("rating", 0),
            "reviews": place.get("userRatingCount", 0),
            "google_maps_uri": place.get("googleMapsUri", ""),
            "business_status": place.get("businessStatus", ""),
            "photos": [p.get("name", "") for p in place.get("photos", [])[:1]],
            "discovery_timestamp": datetime.utcnow().isoformat()
        }


# Test function
async def test_optimized_discovery():
    """Test the optimized Google Places discovery"""
    client = GooglePlacesOptimized()
    
    result = await client.discover_contractors(
        service_type="plumbing",
        location={"city": "Boca Raton", "state": "FL", "zip": "33442"},
        target_count=10,
        radius_miles=15,
        cost_mode="CHEAPEST",
        include_sabs=True,
        min_rating=3.5
    )
    
    print("\n=== OPTIMIZED GOOGLE PLACES TEST ===")
    print(f"Success: {result.get('success')}")
    print(f"Contractors Found: {len(result.get('contractors', []))}")
    print(f"Total Discovered: {result.get('total_discovered')}")
    print(f"API Calls: {result.get('api_calls')}")
    
    if result.get('contractors'):
        print("\nTop 3 Contractors:")
        for i, contractor in enumerate(result['contractors'][:3], 1):
            print(f"\n{i}. {contractor['name']}")
            print(f"   Rating: {contractor['rating']} ({contractor['reviews']} reviews)")
            print(f"   Type: {contractor['primary_type']}")
            print(f"   Phone: {contractor['phone']}")
            print(f"   Website: {contractor['website']}")


if __name__ == "__main__":
    asyncio.run(test_optimized_discovery())