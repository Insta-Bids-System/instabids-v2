#!/usr/bin/env python3
"""
Fixed HomeownerContextAdapter to handle image URLs instead of base64
This ensures when images are retrieved from memory, we only pass URLs to CIA
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class HomeownerContextAdapter:
    """
    Fixed adapter to handle image URLs properly instead of base64 data
    """
    
    def __init__(self, supabase_client=None):
        """Initialize with optional Supabase client"""
        self.supabase = supabase_client
        if not self.supabase:
            logger.warning("No Supabase client provided - limited functionality")
    
    def get_message_attachments(self, message_id: str) -> List[Dict[str, Any]]:
        """Get attachments for a message - returns URLs only, no base64"""
        try:
            result = self.supabase.table("unified_message_attachments").select("*").eq("message_id", message_id).execute()
            attachments = result.data or []
            
            # Clean attachments to ensure only URLs are returned
            cleaned_attachments = []
            for attachment in attachments:
                cleaned = {
                    "id": attachment.get("id"),
                    "url": attachment.get("url"),  # URL from bucket
                    "storage_path": attachment.get("storage_path"),
                    "filename": attachment.get("filename"),
                    "caption": attachment.get("caption", ""),
                    "type": attachment.get("type", "image"),
                    "uploaded_at": attachment.get("created_at")
                }
                # Remove any base64 data if it exists
                if "image_data" in attachment:
                    logger.warning(f"Skipping base64 data for attachment {attachment['id']}")
                cleaned_attachments.append(cleaned)
            
            return cleaned_attachments
        except Exception as e:
            logger.error(f"Error getting attachments: {e}")
            return []
    
    def get_unified_memory(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation memory - ensures image references are URLs only"""
        try:
            result = self.supabase.table("unified_conversation_memory").select("*").eq("conversation_id", conversation_id).execute()
            memories = result.data or []
            
            # Process memories to ensure images are URLs only
            cleaned_memories = []
            for memory in memories:
                if memory.get("memory_type") == "image_upload":
                    # Ensure memory_value contains URL, not base64
                    memory_value = memory.get("memory_value", {})
                    if isinstance(memory_value, dict):
                        # Clean the image memory
                        cleaned_value = {
                            "image_id": memory_value.get("image_id"),
                            "url": memory_value.get("url"),  # URL from bucket
                            "storage_path": memory_value.get("storage_path"),
                            "filename": memory_value.get("filename"),
                            "description": memory_value.get("description"),
                            "uploaded_at": memory_value.get("uploaded_at")
                        }
                        # Remove base64 if it exists
                        if "image_data" in memory_value:
                            logger.warning(f"Removing base64 data from memory {memory['id']}")
                        
                        memory["memory_value"] = cleaned_value
                
                cleaned_memories.append(memory)
            
            return cleaned_memories
        except Exception as e:
            logger.error(f"Error getting unified memory: {e}")
            return []
    
    def get_full_context(
        self, 
        user_id: str,
        conversation_id: Optional[str] = None,
        specific_bid_card_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get complete homeowner context with image URLs only
        """
        context = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "access_level": "full"
        }
        
        # Get conversation context if provided
        if conversation_id:
            # Get messages
            messages = self.get_unified_messages(conversation_id)
            context["messages"] = messages
            
            # Get memory with cleaned image references
            context["memory"] = self.get_unified_memory(conversation_id)
            
            # Get attachments for all messages (URLs only)
            attachments = {}
            for msg in messages:
                msg_id = msg.get("id")
                if msg_id:
                    msg_attachments = self.get_message_attachments(msg_id)
                    if msg_attachments:
                        attachments[msg_id] = msg_attachments
            context["attachments"] = attachments
            
            # Extract image URLs for easy access
            image_urls = []
            for memory in context["memory"]:
                if memory.get("memory_type") == "image_upload":
                    memory_value = memory.get("memory_value", {})
                    if isinstance(memory_value, dict) and memory_value.get("url"):
                        image_urls.append({
                            "url": memory_value["url"],
                            "caption": memory_value.get("description", ""),
                            "uploaded_at": memory_value.get("uploaded_at")
                        })
            
            # Add consolidated image list for CIA agent
            context["image_urls"] = image_urls
            
        logger.info(f"CIA Context loaded: {len(context)} data categories (images as URLs only)")
        return context
    
    def get_unified_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a conversation"""
        try:
            result = self.supabase.table("unified_messages").select("*").eq("conversation_id", conversation_id).order("created_at").execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting unified messages: {e}")
            return []
    
    def save_conversation_with_images(self, conversation_data: Dict[str, Any]) -> bool:
        """
        Save conversation ensuring images are stored as URLs only
        """
        try:
            conversation_id = conversation_data.get("conversation_id", str(uuid.uuid4()))
            
            # Process any images in the conversation
            if "images" in conversation_data:
                for image in conversation_data["images"]:
                    if isinstance(image, dict):
                        # Ensure we're only saving URL references
                        memory_entry = {
                            "id": str(uuid.uuid4()),
                            "conversation_id": conversation_id,
                            "memory_type": "image_upload",
                            "memory_key": f"image_{image.get('id', uuid.uuid4())}",
                            "memory_value": {
                                "image_id": image.get("id"),
                                "url": image.get("url"),  # Only URL!
                                "storage_path": image.get("storage_path"),
                                "filename": image.get("filename"),
                                "description": image.get("description", ""),
                                "uploaded_at": datetime.now().isoformat()
                            },
                            "created_at": datetime.now().isoformat()
                        }
                        
                        # Skip if image has base64 data
                        if "image_data" in image:
                            logger.warning(f"Skipping base64 data when saving image {image.get('id')}")
                        
                        # Save to unified memory
                        self.supabase.table("unified_conversation_memory").insert(memory_entry).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving conversation with images: {e}")
            return False