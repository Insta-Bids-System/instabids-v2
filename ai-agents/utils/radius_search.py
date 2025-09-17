"""
Radius-based search utilities for zip code distance calculations.
Supports contractor job matching and bid card filtering by distance.
"""

import logging
from functools import lru_cache
from typing import Optional

from haversine import Unit, haversine
from uszipcode import SearchEngine


logger = logging.getLogger(__name__)

# Initialize search engine once (loads SQLite database)
_search_engine = None

def get_search_engine():
    """Get or create the uszipcode search engine (lazy loading)."""
    global _search_engine
    if _search_engine is None:
        logger.info("Initializing uszipcode search engine...")
        _search_engine = SearchEngine(simple_zipcode=True)
        logger.info("uszipcode search engine initialized")
    return _search_engine

@lru_cache(maxsize=1024)
def get_zip_coordinates(zip_code: str) -> Optional[tuple[float, float]]:
    """
    Get latitude/longitude coordinates for a zip code.
    
    Args:
        zip_code: 5-digit zip code string
        
    Returns:
        (latitude, longitude) tuple or None if zip not found
    """
    try:
        engine = get_search_engine()
        zipcode_info = engine.by_zipcode(zip_code)

        if zipcode_info and zipcode_info.lat and zipcode_info.lng:
            return (float(zipcode_info.lat), float(zipcode_info.lng))

        logger.warning(f"No coordinates found for zip code: {zip_code}")
        return None

    except Exception as e:
        logger.error(f"Error getting coordinates for zip {zip_code}: {e}")
        return None

@lru_cache(maxsize=512)
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
        engine = get_search_engine()
        center_zipcode = engine.by_zipcode(center_zip)

        if not center_zipcode or not center_zipcode.lat or not center_zipcode.lng:
            logger.warning(f"Invalid center zip code: {center_zip}")
            return [center_zip]  # Return at least the center zip

        # Get all zip codes within radius using uszipcode's built-in method
        nearby_zipcodes = engine.by_coordinate(
            lat=center_zipcode.lat,
            lng=center_zipcode.lng,
            radius=radius_miles,
            returns=0  # Return all matches
        )

        # Extract zip codes from results
        zip_codes = [z.zipcode for z in nearby_zipcodes if z.zipcode]

        logger.info(f"Found {len(zip_codes)} zip codes within {radius_miles} miles of {center_zip}")
        return zip_codes

    except Exception as e:
        logger.error(f"Error finding zip codes near {center_zip}: {e}")
        return [center_zip]  # Return at least the center zip on error

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

        distance = haversine(coords1, coords2, unit=Unit.MILES)
        return round(distance, 2)

    except Exception as e:
        logger.error(f"Error calculating distance between {zip1} and {zip2}: {e}")
        return None

def filter_by_radius(items: list[dict], center_zip: str, radius_miles: int, zip_field: str = "location_zip") -> list[dict]:
    """
    Filter a list of items by radius from a center zip code.
    
    Args:
        items: List of items with zip code field
        center_zip: Center zip code for radius calculation
        radius_miles: Maximum distance in miles
        zip_field: Field name containing zip code in each item
        
    Returns:
        Filtered list of items within radius
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

            item_coords = get_zip_coordinates(str(item_zip))
            if not item_coords:
                continue

            distance = haversine(center_coords, item_coords, unit=Unit.MILES)

            if distance <= radius_miles:
                # Add distance info to item for sorting/display
                item_copy = item.copy()
                item_copy["distance_miles"] = round(distance, 2)
                filtered_items.append(item_copy)

        # Sort by distance (closest first)
        filtered_items.sort(key=lambda x: x.get("distance_miles", 999))

        logger.info(f"Filtered {len(items)} items to {len(filtered_items)} within {radius_miles} miles of {center_zip}")
        return filtered_items

    except Exception as e:
        logger.error(f"Error filtering items by radius: {e}")
        return items  # Return original list on error

# Preload common zip codes on module import to warm cache
def warm_cache():
    """Warm the cache with common zip codes."""
    try:
        # Major city zip codes for cache warming
        major_zips = ["10001", "90210", "60601", "77001", "33101", "94102", "02101", "85001"]
        for zip_code in major_zips:
            get_zip_coordinates(zip_code)
        logger.info("Cache warmed with major city zip codes")
    except Exception as e:
        logger.error(f"Error warming cache: {e}")

# Warm cache on import
warm_cache()
