# IRIS BUCKET STORAGE IMPLEMENTATION PLAN

## 🎯 PROBLEM STATEMENT
Currently storing base64 images directly in database (210KB avg per image), causing massive egress costs. Need to migrate to Supabase Storage buckets.

## 🏗️ ARCHITECTURE OVERVIEW

### Storage Buckets (Coordinated with CIA Agent)
```
supabase-storage/
├── bid-card-images/        [CIA Agent Primary]
├── property-photos/         [IRIS Agent Primary]  
└── inspiration-images/      [IRIS Agent Primary]
```

## 📋 IMPLEMENTATION PLAN

### Phase 1: Create Storage Infrastructure

```python
# services/image_storage_service.py
from supabase import create_client
import uuid
from PIL import Image
import io

class ImageStorageService:
    def __init__(self):
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )
        
    async def upload_to_bucket(self, 
                              image_data: bytes, 
                              bucket_name: str,
                              path_prefix: str,
                              filename: str) -> dict:
        """
        Upload image to Supabase Storage bucket
        Returns URLs for original and thumbnail
        """
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_ext = filename.split('.')[-1]
        storage_filename = f"{file_id}.{file_ext}"
        
        # Upload original
        original_path = f"{path_prefix}/original/{storage_filename}"
        self.supabase.storage.from_(bucket_name).upload(
            original_path,
            image_data,
            {"content-type": f"image/{file_ext}"}
        )
        
        # Generate and upload thumbnail
        thumbnail = self._generate_thumbnail(image_data)
        thumbnail_path = f"{path_prefix}/thumbnails/{storage_filename}"
        self.supabase.storage.from_(bucket_name).upload(
            thumbnail_path,
            thumbnail,
            {"content-type": f"image/{file_ext}"}
        )
        
        # Get public URLs
        base_url = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public"
        
        return {
            "original_url": f"{base_url}/{bucket_name}/{original_path}",
            "thumbnail_url": f"{base_url}/{bucket_name}/{thumbnail_path}",
            "storage_path": original_path,
            "file_id": file_id
        }
    
    def _generate_thumbnail(self, image_data: bytes, size=(150, 150)) -> bytes:
        """Generate thumbnail from image data"""
        img = Image.open(io.BytesIO(image_data))
        img.thumbnail(size, Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        return buffer.getvalue()
```

### Phase 2: Update IRIS Agent Storage Methods

```python
# api/iris_unified_agent.py - UPDATED METHODS

async def _store_to_inspiration_board(self, user_id: str, image_file: bytes, 
                                     filename: str, session_id: str):
    """Store image to inspiration board using bucket storage"""
    try:
        storage_service = ImageStorageService()
        
        # Upload to bucket
        storage_result = await storage_service.upload_to_bucket(
            image_data=image_file,
            bucket_name="inspiration-images",
            path_prefix=f"{user_id}/{board_id}",
            filename=filename
        )
        
        # Store only URLs in database
        image_entry = {
            "id": str(uuid.uuid4()),
            "board_id": board_id,
            "user_id": user_id,
            "image_url": storage_result["original_url"],  # Just URL!
            "thumbnail_url": storage_result["thumbnail_url"],
            "source": "iris_upload",
            "ai_analysis": {
                "uploaded_via": "iris",
                "session_id": session_id,
                "storage_path": storage_result["storage_path"],
                "original_filename": filename
            },
            "created_at": datetime.now().isoformat()
        }
        
        service_client.table("inspiration_images").insert(image_entry).execute()
        
    except Exception as e:
        logger.error(f"Failed to store to inspiration board: {e}")

async def _store_to_property_photos(self, user_id: str, image_file: bytes,
                                   filename: str, session_id: str):
    """Store image to property photos using bucket storage"""
    try:
        storage_service = ImageStorageService()
        
        # Upload to bucket
        storage_result = await storage_service.upload_to_bucket(
            image_data=image_file,
            bucket_name="property-photos",
            path_prefix=f"{property_id}/general",
            filename=filename
        )
        
        # Store only URLs in database
        photo_entry = {
            "id": str(uuid.uuid4()),
            "property_id": property_id,
            "photo_url": storage_result["original_url"],  # Just URL!
            "thumbnail_url": storage_result["thumbnail_url"],
            "original_filename": filename,
            "ai_classification": {
                "storage_path": storage_result["storage_path"],
                "file_id": storage_result["file_id"]
            },
            "created_at": datetime.now().isoformat()
        }
        
        db.client.table("property_photos").insert(photo_entry).execute()
        
    except Exception as e:
        logger.error(f"Failed to store to property photos: {e}")
```

### Phase 3: Unified Memory System Integration

```python
# Memory system stores references, not data
class UnifiedMemoryIntegration:
    
    async def store_image_context(self, session_id: str, image_info: dict):
        """Store image context in unified memory"""
        memory_entry = {
            "conversation_id": session_id,
            "memory_type": "image_context",
            "content": {
                "image_url": image_info["original_url"],
                "thumbnail_url": image_info["thumbnail_url"],
                "ai_analysis": image_info["ai_analysis"],
                "storage_location": image_info["storage_type"],  # "property" or "inspiration"
                "user_intent": image_info["classification"]
            },
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "agent": "iris",
                "file_id": image_info["file_id"]
            }
        }
        
        # Store in unified_conversation_memory
        db.client.table("unified_conversation_memory").insert(memory_entry).execute()
```

### Phase 4: Router Updates for Retrieval

```python
# routers/property_api.py - UPDATED
@router.get("/properties/{property_id}/photos")
async def get_property_photos(property_id: str):
    """Get property photos - returns URLs only, not base64"""
    photos = db.client.table("property_photos")\
        .select("id, photo_url, thumbnail_url, ai_description, created_at")\
        .eq("property_id", property_id)\
        .execute()
    
    # Return lightweight response with URLs
    return {
        "photos": photos.data,  # Each ~200 bytes instead of 200KB
        "count": len(photos.data)
    }

# Frontend fetches images directly from bucket URLs
# <img src="{photo.thumbnail_url}" /> - Browser caches automatically
```

### Phase 5: Migration Script for Existing Images

```python
# scripts/migrate_base64_to_buckets.py
async def migrate_existing_images():
    """One-time migration of base64 images to buckets"""
    
    # 1. Get all base64 images
    photos = db.client.table("property_photos")\
        .select("*")\
        .like("photo_url", "data:image%")\
        .execute()
    
    storage_service = ImageStorageService()
    
    for photo in photos.data:
        # Extract base64 data
        base64_data = photo["photo_url"].split(",")[1]
        image_bytes = base64.b64decode(base64_data)
        
        # Upload to bucket
        storage_result = await storage_service.upload_to_bucket(
            image_data=image_bytes,
            bucket_name="property-photos",
            path_prefix=f"{photo['property_id']}/migrated",
            filename=photo["original_filename"] or f"migrated_{photo['id']}.jpg"
        )
        
        # Update record with URL
        db.client.table("property_photos")\
            .update({
                "photo_url": storage_result["original_url"],
                "thumbnail_url": storage_result["thumbnail_url"]
            })\
            .eq("id", photo["id"])\
            .execute()
        
        print(f"Migrated photo {photo['id']}")
```

## 📊 IMPACT ANALYSIS

### Before (Current State):
- **Database Storage**: 10 images × 210KB = 2.1MB per query
- **API Response Size**: 2.1MB + metadata
- **Egress Cost**: Every API call downloads all image data
- **Performance**: Slow queries, large payloads

### After (With Buckets):
- **Database Storage**: 10 images × 200 bytes = 2KB per query  
- **API Response Size**: 2KB + metadata
- **Egress Cost**: 99.9% reduction (images cached by CDN)
- **Performance**: Fast queries, lazy image loading

## 🚀 IMPLEMENTATION STEPS

1. **Create Buckets** (15 min)
   ```sql
   -- Run in Supabase Dashboard
   INSERT INTO storage.buckets (id, name, public)
   VALUES 
     ('property-photos', 'property-photos', true),
     ('inspiration-images', 'inspiration-images', true);
   ```

2. **Deploy Storage Service** (30 min)
   - Create `services/image_storage_service.py`
   - Test upload/thumbnail generation

3. **Update IRIS Agent** (1 hour)
   - Modify `_store_to_inspiration_board()` 
   - Modify `_store_to_property_photos()`
   - Test with new uploads

4. **Run Migration** (30 min)
   - Execute migration script
   - Verify URLs work
   - Clean up base64 data

5. **Update Frontend** (if needed)
   - Ensure `<img>` tags use URLs
   - Add lazy loading
   - Implement thumbnail preview

## ⚠️ CRITICAL NOTES

1. **AI Analysis Still Needs Base64**: Claude API requires base64 for image analysis, but we only use it temporarily in memory, never store it

2. **Bucket Permissions**: Ensure buckets are PUBLIC for read access or implement signed URLs for private access

3. **Coordination with CIA Agent**: They're handling `bid-card-images` bucket, we handle `property-photos` and `inspiration-images`

4. **Memory System**: Stores only references (URLs), not actual image data

5. **CDN Caching**: Supabase Storage includes CDN, images cached at edge locations

## 🎯 SUCCESS METRICS

- [ ] Zero base64 strings in database
- [ ] API response time < 200ms
- [ ] Egress reduced by 99%
- [ ] Images load directly from CDN
- [ ] Unified memory contains only URLs