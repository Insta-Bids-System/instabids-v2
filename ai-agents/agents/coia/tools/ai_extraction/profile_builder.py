"""
Profile Builder Tool for COIA
Builds comprehensive contractor profiles from multiple data sources
"""

import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime

from ..base import BaseTool

logger = logging.getLogger(__name__)


class ProfileBuilderTool(BaseTool):
    """Build comprehensive contractor profiles from all data sources"""
    
    async def build_contractor_profile(self, company_name: str,
                                      google_data: Optional[Dict[str, Any]] = None,
                                      web_data: Optional[Dict[str, Any]] = None,
                                      license_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Build comprehensive contractor profile from ALL data sources to fill 66 contractor fields
        """
        logger.info(f"Building comprehensive contractor profile for {company_name}")
        
        # STEP 1: Check if contractor already exists
        from ..database.contractors import ContractorDatabaseTool
        db_tool = ContractorDatabaseTool()
        existing_contractor = await db_tool.check_existing_contractor(company_name)
        
        if existing_contractor:
            logger.info(f"Found existing contractor: {company_name}")
            existing_record = existing_contractor
            
            # Return existing profile with indication it already exists
            existing_record.update({
                "already_exists": True,
                "existing_table": existing_contractor.get("table", "potential_contractors"),
                "is_full_contractor": existing_contractor.get("is_full_contractor", False),
                "database_saved": True,
                "contractor_lead_id": existing_record.get("id")
            })
            return existing_record
        
        # Initialize profile with ALL 66 contractor fields
        profile = {
            # Core business info
            "business_name": company_name,
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
                "google_business_status": google_data.get("google_business_status", ""),
                "google_types": google_data.get("google_types", []),
                "verified_business": True
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
            elif extracted.get("email"):  # New direct format from _process_tavily_content
                profile["email"] = extracted["email"]
                
            if contact_methods.get("phones") and not profile["phone"]:
                profile["phone"] = contact_methods["phones"][0]  # Use first phone if no Google phone
            elif extracted.get("phone") and not profile["phone"]:  # New direct format
                profile["phone"] = extracted["phone"]
                
            # Business description
            if extracted.get("business_description"):
                profile["raw_data"]["business_description"] = extracted["business_description"]
            
            profile["completeness_score"] += 30
            profile["profile_insights"].append("Website comprehensively scraped")
            filled_fields += 15
        
        # Integrate social media data
        if web_data and web_data.get("social_media_data"):
            social_data = web_data["social_media_data"]
            profile["data_sources"].append("social_media")
            
            profile.update({
                "social_media_followers": social_data.get("total_followers", 0),
                "digital_presence_score": social_data.get("digital_presence_score", 0)
            })
            
            if social_data.get("recent_posts"):
                profile["enrichment_data"]["recent_social_posts"] = social_data["recent_posts"]
                
            profile["completeness_score"] += 10
            profile["profile_insights"].append("Social media profiles analyzed")
            filled_fields += 3
        
        # Integrate license data
        if license_data and license_data.get("licenses"):
            profile["data_sources"].append("license_database")
            
            licenses = license_data["licenses"]
            if licenses:
                first_license = licenses[0]
                profile.update({
                    "license_number": first_license.get("number", ""),
                    "license_state": first_license.get("state", ""),
                    "license_verified": True
                })
                
                profile["completeness_score"] += 15
                profile["profile_insights"].append("Professional licenses verified")
                filled_fields += 3
        
        # Calculate business intelligence scores
        if web_data and web_data.get("business_intelligence"):
            business_intel = web_data["business_intelligence"]
            
            profile.update({
                "lead_score": business_intel.get("lead_score", 0),
                "data_completeness": business_intel.get("data_completeness", 0)
            })
            
            if business_intel.get("credibility_indicators"):
                profile["enrichment_data"]["credibility_indicators"] = business_intel["credibility_indicators"]
                
            filled_fields += 2
        
        # Final calculations
        profile["data_completeness"] = min(100, (filled_fields / total_fields) * 100)
        profile["lead_score"] = profile["data_completeness"] * 0.8  # Base score on completeness
        
        # Add bonus scores for high-value data
        if profile["verified_business"]:
            profile["lead_score"] += 10
        if profile["has_contact_form"]:
            profile["lead_score"] += 5
        if profile["years_in_business"] and profile["years_in_business"] > 5:
            profile["lead_score"] += 5
        if profile.get("rating") and profile["rating"] > 4.0:
            profile["lead_score"] += 10
            
        profile["lead_score"] = min(100, profile["lead_score"])
        
        # Store all raw data for future reference
        profile["raw_data"].update({
            "google_data": google_data,
            "web_data": web_data,
            "license_data": license_data
        })
        
        # Add base score for having a name
        if not profile["completeness_score"]:
            profile["completeness_score"] = 20
        
        # Save to database if enabled
        save_to_db = self._should_save_to_database()
        if save_to_db:
            saved_result = await db_tool.save_potential_contractor(profile)
            if saved_result and not saved_result.get("error"):
                profile["database_saved"] = True
                profile["contractor_lead_id"] = saved_result.get("contractor_lead_id")
                logger.info(f"✅ Saved contractor profile to database: {profile['contractor_lead_id']}")
            else:
                profile["database_saved"] = False
                logger.warning(f"Could not save profile to database: {saved_result.get('error')}")
        
        logger.info(f"Built contractor profile with {profile['completeness_score']}% completeness")
        return profile
    
    def _should_save_to_database(self) -> bool:
        """Check if we should save to database based on environment setting"""
        import os
        return os.getenv("WRITE_LEADS_ON_RESEARCH", "false").lower() == "true"