"""
National Geocoding Service
Provides geocoding for any US ZIP code using uszipcode library
"""
import logging
from typing import Optional, Tuple, Dict, Any
from uszipcode import SearchEngine

logger = logging.getLogger(__name__)


class GeocodingService:
    """Service for converting ZIP codes to lat/lng coordinates nationwide"""
    
    def __init__(self):
        # Initialize with comprehensive database
        self.search_engine = SearchEngine()
        logger.info("[Geocoding] Initialized national geocoding service")
    
    def get_coordinates(self, zip_code: str) -> Optional[Tuple[float, float]]:
        """
        Get latitude/longitude for any US ZIP code
        
        Args:
            zip_code: 5-digit US ZIP code
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        try:
            # Clean the ZIP code
            zip_clean = str(zip_code).strip()[:5]
            
            # Look up the ZIP code
            result = self.search_engine.by_zipcode(zip_clean)
            
            if result and result.lat and result.lng:
                return (float(result.lat), float(result.lng))
            
            # Try ZCTA lookup as fallback
            if not result:
                result = self.search_engine.by_zipcode(zip_clean, zipcode_type="zcta5")
                if result and result.lat and result.lng:
                    return (float(result.lat), float(result.lng))
            
            logger.warning(f"[Geocoding] No coordinates found for ZIP: {zip_code}")
            return None
            
        except Exception as e:
            logger.error(f"[Geocoding] Error getting coordinates for {zip_code}: {e}")
            return None
    
    def get_location_details(self, zip_code: str) -> Optional[Dict[str, Any]]:
        """
        Get complete location details for a ZIP code
        
        Returns:
            Dict with city, state, lat, lng, timezone, etc.
        """
        try:
            zip_clean = str(zip_code).strip()[:5]
            result = self.search_engine.by_zipcode(zip_clean)
            
            if result:
                return {
                    "zip": result.zipcode,
                    "city": result.major_city or result.post_office_city,
                    "state": result.state,
                    "lat": result.lat,
                    "lng": result.lng,
                    "timezone": result.timezone,
                    "county": result.county,
                    "population": result.population,
                    "radius_in_miles": result.radius_in_miles
                }
            
            return None
            
        except Exception as e:
            logger.error(f"[Geocoding] Error getting details for {zip_code}: {e}")
            return None
    
    def get_nearby_zips(self, zip_code: str, radius_miles: int = 15) -> list[str]:
        """
        Get all ZIP codes within radius of a center ZIP
        
        Args:
            zip_code: Center ZIP code
            radius_miles: Search radius in miles
            
        Returns:
            List of ZIP codes within radius
        """
        try:
            # Get center coordinates
            result = self.search_engine.by_zipcode(zip_code)
            if not result or not result.lat or not result.lng:
                logger.warning(f"[Geocoding] Invalid center ZIP: {zip_code}")
                return [zip_code]
            
            # Search for nearby ZIPs
            nearby = self.search_engine.by_coordinates(
                lat=result.lat,
                lng=result.lng,
                radius=radius_miles,
                returns=0  # Return all matches
            )
            
            # Extract ZIP codes
            zip_codes = [z.zipcode for z in nearby if z.zipcode]
            
            logger.info(f"[Geocoding] Found {len(zip_codes)} ZIPs within {radius_miles} miles of {zip_code}")
            return zip_codes
            
        except Exception as e:
            logger.error(f"[Geocoding] Error finding nearby ZIPs: {e}")
            return [zip_code]
    
    def calculate_search_area(self, location: Dict[str, Any], radius_miles: float) -> Dict[str, Any]:
        """
        Calculate search area for Google Places API
        
        Args:
            location: Dict with zip, city, state
            radius_miles: Search radius
            
        Returns:
            Dict with circle or rectangle for Google Places locationRestriction
        """
        try:
            # Try to get coordinates from ZIP
            zip_code = location.get("zip") or location.get("zip_code", "")
            
            if zip_code:
                coords = self.get_coordinates(zip_code)
                if coords:
                    return {
                        "circle": {
                            "center": {
                                "latitude": coords[0],
                                "longitude": coords[1]
                            },
                            "radius": radius_miles * 1609.34  # Convert to meters
                        }
                    }
            
            # Fallback: Try city/state geocoding
            city = location.get("city", "")
            state = location.get("state", "")
            
            if city and state:
                # Search by city
                city_results = self.search_engine.by_city_and_state(city, state)
                if city_results:
                    first_result = city_results[0]
                    return {
                        "circle": {
                            "center": {
                                "latitude": first_result.lat,
                                "longitude": first_result.lng
                            },
                            "radius": radius_miles * 1609.34
                        }
                    }
            
            # Last resort: Use state center
            if state:
                state_centers = {
                    "FL": (27.9, -81.7),
                    "CA": (36.7, -119.4),
                    "TX": (31.0, -99.0),
                    "NY": (42.9, -75.5),
                    # Add more states as needed
                }
                
                if state in state_centers:
                    lat, lng = state_centers[state]
                    return {
                        "circle": {
                            "center": {
                                "latitude": lat,
                                "longitude": lng
                            },
                            "radius": radius_miles * 1609.34 * 2  # Double radius for state-level
                        }
                    }
            
            # Ultimate fallback: US center
            logger.warning(f"[Geocoding] Using US center as fallback for {location}")
            return {
                "circle": {
                    "center": {
                        "latitude": 39.0,
                        "longitude": -95.0
                    },
                    "radius": radius_miles * 1609.34 * 5  # 5x radius for national
                }
            }
            
        except Exception as e:
            logger.error(f"[Geocoding] Error calculating search area: {e}")
            # Return a default area
            return {
                "circle": {
                    "center": {
                        "latitude": 39.0,
                        "longitude": -95.0
                    },
                    "radius": 50000  # 50km default
                }
            }