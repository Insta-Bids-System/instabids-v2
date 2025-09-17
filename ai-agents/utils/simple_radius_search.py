"""
Simple radius-based search using basic math and a US zip codes database.
Alternative to uszipcode due to SQLAlchemy compatibility issues.
"""

import logging
import math
from functools import lru_cache
from typing import Optional


logger = logging.getLogger(__name__)

# Simple zip code data (can be expanded)
ZIP_COORDINATES = {
    # California
    "90210": (34.0901, -118.4065),  # Beverly Hills
    "90001": (33.9731, -118.2479),  # Los Angeles
    "90402": (34.0194, -118.4912),  # Santa Monica
    "90211": (34.0840, -118.4007),  # Beverly Hills
    "94102": (37.7849, -122.4094),  # San Francisco
    "94105": (37.7893, -122.3932),  # San Francisco SOMA
    "94107": (37.7630, -122.3916),  # San Francisco Mission Bay
    "95014": (37.3229, -122.0353),  # Cupertino

    # New York
    "10001": (40.7505, -73.9934),   # Manhattan
    "10002": (40.7156, -73.9877),   # Lower East Side
    "10003": (40.7316, -73.9885),   # East Village
    "11201": (40.6940, -73.9902),   # Brooklyn Heights

    # Illinois
    "60601": (41.8827, -87.6233),   # Chicago Loop
    "60602": (41.8796, -87.6368),   # Chicago West Loop

    # Texas
    "77001": (29.7604, -95.3698),   # Houston
    "78701": (30.2672, -97.7431),   # Austin

    # Florida
    "33101": (25.7617, -80.1918),   # Miami
    "33139": (25.7907, -80.1300),   # Miami Beach
}

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth in miles.
    
    Args:
        lat1, lon1: Latitude and longitude of first point
        lat2, lon2: Latitude and longitude of second point
        
    Returns:
        Distance in miles
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    # Radius of earth in miles
    r = 3956

    return c * r

@lru_cache(maxsize=512)
def get_zip_coordinates(zip_code: str) -> Optional[tuple[float, float]]:
    """
    Get latitude/longitude coordinates for a zip code.
    
    Args:
        zip_code: 5-digit zip code string
        
    Returns:
        (latitude, longitude) tuple or None if zip not found
    """
    # Check our local database first
    if zip_code in ZIP_COORDINATES:
        return ZIP_COORDINATES[zip_code]

    logger.warning(f"Zip code {zip_code} not found in local database")
    return None

def calculate_distance_miles(zip1: str, zip2: str) -> Optional[float]:
    """
    Calculate distance in miles between two zip codes.
    
    Args:
        zip1: First zip code
        zip2: Second zip code
        
    Returns:
        Distance in miles or None if calculation fails
    """
    try:
        coords1 = get_zip_coordinates(zip1)
        coords2 = get_zip_coordinates(zip2)

        if not coords1 or not coords2:
            return None

        lat1, lon1 = coords1
        lat2, lon2 = coords2

        distance = haversine_distance(lat1, lon1, lat2, lon2)
        return round(distance, 2)

    except Exception as e:
        logger.error(f"Error calculating distance between {zip1} and {zip2}: {e}")
        return None

def get_zip_codes_in_radius(center_zip: str, radius_miles: int) -> list[str]:
    """
    Get all zip codes within a given radius of a center zip code.
    
    Args:
        center_zip: Center zip code (5 digits)
        radius_miles: Radius in miles (1-200)
        
    Returns:
        List of zip codes within the radius
    """
    try:
        center_coords = get_zip_coordinates(center_zip)
        if not center_coords:
            logger.warning(f"Center zip code {center_zip} not found")
            return [center_zip]  # Return at least the center zip

        center_lat, center_lon = center_coords
        zip_codes_in_radius = []

        # Check all known zip codes
        for zip_code, (lat, lon) in ZIP_COORDINATES.items():
            distance = haversine_distance(center_lat, center_lon, lat, lon)
            if distance <= radius_miles:
                zip_codes_in_radius.append(zip_code)

        logger.info(f"Found {len(zip_codes_in_radius)} zip codes within {radius_miles} miles of {center_zip}")
        return zip_codes_in_radius

    except Exception as e:
        logger.error(f"Error finding zip codes near {center_zip}: {e}")
        return [center_zip]  # Return at least the center zip on error

def filter_by_radius(items: list[dict], center_zip: str, radius_miles: int, zip_field: str = "location_zip") -> list[dict]:
    """
    Filter a list of items by radius from a center zip code.
    
    Args:
        items: List of items with zip code field
        center_zip: Center zip code for radius calculation
        radius_miles: Maximum distance in miles
        zip_field: Field name containing zip code in each item
        
    Returns:
        Filtered list of items within radius, sorted by distance
    """
    if not items or not center_zip:
        return items

    try:
        center_coords = get_zip_coordinates(center_zip)
        if not center_coords:
            logger.warning(f"Could not get coordinates for center zip: {center_zip}")
            return items

        filtered_items = []

        for item in items:
            item_zip = item.get(zip_field)
            if not item_zip:
                continue

            distance = calculate_distance_miles(center_zip, str(item_zip))
            if distance is not None and distance <= radius_miles:
                # Add distance info to item for sorting/display
                item_copy = item.copy()
                item_copy["distance_miles"] = distance
                filtered_items.append(item_copy)

        # Sort by distance (closest first)
        filtered_items.sort(key=lambda x: x.get("distance_miles", 999))

        logger.info(f"Filtered {len(items)} items to {len(filtered_items)} within {radius_miles} miles of {center_zip}")
        return filtered_items

    except Exception as e:
        logger.error(f"Error filtering items by radius: {e}")
        return items  # Return original list on error

def add_zip_code(zip_code: str, latitude: float, longitude: float):
    """
    Add a new zip code to the local database.
    
    Args:
        zip_code: 5-digit zip code
        latitude: Latitude coordinate
        longitude: Longitude coordinate
    """
    ZIP_COORDINATES[zip_code] = (latitude, longitude)
    logger.info(f"Added zip code {zip_code} at ({latitude}, {longitude})")

def get_supported_zip_codes() -> list[str]:
    """Get list of all supported zip codes."""
    return list(ZIP_COORDINATES.keys())

# Pre-populate cache on import
def warm_cache():
    """Warm the cache with all known zip codes."""
    try:
        for zip_code in ZIP_COORDINATES:
            get_zip_coordinates(zip_code)
        logger.info(f"Cache warmed with {len(ZIP_COORDINATES)} zip codes")
    except Exception as e:
        logger.error(f"Error warming cache: {e}")

# Warm cache on import
warm_cache()
