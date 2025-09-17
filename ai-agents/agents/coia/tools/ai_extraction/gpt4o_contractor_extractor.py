"""
GPT-4o Contractor Profile Extractor
==================================
The MISSING PIECE: Intelligently extracts all 66 contractor fields from raw research data.
Takes 170KB+ of research data and uses GPT-4o to fill comprehensive contractor profiles.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import os
from openai import AsyncOpenAI

# Import LangFuse for observability (safe import)
try:
    from langfuse import get_client
    langfuse = get_client()
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False

logger = logging.getLogger(__name__)

class GPT4oContractorExtractor:
    """
    The missing GPT-4o extraction tool that processes raw research data
    and intelligently extracts all 66 contractor profile fields
    """
    
    def __init__(self):
        """Initialize OpenAI client"""
        # Use environment variable for API key
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        
        self.client = AsyncOpenAI(api_key=api_key)
        logger.info(f"GPT-4o Contractor Extractor initialized with working API key")
    
    async def _get_all_contractor_types_mapping(self) -> str:
        """
        DYNAMIC: Query database for ALL contractor types and build GPT-4o mapping string
        Replaces hardcoded 15 types with complete 219 types from database
        """
        try:
            # Import database client
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            from database_simple import get_client
            
            supabase = get_client()
            
            # Query ALL contractor types from database
            result = supabase.table("contractor_types").select("id, name").order("id").execute()
            
            if result.data:
                # Build mapping string: "Service Name=ID, Service Name=ID, ..."
                mappings = []
                for contractor_type in result.data:
                    name = contractor_type.get('name', '').strip()
                    type_id = contractor_type.get('id')
                    if name and type_id:
                        mappings.append(f"{name}={type_id}")
                
                mapping_string = ", ".join(mappings)
                logger.info(f"Built contractor types mapping with {len(mappings)} types from database")
                return mapping_string
            else:
                logger.warning("No contractor types found in database - using fallback")
                # Fallback to hardcoded list if database query fails
                return "Artificial Turf Installer=225, Landscaping=31, General Contracting=48, Handyman=127, Landscape Designer=128, Landscaper=221, Lawn Care Provider=222, Plumbing=33, Electrical=34, HVAC=35, Roofing=36, Flooring=37, Pool & Spa=32, Concrete=39, Fencing=40"
                
        except Exception as e:
            logger.error(f"Failed to query contractor types: {e}")
            # Fallback to hardcoded list if database query fails
            return "Artificial Turf Installer=225, Landscaping=31, General Contracting=48, Handyman=127, Landscape Designer=128, Landscaper=221, Lawn Care Provider=222, Plumbing=33, Electrical=34, HVAC=35, Roofing=36, Flooring=37, Pool & Spa=32, Concrete=39, Fencing=40"
    
    async def extract_contractor_profile(self, 
                                       company_name: str,
                                       google_data: Dict[str, Any],
                                       web_data: Dict[str, Any],
                                       license_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main extraction function: Takes 170KB+ of research data and extracts all 66 fields
        
        Args:
            company_name: Business name
            google_data: Google Places API data
            web_data: Tavily web research data (contains bulk content)
            license_data: License verification data
            
        Returns:
            Dict with all 66 contractor fields intelligently extracted
        """
        # Wrap entire GPT-4o extraction with LangFuse generation span
        if LANGFUSE_AVAILABLE:
            try:
                with langfuse.start_as_current_observation(
                    name="coia-gpt4o-contractor-extraction",
                    as_type="generation",
                    model="gpt-4o",
                    input={
                        "company_name": company_name,
                        "data_sources": ["google_places", "tavily_web", "license_data"] if license_data else ["google_places", "tavily_web"],
                        "extraction_task": "66_field_contractor_profile"
                    }
                ) as gen:
                    result = await self._extract_contractor_profile_impl(company_name, google_data, web_data, license_data)
                    gen.update(output={
                        "extraction_success": "error" not in result,
                        "fields_extracted": len([k for k, v in result.items() if v and v not in ['', [], {}, None, 'unknown', 'not_found']]),
                        "data_size_processed": result.get("data_size_processed"),
                        "prompt_tokens": result.get("prompt_tokens"),
                        "completion_tokens": result.get("completion_tokens")
                    })
                    return result
            except Exception as e:
                logger.warning(f"LangFuse GPT-4o extraction span failed: {e}")
                return await self._extract_contractor_profile_impl(company_name, google_data, web_data, license_data)
        else:
            return await self._extract_contractor_profile_impl(company_name, google_data, web_data, license_data)
    
    async def _extract_contractor_profile_impl(self, 
                                             company_name: str,
                                             google_data: Dict[str, Any],
                                             web_data: Dict[str, Any],
                                             license_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Implementation of GPT-4o extraction - extracted for LangFuse wrapping"""
        try:
            logger.info(f"Starting GPT-4o extraction for {company_name}")
            
            # Calculate input size
            total_data_size = len(json.dumps({
                'google_data': google_data,
                'web_data': web_data,
                'license_data': license_data or {}
            }, default=str))
            
            logger.info(f"Processing {total_data_size:,} characters of research data")
            
            # Build extraction prompt with dynamic contractor types
            extraction_prompt = await self._build_extraction_prompt(company_name, google_data, web_data, license_data)
            
            # Call GPT-4o
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": extraction_prompt
                    }
                ],
                max_tokens=4000,  # Enough for detailed 66-field response
                temperature=0.1,  # Low for factual extraction
                response_format={"type": "json_object"}  # Ensure JSON output
            )
            
            # Parse response
            extracted_json = response.choices[0].message.content
            extracted_profile = json.loads(extracted_json)
            
            # Add extraction metadata
            extracted_profile.update({
                "extraction_method": "gpt-4o-intelligent",
                "data_size_processed": total_data_size,
                "extraction_timestamp": datetime.utcnow().isoformat(),
                "gpt4o_model_used": "gpt-4o",
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens
            })
            
            # Count filled fields
            filled_fields = sum(1 for v in extracted_profile.values() 
                              if v and v not in ['', [], {}, None, 'unknown', 'not_found'])
            
            logger.info(f"GPT-4o extracted {filled_fields}/66 fields for {company_name}")
            
            return extracted_profile
            
        except json.JSONDecodeError as e:
            logger.error(f"GPT-4o returned invalid JSON: {e}")
            return {"error": "gpt4o_json_parse_error", "company_name": company_name}
        except Exception as e:
            logger.error(f"GPT-4o extraction error: {e}")
            return {"error": str(e), "company_name": company_name}
    
    def _get_system_prompt(self) -> str:
        """System prompt that defines GPT-4o's role as contractor profile extractor"""
        return """You are an expert contractor business analyst with 20+ years of experience. 
Your job is to analyze comprehensive research data about a contractor business and extract a complete, accurate profile.

CRITICAL REQUIREMENTS:
1. Extract only factual information directly supported by the data
2. For missing string/text fields: use 'unknown' 
3. For missing boolean fields: use false (not 'unknown')
4. For missing numeric fields: use null (not 'unknown')
5. For missing array fields: use [] (empty array)
6. Return a valid JSON object with all 68 required fields
7. Be intelligent about inference (e.g., "serving South Florida for 15 years" = years_in_business: 15)
8. Extract services/specialties from context, not just explicit lists
9. Parse contact information carefully from various formats

EMAIL EXTRACTION PRIORITY:
- Search contact pages, about pages, and footer content for email addresses
- Look for patterns like: info@company.com, contact@company.com, owner@company.com
- Extract from "Contact Us", "Get In Touch", "About" sections
- Check for mailto: links and email formats in text

CONTRACTOR TYPE IDS PRIORITY:
- Match services to the contractor types mapping provided
- Use multiple IDs if business offers multiple services
- Be specific (use "Landscaping=31" not "General Contracting=48" for lawn care)
- Include all relevant service categories found

ADDRESS & ZIP CODE EXTRACTION:
- Parse complete addresses into separate fields: address, city, state, zip_code
- Extract ZIP codes from full addresses (e.g., "123 Main St, Miami, FL 33101" → zip_code: "33101")
- Use Google Places data for accurate address parsing

COMPANY SIZE CLASSIFICATION:
- solo_handyman: 1 person operation, residential focus
- owner_operator: 2-5 employees, owner works on jobs
- small_business: 5-20 employees, established local presence
- regional_company: 20+ employees, multi-city operations
- national_chain: Corporate structure, multiple locations

RESPONSE FORMAT: Return ONLY a valid JSON object with no additional text."""
    
    async def _build_extraction_prompt(self, 
                                       company_name: str,
                                       google_data: Dict[str, Any],
                                       web_data: Dict[str, Any],
                                       license_data: Optional[Dict[str, Any]]) -> str:
        """Build the comprehensive extraction prompt with all research data"""
        
        # Get dynamic contractor types mapping from database
        contractor_types_mapping = await self._get_all_contractor_types_mapping()
        
        # Start with the core prompt
        prompt = f"""CONTRACTOR PROFILE EXTRACTION REQUEST
Company: {company_name}

Extract a comprehensive 66-field contractor profile from the following research data:

=== GOOGLE BUSINESS PROFILE DATA ===
{json.dumps(google_data, indent=2, default=str)}

=== WEB RESEARCH DATA ===
{json.dumps(web_data, indent=2, default=str)}
"""
        
        if license_data:
            prompt += f"""
=== LICENSE/REGULATORY DATA ===
{json.dumps(license_data, indent=2, default=str)}
"""
        
        # Add the complete field specification with dynamic contractor types
        prompt += f"""
EXTRACT THE FOLLOWING 68 FIELDS AS JSON:

{{
  // BASIC BUSINESS INFORMATION (10 fields)
  "company_name": "exact business name",
  "contact_name": "primary contact person", 
  "phone": "primary phone number",
  "email": "primary email address",
  "website": "primary website URL",
  "address": "complete physical address",
  "city": "city location",
  "state": "state abbreviation",
  "zip_code": "postal code",
  "country": "country (default: USA)",
  
  // BUSINESS DETAILS (11 fields)
  "business_type": "type of contractor business",
  "entity_type": "LLC, Corp, Partnership, etc.",
  "contractor_size": "business size category based on employees and operations: solo_handyman, owner_operator, small_business, regional_company, or national_chain",
  "years_in_business": "number as integer",
  "year_established": "founding year as integer",
  "employee_count": "number of employees as integer",
  "annual_revenue": "estimated revenue as integer",
  "business_hours": "operating hours description",
  "emergency_available": "offers emergency services (boolean)",
  "accepts_credit_cards": "accepts credit card payments (boolean)",
  "financing_available": "offers financing options (boolean)",
  
  // LICENSING & INSURANCE (8 fields)
  "license_number": "professional license number",
  "license_state": "state where licensed",
  "license_expiry": "license expiration date",
  "license_verified": "license verification status (boolean)",
  "insurance_carrier": "insurance company name",
  "insurance_amount": "coverage amount",
  "insurance_expiry": "insurance expiration date", 
  "insurance_verified": "insurance verification status (boolean)",
  
  // CERTIFICATIONS & AFFILIATIONS (6 fields)
  "certifications": ["list of professional certifications"],
  "professional_affiliations": ["industry associations"],
  "awards_recognition": ["awards and recognitions received"],
  "bbb_rating": "Better Business Bureau rating",
  "bbb_accredited": "BBB accredited status (boolean)",
  "chamber_member": "Chamber of Commerce member (boolean)",
  
  // SERVICES & SPECIALTIES (9 fields)
  "primary_services": ["main services offered - be specific"],
  "secondary_services": ["additional services"],
  "specializations": ["specialized areas of expertise"],
  "contractor_type_ids": ["numeric IDs matching contractor types from services: {contractor_types_mapping}"],
  "brands_carried": ["brands/manufacturers represented"],
  "service_areas": ["geographic areas served"],
  "service_radius": "service radius in miles (integer)",
  "project_minimum": "minimum project value as integer",
  "typical_project_duration": "average project timeline",
  
  // ONLINE PRESENCE (8 fields)
  "google_rating": "Google rating as float (e.g., 4.9)",
  "google_reviews": "number of Google reviews as integer",
  "yelp_rating": "Yelp rating as float",
  "yelp_reviews": "number of Yelp reviews as integer",
  "facebook_url": "Facebook page URL",
  "instagram_url": "Instagram profile URL",
  "linkedin_url": "LinkedIn profile URL",
  "youtube_url": "YouTube channel URL",
  
  // INTELLIGENT ANALYSIS FIELDS (10 fields - USE YOUR EXPERTISE)
  "business_summary": "2-3 sentence professional summary of the business",
  "unique_selling_points": ["what makes this contractor unique"],
  "competitive_advantages": ["their competitive strengths"],
  "target_market": ["types of customers they serve"],
  "business_philosophy": "their approach to business and customers",
  "company_culture": "workplace culture and values",
  "recent_projects": ["examples of recent work or projects"],
  "client_testimonials": ["customer testimonials or reviews"],
  "growth_trajectory": "business growth status and plans",
  "market_position": "position in local market (established/growing/new)",
  
  // OPERATIONAL DETAILS (6 fields)
  "response_time": "typical response time for inquiries",
  "quote_process": "how they handle estimates and quotes",
  "warranty_offered": "warranty/guarantee information",
  "satisfaction_guarantee": "customer satisfaction policies",
  "preferred_contact_method": "preferred way to be contacted",
  "best_time_to_contact": "optimal contact times"
}}

CRITICAL: Return ONLY the JSON object. 
- String fields without data: use 'unknown'
- Boolean fields without data: use false  
- Numeric fields without data: use null
- Array fields without data: use []
"""
        
        return prompt
    
    async def test_extraction(self) -> bool:
        """Test if GPT-4o extraction is working with sample data"""
        try:
            test_data = {
                "company_name": "Test Contractor LLC",
                "address": "123 Main St, Miami, FL 33101",
                "phone": "(305) 555-0100",
                "website": "https://testcontractor.com"
            }
            
            result = await self.extract_contractor_profile(
                "Test Contractor LLC",
                test_data,
                {"business_description": "Full-service contractor specializing in residential work"},
                None
            )
            
            return "error" not in result and len(result) > 20
            
        except Exception as e:
            logger.error(f"GPT-4o test failed: {e}")
            return False


# Async wrapper function for subagent compatibility
async def extract_profile_with_gpt4o(company_name: str, 
                                    google_data: Dict[str, Any],
                                    web_data: Dict[str, Any],
                                    license_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Async wrapper function that subagents can call directly
    """
    try:
        extractor = GPT4oContractorExtractor()
        return await extractor.extract_contractor_profile(company_name, google_data, web_data, license_data)
    except Exception as e:
        logger.error(f"GPT-4o extraction wrapper error: {e}")
        return {
            "error": str(e),
            "company_name": company_name,
            "extraction_method": "gpt-4o-failed"
        }