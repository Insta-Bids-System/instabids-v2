"""
Google Places API Tool for COIA
Handles Google Places API searches for business information
"""

import logging
import os
import re
from html import unescape
from typing import Dict, Any, Optional, List
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

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
        query = company_name
        if location:
            query = f"{company_name} {location}"

        try:
            
            business_data = await self._search_business_web(query)

            if business_data:
                logger.info(f"Found business data via web search: {company_name}")
                return business_data

            logger.info(f"No web results found for {query}")
            return self._create_minimal_business_data(company_name, location, query)

        except Exception as e:
            logger.error(f"Error with fallback web search: {e}")
            return self._create_minimal_business_data(company_name, location, query)

    async def _search_business_web(self, query: str, max_results: int = 5) -> Optional[Dict[str, Any]]:
        """Use DuckDuckGo Lite as a lightweight web fallback when Google is unavailable."""
        logger.info(f"Attempting DuckDuckGo Lite fallback search for: {query}")

        encoded_query = quote_plus(query)
        url = f"https://lite.duckduckgo.com/lite/?q={encoded_query}"

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        }

        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            response = await client.get(url)

        if response.status_code != 200:
            logger.warning(
                "DuckDuckGo Lite request failed with status %s", response.status_code
            )
            return None

        html_content = response.text

        link_pattern = re.compile(
            r"<a[^>]*href=\"(?P<href>[^\"]+)\"[^>]*class='result-link'>(?P<title>.*?)</a>",
            re.IGNORECASE | re.DOTALL,
        )
        snippet_pattern = re.compile(
            r"<td class='result-snippet'>(?P<snippet>.*?)</td>", re.IGNORECASE | re.DOTALL
        )

        results: List[Dict[str, Any]] = []

        for match in link_pattern.finditer(html_content):
            raw_url = match.group("href")
            normalized_url = self._extract_duckduckgo_target(raw_url)

            # Skip sponsored entries or items without a resolvable target URL
            if not normalized_url or "duckduckgo.com" in normalized_url:
                continue

            snippet_match = snippet_pattern.search(html_content, match.end())
            snippet_text = (
                self._clean_html(snippet_match.group("snippet")) if snippet_match else ""
            )

            title = self._clean_html(match.group("title"))

            results.append(
                {
                    "title": title,
                    "url": normalized_url,
                    "snippet": snippet_text,
                }
            )

            if len(results) >= max_results:
                break

        if not results:
            return None

        top_result = results[0]
        return {
            "company_name": top_result["title"],
            "website": top_result["url"],
            "summary": top_result["snippet"],
            "search_results": results,
            "search_query": query,
            "data_source": "duckduckgo_web_fallback",
        }

    @staticmethod
    def _clean_html(value: str) -> str:
        """Remove HTML tags and decode entities from a snippet."""
        text = re.sub(r"<[^>]+>", " ", value)
        text = unescape(text)
        return " ".join(text.split())

    @staticmethod
    def _extract_duckduckgo_target(raw_url: str) -> str:
        """Extract the ultimate URL from a DuckDuckGo redirect link."""
        if raw_url.startswith("//"):
            raw_url = f"https:{raw_url}"

        try:
            parsed = urlparse(raw_url)
        except ValueError:
            return raw_url

        if "duckduckgo.com" not in parsed.netloc:
            return raw_url

        query_params = parse_qs(parsed.query)
        target = query_params.get("uddg")
        if not target:
            return raw_url

        return unquote(target[0])

    def _create_minimal_business_data(
        self, company_name: str, location: Optional[str], query: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create minimal business data when API fails"""
        return {
            "company_name": company_name,
            "location": location,
            "search_query": query,
            "data_source": "manual_entry",
            "verified": False
        }