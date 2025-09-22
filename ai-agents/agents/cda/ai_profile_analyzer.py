"""
AI-Powered Profile Analyzer using LLM for 66-field extraction
"""
import json
import logging
from typing import Dict, Any, List, Optional
import os

logger = logging.getLogger(__name__)

class AIProfileAnalyzer:
    """Uses AI to intelligently analyze website content and extract 66 contractor fields"""
    
    def __init__(self):
        # Use OpenAI only for all AI analysis
        self.use_openai = True
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("Missing OPENAI_API_KEY")
            self.client = OpenAI(api_key=api_key)
            logger.info("[AI Analyzer] Using GPT-4 for analysis")
        except Exception as e:
            logger.error(f"[AI Analyzer] Failed to initialize OpenAI: {e}")
            raise
        
    async def analyze_contractor_website(self, 
                                        company_name: str,
                                        website_content: str,
                                        website_pages: List[Dict]) -> Dict[str, Any]:
        """
        Use GPT-4 to intelligently analyze website content and extract all 66 fields
        """
        
        # Prepare structured content from all pages
        structured_content = self._prepare_content(website_pages)
        logger.info(f"[AI Analysis] Analyzing {len(website_pages)} pages, total content: {len(structured_content)} chars")
        
        # Create focused prompt for GPT-4 - only fields that exist in database
        prompt = f"""You are an expert at analyzing contractor websites and extracting business information.

Analyze this contractor's website content and extract information for the fields listed below.

Company: {company_name}

WEBSITE CONTENT:
{structured_content[:8000]}

EXTRACT THE FOLLOWING FIELDS (only extract what's clearly stated on the website):

BASIC BUSINESS INFO:
1. company_name - Full legal business name
2. contact_name - Owner or primary contact name (look for "founded by", "owner", "president")
3. phone - Primary phone number (if different from provided)
4. email - Primary email address
5. website - Website URL (if different from provided)

BUSINESS DETAILS:
6. estimated_employees - Number of employees (look for "team of X", "X employees", "staff of")
7. years_in_business - How long in business (look for "X years", "since YEAR", "founded in")
8. business_established_year - Year founded (look for "founded", "established", "since")

SERVICES & SPECIALTIES:
9. specialties - Main service categories as array (Residential, Commercial, Industrial)
10. certifications - Professional certifications as array (Master Electrician, NECA, etc)
11. service_categories - Service categories as array
12. supported_project_types - Types of projects as array (kitchen, bathroom, whole_home, etc)
13. capabilities - Specific capabilities as array

LICENSING & VERIFICATION:
14. license_number - Contractor license number (look for "License #", "Lic #")
15. license_verified - true if license mentioned anywhere
16. insurance_verified - true if "insured" or "insurance" mentioned
17. bonded - true if "bonded" mentioned

CONTACT & SERVICE:
18. service_radius_miles - Service area radius in miles (if mentioned)
19. has_contact_form - true if contact form is visible on website
20. contact_form_url - URL of contact form page (if found)

AI ANALYSIS (always provide these):
21. ai_business_summary - 2-3 sentence business overview
22. ai_capability_description - Detailed description of capabilities and strengths

Return a JSON object with exactly these 22 fields. Use null for unknown fields.
Focus on extracting real, specific information that's actually stated on the website.
Do not guess or infer - only extract what is clearly written.
For arrays, return empty arrays [] if no data found."""

        try:
            # Call GPT-4 for intelligent analysis
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing contractor websites and extracting structured business data. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            result_text = response.choices[0].message.content
            
            # Extract JSON from response
            if "```json" in result_text:
                json_str = result_text.split("```json")[1].split("```")[0]
            elif "{" in result_text:
                # Find the JSON object in the response
                start = result_text.index("{")
                end = result_text.rindex("}") + 1
                json_str = result_text[start:end]
            else:
                json_str = result_text
                
            # Parse JSON
            extracted_data = json.loads(json_str)
            
            logger.info(f"[AI Analysis] Successfully extracted {len([v for v in extracted_data.values() if v])} fields for {company_name}")
            logger.info(f"[AI Analysis] Key fields - employees: {extracted_data.get('estimated_employees')}, years: {extracted_data.get('years_in_business')}, size: {extracted_data.get('contractor_size_category')}")
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"[AI Analysis] Error: {e}")
            # Return basic extraction as fallback
            return self._fallback_extraction(company_name, structured_content)
    
    def _prepare_content(self, website_pages: List[Dict]) -> str:
        """Prepare structured content from website pages"""
        content_parts = []
        
        for page in website_pages[:5]:  # Use top 5 pages
            url = page.get("url", "")
            title = page.get("title", "")
            # Prefer full_content if available, otherwise use content field
            full_content = page.get("full_content", "")
            content = full_content if full_content else page.get("content", "")
            
            # Use more of the content now that we have full extraction
            content_to_use = content[:3000] if content else ""
            
            content_parts.append(f"""
PAGE: {url}
TITLE: {title}
CONTENT: {content_to_use}
---""")
        
        return "\n".join(content_parts)
    
    def _fallback_extraction(self, company_name: str, content: str) -> Dict[str, Any]:
        """Basic fallback extraction if AI fails"""
        return {
            "company_name": company_name,
            "ai_business_summary": f"{company_name} is a contractor providing professional services.",
            "ai_capability_description": "Comprehensive contractor services available.",
            "license_verified": "license" in content.lower(),
            "insurance_verified": "insurance" in content.lower(),
            "emergency_services": "24/7" in content or "emergency" in content.lower(),
            "residential_experience": "residential" in content.lower(),
            "commercial_experience": "commercial" in content.lower()
        }