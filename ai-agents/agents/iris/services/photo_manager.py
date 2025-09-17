"""
IRIS Photo Manager Service
Handles all photo upload, storage, and analysis operations
"""

import logging
import base64
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import os

from ..models.database import PhotoStorageEntry
from ..models.responses import ImageAnalysisResult

logger = logging.getLogger(__name__)

class PhotoManager:
    """Manages photo upload, storage, and analysis operations"""
    
    def __init__(self):
        self.base_storage_path = "uploads/iris/"
        # Ensure storage directory exists
        os.makedirs(self.base_storage_path, exist_ok=True)
    
    def store_to_property_photos(
        self, 
        user_id: str, 
        image_data: str, 
        filename: str,
        session_id: str,
        room_id: Optional[str] = None,
        room_type: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """Store image to property_photos table"""
        from database import db
        
        try:
            photo_id = str(uuid.uuid4())
            file_path = self._save_image_file(image_data, filename, photo_id)
            
            # Store in property_photos table
            result = db.client.table('property_photos').insert({
                'id': photo_id,
                'user_id': user_id,
                'file_path': file_path,
                'filename': filename,
                'session_id': session_id,
                'room_id': room_id,
                'room_type': room_type or 'general',
                'tags': tags or [],
                'created_at': datetime.utcnow().isoformat(),
                'metadata': {
                    'source': 'iris_agent',
                    'upload_session': session_id
                }
            }).execute()
            
            if result.data:
                logger.info(f"Photo stored to property_photos: {photo_id}")
                return photo_id
            else:
                logger.error("Failed to store photo to property_photos")
                return None
                
        except Exception as e:
            logger.error(f"Error storing property photo: {e}")
            return None
    
    def store_to_inspiration_board(
        self,
        user_id: str,
        board_id: str,
        image_data: str,
        filename: str,
        session_id: str,
        tags: Optional[List[str]] = None,
        analysis_results: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store image to inspiration_images table"""
        from database import db
        
        try:
            image_id = str(uuid.uuid4())
            file_path = self._save_image_file(image_data, filename, image_id)
            
            # Store in inspiration_images table
            result = db.client.table('inspiration_images').insert({
                'id': image_id,
                'board_id': board_id,
                'user_id': user_id,
                'file_path': file_path,
                'filename': filename,
                'tags': tags or [],
                'analysis_results': analysis_results or {},
                'created_at': datetime.utcnow().isoformat(),
                'metadata': {
                    'source': 'iris_agent',
                    'upload_session': session_id
                }
            }).execute()
            
            if result.data:
                logger.info(f"Image stored to inspiration board: {image_id}")
                return image_id
            else:
                logger.error("Failed to store image to inspiration board")
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
            
            logger.info(f"Image saved to: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving image file: {e}")
            raise
    
    def get_room_id_for_user(self, user_id: str, room_type: str) -> Optional[str]:
        """Get room_id for a user's property based on detected room type"""
        from database import db
        
        try:
            # First get the user's property
            property_result = db.client.table("properties").select("id").eq("user_id", user_id).limit(1).execute()
            
            if not property_result.data:
                logger.warning(f"No property found for user {user_id}")
                return None
            
            property_id = property_result.data[0]["id"]
            
            # Look for room with matching room_type
            room_result = db.client.table("property_rooms").select("id, name, room_type").eq("property_id", property_id).eq("room_type", room_type).limit(1).execute()
            
            if room_result.data:
                room_id = room_result.data[0]["id"]
                logger.info(f"Found room_id: {room_id} for room_type: {room_type}")
                return room_id
            else:
                logger.info(f"No room found for room_type: {room_type}, will use None")
                return None
                
        except Exception as e:
            logger.error(f"Error getting room_id: {e}")
            return None
    
    def analyze_images_with_vision(self, images: List[Dict[str, Any]], message: str) -> ImageAnalysisResult:
        """Analyze images using OpenAI Vision API with real image analysis"""
        import httpx
        import json
        
        analysis = ImageAnalysisResult()
        
        # If no images, fall back to keyword detection
        if not images:
            return self._keyword_based_analysis(message)
        
        try:
            # Use the first image for analysis (can enhance to analyze multiple later)
            first_image = images[0] if isinstance(images, list) else images
            image_data = first_image.get('data') or first_image.get('content')
            
            if not image_data:
                logger.warning("No image data found, falling back to keyword analysis")
                return self._keyword_based_analysis(message)
            
            # Call OpenAI Vision API endpoint
            vision_request = {
                "image_data": image_data,
                "analysis_type": "comprehensive",
                "include_suggestions": True
            }
            
            # Make synchronous call to vision API (running on same server)
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    "http://localhost:8008/api/vision/analyze",
                    json=vision_request
                )
                
                if response.status_code == 200:
                    vision_result = response.json()
                    vision_analysis = vision_result.get('analysis', {})
                    
                    # Map OpenAI Vision results to ImageAnalysisResult
                    analysis.room_type = vision_analysis.get('room_type', 'general')
                    analysis.style_summary = vision_analysis.get('style', 'contemporary')
                    analysis.key_elements = vision_analysis.get('key_elements', [])
                    analysis.description = vision_analysis.get('description', '')
                    
                    # Generate tags from vision analysis
                    tags = []
                    if analysis.room_type and analysis.room_type != 'unspecified':
                        tags.append(analysis.room_type)
                    if analysis.style_summary:
                        style_word = analysis.style_summary.split()[0].lower()
                        tags.append(style_word)
                    tags.extend(analysis.key_elements[:5])  # Add top 5 key elements as tags
                    
                    # Add category suggestions as tags
                    category_tags = vision_result.get('category_suggestions', [])
                    tags.extend(category_tags[:3])
                    
                    analysis.auto_generated_tags = list(set(tags))  # Remove duplicates
                    analysis.confidence_score = 0.95  # High confidence for real vision analysis
                    
                    # Store vision suggestions for later use
                    analysis.suggestions = vision_result.get('suggestions', [])
                    
                    logger.info(f"OpenAI Vision analysis successful: {analysis.room_type} detected with {len(analysis.key_elements)} elements")
                    
                else:
                    logger.error(f"Vision API returned status {response.status_code}: {response.text}")
                    return self._keyword_based_analysis(message)
                    
        except Exception as e:
            logger.error(f"Error calling OpenAI Vision API: {e}")
            # Fall back to keyword analysis
            return self._keyword_based_analysis(message)
        
        return analysis
    
    def _keyword_based_analysis(self, message: str) -> ImageAnalysisResult:
        """Fallback keyword-based analysis when vision API is unavailable"""
        analysis = ImageAnalysisResult()
        message_lower = message.lower()
        
        if "kitchen" in message_lower:
            analysis.room_type = "kitchen"
            analysis.key_elements = ["cabinets", "countertops", "appliances"]
            analysis.auto_generated_tags = ["kitchen", "cabinetry", "countertops"]
        elif "bathroom" in message_lower:
            analysis.room_type = "bathroom"
            analysis.key_elements = ["tiles", "fixtures", "vanity"]
            analysis.auto_generated_tags = ["bathroom", "tiles", "fixtures"]
        elif "bedroom" in message_lower:
            analysis.room_type = "bedroom"
            analysis.key_elements = ["furniture", "decor", "lighting"]
            analysis.auto_generated_tags = ["bedroom", "furniture", "decor"]
        else:
            analysis.room_type = "general"
            analysis.auto_generated_tags = ["inspiration", "design"]
        
        # Style detection
        if any(word in message_lower for word in ["modern", "contemporary"]):
            analysis.auto_generated_tags.append("modern")
            analysis.style_summary = "Modern contemporary style"
        elif any(word in message_lower for word in ["farmhouse", "rustic"]):
            analysis.auto_generated_tags.append("farmhouse")
            analysis.style_summary = "Modern farmhouse style"
        elif any(word in message_lower for word in ["traditional", "classic"]):
            analysis.auto_generated_tags.append("traditional")
            analysis.style_summary = "Traditional classic style"
        
        analysis.confidence_score = 0.7  # Lower confidence for keyword matching
        return analysis
    
    def generate_image_tags(self, room_type: str, message: str, image_count: int = 1) -> List[str]:
        """Generate relevant tags for uploaded images"""
        base_tags = []
        
        # Room-specific tags
        room_tags = {
            "kitchen": ["kitchen", "cabinetry", "countertops", "appliances", "backsplash"],
            "bathroom": ["bathroom", "tiles", "fixtures", "vanity", "shower"],
            "bedroom": ["bedroom", "furniture", "decor", "lighting", "bedding"],
            "living_room": ["living room", "furniture", "seating", "entertainment", "decor"],
            "dining_room": ["dining room", "table", "chairs", "lighting", "decor"],
            "backyard": ["outdoor", "landscaping", "patio", "garden", "exterior"],
            "front_yard": ["outdoor", "landscaping", "curb appeal", "garden", "exterior"]
        }
        
        if room_type.lower() in room_tags:
            base_tags.extend(room_tags[room_type.lower()])
        
        # Style indicators from message
        message_lower = message.lower()
        style_keywords = {
            "modern": ["modern", "contemporary"],
            "farmhouse": ["farmhouse", "rustic", "country"],
            "traditional": ["traditional", "classic", "timeless"],
            "industrial": ["industrial", "urban", "loft"],
            "minimalist": ["minimalist", "simple", "clean"]
        }
        
        for style, keywords in style_keywords.items():
            if any(word in message_lower for word in keywords):
                base_tags.append(style)
        
        # Color indicators
        color_keywords = ["white", "black", "gray", "blue", "green", "red", "brown", "beige"]
        for color in color_keywords:
            if color in message_lower:
                base_tags.append(f"{color} color")
        
        # Material indicators
        material_keywords = ["wood", "stone", "marble", "granite", "tile", "brick", "metal", "glass"]
        for material in material_keywords:
            if material in message_lower:
                base_tags.append(material)
        
        # Mood tags
        if image_count > 1:
            base_tags.append("inspiration collection")
        else:
            base_tags.append("inspiration")
        
        # Remove duplicates and return unique tags
        return list(set(base_tags))