-- Migration: Contractor Tiers & Timing System
-- Purpose: Support 3-tier contractor system and response timing

-- =====================================================
-- 1. UPDATE POTENTIAL_CONTRACTORS FOR TIER TRACKING
-- =====================================================

-- Add tier tracking fields
ALTER TABLE potential_contractors
ADD COLUMN IF NOT EXISTS tier INTEGER DEFAULT 3,
ADD COLUMN IF NOT EXISTS last_contacted_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS contact_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS first_contacted_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS converted_to_contractor_at TIMESTAMP;

-- Create index for tier queries
CREATE INDEX IF NOT EXISTS idx_potential_contractors_tier ON potential_contractors(tier);
CREATE INDEX IF NOT EXISTS idx_potential_contractors_last_contact ON potential_contractors(last_contacted_at);

-- Update existing records based on lead_status
UPDATE potential_contractors
SET tier = CASE 
    WHEN lead_status = 'contacted' THEN 2
    WHEN lead_status IN ('new', 'enriched', 'qualified') THEN 3
    ELSE 3
END
WHERE tier IS NULL;

-- =====================================================
-- 2. CREATE CONTRACTOR TIERS VIEW
-- =====================================================

CREATE OR REPLACE VIEW contractor_tiers AS
-- Tier 1: Internal contractors (from contractors table)
SELECT 
    c.id,
    c.business_name as company_name,
    c.email,
    c.phone,
    1 as tier,
    'internal' as tier_name,
    0.90 as expected_response_rate,
    TRUE as is_onboarded,
    c.created_at as onboarded_at,
    NULL::INTEGER as contact_count,
    NULL::TIMESTAMP as last_contacted_at
FROM contractors c
WHERE c.status = 'active'

UNION ALL

-- Tier 2: Prospects (previously contacted)
SELECT 
    pc.id,
    pc.company_name,
    pc.email,
    pc.phone,
    2 as tier,
    'prospect' as tier_name,
    0.50 as expected_response_rate,
    FALSE as is_onboarded,
    NULL::TIMESTAMP as onboarded_at,
    pc.contact_count,
    pc.last_contacted_at
FROM potential_contractors pc
WHERE pc.lead_status = 'contacted'
  AND pc.id NOT IN (SELECT contractor_lead_id FROM contractors WHERE contractor_lead_id IS NOT NULL)

UNION ALL

-- Tier 3: New/Cold (never contacted)
SELECT 
    pc.id,
    pc.company_name,
    pc.email,
    pc.phone,
    3 as tier,
    'new' as tier_name,
    0.33 as expected_response_rate,
    FALSE as is_onboarded,
    NULL::TIMESTAMP as onboarded_at,
    pc.contact_count,
    pc.last_contacted_at
FROM potential_contractors pc
WHERE pc.lead_status IN ('new', 'enriched', 'qualified')
  AND (pc.contact_count = 0 OR pc.contact_count IS NULL)
  AND pc.id NOT IN (SELECT contractor_lead_id FROM contractors WHERE contractor_lead_id IS NOT NULL);

-- =====================================================
-- 3. CONTRACTOR RESPONSE RATE TRACKING
-- =====================================================

CREATE TABLE IF NOT EXISTS contractor_response_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Categorization
    tier INTEGER NOT NULL CHECK (tier IN (1, 2, 3)),
    project_type VARCHAR(100),
    urgency_level VARCHAR(20), -- 'emergency', 'urgent', 'standard', 'flexible'
    location_state VARCHAR(2),
    
    -- Period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Contact Metrics
    total_contacted INTEGER DEFAULT 0,
    total_responded INTEGER DEFAULT 0,
    response_rate DECIMAL(5,2) GENERATED ALWAYS AS 
        (CASE WHEN total_contacted > 0 
         THEN ROUND((total_responded::DECIMAL / total_contacted) * 100, 2)
         ELSE 0 END) STORED,
    
    -- Response Time Metrics
    responses_within_1hr INTEGER DEFAULT 0,
    responses_within_6hr INTEGER DEFAULT 0,
    responses_within_24hr INTEGER DEFAULT 0,
    responses_within_72hr INTEGER DEFAULT 0,
    avg_response_time_hours DECIMAL(8,2),
    
    -- Conversion Metrics
    total_bid_submitted INTEGER DEFAULT 0,
    bid_submission_rate DECIMAL(5,2) GENERATED ALWAYS AS
        (CASE WHEN total_responded > 0
         THEN ROUND((total_bid_submitted::DECIMAL / total_responded) * 100, 2)
         ELSE 0 END) STORED,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for response rate queries
CREATE INDEX idx_response_rates_tier ON contractor_response_rates(tier);
CREATE INDEX idx_response_rates_period ON contractor_response_rates(period_start, period_end);
CREATE INDEX idx_response_rates_project ON contractor_response_rates(project_type);

-- =====================================================
-- 4. CAMPAIGN CHECK-IN SCHEDULE
-- =====================================================

CREATE TABLE IF NOT EXISTS campaign_check_ins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES outreach_campaigns(id),
    
    -- Schedule
    check_in_number INTEGER NOT NULL, -- 1, 2, 3, 4
    check_in_percentage DECIMAL(5,2) NOT NULL, -- 25.0, 50.0, 75.0, 100.0
    scheduled_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    
    -- Expectations vs Reality
    expected_bids INTEGER NOT NULL,
    actual_bids INTEGER DEFAULT 0,
    expected_responses INTEGER NOT NULL,
    actual_responses INTEGER DEFAULT 0,
    
    -- Performance
    on_track BOOLEAN DEFAULT TRUE,
    performance_ratio DECIMAL(5,2) GENERATED ALWAYS AS
        (CASE WHEN expected_bids > 0
         THEN ROUND((actual_bids::DECIMAL / expected_bids) * 100, 2)
         ELSE 0 END) STORED,
    
    -- Escalation
    escalation_needed BOOLEAN DEFAULT FALSE,
    escalation_triggered_at TIMESTAMP,
    contractors_added_tier1 INTEGER DEFAULT 0,
    contractors_added_tier2 INTEGER DEFAULT 0,
    contractors_added_tier3 INTEGER DEFAULT 0,
    escalation_notes TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for check-in queries
CREATE INDEX idx_check_ins_campaign ON campaign_check_ins(campaign_id);
CREATE INDEX idx_check_ins_scheduled ON campaign_check_ins(scheduled_at);
CREATE INDEX idx_check_ins_escalation ON campaign_check_ins(escalation_needed);

-- =====================================================
-- 5. OUTREACH TIMING CONFIGURATION
-- =====================================================

CREATE TABLE IF NOT EXISTS outreach_timing_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Timing Rules
    urgency_level VARCHAR(20) NOT NULL UNIQUE,
    timeline_hours_min INTEGER NOT NULL,
    timeline_hours_max INTEGER NOT NULL,
    
    -- Response Rate Multipliers
    tier1_response_multiplier DECIMAL(3,2) DEFAULT 1.00,
    tier2_response_multiplier DECIMAL(3,2) DEFAULT 1.00,
    tier3_response_multiplier DECIMAL(3,2) DEFAULT 1.00,
    
    -- Check-in Configuration
    check_in_intervals DECIMAL(3,2)[] DEFAULT ARRAY[0.25, 0.50, 0.75],
    escalation_threshold DECIMAL(3,2) DEFAULT 0.75, -- Escalate if <75% of expected
    
    -- Tier Limits
    max_tier1_per_campaign INTEGER DEFAULT 4,
    max_tier2_per_campaign INTEGER DEFAULT 8,
    max_tier3_per_campaign INTEGER DEFAULT 12,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert default timing configurations
INSERT INTO outreach_timing_config (
    urgency_level, timeline_hours_min, timeline_hours_max,
    tier1_response_multiplier, tier2_response_multiplier, tier3_response_multiplier
) VALUES
    ('emergency', 0, 6, 0.70, 0.70, 0.70),
    ('urgent', 6, 24, 0.85, 0.85, 0.85),
    ('standard', 24, 72, 1.00, 1.00, 1.00),
    ('flexible', 72, 168, 1.10, 1.10, 1.10),
    ('planning', 168, 999999, 1.20, 1.20, 1.20)
ON CONFLICT (urgency_level) DO NOTHING;

-- =====================================================
-- 6. FUNCTIONS FOR TIER MANAGEMENT
-- =====================================================

-- Function to get available contractors by tier
CREATE OR REPLACE FUNCTION get_available_contractors_by_tier(
    p_project_type VARCHAR DEFAULT NULL,
    p_location_state VARCHAR DEFAULT NULL,
    p_location_city VARCHAR DEFAULT NULL,
    p_radius_miles INTEGER DEFAULT 50
) RETURNS TABLE (
    tier INTEGER,
    tier_name VARCHAR,
    available_count BIGINT,
    avg_response_rate DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ct.tier,
        ct.tier_name::VARCHAR,
        COUNT(*)::BIGINT as available_count,
        ct.expected_response_rate as avg_response_rate
    FROM contractor_tiers ct
    WHERE 
        -- Location filtering would go here
        (p_location_state IS NULL OR ct.tier = 1) -- Tier 1 works everywhere
        -- Additional filters for specialties, etc.
    GROUP BY ct.tier, ct.tier_name, ct.expected_response_rate
    ORDER BY ct.tier;
END;
$$ LANGUAGE plpgsql;

-- Function to promote contractor to higher tier
CREATE OR REPLACE FUNCTION promote_contractor_tier(
    p_contractor_id UUID,
    p_reason TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    v_current_tier INTEGER;
    v_new_tier INTEGER;
BEGIN
    -- Get current tier from potential_contractors
    SELECT tier INTO v_current_tier
    FROM potential_contractors
    WHERE id = p_contractor_id;
    
    IF v_current_tier IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Determine new tier
    IF v_current_tier = 3 THEN
        v_new_tier := 2;
        
        -- Update to Tier 2 (prospect)
        UPDATE potential_contractors
        SET tier = 2,
            lead_status = 'contacted',
            first_contacted_at = COALESCE(first_contacted_at, NOW()),
            updated_at = NOW()
        WHERE id = p_contractor_id;
        
    ELSIF v_current_tier = 2 THEN
        -- Promote to Tier 1 would involve creating a contractors record
        -- This would be handled by the onboarding process
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 7. TRIGGERS FOR AUTOMATIC UPDATES
-- =====================================================

-- Trigger to update contact tracking
CREATE OR REPLACE FUNCTION update_contractor_contact_tracking()
RETURNS TRIGGER AS $$
BEGIN
    -- Update potential_contractors when contacted
    UPDATE potential_contractors
    SET 
        last_contacted_at = NOW(),
        contact_count = COALESCE(contact_count, 0) + 1,
        first_contacted_at = COALESCE(first_contacted_at, NOW()),
        tier = CASE 
            WHEN tier = 3 AND contact_count = 0 THEN 2
            ELSE tier
        END,
        lead_status = CASE
            WHEN lead_status IN ('new', 'enriched', 'qualified') THEN 'contacted'
            ELSE lead_status
        END
    WHERE id = NEW.contractor_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to bid_card_distributions
CREATE TRIGGER track_contractor_contact
    AFTER INSERT ON bid_card_distributions
    FOR EACH ROW
    EXECUTE FUNCTION update_contractor_contact_tracking();

-- =====================================================
-- 8. REPORTING VIEWS
-- =====================================================

-- View for tier performance metrics
CREATE OR REPLACE VIEW tier_performance_summary AS
SELECT 
    t.tier,
    t.tier_name,
    COUNT(DISTINCT ct.id) as total_contractors,
    COUNT(DISTINCT bd.id) as total_contacted,
    COUNT(DISTINCT CASE WHEN cr.id IS NOT NULL THEN bd.contractor_id END) as total_responded,
    ROUND(
        CASE WHEN COUNT(DISTINCT bd.id) > 0
        THEN (COUNT(DISTINCT CASE WHEN cr.id IS NOT NULL THEN bd.contractor_id END)::DECIMAL / 
              COUNT(DISTINCT bd.id)) * 100
        ELSE 0 END, 2
    ) as actual_response_rate,
    t.expected_response_rate * 100 as expected_response_rate,
    COUNT(DISTINCT CASE WHEN b.id IS NOT NULL THEN bd.contractor_id END) as total_bid_submitted
FROM contractor_tiers t
LEFT JOIN bid_card_distributions bd ON bd.contractor_id = t.id
LEFT JOIN contractor_responses cr ON cr.contractor_id = t.id AND cr.bid_card_id = bd.bid_card_id
LEFT JOIN bids b ON b.contractor_id = t.id AND b.project_id IN (
    SELECT project_id FROM bid_cards WHERE id = bd.bid_card_id
)
GROUP BY t.tier, t.tier_name, t.expected_response_rate;

-- =====================================================
-- 9. INDEXES FOR PERFORMANCE
-- =====================================================

-- Additional indexes for tier queries
CREATE INDEX IF NOT EXISTS idx_contractors_status ON contractors(status);
CREATE INDEX IF NOT EXISTS idx_potential_contractors_compound 
    ON potential_contractors(lead_status, tier, contact_count);

-- Index for response tracking
CREATE INDEX IF NOT EXISTS idx_bid_distributions_tracking 
    ON bid_card_distributions(contractor_id, bid_card_id, responded_at);

COMMENT ON TABLE contractor_response_rates IS 'Historical response rates by tier, project type, and urgency';
COMMENT ON TABLE campaign_check_ins IS 'Scheduled check-ins for monitoring campaign progress';
COMMENT ON TABLE outreach_timing_config IS 'Configuration for timing rules and response expectations';
COMMENT ON VIEW contractor_tiers IS 'Unified view of all contractors across 3 tiers';
COMMENT ON VIEW tier_performance_summary IS 'Performance metrics by contractor tier';