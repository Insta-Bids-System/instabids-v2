"""
Tavily Search Tool - Copied from COIA
Comprehensive web research for contractor discovery
"""

import logging
import os
import asyncio
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TavilySearchTool:
    """Tavily API web research tool for comprehensive contractor discovery"""
    
    def __init__(self):
        # Initialize Tavily API from environment
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.use_tavily = bool(self.tavily_api_key)
        
        if self.use_tavily:
            logger.info("TavilySearchTool initialized with API key")
        else:
            logger.warning("TavilySearchTool initialized without API key - disabled")

    async def discover_contractor_pages(self, company_name: str, website_url: str, location: Optional[str] = None) -> Dict[str, Any]:
        """
        Discover contractor pages using Tavily API for comprehensive research
        """
        logger.info(f"Using Tavily API to discover pages for {company_name}")
        
        try:
            # Import Tavily Python SDK
            try:
                from tavily import TavilyClient
            except ImportError:
                logger.warning("Tavily SDK not installed")
                return {"error": "Tavily SDK not installed", "discovered_pages": []}
            
            # Initialize Tavily client
            if not self.use_tavily or not self.tavily_api_key:
                logger.warning("Tavily disabled or TAVILY_API_KEY missing")
                return {"error": "Tavily disabled or no API key", "discovered_pages": []}
            
            client = TavilyClient(api_key=self.tavily_api_key)
            
            discovery_data = {
                "main_website": website_url,
                "discovered_pages": [],
                "content_sources": [],
                "extraction_priority": [],
                "api_used": "TAVILY_API"
            }
            
            # Targeted searches for contact info and services
            search_queries = [
                f"{company_name} contact email phone address",
                f"{company_name} services specialties certifications",
            ]
            
            discovered_urls = set()
            
            for query in search_queries:
                logger.info(f"Making Tavily API call: {query}")
                
                try:
                    # Search for pages AND get their content
                    website_domain = website_url.replace("http://", "").replace("https://", "").split("/")[0] if website_url else None
                    response = client.search(
                        query=query,
                        search_depth="advanced",
                        max_results=8,
                        include_domains=[website_domain] if website_domain else None,
                        include_raw_content=True
                    )
                    
                    if response and 'results' in response:
                        for result in response['results']:
                            url = result.get('url', '')
                            score = result.get('score', 0)
                            if url and url not in discovered_urls and score > 0.4:
                                discovered_urls.add(url)
                                page_type = self._categorize_page_type(url, result.get('title', ''))
                                priority = self._calculate_page_priority(url, result.get('title', ''), page_type)
                                
                                discovery_data["discovered_pages"].append({
                                    "url": url,
                                    "title": result.get('title', ''),
                                    "score": score,
                                    "content": result.get('content', '')[:1500],
                                    "type": page_type,
                                    "priority": priority,
                                    "has_contact_info": self._likely_has_contact_info(url, result.get('title', ''), result.get('content', ''))
                                })
                        
                except Exception as api_error:
                    logger.error(f"Tavily API error: {api_error}")
                    continue
                
                # Rate limiting
                await asyncio.sleep(3)
            
            # Prioritize discovered pages
            discovery_data["extraction_priority"] = sorted(
                discovery_data["discovered_pages"],
                key=lambda x: {
                    "critical": 4,
                    "high": 3,
                    "medium": 2,
                    "low": 1
                }.get(x.get("priority", "low"), 1),
                reverse=True
            )[:8]
            
            logger.info(f"Tavily API discovered {len(discovery_data['discovered_pages'])} pages")
            
            # Extract full content from the best URLs
            if discovery_data["discovered_pages"]:
                await self._extract_page_content(client, discovery_data)
            
            return discovery_data
            
        except Exception as e:
            logger.error(f"Tavily discovery error: {e}")
            return {"error": str(e), "discovered_pages": []}

    async def _extract_page_content(self, client, discovery_data: Dict[str, Any]):
        """
        Extract full content from top URLs using Tavily Extract API
        """
        logger.info("Using Tavily Extract API for full content extraction")
        
        # Get pages with highest priority
        top_urls = sorted(discovery_data["discovered_pages"], 
                        key=lambda x: (
                            {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(x.get("priority", "low"), 1),
                            x.get("has_contact_info", False),
                            x.get('score', 0)
                        ), reverse=True)[:4]
        
        for page in top_urls:
            url = page["url"]
            try:
                # Extract full content
                extract_response = client.extract(
                    url,
                    extract_depth="advanced",
                    format="markdown"
                )
                
                if extract_response and 'results' in extract_response:
                    for extract_result in extract_response['results']:
                        if extract_result.get('url') == url:
                            full_content = extract_result.get('raw_content', '')[:2000]
                            page["full_content"] = full_content
                            logger.info(f"Extracted {len(full_content)} chars from {url}")
                            break
                
            except Exception as extract_error:
                logger.warning(f"Extract API error for {url}: {extract_error}")
                continue
            
            # Rate limiting
            await asyncio.sleep(2)

    def _categorize_page_type(self, url: str, title: str) -> str:
        """Helper to categorize page types"""
        url_lower = url.lower()
        title_lower = title.lower()
        
        if 'contact' in url_lower or 'contact' in title_lower:
            return 'contact'
        elif 'about' in url_lower or 'about' in title_lower:
            return 'about'
        elif 'service' in url_lower or 'service' in title_lower:
            return 'services'
        elif 'project' in url_lower or 'portfolio' in url_lower:
            return 'portfolio'
        elif 'license' in url_lower or 'certification' in url_lower:
            return 'credentials'
        else:
            return 'other'
    
    def _calculate_page_priority(self, url: str, title: str, page_type: str) -> str:
        """Calculate priority for extraction"""
        if page_type == 'contact':
            return 'critical'
        elif page_type == 'about':
            return 'high'
        elif page_type == 'services':
            return 'high'
        elif page_type == 'credentials':
            return 'medium'
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