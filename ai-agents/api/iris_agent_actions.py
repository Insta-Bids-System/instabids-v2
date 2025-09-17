"""
IRIS Agent Action System
Enables IRIS to perform real-time modifications to bid cards, repairs, and properties
"""

import logging
import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import asyncio
from config.service_urls import get_backend_url

logger = logging.getLogger(__name__)

class IRISActionSystem:
    """System for IRIS to perform actual modifications"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or get_backend_url()
        self.session = requests.Session()
        
    def add_repair_item(
        self,
        potential_bid_card_id: str,
        item_description: str,
        severity: str = "medium",
        category: Optional[str] = None,
        estimated_cost: Optional[float] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a repair item to a potential bid card"""
        try:
            from database import db
            
            # Get current ai_analysis
            result = db.client.table('potential_bid_cards').select('ai_analysis').eq('id', potential_bid_card_id).execute()
            
            if not result.data:
                return {"success": False, "message": "Potential bid card not found"}
            
            ai_analysis = result.data[0].get('ai_analysis', {}) or {}
            repair_items = ai_analysis.get('repair_items', [])
            
            # Create new repair item with unique ID
            new_item = {
                "id": f"repair_{uuid.uuid4().hex[:8]}",
                "description": item_description,
                "severity": severity,
                "category": category or "general",
                "estimated_cost": estimated_cost or 0,
                "created_at": datetime.utcnow().isoformat()
            }
            
            repair_items.append(new_item)
            ai_analysis['repair_items'] = repair_items
            
            # Update the potential bid card
            update_result = db.client.table('potential_bid_cards').update({
                'ai_analysis': ai_analysis,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', potential_bid_card_id).execute()
            
            if update_result.data:
                logger.info(f"IRIS added repair item: {item_description}")
                return {
                    "success": True,
                    "action": "added_repair_item",
                    "item": new_item,
                    "message": f"I've added '{item_description}' to your project."
                }
            else:
                return {"success": False, "message": "Failed to add repair item"}
                
        except Exception as e:
            logger.error(f"Error adding repair item: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "There was an error adding the repair item."
            }
    
    def update_repair_item(
        self,
        potential_bid_card_id: str,
        repair_item_id: str,
        updates: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a specific repair item in a potential bid card"""
        try:
            from database import db
            
            # Get current ai_analysis
            result = db.client.table('potential_bid_cards').select('ai_analysis').eq('id', potential_bid_card_id).execute()
            
            if not result.data:
                return {"success": False, "message": "Potential bid card not found"}
            
            ai_analysis = result.data[0].get('ai_analysis', {}) or {}
            repair_items = ai_analysis.get('repair_items', [])
            
            # Find and update the repair item
            item_found = False
            for item in repair_items:
                if item.get('id') == repair_item_id:
                    # Update allowed fields
                    if 'description' in updates:
                        item['description'] = updates['description']
                    if 'severity' in updates:
                        item['severity'] = updates['severity']
                    if 'category' in updates:
                        item['category'] = updates['category']
                    if 'estimated_cost' in updates:
                        item['estimated_cost'] = updates['estimated_cost']
                    if 'status' in updates:
                        item['status'] = updates['status']
                    
                    item['updated_at'] = datetime.utcnow().isoformat()
                    item_found = True
                    break
            
            if not item_found:
                return {"success": False, "message": "Repair item not found"}
            
            ai_analysis['repair_items'] = repair_items
            
            # Update the potential bid card
            update_result = db.client.table('potential_bid_cards').update({
                'ai_analysis': ai_analysis,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', potential_bid_card_id).execute()
            
            if update_result.data:
                logger.info(f"IRIS updated repair item: {repair_item_id}")
                return {
                    "success": True,
                    "action": "updated_repair_item",
                    "item_id": repair_item_id,
                    "updates": updates,
                    "message": f"I've updated the repair item."
                }
            else:
                return {"success": False, "message": "Failed to update repair item"}
                
        except Exception as e:
            logger.error(f"Error updating repair item: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_repair_item(
        self,
        potential_bid_card_id: str,
        repair_item_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delete a repair item from a potential bid card"""
        try:
            from database import db
            
            # Get current ai_analysis
            result = db.client.table('potential_bid_cards').select('ai_analysis').eq('id', potential_bid_card_id).execute()
            
            if not result.data:
                return {"success": False, "message": "Potential bid card not found"}
            
            ai_analysis = result.data[0].get('ai_analysis', {}) or {}
            repair_items = ai_analysis.get('repair_items', [])
            
            # Find and remove the repair item
            original_count = len(repair_items)
            repair_items = [item for item in repair_items if item.get('id') != repair_item_id]
            
            if len(repair_items) == original_count:
                return {"success": False, "message": "Repair item not found"}
            
            ai_analysis['repair_items'] = repair_items
            
            # Update the potential bid card
            update_result = db.client.table('potential_bid_cards').update({
                'ai_analysis': ai_analysis,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', potential_bid_card_id).execute()
            
            if update_result.data:
                logger.info(f"IRIS deleted repair item: {repair_item_id}")
                return {
                    "success": True,
                    "action": "deleted_repair_item",
                    "item_id": repair_item_id,
                    "message": "I've removed that repair item from your project."
                }
            else:
                return {"success": False, "message": "Failed to delete repair item"}
                
        except Exception as e:
            logger.error(f"Error deleting repair item: {e}")
            return {"success": False, "error": str(e)}
    
    def list_repair_items(
        self,
        potential_bid_card_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """List all repair items in a potential bid card"""
        try:
            from database import db
            
            # Get current ai_analysis
            result = db.client.table('potential_bid_cards').select('ai_analysis, title').eq('id', potential_bid_card_id).execute()
            
            if not result.data:
                return {"success": False, "message": "Potential bid card not found"}
            
            card_data = result.data[0]
            ai_analysis = card_data.get('ai_analysis', {}) or {}
            repair_items = ai_analysis.get('repair_items', [])
            
            # Calculate total estimated cost
            total_cost = sum(item.get('estimated_cost', 0) for item in repair_items)
            
            return {
                "success": True,
                "action": "listed_repair_items",
                "card_title": card_data.get('title', 'Untitled'),
                "repair_items": repair_items,
                "total_items": len(repair_items),
                "total_estimated_cost": total_cost,
                "message": f"This project has {len(repair_items)} repair items with an estimated total of ${total_cost:,.2f}"
            }
                
        except Exception as e:
            logger.error(f"Error listing repair items: {e}")
            return {"success": False, "error": str(e)}
    
    def update_bid_card(
        self,
        bid_card_id: str,  # This is actually a potential_bid_card_id
        updates: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update POTENTIAL bid card fields with real-time UI updates"""
        try:
            request_id = str(uuid.uuid4())
            
            # Map user-friendly field names to POTENTIAL bid card database fields
            field_mapping = {
                "budget": ["budget_range_min", "budget_range_max"],
                "timeline": ["estimated_timeline"],  # potential_bid_cards uses single timeline field
                "urgency": ["urgency_level"],
                "description": ["user_scope_notes"],  # potential_bid_cards uses this for description
                "title": ["title"],
                "location": ["zip_code"],  # potential_bid_cards uses zip_code
                "trade": ["primary_trade"]  # potential_bid_cards uses primary_trade
            }
            
            # Process updates for potential_bid_cards
            processed_updates = {}
            for key, value in updates.items():
                if key in field_mapping:
                    fields = field_mapping[key]
                    if key == "budget" and isinstance(value, dict):
                        if "min" in value:
                            processed_updates["budget_range_min"] = value["min"]
                        if "max" in value:
                            processed_updates["budget_range_max"] = value["max"]
                    elif key == "timeline":
                        # potential_bid_cards uses single estimated_timeline field
                        processed_updates["estimated_timeline"] = value
                    else:
                        for field in fields:
                            processed_updates[field] = value
            
            # Direct database update instead of API call to avoid recursion
            from database import db
            
            try:
                # Update the POTENTIAL bid card (not the actual bid card!)
                processed_updates["updated_at"] = datetime.utcnow().isoformat()
                result = db.client.table('potential_bid_cards').update(processed_updates).eq('id', bid_card_id).execute()
                
                if result.data:
                    changed_fields = list(processed_updates.keys())
                    logger.info(f"IRIS updated bid card fields: {changed_fields}")
                    return {
                        "success": True,
                        "action": "updated_bid_card",
                        "changed_fields": changed_fields,
                        "message": f"I've updated the {', '.join(updates.keys())} for this project."
                    }
                else:
                    return {
                        "success": False,
                        "message": "I couldn't update those fields right now."
                    }
            except Exception as e:
                logger.error(f"Database update failed: {e}")
                return {
                    "success": False,
                    "message": "I couldn't update those fields right now."
                }
                
        except Exception as e:
            logger.error(f"Error updating bid card: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "There was an error updating the bid card."
            }
    
    def update_potential_bid_card(
        self,
        potential_bid_card_id: str,
        field_updates: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update potential bid card fields with real-time UI updates"""
        try:
            request_id = str(uuid.uuid4())
            
            payload = {
                "request_id": request_id,
                "agent_name": "IRIS",
                "user_id": user_id,
                "potential_bid_card_id": potential_bid_card_id,
                "field_updates": field_updates
            }
            
            response = self.session.post(
                f"{self.base_url}/api/iris/actions/update-potential-bid-card",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"IRIS updated potential bid card: {list(field_updates.keys())}")
                return {
                    "success": True,
                    "action": "updated_potential_bid_card",
                    "updated_fields": list(field_updates.keys()),
                    "message": f"I've updated the potential bid card with your changes."
                }
            else:
                return {
                    "success": False,
                    "message": "I couldn't update the potential bid card."
                }
                
        except Exception as e:
            logger.error(f"Error updating potential bid card: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_bid_card_from_repairs(
        self,
        property_id: str,
        repair_items: List[Dict[str, Any]],
        project_title: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new bid card from repair items"""
        try:
            request_id = str(uuid.uuid4())
            
            # Estimate budget based on repair items
            total_cost = sum(item.get("estimated_cost", 5000) for item in repair_items)
            budget_min = int(total_cost * 0.8)
            budget_max = int(total_cost * 1.2)
            
            # Determine trade type from repairs
            trade_types = set()
            for item in repair_items:
                category = item.get("category", "").lower()
                if "electrical" in category:
                    trade_types.add("Electrical")
                elif "plumbing" in category:
                    trade_types.add("Plumbing")
                elif "hvac" in category or "heating" in category or "cooling" in category:
                    trade_types.add("HVAC")
                elif "roof" in category:
                    trade_types.add("Roofing")
                elif "paint" in category:
                    trade_types.add("Painting")
                else:
                    trade_types.add("General Contractor")
            
            trade_type = ", ".join(trade_types) if trade_types else "General Contractor"
            
            bid_card_data = {
                "project_title": project_title,
                "description": f"Project including {len(repair_items)} repair items",
                "budget_min": budget_min,
                "budget_max": budget_max,
                "trade_type": trade_type,
                "urgency_level": "normal",
                "timeline_start": datetime.utcnow().isoformat(),
                "timeline_end": datetime.utcnow().isoformat(),  # Will be updated
                "repair_items": repair_items
            }
            
            payload = {
                "request_id": request_id,
                "agent_name": "IRIS",
                "user_id": user_id,
                "property_id": property_id,
                "bid_card_data": bid_card_data
            }
            
            response = self.session.post(
                f"{self.base_url}/api/iris/actions/create-bid-card",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"IRIS created bid card: {project_title}")
                return {
                    "success": True,
                    "action": "created_bid_card",
                    "bid_card": result.get("bid_card"),
                    "message": f"I've created a new bid card: '{project_title}' with {len(repair_items)} repair items."
                }
            else:
                return {
                    "success": False,
                    "message": "I couldn't create the bid card right now."
                }
                
        except Exception as e:
            logger.error(f"Error creating bid card: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_property_details(
        self,
        property_id: str,
        updates: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update property details (needs endpoint implementation)"""
        try:
            # TODO: Implement when property update endpoint is ready
            logger.info(f"Would update property {property_id} with: {updates}")
            return {
                "success": False,
                "action": "property_update_pending",
                "message": "Property updates are coming soon! I've noted your changes."
            }
        except Exception as e:
            logger.error(f"Error updating property: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def parse_user_intent_for_actions(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse user message to determine what actions to take"""
        message_lower = message.lower()
        actions = []
        
        # Check for title/name changes (HIGH PRIORITY)
        if any(word in message_lower for word in ["rename", "change name", "change title", "call it"]):
            actions.append({
                "type": "update_title",
                "confidence": 0.95
            })
        
        # Check for repair item additions
        if any(word in message_lower for word in ["add", "include", "need"]) and \
           any(word in message_lower for word in ["repair", "fix", "replace", "install"]):
            actions.append({
                "type": "add_repair",
                "confidence": 0.8
            })
        
        # Check for budget updates
        if any(word in message_lower for word in ["budget", "cost", "price", "spend"]) and \
           any(word in message_lower for word in ["$", "dollar", "thousand", "million"]):
            actions.append({
                "type": "update_budget",
                "confidence": 0.7
            })
        
        # Check for urgency updates
        if any(word in message_lower for word in ["urgent", "emergency", "asap", "immediately", "quickly", "rush"]):
            actions.append({
                "type": "update_urgency",
                "confidence": 0.9
            })
        
        # Check for timeline updates
        if any(word in message_lower for word in ["timeline", "deadline", "when", "start", "finish", "complete"]):
            actions.append({
                "type": "update_timeline",
                "confidence": 0.7
            })
        
        # Check for bid card creation
        if any(word in message_lower for word in ["create", "make", "start"]) and \
           any(word in message_lower for word in ["project", "bid", "quote"]):
            actions.append({
                "type": "create_bid_card",
                "confidence": 0.8
            })
        
        return {
            "actions": actions,
            "requires_action": len(actions) > 0
        }

# Global instance
iris_actions = IRISActionSystem()