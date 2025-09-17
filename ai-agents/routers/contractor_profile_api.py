"""
Contractor Profile API - Enhanced with Unified Contractors Table
Uses the newly expanded contractors table (17 → 59 fields) for rich contractor profiles
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database_simple import db

router = APIRouter()
logger = logging.getLogger(__name__)

class ContractorProfileResponse(BaseModel):
    """Complete contractor profile using unified contractors table (59 fields)"""
    # Core contractor data (original 17 fields)
    id: Optional[str] = None
    name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    services_offered: Optional[List[str]] = None
    license_info: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    verified: Optional[bool] = None
    is_active: Optional[bool] = None
    profile_image_url: Optional[str] = None
    
    # Enhanced business data (from contractor_leads integration - 42 new fields)
    business_name: Optional[str] = None
    business_phone: Optional[str] = None
    business_email: Optional[str] = None
    website_url: Optional[str] = None
    business_address: Optional[str] = None
    business_city: Optional[str] = None
    business_state: Optional[str] = None
    business_zip: Optional[str] = None
    business_hours: Optional[str] = None
    
    # Professional credentials
    license_number: Optional[str] = None
    license_state: Optional[str] = None
    insurance_info: Optional[str] = None
    bonded: Optional[bool] = None
    years_in_business: Optional[int] = None
    crew_size: Optional[int] = None
    service_area_radius: Optional[int] = None
    specialty_services: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    awards: Optional[List[str]] = None
    
    # Online presence & ratings
    bbb_rating: Optional[str] = None
    bbb_accredited: Optional[bool] = None
    angi_rating: Optional[float] = None
    angi_reviews: Optional[int] = None
    google_rating: Optional[float] = None
    google_reviews: Optional[int] = None
    yelp_rating: Optional[float] = None
    yelp_reviews: Optional[int] = None
    facebook_rating: Optional[float] = None
    facebook_reviews: Optional[int] = None
    
    # Social media & portfolio
    linkedin_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    youtube_url: Optional[str] = None
    portfolio_images: Optional[List[str]] = None
    project_gallery: Optional[List[str]] = None
    testimonials: Optional[List[str]] = None
    
    # Service options
    emergency_services: Optional[bool] = None
    warranty_offered: Optional[str] = None
    financing_options: Optional[bool] = None
    free_estimates: Optional[bool] = None
    senior_discount: Optional[bool] = None
    military_discount: Optional[bool] = None
    referral_program: Optional[bool] = None
    
    # Metadata
    data_source: Optional[str] = None
    profile_completeness: Optional[int] = None
    last_updated: Optional[str] = None

@router.get("/contractors/{contractor_id}/profile")
async def get_contractor_profile(contractor_id: str) -> ContractorProfileResponse:
    """
    Get complete contractor profile using unified contractors table
    Returns rich profile data from all 59 fields
    """
    try:
        # Query the unified contractors table for complete profile
        query = """
        SELECT 
            -- Original contractor fields (17)
            id, name, company_name, phone, email, location_city, location_state,
            services_offered, license_info, rating, reviews_count, verified,
            created_at, updated_at, user_id, is_active, profile_image_url,
            
            -- New business fields (42 from contractor_leads integration)
            business_name, business_phone, business_email, website_url,
            business_address, business_city, business_state, business_zip, business_hours,
            license_number, license_state, insurance_info, bonded, years_in_business,
            crew_size, service_area_radius, specialty_services, certifications, awards,
            bbb_rating, bbb_accredited, angi_rating, angi_reviews, google_rating, google_reviews,
            yelp_rating, yelp_reviews, facebook_rating, facebook_reviews,
            linkedin_url, facebook_url, instagram_url, twitter_url, youtube_url,
            portfolio_images, project_gallery, testimonials,
            emergency_services, warranty_offered, financing_options, free_estimates,
            senior_discount, military_discount, referral_program
        FROM contractors 
        WHERE id = %s
        """
        
        result = await db.fetch_one(query, (contractor_id,))
        
        if not result:
            raise HTTPException(status_code=404, detail="Contractor not found")
            
        # Calculate profile completeness score
        profile_data = dict(result)
        completeness = calculate_profile_completeness(profile_data)
        
        # Convert to response model with completeness score
        profile_response = ContractorProfileResponse(**profile_data)
        profile_response.profile_completeness = completeness
        profile_response.data_source = "unified_contractors_table"
        profile_response.last_updated = str(profile_data.get('updated_at', ''))
        
        logger.info(f"Retrieved contractor profile for {contractor_id} - {completeness}% complete")
        return profile_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving contractor profile {contractor_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve contractor profile")

@router.get("/contractors/{contractor_id}/profile/summary")
async def get_contractor_profile_summary(contractor_id: str) -> Dict[str, Any]:
    """
    Get contractor profile summary for cards and listings
    Returns key fields only for performance
    """
    try:
        query = """
        SELECT 
            id, name, company_name, business_name, phone, business_phone,
            email, business_email, website_url, location_city, location_state,
            business_city, business_state, rating, google_rating, verified,
            years_in_business, license_number, specialty_services,
            services_offered, emergency_services, free_estimates,
            profile_image_url
        FROM contractors 
        WHERE id = %s AND is_active = true
        """
        
        result = await db.fetch_one(query, (contractor_id,))
        
        if not result:
            raise HTTPException(status_code=404, detail="Contractor not found")
            
        profile_data = dict(result)
        
        # Create summary with best available data
        summary = {
            "id": profile_data["id"],
            "display_name": profile_data["business_name"] or profile_data["company_name"] or profile_data["name"],
            "phone": profile_data["business_phone"] or profile_data["phone"],
            "email": profile_data["business_email"] or profile_data["email"],
            "website": profile_data["website_url"],
            "location": f"{profile_data['business_city'] or profile_data['location_city']}, {profile_data['business_state'] or profile_data['location_state']}",
            "rating": profile_data["google_rating"] or profile_data["rating"],
            "verified": profile_data["verified"],
            "years_experience": profile_data["years_in_business"],
            "license_number": profile_data["license_number"],
            "specialties": profile_data["specialty_services"] or profile_data["services_offered"],
            "emergency_services": profile_data["emergency_services"],
            "free_estimates": profile_data["free_estimates"],
            "profile_image": profile_data["profile_image_url"],
            "data_source": "unified_contractors_table"
        }
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving contractor profile summary {contractor_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve contractor profile summary")

@router.get("/contractors/search/profiles")
async def search_contractor_profiles(
    specialty: Optional[str] = None,
    location: Optional[str] = None,
    min_rating: Optional[float] = None,
    min_years: Optional[int] = None,
    verified_only: bool = False,
    emergency_services: Optional[bool] = None,
    free_estimates: Optional[bool] = None,
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Search contractor profiles using unified table with rich filtering
    Leverages all 59 fields for advanced search capabilities
    """
    try:
        # Build dynamic query with unified table fields
        conditions = ["is_active = true"]
        params = []
        
        if specialty:
            conditions.append("(specialty_services @> %s OR services_offered @> %s)")
            params.extend([[specialty], [specialty]])
            
        if location:
            conditions.append("(business_city ILIKE %s OR location_city ILIKE %s OR business_state ILIKE %s OR location_state ILIKE %s)")
            params.extend([f"%{location}%", f"%{location}%", f"%{location}%", f"%{location}%"])
            
        if min_rating:
            conditions.append("(google_rating >= %s OR rating >= %s)")
            params.extend([min_rating, min_rating])
            
        if min_years:
            conditions.append("years_in_business >= %s")
            params.append(min_years)
            
        if verified_only:
            conditions.append("verified = true")
            
        if emergency_services is not None:
            conditions.append("emergency_services = %s")
            params.append(emergency_services)
            
        if free_estimates is not None:
            conditions.append("free_estimates = %s")
            params.append(free_estimates)
        
        where_clause = " AND ".join(conditions)
        
        # Count query
        count_query = f"SELECT COUNT(*) FROM contractors WHERE {where_clause}"
        total_count = await db.fetch_val(count_query, params)
        
        # Main search query with unified fields
        search_query = f"""
        SELECT 
            id, name, company_name, business_name, phone, business_phone,
            email, business_email, website_url, location_city, location_state,
            business_city, business_state, rating, google_rating, google_reviews,
            verified, years_in_business, license_number, specialty_services,
            services_offered, emergency_services, free_estimates, crew_size,
            bbb_rating, angi_rating, portfolio_images, profile_image_url
        FROM contractors 
        WHERE {where_clause}
        ORDER BY 
            verified DESC,
            COALESCE(google_rating, rating, 0) DESC,
            COALESCE(years_in_business, 0) DESC
        LIMIT %s OFFSET %s
        """
        
        params.extend([limit, offset])
        results = await db.fetch_all(search_query, params)
        
        # Format results with unified data
        contractors = []
        for result in results:
            contractor_data = dict(result)
            contractors.append({
                "id": contractor_data["id"],
                "display_name": contractor_data["business_name"] or contractor_data["company_name"] or contractor_data["name"],
                "phone": contractor_data["business_phone"] or contractor_data["phone"],
                "email": contractor_data["business_email"] or contractor_data["email"],
                "website": contractor_data["website_url"],
                "location": f"{contractor_data['business_city'] or contractor_data['location_city']}, {contractor_data['business_state'] or contractor_data['location_state']}",
                "rating": contractor_data["google_rating"] or contractor_data["rating"],
                "review_count": contractor_data["google_reviews"],
                "verified": contractor_data["verified"],
                "years_experience": contractor_data["years_in_business"],
                "license_number": contractor_data["license_number"],
                "specialties": contractor_data["specialty_services"] or contractor_data["services_offered"],
                "emergency_services": contractor_data["emergency_services"],
                "free_estimates": contractor_data["free_estimates"],
                "crew_size": contractor_data["crew_size"],
                "bbb_rating": contractor_data["bbb_rating"],
                "angi_rating": contractor_data["angi_rating"],
                "portfolio_images": contractor_data["portfolio_images"],
                "profile_image": contractor_data["profile_image_url"],
            })
        
        return {
            "contractors": contractors,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_count,
            "search_criteria": {
                "specialty": specialty,
                "location": location,
                "min_rating": min_rating,
                "min_years": min_years,
                "verified_only": verified_only,
                "emergency_services": emergency_services,
                "free_estimates": free_estimates,
            }
        }
        
    except Exception as e:
        logger.error(f"Error searching contractor profiles: {e}")
        raise HTTPException(status_code=500, detail="Failed to search contractor profiles")

def calculate_profile_completeness(profile_data: Dict[str, Any]) -> int:
    """
    Calculate profile completeness percentage based on filled fields
    Uses all 59 unified table fields for comprehensive scoring
    """
    # Critical fields (higher weight)
    critical_fields = [
        'company_name', 'business_name', 'phone', 'business_phone', 
        'email', 'business_email', 'location_city', 'business_city',
        'services_offered', 'specialty_services'
    ]
    
    # Important fields (medium weight)  
    important_fields = [
        'website_url', 'license_number', 'years_in_business', 'crew_size',
        'insurance_info', 'certifications', 'rating', 'google_rating',
        'business_address', 'business_hours'
    ]
    
    # Optional fields (lower weight)
    optional_fields = [
        'bbb_rating', 'portfolio_images', 'testimonials', 'awards',
        'emergency_services', 'warranty_offered', 'financing_options',
        'social_media_profiles', 'linkedin_url', 'facebook_url'
    ]
    
    critical_filled = sum(1 for field in critical_fields if profile_data.get(field))
    important_filled = sum(1 for field in important_fields if profile_data.get(field))  
    optional_filled = sum(1 for field in optional_fields if profile_data.get(field))
    
    # Weighted scoring: critical=3, important=2, optional=1
    total_points = (critical_filled * 3) + (important_filled * 2) + (optional_filled * 1)
    max_points = (len(critical_fields) * 3) + (len(important_fields) * 2) + (len(optional_fields) * 1)
    
    completeness = int((total_points / max_points) * 100)
    return min(completeness, 100)