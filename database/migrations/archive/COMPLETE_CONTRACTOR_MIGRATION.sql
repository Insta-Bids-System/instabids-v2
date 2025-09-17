-- COMPLETE CONTRACTOR SYSTEM MIGRATION
-- Run this in Supabase SQL Editor to add all missing columns

-- 1. Add AI writeup fields to potential_contractors table
ALTER TABLE potential_contractors 
ADD COLUMN IF NOT EXISTS ai_business_summary TEXT,
ADD COLUMN IF NOT EXISTS ai_capability_description TEXT,
ADD COLUMN IF NOT EXISTS business_size_category VARCHAR(50) CHECK (business_size_category IN ('INDIVIDUAL_HANDYMAN', 'OWNER_OPERATOR', 'LOCAL_BUSINESS_TEAMS', 'NATIONAL_COMPANY')),
ADD COLUMN IF NOT EXISTS is_test_contractor BOOLEAN DEFAULT FALSE;

-- 2. Add test flags to all contractor-related tables
ALTER TABLE contractor_communications 
ADD COLUMN IF NOT EXISTS is_test_contractor BOOLEAN DEFAULT FALSE;

ALTER TABLE contractor_interactions 
ADD COLUMN IF NOT EXISTS is_test_contractor BOOLEAN DEFAULT FALSE;

ALTER TABLE contractor_qualifications 
ADD COLUMN IF NOT EXISTS is_test_contractor BOOLEAN DEFAULT FALSE;

ALTER TABLE contractor_enrichment_logs 
ADD COLUMN IF NOT EXISTS is_test_contractor BOOLEAN DEFAULT FALSE;

ALTER TABLE contractor_responses 
ADD COLUMN IF NOT EXISTS is_test_contractor BOOLEAN DEFAULT FALSE;

ALTER TABLE contractor_matches 
ADD COLUMN IF NOT EXISTS is_test_contractor BOOLEAN DEFAULT FALSE;

ALTER TABLE contractor_invitations 
ADD COLUMN IF NOT EXISTS is_test_contractor BOOLEAN DEFAULT FALSE;

-- 3. Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_potential_contractors_test ON potential_contractors(is_test_contractor);
CREATE INDEX IF NOT EXISTS idx_potential_contractors_business_size ON potential_contractors(business_size_category);
CREATE INDEX IF NOT EXISTS idx_potential_contractors_status ON potential_contractors(status);

-- 4. Add comments for documentation
COMMENT ON COLUMN potential_contractors.ai_business_summary IS 'AI-generated business description for bid card matching';
COMMENT ON COLUMN potential_contractors.ai_capability_description IS 'AI-generated capability writeup for contractor expertise';
COMMENT ON COLUMN potential_contractors.business_size_category IS 'Business size classification: INDIVIDUAL_HANDYMAN, OWNER_OPERATOR, LOCAL_BUSINESS_TEAMS, NATIONAL_COMPANY';
COMMENT ON COLUMN potential_contractors.is_test_contractor IS 'Flag for test/fake contractors used in development';

-- 5. Verify the changes
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'potential_contractors' 
AND column_name IN ('ai_business_summary', 'ai_capability_description', 'business_size_category', 'is_test_contractor')
ORDER BY column_name;