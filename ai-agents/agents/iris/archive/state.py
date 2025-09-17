"""
IRIS Agent State Management
Handles conversation state and context for IRIS
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class IrisConversationState(BaseModel):
    """State for IRIS conversations"""
    user_id: str
    session_id: str
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    current_intent: str = "unknown"
    confidence: float = 0.0
    available_tools: List[str] = Field(default_factory=list)
    
    # Context data
    inspiration_boards: List[Dict[str, Any]] = Field(default_factory=list)
    property_photos: List[Dict[str, Any]] = Field(default_factory=list)
    trade_projects: Dict[str, Any] = Field(default_factory=dict)
    maintenance_issues: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Action tracking
    actions_performed: List[Dict[str, Any]] = Field(default_factory=list)
    pending_actions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Image workflow state
    uploaded_images: List[Dict[str, Any]] = Field(default_factory=list)
    workflow_questions: List[Dict[str, Any]] = Field(default_factory=list)
    workflow_responses: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Potential bid cards
    potential_bid_cards: List[Dict[str, Any]] = Field(default_factory=list)
    active_bid_card_id: Optional[str] = None

class IrisImageContext(BaseModel):
    """Context for image processing"""
    image_upload_session: str
    images_uploaded: int = 0
    successful_analyses: int = 0
    image_categories: List[str] = Field(default_factory=list)
    room_assignments: List[str] = Field(default_factory=list)
    inspiration_board_assignments: List[str] = Field(default_factory=list)
    analysis_summaries: List[Dict[str, Any]] = Field(default_factory=list)
    user_classifications: Optional[Dict[str, Any]] = None

class IrisActionIntent(BaseModel):
    """Intent analysis for actions"""
    requires_action: bool = False
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    action_type: Optional[str] = None
    target_bid_card_id: Optional[str] = None
    confidence: float = 0.0

class IrisMemoryEntry(BaseModel):
    """Memory entry for unified conversation system"""
    conversation_id: Optional[str] = None
    memory_type: str = "iris_context"
    memory_key: str
    memory_value: Dict[str, Any]
    importance_score: int = 5
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

# Intent types
INTENT_TYPES = {
    "photo_analysis": "Analyzing uploaded photos",
    "maintenance_issue": "Handling maintenance and repair issues", 
    "project_management": "Managing projects and bid cards",
    "design_inspiration": "Design and style inspiration",
    "image_classification_response": "Processing image workflow response",
    "general_conversation": "General chat"
}

# Available trade types
AVAILABLE_TRADES = [
    "electrical",
    "plumbing", 
    "painting",
    "flooring",
    "drywall",
    "hvac",
    "roofing",
    "landscaping",
    "carpentry",
    "general"
]

# Project scale categories
PROJECT_SCALES = {
    "small": "Minor repairs or touch-ups",
    "medium": "Standard maintenance or single room updates",
    "large": "Major renovations or multiple room projects"
}

# Urgency levels
URGENCY_LEVELS = {
    "urgent": "Needs immediate attention",
    "high": "Should be addressed soon",
    "medium": "Standard priority",
    "low": "Can be scheduled flexibly"
}