"""
IRIS Task Manager Service
Manages property maintenance tasks/issues detected from photos
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.database import PropertyTask
from ..utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

class TaskManager:
    """Manages property maintenance tasks and issues"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.contractor_types = {
            # Electrical
            "outlet": "electrical",
            "switch": "electrical", 
            "lighting": "electrical",
            "wiring": "electrical",
            "panel": "electrical",
            
            # Plumbing
            "leak": "plumbing",
            "pipe": "plumbing",
            "faucet": "plumbing",
            "toilet": "plumbing",
            "drain": "plumbing",
            "water damage": "plumbing",
            
            # Painting/Drywall
            "crack": "painting",
            "hole": "drywall",
            "paint": "painting",
            "wall damage": "drywall",
            "ceiling": "painting",
            "stain": "painting",
            
            # HVAC
            "vent": "hvac",
            "heating": "hvac",
            "cooling": "hvac",
            "air conditioning": "hvac",
            "furnace": "hvac",
            
            # Carpentry
            "door": "carpentry",
            "window": "carpentry",
            "cabinet": "carpentry",
            "trim": "carpentry",
            "floor": "flooring",
            
            # Landscaping
            "lawn": "landscaping",
            "tree": "landscaping",
            "drainage": "landscaping",
            "irrigation": "landscaping",
            "fence": "landscaping",
            
            # Roofing
            "roof": "roofing",
            "gutter": "roofing",
            "shingle": "roofing",
            "chimney": "roofing",
            
            # General
            "appliance": "appliance_repair",
            "tile": "tile_contractor",
            "concrete": "concrete",
            "pest": "pest_control"
        }
    
    def create_task_from_image_analysis(
        self,
        user_id: str,
        property_id: str,
        room_id: Optional[str],
        room_type: str,
        image_analysis: Dict[str, Any],
        photo_ids: List[str]
    ) -> PropertyTask:
        """Create a task from image analysis results"""
        
        # Extract issue details from analysis
        detected_issues = image_analysis.get('detected_issues', {})
        description = image_analysis.get('description', '')
        
        # Determine contractor type
        contractor_type = self._determine_contractor_type(description, detected_issues)
        
        # Determine severity
        severity = self._determine_severity(detected_issues)
        
        # Generate title
        title = self._generate_task_title(room_type, contractor_type, detected_issues)
        
        # Create task
        task = PropertyTask(
            id=str(uuid.uuid4()),
            property_id=property_id,
            room_id=room_id,
            room_type=room_type,
            title=title,
            description=description,
            severity=severity,
            contractor_type=contractor_type,
            photo_ids=photo_ids,
            detected_issues=detected_issues,
            status="pending"
        )
        
        # Save to database
        self._save_task(task, user_id)
        
        logger.info(f"Created task {task.id}: {title} ({contractor_type})")
        return task
    
    def _determine_contractor_type(self, description: str, detected_issues: Dict) -> str:
        """Determine which type of contractor is needed"""
        
        text_to_check = f"{description} {str(detected_issues)}".lower()
        
        # Check for specific keywords
        for keyword, contractor in self.contractor_types.items():
            if keyword in text_to_check:
                return contractor
        
        # Default to general handyman
        return "general_handyman"
    
    def _determine_severity(self, detected_issues: Dict) -> str:
        """Determine task severity from detected issues"""
        
        # Look for severity indicators
        issue_text = str(detected_issues).lower()
        
        if any(word in issue_text for word in ["urgent", "dangerous", "hazard", "emergency"]):
            return "urgent"
        elif any(word in issue_text for word in ["major", "significant", "extensive"]):
            return "high"
        elif any(word in issue_text for word in ["minor", "small", "cosmetic"]):
            return "low"
        else:
            return "medium"
    
    def _generate_task_title(self, room_type: str, contractor_type: str, detected_issues: Dict) -> str:
        """Generate a descriptive task title"""
        
        room_display = room_type.replace('_', ' ').title()
        contractor_display = contractor_type.replace('_', ' ').title()
        
        # Try to extract specific issue
        issue_summary = detected_issues.get('summary', '')
        if issue_summary:
            return f"{room_display} - {issue_summary}"
        else:
            return f"{room_display} - {contractor_display} Needed"
    
    def _save_task(self, task: PropertyTask, user_id: str):
        """Save task to database"""
        
        try:
            # Save to property_tasks table
            task_data = task.dict()
            task_data['user_id'] = user_id
            
            self.supabase.table('property_tasks').insert(task_data).execute()
            
            # Update room task count if room_id exists
            if task.room_id:
                self._update_room_task_count(task.room_id)
                
        except Exception as e:
            logger.error(f"Failed to save task: {e}")
            raise
    
    def get_tasks_by_property(self, property_id: str) -> List[PropertyTask]:
        """Get all tasks for a property"""
        
        try:
            response = self.supabase.table('property_tasks')\
                .select('*')\
                .eq('property_id', property_id)\
                .order('created_at', desc=True)\
                .execute()
            
            tasks = []
            for data in response.data:
                tasks.append(PropertyTask(**data))
            
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to get tasks: {e}")
            return []
    
    def get_tasks_by_room(self, room_id: str) -> List[PropertyTask]:
        """Get all tasks for a specific room"""
        
        try:
            response = self.supabase.table('property_tasks')\
                .select('*')\
                .eq('room_id', room_id)\
                .order('created_at', desc=True)\
                .execute()
            
            tasks = []
            for data in response.data:
                tasks.append(PropertyTask(**data))
            
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to get room tasks: {e}")
            return []
    
    def group_tasks_by_contractor(self, property_id: str) -> Dict[str, List[PropertyTask]]:
        """Group pending tasks by contractor type"""
        
        tasks = self.get_tasks_by_property(property_id)
        
        grouped = {}
        for task in tasks:
            if task.status == "pending":
                contractor = task.contractor_type
                if contractor not in grouped:
                    grouped[contractor] = []
                grouped[contractor].append(task)
        
        return grouped
    
    def create_task_group(self, task_ids: List[str], group_name: str) -> str:
        """Create a group of tasks for bundling"""
        
        group_id = str(uuid.uuid4())
        
        try:
            # Update all tasks with group_id
            for task_id in task_ids:
                self.supabase.table('property_tasks')\
                    .update({'group_id': group_id, 'status': 'grouped'})\
                    .eq('id', task_id)\
                    .execute()
            
            logger.info(f"Created task group {group_id} with {len(task_ids)} tasks")
            return group_id
            
        except Exception as e:
            logger.error(f"Failed to create task group: {e}")
            raise
    
    def convert_group_to_bid_card(self, group_id: str, bid_card_id: str):
        """Convert a task group to a bid card"""
        
        try:
            # Update all tasks in group
            self.supabase.table('property_tasks')\
                .update({
                    'potential_bid_card_id': bid_card_id,
                    'status': 'bid_created'
                })\
                .eq('group_id', group_id)\
                .execute()
            
            logger.info(f"Converted group {group_id} to bid card {bid_card_id}")
            
        except Exception as e:
            logger.error(f"Failed to convert group to bid card: {e}")
            raise
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update a task"""
        
        try:
            updates['updated_at'] = datetime.utcnow().isoformat()
            
            self.supabase.table('property_tasks')\
                .update(updates)\
                .eq('id', task_id)\
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        
        try:
            # Get task first to update room count
            response = self.supabase.table('property_tasks')\
                .select('room_id')\
                .eq('id', task_id)\
                .single()\
                .execute()
            
            room_id = response.data.get('room_id') if response.data else None
            
            # Delete task
            self.supabase.table('property_tasks')\
                .delete()\
                .eq('id', task_id)\
                .execute()
            
            # Update room count
            if room_id:
                self._update_room_task_count(room_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            return False
    
    def _update_room_task_count(self, room_id: str):
        """Update the task count for a room"""
        
        try:
            # Get current task count
            response = self.supabase.table('property_tasks')\
                .select('id', count='exact')\
                .eq('room_id', room_id)\
                .execute()
            
            task_count = response.count if hasattr(response, 'count') else 0
            
            # Update room
            self.supabase.table('property_rooms')\
                .update({'task_count': task_count})\
                .eq('id', room_id)\
                .execute()
                
        except Exception as e:
            logger.error(f"Failed to update room task count: {e}")