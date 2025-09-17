"""
IRIS Database Models
Models for database operations and memory management
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class MemoryType(str, Enum):
    """Types of memory entries"""
    PROPERTY_ISSUE = "property_issue"
    ROOM_DOCUMENTATION = "room_documentation"
    TASK_CREATED = "task_created"
    PHOTO_REFERENCE = "photo_reference"
    IMAGE_ANALYSIS = "image_analysis"
    CONVERSATION_CONTEXT = "conversation_context"

class PhotoStorageEntry(BaseModel):
    """Model for photo storage operations"""
    user_id: str = Field(..., description="User ID")
    image_data: str = Field(..., description="Base64 image data")
    filename: str = Field(..., description="Filename")
    session_id: str = Field(..., description="Session ID")
    room_id: Optional[str] = Field(None, description="Room ID for property photos")
    
    # Metadata
    room_type: Optional[str] = Field(None, description="Detected room type")
    tags: Optional[List[str]] = Field(default_factory=list, description="Auto-generated tags")
    analysis_results: Optional[Dict[str, Any]] = Field(None, description="Image analysis results")

class MemoryEntry(BaseModel):
    """Model for unified conversation memory entries"""
    conversation_id: str = Field(..., description="Conversation ID")
    memory_type: MemoryType = Field(..., description="Type of memory")
    memory_key: str = Field(..., description="Memory key")
    memory_value: Dict[str, Any] = Field(..., description="Memory value")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class ConversationMessage(BaseModel):
    """Model for conversation messages"""
    conversation_id: str = Field(..., description="Conversation ID")
    sender: str = Field(..., description="Message sender (user/assistant)")
    content: str = Field(..., description="Message content")
    message_type: Optional[str] = Field("text", description="Message type")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class PropertyRoom(BaseModel):
    """Model for property rooms"""
    id: str = Field(..., description="Room ID")
    property_id: str = Field(..., description="Property ID")
    name: str = Field(..., description="Room name")
    room_type: str = Field(..., description="Room type")
    description: Optional[str] = Field(None, description="Room description")
    photo_count: Optional[int] = Field(0, description="Number of photos")
    task_count: Optional[int] = Field(0, description="Number of tasks/issues")

class PropertyTask(BaseModel):
    """Model for property maintenance tasks/issues"""
    id: str = Field(..., description="Task ID")
    property_id: str = Field(..., description="Property ID")
    room_id: Optional[str] = Field(None, description="Room ID")
    room_type: str = Field(..., description="Room type")
    
    # Task details
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Detailed description")
    severity: str = Field(default="medium", description="Severity: low, medium, high, urgent")
    contractor_type: str = Field(..., description="Type of contractor needed")
    
    # Photo evidence
    photo_ids: List[str] = Field(default_factory=list, description="Related photo IDs")
    detected_issues: Optional[Dict[str, Any]] = Field(None, description="AI-detected issues")
    
    # Grouping and status
    group_id: Optional[str] = Field(None, description="Task group ID for bundling")
    potential_bid_card_id: Optional[str] = Field(None, description="Associated bid card")
    status: str = Field(default="pending", description="Status: pending, grouped, bid_created")
    
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class PotentialBidCard(BaseModel):
    """Model for potential bid cards"""
    id: str = Field(..., description="Bid card ID")
    user_id: str = Field(..., description="User ID")
    title: Optional[str] = Field(None, description="Project title")
    primary_trade: Optional[str] = Field(None, description="Primary trade")
    estimated_timeline: Optional[str] = Field(None, description="Timeline")
    urgency_level: Optional[str] = Field(None, description="Urgency level")
    user_scope_notes: Optional[str] = Field(None, description="User scope notes")
    ai_analysis: Optional[Dict[str, Any]] = Field(default_factory=dict, description="AI analysis data")
    completion_percentage: Optional[float] = Field(0.0, description="Completion percentage")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)