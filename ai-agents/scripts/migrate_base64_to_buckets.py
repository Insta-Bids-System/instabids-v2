#!/usr/bin/env python3
"""
Migration Script: Convert Base64 Images to Supabase Storage Buckets
Migrates existing base64 images from database to bucket storage
"""

import os
import sys
import asyncio
import base64
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from services.image_storage_service import ImageStorageService
from database_simple import db
from supabase import create_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Base64ToBucketMigration:
    """Migrate base64 images from database to Supabase Storage buckets"""
    
    def __init__(self):
        self.storage_service = ImageStorageService()
        self.stats = {
            'property_photos_migrated': 0,
            'inspiration_images_migrated': 0,
            'errors': 0,
            'skipped': 0,
            'total_size_freed': 0
        }
    
    async def create_buckets_if_needed(self):
        """Ensure storage buckets exist"""
        logger.info("Checking/creating storage buckets...")
        
        buckets = ['property-photos', 'inspiration-images']
        for bucket in buckets:
            success = await self.storage_service.create_bucket_if_not_exists(bucket, public=True)
            if success:
                logger.info(f"✅ Bucket '{bucket}' ready")
            else:
                logger.error(f"❌ Failed to create/verify bucket '{bucket}'")
                return False
        
        return True
    
    async def migrate_property_photos(self):
        """Migrate property photos from base64 to bucket storage"""
        logger.info("\n=== Migrating Property Photos ===")
        
        try:
            # Get all property photos with base64 data
            photos = db.client.table("property_photos")\
                .select("*")\
                .like("photo_url", "data:image%")\
                .execute()
            
            if not photos.data:
                logger.info("No base64 property photos found to migrate")
                return
            
            logger.info(f"Found {len(photos.data)} property photos to migrate")
            
            for photo in photos.data:
                try:
                    photo_id = photo['id']
                    property_id = photo['property_id']
                    original_filename = photo.get('original_filename', f"photo_{photo_id}.jpg")
                    
                    # Extract base64 data
                    base64_url = photo['photo_url']
                    if ',' in base64_url:
                        base64_data = base64_url.split(',')[1]
                    else:
                        base64_data = base64_url
                    
                    # Calculate size freed
                    size_freed = len(base64_data)
                    self.stats['total_size_freed'] += size_freed
                    
                    # Upload to bucket
                    logger.info(f"Migrating photo {photo_id} ({size_freed:,} bytes)...")
                    
                    storage_result = await self.storage_service.upload_base64_image(
                        base64_string=base64_data,
                        bucket_name="property-photos",
                        path_prefix=f"{property_id}/migrated",
                        filename=original_filename
                    )
                    
                    # Update database record with URLs
                    update_data = {
                        "photo_url": storage_result["original_url"],
                        "ai_classification": {
                            **(photo.get("ai_classification", {})),
                            "migrated_from_base64": True,
                            "migration_date": datetime.now().isoformat(),
                            "storage_path": storage_result["storage_path"],
                            "file_id": storage_result["file_id"],
                            "thumbnail_url": storage_result.get("thumbnail_url")
                        }
                    }
                    
                    db.client.table("property_photos")\
                        .update(update_data)\
                        .eq("id", photo_id)\
                        .execute()
                    
                    self.stats['property_photos_migrated'] += 1
                    logger.info(f"✅ Migrated photo {photo_id} to bucket")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to migrate photo {photo.get('id')}: {e}")
                    self.stats['errors'] += 1
                    
        except Exception as e:
            logger.error(f"Error during property photos migration: {e}")
    
    async def migrate_inspiration_images(self):
        """Migrate inspiration images from base64 to bucket storage"""
        logger.info("\n=== Migrating Inspiration Images ===")
        
        try:
            # Get all inspiration images with base64 data
            images = db.client.table("inspiration_images")\
                .select("*")\
                .like("image_url", "data:image%")\
                .execute()
            
            if not images.data:
                logger.info("No base64 inspiration images found to migrate")
                return
            
            logger.info(f"Found {len(images.data)} inspiration images to migrate")
            
            for image in images.data:
                try:
                    image_id = image['id']
                    board_id = image.get('board_id')
                    user_id = image.get('user_id') or image.get('homeowner_id')
                    
                    # Get original filename from AI analysis if available
                    ai_analysis = image.get('ai_analysis', {})
                    original_filename = ai_analysis.get('original_filename', f"inspiration_{image_id}.jpg")
                    
                    # Extract base64 data
                    base64_url = image['image_url']
                    if ',' in base64_url:
                        base64_data = base64_url.split(',')[1]
                    else:
                        base64_data = base64_url
                    
                    # Calculate size freed
                    size_freed = len(base64_data)
                    self.stats['total_size_freed'] += size_freed
                    
                    # Upload to bucket
                    logger.info(f"Migrating inspiration image {image_id} ({size_freed:,} bytes)...")
                    
                    path_prefix = f"{user_id}/{board_id}" if board_id else f"{user_id}/general"
                    
                    storage_result = await self.storage_service.upload_base64_image(
                        base64_string=base64_data,
                        bucket_name="inspiration-images",
                        path_prefix=path_prefix,
                        filename=original_filename
                    )
                    
                    # Update database record with URLs
                    update_data = {
                        "image_url": storage_result["original_url"],
                        "thumbnail_url": storage_result.get("thumbnail_url"),
                        "ai_analysis": {
                            **ai_analysis,
                            "migrated_from_base64": True,
                            "migration_date": datetime.now().isoformat(),
                            "storage_path": storage_result["storage_path"],
                            "file_id": storage_result["file_id"]
                        }
                    }
                    
                    db.client.table("inspiration_images")\
                        .update(update_data)\
                        .eq("id", image_id)\
                        .execute()
                    
                    self.stats['inspiration_images_migrated'] += 1
                    logger.info(f"✅ Migrated inspiration image {image_id} to bucket")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to migrate image {image.get('id')}: {e}")
                    self.stats['errors'] += 1
                    
        except Exception as e:
            logger.error(f"Error during inspiration images migration: {e}")
    
    async def verify_migration(self):
        """Verify migration was successful"""
        logger.info("\n=== Verifying Migration ===")
        
        # Check for remaining base64 images
        remaining_property = db.client.table("property_photos")\
            .select("id")\
            .like("photo_url", "data:image%")\
            .execute()
        
        remaining_inspiration = db.client.table("inspiration_images")\
            .select("id")\
            .like("image_url", "data:image%")\
            .execute()
        
        remaining_count = len(remaining_property.data or []) + len(remaining_inspiration.data or [])
        
        if remaining_count == 0:
            logger.info("✅ All base64 images successfully migrated!")
        else:
            logger.warning(f"⚠️ {remaining_count} base64 images still remain in database")
        
        # Check migrated images have valid URLs
        migrated_property = db.client.table("property_photos")\
            .select("id, photo_url")\
            .like("photo_url", "https://%")\
            .execute()
        
        migrated_inspiration = db.client.table("inspiration_images")\
            .select("id, image_url")\
            .like("image_url", "https://%")\
            .execute()
        
        migrated_count = len(migrated_property.data or []) + len(migrated_inspiration.data or [])
        logger.info(f"✅ {migrated_count} images now using bucket storage URLs")
    
    async def run_migration(self, dry_run=False):
        """Run the complete migration"""
        logger.info("=" * 60)
        logger.info("BASE64 TO BUCKET MIGRATION")
        logger.info("=" * 60)
        
        if dry_run:
            logger.info("🔍 DRY RUN MODE - No changes will be made")
            await self.analyze_current_state()
            return
        
        # Create buckets if needed
        if not await self.create_buckets_if_needed():
            logger.error("Failed to create/verify buckets. Aborting migration.")
            return
        
        # Run migrations
        await self.migrate_property_photos()
        await self.migrate_inspiration_images()
        
        # Verify results
        await self.verify_migration()
        
        # Print summary
        self.print_summary()
    
    async def analyze_current_state(self):
        """Analyze current state without making changes"""
        logger.info("\n=== Current State Analysis ===")
        
        # Count base64 images
        property_photos = db.client.table("property_photos")\
            .select("photo_url")\
            .like("photo_url", "data:image%")\
            .execute()
        
        inspiration_images = db.client.table("inspiration_images")\
            .select("image_url")\
            .like("image_url", "data:image%")\
            .execute()
        
        # Calculate sizes
        property_size = sum(len(p['photo_url']) for p in (property_photos.data or []))
        inspiration_size = sum(len(i['image_url']) for i in (inspiration_images.data or []))
        
        logger.info(f"Property Photos with base64: {len(property_photos.data or [])} ({property_size:,} bytes)")
        logger.info(f"Inspiration Images with base64: {len(inspiration_images.data or [])} ({inspiration_size:,} bytes)")
        logger.info(f"Total database bloat: {(property_size + inspiration_size):,} bytes")
        logger.info(f"Estimated egress per API call: {(property_size + inspiration_size):,} bytes")
    
    def print_summary(self):
        """Print migration summary"""
        logger.info("\n" + "=" * 60)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Property Photos Migrated: {self.stats['property_photos_migrated']}")
        logger.info(f"Inspiration Images Migrated: {self.stats['inspiration_images_migrated']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Skipped: {self.stats['skipped']}")
        logger.info(f"Total Storage Freed: {self.stats['total_size_freed']:,} bytes")
        logger.info(f"Estimated Egress Reduction: {(self.stats['total_size_freed'] / 1024 / 1024):.2f} MB per API call")

async def main():
    """Main migration entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate base64 images to Supabase Storage buckets")
    parser.add_argument("--dry-run", action="store_true", help="Analyze without making changes")
    args = parser.parse_args()
    
    migration = Base64ToBucketMigration()
    await migration.run_migration(dry_run=args.dry_run)

if __name__ == "__main__":
    asyncio.run(main())