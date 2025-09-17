"""
CIA Schemas - Clean Pydantic models for the 12 InstaBids data points
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class UrgencyLevel(str, Enum):
    """Urgency levels for projects"""
    EMERGENCY = "emergency"
    URGENT = "urgent" 
    WEEK = "week"
    MONTH = "month"
    FLEXIBLE = "flexible"


class BidCardUpdate(BaseModel):
    """The 12 InstaBids data points we extract from conversation"""
    
    # Core project info
    project_type: Optional[str] = Field(None, description="Kitchen, bathroom, lawn, roofing, etc.")
    urgency: Optional[UrgencyLevel] = Field(None, description="How urgent is the project")
    scope_details: Optional[str] = Field(None, description="Detailed description of work needed")
    
    # Location
    location: Optional[str] = Field(None, description="Address or zip code")
    zip_code: Optional[str] = Field(None, description="Just the zip code if available")
    
    # Budget (only if volunteered)
    budget_min: Optional[float] = Field(None, description="Minimum budget if mentioned")
    budget_max: Optional[float] = Field(None, description="Maximum budget if mentioned")
    
    # Timeline
    timeline: Optional[str] = Field(None, description="When they want it done")
    timeline_flexibility: Optional[bool] = Field(None, description="Can timeline be adjusted")
    
    # Property details
    property_type: Optional[str] = Field(None, description="Single family, condo, commercial, etc.")
    property_size: Optional[str] = Field(None, description="Square footage or rooms if mentioned")
    
    # Requirements
    special_requirements: Optional[str] = Field(None, description="Permits, HOA, access issues")
    materials: Optional[str] = Field(None, description="Specific material preferences")
    
    # Contact
    email: Optional[str] = Field(None, description="Email for bid delivery")
    phone: Optional[str] = Field(None, description="Phone if provided")
    
    # Preferences
    contractor_preferences: Optional[str] = Field(None, description="Small/large company, local, etc.")
    contractor_count: Optional[int] = Field(None, description="How many bids they want")
    
    # Additional
    additional_notes: Optional[str] = Field(None, description="Any other relevant info")

    def to_bid_card_fields(self) -> dict:
        """Convert to format expected by unified 84-field schema"""
        # Map our clean fields to the NEW 84-field schema field names
        field_mapping = {
            # REQUIRED FIELDS for conversion
            "title": "title",
            "project_description": "description", 
            "zip_code": "location_zip",
            "urgency": "urgency_level",
            
            # CORE PROJECT FIELDS
            "project_type": "primary_trade",
            "service_type": "service_type",
            "room_location": "room_location",
            "property_area": "property_area",
            
            # BUDGET FIELDS
            "budget_min": "budget_min",
            "budget_max": "budget_max",
            
            # TIMELINE FIELDS  
            "timeline": "estimated_timeline",
            "timeline_flexibility": "timeline_flexibility",
            
            # CONTRACTOR FIELDS
            "contractor_preferences": "contractor_size_preference", 
            "contractor_count": "contractor_count_needed",
            "quality_expectations": "quality_expectations",
            
            # REQUIREMENTS (now JSONB arrays)
            "materials": "materials_specified",
            "special_requirements": "special_requirements",
            "group_bidding": "eligible_for_group_bidding",
            
            # CONTACT FIELDS
            "email": "email_address",
            "phone": "phone_number",
            
            # LOCATION FIELDS
            "city": "location_city",
            "state": "location_state"
        }
        
        result = {}
        data = self.dict(exclude_none=True)
        
        for our_field, db_field in field_mapping.items():
            if our_field in data:
                result[db_field] = data[our_field]
                
        # Handle JSONB fields properly (convert strings/lists to arrays)
        for our_field, db_field in field_mapping.items():
            if our_field in data and data[our_field] is not None:
                value = data[our_field]
                
                # Convert to JSONB arrays for specific fields
                if db_field in ['materials_specified', 'special_requirements']:
                    if isinstance(value, str):
                        # Convert comma-separated string to array
                        result[db_field] = [item.strip() for item in value.split(',') if item.strip()]
                    elif isinstance(value, list):
                        result[db_field] = value
                    else:
                        result[db_field] = [str(value)]
                
                # Convert service_type to JSONB object
                elif db_field == 'service_type':
                    if isinstance(value, str):
                        result[db_field] = {"type": value, "category": value}
                    else:
                        result[db_field] = value
                        
                else:
                    result[db_field] = value
                    
        # Also include unmapped fields that match schema
        for field, value in data.items():
            if field not in field_mapping and value is not None:
                result[field] = value
                
        return result

    def calculate_completion(self) -> int:
        """Calculate % of critical fields filled based on 84-field schema"""
        # Define which fields are critical for conversion (matches schema requirements)
        critical_fields = [
            "title", "project_description", "zip_code", "urgency", "contractor_count"
        ]
        
        # Additional important fields
        important_fields = [
            "project_type", "email", "timeline", "budget_min", "budget_max"
        ]
        
        # Count how many critical fields are filled
        filled_critical = sum(
            1 for field in critical_fields 
            if getattr(self, field) is not None
        )
        
        # Count total non-None fields
        all_fields = [
            field for field in self.dict() 
            if getattr(self, field) is not None
        ]
        
        # Weight critical fields more heavily
        critical_score = (filled_critical / len(critical_fields)) * 60
        other_score = (len(all_fields) / 12) * 40
        
        return min(int(critical_score + other_score), 100)