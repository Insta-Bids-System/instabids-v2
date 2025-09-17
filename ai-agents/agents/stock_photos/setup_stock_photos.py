#!/usr/bin/env python3
"""
Setup Stock Photo System for Bid Cards
Creates database tables and configures automatic fallback logic
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database_simple import get_client
import asyncio

async def create_stock_photo_tables():
    """Create the stock photo tables and triggers"""
    
    supabase = get_client()
    
    # Create project_type_stock_photos table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS project_type_stock_photos (
        id SERIAL PRIMARY KEY,
        project_type_id INTEGER REFERENCES project_types(id),
        project_type_slug VARCHAR(100),  -- For easier matching
        photo_url TEXT NOT NULL,
        storage_path TEXT,
        alt_text VARCHAR(200),
        priority INTEGER DEFAULT 1,
        is_active BOOLEAN DEFAULT TRUE,
        uploaded_by VARCHAR(100),
        tags TEXT[],
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Indexes for performance
    CREATE INDEX IF NOT EXISTS idx_stock_photos_type_id ON project_type_stock_photos(project_type_id);
    CREATE INDEX IF NOT EXISTS idx_stock_photos_slug ON project_type_stock_photos(project_type_slug);
    CREATE INDEX IF NOT EXISTS idx_stock_photos_active ON project_type_stock_photos(is_active);
    CREATE INDEX IF NOT EXISTS idx_stock_photos_priority ON project_type_stock_photos(priority);
    
    -- Add stock photo fields to bid_cards if not exists
    ALTER TABLE bid_cards 
    ADD COLUMN IF NOT EXISTS stock_photo_url TEXT,
    ADD COLUMN IF NOT EXISTS photo_source VARCHAR(50) DEFAULT 'none';
    
    -- Create function to get stock photo for project type
    CREATE OR REPLACE FUNCTION get_stock_photo_for_project_type(p_project_type VARCHAR)
    RETURNS TEXT AS $$
    DECLARE
        v_photo_url TEXT;
    BEGIN
        -- First try exact match on project_type_slug
        SELECT photo_url INTO v_photo_url
        FROM project_type_stock_photos
        WHERE project_type_slug = LOWER(REPLACE(p_project_type, ' ', '_'))
        AND is_active = TRUE
        ORDER BY priority ASC
        LIMIT 1;
        
        -- If no match, try partial match
        IF v_photo_url IS NULL THEN
            SELECT photo_url INTO v_photo_url
            FROM project_type_stock_photos
            WHERE LOWER(project_type_slug) LIKE '%' || LOWER(SPLIT_PART(p_project_type, '_', 1)) || '%'
            AND is_active = TRUE
            ORDER BY priority ASC
            LIMIT 1;
        END IF;
        
        RETURN v_photo_url;
    END;
    $$ LANGUAGE plpgsql;
    
    -- Create trigger to auto-set stock photo on bid card creation/update
    CREATE OR REPLACE FUNCTION set_bid_card_stock_photo()
    RETURNS TRIGGER AS $$
    BEGIN
        -- Only set stock photo if no homeowner photos exist
        IF (NEW.bid_document IS NULL OR 
            NEW.bid_document->'project_images' IS NULL OR 
            jsonb_array_length(COALESCE(NEW.bid_document->'project_images', '[]'::jsonb)) = 0) THEN
            
            -- Get stock photo for this project type
            NEW.stock_photo_url := get_stock_photo_for_project_type(NEW.project_type);
            
            -- Set photo source
            IF NEW.stock_photo_url IS NOT NULL THEN
                NEW.photo_source := 'stock';
            ELSE
                NEW.photo_source := 'none';
            END IF;
        ELSE
            -- Homeowner has photos
            NEW.photo_source := 'homeowner';
            NEW.stock_photo_url := NULL;
        END IF;
        
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    
    -- Create trigger
    CREATE TRIGGER set_stock_photo_trigger
    BEFORE INSERT OR UPDATE ON bid_cards
    FOR EACH ROW EXECUTE FUNCTION set_bid_card_stock_photo();
    """
    
    try:
        # Execute the SQL
        result = supabase.rpc('exec_sql', {'query': create_table_sql}).execute()
        print("[OK] Stock photo tables created successfully!")
        return True
    except Exception as e:
        print(f"[ERROR] Error creating tables: {e}")
        
        # Try alternative approach - execute statements one by one
        try:
            statements = create_table_sql.split(';')
            for statement in statements:
                if statement.strip():
                    supabase.rpc('exec_sql', {'query': statement}).execute()
            print("[OK] Stock photo tables created successfully (alternative method)!")
            return True
        except Exception as e2:
            print(f"[ERROR] Alternative method also failed: {e2}")
            return False

async def add_sample_stock_photos():
    """Add some sample stock photos for testing"""
    
    supabase = get_client()
    
    sample_photos = [
        # Plumbing
        {
            'project_type_slug': 'plumbing_repair',
            'photo_url': 'https://images.unsplash.com/photo-1607472586893-edb57bdc0e39?w=800',
            'alt_text': 'Professional plumber working on pipes',
            'priority': 1
        },
        {
            'project_type_slug': 'toilet_repair',
            'photo_url': 'https://images.unsplash.com/photo-1595515106969-1ce29566ff1c?w=800',
            'alt_text': 'Modern bathroom toilet',
            'priority': 1
        },
        # Kitchen
        {
            'project_type_slug': 'kitchen_remodel',
            'photo_url': 'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=800',
            'alt_text': 'Beautiful modern kitchen remodel',
            'priority': 1
        },
        {
            'project_type_slug': 'kitchen_renovation',
            'photo_url': 'https://images.unsplash.com/photo-1565538810643-b5bdb714032a?w=800',
            'alt_text': 'Kitchen renovation in progress',
            'priority': 1
        },
        # Bathroom
        {
            'project_type_slug': 'bathroom_remodel',
            'photo_url': 'https://images.unsplash.com/photo-1620626011761-996317b8d101?w=800',
            'alt_text': 'Modern bathroom remodel',
            'priority': 1
        },
        # Landscaping
        {
            'project_type_slug': 'landscaping',
            'photo_url': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800',
            'alt_text': 'Professional landscaping work',
            'priority': 1
        },
        {
            'project_type_slug': 'lawn_care',
            'photo_url': 'https://images.unsplash.com/photo-1558904541-efa843a96f01?w=800',
            'alt_text': 'Lawn care and maintenance',
            'priority': 1
        },
        # Roofing
        {
            'project_type_slug': 'roofing',
            'photo_url': 'https://images.unsplash.com/photo-1632207691143-643e2a9a9361?w=800',
            'alt_text': 'Roof repair and installation',
            'priority': 1
        },
        {
            'project_type_slug': 'roof_repair',
            'photo_url': 'https://images.unsplash.com/photo-1621905251189-08b45d6a269e?w=800',
            'alt_text': 'Professional roof repair',
            'priority': 1
        },
        # Electrical
        {
            'project_type_slug': 'electrical_repair',
            'photo_url': 'https://images.unsplash.com/photo-1621905251918-48416bd8575a?w=800',
            'alt_text': 'Electrical panel and wiring',
            'priority': 1
        }
    ]
    
    try:
        for photo in sample_photos:
            result = supabase.table('project_type_stock_photos').insert(photo).execute()
            print(f"[OK] Added stock photo for {photo['project_type_slug']}")
    except Exception as e:
        print(f"[ERROR] Error adding sample photos: {e}")
        return False
    
    return True

async def main():
    """Setup the complete stock photo system"""
    
    print("\n> Setting up Stock Photo System for Bid Cards\n")
    print("=" * 50)
    
    # Step 1: Create tables
    print("\n1. Creating database tables and triggers...")
    success = await create_stock_photo_tables()
    
    if not success:
        print("\n[WARNING]  Failed to create tables. Please check database connection.")
        return
    
    # Step 2: Add sample photos
    print("\n2. Adding sample stock photos for testing...")
    await add_sample_stock_photos()
    
    print("\n" + "=" * 50)
    print("[OK] Stock Photo System Setup Complete!")
    print("\nFallback Logic:")
    print("- If homeowner uploads photos → Use homeowner photos")
    print("- If no homeowner photos → Use stock photo for project type")
    print("- If no stock photo available → No photo displayed")
    print("\nNext steps:")
    print("1. Run test_stock_photo_fallback.py to test the system")
    print("2. Upload more stock photos using upload_stock_photos.py")
    print("3. Check bid cards to see stock photos in action!")

if __name__ == "__main__":
    asyncio.run(main())