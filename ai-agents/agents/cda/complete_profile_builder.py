"""
Complete Profile Builder Tool - Copied from COIA
Builds comprehensive 66-field contractor profiles from multiple data sources
"""

import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime

from database_simple import SupabaseDB

logger = logging.getLogger(__name__)


class CompleteProfileBuilder:
    """Build comprehensive contractor profiles from all data sources - 66 fields total"""
    
    def __init__(self):
        """Initialize with database connection"""
        self.db = SupabaseDB()
    
    async def build_contractor_profile(self, company_name: str,
                                      google_data: Optional[Dict[str, Any]] = None,
                                      web_data: Optional[Dict[str, Any]] = None,
                                      license_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Build comprehensive contractor profile from ALL data sources to fill 66 contractor fields
        """
        logger.info(f"Building comprehensive contractor profile for {company_name}")
        
        # Initialize profile with ALL 66 contractor fields
        profile = {
            # Core business info
            "business_name": company_name,
            "company_name": company_name,  # Duplicate for compatibility
            "contact_name": "",
            "phone": "",
            "email": "",
            "website": "",
            "address": "",
            "city": "",
            "state": "",
            "zip_code": "",
            "latitude": None,
            "longitude": None,
            
            # Business details
            "years_in_business": None,
            "business_established_year": None,
            "estimated_employees": None,
            "contractor_size": "small_business",  # Default to valid enum value
            "contractor_size_category": "small_business",  # Same as contractor_size for potential_contractors table
            "service_radius_miles": None,
            "service_zip_codes": [],
            
            # Services and specialties
            "specialties": [],
            "certifications": [],
            "license_number": "",
            "license_state": "",
            "license_verified": False,
            "insurance_verified": False,
            "bonded": False,
            
            # Ratings and reviews
            "rating": None,
            "review_count": 0,
            "recent_reviews": [],
            "last_review_date": None,
            
            # Google specific fields
            "google_rating": None,
            "google_review_count": 0,
            "google_place_id": "",
            "google_maps_url": "",
            "google_business_status": "",
            "google_types": [],
            
            # Lead scoring
            "lead_score": 0,
            "data_completeness": 0,
            "lead_status": "qualified",  # Use valid enum value
            
            # Contact and forms
            "has_contact_form": False,
            "contact_form_url": "",
            "form_fields": [],
            "last_form_submission": None,
            "form_submission_count": 0,
            
            # Social media and digital presence
            "facebook_url": "",
            "instagram_url": "",
            "linkedin_url": "",
            "twitter_url": "",
            "youtube_url": "",
            "social_media_followers": 0,
            "digital_presence_score": 0,
            
            # Business intelligence
            "completeness_score": 0,
            "verified_business": False,
            "profile_insights": [],
            "data_sources": [],
            
            # Discovery metadata
            "discovery_source": "intelligent_discovery",
            "discovery_timestamp": datetime.utcnow().isoformat(),
            "tier": 3,  # Tier 3 for discovered contractors
            
            # Raw data storage
            "raw_data": {},
            "enrichment_data": {}
        }
        
        filled_fields = 0
        total_fields = 66
        
        # Integrate Google Places data
        if google_data and google_data.get("success") != False:
            profile["data_sources"].append("google_places")
            
            # Map Google data to profile fields (using correct Google API field names)
            profile.update({
                "phone": google_data.get("phone", ""),
                "address": google_data.get("address", ""),
                "website": google_data.get("website", ""),
                "google_rating": google_data.get("google_rating", 0),
                "google_review_count": google_data.get("google_review_count", 0),
                "google_place_id": google_data.get("google_place_id", ""),
                "google_maps_url": google_data.get("google_maps_url", ""),
                "google_business_status": google_data.get("google_business_status", ""),
                "google_types": google_data.get("google_types", []),
                "verified_business": True,
                "rating": google_data.get("google_rating", 0),  # Use Google rating as general rating
                "review_count": google_data.get("google_review_count", 0)
            })
            
            # Extract city/state/zip from address with multiple patterns
            address = google_data.get("address", "")
            if address:
                # Try multiple patterns for address parsing
                # Pattern 1: Standard US format "123 Main St, City, ST 12345"
                match = re.search(r',\s*([^,]+),\s*([A-Z]{2})\s*(\d{5})', address)
                if match:
                    profile["city"] = match.group(1).strip()
                    profile["state"] = match.group(2).strip()
                    profile["zip_code"] = match.group(3).strip()
                else:
                    # Pattern 2: Try without comma before state "City ST 12345"
                    match = re.search(r'([^,]+)\s+([A-Z]{2})\s+(\d{5})', address)
                    if match:
                        profile["city"] = match.group(1).strip()
                        profile["state"] = match.group(2).strip()
                        profile["zip_code"] = match.group(3).strip()
                    else:
                        # Pattern 3: Extract whatever we can
                        parts = address.split(',')
                        if len(parts) >= 2:
                            profile["city"] = parts[-2].strip() if len(parts) >= 2 else ""
                            # Try to extract state and zip from last part
                            last_part = parts[-1].strip()
                            state_zip = re.search(r'([A-Z]{2})\s*(\d{5})?', last_part)
                            if state_zip:
                                profile["state"] = state_zip.group(1)
                                if state_zip.group(2):
                                    profile["zip_code"] = state_zip.group(2)
            
            # Add Google business hours if available
            if google_data.get("business_hours"):
                profile["business_hours"] = google_data.get("business_hours")
            
            # Add lat/long if available
            if google_data.get("latitude"):
                profile["latitude"] = google_data.get("latitude")
            if google_data.get("longitude"):
                profile["longitude"] = google_data.get("longitude")
            
            profile["completeness_score"] += 25
            profile["profile_insights"].append("Google Business Profile verified")
            filled_fields += 8
        
        # Integrate comprehensive web data (support both formats)
        if web_data:
            profile["data_sources"].append("website_scraping")
            
            # Handle Tavily format (discovered_pages)
            if web_data.get("discovered_pages"):
                logger.info(f"[DEBUG] Found {len(web_data['discovered_pages'])} pages, calling AI analysis...")
                extracted = await self._analyze_discovered_pages(web_data["discovered_pages"], company_name)
                logger.info(f"[DEBUG] AI analysis returned {len(extracted)} fields")
            # Handle old format (extracted_info)  
            elif web_data.get("extracted_info"):
                extracted = web_data["extracted_info"]
            else:
                extracted = {}
            
            # Map web data to profile fields - comprehensive mapping
            profile.update({
                "specialties": extracted.get("specialties") or extracted.get("services", []),
                "years_in_business": extracted.get("years_in_business"),
                "estimated_employees": extracted.get("estimated_employees") or extracted.get("employees"),
                "business_established_year": extracted.get("business_established_year"),
                "contact_name": extracted.get("contact_name"),
                "has_contact_form": bool(extracted.get("contact_form_url")),
                "contact_form_url": extracted.get("contact_form_url", ""),
                "certifications": extracted.get("certifications", []),
                "license_number": extracted.get("license_number"),
                "license_verified": extracted.get("license_verified", False),
                "insurance_verified": extracted.get("insurance_verified", False),
                "bonded": extracted.get("bonded", False),
                "service_areas": extracted.get("service_areas", []),
                "ai_business_summary": extracted.get("ai_business_summary", ""),
                "ai_capability_description": extracted.get("ai_capability_description", ""),
                "competitive_advantages": extracted.get("competitive_advantages", "")
            })
            
            # Add more extracted fields that were being missed
            if extracted.get("service_radius"):
                profile["service_radius_miles"] = extracted.get("service_radius")
            
            if extracted.get("emergency_services"):
                profile["emergency_services"] = extracted.get("emergency_services")
                
            if extracted.get("project_types"):
                profile["supported_project_types"] = extracted.get("project_types")
                
            if extracted.get("capabilities"):
                profile["capabilities"] = extracted.get("capabilities")
                
            # Override with specific extracted values if they exist
            if not profile.get("email") and extracted.get("email"):
                profile["email"] = extracted.get("email")
                
            if not profile.get("phone") and extracted.get("phone"):
                profile["phone"] = extracted.get("phone")
                
            if not profile.get("city") and extracted.get("city"):
                profile["city"] = extracted.get("city")
                
            if not profile.get("state") and extracted.get("state"):
                profile["state"] = extracted.get("state")
                
            if not profile.get("zip_code") and extracted.get("zip"):
                profile["zip_code"] = extracted.get("zip")
            
            # Map contractor size from extracted data to proper enum values
            extracted_size = extracted.get("contractor_size", "").lower()
            if extracted_size:
                size_mapping = {
                    "small": "small_business",
                    "medium": "small_business",  # Map medium to small_business as well
                    "large": "regional_company",
                    "solo": "solo_handyman",
                    "owner": "owner_operator"
                }
                mapped_size = size_mapping.get(extracted_size, "small_business")
                profile["contractor_size"] = mapped_size
                profile["contractor_size_category"] = mapped_size  # Set both fields for compatibility
            
            # Add social media URLs
            social_links = extracted.get("social_media_links", {})
            profile.update({
                "facebook_url": social_links.get("facebook_url", ""),
                "instagram_url": social_links.get("instagram_url", ""),
                "linkedin_url": social_links.get("linkedin_url", ""),
                "twitter_url": social_links.get("twitter_url", ""),
                "youtube_url": social_links.get("youtube_url", "")
            })
            
            # Add contact methods - handle both new format and old format
            contact_methods = extracted.get("contact_methods", {})
            if contact_methods.get("emails"):
                profile["email"] = contact_methods["emails"][0]  # Use first email
            elif extracted.get("email"):  # New direct format
                profile["email"] = extracted["email"]
                
            if contact_methods.get("phones") and not profile["phone"]:
                profile["phone"] = contact_methods["phones"][0]  # Use first phone if no Google phone
            elif extracted.get("phone") and not profile["phone"]:  # New direct format
                profile["phone"] = extracted["phone"]
            
            profile["completeness_score"] += 35
            profile["profile_insights"].append("Website data integrated")
            filled_fields += 15
        
        # Integrate license data if available
        if license_data and license_data.get("success"):
            profile["data_sources"].append("license_verification")
            
            profile.update({
                "license_number": license_data.get("license_number", ""),
                "license_state": license_data.get("state", ""),
                "license_verified": True,
                "license_status": license_data.get("status", ""),
                "license_expiry": license_data.get("expiry_date", "")
            })
            
            profile["completeness_score"] += 15
            profile["profile_insights"].append("License verified")
            filled_fields += 5
        
        # Calculate final scores
        profile["data_completeness"] = round((filled_fields / total_fields) * 100)
        profile["lead_score"] = self._calculate_lead_score(profile)
        
        # Add qualification status based on completeness
        if profile["data_completeness"] >= 60:
            profile["lead_status"] = "qualified"
        elif profile["data_completeness"] >= 30:
            profile["lead_status"] = "enriched"
        else:
            profile["lead_status"] = "new"
        
        # Store raw data for future reference
        profile["raw_data"] = {
            "google": google_data,
            "web": web_data,
            "license": license_data
        }
        
        logger.info(f"Profile built for {company_name}: {profile['data_completeness']}% complete, Score: {profile['lead_score']}")
        
        # Save to database
        saved_profile = await self.save_to_database(profile)
        if saved_profile:
            profile["database_id"] = saved_profile.get("id")
            logger.info(f"Profile saved to database with ID: {profile['database_id']}")
        
        return profile
    
    def _calculate_lead_score(self, profile: Dict[str, Any]) -> int:
        """Calculate lead score based on profile completeness and quality indicators"""
        score = 0
        
        # Basic contact info (30 points)
        if profile.get("phone"):
            score += 10
        if profile.get("email"):
            score += 10
        if profile.get("website"):
            score += 10
        
        # Business verification (25 points)
        if profile.get("verified_business"):
            score += 15
        if profile.get("license_verified"):
            score += 10
        
        # Reputation (25 points)
        rating = profile.get("google_rating") or profile.get("rating") or 0
        if rating >= 4.5:
            score += 25
        elif rating >= 4.0:
            score += 20
        elif rating >= 3.5:
            score += 15
        elif rating > 0:
            score += 10
        
        # Experience (10 points)
        years = profile.get("years_in_business") or 0
        if years >= 10:
            score += 10
        elif years >= 5:
            score += 7
        elif years >= 2:
            score += 5
        
        # Digital presence (10 points)
        if profile.get("has_contact_form"):
            score += 5
        social_count = sum(1 for k in ["facebook_url", "instagram_url", "linkedin_url"] 
                          if profile.get(k))
        score += min(social_count * 2, 5)
        
        return min(score, 100)  # Cap at 100
    
    async def save_to_database(self, profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Save the contractor profile to the contractor_leads table"""
        try:
            # Prepare data for contractor_leads table
            contractor_lead_data = {
                "source": "manual",  # Required enum field (manual, google_maps, yelp, etc.)
                "source_url": profile.get("website"),  # Store website as source URL
                "company_name": profile.get("company_name"),
                "contact_name": profile.get("contact_name"),
                "phone": profile.get("phone"),
                "email": profile.get("email"),
                "website": profile.get("website"),
                "address": profile.get("address"),
                "city": profile.get("city"),
                "state": profile.get("state"),
                "zip_code": profile.get("zip_code"),
                "latitude": profile.get("latitude"),
                "longitude": profile.get("longitude"),
                "service_radius_miles": profile.get("service_radius_miles"),
                
                # Business details
                "estimated_employees": profile.get("estimated_employees"),
                "years_in_business": profile.get("years_in_business"),
                "business_established_year": profile.get("business_established_year"),
                
                # Services and capabilities
                "specialties": profile.get("specialties", []),
                "certifications": profile.get("certifications", []),
                "service_categories": profile.get("service_categories", []),
                "supported_project_types": profile.get("supported_project_types", []),
                "capabilities": profile.get("capabilities", []),
                
                # Licensing and verification
                "license_number": profile.get("license_number"),
                "license_state": profile.get("license_state"),
                "license_verified": profile.get("license_verified", False),
                "insurance_verified": profile.get("insurance_verified", False),
                "bonded": profile.get("bonded", False),
                
                # Ratings and reviews
                "rating": profile.get("google_rating"),
                "review_count": profile.get("google_review_count"),
                
                # Contact form data
                "has_contact_form": profile.get("has_contact_form", False),
                "contact_form_url": profile.get("contact_form_url"),
                
                # Store AI summaries in enrichment_data since columns don't exist
                
                # Metadata
                "lead_score": profile.get("lead_score"),
                "data_completeness": profile.get("data_completeness"),
                "lead_status": profile.get("lead_status"),
                
                # Store raw data and AI summaries for reference
                "enrichment_data": {
                    "google_data": profile.get("raw_data", {}).get("google"),
                    "web_extraction": profile.get("raw_data", {}).get("web"),
                    "ai_extracted": True,
                    "extraction_date": datetime.now().isoformat(),
                    "ai_business_summary": profile.get("ai_business_summary"),
                    "ai_capability_description": profile.get("ai_capability_description"),
                    "competitive_advantages": profile.get("competitive_advantages"),
                    "services": profile.get("services", [])
                }
            }
            
            # Check if contractor already exists
            existing = self.db.client.table('contractor_leads').select('id').eq(
                'company_name', contractor_lead_data['company_name']
            ).execute()
            
            if existing.data:
                # Update existing record
                logger.info(f"Updating existing contractor_leads record for {contractor_lead_data['company_name']}")
                result = self.db.client.table('contractor_leads').update(
                    contractor_lead_data
                ).eq('id', existing.data[0]['id']).execute()
                
                if result.data:
                    return result.data[0]
            else:
                # Insert new record
                logger.info(f"Inserting new contractor_leads record for {contractor_lead_data['company_name']}")
                result = self.db.client.table('contractor_leads').insert(
                    contractor_lead_data
                ).execute()
                
                if result.data:
                    return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error saving contractor to database: {e}")
            return None
    
    async def _analyze_discovered_pages(self, pages: list, company_name: str) -> Dict[str, Any]:
        """Use GPT-4 AI to analyze Tavily discovered pages and extract all 66 fields"""
        
        logger.info(f"[CompleteProfileBuilder] Using GPT-4 AI to analyze {len(pages)} pages for {company_name}")
        
        # Initialize AI analyzer
        from agents.cda.ai_profile_analyzer import AIProfileAnalyzer
        ai_analyzer = AIProfileAnalyzer()
        
        # Use real AI to extract all 66 fields
        extracted_data = await ai_analyzer.analyze_contractor_website(
            company_name=company_name,
            website_content="",  # Not used, pages are passed directly
            website_pages=pages
        )
        
        # Log what AI extracted
        filled_count = len([v for v in extracted_data.values() if v is not None and v != ""])
        logger.info(f"[CompleteProfileBuilder] GPT-4 AI extracted {filled_count} fields")
        logger.info(f"[CompleteProfileBuilder] AI Summary: {extracted_data.get('ai_business_summary', 'No summary')}")
        logger.info(f"[CompleteProfileBuilder] AI Capability: {extracted_data.get('ai_capability_description', 'No description')}")
        
        # Ensure backward compatibility with existing code that expects certain fields
        if not extracted_data.get("services") and extracted_data.get("specialties"):
            extracted_data["services"] = extracted_data["specialties"]
        
        if not extracted_data.get("contractor_size") and extracted_data.get("contractor_size_category"):
            extracted_data["contractor_size"] = extracted_data["contractor_size_category"]
            
        return extracted_data
    
    def _extract_services_from_content(self, content: str) -> list:
        """Extract services from website content"""
        content_lower = content.lower()
        
        services = []
        service_keywords = [
            "plumbing repair", "drain cleaning", "water heater", "toilet repair",
            "electrical repair", "wiring", "panel upgrade", "outlet installation",
            "hvac", "air conditioning", "heating", "furnace",
            "roofing", "roof repair", "roof replacement", "gutters",
            "painting", "interior painting", "exterior painting",
            "landscaping", "lawn care", "tree service",
            "carpentry", "flooring", "kitchen remodel", "bathroom remodel",
            "emergency service", "24/7", "licensed", "insured"
        ]
        
        for keyword in service_keywords:
            if keyword in content_lower:
                services.append(keyword)
        
        return services[:10]  # Limit to top 10
    
    def _extract_years_in_business(self, content: str) -> Optional[int]:
        """Extract years in business from content"""
        import re
        current_year = 2025
        
        patterns = [
            r"since\s+(\d{4})", r"established\s+(\d{4})", r"founded\s+(\d{4})",
            r"(\d+)\s+years?\s+(?:of\s+)?experience", r"over\s+(\d+)\s+years?"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                try:
                    value = int(matches[0])
                    if pattern.startswith(r"(\d{4})") or "since" in pattern or "established" in pattern or "founded" in pattern:
                        if 1950 <= value <= current_year:
                            return current_year - value
                    else:
                        if 1 <= value <= 100:
                            return value
                except ValueError:
                    continue
        return None
    
    def _extract_employee_count(self, content: str) -> Optional[int]:
        """Extract employee count from content"""
        import re
        
        patterns = [
            r"(\d+)\s+employees?", r"team\s+of\s+(\d+)", r"(\d+)\s+technicians?",
            r"staff\s+of\s+(\d+)", r"(\d+)\s+professionals?"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                try:
                    count = int(matches[0])
                    if 1 <= count <= 1000:
                        return count
                except ValueError:
                    continue
        return None
    
    def _extract_certifications(self, content: str) -> list:
        """Extract certifications from content"""
        content_lower = content.lower()
        certifications = []
        
        cert_keywords = [
            "licensed", "insured", "bonded", "certified", "accredited",
            "epa certified", "osha", "nate", "acca", "bbb accredited",
            "master plumber", "journeyman", "contractor license"
        ]
        
        for cert in cert_keywords:
            if cert in content_lower:
                certifications.append(cert)
        
        return certifications[:5]
    
    def _extract_service_areas(self, content: str) -> list:
        """Extract service areas from content"""
        import re
        areas = []
        
        patterns = [
            r"serving\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"service\s+area[s]?\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"we\s+serve\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match) > 3 and match not in areas:
                    areas.append(match)
        
        return areas[:8]
    
    def _find_contact_form(self, pages: list) -> str:
        """Find contact form URL from pages"""
        for page in pages:
            url = page.get("url", "")
            if "contact" in url.lower() or "quote" in url.lower():
                return url
        return ""
    
    def _extract_phone_number(self, content: str) -> str:
        """Extract phone number from content"""
        import re
        patterns = [
            r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
            r"\d{3}[-.\s]?\d{3}[-.\s]?\d{4}"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            if matches:
                return matches[0]
        return ""
    
    def _extract_email(self, content: str) -> str:
        """Extract email from content"""
        import re
        pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        matches = re.findall(pattern, content)
        return matches[0] if matches else ""
    
    def _determine_contractor_size(self, content: str) -> str:
        """Determine contractor size from content"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["corporation", "inc", "llc", "enterprise", "company"]):
            if any(word in content_lower for word in ["large", "major", "leading", "premier"]):
                return "large"
            return "medium"
        elif any(word in content_lower for word in ["owner", "family", "personal"]):
            return "small"
        else:
            return "small"  # Default
    
    def _generate_business_summary(self, company_name: str, content: str) -> str:
        """Generate AI business summary from website content"""
        
        # Extract key business information
        content_preview = content[:800]  # First 800 chars
        
        # Simple rule-based summary generation
        if "plumbing" in content.lower():
            service_type = "plumbing"
        elif "electrical" in content.lower():
            service_type = "electrical"
        elif "hvac" in content.lower():
            service_type = "HVAC"
        elif "roofing" in content.lower():
            service_type = "roofing"
        else:
            service_type = "home improvement"
        
        # Check for key business attributes
        attributes = []
        if "licensed" in content.lower():
            attributes.append("licensed")
        if "insured" in content.lower():
            attributes.append("insured")
        if "emergency" in content.lower() or "24/7" in content.lower():
            attributes.append("emergency services")
        if "residential" in content.lower():
            attributes.append("residential")
        if "commercial" in content.lower():
            attributes.append("commercial")
        
        # Generate summary
        attr_text = f" offering {', '.join(attributes)}" if attributes else ""
        summary = f"{company_name} is a professional {service_type} contractor{attr_text}. "
        
        if "experience" in content.lower() or "years" in content.lower():
            summary += "The company brings extensive experience to every project. "
        
        if "quality" in content.lower() or "professional" in content.lower():
            summary += "They are committed to providing high-quality professional services to their customers."
        
        return summary[:500]  # Limit to 500 chars
    
    def _generate_capability_description(self, company_name: str, content: str) -> str:
        """Generate AI capability description from website content"""
        
        # Extract services mentioned
        services = self._extract_services_from_content(content)
        
        if not services:
            return f"{company_name} provides comprehensive contractor services."
        
        # Group services by category
        service_text = ""
        if any("repair" in s for s in services):
            service_text += "repair services, "
        if any("installation" in s or "install" in s for s in services):
            service_text += "installation work, "
        if any("maintenance" in s for s in services):
            service_text += "maintenance, "
        if any("emergency" in s or "24/7" in s for s in services):
            service_text += "emergency response, "
        
        service_text = service_text.rstrip(", ")
        
        capability_desc = f"{company_name} specializes in {service_text}. "
        
        # Add capability indicators
        if "licensed" in content.lower():
            capability_desc += "All work is performed by licensed professionals. "
        if "warranty" in content.lower() or "guarantee" in content.lower():
            capability_desc += "They stand behind their work with warranties and guarantees."
        
        return capability_desc[:500]  # Limit to 500 chars