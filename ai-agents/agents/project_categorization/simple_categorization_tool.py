"""
Simple Project Categorization Tool
Provides categorization functions for CIA and IRIS agents using GPT-4o
"""

import logging
import json
from typing import Dict, Any, Optional
from database_simple import db
# db_select is not available, use db.client.table().select() instead
import openai
from datetime import datetime

logger = logging.getLogger(__name__)

async def categorize_and_save_project(
    description: str,
    bid_card_id: str,
    context: str = ""
) -> Dict[str, Any]:
    """
    Categorize a project using GPT-4o and save the results
    Maps project descriptions to actual project types in database
    """
    try:
        # Load project types from database
        # Use db.client directly instead of db_select
        result = db.client.table("project_types").select("*").limit(200).execute()
        project_types = result.data if result else []
        if not project_types:
            logger.error("No project types found in database")
            return {
                "success": False,
                "error": "No project types available",
                "message": "Database configuration error"
            }
        
        # Find best matching project type using GPT-4o
        matched_type = await _find_matching_project_type(description, context, project_types)
        
        if matched_type:
            # Update the bid card with the project type ID
            updated = await _update_bid_card_project_type(bid_card_id, matched_type['id'])
            
            if updated:
                # Get the contractor_type_ids that were saved
                contractor_type_ids = []
                try:
                    mapping_result = db.client.table("project_type_contractor_mappings").select("contractor_type_id").eq("project_type_id", matched_type['id']).execute()
                    if mapping_result.data:
                        contractor_type_ids = [row['contractor_type_id'] for row in mapping_result.data]
                except:
                    pass
                
                return {
                    "success": True,
                    "project_type_id": matched_type['id'],
                    "project_type_name": matched_type['name'],
                    "project_type": matched_type['name'],  # Add this for agent_fast.py
                    "service_category": matched_type.get('service_category'),
                    "contractor_type_ids": contractor_type_ids,  # Include the actual IDs
                    "complexity_score": 0.5,  # Default for now
                    "message": f"Project categorized as {matched_type['name']}"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to update bid card",
                    "message": "Database update failed"
                }
        else:
            # Fallback to general if no match found
            return {
                "success": True,
                "project_type_id": None,
                "project_type_name": "general_construction",
                "service_category": "general",
                "complexity_score": 0.5,
                "message": "Project categorized as general construction"
            }
        
    except Exception as e:
        logger.error(f"Error categorizing project: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to categorize project"
        }

async def _find_matching_project_type(
    description: str, 
    context: str,
    project_types: list
) -> Optional[Dict[str, Any]]:
    """
    Use GPT-4o to find the best matching project type
    """
    try:
        # Check for direct keyword matches first
        description_lower = description.lower()
        
        # Common mappings
        direct_mappings = {
            "toilet repair": 122,  # Toilet Repair ID
            "toilet leak": 122,
            "toilet running": 122,
            "toilet won't stop": 122,
            "leaking toilet": 122,
            "running toilet": 122,
            "toilet installation": 123,  # Toilet Installation ID
            "new toilet": 123,
            "replace toilet": 123,
            "kitchen sink": 45,  # Kitchen Sink Installation
            "bathroom remodel": 89,  # Bathroom Remodel
            "lawn care": 156,  # Lawn Care
            "lawn maintenance": 156,
        }
        
        # Check direct mappings
        for keyword, project_id in direct_mappings.items():
            if keyword in description_lower:
                for pt in project_types:
                    if pt['id'] == project_id:
                        logger.info(f"Direct match found: {pt['name']} for keyword '{keyword}'")
                        return pt
        
        # If no direct match, use GPT-4o
        system_prompt = """You are a construction project categorization expert for InstaBids.
Match the project description to the EXACT project type from the available list.
Focus on finding the most specific match possible.
For toilet-related issues that involve repairs, leaks, or running water, choose 'Toilet Repair' (ID: 122).
For new toilet installations, choose 'Toilet Installation' (ID: 123)."""

        # Prepare project options
        project_options = [
            {
                "id": pt['id'],
                "name": pt['name'],
                "category": pt.get('service_category', 'general')
            } 
            for pt in project_types
        ]
        
        combined_description = f"{description} {context}".strip()
        
        user_prompt = f"""Project description: "{combined_description}"

Available project types (showing first 50):
{json.dumps(project_options[:50], indent=2)}

Based on the description, which project type is the best match?

Return JSON format:
{{
    "project_type_id": <id>,
    "confidence": <0-100>,
    "reasoning": "<brief explanation>"
}}"""

        # Call OpenAI GPT-4o
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=200
        )
        
        # Parse response
        response_text = response.choices[0].message.content.strip()
        
        # Handle JSON extraction
        if not response_text.startswith('{'):
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
        
        result = json.loads(response_text)
        
        # Find matching project type
        project_id = result.get('project_type_id')
        confidence = result.get('confidence', 0)
        reasoning = result.get('reasoning', '')
        
        for project_type in project_types:
            if project_type['id'] == project_id:
                logger.info(f"GPT-4o match: {project_type['name']} (confidence: {confidence}%) - {reasoning}")
                return project_type
        
        return None
        
    except Exception as e:
        logger.error(f"Error in GPT-4o matching: {e}")
        return None

async def _update_bid_card_project_type(bid_card_id: str, project_type_id: int) -> bool:
    """
    Update bid card with project type AND contractor_type_ids
    """
    try:
        # First, get the contractor_type_ids for this project_type
        contractor_type_ids = []
        try:
            # Get the mapping from project_type to contractor_types
            mapping_result = db.client.table("project_type_contractor_mappings").select("contractor_type_id").eq("project_type_id", project_type_id).execute()
            
            if mapping_result.data:
                contractor_type_ids = [row['contractor_type_id'] for row in mapping_result.data]
                logger.info(f"Found contractor_type_ids for project_type {project_type_id}: {contractor_type_ids}")
            else:
                logger.warning(f"No contractor_type_ids found for project_type {project_type_id}")
        except Exception as e:
            logger.error(f"Error getting contractor_type_ids: {e}")
        
        # Update potential_bid_cards with both project_type AND contractor_type_ids
        try:
            update_data = {
                "project_type": str(project_type_id),  # Convert to string for varchar column
                "updated_at": datetime.now().isoformat()
            }
            
            # Only add contractor_type_ids if we found some
            if contractor_type_ids:
                update_data["contractor_type_ids"] = contractor_type_ids
            
            potential_result = db.client.table("potential_bid_cards").update(update_data).eq("id", bid_card_id).execute()
            
            if potential_result.data:
                logger.info(f"Successfully updated potential_bid_cards for {bid_card_id} with project_type: {project_type_id} and contractor_type_ids: {contractor_type_ids}")
                return True
            else:
                logger.error(f"No rows updated in potential_bid_cards for {bid_card_id}")
                return False
        except Exception as e:
            logger.error(f"Error updating potential_bid_cards: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating bid card: {e}")
        return False

def format_response_for_agent(result: Dict[str, Any]) -> str:
    """
    Format categorization result for agent response
    """
    if result.get("success"):
        project_name = result.get('project_type_name', 'general')
        
        # Return empty string so it doesn't override the main conversation
        # The categorization happens behind the scenes
        return ""
    else:
        # Return empty string to let normal conversation continue
        return ""