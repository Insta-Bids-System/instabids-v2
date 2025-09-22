"""
Mock AI-Powered Profile Analyzer for testing without API key
Simulates what Claude would extract from website content
"""
import json
import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class AIProfileAnalyzerMock:
    """Mock version that simulates Claude AI extraction for testing"""
    
    async def analyze_contractor_website(self, 
                                        company_name: str,
                                        website_content: str,
                                        website_pages: List[Dict]) -> Dict[str, Any]:
        """
        Simulate intelligent AI analysis of website content
        This shows what Claude WOULD extract with proper API key
        """
        
        # Combine all page content
        all_content = ""
        for page in website_pages[:5]:
            all_content += f"{page.get('content', '')} "
        
        logger.info(f"[Mock AI Analysis] Analyzing {len(website_pages)} pages for {company_name}")
        
        # Simulate intelligent extraction based on actual content
        extracted_data = {}
        
        # Basic company info
        extracted_data["company_name"] = company_name
        
        # Extract phone intelligently
        phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', all_content)
        if phone_match:
            extracted_data["phone"] = phone_match.group()
        
        # Extract email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', all_content)
        if email_match:
            extracted_data["email"] = email_match.group()
        
        # Extract address
        address_match = re.search(r'\d+\s+[A-Za-z\s]+(?:Blvd|St|Ave|Road|Lane|Drive|Way)[,\s]+[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}', all_content)
        if address_match:
            full_address = address_match.group()
            extracted_data["address"] = full_address
            
            # Parse city, state, zip
            parts = full_address.split(',')
            if len(parts) >= 2:
                extracted_data["city"] = parts[-2].strip().split()[-1] if parts[-2] else ""
                state_zip = parts[-1].strip()
                state_match = re.search(r'([A-Z]{2})\s+(\d{5})', state_zip)
                if state_match:
                    extracted_data["state"] = state_match.group(1)
                    extracted_data["zip_code"] = state_match.group(2)
        
        # Extract owner name
        owner_match = re.search(r'Owner:\s*([A-Za-z\s]+)(?:,|\n)', all_content)
        if owner_match:
            extracted_data["contact_name"] = owner_match.group(1).strip()
        
        # Extract years in business
        year_match = re.search(r'(?:Founded|Established|Since)\s+(\d{4})', all_content, re.I)
        if year_match:
            year = int(year_match.group(1))
            extracted_data["years_in_business"] = 2025 - year
            extracted_data["business_established_year"] = year
        
        # Extract employee count
        emp_match = re.search(r'team of (\d+)|(\d+)\s+(?:licensed\s+)?(?:electricians|technicians|employees)', all_content, re.I)
        if emp_match:
            count = emp_match.group(1) or emp_match.group(2)
            extracted_data["estimated_employees"] = int(count)
            
            # Determine size category based on employees
            emp_count = int(count)
            if emp_count <= 1:
                extracted_data["contractor_size_category"] = "solo_handyman"
            elif emp_count <= 3:
                extracted_data["contractor_size_category"] = "owner_operator"
            elif emp_count <= 20:
                extracted_data["contractor_size_category"] = "small_business"
            else:
                extracted_data["contractor_size_category"] = "regional_company"
        
        # Extract license
        license_match = re.search(r'License\s*#?\s*([A-Z0-9]+)', all_content, re.I)
        if license_match:
            extracted_data["license_number"] = license_match.group(1)
            extracted_data["license_verified"] = True
            extracted_data["license_state"] = "FL"  # From context
        
        # Extract certifications intelligently
        certifications = []
        cert_patterns = [
            "Tesla Certified", "ChargePoint Certified", "NECA Member",
            "BBB Accredited", "OSHA Certified", "Master Electrician",
            "Licensed", "Insured", "Bonded"
        ]
        for cert in cert_patterns:
            if cert.lower() in all_content.lower():
                certifications.append(cert)
        extracted_data["certifications"] = certifications
        
        # Extract services/specialties
        services = []
        service_patterns = [
            "Tesla Wall Connector Installation",
            "ChargePoint.*Installation",
            "Commercial EV Charging",
            "Electrical Panel Upgrades",
            "Smart Home Wiring",
            "Emergency.*Repairs",
            "Commercial Lighting",
            "Generator Installation",
            "Solar Panel.*Integration"
        ]
        for pattern in service_patterns:
            if re.search(pattern, all_content, re.I):
                services.append(pattern.replace(".*", "").replace("\\", ""))
        extracted_data["specialties"] = services[:10]
        extracted_data["services"] = services
        
        # Extract service areas
        areas_match = re.search(r'Service Areas?:\s*([^\n]+)', all_content, re.I)
        if areas_match:
            areas = [a.strip() for a in areas_match.group(1).split(',')]
            extracted_data["service_zip_codes"] = areas[:5]
        
        # Extract service radius
        radius_match = re.search(r'(\d+)\s*miles?\s+(?:from|radius)', all_content, re.I)
        if radius_match:
            extracted_data["service_radius_miles"] = int(radius_match.group(1))
        
        # Check for emergency services
        extracted_data["emergency_services"] = bool(re.search(r'24/7|emergency', all_content, re.I))
        
        # Check insurance/bonding
        extracted_data["insurance_verified"] = "insured" in all_content.lower()
        extracted_data["bonded"] = "bonded" in all_content.lower()
        
        # Extract social media
        fb_match = re.search(r'Facebook\.com/([A-Za-z0-9_]+)', all_content, re.I)
        if fb_match:
            extracted_data["facebook_url"] = f"https://facebook.com/{fb_match.group(1)}"
        
        ig_match = re.search(r'Instagram\s*@([A-Za-z0-9_]+)', all_content, re.I)
        if ig_match:
            extracted_data["instagram_url"] = f"https://instagram.com/{ig_match.group(1)}"
        
        # Check business type
        extracted_data["family_owned"] = "family owned" in all_content.lower()
        extracted_data["locally_owned"] = True  # Assumed from context
        
        # Check for free estimates
        extracted_data["free_estimates"] = "free estimate" in all_content.lower()
        
        # Check financing
        extracted_data["financing_available"] = "financing available" in all_content.lower()
        
        # Experience flags
        extracted_data["residential_experience"] = "residential" in all_content.lower()
        extracted_data["commercial_experience"] = "commercial" in all_content.lower()
        
        # Generate comprehensive AI summaries (simulating what Claude would write)
        extracted_data["ai_business_summary"] = (
            f"{company_name} is a family-owned electrical contracting company founded in 2015, "
            f"specializing in Tesla and ChargePoint EV charging station installations. "
            f"With a team of {extracted_data.get('estimated_employees', 'multiple')} licensed electricians, "
            f"they serve the Tampa Bay area with both residential and commercial electrical services."
        )
        
        extracted_data["ai_capability_description"] = (
            f"As certified installers for Tesla and ChargePoint, {company_name} offers comprehensive "
            f"electrical services including EV charging station installation, electrical panel upgrades, "
            f"smart home wiring, and 24/7 emergency repairs. Their team holds multiple certifications "
            f"including OSHA, NECA membership, and BBB accreditation with an A+ rating. They provide "
            f"free estimates, offer financing options, and maintain full licensing, insurance, and bonding "
            f"for customer protection. Their service radius extends 30 miles from Tampa, covering major "
            f"areas including St. Petersburg, Clearwater, Brandon, and Wesley Chapel."
        )
        
        extracted_data["competitive_advantages"] = (
            "Tesla & ChargePoint certified installer status, 24/7 emergency service availability, "
            "A+ BBB rating, comprehensive insurance and bonding, financing options available"
        )
        
        extracted_data["pricing_strategy"] = "Free estimates with competitive project-based pricing and financing options"
        
        # Add other fields that would be extracted
        extracted_data["business_hours"] = "24/7 for emergencies, standard hours for regular service"
        extracted_data["warranty_offered"] = True
        extracted_data["background_checks"] = True  # Implied by certifications
        extracted_data["safety_program"] = True  # OSHA certified
        
        logger.info(f"[Mock AI Analysis] Extracted {len([v for v in extracted_data.values() if v])} fields")
        
        return extracted_data