"""
CIA Integration with Potential Bid Cards API
This module handles creating and updating potential bid cards during CIA conversations
"""

import logging
import json
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PotentialBidCardManager:
    """Manages potential bid card creation and updates during CIA conversations"""
    
    def __init__(self, base_url: str = "http://localhost:8008"):
        self.base_url = base_url
        self.api_endpoint = f"{base_url}/api/cia/potential-bid-cards"
        
    async def create_potential_bid_card(
        self, 
        conversation_id: str,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a new potential bid card for the conversation
        Returns the bid card ID if successful
        """
        try:
            payload = {
                "conversation_id": conversation_id,
                "session_id": session_id,
                "user_id": user_id,
                "anonymous_user_id": user_id if user_id == "00000000-0000-0000-0000-000000000000" else None,
                "title": "New Project"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.api_endpoint, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                bid_card_id = data.get("id")
                logger.info(f"[CIA] Created potential bid card: {bid_card_id}")
                return bid_card_id
            else:
                logger.error(f"[CIA] Failed to create potential bid card: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"[CIA] Error creating potential bid card: {e}")
            return None
    
    async def update_bid_card_field(
        self,
        bid_card_id: str,
        field_name: str,
        field_value: Any,
        confidence: float = 1.0
    ) -> bool:
        """
        Update a specific field in the potential bid card
        """
        try:
            # Map CIA field names to potential bid card field names
            # FIXED: These mappings now correctly match the database schema
            field_mapping = {
                # Core project fields (FIXED)
                "project_type": "project_type",  # FIXED: was mapping to primary_trade
                "project_description": "description",  # FIXED: was mapping to non-existent user_scope_notes
                "title": "title",  # NEW: was missing
                
                # Location fields (FIXED)
                "location_zip": "location_zip",  # FIXED: was missing
                "zip_code": "zip_code",  # Keep for backward compatibility
                "zip": "zip_code",  # Keep for backward compatibility
                "room_location": "room_location",
                "property_area": "property_area",
                
                # Budget fields (FIXED)
                "budget_min": "budget_min",  # FIXED: was mapping to non-existent budget_range_min
                "budget_max": "budget_max",  # FIXED: was mapping to non-existent budget_range_max
                "budget_context": "budget_context",
                
                # Timeline fields
                "timeline": "estimated_timeline",
                "urgency": "urgency_level",
                "timeline_flexibility": "timeline_flexibility",
                
                # Contractor preferences
                "contractor_size": "contractor_size_preference",
                "quality_expectations": "quality_expectations",
                
                # Materials and specifications
                "materials": "materials_specified",
                "special_requirements": "special_requirements",
                
                # Service and complexity
                "service_type": "service_type",
                "project_complexity": "project_complexity",
                "component_type": "component_type",
                "service_complexity": "service_complexity",
                "trade_count": "trade_count",
                "primary_trade": "primary_trade",
                "secondary_trades": "secondary_trades",
                
                # Date fields
                "bid_collection_deadline": "bid_collection_deadline",
                "project_completion_deadline": "project_completion_deadline",
                "deadline_hard": "deadline_hard",
                "deadline_context": "deadline_context",
                
                # Email/contact
                "email_address": "email_address"
            }
            
            # Fields that don't exist in database - ignore these to avoid 500 errors
            ignored_fields = {
                "property_type",
                "property_size", 
                "current_condition",
                "location",
                "location_context",
                "contractor_requirements",
                "urgency_reason",
                "timeline_details",
                "uploaded_photos",
                "photo_analyses",
                "phone_number"
            }
            
            # Skip fields that don't exist in database
            if field_name in ignored_fields:
                logger.info(f"[CIA] Skipping ignored field: {field_name}")
                return True  # Return success to avoid blocking other updates
            
            # Get the mapped field name
            mapped_field = field_mapping.get(field_name, field_name)
            
            payload = {
                "field_name": mapped_field,
                "field_value": field_value,
                "confidence": confidence,
                "source": "conversation"
            }
            
            url = f"{self.api_endpoint}/{bid_card_id}/field"
            async with httpx.AsyncClient() as client:
                response = await client.put(url, json=payload)
            
            if response.status_code == 200:
                logger.info(f"[CIA] Updated bid card field {mapped_field}: {field_value}")
                return True
            else:
                logger.error(f"[CIA] Failed to update field {mapped_field}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"[CIA] Error updating bid card field: {e}")
            return False
    
    async def update_from_collected_info(
        self,
        bid_card_id: str,
        collected_info: Dict[str, Any]
    ) -> int:
        """
        Update multiple fields from CIA's collected_info
        Returns number of fields successfully updated
        """
        if not bid_card_id or not collected_info:
            return 0
            
        updated_count = 0
        
        # Update each collected field
        for field_name, field_value in collected_info.items():
            if field_value is not None and field_value != "":
                success = await self.update_bid_card_field(
                    bid_card_id,
                    field_name,
                    field_value
                )
                if success:
                    updated_count += 1
                    
        logger.info(f"[CIA] Updated {updated_count} fields in potential bid card")
        return updated_count
    
    async def get_bid_card_status(self, bid_card_id: str) -> Optional[Dict]:
        """
        Get the current status of a potential bid card
        """
        try:
            url = f"{self.api_endpoint}/{bid_card_id}"
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"[CIA] Failed to get bid card status: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"[CIA] Error getting bid card status: {e}")
            return None
    
    async def convert_to_official_bid_card(
        self,
        bid_card_id: str,
        user_id: str
    ) -> Optional[str]:
        """
        Convert potential bid card to official bid card after signup
        Returns the official bid card ID if successful
        """
        try:
            url = f"{self.api_endpoint}/{bid_card_id}/convert-to-bid-card"
            payload = {"user_id": user_id}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                official_bid_card_id = data.get("official_bid_card_id")
                logger.info(f"[CIA] Converted to official bid card: {official_bid_card_id}")
                return official_bid_card_id
            else:
                logger.error(f"[CIA] Failed to convert bid card: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"[CIA] Error converting bid card: {e}")
            return None