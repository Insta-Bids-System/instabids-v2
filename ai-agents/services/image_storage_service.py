"""
Image Storage Service for Supabase Buckets
Handles upload, thumbnail generation, and URL management
"""

import os
import io
import uuid
import base64
import logging
from typing import Dict, Optional, Tuple
from PIL import Image
from supabase import create_client, Client
from datetime import datetime

logger = logging.getLogger(__name__)

class ImageStorageService:
    """Service for managing image uploads to Supabase Storage buckets"""
    
    def __init__(self):
        """Initialize Supabase client with service role for full access"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.supabase_url or not self.service_role_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        
        self.supabase: Client = create_client(self.supabase_url, self.service_role_key)
        logger.info("ImageStorageService initialized")
    
    async def upload_to_bucket(self, 
                              image_data: bytes, 
                              bucket_name: str,
                              path_prefix: str,
                              filename: str,
                              generate_thumbnail: bool = True) -> Dict:
        """
        Upload image to Supabase Storage bucket with optional thumbnail
        
        Args:
            image_data: Raw image bytes
            bucket_name: Name of the storage bucket
            path_prefix: Path prefix (e.g., "user_id/board_id")
            filename: Original filename
            generate_thumbnail: Whether to generate and upload thumbnail
            
        Returns:
            Dict with URLs and metadata
        """
        try:
            # Generate unique filename to avoid collisions
            file_id = str(uuid.uuid4())
            file_ext = filename.split('.')[-1].lower() if '.' in filename else 'jpg'
            storage_filename = f"{file_id}.{file_ext}"
            
            # Determine content type
            content_type = self._get_content_type(file_ext)
            
            # Upload original image
            original_path = f"{path_prefix}/original/{storage_filename}"
            logger.info(f"Uploading to {bucket_name}/{original_path}")
            
            upload_response = self.supabase.storage.from_(bucket_name).upload(
                original_path,
                image_data,
                {"content-type": content_type}
            )
            
            # Generate and upload thumbnail if requested
            thumbnail_url = None
            thumbnail_path = None
            if generate_thumbnail:
                try:
                    thumbnail_data = self._generate_thumbnail(image_data)
                    thumbnail_path = f"{path_prefix}/thumbnails/{storage_filename}"
                    
                    self.supabase.storage.from_(bucket_name).upload(
                        thumbnail_path,
                        thumbnail_data,
                        {"content-type": "image/jpeg"}
                    )
                    
                    thumbnail_url = self._get_public_url(bucket_name, thumbnail_path)
                    logger.info(f"Thumbnail uploaded to {thumbnail_path}")
                except Exception as e:
                    logger.warning(f"Thumbnail generation failed: {e}")
            
            # Get public URLs
            original_url = self._get_public_url(bucket_name, original_path)
            
            result = {
                "original_url": original_url,
                "thumbnail_url": thumbnail_url,
                "storage_path": original_path,
                "file_id": file_id,
                "filename": storage_filename,
                "original_filename": filename,
                "bucket": bucket_name,
                "size_bytes": len(image_data),
                "uploaded_at": datetime.now().isoformat()
            }
            
            logger.info(f"Successfully uploaded image: {file_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to upload image: {e}")
            raise
    
    async def upload_base64_image(self,
                                 base64_string: str,
                                 bucket_name: str,
                                 path_prefix: str,
                                 filename: str) -> Dict:
        """
        Upload a base64 encoded image to bucket
        
        Args:
            base64_string: Base64 encoded image (with or without data URL prefix)
            bucket_name: Name of the storage bucket
            path_prefix: Path prefix
            filename: Original filename
            
        Returns:
            Dict with URLs and metadata
        """
        try:
            # Remove data URL prefix if present
            if base64_string.startswith('data:'):
                base64_string = base64_string.split(',')[1]
            
            # Decode base64 to bytes
            image_data = base64.b64decode(base64_string)
            
            # Upload using standard method
            return await self.upload_to_bucket(
                image_data=image_data,
                bucket_name=bucket_name,
                path_prefix=path_prefix,
                filename=filename
            )
            
        except Exception as e:
            logger.error(f"Failed to upload base64 image: {e}")
            raise
    
    def _generate_thumbnail(self, image_data: bytes, size: Tuple[int, int] = (150, 150)) -> bytes:
        """
        Generate thumbnail from image data
        
        Args:
            image_data: Original image bytes
            size: Target thumbnail size (width, height)
            
        Returns:
            Thumbnail image bytes
        """
        try:
            # Open image
            img = Image.open(io.BytesIO(image_data))
            
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Generate thumbnail
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85, optimize=True)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")
            raise
    
    def _get_public_url(self, bucket_name: str, path: str) -> str:
        """Generate public URL for stored file"""
        return f"{self.supabase_url}/storage/v1/object/public/{bucket_name}/{path}"
    
    def _get_content_type(self, file_ext: str) -> str:
        """Determine content type from file extension"""
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'bmp': 'image/bmp',
            'svg': 'image/svg+xml'
        }
        return content_types.get(file_ext.lower(), 'image/jpeg')
    
    async def delete_from_bucket(self, bucket_name: str, path: str) -> bool:
        """
        Delete file from bucket
        
        Args:
            bucket_name: Name of the storage bucket
            path: Path to file in bucket
            
        Returns:
            True if successful
        """
        try:
            self.supabase.storage.from_(bucket_name).remove([path])
            logger.info(f"Deleted {bucket_name}/{path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    async def create_bucket_if_not_exists(self, bucket_name: str, public: bool = True) -> bool:
        """
        Create storage bucket if it doesn't exist
        
        Args:
            bucket_name: Name of the bucket to create
            public: Whether bucket should be publicly accessible
            
        Returns:
            True if bucket exists or was created
        """
        try:
            # Try to list files in bucket (will fail if doesn't exist)
            self.supabase.storage.from_(bucket_name).list()
            logger.info(f"Bucket {bucket_name} already exists")
            return True
        except:
            try:
                # Create bucket
                self.supabase.storage.create_bucket(
                    bucket_name,
                    {"public": public}
                )
                logger.info(f"Created bucket: {bucket_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to create bucket: {e}")
                return False

# Singleton instance - create lazily when needed
_image_storage_service = None

def get_image_storage_service():
    """Get or create the singleton image storage service"""
    global _image_storage_service
    if _image_storage_service is None:
        _image_storage_service = ImageStorageService()
    return _image_storage_service