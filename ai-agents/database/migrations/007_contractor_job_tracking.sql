-- Migration: Track Unique Job Opportunities Per Contractor
-- Purpose: Track how many different jobs each contractor has been contacted about

-- =====================================================
-- 1. CONTRACTOR JOB OPPORTUNITIES TRACKING
-- =====================================================

-- Track each unique job opportunity sent to a contractor
CREATE TABLE IF NOT EXISTS contractor_job_opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_id UUID NOT NULL REFERENCES potential_contractors(id),
    bid_card_id UUID NOT NULL REFERENCES bid_cards(id),
    
    -- Job Details (denormalized for quick access)
    project_type VARCHAR(100),
    project_location_city VARCHAR(100),
    project_location_state VARCHAR(2),
    project_urgency VARCHAR(20),
    
    -- Contact Details
    first_contacted_at TIMESTAMP DEFAULT NOW(),
    last_contacted_at TIMESTAMP DEFAULT NOW(),
    contact_count INTEGER DEFAULT 1,
    contact_methods TEXT[], -- ['email', 'sms', 'website_form']
    
    -- Response Tracking
    contractor_responded BOOLEAN DEFAULT FALSE,
    responded_at TIMESTAMP,
    response_type VARCHAR(50), -- 'interested', 'not_interested', 'busy', 'out_of_area'
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Prevent duplicate job sends
    UNIQUE(contractor_id, bid_card_id)
);

-- Indexes for performance
CREATE INDEX idx_contractor_jobs_contractor ON contractor_job_opportunities(contractor_id);
CREATE INDEX idx_contractor_jobs_bid_card ON contractor_job_opportunities(bid_card_id);
CREATE INDEX idx_contractor_jobs_responded ON contractor_job_opportunities(contractor_responded);

-- =====================================================
-- 2. CONTRACTOR PREFERENCES & OPT-OUTS
-- =====================================================

CREATE TABLE IF NOT EXISTS contractor_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_id UUID NOT NULL REFERENCES potential_contractors(id) UNIQUE,
    
    -- Communication Preferences
    opted_out BOOLEAN DEFAULT FALSE,
    opted_out_at TIMESTAMP,
    opt_out_reason TEXT,
    
    -- Contact Preferences
    preferred_contact_method VARCHAR(50), -- 'email', 'sms', 'phone'
    do_not_contact_before TIME,
    do_not_contact_after TIME,
    preferred_days_of_week INTEGER[], -- 1=Monday, 7=Sunday
    
    -- Project Preferences
    interested_project_types TEXT[],
    not_interested_project_types TEXT[],
    minimum_project_budget DECIMAL(10,2),
    maximum_distance_miles INTEGER,
    
    -- Frequency Limits
    max_contacts_per_week INTEGER DEFAULT 3,
    max_contacts_per_month INTEGER DEFAULT 10,
    
    -- Notes
    internal_notes TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- 3. UPDATE POTENTIAL_CONTRACTORS TABLE
-- =====================================================

-- Add job tracking fields
ALTER TABLE potential_contractors
ADD COLUMN IF NOT EXISTS total_jobs_sent INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS unique_project_types_sent TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS last_job_sent_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS opted_out BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS opted_out_at TIMESTAMP;

-- =====================================================
-- 4. VIEWS FOR EASY QUERYING
-- =====================================================

-- View for contractor contact history
CREATE OR REPLACE VIEW contractor_contact_summary AS
SELECT 
    pc.id as contractor_id,
    pc.company_name,
    pc.tier,
    pc.lead_status,
    pc.total_jobs_sent,
    pc.opted_out,
    COUNT(DISTINCT cjo.bid_card_id) as unique_jobs_contacted,
    COUNT(DISTINCT cjo.project_type) as unique_project_types,
    SUM(cjo.contact_count) as total_contact_attempts,
    COUNT(DISTINCT CASE WHEN cjo.contractor_responded THEN cjo.id END) as jobs_responded_to,
    ROUND(
        CASE WHEN COUNT(DISTINCT cjo.id) > 0
        THEN (COUNT(DISTINCT CASE WHEN cjo.contractor_responded THEN cjo.id END)::DECIMAL / 
              COUNT(DISTINCT cjo.id)) * 100
        ELSE 0 END, 2
    ) as response_rate,
    MAX(cjo.last_contacted_at) as most_recent_contact,
    cp.max_contacts_per_week,
    cp.max_contacts_per_month
FROM potential_contractors pc
LEFT JOIN contractor_job_opportunities cjo ON cjo.contractor_id = pc.id
LEFT JOIN contractor_preferences cp ON cp.contractor_id = pc.id
GROUP BY 
    pc.id, pc.company_name, pc.tier, pc.lead_status, 
    pc.total_jobs_sent, pc.opted_out,
    cp.max_contacts_per_week, cp.max_contacts_per_month;

-- View for contractors eligible for new jobs
CREATE OR REPLACE VIEW eligible_contractors AS
SELECT 
    ct.*,
    ccs.unique_jobs_contacted,
    ccs.total_contact_attempts,
    ccs.response_rate,
    ccs.most_recent_contact,
    -- Check weekly limit
    (
        SELECT COUNT(*) 
        FROM contractor_job_opportunities 
        WHERE contractor_id = ct.id 
        AND first_contacted_at >= NOW() - INTERVAL '7 days'
    ) as contacts_this_week,
    -- Check monthly limit
    (
        SELECT COUNT(*) 
        FROM contractor_job_opportunities 
        WHERE contractor_id = ct.id 
        AND first_contacted_at >= NOW() - INTERVAL '30 days'
    ) as contacts_this_month
FROM contractor_tiers ct
JOIN contractor_contact_summary ccs ON ccs.contractor_id = ct.id
WHERE 
    -- Not opted out
    (ccs.opted_out IS FALSE OR ccs.opted_out IS NULL)
    -- Within contact limits
    AND (
        ccs.max_contacts_per_week IS NULL 
        OR (
            SELECT COUNT(*) 
            FROM contractor_job_opportunities 
            WHERE contractor_id = ct.id 
            AND first_contacted_at >= NOW() - INTERVAL '7 days'
        ) < COALESCE(ccs.max_contacts_per_week, 3)
    )
    AND (
        ccs.max_contacts_per_month IS NULL 
        OR (
            SELECT COUNT(*) 
            FROM contractor_job_opportunities 
            WHERE contractor_id = ct.id 
            AND first_contacted_at >= NOW() - INTERVAL '30 days'
        ) < COALESCE(ccs.max_contacts_per_month, 10)
    );

-- =====================================================
-- 5. FUNCTIONS FOR TRACKING
-- =====================================================

-- Function to record job opportunity sent to contractor
CREATE OR REPLACE FUNCTION record_contractor_job_opportunity(
    p_contractor_id UUID,
    p_bid_card_id UUID,
    p_contact_method VARCHAR
) RETURNS BOOLEAN AS $$
DECLARE
    v_project_type VARCHAR;
    v_city VARCHAR;
    v_state VARCHAR;
    v_urgency VARCHAR;
BEGIN
    -- Get bid card details
    SELECT 
        bc.project_type,
        bc.location->>'city',
        bc.location->>'state',
        bc.urgency_level
    INTO v_project_type, v_city, v_state, v_urgency
    FROM bid_cards bc
    WHERE bc.id = p_bid_card_id;
    
    -- Insert or update job opportunity
    INSERT INTO contractor_job_opportunities (
        contractor_id,
        bid_card_id,
        project_type,
        project_location_city,
        project_location_state,
        project_urgency,
        contact_methods
    ) VALUES (
        p_contractor_id,
        p_bid_card_id,
        v_project_type,
        v_city,
        v_state,
        v_urgency,
        ARRAY[p_contact_method]
    )
    ON CONFLICT (contractor_id, bid_card_id) DO UPDATE
    SET 
        last_contacted_at = NOW(),
        contact_count = contractor_job_opportunities.contact_count + 1,
        contact_methods = CASE 
            WHEN p_contact_method = ANY(contractor_job_opportunities.contact_methods)
            THEN contractor_job_opportunities.contact_methods
            ELSE array_append(contractor_job_opportunities.contact_methods, p_contact_method)
        END,
        updated_at = NOW();
    
    -- Update contractor summary
    UPDATE potential_contractors
    SET 
        total_jobs_sent = (
            SELECT COUNT(DISTINCT bid_card_id) 
            FROM contractor_job_opportunities 
            WHERE contractor_id = p_contractor_id
        ),
        unique_project_types_sent = (
            SELECT array_agg(DISTINCT project_type) 
            FROM contractor_job_opportunities 
            WHERE contractor_id = p_contractor_id
        ),
        last_job_sent_at = NOW()
    WHERE id = p_contractor_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 6. TRIGGERS FOR AUTOMATIC TRACKING
-- =====================================================

-- Trigger to track job opportunities when distributions are created
CREATE OR REPLACE FUNCTION track_job_opportunity()
RETURNS TRIGGER AS $$
BEGIN
    -- Record the job opportunity
    PERFORM record_contractor_job_opportunity(
        NEW.contractor_id,
        NEW.bid_card_id,
        NEW.method
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER track_contractor_job_opportunity
    AFTER INSERT ON bid_card_distributions
    FOR EACH ROW
    EXECUTE FUNCTION track_job_opportunity();

-- =====================================================
-- 7. SAMPLE QUERIES
-- =====================================================

/*
-- Find contractors who haven't been contacted in 30 days
SELECT * FROM contractor_contact_summary
WHERE most_recent_contact < NOW() - INTERVAL '30 days'
AND opted_out = FALSE
ORDER BY response_rate DESC;

-- Find contractors contacted too frequently
SELECT * FROM contractor_contact_summary
WHERE contacts_this_week >= 3
OR contacts_this_month >= 10;

-- Get eligible Tier 2 contractors for a new job
SELECT * FROM eligible_contractors
WHERE tier = 2
AND response_rate > 40
ORDER BY response_rate DESC
LIMIT 10;

-- Check contractor's job history
SELECT 
    cjo.*,
    bc.title as job_title
FROM contractor_job_opportunities cjo
JOIN bid_cards bc ON bc.id = cjo.bid_card_id
WHERE cjo.contractor_id = 'contractor-uuid-here'
ORDER BY cjo.first_contacted_at DESC;
*/

COMMENT ON TABLE contractor_job_opportunities IS 'Tracks unique job opportunities sent to each contractor';
COMMENT ON TABLE contractor_preferences IS 'Contractor communication preferences and opt-out status';
COMMENT ON VIEW contractor_contact_summary IS 'Summary of all contractor contacts and response rates';
COMMENT ON VIEW eligible_contractors IS 'Contractors eligible for new job opportunities based on preferences and limits';