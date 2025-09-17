"""
IRIS Request Models
Pydantic models for API requests with validation
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
import uuid

class ImageData(BaseModel):
    """Single image data model"""
    data: str = Field(..., description="Base64 encoded image data")
    filename: Optional[str] = Field(None, description="Original filename")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class UnifiedChatRequest(BaseModel):
    """Main IRIS chat request model"""
    user_id: str = Field(..., description="User ID")
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Chat session ID")
    images: Optional[List[ImageData]] = Field(default_factory=list, description="Uploaded images")
    
    # Board context
    board_id: Optional[str] = Field(None, description="Inspiration board ID")
    board_title: Optional[str] = Field(None, description="Board title")
    board_room_type: Optional[str] = Field(None, description="Room type for board")
    board_status: Optional[str] = Field(None, description="Board status (collecting/organizing/refining/ready)")
    
    # Action intents
    action_intent: Optional[str] = Field(None, description="Specific action requested")
    bid_card_id: Optional[str] = Field(None, description="Associated bid card ID")
    
    @validator('user_id')
    def validate_user_id(cls, v):
        """Validate user_id is a valid UUID format"""
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('user_id must be a valid UUID')
        return v
    
    @validator('board_status')
    def validate_board_status(cls, v):
        """Validate board status is one of allowed values"""
        if v and v not in ['collecting', 'organizing', 'refining', 'ready']:
            raise ValueError('board_status must be one of: collecting, organizing, refining, ready')
        return v

class ContextRequest(BaseModel):
    """Context retrieval request"""
    user_id: str = Field(..., description="User ID")
    project_id: Optional[str] = Field(None, description="Optional project ID for filtering")
    
    @validator('user_id')
    def validate_user_id(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('user_id must be a valid UUID')
        return v

class BidCardUpdateRequest(BaseModel):
    """Bid card update request via action system"""
    bid_card_id: str = Field(..., description="Bid card ID to update")
    field_updates: Dict[str, Any] = Field(..., description="Fields to update")
    user_id: str = Field(..., description="User ID")
    
class RepairItemRequest(BaseModel):
    """Repair item management request"""
    potential_bid_card_id: str = Field(..., description="Potential bid card ID")
    item_description: str = Field(..., description="Description of repair item")
    severity: Optional[str] = Field("medium", description="Severity level")
    category: Optional[str] = Field("general", description="Repair category")
    estimated_cost: Optional[float] = Field(0.0, description="Estimated cost")
    user_id: Optional[str] = Field(None, description="User ID")

class ToolSuggestionRequest(BaseModel):
    """Tool suggestion request"""
    tool_name: str = Field(..., description="Name of the tool")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")