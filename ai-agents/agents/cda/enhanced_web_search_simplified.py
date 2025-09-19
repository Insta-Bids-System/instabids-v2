"""
Enhanced Web Search Contractor Discovery Agent - Simplified for Current Database
Adapts Google Places discovery with website analysis for current property management system
"""
import json
import os
from typing import Any, Optional, Dict, List
import logging
import asyncio

logger = logging.getLogger(__name__)


class EnhancedWebSearchSimplified:
    """Enhanced web search adapted for current database schema"""

    def __init__(self, supabase_client):
        self.supabase = supabase_client
        
        # Set environment variables for APIs
        os.environ["GOOGLE_PLACES_API_KEY"] = "AIzaSyBacJk_H4rpExmLiG1g8-nAGZJbSgC3IaA"
        os.environ["TAVILY_API_KEY"] = "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"
        
        logger.info(f"[EnhancedWebSearchSimplified] Initialized with current database schema")

    async def discover_contractors_with_profiles(self, 
                                                project_type: str,
                                                location: Dict[str, str],
                                                contractors_needed: int = 10,
                                                radius_miles: int = 15) -> Dict[str, Any]:
        """
        Discover contractors with enhanced profiles using Google Places + Tavily
        
        Args:
            project_type: Type of project (plumbing, electrical, etc.)
            location: Location dict with city, state, zip
            contractors_needed: Number of contractors to find
            radius_miles: Search radius
        
        Returns:
            Dict with discovered contractors with enhanced profiles
        """
        logger.info(f"[EnhancedWebSearchSimplified] Starting discovery for {project_type} in {location.get('city', '')}")
        
        try:
            # Step 1: Google Places Discovery
            from agents.cda.google_places_optimized import GooglePlacesOptimized
            google_tool = GooglePlacesOptimized()
            
            google_discovery = await google_tool.discover_contractors(
                service_type=project_type,
                location=location,
                target_count=contractors_needed,
                radius_miles=radius_miles,
                cost_mode="CHEAPEST",
                include_sabs=True,
                min_rating=3.0
            )
            
            if not google_discovery.get("success"):
                return {
                    "success": False,
                    "error": "Google Places discovery failed",
                    "contractors": []
                }
            
            # Step 2: Build enhanced profiles with website analysis
            enhanced_contractors = []
            for google_contractor in google_discovery.get("contractors", []):
                try:
                    # Create enhanced profile with website analysis
                    enhanced_profile = await self._build_enhanced_profile(
                        google_contractor,
                        project_type
                    )
                    
                    enhanced_contractors.append(enhanced_profile)
                    
                    # Save to database
                    await self._save_to_contractors_table(enhanced_profile)
                    
                    if len(enhanced_contractors) >= contractors_needed:
                        break
                        
                except Exception as e:
                    logger.error(f"Error building enhanced profile: {e}")
                    continue
            
            return {
                "success": True,
                "contractors": enhanced_contractors,
                "total_discovered": len(enhanced_contractors),
                "google_api_calls": google_discovery.get("api_calls", {}),
                "enhanced_profiles": len(enhanced_contractors)
            }
            
        except Exception as e:
            logger.error(f"Enhanced discovery error: {e}")
            return {
                "success": False,
                "error": str(e),
                "contractors": []
            }
    
    async def _build_enhanced_profile(self, google_contractor: Dict[str, Any], project_type: str) -> Dict[str, Any]:
        """Build enhanced contractor profile with website analysis"""
        
        enhanced_profile = {
            # Basic Google data
            "business_name": google_contractor.get("name", "Unknown"),
            "website": google_contractor.get("website", ""),
            "business_description": f"Professional {project_type} contractor",
            "primary_trade": self._map_project_type_to_trade(project_type),
            "secondary_trades": [],
            
            # Address from Google Places
            "business_address": {
                "street": google_contractor.get("address", ""),
                "city": google_contractor.get("city", ""),
                "state": google_contractor.get("state", ""),
                "zip": google_contractor.get("zip", ""),
                "formatted": google_contractor.get("formatted_address", "")
            },
            
            # Business info
            "business_type": "llc",  # Default assumption
            "years_in_business": None,
            "employee_count": None,
            
            # Service capabilities (inferred from project type)
            "emergency_service": project_type.lower() in ["plumbing", "electrical", "hvac"],
            "preventive_maintenance": True,
            "new_installations": True,
            "renovations": True,
            "inspections": True,
            
            # Status
            "verification_status": "pending_review",
            "profile_completion_percentage": 60,  # Base completion from Google data
            "onboarding_completed": False,
            
            # Enhanced data from website analysis
            "google_rating": google_contractor.get("rating", 0),
            "google_reviews": google_contractor.get("reviews", 0),
            "phone": google_contractor.get("phone", ""),
            "google_place_id": google_contractor.get("google_place_id", ""),
            "discovery_source": "enhanced_web_search",
            "website_analyzed": False
        }
        
        # Step 3: Website analysis with Tavily if website available
        website = google_contractor.get("website", "")
        if website:
            try:
                website_data = await self._analyze_contractor_website(
                    google_contractor.get("name", ""),
                    website
                )
                
                if website_data:
                    enhanced_profile.update(website_data)
                    enhanced_profile["website_analyzed"] = True
                    enhanced_profile["profile_completion_percentage"] = 85  # Higher completion with website data
                    
            except Exception as e:
                logger.error(f"Website analysis failed for {website}: {e}")
        
        return enhanced_profile
    
    async def _analyze_contractor_website(self, company_name: str, website: str) -> Dict[str, Any]:
        """Analyze contractor website using Tavily API"""
        
        try:
            # Import Tavily search tool
            from agents.cda.tavily_search import TavilySearchTool
            tavily_search = TavilySearchTool()
            
            # Search for company information
            search_result = await tavily_search.discover_contractor_pages(
                company_name=company_name,
                website_url=website,
                location=""  # Location not needed for website analysis
            )
            
            if search_result and search_result.get("discovered_pages"):
                pages = search_result["discovered_pages"]
                
                # Extract enhanced data from website
                website_data = {
                    "business_description": self._extract_business_description(pages),
                    "years_in_business": self._extract_years_in_business(pages),
                    "employee_count": self._extract_employee_count(pages),
                    "specialized_services": self._extract_specialized_services(pages),
                    "certifications": self._extract_certifications(pages),
                    "service_areas": self._extract_service_areas(pages)
                }
                
                # Remove None values
                return {k: v for k, v in website_data.items() if v is not None}
            
        except Exception as e:
            logger.error(f"Tavily website analysis error: {e}")
        
        return {}
    
    def _extract_business_description(self, pages: List[Dict]) -> Optional[str]:
        """Extract business description from website content"""
        for page in pages[:2]:  # Check first 2 pages
            content = page.get("content", "").lower()
            if "about" in page.get("url", "").lower() or "about" in content:
                # Extract meaningful description (simple version)
                sentences = content.split(".")[:3]  # First 3 sentences
                description = ". ".join(sentences).strip()
                if len(description) > 50:
                    return description[:500]  # Limit to 500 chars
        return None
    
    def _extract_years_in_business(self, pages: List[Dict]) -> Optional[int]:
        """Extract years in business from website content"""
        import re
        current_year = 2025
        
        for page in pages:
            content = page.get("content", "")
            # Look for patterns like "since 2010", "established 2005", etc.
            patterns = [
                r"since\s+(\d{4})",
                r"established\s+(\d{4})",
                r"founded\s+(\d{4})",
                r"serving.*?(\d{4})"
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    try:
                        year = int(matches[0])
                        if 1950 <= year <= current_year:
                            return current_year - year
                    except ValueError:
                        continue
        return None
    
    def _extract_employee_count(self, pages: List[Dict]) -> Optional[int]:
        """Extract employee count from website content"""
        import re
        
        for page in pages:
            content = page.get("content", "")
            # Look for patterns about team size
            patterns = [
                r"(\d+)\s+employees?",
                r"team\s+of\s+(\d+)",
                r"(\d+)\s+technicians?",
                r"staff\s+of\s+(\d+)"
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    try:
                        count = int(matches[0])
                        if 1 <= count <= 1000:  # Reasonable range
                            return count
                    except ValueError:
                        continue
        return None
    
    def _extract_specialized_services(self, pages: List[Dict]) -> List[str]:
        """Extract specialized services from website content"""
        services = []
        service_keywords = [
            "emergency repair", "installation", "maintenance", "inspection",
            "renovation", "residential", "commercial", "industrial",
            "24/7", "licensed", "insured", "certified"
        ]
        
        for page in pages:
            content = page.get("content", "").lower()
            for keyword in service_keywords:
                if keyword in content and keyword not in services:
                    services.append(keyword)
        
        return services[:10]  # Limit to top 10
    
    def _extract_certifications(self, pages: List[Dict]) -> List[str]:
        """Extract certifications from website content"""
        certifications = []
        cert_keywords = [
            "licensed", "certified", "bonded", "insured", "accredited",
            "EPA certified", "OSHA", "NATE", "ACCA", "BBB"
        ]
        
        for page in pages:
            content = page.get("content", "").lower()
            for keyword in cert_keywords:
                if keyword in content and keyword not in certifications:
                    certifications.append(keyword)
        
        return certifications[:5]  # Limit to top 5
    
    def _extract_service_areas(self, pages: List[Dict]) -> List[str]:
        """Extract service areas from website content"""
        import re
        areas = []
        
        for page in pages:
            content = page.get("content", "")
            # Look for city/area mentions
            city_patterns = [
                r"serving\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"areas?\s+include[s]?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            ]
            
            for pattern in city_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if len(match) > 3 and match not in areas:
                        areas.append(match)
        
        return areas[:10]  # Limit to top 10
    
    def _map_project_type_to_trade(self, project_type: str) -> str:
        """Map project type to database trade enum"""
        mapping = {
            "plumbing": "plumbing",
            "electrical": "electrical", 
            "hvac": "hvac",
            "roofing": "roofing",
            "painting": "painting",
            "landscaping": "landscaping",
            "carpentry": "carpentry",
            "general": "general_maintenance"
        }
        return mapping.get(project_type.lower(), "other")
    
    async def _save_to_contractors_table(self, profile: Dict[str, Any]):
        """Save contractor profile to contractors table"""
        try:
            # Prepare database record for contractors table
            record = {
                "business_name": profile.get("business_name", ""),
                "business_type": profile.get("business_type", "llc"),
                "years_in_business": profile.get("years_in_business"),
                "employee_count": profile.get("employee_count"),
                "business_address": profile.get("business_address", {}),
                "website": profile.get("website", ""),
                "business_description": profile.get("business_description", ""),
                "primary_trade": profile.get("primary_trade", "other"),
                "secondary_trades": profile.get("secondary_trades", []),
                "emergency_service": profile.get("emergency_service", False),
                "preventive_maintenance": profile.get("preventive_maintenance", True),
                "new_installations": profile.get("new_installations", True),
                "renovations": profile.get("renovations", True),
                "inspections": profile.get("inspections", True),
                "verification_status": profile.get("verification_status", "pending_review"),
                "profile_completion_percentage": profile.get("profile_completion_percentage", 60),
                "onboarding_completed": profile.get("onboarding_completed", False)
            }
            
            # Remove None values
            record = {k: v for k, v in record.items() if v is not None}
            
            # Insert to database
            result = self.supabase.table("contractors").insert(record).execute()
            
            if result.data:
                logger.info(f"[Database] Saved contractor: {profile.get('business_name', 'Unknown')}")
                return True
                
        except Exception as e:
            logger.error(f"Database save error: {e}")
            
        return False