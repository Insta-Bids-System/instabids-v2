"""
Tavily API Tool for COIA
EXTRACTED FROM LEGACY tools.py - REAL IMPLEMENTATION
"""

import logging
import os
import asyncio
from typing import Dict, Any, Optional

from ..base import BaseTool

# Import LangFuse for observability (safe import)
try:
    from langfuse import get_client
    langfuse = get_client()
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False

logger = logging.getLogger(__name__)


class TavilySearchTool(BaseTool):
    """Tavily API web research tool - REAL IMPLEMENTATION"""
    
    def __init__(self):
        super().__init__()
        # Initialize Tavily API from environment
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.use_tavily = bool(self.tavily_api_key)
        
        if self.use_tavily:
            logger.info("TavilySearchTool initialized with API key")
        else:
            logger.warning("TavilySearchTool initialized without API key - disabled")

    async def discover_contractor_pages(self, company_name: str, website_url: str, location: Optional[str] = None) -> Dict[str, Any]:
        """
        🧠 PURE TAVILY INTELLIGENCE: Discover contractor pages using real Tavily API
        EXTRACTED FROM LEGACY tools.py
        """
        logger.info(f"Using REAL Tavily API to discover pages for {company_name}")
        
        # Wrap entire Tavily discovery with LangFuse span
        if LANGFUSE_AVAILABLE:
            try:
                with langfuse.start_as_current_observation(
                    name="coia-tavily-discovery",
                    as_type="span",
                    input={
                        "company_name": company_name,
                        "website_url": website_url,
                        "location": location,
                        "tool": "TavilySearchTool"
                    }
                ) as span:
                    result = await self._discover_contractor_pages_impl(company_name, website_url, location)
                    span.update(output={
                        "discovered_pages_count": len(result.get("discovered_pages", [])),
                        "api_used": result.get("api_used"),
                        "has_error": "error" in result
                    })
                    return result
            except Exception as e:
                logger.warning(f"LangFuse Tavily span failed: {e}")
                return await self._discover_contractor_pages_impl(company_name, website_url, location)
        else:
            return await self._discover_contractor_pages_impl(company_name, website_url, location)
    
    async def _discover_contractor_pages_impl(self, company_name: str, website_url: str, location: Optional[str] = None) -> Dict[str, Any]:
        """Implementation of Tavily discovery - extracted for LangFuse wrapping"""
        try:
            # Import Tavily Python SDK
            try:
                from tavily import TavilyClient
            except ImportError:
                logger.warning("Tavily SDK not installed - THIS IS NOT A WORKING INTEGRATION")
                return {"error": "Tavily SDK not installed", "discovered_pages": []}
            
            # Initialize REAL Tavily client via env (no hard-coded keys)
            if not self.use_tavily or not self.tavily_api_key:
                logger.warning("Tavily disabled or TAVILY_API_KEY missing; skipping discovery")
                return {"error": "Tavily disabled or no API key", "discovered_pages": []}
            client = TavilyClient(api_key=self.tavily_api_key)
            
            discovery_data = {
                "main_website": website_url,
                "discovered_pages": [],
                "content_sources": [],
                "extraction_priority": [],
                "api_used": "REAL_TAVILY_API"  # Proof this is real
            }
            
            # OPTIMIZED: Two targeted searches - one for contact info, one for services
            search_queries = [
                f"{company_name} contact email phone address",  # PRIORITIZE: Contact information extraction
                f"{company_name} services specialties certifications",  # Service information
            ]
            
            discovered_urls = set()
            
            for query in search_queries:
                logger.info(f"Making REAL Tavily API call: {query}")
                
                try:
                    # Search for pages AND get their content - FIXED for specific website
                    website_domain = website_url.replace("http://", "").replace("https://", "").split("/")[0] if website_url else None
                    response = client.search(
                        query=query,
                        search_depth="advanced",
                        max_results=8,  # Reduced from 10 to 8 to avoid rate limits
                        include_domains=[website_domain] if website_domain else None,
                        include_raw_content=True  # GET THE ACTUAL CONTENT
                    )
                    
                    if response and 'results' in response:
                        for result in response['results']:
                            url = result.get('url', '')
                            score = result.get('score', 0)
                            if url and url not in discovered_urls and score > 0.4:  # Lower threshold for better coverage
                                discovered_urls.add(url)
                                page_type = self._categorize_page_type(url, result.get('title', ''))
                                priority = self._calculate_page_priority(url, result.get('title', ''), page_type)
                                
                                discovery_data["discovered_pages"].append({
                                    "url": url,
                                    "title": result.get('title', ''),
                                    "score": score,
                                    "content": result.get('content', '')[:1500],  # Increased for better extraction
                                    "type": page_type,
                                    "priority": priority,
                                    "has_contact_info": self._likely_has_contact_info(url, result.get('title', ''), result.get('content', ''))
                                })
                        
                except Exception as api_error:
                    logger.error(f"REAL Tavily API error: {api_error}")
                    continue
                
                # INCREASED rate limiting for real API to avoid blocks
                await asyncio.sleep(3)
            
            # Prioritize discovered pages with new priority system
            discovery_data["extraction_priority"] = sorted(
                discovery_data["discovered_pages"],
                key=lambda x: {
                    "critical": 4,  # Contact pages get highest priority
                    "high": 3,      # About and services pages
                    "medium": 2,    # Credentials pages
                    "low": 1        # Other pages
                }.get(x.get("priority", "low"), 1),
                reverse=True
            )[:8]  # Reduced to 8 to focus on highest quality pages
            
            logger.info(f"REAL Tavily API discovered {len(discovery_data['discovered_pages'])} pages")
            
            # STEP 2: Extract full content from the best URLs using Extract API
            if discovery_data["discovered_pages"]:
                await self._extract_page_content(client, discovery_data)
            
            return discovery_data
            
        except Exception as e:
            logger.error(f"Tavily MCP discovery error: {e}")
            return {"error": str(e), "discovered_pages": []}

    async def _extract_page_content(self, client, discovery_data: Dict[str, Any]):
        """
        Extract full content from top URLs using Tavily Extract API
        EXTRACTED FROM LEGACY tools.py
        """
        logger.info("🔍 STEP 2: Using Tavily Extract API for full content extraction")
        
        # PRIORITIZE: Get pages with highest priority and contact info likelihood
        top_urls = sorted(discovery_data["discovered_pages"], 
                        key=lambda x: (
                            {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(x.get("priority", "low"), 1),
                            x.get("has_contact_info", False),
                            x.get('score', 0)
                        ), reverse=True)[:4]  # Increased to 4 for better coverage
        
        for page in top_urls:
            url = page["url"]
            try:
                # REAL EXTRACT API CALL
                extract_response = client.extract(
                    url,
                    extract_depth="advanced",  # Get tables, structured data
                    format="markdown"  # Better structured content
                )
                
                if extract_response and 'results' in extract_response:
                    for extract_result in extract_response['results']:
                        if extract_result.get('url') == url:
                            # Limit extracted content to 2000 chars to prevent context overflow
                            full_content = extract_result.get('raw_content', '')[:2000]
                            page["full_content"] = full_content
                            logger.info(f"✅ Extracted {len(full_content)} chars from {url} (limited to prevent context overflow)")
                            break
                
            except Exception as extract_error:
                logger.warning(f"Extract API error for {url}: {extract_error}")
                continue
            
            # INCREASED rate limiting for extract API
            await asyncio.sleep(2)

    def _categorize_page_type(self, url: str, title: str) -> str:
        """Helper to categorize page types from URL and title"""
        url_lower = url.lower()
        title_lower = title.lower()
        
        if 'contact' in url_lower or 'contact' in title_lower or 'get-in-touch' in url_lower:
            return 'contact'
        elif 'about' in url_lower or 'team' in url_lower or 'about' in title_lower or 'who-we-are' in url_lower:
            return 'about'
        elif 'service' in url_lower or 'service' in title_lower or 'what-we-do' in url_lower:
            return 'services'
        elif 'project' in url_lower or 'gallery' in url_lower or 'portfolio' in url_lower:
            return 'portfolio'
        elif 'license' in url_lower or 'insurance' in url_lower or 'certification' in url_lower:
            return 'credentials'
        else:
            return 'other'
    
    def _calculate_page_priority(self, url: str, title: str, page_type: str) -> str:
        """Calculate priority for extraction based on likelihood of containing critical info"""
        if page_type == 'contact':
            return 'critical'  # Highest priority for contact pages
        elif page_type == 'about':
            return 'high'  # High priority for about pages (often have contact info)
        elif page_type == 'services':
            return 'high'  # High priority for services (contractor_type_ids)
        elif page_type == 'credentials':
            return 'medium'  # Medium for licensing info
        else:
            return 'low'
    
    def _likely_has_contact_info(self, url: str, title: str, content: str) -> bool:
        """Check if page likely contains contact information"""
        indicators = [
            'email', 'phone', 'contact', 'call', 'reach', '@', 'tel:', 'mailto:',
            '(', ')', '-', 'phone:', 'email:', 'address:', 'location:'
        ]
        text_to_check = f"{url} {title} {content}".lower()
        return any(indicator in text_to_check for indicator in indicators)