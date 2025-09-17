            # Extract business description
            desc_patterns = [
                r'(?:about us|company|business|who we are|our story)[^\n.]{10,500}',
                r'(?:we are|we provide|we specialize|our mission)[^\n.]{10,300}',
                r'(?:established|founded|since \d{4})[^\n.]{10,300}'
            ]
            
            for pattern in desc_patterns:
                matches = re.findall(pattern, clean_text, re.IGNORECASE)
                if matches:
                    all_page_data["business_description"] = matches[0].strip()
                    break
            
            # Extract services and specializations
            service_patterns = [
                r'(?:services|we offer|specializ[e|ing]|we do)[:\s]([^.]{10,200})',
                r'(?:holiday lighting|christmas lights|event lighting|landscape|residential|commercial)[^.]{0,100}',
                r'(?:installation|maintenance|design|custom)[^.]{0,100}'
            ]
            
            services_found = []
            for pattern in service_patterns:
                matches = re.findall(pattern, clean_text, re.IGNORECASE)
                services_found.extend([m.strip() for m in matches if len(m.strip()) > 5])
            
            all_page_data["services"] = list(set(services_found))[:10]  # Limit to 10 unique services
            
            # Extract specializations from services
            specialization_keywords = {
                "Holiday Lighting": ["holiday", "christmas", "seasonal", "light"],
                "Event Lighting": ["event", "wedding", "party", "special"],
                "Landscape Lighting": ["landscape", "outdoor", "garden", "pathway"],
                "Commercial": ["commercial", "business", "office", "retail"],
                "Residential": ["residential", "home", "house", "property"]
            }
            
            for spec, keywords in specialization_keywords.items():
                if any(keyword in clean_text.lower() for keyword in keywords):
                    all_page_data["specializations"].append(spec)
            
            # Extract years in business
            years_patterns = [
                r'(?:since|established|founded|in business)\s*(?:since)?\s*(\d{4})',
                r'(\d+)\s*years?\s*(?:of\s*)?(?:experience|in business)',
                r'over\s*(\d+)\s*years'
            ]
            
            for pattern in years_patterns:
                matches = re.findall(pattern, clean_text, re.IGNORECASE)
                if matches:
                    try:
                        year_or_years = int(matches[0])
                        if year_or_years > 1900:  # It's a year
                            all_page_data["years_in_business"] = 2024 - year_or_years
                        else:  # It's already years
                            all_page_data["years_in_business"] = year_or_years
                        break
                    except ValueError:
                        continue
            
            # Extract contact methods (emails and phones)
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            phone_pattern = r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
            
            emails = re.findall(email_pattern, clean_text)
            phones = re.findall(phone_pattern, clean_text)
            
            all_page_data["contact_methods"]["emails"] = list(set(emails))[:5]
            all_page_data["contact_methods"]["phones"] = [f"({p[0]}) {p[1]}-{p[2]}" for p in phones[:3]]
            
            # Extract team members
            team_patterns = [
                r'(?:owner|founder|ceo|president|manager)[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)[,\s]*(?:owner|founder|ceo|president)'
            ]
            
            for pattern in team_patterns:
                matches = re.findall(pattern, clean_text)
                for match in matches:
                    if len(match) > 3 and len(match) < 50:
                        all_page_data["team_members"].append({"name": match.strip(), "role": "Owner/Manager"})
            
            # Extract service areas
            area_patterns = [
                r'(?:serving|service area|we serve|covering|areas?)[:\s]*([^.]{10,200})',
                r'(?:fort lauderdale|miami|boca raton|palm beach|broward|dade)[^.]{0,100}'
            ]
            
            areas_found = []
            for pattern in area_patterns:
                matches = re.findall(pattern, clean_text, re.IGNORECASE)
                areas_found.extend([m.strip() for m in matches if len(m.strip()) > 3])
            
            all_page_data["service_areas"] = list(set(areas_found))[:10]
            
            # Extract certifications and licenses
            cert_patterns = [
                r'(?:licensed|certified|insured|bonded)[^.]{0,100}',
                r'(?:license|certification|insurance|bond)\s*#?\s*([A-Z0-9]+)',
                r'(?:member of|certified by|accredited)[^.]{0,100}'
            ]
            
            certs_found = []
            for pattern in cert_patterns:
                matches = re.findall(pattern, clean_text, re.IGNORECASE)
                certs_found.extend([m.strip() for m in matches if len(m.strip()) > 2])
            
            all_page_data["certifications"] = list(set(certs_found))[:10]
            
            # Extract business hours
            hours_patterns = [
                r'(?:hours|open)[:\s]*([^.]{10,100})',
                r'(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)[^.]{0,50}'
            ]
            
            for pattern in hours_patterns:
                matches = re.findall(pattern, clean_text, re.IGNORECASE)
                if matches:
                    all_page_data["business_hours"]["extracted"] = matches[0].strip()
                    break
            
            # Extract testimonials
            testimonial_patterns = [
                r'"([^"]{50,300})"',
                r'(?:customer says?|review|testimonial)[:\s]*"?([^."]{50,300})"?',
                r'(?:excellent|great|professional|highly recommend)[^.]{20,200}'
            ]
            
            for pattern in testimonial_patterns:
                matches = re.findall(pattern, clean_text, re.IGNORECASE)
                for match in matches[:5]:  # Limit to 5 testimonials
                    if 50 <= len(match.strip()) <= 300:
                        all_page_data["testimonials"].append(match.strip())
            
            # Extract company size indicators
            size_indicators = {
                "large": ["nationwide", "regional", "corporate", "enterprise", "hundreds", "over 100"],
                "medium": ["established", "experienced team", "professional staff", "decades", "20+ years"],
                "small": ["family owned", "local", "personalized", "owner operated", "small business"]
            }
            
            for size, indicators in size_indicators.items():
                if any(indicator.lower() in clean_text.lower() for indicator in indicators):
                    all_page_data["contractor_size"] = size
                    break
            
            # Estimate employees based on content
            employee_patterns = [
                r'(\d+)\s*(?:employees?|staff|team members?)',
                r'(?:staff of|team of)\s*(\d+)',
                r'over\s*(\d+)\s*(?:people|employees?)'
            ]
            
            for pattern in employee_patterns:
                matches = re.findall(pattern, clean_text, re.IGNORECASE)
                if matches:
                    try:
                        count = int(matches[0])
                        if count < 100:  # Reasonable range
                            all_page_data["estimated_employees"] = str(count)
                            break
                    except ValueError:
                        continue
            
            logger.info(f"🔍 REAL EXTRACTION completed: {len(all_page_data['services'])} services, {len(all_page_data['specializations'])} specializations, {len(all_page_data['certifications'])} certifications")
            
            return all_page_data
            
        except Exception as e:
            logger.error(f"Real extraction error: {e}")
            return {"error": str(e), "extraction_method": "FAILED"}