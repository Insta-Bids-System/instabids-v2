"""
Complete Profile Builder Tool - Copied from COIA
Builds comprehensive 66-field contractor profiles from multiple data sources
"""

import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CompleteProfileBuilder:
    """Build comprehensive contractor profiles from all data sources - 66 fields total"""
    
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
            
            # Extract city/state from address
            address = google_data.get("address", "")
            if address:
                # Try to extract city and state from address
                match = re.search(r',\s*([^,]+),\s*([A-Z]{2})\s*\d{5}', address)
                if match:
                    profile["city"] = match.group(1).strip()
                    profile["state"] = match.group(2).strip()
            
            profile["completeness_score"] += 25
            profile["profile_insights"].append("Google Business Profile verified")
            filled_fields += 8
        
        # Integrate comprehensive web data
        if web_data and web_data.get("extracted_info"):
            profile["data_sources"].append("website_scraping")
            extracted = web_data["extracted_info"]
            
            # Map web data to profile fields
            profile.update({
                "specialties": extracted.get("services", []),
                "years_in_business": extracted.get("years_in_business"),
                "estimated_employees": extracted.get("employees"),
                "has_contact_form": bool(extracted.get("contact_form_url")),
                "contact_form_url": extracted.get("contact_form_url", ""),
                "certifications": extracted.get("certifications", []),
                "service_areas": extracted.get("service_areas", [])
            })
            
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
            profile["lead_status"] = "partially_qualified"
        else:
            profile["lead_status"] = "needs_enrichment"
        
        # Store raw data for future reference
        profile["raw_data"] = {
            "google": google_data,
            "web": web_data,
            "license": license_data
        }
        
        logger.info(f"Profile built for {company_name}: {profile['data_completeness']}% complete, Score: {profile['lead_score']}")
        
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