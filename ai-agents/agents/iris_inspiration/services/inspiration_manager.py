"""
Inspiration Manager Service
Handles inspiration board creation, image analysis, and style management
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class InspirationManager:
    """Manages inspiration boards and style analysis"""
    
    def __init__(self):
        self.supported_styles = [
            "modern", "farmhouse", "traditional", "contemporary", "industrial",
            "scandinavian", "bohemian", "minimalist", "rustic", "transitional"
        ]
    
    def create_inspiration_board(
        self,
        user_id: str,
        title: str,
        room_type: str,
        description: Optional[str] = None
    ) -> str:
        """
        Create a new inspiration board
        
        Returns:
            Board ID if successful
        """
        try:
            from database import db
            
            board_id = str(uuid.uuid4())
            
            board_data = {
                'id': board_id,
                'user_id': user_id,
                'homeowner_id': user_id,  # Both fields exist in schema
                'title': title,
                'description': description or f"Inspiration board for {room_type} design",
                'room_type': room_type,
                'status': 'collecting',
                'ai_insights': {
                    'created_by': 'iris_inspiration_agent',
                    'room_type': room_type,
                    'auto_generated': True
                },
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            db.client.table('inspiration_boards').insert(board_data).execute()
            
            logger.info(f"Created inspiration board: {board_id} for user: {user_id}")
            return board_id
            
        except Exception as e:
            logger.error(f"Error creating inspiration board: {e}")
            raise
    
    def get_user_boards(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all inspiration boards for a user"""
        try:
            from database import db
            
            result = db.client.table('inspiration_boards').select(
                '*'
            ).eq('user_id', user_id).order('created_at', desc=True).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching user boards: {e}")
            return []
    
    def add_image_to_board(
        self,
        board_id: str,
        user_id: str,
        image_url: str,
        filename: str,
        style_analysis: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Add an image to an inspiration board
        
        Returns:
            Image ID if successful
        """
        try:
            from database import db
            
            image_data = {
                'board_id': board_id,
                'user_id': user_id,
                'image_url': image_url,
                'source': 'upload',
                'category': 'inspiration',  # Always inspiration for this agent
                'tags': tags or [],
                'ai_analysis': {
                    'filename': filename,
                    'style_analysis': style_analysis or {},
                    'analyzed_by': 'iris_inspiration_agent',
                    'analysis_timestamp': datetime.utcnow().isoformat()
                },
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = db.client.table('inspiration_images').insert(image_data).select().execute()
            
            if result.data:
                image_id = result.data[0]['id']
                logger.info(f"Added image {image_id} to board {board_id}")
                return image_id
            else:
                raise Exception("Failed to insert image record")
                
        except Exception as e:
            logger.error(f"Error adding image to board: {e}")
            raise
    
    def analyze_style(
        self,
        image_descriptions: List[str],
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze style from image descriptions and user context
        
        Args:
            image_descriptions: List of image analysis descriptions
            user_context: Previous style preferences and history
            
        Returns:
            Style analysis results
        """
        try:
            # Combine descriptions for analysis
            combined_description = " ".join(image_descriptions)
            
            # Extract style keywords
            style_keywords = []
            for style in self.supported_styles:
                if style.lower() in combined_description.lower():
                    style_keywords.append(style)
            
            # Determine primary style
            primary_style = style_keywords[0] if style_keywords else "contemporary"
            
            # Generate analysis
            analysis = {
                'primary_style': primary_style,
                'detected_styles': style_keywords,
                'confidence_score': 0.8 if style_keywords else 0.5,
                'style_elements': self._extract_style_elements(combined_description),
                'color_preferences': self._extract_colors(combined_description),
                'design_mood': self._determine_mood(combined_description),
                'recommendations': self._generate_style_recommendations(primary_style)
            }
            
            logger.info(f"Style analysis complete: {primary_style} ({len(style_keywords)} styles detected)")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing style: {e}")
            return {
                'primary_style': 'contemporary',
                'detected_styles': [],
                'confidence_score': 0.0,
                'error': str(e)
            }
    
    def generate_inspiration_tags(
        self,
        room_type: str,
        style_analysis: Dict[str, Any],
        user_preferences: Optional[List[str]] = None
    ) -> List[str]:
        """Generate relevant tags for inspiration organization"""
        
        tags = []
        
        # Room type tags
        tags.append(f"{room_type.replace('_', '-')}")
        
        # Style tags
        if 'primary_style' in style_analysis:
            tags.append(style_analysis['primary_style'])
        
        if 'detected_styles' in style_analysis:
            tags.extend(style_analysis['detected_styles'])
        
        # Color tags
        if 'color_preferences' in style_analysis:
            for color in style_analysis['color_preferences'][:3]:  # Limit to top 3 colors
                tags.append(f"{color}-tones")
        
        # User preference tags
        if user_preferences:
            tags.extend(user_preferences[:3])  # Limit to top 3
        
        # Standard inspiration tags
        tags.extend(['inspiration', 'design-ideas', 'style-reference'])
        
        # Remove duplicates and return
        return list(set(tags))
    
    def _extract_style_elements(self, description: str) -> List[str]:
        """Extract design elements from description"""
        elements = []
        
        element_keywords = {
            'lighting': ['pendant', 'chandelier', 'sconce', 'recessed', 'natural light'],
            'materials': ['marble', 'granite', 'wood', 'stone', 'metal', 'glass'],
            'fixtures': ['cabinet', 'countertop', 'backsplash', 'hardware', 'faucet'],
            'colors': ['white', 'black', 'gray', 'blue', 'green', 'warm', 'cool']
        }
        
        desc_lower = description.lower()
        for category, keywords in element_keywords.items():
            found_keywords = [kw for kw in keywords if kw in desc_lower]
            if found_keywords:
                elements.extend(found_keywords)
        
        return elements[:10]  # Limit to top 10 elements
    
    def _extract_colors(self, description: str) -> List[str]:
        """Extract color preferences from description"""
        colors = []
        color_words = [
            'white', 'black', 'gray', 'grey', 'blue', 'green', 'red', 
            'yellow', 'brown', 'beige', 'cream', 'navy', 'gold'
        ]
        
        desc_lower = description.lower()
        for color in color_words:
            if color in desc_lower:
                colors.append(color)
        
        return colors[:5]  # Limit to top 5 colors
    
    def _determine_mood(self, description: str) -> str:
        """Determine design mood from description"""
        mood_keywords = {
            'elegant': ['elegant', 'sophisticated', 'refined', 'luxurious'],
            'cozy': ['cozy', 'warm', 'comfortable', 'inviting', 'homey'],
            'modern': ['modern', 'contemporary', 'sleek', 'clean', 'minimal'],
            'rustic': ['rustic', 'farmhouse', 'country', 'natural', 'organic'],
            'dramatic': ['dramatic', 'bold', 'striking', 'statement']
        }
        
        desc_lower = description.lower()
        for mood, keywords in mood_keywords.items():
            if any(keyword in desc_lower for keyword in keywords):
                return mood
        
        return 'contemporary'  # Default mood
    
    def _generate_style_recommendations(self, primary_style: str) -> List[str]:
        """Generate style-specific recommendations"""
        recommendations = {
            'modern': [
                'Focus on clean lines and minimal ornamentation',
                'Use neutral color palette with bold accent pieces',
                'Incorporate natural materials like wood and stone'
            ],
            'farmhouse': [
                'Mix vintage and new pieces for authentic feel',
                'Use white or cream as primary color with wood accents',
                'Add shiplap or beadboard for texture'
            ],
            'traditional': [
                'Choose rich, warm colors and classic patterns',
                'Invest in quality wood furniture and fixtures',
                'Layer textures through fabrics and accessories'
            ],
            'contemporary': [
                'Balance comfort with style in furniture choices',
                'Use a mix of textures for visual interest',
                'Keep color palette cohesive throughout space'
            ]
        }
        
        return recommendations.get(primary_style, recommendations['contemporary'])