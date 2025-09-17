"""
Intelligent Contractor Discovery System with Complete Profile Building
Integrates Google Business Search + COIA Profile Builder + Database Storage
"""

from typing import Dict, Any, List, Optional
import logging
import asyncio
import os
import sys
from datetime import datetime

# Import the complete COIA profile system
from complete_profile_builder import CompleteProfileBuilder
from tavily_search import TavilySearchTool
from database_manager import DatabaseManagerTool

# Import the NEW optimized Google Places tool
from google_places_optimized import GooglePlacesOptimized

# Add paths for existing tools
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../agents/eaa'))

logger = logging.getLogger(__name__)


class IntelligentContractorDiscovery:
    """
    Complete intelligent contractor discovery with 66-field profile creation
    Uses COIA's complete profile building system for comprehensive contractor data
    """
    
    def __init__(self):
        """Initialize the intelligent discovery system with optimized Google Places"""
        # Use the complete COIA profile building system
        self.profile_builder = CompleteProfileBuilder()
        self.tavily_search = TavilySearchTool()
        self.database_manager = DatabaseManagerTool()
        # Use the NEW optimized Google Places tool
        self.google_tool = GooglePlacesOptimized()
        self.google_api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        logger.info("IntelligentContractorDiscovery initialized with OPTIMIZED Google Places")

    def _get_flexible_sizes(self, size_preference: str) -> List[str]:
        """
        Get flexible size options based on preference (±1 range)
        This allows matching contractors one size up or down from preference
        """
        size_flexibility = {
            "solo_handyman": ["solo_handyman", "owner_operator"],  # Sizes 1-2
            "owner_operator": ["solo_handyman", "owner_operator", "small_business"],  # Sizes 1-3
            "small_business": ["owner_operator", "small_business", "regional_company"],  # Sizes 2-4
            "regional_company": ["small_business", "regional_company", "enterprise"],  # Sizes 3-5
            "enterprise": ["regional_company", "enterprise"],  # Sizes 4-5
            # Legacy mappings
            "national_chain": ["regional_company", "enterprise"],
        }
        return size_flexibility.get(size_preference, [size_preference])

    async def discover_and_validate_contractors(self, 
                                              project_type: str,
                                              location: Dict[str, str],
                                              target_count: int = 12,
                                              company_size_preference: Optional[str] = None) -> Dict[str, Any]:
        """
        Main intelligent contractor discovery workflow with complete profile building
        
        Args:
            project_type: Type of project (e.g., "plumbing", "electrical")
            location: Dict with city, state, zip
            target_count: Number of contractors needed
            company_size_preference: "solo_handyman", "owner_operator", "small_business", "regional_company"
        
        Returns:
            Dict with discovered contractors with complete 66-field profiles
        """
        logger.info(f"Starting intelligent discovery for {project_type} in {location.get('city', 'Unknown')}")
        
        discovery_results = {
            "success": False,
            "contractors": [],
            "profiles_created": 0,
            "database_saved": 0,
            "expansion_rounds": 0,
            "total_discovered": 0
        }
        
        search_round = 0  # Initialize search round counter
        
        try:
            # Use optimized Google Places discovery
            logger.info(f"[OPTIMIZED] Starting batch discovery for {project_type} in {location.get('city', 'Unknown')}")
            
            # Call optimized Google Places discovery
            google_discovery = await self.google_tool.discover_contractors(
                service_type=project_type,
                location=location,
                target_count=target_count * 2,  # Get 2x to allow for filtering
                radius_miles=15,
                cost_mode="CHEAPEST",  # Use cost-optimized mode
                include_sabs=True,  # Include mobile/service area businesses
                min_rating=3.0  # Lower threshold, we'll filter later
            )
            
            if not google_discovery.get("success") or not google_discovery.get("contractors"):
                logger.warning("No contractors found via Google Places")
                discovery_results["success"] = False
                discovery_results["error"] = "No contractors discovered"
                return discovery_results
            
            logger.info(f"[GOOGLE RESULTS] Found {len(google_discovery['contractors'])} contractors")
            logger.info(f"[API EFFICIENCY] Used {google_discovery['api_calls']['searches']} searches, {google_discovery['api_calls']['details']} detail calls")
            
            profiles_created = []
            
            # Process discovered contractors
            for google_contractor in google_discovery["contractors"]:
                try:
                    company_name = google_contractor.get("name", "Unknown")
                    
                    # Check if already exists in database
                    existing = await self.database_manager.check_existing_contractor(company_name)
                    if existing:
                        logger.info(f"[SKIP] Already in database: {company_name}")
                        profiles_created.append(existing)
                        continue
                    
                    # Build web data using Tavily if website available
                    web_data = None
                    website = google_contractor.get("website", "")
                    if website:
                        logger.info(f"[TAVILY] Enriching {company_name}")
                        tavily_discovery = await self.tavily_search.discover_contractor_pages(
                            company_name=company_name,
                            website_url=website,
                            location=f"{location.get('city', '')}, {location.get('state', '')}"
                        )
                        
                        if tavily_discovery and tavily_discovery.get("discovered_pages"):
                            web_data = self._process_tavily_content(tavily_discovery)
                    
                    # Build complete 66-field profile
                    contractor_profile = await self.profile_builder.build_contractor_profile(
                        company_name=company_name,
                        google_data=google_contractor,  # Pass the optimized data
                        web_data=web_data,
                        license_data=None
                    )
                    
                    # Check company size preference AFTER building profile with ±1 flexibility
                    if company_size_preference:
                        profile_size = contractor_profile.get("contractor_size")
                        if profile_size:
                            # Use flexible size matching (±1 range)
                            acceptable_sizes = self._get_flexible_sizes(company_size_preference)
                            if profile_size not in acceptable_sizes:
                                logger.info(f"[FILTER] Size outside ±1 range: {company_name} is {profile_size}, acceptable: {acceptable_sizes}")
                                continue
                            else:
                                logger.info(f"[MATCH] Size within ±1 range: {company_name} is {profile_size}, wanted {company_size_preference}")
                    
                    # Save to database
                    save_result = await self.database_manager.save_potential_contractor(contractor_profile)
                    if save_result.get("success"):
                        logger.info(f"[DATABASE] Saved: {company_name}")
                        contractor_profile["database_saved"] = True
                        contractor_profile["staging_id"] = save_result.get("staging_id")
                        discovery_results["database_saved"] += 1
                    
                    profiles_created.append(contractor_profile)
                    discovery_results["profiles_created"] += 1
                    
                    # Stop if we have enough
                    if len(profiles_created) >= target_count:
                        logger.info(f"[TARGET MET] Found {len(profiles_created)} contractors")
                        break
                    
                except Exception as e:
                    logger.error(f"Error processing contractor: {e}")
                    continue
                
                # Rate limiting for Tavily/database operations
                await asyncio.sleep(0.5)
            
            discovery_results["contractors"] = profiles_created
            discovery_results["total_discovered"] = len(profiles_created)
            discovery_results["expansion_rounds"] = search_round
            discovery_results["success"] = len(profiles_created) >= target_count * 0.8
            
            logger.info(f"[COMPLETE] Created {len(profiles_created)} contractor profiles")
            return discovery_results
            
        except Exception as e:
            logger.error(f"Intelligent discovery error: {e}")
            discovery_results["error"] = str(e)
            return discovery_results

    def _generate_search_terms(self, project_type: str, location: Dict[str, str]) -> List[str]:
        """Generate intelligent search terms for contractor discovery"""
        city = location.get("city", "")
        state = location.get("state", "")
        
        base_terms = [
            project_type,
            f"{project_type} repair",
            f"{project_type} service", 
            f"{project_type} contractor",
            f"emergency {project_type}",
            f"residential {project_type}",
            f"commercial {project_type}",
            f"{project_type} installation",
            f"licensed {project_type}"
        ]
        
        # Add location-specific terms
        search_terms = []
        for term in base_terms:
            if city and state:
                search_terms.append(f"{term} {city} {state}")
                search_terms.append(f"{city} {term}")
        
        return search_terms[:12]  # Limit to prevent API overuse

    def _process_tavily_content(self, tavily_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Tavily discovery data into format for profile builder"""
        web_data = {
            "extracted_info": {
                "services": [],
                "years_in_business": None,
                "employees": None,
                "has_contact_form": False,
                "contact_form_url": "",
                "certifications": [],
                "service_areas": [],
                "contractor_size": "small_business",
                "social_media_links": {},
                "email": None,
                "phone": None,
                "business_description": ""
            },
            "discovered_pages": tavily_data.get("discovered_pages", [])
        }
        
        # Process discovered pages to extract information
        for page in tavily_data.get("discovered_pages", []):
            content = page.get("full_content", "") or page.get("content", "")
            url = page.get("url", "")
            page_type = page.get("type", "")
            
            # Extract contact information
            if page_type == "contact" and content:
                import re
                # Email extraction
                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', content)
                if email_match and not web_data["extracted_info"]["email"]:
                    web_data["extracted_info"]["email"] = email_match.group(0)
                
                # Phone extraction
                phone_match = re.search(r'[\(]?\d{3}[\)]?[-.\s]?\d{3}[-.\s]?\d{4}', content)
                if phone_match and not web_data["extracted_info"]["phone"]:
                    web_data["extracted_info"]["phone"] = phone_match.group(0)
                
                # Check for contact form
                if 'contact' in url.lower() and ('form' in content.lower() or 'submit' in content.lower()):
                    web_data["extracted_info"]["has_contact_form"] = True
                    web_data["extracted_info"]["contact_form_url"] = url
            
            # Extract services from service pages
            elif page_type == "services" and content:
                # Look for service-related keywords
                service_keywords = ["plumbing", "electrical", "hvac", "roofing", "painting", 
                                  "landscaping", "construction", "remodeling", "repair"]
                for keyword in service_keywords:
                    if keyword in content.lower() and keyword not in web_data["extracted_info"]["services"]:
                        web_data["extracted_info"]["services"].append(keyword)
            
            # Extract business info from about pages
            elif page_type == "about" and content:
                # Years in business
                year_match = re.search(r'(\d+)\+?\s*years?\s*(in business|of experience|serving)', content.lower())
                if year_match:
                    web_data["extracted_info"]["years_in_business"] = int(year_match.group(1))
                
                # Employee count
                emp_match = re.search(r'(\d+)\+?\s*(employees|team members|staff)', content.lower())
                if emp_match:
                    web_data["extracted_info"]["employees"] = int(emp_match.group(1))
                
                # Save business description (first 500 chars of about content)
                if not web_data["extracted_info"]["business_description"]:
                    web_data["extracted_info"]["business_description"] = content[:500]
        
        return web_data


# Test function
async def test_complete_profile_discovery():
    """Test the complete profile discovery system"""
    discovery = IntelligentContractorDiscovery()
    
    result = await discovery.discover_and_validate_contractors(
        project_type="plumbing",
        location={"city": "Orlando", "state": "FL", "zip": "32801"},
        target_count=3,
        company_size_preference="small_business"
    )
    
    print("\n=== COMPLETE PROFILE DISCOVERY TEST ===")
    print(f"Success: {result['success']}")
    print(f"Profiles Created: {result['profiles_created']}")
    print(f"Database Saved: {result['database_saved']}")
    print(f"Expansion Rounds: {result['expansion_rounds']}")
    
    if result['contractors']:
        print("\nContractor Profiles Created:")
        for i, contractor in enumerate(result['contractors'][:3]):
            print(f"\n{i+1}. {contractor.get('company_name', 'Unknown')}")
            print(f"   Data Completeness: {contractor.get('data_completeness', 0)}%")
            print(f"   Lead Score: {contractor.get('lead_score', 0)}")
            print(f"   Company Size: {contractor.get('contractor_size', 'Unknown')}")
            print(f"   Database Saved: {contractor.get('database_saved', False)}")
            print(f"   Data Sources: {', '.join(contractor.get('data_sources', []))}")


if __name__ == "__main__":
    asyncio.run(test_complete_profile_discovery())