-- Proposed additions to potential_contractors table

ALTER TABLE potential_contractors ADD COLUMN IF NOT EXISTS business_size VARCHAR(50);
-- Values: 'INDIVIDUAL_HANDYMAN', 'OWNER_OPERATOR', 'LOCAL_BUSINESS_TEAMS', 'NATIONAL_COMPANY'

ALTER TABLE potential_contractors ADD COLUMN IF NOT EXISTS service_types TEXT[];
-- Array of: ['REPAIR', 'INSTALLATION', 'MAINTENANCE', 'EMERGENCY', 'CONSULTATION']

ALTER TABLE potential_contractors ADD COLUMN IF NOT EXISTS service_description TEXT;
-- Detailed searchable description of services

ALTER TABLE potential_contractors ADD COLUMN IF NOT EXISTS service_areas TEXT[];
-- Array of zip codes they serve

ALTER TABLE potential_contractors ADD COLUMN IF NOT EXISTS enrichment_status VARCHAR(50);
-- Values: 'PENDING', 'ENRICHED', 'FAILED', 'NO_WEBSITE'

ALTER TABLE potential_contractors ADD COLUMN IF NOT EXISTS enrichment_data JSONB;
-- Store all extracted data from website including:
-- {
--   "about_text": "...",
--   "services_offered": [...],
--   "service_area_text": "...",
--   "team_size_indicators": [...],
--   "years_in_business_text": "...",
--   "certifications": [...],
--   "enrichment_timestamp": "..."
-- }

-- Create indexes for efficient searching
CREATE INDEX idx_contractors_zip ON potential_contractors USING GIN (service_areas);
CREATE INDEX idx_contractors_services ON potential_contractors USING GIN (service_types);
CREATE INDEX idx_contractors_description ON potential_contractors USING GIN (to_tsvector('english', service_description));
CREATE INDEX idx_contractors_business_size ON potential_contractors (business_size);
CREATE INDEX idx_contractors_project_type ON potential_contractors (project_type);