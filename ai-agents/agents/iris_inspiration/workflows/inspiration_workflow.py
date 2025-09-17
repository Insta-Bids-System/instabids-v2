"""
IRIS Inspiration Image Processing Workflow
Handles inspiration image uploads and style analysis for design boards
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import asyncio
from pathlib import Path

from ..services.memory_manager import MemoryManager
from ..services.inspiration_manager import InspirationManager
from ..services.photo_manager import PhotoManager
from ..models.responses import IRISInspirationResponse, StyleAnalysisResult

logger = logging.getLogger(__name__)

class InspirationImageWorkflow:
    """Handles inspiration image processing workflow"""
    
    def __init__(self):
        self.memory_manager = MemoryManager()
        self.inspiration_manager = InspirationManager()
        self.photo_manager = PhotoManager()
    
    async def process_inspiration_images(
        self,
        user_id: str,
        conversation_id: str,
        session_id: str,
        image_files: List[Dict[str, Any]],
        room_type: Optional[str] = None,
        board_title: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> IRISInspirationResponse:
        """
        Process inspiration images for design boards
        
        Args:
            user_id: User ID
            conversation_id: Conversation ID for memory
            session_id: Current session ID
            image_files: List of image file data
            room_type: Room type for the inspiration
            board_title: Optional board title
            user_context: Previous user preferences
            
        Returns:
            IRISInspirationResponse with style analysis
        """
        try:
            logger.info(f"Processing {len(image_files)} inspiration images for user {user_id}")
            
            # Get or create inspiration board
            board_id = await self._get_or_create_board(
                user_id=user_id,
                room_type=room_type or "general",
                board_title=board_title
            )
            
            if not board_id:
                return IRISInspirationResponse(
                    success=False,
                    response="Failed to create inspiration board",
                    error="Could not create or access inspiration board"
                )
            
            # Process images and analyze style
            image_analyses = []
            uploaded_images = []
            
            for image_file in image_files:
                try:
                    # Analyze image for design elements using PhotoManager vision analysis
                    filename = image_file.get('filename', f'inspiration_{len(uploaded_images)+1}.png')
                    image_data = image_file.get('data') or image_file.get('content', '')
                    
                    # Use PhotoManager for vision analysis
                    vision_analysis = self.photo_manager.analyze_inspiration_images_with_vision(
                        [image_file], 
                        user_context.get('message', '') if user_context else ''
                    )
                    
                    # Convert vision analysis to dict for storage
                    analysis_dict = {
                        'room_type': vision_analysis.room_type,
                        'style_summary': vision_analysis.style_summary,
                        'key_elements': vision_analysis.key_elements,
                        'description': vision_analysis.description,
                        'confidence_score': vision_analysis.confidence_score,
                        'auto_generated_tags': vision_analysis.auto_generated_tags
                    }
                    image_analyses.append(analysis_dict)
                    
                    # Store image using PhotoManager (handles file storage + database)
                    image_id = self.photo_manager.store_inspiration_image(
                        user_id=user_id,
                        board_id=board_id,
                        image_data=image_data,
                        filename=filename,
                        session_id=session_id,
                        tags=vision_analysis.auto_generated_tags,
                        analysis_results=analysis_dict
                    )
                    
                    if image_id:
                        uploaded_images.append({
                            'image_id': image_id,
                            'filename': filename,
                            'analysis': analysis_dict
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing image {image_file.get('filename', 'unknown')}: {e}")
                    continue
            
            if not uploaded_images:
                return IRISInspirationResponse(
                    success=False,
                    response="Failed to process any inspiration images",
                    error="No images could be processed successfully"
                )
            
            # Generate comprehensive style analysis
            combined_analysis = self._generate_comprehensive_style_analysis(
                image_analyses=image_analyses,
                user_context=user_context or {}
            )
            
            # Save style analysis to memory
            await self._save_inspiration_analysis(
                conversation_id=conversation_id,
                session_id=session_id,
                board_id=board_id,
                analysis_results=combined_analysis,
                image_data=uploaded_images
            )
            
            # Generate response with style insights
            response = self._generate_inspiration_response(
                board_id=board_id,
                room_type=room_type or "general",
                style_analysis=combined_analysis,
                images_processed=len(uploaded_images),
                inspiration_items=uploaded_images
            )
            
            logger.info(f"Successfully processed {len(uploaded_images)} inspiration images")
            return response
            
        except Exception as e:
            logger.error(f"Error in inspiration image workflow: {e}")
            return IRISInspirationResponse(
                success=False,
                response="An error occurred while processing your inspiration images",
                error=str(e)
            )
    
    async def _get_or_create_board(
        self,
        user_id: str,
        room_type: str,
        board_title: Optional[str] = None
    ) -> Optional[str]:
        """Get existing board or create new inspiration board"""
        try:
            # Check for existing boards
            user_boards = self.inspiration_manager.get_user_boards(user_id)
            
            # Look for matching room type board that's still collecting
            for board in user_boards:
                if (board.get('room_type') == room_type and 
                    board.get('status') == 'collecting'):
                    logger.info(f"Using existing board {board['id']} for {room_type}")
                    return board['id']
            
            # Create new board
            title = board_title or f"{room_type.replace('_', ' ').title()} Inspiration Board"
            
            board_id = self.inspiration_manager.create_inspiration_board(
                user_id=user_id,
                title=title,
                room_type=room_type,
                description=f"Inspiration collection for {room_type} design"
            )
            
            logger.info(f"Created new inspiration board {board_id}")
            return board_id
            
        except Exception as e:
            logger.error(f"Error creating inspiration board: {e}")
            return None
    
    
    
    
    def _generate_comprehensive_style_analysis(
        self,
        image_analyses: List[Dict[str, Any]],
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive style analysis from multiple images"""
        try:
            # Extract all style elements
            all_elements = []
            all_categories = []
            
            for analysis in image_analyses:
                all_elements.extend(analysis.get('style_elements', []))
                if analysis.get('design_category'):
                    all_categories.append(analysis['design_category'])
            
            # Use inspiration manager for style analysis
            descriptions = [f"Image with {', '.join(analysis.get('style_elements', []))}" 
                          for analysis in image_analyses]
            
            style_analysis = self.inspiration_manager.analyze_style(
                image_descriptions=descriptions,
                user_context=user_context
            )
            
            # Add inspiration-specific data
            style_analysis['inspiration_categories'] = list(set(all_categories))
            style_analysis['total_images'] = len(image_analyses)
            style_analysis['extracted_elements'] = list(set(all_elements))
            style_analysis['analysis_timestamp'] = datetime.utcnow().isoformat()
            
            return style_analysis
            
        except Exception as e:
            logger.error(f"Error generating comprehensive style analysis: {e}")
            return {
                'error': str(e),
                'total_images': len(image_analyses),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
    
    async def _save_inspiration_analysis(
        self,
        conversation_id: str,
        session_id: str,
        board_id: str,
        analysis_results: Dict[str, Any],
        image_data: List[Dict[str, Any]]
    ) -> bool:
        """Save inspiration analysis to memory"""
        try:
            image_urls = [img.get('url', '') for img in image_data]
            
            return self.memory_manager.save_inspiration_analysis(
                conversation_id=conversation_id,
                session_id=session_id,
                board_id=board_id,
                analysis_results=analysis_results,
                image_urls=image_urls
            )
            
        except Exception as e:
            logger.error(f"Error saving inspiration analysis: {e}")
            return False
    
    def _generate_inspiration_response(
        self,
        board_id: str,
        room_type: str,
        style_analysis: Dict[str, Any],
        images_processed: int,
        inspiration_items: List[Dict[str, Any]]
    ) -> IRISInspirationResponse:
        """Generate inspiration response with style insights"""
        
        primary_style = style_analysis.get('primary_style', 'contemporary')
        detected_styles = style_analysis.get('detected_styles', [])
        confidence = style_analysis.get('confidence_score', 0.7)
        
        # Generate personalized response
        if confidence > 0.8:
            response_text = f"I love your {primary_style} inspiration! "
        elif confidence > 0.6:
            response_text = f"I can see {primary_style} influences in your selections. "
        else:
            response_text = "Your inspiration images show an interesting mix of styles. "
        
        if detected_styles:
            style_list = ", ".join(detected_styles[:3])  # Top 3 styles
            response_text += f"I'm detecting elements of {style_list} design. "
        
        response_text += f"These {images_processed} images will be perfect for your {room_type} inspiration board."
        
        # Generate suggestions based on style analysis
        suggestions = style_analysis.get('recommendations', [])
        if not suggestions:
            suggestions = [
                f"Consider exploring more {primary_style} design elements",
                f"Look for complementary pieces that match your {room_type} vision",
                "Think about how these styles might work in your actual space"
            ]
        
        # Extract color palette
        colors = style_analysis.get('color_preferences', [])
        design_elements = style_analysis.get('style_elements', [])
        
        return IRISInspirationResponse(
            success=True,
            response=response_text,
            suggestions=suggestions[:3],  # Limit to top 3
            board_id=board_id,
            style_analysis=style_analysis,
            color_palette=colors,
            design_elements=design_elements,
            images_processed=images_processed,
            inspiration_items=inspiration_items
        )