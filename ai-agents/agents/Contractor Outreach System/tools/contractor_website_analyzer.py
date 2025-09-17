"""
Contractor Website Analysis Tool
ADAPTED FROM COIA Tavily Tool for Contractor Selection System
Analyzes contractor websites to determine company size and capabilities
"""

import logging
import os
import asyncio
from typing import Dict, Any, Optional, List
import json

logger = logging.getLogger(__name__)


class ContractorWebsiteAnalyzer:
    """Website analysis tool for contractor discovery and validation"""
    
    def __init__(self):
        # Initialize Tavily API from environment
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.use_tavily = bool(self.tavily_api_key)
        
        if self.use_tavily:
            logger.info("ContractorWebsiteAnalyzer initialized with Tavily API key")
        else:
            logger.warning("ContractorWebsiteAnalyzer initialized without API key - disabled")

    async def analyze_contractor_website(self, website_url: str, company_name: str) -> Dict[str, Any]:
        """
        Main function: Analyze contractor website to determine company size and capabilities
        
        Args:
            website_url: Contractor's website URL  
            company_name: Company name for context
            
        Returns:
            Dict with company size classification and business details
        """
        logger.info(f"Analyzing contractor website: {company_name} - {website_url}")
        
        try:
            # Step 1: Discover and extract key pages using Tavily
            page_data = await self._discover_contractor_pages(company_name, website_url)
            
            if "error" in page_data:
                logger.warning(f"Website discovery failed: {page_data['error']}")
                return self._fallback_analysis(website_url, company_name)
            
            # Step 2: Extract company size indicators
            size_indicators = self._extract_size_indicators(page_data)
            
            # Step 3: GPT-4 analysis for final classification (placeholder for now)
            classification = await self._classify_contractor_size(size_indicators, company_name)
            
            return {
                'company_size': classification['size_classification'],
                'size_confidence': classification['confidence_score'], 
                'team_size_estimate': classification['estimated_employees'],
                'business_type': classification['business_classification'],
                'specializations': classification['core_specialties'],
                'service_areas': classification['coverage_areas'],
                'target_market': classification['typical_customers'],
                'quality_indicators': classification['quality_signals'],
                'website_data': {
                    'pages_analyzed': len(page_data.get('discovered_pages', [])),
                    'has_team_page': size_indicators['has_team_page'],
                    'has_about_page': size_indicators['has_about_page'],
                    'services_count': len(size_indicators['services_mentioned']),
                    'locations_count': len(size_indicators['office_locations'])
                }
            }
            
        except Exception as e:
            logger.error(f"Contractor website analysis error: {e}")
            return self._fallback_analysis(website_url, company_name)

    async def _discover_contractor_pages(self, company_name: str, website_url: str) -> Dict[str, Any]:
        """
        Discover contractor pages using Tavily API (adapted from COIA tool)
        """
        try:
            # Import Tavily Python SDK
            try:
                from tavily import TavilyClient
            except ImportError:
                logger.warning("Tavily SDK not installed")
                return {"error": "Tavily SDK not installed", "discovered_pages": []}
            
            if not self.use_tavily or not self.tavily_api_key:
                logger.warning("Tavily disabled or TAVILY_API_KEY missing")
                return {"error": "Tavily disabled or no API key", "discovered_pages": []}
            
            client = TavilyClient(api_key=self.tavily_api_key)
            
            discovery_data = {
                "main_website": website_url,
                "discovered_pages": [],
                "api_used": "TAVILY_CONTRACTOR_ANALYSIS"
            }
            
            # Targeted searches for contractor analysis
            search_queries = [
                f"{company_name} about us team staff",  # Team and company info
                f"{company_name} services specialties",  # Services offered
                f"{company_name} contact locations",     # Contact and location info
            ]
            
            discovered_urls = set()
            
            for query in search_queries:
                logger.info(f"Tavily search: {query}")
                
                try:
                    # Focus search on specific website domain
                    website_domain = website_url.replace("http://", "").replace("https://", "").split("/")[0] if website_url else None
                    response = client.search(
                        query=query,
                        search_depth="advanced",
                        max_results=6,
                        include_domains=[website_domain] if website_domain else None,
                        include_raw_content=True
                    )
                    
                    if response and 'results' in response:
                        for result in response['results']:
                            url = result.get('url', '')
                            score = result.get('score', 0)
                            if url and url not in discovered_urls and score > 0.3:
                                discovered_urls.add(url)
                                page_type = self._categorize_contractor_page_type(url, result.get('title', ''))
                                
                                discovery_data["discovered_pages"].append({
                                    "url": url,
                                    "title": result.get('title', ''),
                                    "score": score,
                                    "content": result.get('content', '')[:1000],
                                    "type": page_type,
                                    "has_team_indicators": self._has_team_indicators(url, result.get('title', ''), result.get('content', ''))
                                })
                        
                except Exception as api_error:
                    logger.error(f"Tavily API error: {api_error}")
                    continue
                
                # Rate limiting
                await asyncio.sleep(2)
            
            # Extract full content from key pages
            if discovery_data["discovered_pages"]:
                await self._extract_contractor_page_content(client, discovery_data)
            
            logger.info(f"Discovered {len(discovery_data['discovered_pages'])} contractor pages")
            return discovery_data
            
        except Exception as e:
            logger.error(f"Contractor page discovery error: {e}")
            return {"error": str(e), "discovered_pages": []}

    async def _extract_contractor_page_content(self, client, discovery_data: Dict[str, Any]):
        """Extract full content from key contractor pages"""
        logger.info("Extracting full content from contractor pages")
        
        # Prioritize team, about, and services pages
        priority_pages = sorted(discovery_data["discovered_pages"], 
                               key=lambda x: (
                                   x.get("type") in ["team", "about", "services"],
                                   x.get("has_team_indicators", False),
                                   x.get('score', 0)
                               ), reverse=True)[:3]  # Top 3 pages
        
        for page in priority_pages:
            url = page["url"]
            try:
                extract_response = client.extract(
                    url,
                    extract_depth="advanced",
                    format="markdown"
                )
                
                if extract_response and 'results' in extract_response:
                    for extract_result in extract_response['results']:
                        if extract_result.get('url') == url:
                            full_content = extract_result.get('raw_content', '')[:1500]  # Limit content
                            page["full_content"] = full_content
                            logger.info(f"Extracted content from {url}")
                            break
                
            except Exception as extract_error:
                logger.warning(f"Content extraction error for {url}: {extract_error}")
                continue
            
            await asyncio.sleep(1.5)

    def _categorize_contractor_page_type(self, url: str, title: str) -> str:
        """Categorize contractor page types for analysis"""
        url_lower = url.lower()
        title_lower = title.lower()
        
        # Team/staff pages
        if any(keyword in url_lower or keyword in title_lower for keyword in ['team', 'staff', 'crew', 'our-people']):
            return 'team'
        # About pages
        elif any(keyword in url_lower or keyword in title_lower for keyword in ['about', 'company', 'history', 'who-we-are']):
            return 'about'
        # Services pages  
        elif any(keyword in url_lower or keyword in title_lower for keyword in ['service', 'specialt', 'what-we-do']):
            return 'services'
        # Contact pages
        elif any(keyword in url_lower or keyword in title_lower for keyword in ['contact', 'location', 'office']):
            return 'contact'
        else:
            return 'other'

    def _has_team_indicators(self, url: str, title: str, content: str) -> bool:
        """Check if page likely contains team/size information"""
        indicators = [
            'team', 'staff', 'crew', 'employees', 'workers', 'our people',
            'meet the', 'founded', 'years experience', 'established',
            'owner', 'manager', 'foreman', 'technician'
        ]
        text_to_check = f"{url} {title} {content}".lower()
        return any(indicator in text_to_check for indicator in indicators)

    def _extract_size_indicators(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract company size indicators from discovered pages"""
        indicators = {
            'has_team_page': False,
            'has_about_page': False,
            'team_members_mentioned': [],
            'services_mentioned': [],
            'office_locations': [],
            'years_in_business': None,
            'size_keywords': [],
            'quality_indicators': []
        }
        
        for page in page_data.get('discovered_pages', []):
            page_type = page.get('type', '')
            content = page.get('full_content', '') or page.get('content', '')
            title = page.get('title', '')
            
            # Track page types
            if page_type == 'team':
                indicators['has_team_page'] = True
            elif page_type == 'about':
                indicators['has_about_page'] = True
            
            # Extract team members, services, etc. from content
            content_lower = content.lower()
            
            # Look for team size indicators
            size_keywords = [
                'solo', 'one-man', 'owner-operator', 'small team', 'family business',
                'employees', 'staff members', 'crew', 'technicians', 'workers'
            ]
            for keyword in size_keywords:
                if keyword in content_lower:
                    indicators['size_keywords'].append(keyword)
            
            # Look for services
            service_keywords = [
                'installation', 'repair', 'maintenance', 'replacement', 'service',
                'plumbing', 'electrical', 'hvac', 'roofing', 'flooring'
            ]
            for keyword in service_keywords:
                if keyword in content_lower and keyword not in indicators['services_mentioned']:
                    indicators['services_mentioned'].append(keyword)
            
            # Look for quality indicators
            quality_keywords = [
                'licensed', 'insured', 'certified', 'bonded', 'warranty',
                'guarantee', 'professional', 'experienced', 'established'
            ]
            for keyword in quality_keywords:
                if keyword in content_lower and keyword not in indicators['quality_indicators']:
                    indicators['quality_indicators'].append(keyword)
        
        return indicators

    async def _classify_contractor_size(self, indicators: Dict[str, Any], company_name: str) -> Dict[str, Any]:
        """
        Classify contractor size based on extracted indicators
        TODO: Replace with GPT-4 analysis for more sophisticated classification
        """
        # Simple rule-based classification for now
        size_classification = "small_team"  # Default
        estimated_employees = "2-5"
        confidence_score = 60
        
        # Check for solo operator indicators
        solo_indicators = ['solo', 'one-man', 'owner-operator', 'myself', 'i am']
        if any(indicator in indicators['size_keywords'] for indicator in solo_indicators):
            size_classification = "solo_operator" 
            estimated_employees = "1"
            confidence_score = 80
        
        # Check for larger company indicators  
        large_indicators = ['employees', 'staff members', 'crew', 'multiple locations']
        if any(indicator in indicators['size_keywords'] for indicator in large_indicators):
            if indicators['has_team_page']:
                size_classification = "medium_company"
                estimated_employees = "6-15"
                confidence_score = 75
        
        return {
            'size_classification': size_classification,
            'confidence_score': confidence_score,
            'estimated_employees': estimated_employees,
            'business_classification': 'local_contractor',  # Default
            'core_specialties': indicators['services_mentioned'][:3],  # Top 3 services
            'coverage_areas': ['local'],  # Default
            'typical_customers': 'residential',  # Default
            'quality_signals': indicators['quality_indicators']
        }

    def _fallback_analysis(self, website_url: str, company_name: str) -> Dict[str, Any]:
        """Fallback analysis when website scraping fails"""
        return {
            'company_size': 'unknown',
            'size_confidence': 0,
            'team_size_estimate': 'unknown',
            'business_type': 'unknown',
            'specializations': [],
            'service_areas': [],
            'target_market': 'unknown',
            'quality_indicators': [],
            'website_data': {
                'pages_analyzed': 0,
                'analysis_failed': True,
                'error': 'Website analysis unavailable'
            }
        }


# Test function
async def test_contractor_website_analyzer():
    """Test the contractor website analyzer"""
    analyzer = ContractorWebsiteAnalyzer()
    
    # Test with a sample contractor
    result = await analyzer.analyze_contractor_website(
        website_url="https://emergencyplumbing.com",
        company_name="Emergency Plumbing Services"
    )
    
    print("\nContractor Website Analysis Results:")
    print(f"Company Size: {result['company_size']}")
    print(f"Confidence: {result['size_confidence']}")
    print(f"Team Size: {result['team_size_estimate']}")
    print(f"Specializations: {result['specializations']}")
    print(f"Quality Indicators: {result['quality_indicators']}")


if __name__ == "__main__":
    asyncio.run(test_contractor_website_analyzer())