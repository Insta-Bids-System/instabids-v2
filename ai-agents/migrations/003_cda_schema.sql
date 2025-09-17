-- CDA (Contractor Discovery Agent) Database Schema
-- Creates tables for 3-tier contractor sourcing system

-- 1. contractors (Internal Contractor Database)
CREATE TABLE contractors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_name TEXT NOT NULL,
  contact_name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  phone TEXT,
  specialties TEXT[] NOT NULL, -- ['kitchen', 'bathroom', 'roofing']
  zip_codes TEXT[] NOT NULL,   -- ['32904', '32901', '32903']
  min_project_size INTEGER DEFAULT 1000,
  max_project_size INTEGER DEFAULT 100000,
  rating DECIMAL(3,2) DEFAULT 0.00,
  total_projects INTEGER DEFAULT 0,
  availability TEXT CHECK (availability IN ('available', 'busy', 'unavailable')) DEFAULT 'available',
  onboarded BOOLEAN DEFAULT false,
  license_number TEXT,
  insurance_verified BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for Tier 1 performance optimization
CREATE INDEX idx_contractors_onboarded ON contractors (onboarded);
CREATE INDEX idx_contractors_specialties ON contractors USING GIN (specialties);
CREATE INDEX idx_contractors_zip_codes ON contractors USING GIN (zip_codes);
CREATE INDEX idx_contractors_availability ON contractors (availability);
CREATE INDEX idx_contractors_project_size ON contractors (min_project_size, max_project_size);
CREATE INDEX idx_contractors_rating ON contractors (rating DESC);

-- Composite index for common Tier 1 queries
CREATE INDEX idx_contractors_tier1_search ON contractors (onboarded, availability, rating DESC) 
WHERE onboarded = true AND availability = 'available';

-- 2. contractor_discovery_cache (Discovery Results Cache)
CREATE TABLE contractor_discovery_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bid_card_id UUID REFERENCES bid_cards(id),
  tier_1_matches JSONB, -- Internal contractors found
  tier_2_matches JSONB, -- Previously contacted contractors
  tier_3_sources JSONB, -- External sources to search
  discovery_status TEXT DEFAULT 'pending' CHECK (discovery_status IN ('pending', 'completed', 'failed')),
  total_contractors_found INTEGER DEFAULT 0,
  processing_time_ms INTEGER, -- Performance tracking
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_discovery_cache_bid_card ON contractor_discovery_cache (bid_card_id);
CREATE INDEX idx_discovery_cache_status ON contractor_discovery_cache (discovery_status);

-- 3. contractor_outreach (Outreach History for Tier 2)
CREATE TABLE contractor_outreach (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contractor_id UUID, -- May be null for external contacts
  bid_card_id UUID REFERENCES bid_cards(id),
  contact_method TEXT CHECK (contact_method IN ('email', 'sms', 'phone')),
  outreach_date TIMESTAMP DEFAULT NOW(),
  response_status TEXT CHECK (response_status IN ('pending', 'interested', 'declined', 'permanently_declined')),
  response_date TIMESTAMP,
  project_match_score DECIMAL(3,2), -- 0.0 to 1.0 matching score
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for Tier 2 re-engagement queries
CREATE INDEX idx_contractor_outreach_contacted_date ON contractor_outreach (outreach_date DESC);
CREATE INDEX idx_contractor_outreach_response_status ON contractor_outreach (response_status);
CREATE INDEX idx_contractor_outreach_match_score ON contractor_outreach (project_match_score DESC);

-- Composite index for Tier 2 re-engagement queries
CREATE INDEX idx_outreach_tier2_search ON contractor_outreach (outreach_date, response_status, project_match_score DESC)
WHERE response_status != 'permanently_declined' AND outreach_date > (NOW() - INTERVAL '6 months');

-- Insert test contractor data for development
INSERT INTO contractors (company_name, contact_name, email, phone, specialties, zip_codes, min_project_size, max_project_size, rating, total_projects, availability, onboarded, license_number, insurance_verified) VALUES
-- Florida contractors for testing
('AAA Kitchen Remodeling', 'John Smith', 'john@aaakitchen.com', '321-555-0101', ARRAY['kitchen', 'bathroom'], ARRAY['32904', '32901', '32903'], 5000, 75000, 4.8, 45, 'available', true, 'FL-CGC-123456', true),
('Best Roofing Solutions', 'Maria Garcia', 'maria@bestroofing.com', '321-555-0102', ARRAY['roofing', 'gutters'], ARRAY['32904', '32905', '32934'], 3000, 50000, 4.6, 78, 'available', true, 'FL-CCC-789012', true),
('Elite Home Contractors', 'David Johnson', 'david@elitehome.com', '321-555-0103', ARRAY['kitchen', 'bathroom', 'flooring'], ARRAY['32901', '32902', '32903'], 2000, 100000, 4.9, 120, 'available', true, 'FL-CGC-345678', true),
('Precision Plumbing Pro', 'Sarah Wilson', 'sarah@precisionplumbing.com', '321-555-0104', ARRAY['plumbing', 'bathroom'], ARRAY['32904', '32905'], 500, 25000, 4.7, 200, 'available', true, 'FL-CFC-567890', true),
('Melbourne Lawn Care', 'Mike Thompson', 'mike@melbournelawn.com', '321-555-0105', ARRAY['lawn care', 'landscaping'], ARRAY['32904', '32901'], 100, 5000, 4.5, 350, 'available', true, 'FL-LC-901234', true),

-- Some busy/unavailable contractors
('Premium Kitchen Designs', 'Lisa Brown', 'lisa@premiumkitchen.com', '321-555-0106', ARRAY['kitchen'], ARRAY['32903', '32934'], 10000, 150000, 4.9, 85, 'busy', true, 'FL-CGC-111222', true),
('Roof Masters Inc', 'Tom Anderson', 'tom@roofmasters.com', '321-555-0107', ARRAY['roofing'], ARRAY['32904', '32905'], 5000, 80000, 4.6, 60, 'unavailable', true, 'FL-CCC-333444', true),

-- Non-onboarded contractors (for future outreach)
('Local Handyman Services', 'Bob Miller', 'bob@localhandyman.com', '321-555-0108', ARRAY['general'], ARRAY['32904'], 200, 10000, 0.0, 0, 'available', false, null, false),
('Quality Contractors LLC', 'Amy Davis', 'amy@qualitycontractors.com', '321-555-0109', ARRAY['kitchen', 'bathroom', 'roofing'], ARRAY['32901', '32902'], 1000, 50000, 0.0, 0, 'available', false, 'FL-CGC-555666', false);

-- Insert sample outreach history for Tier 2 testing
INSERT INTO contractor_outreach (contractor_id, bid_card_id, contact_method, outreach_date, response_status, response_date, project_match_score, notes) VALUES
-- Recent outreach attempts (for Tier 2 re-engagement)
((SELECT id FROM contractors WHERE email = 'bob@localhandyman.com'), null, 'email', NOW() - INTERVAL '2 months', 'declined', NOW() - INTERVAL '2 months' + INTERVAL '1 day', 0.6, 'Not interested in lawn care projects'),
((SELECT id FROM contractors WHERE email = 'amy@qualitycontractors.com'), null, 'email', NOW() - INTERVAL '3 months', 'interested', NOW() - INTERVAL '3 months' + INTERVAL '2 days', 0.8, 'Interested but was too busy at the time'),
((SELECT id FROM contractors WHERE email = 'bob@localhandyman.com'), null, 'phone', NOW() - INTERVAL '4 months', 'interested', NOW() - INTERVAL '4 months' + INTERVAL '1 hour', 0.7, 'Expressed interest in small projects'),

-- Old outreach (should not appear in Tier 2)
((SELECT id FROM contractors WHERE email = 'amy@qualitycontractors.com'), null, 'email', NOW() - INTERVAL '8 months', 'declined', NOW() - INTERVAL '8 months' + INTERVAL '1 day', 0.5, 'Too old for re-engagement'),

-- Permanently declined (should never appear in Tier 2)
((SELECT id FROM contractors WHERE email = 'bob@localhandyman.com'), null, 'sms', NOW() - INTERVAL '1 month', 'permanently_declined', NOW() - INTERVAL '1 month' + INTERVAL '1 day', 0.0, 'Requested no further contact');

-- Comments for documentation
COMMENT ON TABLE contractors IS 'Internal contractor database for Tier 1 matching';
COMMENT ON TABLE contractor_discovery_cache IS 'Cache of discovery results for performance';
COMMENT ON TABLE contractor_outreach IS 'History of contractor outreach for Tier 2 re-engagement';

COMMENT ON COLUMN contractors.specialties IS 'Array of contractor specialties for GIN index searching';
COMMENT ON COLUMN contractors.zip_codes IS 'Array of service area zip codes for GIN index searching';
COMMENT ON COLUMN contractor_outreach.project_match_score IS 'Calculated match score (0.0-1.0) for project suitability';