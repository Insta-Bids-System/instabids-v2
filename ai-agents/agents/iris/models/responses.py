"""
IRIS Response Models
Pydantic models for API responses with consistent structure
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

class IRISResponse(BaseModel):
    """Base IRIS response model"""
    success: bool = Field(default=True, description="Response success status")
    response: str = Field(..., description="Main response text")
    suggestions: Optional[List[str]] = Field(default_factory=list, description="Suggested next actions")
    interface: Optional[str] = Field(None, description="Interface type (homeowner/contractor)")
    
    # Context data
    session_id: Optional[str] = Field(None, description="Chat session ID")
    user_id: Optional[str] = Field(None, description="User ID")
    
    # Action results
    action_results: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Results from actions taken")
    
    # Image processing
    images_processed: Optional[int] = Field(None, description="Number of images processed")
    image_analysis: Optional[Dict[str, Any]] = Field(None, description="Image analysis results")
    
    # Error handling
    error: Optional[str] = Field(None, description="Error message if success=False")

class ContextResponse(BaseModel):
    """User context response model"""
    inspiration_boards: List[Dict[str, Any]] = Field(default_factory=list)
    project_context: Dict[str, Any] = Field(default_factory=dict)
    design_preferences: Dict[str, Any] = Field(default_factory=dict)
    previous_designs: List[Dict[str, Any]] = Field(default_factory=list)
    conversations_from_other_agents: Dict[str, Any] = Field(default_factory=dict)
    photos_from_unified_system: Dict[str, Any] = Field(default_factory=dict)
    privacy_level: str = Field(default="homeowner_side_access")

class BidCardResponse(BaseModel):
    """Bid card operation response"""
    success: bool = Field(default=True)
    action: str = Field(..., description="Action performed")
    message: str = Field(..., description="Human-readable message")
    
    # Optional data
    bid_card: Optional[Dict[str, Any]] = Field(None)
    changed_fields: Optional[List[str]] = Field(None)
    item: Optional[Dict[str, Any]] = Field(None)
    
class RepairItemResponse(BaseModel):
    """Repair item operation response"""
    success: bool = Field(default=True)
    action: str = Field(..., description="Action performed")
    message: str = Field(..., description="Human-readable message")
    
    # Item data
    item: Optional[Dict[str, Any]] = Field(None)
    item_id: Optional[str] = Field(None)
    repair_items: Optional[List[Dict[str, Any]]] = Field(None)
    total_items: Optional[int] = Field(None)
    total_estimated_cost: Optional[float] = Field(None)

class ImageAnalysisResult(BaseModel):
    """Image analysis result model"""
    style_summary: Optional[str] = Field(None)
    primary_colors: Optional[List[str]] = Field(default_factory=list)
    key_elements: Optional[List[str]] = Field(default_factory=list)
    materials_identified: Optional[List[str]] = Field(default_factory=list)
    room_type: Optional[str] = Field(None)
    confidence_score: Optional[float] = Field(None)
    auto_generated_tags: Optional[List[str]] = Field(default_factory=list)
    estimated_style_cost: Optional[Dict[str, str]] = Field(default_factory=dict)
    design_coherence: Optional[float] = Field(None)
    recommendations: Optional[List[str]] = Field(default_factory=list)
    description: Optional[str] = Field(None)  # Added for vision analysis description
    suggestions: Optional[List[str]] = Field(default_factory=list)  # Added for vision suggestions