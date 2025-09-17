"""
Radius search implementation following your exact specification.
Uses uszipcode + haversine exactly as specified in the implementation doc.
"""

import logging
from functools import lru_cache
from typing import Optional

from haversine import haversine
from uszipcode import SearchEngine


logger = logging.getLogger(__name__)

# Global search engine (loads mini SQLite once)
_engine = SearchEngine(simple_zipcode=True)

@lru_cache(maxsize=8_192)
def get_zip_coordinates(zip_code: str) -> Optional[tuple[float, float]]:
    """Get latitude/longitude coordinates for a zip code."""
    try:
        z = _engine.by_zipcode(zip_code)
        if z and z.lat and z.lng:
            return (float(z.lat), float(z.lng))
        return None
    except Exception as e:
        logger.error(f"Error getting coordinates for zip {zip_code}: {e}")
        return None

@lru_cache(maxsize=8_192)
def get_zip_codes_in_radius(center_zip: str, radius_miles: int) -> list[str]:
    """Return ZIP codes within *radius_miles* of *center_zip*."""
    try:
        z = _engine.by_zipcode(center_zip)
        if not z or not z.lat or not z.lng:
            logger.warning(f"Invalid center zip code: {center_zip}")
            return [center_zip]

        # Get nearby zip codes using uszipcode's radius search
        nearby = _engine.by_coordinates(
            lat=z.lat,
            lng=z.lng,
            radius=radius_miles,
            returns=0  # Return all matches
        )

        # Extract zip codes from results
        zip_codes = [s.zipcode for s in nearby if s.zipcode]

        logger.info(f"Found {len(zip_codes)} zip codes within {radius_miles} miles of {center_zip}")
        return zip_codes

    except Exception as e:
        logger.error(f"Error finding zip codes near {center_zip}: {e}")
        return [center_zip]

def calculate_distance_miles(zip1: str, zip2: str) -> Optional[float]:
    """Calculate distance in miles between two zip codes."""
    try:
        coords1 = get_zip_coordinates(zip1)
        coords2 = get_zip_coordinates(zip2)

        if not coords1 or not coords2:
            return None

        distance = haversine(coords1, coords2)  # Returns miles by default
        return round(distance, 2)

    except Exception as e:
        logger.error(f"Error calculating distance between {zip1} and {zip2}: {e}")
        return None

def filter_by_radius(items: list[dict], center_zip: str, radius_miles: int, zip_field: str = "location_zip") -> list[dict]:
    """Filter a list of items by radius from a center zip code."""
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

            distance = haversine(center_coords, item_coords)

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
        return items

# Warm cache on import as specified
def warm_cache():
    """Warm the cache with common zip codes."""
    try:
        # Warm cache as specified in your implementation doc
        get_zip_codes_in_radius("10001", 50)
        logger.info("Cache warmed successfully")
    except Exception as e:
        logger.error(f"Error warming cache: {e}")

# Warm cache on import
warm_cache()
