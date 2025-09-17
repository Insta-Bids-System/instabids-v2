"""
IRIS Inspiration Photo Manager
Handles inspiration image upload, storage, and vision analysis
"""

import logging
import base64
import uuid
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ..models.responses import StyleAnalysisResult

logger = logging.getLogger(__name__)

class PhotoManager:
    """Manages inspiration photo upload, storage, and analysis"""
    
    def __init__(self):
        self.base_storage_path = "uploads/iris_inspiration/"
        # Ensure storage directory exists
        os.makedirs(self.base_storage_path, exist_ok=True)
    
    def store_inspiration_image(
        self, 
        user_id: str, 
        board_id: str,
        image_data: str, 
        filename: str,
        session_id: str,
        tags: Optional[List[str]] = None,
        analysis_results: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store image to inspiration_images table and filesystem"""
        from database import db
        
        try:
            image_id = str(uuid.uuid4())
            file_path = self._save_image_file(image_data, filename, image_id)
            
            # Store in inspiration_images table
            result = db.client.table('inspiration_images').insert({
                'id': image_id,
                'board_id': board_id,
                'user_id': user_id,
                'image_url': file_path,
                'source': 'upload',
                'category': 'inspiration',
                'tags': tags or [],
                'ai_analysis': {
                    'filename': filename,
                    'style_analysis': analysis_results or {},
                    'analyzed_by': 'iris_inspiration_agent',
                    'analysis_timestamp': datetime.utcnow().isoformat(),
                    'upload_session': session_id
                },
                'created_at': datetime.utcnow().isoformat()
            }).execute()
            
            if result.data:
                logger.info(f"Inspiration image stored: {image_id}")
                return image_id
            else:
                logger.error("Failed to store inspiration image")
                return None
                
        except Exception as e:
            logger.error(f"Error storing inspiration image: {e}")
            return None
    
    def _save_image_file(self, image_data: str, filename: str, unique_id: str) -> str:
        """Save base64 image data to file system"""
        try:
            # Clean the base64 data
            if image_data.startswith('data:image/'):
                image_data = image_data.split(',', 1)[1]
            
            # Generate unique filename
            file_extension = os.path.splitext(filename)[1] or '.png'
            unique_filename = f"{unique_id}_{filename.replace(' ', '_')}{file_extension}"
            file_path = os.path.join(self.base_storage_path, unique_filename)
            
            # Decode and save
            image_bytes = base64.b64decode(image_data)
            with open(file_path, 'wb') as f:
                f.write(image_bytes)
            
            logger.info(f"Inspiration image saved to: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving inspiration image file: {e}")
            raise
    
    def analyze_inspiration_images_with_vision(self, images: List[Dict[str, Any]], message: str) -> StyleAnalysisResult:
        """Analyze inspiration images using OpenAI Vision API"""
        import httpx
        
        analysis = StyleAnalysisResult()
        
        # If no images, fall back to keyword detection
        if not images:
            return self._keyword_based_inspiration_analysis(message)
        
        try:
            # Use the first image for analysis
            first_image = images[0] if isinstance(images, list) else images
            
            # Handle both ImageData objects and plain dictionaries
            if hasattr(first_image, 'data'):
                image_data = first_image.data
            elif isinstance(first_image, dict):
                image_data = first_image.get('data') or first_image.get('content')
            else:
                logger.error(f"Unknown image object type: {type(first_image)}")
                return self._keyword_based_inspiration_analysis(message)
            
            if not image_data:
                logger.warning("No image data found, falling back to keyword analysis")
                return self._keyword_based_inspiration_analysis(message)
            
            # Call OpenAI Vision API endpoint for inspiration analysis
            vision_request = {
                "image_data": image_data,
                "analysis_type": "inspiration_analysis",
                "focus": "style_elements_design_mood_color_palette",
                "include_suggestions": True
            }
            
            # Make synchronous call to vision API
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    "http://localhost:8008/api/vision/analyze",
                    json=vision_request
                )
                
                if response.status_code == 200:
                    vision_result = response.json()
                    vision_analysis = vision_result.get('analysis', {})
                    
                    # Map OpenAI Vision results to ImageAnalysisResult for inspiration
                    analysis.room_type = vision_analysis.get('room_type', 'general')
                    analysis.style_summary = vision_analysis.get('style', 'contemporary')
                    analysis.key_elements = vision_analysis.get('design_elements', [])
                    analysis.description = vision_analysis.get('description', '')
                    
                    # Generate inspiration-focused tags
                    tags = []
                    if analysis.style_summary:
                        style_words = analysis.style_summary.split()[:2]
                        tags.extend([word.lower() for word in style_words])
                    tags.extend(analysis.key_elements[:5])
                    tags.extend(['inspiration', 'design-ideas', 'style-reference'])
                    
                    # Add color and mood tags from vision analysis
                    if 'colors' in vision_result:
                        color_tags = [f"{color}-tones" for color in vision_result['colors'][:3]]
                        tags.extend(color_tags)
                    
                    analysis.auto_generated_tags = list(set(tags))
                    analysis.confidence_score = 0.95
                    analysis.suggestions = vision_result.get('style_suggestions', [])
                    
                    logger.info(f"OpenAI Vision inspiration analysis successful: {analysis.style_summary}")
                    
                else:
                    logger.error(f"Vision API returned status {response.status_code}: {response.text}")
                    return self._keyword_based_inspiration_analysis(message)
                    
        except Exception as e:
            logger.error(f"Error calling OpenAI Vision API for inspiration: {e}")
            return self._keyword_based_inspiration_analysis(message)
        
        return analysis
    
    def _keyword_based_inspiration_analysis(self, message: str) -> StyleAnalysisResult:
        """Fallback keyword-based analysis for inspiration images"""
        analysis = StyleAnalysisResult()
        message_lower = message.lower()
        
        # Style detection for inspiration
        if any(word in message_lower for word in ["modern", "contemporary", "sleek"]):
            analysis.style_summary = "Modern contemporary style"
            analysis.auto_generated_tags = ["modern", "contemporary", "inspiration", "design-ideas"]
        elif any(word in message_lower for word in ["farmhouse", "rustic", "country"]):
            analysis.style_summary = "Modern farmhouse style"
            analysis.auto_generated_tags = ["farmhouse", "rustic", "inspiration", "design-ideas"]
        elif any(word in message_lower for word in ["traditional", "classic", "elegant"]):
            analysis.style_summary = "Traditional classic style"
            analysis.auto_generated_tags = ["traditional", "classic", "inspiration", "design-ideas"]
        elif any(word in message_lower for word in ["boho", "bohemian", "eclectic"]):
            analysis.style_summary = "Bohemian eclectic style"
            analysis.auto_generated_tags = ["bohemian", "eclectic", "inspiration", "design-ideas"]
        else:
            analysis.style_summary = "Contemporary design style"
            analysis.auto_generated_tags = ["contemporary", "inspiration", "design-ideas"]
        
        # Room type detection
        if "kitchen" in message_lower:
            analysis.room_type = "kitchen"
            analysis.key_elements = ["cabinetry", "countertops", "backsplash", "lighting"]
        elif "bathroom" in message_lower:
            analysis.room_type = "bathroom"
            analysis.key_elements = ["vanity", "tiles", "fixtures", "mirrors"]
        elif "bedroom" in message_lower:
            analysis.room_type = "bedroom"
            analysis.key_elements = ["furniture", "textiles", "lighting", "decor"]
        elif any(word in message_lower for word in ["living", "family"]):
            analysis.room_type = "living_room"
            analysis.key_elements = ["seating", "lighting", "decor", "layout"]
        else:
            analysis.room_type = "general"
            analysis.key_elements = ["style", "color", "texture", "mood"]
        
        analysis.confidence_score = 0.7
        return analysis