"""
IRIS Inspiration Request Models
Pydantic models for design inspiration API requests with validation
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

class InspirationChatRequest(BaseModel):
    """Main IRIS Inspiration chat request model"""
    user_id: str = Field(..., description="User ID")
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Chat session ID")
    images: Optional[List[ImageData]] = Field(default_factory=list, description="Uploaded inspiration images")
    
    # Board context (inspiration only)
    board_id: Optional[str] = Field(None, description="Inspiration board ID")
    board_title: Optional[str] = Field(None, description="Board title")
    board_room_type: Optional[str] = Field(None, description="Room type for board")
    board_status: Optional[str] = Field(None, description="Board status (collecting/organizing/refining/ready)")
    
    # Design context
    style_preferences: Optional[List[str]] = Field(default_factory=list, description="User's style preferences")
    color_preferences: Optional[List[str]] = Field(default_factory=list, description="Preferred colors")
    design_elements: Optional[List[str]] = Field(default_factory=list, description="Design elements of interest")
    
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
    """Context retrieval request for inspiration"""
    user_id: str = Field(..., description="User ID")
    board_id: Optional[str] = Field(None, description="Optional board ID for filtering")
    
    @validator('user_id')
    def validate_user_id(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('user_id must be a valid UUID')
        return v

class StyleAnalysisRequest(BaseModel):
    """Style analysis request for inspiration images"""
    image_urls: List[str] = Field(..., description="URLs of images to analyze")
    user_id: str = Field(..., description="User ID")
    board_id: Optional[str] = Field(None, description="Board ID if adding to existing board")
    analysis_focus: Optional[str] = Field("general", description="Focus area: general, color, materials, layout")