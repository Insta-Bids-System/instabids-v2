"""
IRIS Property Context Builder Service
Gathers comprehensive property context for intelligent conversations
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Use unified database system like other agents
from database_simple import db

logger = logging.getLogger(__name__)

class PropertyContextBuilder:
    """Builds comprehensive property context for IRIS conversations"""
    
    def __init__(self):
        """Initialize with database connection"""
        self.db = db
        self._verify_database_connection()
    
    def _verify_database_connection(self):
        """Verify database connection works - fail loudly if not"""
        try:
            if not (hasattr(self.db, 'client') and self.db.client):
                raise Exception("Database client not properly initialized")
                
            # Test with a simple query to verify connection works
            test_result = self.db.client.table('property_photos').select('id').limit(1).execute()
            logger.info("PropertyContextBuilder database connection verified")
            
        except Exception as e:
            error_msg = f"CRITICAL: PropertyContextBuilder cannot function without database. Error: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    async def get_complete_property_context(self, user_id: str) -> Dict[str, Any]:
        """Get complete property context including all rooms, photos, tasks, and bid cards"""
        try:
            logger.info(f"Building complete property context for user {user_id}")
            
            # Fetch all data first
            properties = await self.get_user_properties(user_id)
            rooms = await self.get_all_rooms_with_descriptions(user_id)
            photos = await self.get_room_photos_with_analysis(user_id)
            tasks = await self.get_property_tasks_all_statuses(user_id)
            bid_cards = await self.get_bid_cards_current_and_past(user_id)
            
            # Compute stats from fetched data (no recursion!)
            stats = self._compute_stats_from_data(rooms, photos, tasks, bid_cards, properties)
            
            context = {
                'user_properties': properties,
                'rooms_with_descriptions': rooms,
                'photos_with_analysis': photos,
                'property_tasks': tasks,
                'bid_cards': bid_cards,
                'property_stats': stats,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Successfully built property context for user {user_id}: "
                       f"{len(context['rooms_with_descriptions'])} rooms, "
                       f"{len(context['photos_with_analysis'])} photos, "
                       f"{len(context['property_tasks'])} tasks, "
                       f"{len(context['bid_cards'])} bid cards")
            
            return context
            
        except Exception as e:
            logger.error(f"Error building property context for user {user_id}: {e}")
            return {
                'error': str(e),
                'user_properties': [],
                'rooms_with_descriptions': [],
                'photos_with_analysis': [],
                'property_tasks': [],
                'bid_cards': [],
                'property_stats': {},
                'generated_at': datetime.utcnow().isoformat()
            }
    
    async def get_user_properties(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all properties for user"""
        try:
            # Query property_rooms to get distinct properties for this user
            result = self.db.client.table('property_rooms').select(
                'user_id, property_address, property_type, created_at'
            ).eq('user_id', user_id).execute()
            
            properties = []
            seen_addresses = set()
            
            for row in result.data or []:
                address = row.get('property_address', 'Unknown Address')
                if address not in seen_addresses:
                    properties.append({
                        'address': address,
                        'property_type': row.get('property_type', 'Unknown'),
                        'first_documented': row.get('created_at'),
                        'user_id': user_id
                    })
                    seen_addresses.add(address)
            
            logger.info(f"Found {len(properties)} properties for user {user_id}")
            return properties
            
        except Exception as e:
            logger.error(f"Error getting user properties: {e}")
            return []
    
    async def get_all_rooms_with_descriptions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get comprehensive room data with descriptions and metadata"""
        try:
            result = self.db.client.table('property_rooms').select('*').eq(
                'user_id', user_id
            ).order('created_at', desc=False).execute()
            
            rooms = []
            for row in result.data or []:
                room_data = {
                    'room_id': row.get('id'),
                    'room_type': row.get('room_type'),
                    'description': row.get('description', ''),
                    'property_address': row.get('property_address'),
                    'room_details': row.get('room_details', {}),
                    'created_at': row.get('created_at'),
                    'updated_at': row.get('updated_at'),
                    'photo_count': 0,  # Will be filled by photo analysis
                    'task_count': 0,   # Will be filled by task analysis
                }
                rooms.append(room_data)
            
            logger.info(f"Found {len(rooms)} rooms for user {user_id}")
            return rooms
            
        except Exception as e:
            logger.error(f"Error getting room descriptions: {e}")
            return []
    
    async def get_room_photos_with_analysis(self, user_id: str) -> List[Dict[str, Any]]:
        """Get photos with AI analysis results"""
        try:
            result = self.db.client.table('property_photos').select('*').eq(
                'user_id', user_id
            ).order('created_at', desc=True).execute()
            
            photos = []
            for row in result.data or []:
                photo_data = {
                    'photo_id': row.get('id'),
                    'room_type': row.get('room_type'),
                    'file_path': row.get('file_path'),
                    'description': row.get('description', ''),
                    'ai_analysis': row.get('ai_analysis', {}),
                    'maintenance_issues': row.get('maintenance_issues', []),
                    'uploaded_at': row.get('created_at'),
                    'conversation_context': row.get('conversation_context', {})
                }
                photos.append(photo_data)
            
            logger.info(f"Found {len(photos)} photos for user {user_id}")
            return photos
            
        except Exception as e:
            logger.error(f"Error getting photos with analysis: {e}")
            return []
    
    async def get_property_tasks_all_statuses(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all property tasks (pending, in_progress, completed)"""
        try:
            # Query PropertyTask model through database
            result = self.db.client.table('property_tasks').select('*').eq(
                'user_id', user_id
            ).order('created_at', desc=True).execute()
            
            tasks = []
            for row in result.data or []:
                task_data = {
                    'task_id': row.get('id'),
                    'title': row.get('title'),
                    'description': row.get('description'),
                    'room_type': row.get('room_type'),
                    'contractor_type': row.get('contractor_type'),
                    'priority': row.get('priority', 'medium'),
                    'status': row.get('status', 'pending'),
                    'estimated_cost_min': row.get('estimated_cost_min'),
                    'estimated_cost_max': row.get('estimated_cost_max'),
                    'timeline_estimate': row.get('timeline_estimate'),
                    'photos': row.get('photos', []),
                    'created_at': row.get('created_at'),
                    'updated_at': row.get('updated_at'),
                    'completion_notes': row.get('completion_notes', ''),
                    'created_from_photo': row.get('created_from_photo', False)
                }
                tasks.append(task_data)
            
            logger.info(f"Found {len(tasks)} tasks for user {user_id}")
            return tasks
            
        except Exception as e:
            logger.error(f"Error getting property tasks: {e}")
            return []
    
    async def get_bid_cards_current_and_past(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all bid cards - both potential and finalized"""
        try:
            bid_cards = []
            
            # Get potential bid cards (created by IRIS)
            potential_result = self.db.client.table('potential_bid_cards').select('*').eq(
                'user_id', user_id
            ).order('created_at', desc=True).execute()
            
            for row in potential_result.data or []:
                bid_card_data = {
                    'bid_card_id': row.get('id'),
                    'type': 'potential',
                    'project_title': row.get('project_title'),
                    'project_type': row.get('project_type'),
                    'description': row.get('description'),
                    'room_type': row.get('room_type'),
                    'urgency_level': row.get('urgency_level'),
                    'budget_min': row.get('budget_min'),
                    'budget_max': row.get('budget_max'),
                    'status': row.get('status', 'draft'),
                    'photos': row.get('photos', []),
                    'tasks_included': row.get('tasks_included', []),
                    'created_at': row.get('created_at'),
                    'updated_at': row.get('updated_at')
                }
                bid_cards.append(bid_card_data)
            
            # Get finalized bid cards (main system)
            finalized_result = self.db.client.table('bid_cards').select('*').eq(
                'homeowner_id', user_id  # Note: might be different field name
            ).order('created_at', desc=True).execute()
            
            for row in finalized_result.data or []:
                bid_card_data = {
                    'bid_card_id': row.get('id'),
                    'type': 'finalized',
                    'project_title': row.get('project_type', 'Project'),
                    'project_type': row.get('project_type'),
                    'description': row.get('project_description', ''),
                    'status': row.get('status', 'unknown'),
                    'budget_min': row.get('budget_min'),
                    'budget_max': row.get('budget_max'),
                    'contractor_count_needed': row.get('contractor_count_needed'),
                    'bids_received_count': row.get('bids_received_count', 0),
                    'created_at': row.get('created_at'),
                    'updated_at': row.get('updated_at')
                }
                bid_cards.append(bid_card_data)
            
            logger.info(f"Found {len(bid_cards)} bid cards for user {user_id}")
            return bid_cards
            
        except Exception as e:
            logger.error(f"Error getting bid cards: {e}")
            return []
    
    def _compute_stats_from_data(self, rooms: List, photos: List, tasks: List, bids: List, properties: List = None) -> Dict[str, Any]:
        """Compute statistics from already-fetched data (no DB calls)"""
        # Calculate room statistics
        room_types = {}
        for room in rooms:
            room_type = room.get('room_type', 'unknown')
            room_types[room_type] = room_types.get(room_type, 0) + 1
        
        # Calculate task statistics
        task_stats = {'pending': 0, 'in_progress': 0, 'completed': 0}
        for task in tasks:
            status = task.get('status', 'pending')
            task_stats[status] = task_stats.get(status, 0) + 1
        
        # Calculate bid card statistics
        bid_card_stats = {'potential': 0, 'finalized': 0}
        for bid_card in bids:
            card_type = bid_card.get('type', 'unknown')
            if card_type in bid_card_stats:
                bid_card_stats[card_type] += 1
        
        stats = {
            'total_properties': len(properties) if properties else 0,
            'total_rooms': len(rooms),
            'total_photos': len(photos),
            'total_tasks': len(tasks),
            'total_bid_cards': len(bids),
            'room_breakdown': room_types,
            'task_breakdown': task_stats,
            'bid_card_breakdown': bid_card_stats,
            'last_activity': datetime.utcnow().isoformat()
        }
        
        return stats
    
    async def get_room_context(self, user_id: str, room_type: Optional[str] = None) -> Dict[str, Any]:
        """Get context for specific room type or all rooms"""
        try:
            complete_context = await self.get_complete_property_context(user_id)
            
            if room_type:
                # Filter for specific room type
                rooms = [r for r in complete_context['rooms_with_descriptions'] 
                        if r.get('room_type', '').lower() == room_type.lower()]
                photos = [p for p in complete_context['photos_with_analysis']
                         if p.get('room_type', '').lower() == room_type.lower()]
                tasks = [t for t in complete_context['property_tasks']
                        if t.get('room_type', '').lower() == room_type.lower()]
                bid_cards = [b for b in complete_context['bid_cards']
                           if b.get('room_type', '').lower() == room_type.lower()]
            else:
                # Return all
                rooms = complete_context['rooms_with_descriptions']
                photos = complete_context['photos_with_analysis']
                tasks = complete_context['property_tasks']
                bid_cards = complete_context['bid_cards']
            
            return {
                'room_type': room_type or 'all',
                'rooms': rooms,
                'photos': photos,
                'tasks': tasks,
                'bid_cards': bid_cards,
                'summary': {
                    'room_count': len(rooms),
                    'photo_count': len(photos),
                    'task_count': len(tasks),
                    'bid_card_count': len(bid_cards)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting room context: {e}")
            return {
                'error': str(e),
                'room_type': room_type or 'all',
                'rooms': [],
                'photos': [],
                'tasks': [],
                'bid_cards': [],
                'summary': {}
            }
