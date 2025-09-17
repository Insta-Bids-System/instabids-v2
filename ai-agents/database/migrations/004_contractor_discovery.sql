-- Migration: Contractor Discovery System
-- Purpose: Core tables for discovering and tracking contractor leads

-- Contractor size enum
CREATE TYPE contractor_size AS ENUM (
    'solo_handyman',
    'owner_operator', 
    'small_business',
    'regional_company',
    'national_chain'
);

-- Lead status enum
CREATE TYPE lead_status AS ENUM (
    'new',
    'enriching', 
    'enriched',
    'qualified',
    'disqualified',
    'contacted',
    'opted_out'
);

-- Discovery source enum
CREATE TYPE discovery_source AS ENUM (
    'google_maps',
    'yelp',
    'angi',
    'bbb',
    'homeadvisor',
    'thumbtack',
    'facebook',
    'nextdoor',
    'craigslist',
    'referral',
    'manual',
    'other'
);

-- Main contractor leads table
CREATE TABLE contractor_leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Discovery Information
    source discovery_source NOT NULL,
    source_url TEXT,
    source_id VARCHAR(255), -- External ID from source
    discovery_run_id UUID,
    discovered_at TIMESTAMP DEFAULT NOW(),
    
    -- Basic Company Information
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(255),
    website TEXT,
    
    -- Location Data
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    service_radius_miles INT,
    service_zip_codes TEXT[],
    
    -- Business Classification
    contractor_size contractor_size,
    estimated_employees VARCHAR(20), -- '1', '2-5', '6-10', etc
    years_in_business INT,
    business_established_year INT,
    
    -- Capabilities & Specialties
    specialties TEXT[], -- ['kitchen', 'bathroom', 'plumbing', etc]
    certifications TEXT[],
    license_number VARCHAR(100),
    license_state VARCHAR(2),
    license_verified BOOLEAN DEFAULT FALSE,
    insurance_verified BOOLEAN DEFAULT FALSE,
    bonded BOOLEAN DEFAULT FALSE,
    
    -- Ratings & Reviews
    rating DECIMAL(3,2), -- 0.00 to 5.00
    review_count INT DEFAULT 0,
    recent_reviews JSONB, -- Array of recent reviews
    last_review_date DATE,
    
    -- Quality Scoring
    lead_score INT DEFAULT 0, -- 0-100 overall quality score
    data_completeness INT DEFAULT 0, -- 0-100 how complete the data is
    
    -- Raw & Enrichment Data
    raw_data JSONB, -- Complete data from discovery source
    enrichment_data JSONB, -- Additional enriched data
    
    -- Status Tracking
    lead_status lead_status DEFAULT 'new',
    disqualification_reason TEXT,
    disqualified_at TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_enriched_at TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX idx_contractor_leads_location ON contractor_leads(state, city, zip_code);
CREATE INDEX idx_contractor_leads_size ON contractor_leads(contractor_size);
CREATE INDEX idx_contractor_leads_specialties ON contractor_leads USING GIN(specialties);
CREATE INDEX idx_contractor_leads_status ON contractor_leads(lead_status);
CREATE INDEX idx_contractor_leads_score ON contractor_leads(lead_score DESC);
CREATE INDEX idx_contractor_leads_source ON contractor_leads(source, discovered_at);

-- Discovery runs tracking
CREATE TABLE discovery_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bid_card_id UUID,
    
    -- Search Parameters
    search_parameters JSONB NOT NULL, -- Complete search criteria
    location VARCHAR(255),
    radius_miles INT,
    project_type VARCHAR(100),
    contractor_sizes contractor_size[],
    minimum_rating DECIMAL(3,2),
    license_required BOOLEAN DEFAULT TRUE,
    target_count INT DEFAULT 10, -- How many to find
    
    -- Execution Details
    sources_to_search discovery_source[],
    sources_completed discovery_source[],
    
    -- Results Summary
    total_found INT DEFAULT 0,
    qualified_count INT DEFAULT 0,
    disqualified_count INT DEFAULT 0,
    duplicate_count INT DEFAULT 0,
    
    -- Performance Metrics
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_seconds INT,
    api_calls_made INT DEFAULT 0,
    api_cost_cents INT DEFAULT 0,
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed
    current_source discovery_source,
    error_message TEXT,
    error_details JSONB
);

CREATE INDEX idx_discovery_runs_status ON discovery_runs(status, started_at);
CREATE INDEX idx_discovery_runs_bid_card ON discovery_runs(bid_card_id);

-- Lead enrichment tracking
CREATE TABLE lead_enrichment_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_lead_id UUID NOT NULL REFERENCES contractor_leads(id),
    
    -- Task Details
    enrichment_type VARCHAR(50) NOT NULL, -- 'license_verify', 'insurance_check', 'reviews_fetch', 'business_verify'
    priority INT DEFAULT 5, -- 1-10, 1 is highest
    
    -- Execution
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    attempts INT DEFAULT 0,
    max_attempts INT DEFAULT 3,
    
    -- Results
    success BOOLEAN,
    enrichment_data JSONB,
    error_message TEXT,
    
    -- Timing
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    next_retry_at TIMESTAMP
);

CREATE INDEX idx_enrichment_tasks_status ON lead_enrichment_tasks(status, priority, created_at);
CREATE INDEX idx_enrichment_tasks_lead ON lead_enrichment_tasks(contractor_lead_id);

-- Function to update lead score based on data completeness and quality
CREATE OR REPLACE FUNCTION calculate_lead_score(lead_id UUID)
RETURNS INT AS $$
DECLARE
    lead RECORD;
    score INT := 0;
BEGIN
    SELECT * INTO lead FROM contractor_leads WHERE id = lead_id;
    
    -- Base score for having data
    score := 10;
    
    -- Contact information (30 points max)
    IF lead.email IS NOT NULL THEN score := score + 10; END IF;
    IF lead.phone IS NOT NULL THEN score := score + 10; END IF;
    IF lead.website IS NOT NULL THEN score := score + 10; END IF;
    
    -- Business verification (25 points max)
    IF lead.license_verified THEN score := score + 15; END IF;
    IF lead.insurance_verified THEN score := score + 10; END IF;
    
    -- Ratings and reviews (25 points max)
    IF lead.rating >= 4.5 AND lead.review_count >= 10 THEN
        score := score + 25;
    ELSIF lead.rating >= 4.0 AND lead.review_count >= 5 THEN
        score := score + 15;
    ELSIF lead.rating >= 3.5 THEN
        score := score + 5;
    END IF;
    
    -- Business maturity (10 points max)
    IF lead.years_in_business >= 5 THEN
        score := score + 10;
    ELSIF lead.years_in_business >= 2 THEN
        score := score + 5;
    END IF;
    
    -- Data completeness (10 points max)
    IF lead.contractor_size IS NOT NULL THEN score := score + 5; END IF;
    IF array_length(lead.specialties, 1) > 0 THEN score := score + 5; END IF;
    
    -- Update the lead with calculated score
    UPDATE contractor_leads 
    SET lead_score = score,
        updated_at = NOW()
    WHERE id = lead_id;
    
    RETURN score;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_contractor_leads_updated_at 
    BEFORE UPDATE ON contractor_leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Sample data for testing (commented out for production)
/*
INSERT INTO contractor_leads (
    source, company_name, phone, email, 
    city, state, zip_code, contractor_size,
    specialties, rating, review_count
) VALUES 
    ('google_maps', 'Orlando Kitchen Pros', '407-555-0001', 'info@orlandokitchen.com',
     'Orlando', 'FL', '32801', 'small_business',
     ARRAY['kitchen', 'bathroom'], 4.8, 156),
    ('yelp', 'Mike''s Handyman Service', '407-555-0002', 'mike@handyman.com',
     'Orlando', 'FL', '32803', 'solo_handyman',
     ARRAY['general', 'repairs'], 4.6, 89);
*/