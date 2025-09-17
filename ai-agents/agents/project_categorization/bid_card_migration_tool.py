"""
BID CARD MIGRATION TOOL
Processes existing bid cards through the new 4-tier categorization system
Salvages ~78% of existing bid cards automatically
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database_simple import execute_query, db_select, db
import openai

logger = logging.getLogger(__name__)

class BidCardMigrationTool:
    def __init__(self):
        self.project_types = []
        self.migration_stats = {
            "total_processed": 0,
            "successful_categorizations": 0,
            "failed_categorizations": 0,
            "skipped_insufficient_data": 0,
            "direct_mappings": 0
        }
    
    async def migrate_all_bid_cards(self, test_mode: bool = True, batch_size: int = 5) -> Dict[str, Any]:
        """
        Main migration function - processes all bid cards through categorization system
        
        Args:
            test_mode: If True, only processes first batch_size bid cards
            batch_size: Number of bid cards to process in test mode
        """
        try:
            # Load available project types
            await self._load_project_types()
            
            # Get all bid cards that need categorization
            bid_cards = await self._get_bid_cards_for_migration()
            
            if not bid_cards:
                return {
                    "success": False,
                    "message": "No bid cards found for migration"
                }
            
            # Limit batch size in test mode
            if test_mode:
                bid_cards = bid_cards[:batch_size]
                logger.info(f"TEST MODE: Processing only {len(bid_cards)} bid cards")
            
            # Process each bid card
            results = []
            for bid_card in bid_cards:
                result = await self._process_single_bid_card(bid_card)
                results.append(result)
                
                # Log progress
                self.migration_stats["total_processed"] += 1
                if result["success"]:
                    self.migration_stats["successful_categorizations"] += 1
                else:
                    self.migration_stats["failed_categorizations"] += 1
                
                # Brief pause to avoid overwhelming the system
                await asyncio.sleep(0.5)
            
            # Verify contractor_type_ids were populated
            await self._verify_auto_population()
            
            return {
                "success": True,
                "message": f"Migration completed. Processed {len(bid_cards)} bid cards.",
                "stats": self.migration_stats,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Migration error: {e}")
            return {
                "success": False,
                "message": f"Migration failed: {str(e)}",
                "stats": self.migration_stats
            }
    
    async def _load_project_types(self):
        """Load all available project types from database"""
        try:
            self.project_types = await db_select("project_types", limit=500)
            logger.info(f"Loaded {len(self.project_types)} project types for matching")
        except Exception as e:
            logger.error(f"Error loading project types: {e}")
            self.project_types = []
    
    async def _get_bid_cards_for_migration(self) -> List[Dict[str, Any]]:
        """Get bid cards that need categorization - uses Supabase client directly"""
        try:
            # Get all bid cards and filter in Python for empty contractor_type_ids
            all_bid_cards = await db_select("bid_cards", limit=1000)
            
            if not all_bid_cards:
                return []
            
            # Filter bid cards that need migration (empty contractor_type_ids arrays)
            migration_candidates = []
            for card in all_bid_cards:
                contractor_type_ids = card.get('contractor_type_ids', [])
                
                # Check if contractor_type_ids is empty list or None
                if not contractor_type_ids or contractor_type_ids == []:
                    migration_candidates.append({
                        'id': card['id'],
                        'bid_card_number': card['bid_card_number'],
                        'project_type': card.get('project_type'),
                        'title': card.get('title'),
                        'description': card.get('description'),
                        'contractor_type_ids': contractor_type_ids,
                        'service_category': card.get('service_category')
                    })
            
            logger.info(f"Found {len(migration_candidates)} bid cards needing migration out of {len(all_bid_cards)} total")
            return migration_candidates
            
        except Exception as e:
            logger.error(f"Error fetching bid cards for migration: {e}")
            return []
    
    async def _process_single_bid_card(self, bid_card: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single bid card through categorization"""
        try:
            bid_card_id = bid_card['id']
            project_type = bid_card.get('project_type', '')
            title = bid_card.get('title', '')
            description = bid_card.get('description', '')
            
            logger.info(f"Processing bid card {bid_card.get('bid_card_number', bid_card_id)}")
            
            # Check if project_type is already an integer ID (already migrated)
            if isinstance(project_type, int):
                logger.info(f"Bid card {bid_card_id} already has integer project_type {project_type}")
                return {
                    "success": True,
                    "bid_card_id": bid_card_id,
                    "reason": "already_migrated",
                    "message": f"Bid card already has integer project_type: {project_type}",
                    "method": "skip_already_migrated"
                }
            
            # Convert project_type to string for processing
            project_type_str = str(project_type) if project_type else ''
            
            # Determine processing strategy based on available data
            if description and len(description) > 20:
                # Use intelligent categorization for good descriptions
                return await self._intelligent_categorization(bid_card_id, description, title, project_type_str)
            elif title and len(title) > 10:
                # Use title for categorization
                return await self._intelligent_categorization(bid_card_id, title, '', project_type_str)
            elif project_type_str:
                # Try direct mapping for project_type only
                return await self._direct_mapping(bid_card_id, project_type_str)
            else:
                # Insufficient data
                self.migration_stats["skipped_insufficient_data"] += 1
                return {
                    "success": False,
                    "bid_card_id": bid_card_id,
                    "reason": "insufficient_data",
                    "message": "Insufficient data for categorization"
                }
                
        except Exception as e:
            logger.error(f"Error processing bid card {bid_card.get('id', 'unknown')}: {e}")
            return {
                "success": False,
                "bid_card_id": bid_card.get('id'),
                "reason": "processing_error",
                "message": str(e)
            }
    
    async def _intelligent_categorization(self, bid_card_id: str, description: str, title: str = '', original_project_type: str = '') -> Dict[str, Any]:
        """Use GPT-4o for intelligent categorization"""
        try:
            # Combine available text
            full_description = f"{description} {title}".strip()
            context = f"Original project_type: {original_project_type}" if original_project_type else ""
            
            # Use GPT-4o to find best match
            best_match = await self._intelligent_match_project_type(full_description + " " + context, self.project_types)
            
            if not best_match:
                return {
                    "success": False,
                    "bid_card_id": bid_card_id,
                    "reason": "no_match_found",
                    "message": "Could not find suitable project type match"
                }
            
            # Update bid card with new project type
            success = await self._update_bid_card_project_type(bid_card_id, best_match['id'])
            
            if success:
                return {
                    "success": True,
                    "bid_card_id": bid_card_id,
                    "categorization": {
                        "project_type_id": best_match['id'],
                        "project_type_name": best_match['name'],
                        "original_project_type": original_project_type
                    },
                    "method": "intelligent_categorization"
                }
            else:
                return {
                    "success": False,
                    "bid_card_id": bid_card_id,
                    "reason": "database_update_failed",
                    "message": "Could not update bid card in database"
                }
                
        except Exception as e:
            logger.error(f"Intelligent categorization error for {bid_card_id}: {e}")
            return {
                "success": False,
                "bid_card_id": bid_card_id,
                "reason": "categorization_error",
                "message": str(e)
            }
    
    async def _direct_mapping(self, bid_card_id: str, project_type_string: str) -> Dict[str, Any]:
        """Direct mapping for project types that exactly match our system"""
        try:
            # Find exact match
            for pt in self.project_types:
                if pt['name'].lower() == project_type_string.lower():
                    success = await self._update_bid_card_project_type(bid_card_id, pt['id'])
                    
                    if success:
                        self.migration_stats["direct_mappings"] += 1
                        return {
                            "success": True,
                            "bid_card_id": bid_card_id,
                            "categorization": {
                                "project_type_id": pt['id'],
                                "project_type_name": pt['name'],
                                "original_project_type": project_type_string
                            },
                            "method": "direct_mapping"
                        }
                    
            return {
                "success": False,
                "bid_card_id": bid_card_id,
                "reason": "no_direct_match",
                "message": f"No direct match found for '{project_type_string}'"
            }
            
        except Exception as e:
            return {
                "success": False,
                "bid_card_id": bid_card_id,
                "reason": "direct_mapping_error",
                "message": str(e)
            }
    
    async def _intelligent_match_project_type(self, description: str, project_types: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Use OpenAI GPT-4o to intelligently match project type"""
        try:
            # Create list of available project types for GPT
            project_options = []
            for pt in project_types:
                project_options.append({
                    "id": pt['id'],
                    "name": pt['name'],
                    "service_category_id": pt.get('service_category_id', 0)
                })
            
            system_prompt = """You are a project categorization expert for a home improvement platform. Your job is to analyze existing bid card descriptions and match them to the most appropriate project type from available options.

CRITICAL: Pay attention to service categories:
- Installation (1): Installing something new
- Repair (2): Fixing something broken  
- Replacement (3): Replacing existing items
- Renovation (4): Major remodeling projects
- Service (5): Maintenance and service work
- Labor Only (6): Labor-only tasks
- Events (7): Event-related services
- Lifestyle & Wellness (8): Health/wellness services
- Professional (9): Professional services
- Digital (10): Digital/marketing services
- AI Solutions (11): AI-related services

Return only a JSON object with the matching project type ID and confidence score."""

            user_prompt = f"""
Project description: "{description}"

Available project types (showing first 50 for context):
{json.dumps(project_options[:50], indent=2)}

Based on the description, which project type is the best match? Consider both the type of work AND the service category.

Return JSON format:
{{
    "project_type_id": <id>,
    "confidence": <0-100>,
    "reasoning": "<brief explanation>"
}}
"""

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
            
            # Validate response
            project_id = result.get('project_type_id')
            confidence = result.get('confidence', 0)
            reasoning = result.get('reasoning', '')
            
            if confidence < 70:
                logger.warning(f"Low confidence categorization: {confidence}% for description: {description[:100]}")
                return None
            
            # Find matching project type
            for project_type in project_types:
                if project_type['id'] == project_id:
                    logger.info(f"Match found: {project_type['name']} (confidence: {confidence}%) - {reasoning}")
                    return project_type
            
            return None
            
        except Exception as e:
            logger.error(f"Error in intelligent matching: {e}")
            return None
    
    async def _update_bid_card_project_type(self, bid_card_id: str, project_type_id: int) -> bool:
        """Update bid card with project type - triggers will populate contractor_type_ids"""
        try:
            # Update the bid_cards table directly (not potential_bid_cards)
            result = db.client.table("bid_cards").update({
                "project_type": project_type_id,
                "updated_at": datetime.now().isoformat()
            }).eq("id", bid_card_id).execute()
            
            if result.data:
                logger.info(f"Updated bid card {bid_card_id} with project_type: {project_type_id}")
                return True
            else:
                logger.error(f"No rows updated for bid card {bid_card_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating bid card: {e}")
            return False
    
    async def _verify_auto_population(self):
        """Verify that contractor_type_ids were populated by database triggers"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_with_project_type,
                COUNT(CASE WHEN contractor_type_ids IS NOT NULL AND array_length(contractor_type_ids, 1) > 0 THEN 1 END) as total_with_contractor_types
            FROM bid_cards 
            WHERE project_type IS NOT NULL
            """
            
            result = await execute_query(query)
            if result and len(result) > 0:
                stats = result[0]
                logger.info(f"Auto-population verification: {stats['total_with_contractor_types']}/{stats['total_with_project_type']} bid cards have contractor_type_ids")
                return stats
            
        except Exception as e:
            logger.error(f"Error verifying auto-population: {e}")
            
        return None

# Main execution function for testing
async def test_migration():
    """Test the migration tool on a small batch"""
    tool = BidCardMigrationTool()
    result = await tool.migrate_all_bid_cards(test_mode=True, batch_size=3)
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(test_migration())