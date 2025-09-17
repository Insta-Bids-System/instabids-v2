# Stock Photo System for Bid Cards

**Purpose**: Automatically provide professional stock photos for bid cards when homeowners don't upload their own photos.

## How It Works
1. **Homeowner uploads photos** → Use homeowner's photos (priority)
2. **No homeowner photos** → Use stock photo based on project_type
3. **No stock photo available** → Use generic placeholder

## Quick Start
```bash
# 1. Run migration to create tables
python setup_stock_photos.py

# 2. Upload stock photos for project types
python upload_stock_photos.py

# 3. Test the system
python test_stock_photo_fallback.py
```

## Files
- `setup_stock_photos.py` - Creates database tables and triggers
- `stock_photo_manager.py` - Core logic for managing stock photos
- `upload_stock_photos.py` - Bulk upload stock photos
- `api.py` - API endpoints for stock photo management