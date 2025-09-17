-- Migration: Contractor Image Management System
-- Purpose: Create tables for contractor portfolios, uploaded work, and InstaBids completed projects
-- Agent: Agent 4 (Contractor UX)
-- Date: January 31, 2025

-- =============================================================================
-- PART 1: CONTRACTOR IMAGES TABLE
-- =============================================================================

CREATE TABLE contractor_images (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    contractor_id uuid NOT NULL REFERENCES contractors(id) ON DELETE CASCADE,
    
    -- Image details
    image_url text NOT NULL,
    thumbnail_url text,
    storage_path text NOT NULL,
    
    -- Categorization
    category varchar NOT NULL CHECK (category IN ('portfolio', 'uploaded', 'instabids_completed')),
    project_type varchar, -- 'kitchen', 'bathroom', 'lawn', 'roofing', etc.
    
    -- Source tracking
    source varchar, -- 'website_scrape', 'google_business', 'manual_upload', 'homeowner_upload'
    source_url text,
    scraped_from_url text,
    
    -- Project association
    bid_card_id uuid REFERENCES bid_cards(id) ON DELETE SET NULL, -- For InstaBids completed work
    project_completion_date date,
    
    -- AI Analysis
    ai_analysis jsonb, -- AI-generated tags, quality scores, project type detection
    tags text[],
    quality_score integer CHECK (quality_score >= 1 AND quality_score <= 10),
    
    -- Display and ordering
    is_featured boolean DEFAULT false,
    display_order integer,
    is_public boolean DEFAULT true,
    
    -- Testing flag
    is_test_image boolean DEFAULT false,
    
    -- Metadata
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- =============================================================================
-- PART 2: CONTRACTOR IMAGE COLLECTIONS TABLE
-- =============================================================================

CREATE TABLE contractor_image_collections (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    contractor_id uuid NOT NULL REFERENCES contractors(id) ON DELETE CASCADE,
    
    -- Collection details
    name varchar NOT NULL, -- "Kitchen Remodels", "Bathroom Projects", etc.
    description text,
    collection_type varchar NOT NULL, -- 'project_type', 'time_period', 'featured', 'before_after'
    
    -- Display
    cover_image_id uuid REFERENCES contractor_images(id) ON DELETE SET NULL,
    is_public boolean DEFAULT true,
    display_order integer,
    
    -- Testing flag
    is_test_collection boolean DEFAULT false,
    
    -- Metadata
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- =============================================================================
-- PART 3: CONTRACTOR IMAGE COLLECTION ITEMS (JUNCTION TABLE)
-- =============================================================================

CREATE TABLE contractor_image_collection_items (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id uuid NOT NULL REFERENCES contractor_image_collections(id) ON DELETE CASCADE,
    image_id uuid NOT NULL REFERENCES contractor_images(id) ON DELETE CASCADE,
    display_order integer,
    created_at timestamptz DEFAULT now(),
    
    UNIQUE(collection_id, image_id)
);

-- =============================================================================
-- PART 4: INDEXES FOR PERFORMANCE
-- =============================================================================

-- Primary lookup indexes
CREATE INDEX idx_contractor_images_contractor_id ON contractor_images(contractor_id);
CREATE INDEX idx_contractor_images_category ON contractor_images(category);
CREATE INDEX idx_contractor_images_project_type ON contractor_images(project_type);
CREATE INDEX idx_contractor_images_featured ON contractor_images(is_featured) WHERE is_featured = true;

-- Source tracking indexes
CREATE INDEX idx_contractor_images_source ON contractor_images(source);
CREATE INDEX idx_contractor_images_bid_card ON contractor_images(bid_card_id) WHERE bid_card_id IS NOT NULL;

-- Testing and production separation
CREATE INDEX idx_contractor_images_test ON contractor_images(is_test_image);
CREATE INDEX idx_contractor_images_production ON contractor_images(contractor_id, category, is_public) 
    WHERE is_test_image = false;

-- Collection indexes
CREATE INDEX idx_contractor_collections_contractor_id ON contractor_image_collections(contractor_id);
CREATE INDEX idx_contractor_collections_type ON contractor_image_collections(collection_type);
CREATE INDEX idx_contractor_collections_test ON contractor_image_collections(is_test_collection);

-- Junction table indexes
CREATE INDEX idx_collection_items_collection_id ON contractor_image_collection_items(collection_id);
CREATE INDEX idx_collection_items_image_id ON contractor_image_collection_items(image_id);

-- =============================================================================
-- PART 5: UTILITY FUNCTIONS
-- =============================================================================

-- Function to get contractor image statistics
CREATE OR REPLACE FUNCTION get_contractor_image_stats(contractor_uuid UUID)
RETURNS TABLE(
    total_images INTEGER,
    portfolio_images INTEGER,
    uploaded_images INTEGER,
    instabids_completed INTEGER,
    featured_images INTEGER,
    avg_quality_score NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_images,
        COUNT(*) FILTER (WHERE category = 'portfolio')::INTEGER as portfolio_images,
        COUNT(*) FILTER (WHERE category = 'uploaded')::INTEGER as uploaded_images,
        COUNT(*) FILTER (WHERE category = 'instabids_completed')::INTEGER as instabids_completed,
        COUNT(*) FILTER (WHERE is_featured = true)::INTEGER as featured_images,
        ROUND(AVG(quality_score), 2) as avg_quality_score
    FROM contractor_images 
    WHERE contractor_id = contractor_uuid 
    AND is_test_image = false
    AND is_public = true;
END;
$$ LANGUAGE plpgsql;

-- Function to mark contractor images as test data
CREATE OR REPLACE FUNCTION mark_contractor_images_as_test(contractor_uuid UUID)
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    -- Mark all images as test
    UPDATE contractor_images 
    SET is_test_image = true 
    WHERE contractor_id = contractor_uuid;
    
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    
    -- Mark all collections as test
    UPDATE contractor_image_collections 
    SET is_test_collection = true 
    WHERE contractor_id = contractor_uuid;
    
    RAISE NOTICE 'Marked % contractor images as test data for contractor %', updated_count, contractor_uuid;
    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup test image data
CREATE OR REPLACE FUNCTION cleanup_test_image_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
    temp_count INTEGER;
BEGIN
    -- Delete test images (will cascade to collection items)
    DELETE FROM contractor_images WHERE is_test_image = true;
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    RAISE NOTICE 'Deleted % test contractor images', temp_count;
    
    -- Delete test collections
    DELETE FROM contractor_image_collections WHERE is_test_collection = true;
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    RAISE NOTICE 'Deleted % test image collections', temp_count;
    
    RAISE NOTICE 'Total test image records deleted: %', deleted_count;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PART 6: SAMPLE DATA FOR TESTING
-- =============================================================================

-- Add some sample project types for reference
INSERT INTO contractor_images (id, contractor_id, image_url, thumbnail_url, storage_path, category, project_type, source, tags, quality_score, is_test_image, created_at)
VALUES 
    (
        '00000000-0000-0000-0000-000000000001',
        '550e8400-e29b-41d4-a716-446655440001', -- Sample contractor ID
        'https://example.com/sample-kitchen.jpg',
        'https://example.com/sample-kitchen-thumb.jpg',
        'contractor-media/uploads/550e8400-e29b-41d4-a716-446655440001/sample-kitchen.jpg',
        'uploaded',
        'kitchen',
        'manual_upload',
        ARRAY['modern', 'granite', 'stainless-steel'],
        8,
        true, -- Mark as test data
        now()
    ) ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- PART 7: VERIFICATION QUERIES
-- =============================================================================

-- Verify tables were created
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
AND table_name LIKE '%contractor_image%'
ORDER BY table_name;

-- Verify indexes were created
SELECT 
    indexname,
    tablename,
    indexdef
FROM pg_indexes 
WHERE tablename LIKE '%contractor_image%'
ORDER BY tablename, indexname;

-- Verify functions were created
SELECT 
    routine_name,
    routine_type
FROM information_schema.routines
WHERE routine_name LIKE '%contractor_image%' 
OR routine_name LIKE '%test_image%'
ORDER BY routine_name;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 010 completed successfully!';
    RAISE NOTICE '✅ Created contractor_images table with AI analysis fields';
    RAISE NOTICE '✅ Created contractor_image_collections table for portfolio organization';
    RAISE NOTICE '✅ Created contractor_image_collection_items junction table';
    RAISE NOTICE '✅ Added performance indexes for all tables';
    RAISE NOTICE '✅ Added utility functions for statistics and test data management';
    RAISE NOTICE '✅ Added sample test data for verification';
    RAISE NOTICE '';
    RAISE NOTICE '🎯 Ready for Phase 2: Backend API Development';
    RAISE NOTICE '📁 Storage bucket needed: contractor-media/';
    RAISE NOTICE '🔧 Next: Test contractor image upload and gallery interface';
END $$;