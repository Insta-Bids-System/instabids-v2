"""
IRIS Inspiration Response Models
Pydantic models for design inspiration API responses with consistent structure
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class IRISInspirationResponse(BaseModel):
    """Base IRIS Inspiration response model"""
    success: bool = Field(default=True, description="Response success status")
    response: str = Field(..., description="Main response text")
    suggestions: Optional[List[str]] = Field(default_factory=list, description="Design-focused suggestions")
    
    # Context data
    session_id: Optional[str] = Field(None, description="Chat session ID")
    user_id: Optional[str] = Field(None, description="User ID")
    board_id: Optional[str] = Field(None, description="Associated inspiration board ID")
    
    # Design analysis results
    style_analysis: Optional[Dict[str, Any]] = Field(None, description="Style analysis results")
    color_palette: Optional[List[str]] = Field(default_factory=list, description="Extracted color palette")
    design_elements: Optional[List[str]] = Field(default_factory=list, description="Identified design elements")
    
    # Image processing
    images_processed: Optional[int] = Field(None, description="Number of inspiration images processed")
    inspiration_items: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Generated inspiration items")
    
    # Error handling
    error: Optional[str] = Field(None, description="Error message if success=False")

class InspirationContextResponse(BaseModel):
    """User inspiration context response model"""
    inspiration_boards: List[Dict[str, Any]] = Field(default_factory=list, description="User's inspiration boards")
    style_preferences: Dict[str, Any] = Field(default_factory=dict, description="Learned style preferences")
    favorite_colors: List[str] = Field(default_factory=list, description="Preferred colors")
    design_history: List[Dict[str, Any]] = Field(default_factory=list, description="Previous design explorations")
    room_types: List[str] = Field(default_factory=list, description="Room types user has explored")

class StyleAnalysisResult(BaseModel):
    """Style analysis result model for inspiration images"""
    overall_style: Optional[str] = Field(None, description="Identified design style")
    style_confidence: Optional[float] = Field(None, description="Confidence in style identification")
    
    # Visual elements
    primary_colors: List[str] = Field(default_factory=list, description="Main colors in the design")
    secondary_colors: List[str] = Field(default_factory=list, description="Accent colors")
    materials_identified: List[str] = Field(default_factory=list, description="Materials spotted")
    furniture_styles: List[str] = Field(default_factory=list, description="Furniture style elements")
    
    # Design characteristics
    mood_descriptors: List[str] = Field(default_factory=list, description="Words describing the mood/feeling")
    key_features: List[str] = Field(default_factory=list, description="Standout design features")
    lighting_style: Optional[str] = Field(None, description="Lighting approach")
    
    # Recommendations
    style_suggestions: List[str] = Field(default_factory=list, description="Style recommendations")
    similar_styles: List[str] = Field(default_factory=list, description="Related design styles")
    complementary_elements: List[str] = Field(default_factory=list, description="Elements that would complement this style")
    
    # Auto-generated tags for organization
    auto_tags: List[str] = Field(default_factory=list, description="Tags for organizing this inspiration")

class InspirationBoardResponse(BaseModel):
    """Inspiration board operation response"""
    success: bool = Field(default=True)
    action: str = Field(..., description="Action performed (created/updated/analyzed)")
    message: str = Field(..., description="Human-readable message")
    
    # Board data
    board: Optional[Dict[str, Any]] = Field(None, description="Board information")
    board_id: Optional[str] = Field(None, description="Board ID")
    images_added: Optional[int] = Field(None, description="Number of images added")
    board_analysis: Optional[Dict[str, Any]] = Field(None, description="Board-wide style analysis")