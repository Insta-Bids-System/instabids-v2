"""
Field mappings between AI-extracted insights and database columns
Maps GPT-4o extraction results to actual database schema
"""

# Relationship memory field mappings
RELATIONSHIP_FIELD_MAPPINGS = {
    # AI extracts -> Database column
    "personality_type": "personality_traits",  # Store as JSONB {"type": "analytical"}
    "work_style": "work_style",  # Direct match
    "customer_approach": "customer_approach",  # Direct match
    "decision_making_style": "decision_making_style",  # Direct match
    "stress_response": "stress_response",  # Direct match
    "confidence_level": "confidence_level",  # Direct match
}

# Bidding patterns field mappings  
BIDDING_FIELD_MAPPINGS = {
    "preferred_project_types": "sweet_spot_projects",  # Store as JSONB array
    "quality_standards": "competitive_positioning",  # Map to text field
    "pricing_strategy": "pricing_strategy",  # Direct match
    "timeline_preferences": "seasonal_patterns",  # Store in JSONB
    "project_size_preference": "preferred_project_size",  # Direct match
    "complexity_comfort": "competitive_positioning",  # Combine with quality
    "markup_info": "markup_percentages",  # Store as JSONB
}

# Information needs field mappings
INFO_NEEDS_FIELD_MAPPINGS = {
    "preferred_channels": "common_rfi_topics",  # Store as JSONB array
    "response_timing": "detail_level_preference",  # Map to preference
    "documentation_style": "technical_depth",  # Map to depth level
    "detail_level": "detail_level_preference",  # Direct match  
    "formality_level": "technical_depth",  # Combine with tech depth
    "follow_up_style": "project_scoping_approach",  # Map to approach
}

# Business profile field mappings
BUSINESS_FIELD_MAPPINGS = {
    "negotiation_style": "business_model",  # Store in text field
    "change_order_approach": "business_challenges",  # Store as JSONB
    "payment_preferences": "referral_sources",  # Store as JSONB
    "follow_up_style": "marketing_channels",  # Store as JSONB
    "risk_tolerance": "competitive_advantages",  # Store as JSONB
    "business_growth_focus": "growth_trajectory",  # Direct match
    "crm_system": "crm_system",  # Direct match
    "employee_count": "employee_count",  # Direct match
    "technology_adoption": "technology_adoption",  # Direct match
    "software_stack": "software_stack",  # Direct match
}

# Pain points field mappings
PAIN_POINTS_FIELD_MAPPINGS = {
    "operational_challenges": "operational_challenges",  # Direct match
    "technology_gaps": "technology_gaps",  # Direct match
    "workflow_inefficiencies": "workflow_inefficiencies",  # Direct match
    "financial_pain_points": "financial_pain_points",  # Direct match
    "immediate_needs": "immediate_needs",  # Direct match
    "automation_opportunities": "automation_opportunities",  # Direct match
    "customer_acquisition_challenges": "customer_acquisition_challenges",  # Direct match
    "compliance_concerns": "compliance_concerns",  # Direct match
}

def map_ai_to_database(ai_data: dict, field_mapping: dict) -> dict:
    """
    Map AI-extracted fields to database columns
    
    Args:
        ai_data: Dictionary from GPT-4o extraction
        field_mapping: Mapping dictionary for specific table
        
    Returns:
        Dictionary with database column names
    """
    mapped_data = {}
    
    for ai_field, value in ai_data.items():
        if ai_field in field_mapping:
            db_field = field_mapping[ai_field]
            
            # Special handling for certain fields
            if ai_field == "personality_type" and db_field == "personality_traits":
                # Convert single type to traits JSONB
                mapped_data[db_field] = {"type": value, "traits": [value]}
            elif ai_field == "markup_info" and db_field == "markup_percentages":
                # Parse markup info into structured JSONB
                if isinstance(value, str):
                    # Try to extract percentages
                    import re
                    materials_match = re.search(r'materials?\s*[:=]?\s*(\d+)%', value, re.I)
                    labor_match = re.search(r'labor\s*[:=]?\s*(\d+)%', value, re.I)
                    mapped_data[db_field] = {
                        "materials": int(materials_match.group(1)) if materials_match else None,
                        "labor": int(labor_match.group(1)) if labor_match else None
                    }
                else:
                    mapped_data[db_field] = value
            else:
                # Direct mapping
                mapped_data[db_field] = value
        else:
            # Field not in mapping - skip or store in a catch-all field
            pass
    
    return mapped_data

def prepare_for_database_insert(table_name: str, ai_data: dict, contractor_id: str) -> dict:
    """
    Prepare AI-extracted data for database insertion
    
    Args:
        table_name: Name of the database table
        ai_data: Dictionary from GPT-4o extraction
        contractor_id: Contractor ID for the record
        
    Returns:
        Dictionary ready for database insertion
    """
    # Select appropriate mapping
    if table_name == "contractor_relationship_memory":
        mapped = map_ai_to_database(ai_data, RELATIONSHIP_FIELD_MAPPINGS)
    elif table_name == "contractor_bidding_patterns":
        mapped = map_ai_to_database(ai_data, BIDDING_FIELD_MAPPINGS)
    elif table_name == "contractor_information_needs":
        mapped = map_ai_to_database(ai_data, INFO_NEEDS_FIELD_MAPPINGS)
    elif table_name == "contractor_business_profile":
        mapped = map_ai_to_database(ai_data, BUSINESS_FIELD_MAPPINGS)
    elif table_name == "contractor_pain_points":
        mapped = map_ai_to_database(ai_data, PAIN_POINTS_FIELD_MAPPINGS)
    else:
        mapped = ai_data
    
    # Add contractor_id
    mapped["contractor_id"] = contractor_id
    
    # Remove any None values to avoid database errors
    cleaned = {k: v for k, v in mapped.items() if v is not None}
    
    return cleaned