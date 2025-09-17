-- Migration: Add Test Flags and Fix Foreign Key References
-- Purpose: Enable safe testing with fake contractors and fix table reference mismatches
-- Date: January 31, 2025

-- =============================================================================
-- PART 1: FIX FOREIGN KEY REFERENCES
-- Problem: Schema references 'contractor_leads' but production table is 'potential_contractors'
-- =============================================================================

-- Fix contractor_outreach_attempts
ALTER TABLE contractor_outreach_attempts 
DROP CONSTRAINT IF EXISTS contractor_outreach_attempts_contractor_lead_id_fkey;

ALTER TABLE contractor_outreach_attempts 
ADD CONSTRAINT contractor_outreach_attempts_contractor_lead_id_fkey 
FOREIGN KEY (contractor_lead_id) REFERENCES potential_contractors(id);

-- Fix contractor_engagement_summary
ALTER TABLE contractor_engagement_summary
DROP CONSTRAINT IF EXISTS contractor_engagement_summary_contractor_lead_id_fkey;

ALTER TABLE contractor_engagement_summary
ADD CONSTRAINT contractor_engagement_summary_contractor_lead_id_fkey 
FOREIGN KEY (contractor_lead_id) REFERENCES potential_contractors(id);

-- Fix lead_enrichment_tasks (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'lead_enrichment_tasks') THEN
        ALTER TABLE lead_enrichment_tasks
        DROP CONSTRAINT IF EXISTS lead_enrichment_tasks_contractor_lead_id_fkey;
        
        ALTER TABLE lead_enrichment_tasks
        ADD CONSTRAINT lead_enrichment_tasks_contractor_lead_id_fkey 
        FOREIGN KEY (contractor_lead_id) REFERENCES potential_contractors(id);
    END IF;
END $$;

-- Fix bid_card_distributions (if exists)  
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'bid_card_distributions') THEN
        ALTER TABLE bid_card_distributions
        DROP CONSTRAINT IF EXISTS bid_card_distributions_contractor_id_fkey;
        
        ALTER TABLE bid_card_distributions
        ADD CONSTRAINT bid_card_distributions_contractor_id_fkey 
        FOREIGN KEY (contractor_id) REFERENCES potential_contractors(id);
    END IF;
END $$;

-- Fix bid_card_public_urls (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'bid_card_public_urls') THEN
        ALTER TABLE bid_card_public_urls
        DROP CONSTRAINT IF EXISTS bid_card_public_urls_contractor_lead_id_fkey;
        
        ALTER TABLE bid_card_public_urls
        ADD CONSTRAINT bid_card_public_urls_contractor_lead_id_fkey 
        FOREIGN KEY (contractor_lead_id) REFERENCES potential_contractors(id);
    END IF;
END $$;

-- =============================================================================
-- PART 2: ADD TEST/FAKE BUSINESS FLAGS TO ALL CONTRACTOR TABLES
-- Purpose: Enable safe testing without affecting production data
-- =============================================================================

-- Main contractor table
ALTER TABLE potential_contractors 
ADD COLUMN IF NOT EXISTS is_test_contractor BOOLEAN DEFAULT FALSE;

-- Discovery tables
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'discovery_runs') THEN
        ALTER TABLE discovery_runs 
        ADD COLUMN IF NOT EXISTS is_test_run BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'lead_enrichment_tasks') THEN
        ALTER TABLE lead_enrichment_tasks 
        ADD COLUMN IF NOT EXISTS is_test_task BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- Outreach tables
ALTER TABLE outreach_campaigns 
ADD COLUMN IF NOT EXISTS is_test_campaign BOOLEAN DEFAULT FALSE;

ALTER TABLE contractor_outreach_attempts 
ADD COLUMN IF NOT EXISTS is_test_outreach BOOLEAN DEFAULT FALSE;

ALTER TABLE contractor_engagement_summary 
ADD COLUMN IF NOT EXISTS is_test_data BOOLEAN DEFAULT FALSE;

-- Job tracking tables  
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'contractor_job_opportunities') THEN
        ALTER TABLE contractor_job_opportunities 
        ADD COLUMN IF NOT EXISTS is_test_opportunity BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'contractor_preferences') THEN
        ALTER TABLE contractor_preferences 
        ADD COLUMN IF NOT EXISTS is_test_preferences BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- Analytics tables
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'contractor_response_rates') THEN
        ALTER TABLE contractor_response_rates 
        ADD COLUMN IF NOT EXISTS is_test_data BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'bid_card_distributions') THEN
        ALTER TABLE bid_card_distributions 
        ADD COLUMN IF NOT EXISTS is_test_distribution BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'bid_card_public_urls') THEN
        ALTER TABLE bid_card_public_urls 
        ADD COLUMN IF NOT EXISTS is_test_access BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- =============================================================================
-- PART 3: CREATE INDEXES FOR EFFICIENT TEST DATA FILTERING
-- =============================================================================

-- Main contractor test filtering
CREATE INDEX IF NOT EXISTS idx_potential_contractors_test 
    ON potential_contractors(is_test_contractor);

-- Outreach test filtering
CREATE INDEX IF NOT EXISTS idx_outreach_attempts_test 
    ON contractor_outreach_attempts(is_test_outreach);

-- Campaign test filtering  
CREATE INDEX IF NOT EXISTS idx_campaigns_test 
    ON outreach_campaigns(is_test_campaign);

-- Job opportunities test filtering
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'contractor_job_opportunities') THEN
        CREATE INDEX IF NOT EXISTS idx_job_opportunities_test 
            ON contractor_job_opportunities(is_test_opportunity);
    END IF;
END $$;

-- Compound indexes for production queries (exclude test data)
CREATE INDEX IF NOT EXISTS idx_potential_contractors_production 
    ON potential_contractors(lead_status, tier) 
    WHERE is_test_contractor = FALSE;

CREATE INDEX IF NOT EXISTS idx_outreach_attempts_production 
    ON contractor_outreach_attempts(contractor_lead_id, status, sent_at) 
    WHERE is_test_outreach = FALSE;

-- =============================================================================
-- PART 4: CREATE TEST DATA MANAGEMENT FUNCTIONS
-- =============================================================================

-- Function to mark all data related to a test contractor as test data
CREATE OR REPLACE FUNCTION mark_contractor_as_test(contractor_id UUID)
RETURNS VOID AS $$
BEGIN
    -- Mark the contractor as test
    UPDATE potential_contractors 
    SET is_test_contractor = TRUE 
    WHERE id = contractor_id;

    -- Mark all outreach attempts as test
    UPDATE contractor_outreach_attempts 
    SET is_test_outreach = TRUE 
    WHERE contractor_lead_id = contractor_id;

    -- Mark engagement summary as test
    UPDATE contractor_engagement_summary 
    SET is_test_data = TRUE 
    WHERE contractor_lead_id = contractor_id;

    -- Mark job opportunities as test (if table exists)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'contractor_job_opportunities') THEN
        EXECUTE 'UPDATE contractor_job_opportunities SET is_test_opportunity = TRUE WHERE contractor_id = $1'
        USING contractor_id;
    END IF;

    -- Mark preferences as test (if table exists)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'contractor_preferences') THEN
        EXECUTE 'UPDATE contractor_preferences SET is_test_preferences = TRUE WHERE contractor_id = $1'
        USING contractor_id;
    END IF;

    -- Mark bid distributions as test (if table exists)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'bid_card_distributions') THEN
        EXECUTE 'UPDATE bid_card_distributions SET is_test_distribution = TRUE WHERE contractor_id = $1'
        USING contractor_id;
    END IF;

    -- Mark URL access as test (if table exists)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'bid_card_public_urls') THEN
        EXECUTE 'UPDATE bid_card_public_urls SET is_test_access = TRUE WHERE contractor_lead_id = $1'
        USING contractor_id;
    END IF;

    RAISE NOTICE 'Marked contractor % and all related data as test data', contractor_id;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up all test data (for production cleanup)
CREATE OR REPLACE FUNCTION cleanup_all_test_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
    temp_count INTEGER;
BEGIN
    -- Delete test contractors and cascade
    DELETE FROM potential_contractors WHERE is_test_contractor = TRUE;
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    RAISE NOTICE 'Deleted % test contractors', temp_count;

    -- Clean up any orphaned test data
    DELETE FROM contractor_outreach_attempts WHERE is_test_outreach = TRUE;
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    RAISE NOTICE 'Deleted % test outreach attempts', temp_count;

    DELETE FROM contractor_engagement_summary WHERE is_test_data = TRUE;
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    RAISE NOTICE 'Deleted % test engagement summaries', temp_count;

    DELETE FROM outreach_campaigns WHERE is_test_campaign = TRUE;
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    RAISE NOTICE 'Deleted % test campaigns', temp_count;

    -- Clean up other test tables if they exist
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'contractor_job_opportunities') THEN
        EXECUTE 'DELETE FROM contractor_job_opportunities WHERE is_test_opportunity = TRUE';
        GET DIAGNOSTICS temp_count = ROW_COUNT;
        deleted_count := deleted_count + temp_count;
        RAISE NOTICE 'Deleted % test job opportunities', temp_count;
    END IF;

    RAISE NOTICE 'Total test records deleted: %', deleted_count;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PART 5: VERIFICATION QUERIES
-- =============================================================================

-- Verify foreign key fixes
SELECT 
    conname as constraint_name,
    conrelid::regclass as table_name,
    confrelid::regclass as referenced_table
FROM pg_constraint 
WHERE confrelid = 'potential_contractors'::regclass
AND contype = 'f'
ORDER BY conrelid::regclass::text;

-- Verify test flag columns were added
SELECT 
    table_name,
    column_name,
    data_type,
    column_default
FROM information_schema.columns 
WHERE column_name LIKE '%test%' 
AND table_schema = 'public'
ORDER BY table_name, column_name;

-- Count current test vs production data
SELECT 
    'potential_contractors' as table_name,
    COUNT(*) FILTER (WHERE is_test_contractor = FALSE) as production_count,
    COUNT(*) FILTER (WHERE is_test_contractor = TRUE) as test_count,
    COUNT(*) as total_count
FROM potential_contractors

UNION ALL

SELECT 
    'contractor_outreach_attempts' as table_name,
    COUNT(*) FILTER (WHERE is_test_outreach = FALSE) as production_count,
    COUNT(*) FILTER (WHERE is_test_outreach = TRUE) as test_count,
    COUNT(*) as total_count
FROM contractor_outreach_attempts

UNION ALL

SELECT 
    'outreach_campaigns' as table_name,
    COUNT(*) FILTER (WHERE is_test_campaign = FALSE) as production_count,
    COUNT(*) FILTER (WHERE is_test_campaign = TRUE) as test_count,
    COUNT(*) as total_count
FROM outreach_campaigns;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 009 completed successfully!';
    RAISE NOTICE '✅ Fixed foreign key references to potential_contractors';
    RAISE NOTICE '✅ Added test flags to all contractor tables';
    RAISE NOTICE '✅ Created indexes for efficient test data filtering';
    RAISE NOTICE '✅ Added test data management functions';
    RAISE NOTICE '';
    RAISE NOTICE '🎯 Next steps:';
    RAISE NOTICE '1. Test campaign creation (should work now)';
    RAISE NOTICE '2. Create fake contractors with is_test_contractor=TRUE';
    RAISE NOTICE '3. Run end-to-end outreach test with fake data';
END $$;