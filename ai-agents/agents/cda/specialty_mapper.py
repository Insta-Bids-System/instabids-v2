"""
Specialty Mapper - Maps Google Maps types to contractor specialties
"""

def map_google_types_to_specialties(google_types: list[str], project_type: str) -> list[str]:
    """
    Map Google Maps place types to contractor specialties
    
    Google typically returns types like:
    - 'plumber', 'contractor', 'roofing_contractor'
    - 'electrician', 'general_contractor', 'construction_company'
    
    We map these to specialties like:
    - 'plumbing', 'electrical work', 'roofing repair', 'roofing installation'
    """

    specialties = []

    # Mapping of Google types to our specialty terms
    type_to_specialty_map = {
        # Service types
        "plumber": ["plumbing", "pipe repair", "drain cleaning"],
        "electrician": ["electrical work", "wiring", "electrical repairs"],
        "roofing_contractor": ["roofing repair", "roofing installation", "roof maintenance"],
        "painter": ["painting", "interior painting", "exterior painting"],
        "carpenter": ["carpentry", "woodwork", "custom carpentry"],
        "hvac_contractor": ["hvac", "heating", "cooling", "air conditioning"],
        "landscaping": ["landscaping", "lawn care", "yard maintenance"],
        "flooring_contractor": ["flooring", "tile installation", "hardwood flooring"],
        "general_contractor": ["general contracting", "home remodeling", "renovations"],
        "construction_company": ["construction", "building", "home additions"],
        "bathroom_remodeler": ["bathroom remodeling", "bath renovation", "shower installation"],
        "kitchen_remodeler": ["kitchen remodeling", "cabinet installation", "countertop installation"],
        "handyman": ["general repairs", "minor repairs", "home maintenance"],
        "contractor": ["general contracting", "home improvement"],

        # Additional service indicators
        "home_improvement_store": ["materials supply", "DIY assistance"],
        "building_materials_store": ["materials supply"],
        "hardware_store": ["tools and materials"],
    }

    # Process each Google type
    for google_type in google_types:
        # Clean and normalize the type
        google_type_clean = google_type.lower().replace("_", " ")

        # Direct mapping
        if google_type in type_to_specialty_map:
            specialties.extend(type_to_specialty_map[google_type])

        # Check for partial matches (e.g., "roofing_contractor" contains "roofing")
        for key, values in type_to_specialty_map.items():
            if key in google_type or google_type in key:
                for specialty in values:
                    if specialty not in specialties:
                        specialties.append(specialty)

    # Add project-specific specialties based on the search
    project_specialties = get_project_type_specialties(project_type)
    for specialty in project_specialties:
        if specialty not in specialties:
            specialties.append(specialty)

    # Remove duplicates while preserving order
    seen = set()
    unique_specialties = []
    for specialty in specialties:
        if specialty not in seen:
            seen.add(specialty)
            unique_specialties.append(specialty)

    # Limit to top 4 most relevant specialties
    return unique_specialties[:4] if unique_specialties else [project_type]


def get_project_type_specialties(project_type: str) -> list[str]:
    """
    Get default specialties based on project type
    """
    project_specialty_map = {
        "roofing": ["roofing repair", "roofing installation", "roof maintenance"],
        "plumbing": ["plumbing", "pipe repair", "drain cleaning", "fixture installation"],
        "electrical": ["electrical work", "wiring", "electrical repairs", "panel upgrades"],
        "kitchen remodel": ["kitchen remodeling", "cabinet installation", "countertop installation"],
        "bathroom remodel": ["bathroom remodeling", "tile work", "fixture installation"],
        "landscaping": ["landscaping", "lawn care", "tree service", "yard maintenance"],
        "painting": ["interior painting", "exterior painting", "drywall repair"],
        "hvac": ["hvac repair", "hvac installation", "hvac maintenance"],
        "flooring": ["flooring installation", "tile work", "carpet installation"],
        "general": ["general contracting", "home improvement", "repairs"],
    }

    # Clean project type
    project_type_clean = project_type.lower().strip()

    # Direct match
    if project_type_clean in project_specialty_map:
        return project_specialty_map[project_type_clean]

    # Partial match
    for key, values in project_specialty_map.items():
        if key in project_type_clean or project_type_clean in key:
            return values

    # Default
    return [project_type_clean]


def infer_contractor_size_from_google(google_types: list[str], review_count: int, company_name: str) -> str:
    """
    Infer contractor size based on Google data
    
    Returns: 'solo_handyman', 'owner_operator', 'small_business', 'regional_company'
    """

    # Check for handyman indicators
    if "handyman" in google_types or "handyman" in company_name.lower():
        return "solo_handyman"

    # Check review count as proxy for business size
    if review_count < 20:
        return "solo_handyman"
    elif review_count < 50:
        return "owner_operator"
    elif review_count < 200:
        return "small_business"
    else:
        return "regional_company"

    # Check for company type indicators in name
    name_lower = company_name.lower()
    if any(word in name_lower for word in ["inc", "corp", "group", "enterprises"]):
        return "regional_company" if review_count > 100 else "small_business"
    elif any(word in name_lower for word in ["bob's", "mike's", "joe's", "john's"]):
        return "owner_operator"

    # Default based on review count
    return "small_business"
