"""
Image Persistence Service
Handles downloading and storing images permanently in Supabase Storage
Replaces temporary OpenAI URLs with permanent storage URLs
"""
import logging
import os
from datetime import datetime
from typing import Any, Optional

import aiohttp
from dotenv import load_dotenv
from supabase import Client, create_client


# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(env_path, override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImagePersistenceService:
    def __init__(self):
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")

        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.bucket_name = "iris-images"

    async def ensure_bucket_exists(self) -> bool:
        """Ensure the iris-images bucket exists, create if it doesn't"""
        try:
            # Try to get bucket info
            result = self.supabase.storage.get_bucket(self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} already exists")
            return True
        except Exception:
            logger.info(f"Bucket {self.bucket_name} doesn't exist, creating it...")
            try:
                # Create the bucket as public
                result = self.supabase.storage.create_bucket(
                    self.bucket_name,
                    options={"public": True}
                )
                logger.info(f"Created bucket {self.bucket_name}")
                return True
            except Exception as create_error:
                logger.error(f"Failed to create bucket: {create_error}")
                return False

    async def download_and_store_image(self, image_url: str, image_id: str, image_type: str = "png") -> Optional[str]:
        """
        Download image from URL and store it permanently in Supabase Storage
        
        Args:
            image_url: The temporary URL (e.g., OpenAI DALL-E URL)
            image_id: Unique identifier for the image
            image_type: File extension (png, jpg, etc.)
            
        Returns:
            Public URL of the stored image, or None if failed
        """
        try:
            # Ensure bucket exists
            if not await self.ensure_bucket_exists():
                return None

            # Download the image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download image: HTTP {response.status}")
                        return None

                    image_data = await response.read()
                    logger.info(f"Downloaded image: {len(image_data)} bytes")

            # Generate storage path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"iris_visions/{timestamp}_{image_id}.{image_type}"

            # Upload to Supabase Storage
            try:
                result = self.supabase.storage.from_(self.bucket_name).upload(
                    path=file_path,
                    file=image_data,
                    file_options={"content-type": f"image/{image_type}"}
                )
                logger.info(f"Upload successful to path: {file_path}")
            except Exception as upload_error:
                # If file already exists, try with a different name
                if "duplicate" in str(upload_error).lower():
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")
                    file_path = f"iris_visions/{timestamp}_{image_id}.{image_type}"
                    result = self.supabase.storage.from_(self.bucket_name).upload(
                        path=file_path,
                        file=image_data,
                        file_options={"content-type": f"image/{image_type}"}
                    )
                    logger.info(f"Upload successful to alternate path: {file_path}")
                else:
                    logger.error(f"Upload failed: {upload_error}")
                    return None

            # Get public URL
            public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(file_path)
            logger.info(f"Image stored successfully: {public_url}")

            return public_url

        except Exception as e:
            logger.error(f"Error storing image: {e}")
            return None

    async def update_image_record(self, image_id: str, new_url: str) -> bool:
        """Update the database record with the new permanent URL
        
        UPDATED: Now saves to unified_conversation_memory instead of legacy inspiration_images table
        """
        try:
            # Update in unified_conversation_memory table
            result = self.supabase.table("unified_conversation_memory").update({
                "memory_value": {
                    "images": [{
                        "url": new_url,
                        "thumbnail_url": new_url,
                        "updated_at": datetime.now().isoformat()
                    }]
                }
            }).eq("id", image_id).execute()

            if result.data:
                logger.info(f"Updated image record {image_id} in unified memory with permanent URL")
                return True
            else:
                logger.error(f"Failed to update image record {image_id} in unified memory")
                return False

        except Exception as e:
            logger.error(f"Error updating image record in unified memory: {e}")
            return False

    async def make_image_persistent(self, image_id: str, current_url: str) -> Optional[str]:
        """
        Complete flow: download temporary image and make it persistent
        
        Args:
            image_id: Database ID of the image
            current_url: Current temporary URL
            
        Returns:
            New permanent URL or None if failed
        """
        try:
            # Download and store the image
            permanent_url = await self.download_and_store_image(current_url, image_id)

            if not permanent_url:
                return None

            # Update database record
            if await self.update_image_record(image_id, permanent_url):
                return permanent_url
            else:
                return None

        except Exception as e:
            logger.error(f"Error making image persistent: {e}")
            return None

    async def fix_all_expired_images(self) -> dict[str, Any]:
        """
        Find all images with temporary URLs and make them persistent
        
        UPDATED: Now queries unified_conversation_memory for photo_reference entries
        """
        try:
            # Get all photo references from unified memory that might have temporary URLs
            result = self.supabase.table("unified_conversation_memory").select("*").eq(
                "memory_type", "photo_reference"
            ).execute()

            if not result.data:
                return {"success": False, "error": "No images found"}

            fixed_count = 0
            failed_count = 0
            results = []

            for image in result.data:
                image_id = image.get("id")
                memory_value = image.get("memory_value", {})
                # Extract image URL from memory value
                images = memory_value.get("images", [])
                current_url = images[0].get("url", "") if images else ""

                # Check if it's an OpenAI URL (temporary)
                if "oaidalleapiprodscus.blob.core.windows.net" in current_url:
                    logger.info(f"Processing temporary image: {image_id}")

                    # Try to make it persistent
                    permanent_url = await self.make_image_persistent(image_id, current_url)

                    if permanent_url:
                        fixed_count += 1
                        results.append({
                            "id": image_id,
                            "status": "fixed",
                            "new_url": permanent_url
                        })
                    else:
                        failed_count += 1
                        results.append({
                            "id": image_id,
                            "status": "failed",
                            "old_url": current_url
                        })
                else:
                    results.append({
                        "id": image_id,
                        "status": "already_persistent",
                        "url": current_url
                    })

            return {
                "success": True,
                "fixed_count": fixed_count,
                "failed_count": failed_count,
                "total_processed": len(result.data),
                "results": results
            }

        except Exception as e:
            logger.error(f"Error fixing expired images: {e}")
            return {"success": False, "error": str(e)}

    async def save_to_unified_memory(self, 
                                     conversation_id: str, 
                                     image_url: str, 
                                     image_path: str,
                                     metadata: dict = None) -> str:
        """
        Save image reference to unified conversation memory system
        This is the CORRECT way for IRIS to save images!
        
        Args:
            conversation_id: The conversation this image belongs to
            image_url: Public URL of the image (from storage)
            image_path: Storage path of the image
            metadata: Additional image metadata (room_type, style, etc.)
            
        Returns:
            Memory ID if successful, None if failed
        """
        try:
            import uuid
            memory_id = str(uuid.uuid4())
            
            memory_data = {
                "id": memory_id,
                "tenant_id": "00000000-0000-0000-0000-000000000000",
                "conversation_id": conversation_id,
                "memory_scope": "conversation",
                "memory_type": "photo_reference",
                "memory_key": f"iris_image_{datetime.now().timestamp()}",
                "memory_value": {
                    "images": [{
                        "url": image_url,
                        "path": image_path,
                        "thumbnail_url": image_url,  # Can be different if thumbnails generated
                        "metadata": metadata or {},
                        "uploaded_at": datetime.now().isoformat(),
                        "source": "iris_agent"
                    }]
                },
                "importance_score": 8  # High importance for user-uploaded images
            }
            
            result = self.supabase.table("unified_conversation_memory").insert(memory_data).execute()
            
            if result.data:
                logger.info(f"Saved image to unified memory: {memory_id} for conversation {conversation_id}")
                return memory_id
            else:
                logger.error(f"Failed to save image to unified memory")
                return None
                
        except Exception as e:
            logger.error(f"Error saving image to unified memory: {e}")
            return None

# Initialize service instance
image_service = ImagePersistenceService()
