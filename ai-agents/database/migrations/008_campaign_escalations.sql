-- Migration: Campaign Escalations and Strategy Storage
-- Purpose: Support intelligent campaign orchestration with check-ins and escalations

-- =====================================================
-- 1. CAMPAIGN ESCALATION TRACKING
-- =====================================================

CREATE TABLE IF NOT EXISTS campaign_escalations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES outreach_campaigns(id),
    check_in_id INTEGER NOT NULL,
    
    -- Escalation Details
    escalation_level VARCHAR(20) NOT NULL, -- 'none', 'mild', 'moderate', 'severe', 'critical'
    performance_ratio DECIMAL(5,2) NOT NULL,
    bids_expected INTEGER NOT NULL,
    bids_received INTEGER NOT NULL,
    
    -- Actions Taken
    actions_taken TEXT[],
    contractors_added_tier1 INTEGER DEFAULT 0,
    contractors_added_tier2 INTEGER DEFAULT 0,
    contractors_added_tier3 INTEGER DEFAULT 0,
    
    -- Outcome
    escalation_successful BOOLEAN,
    final_bid_count INTEGER,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

-- Index for quick lookups
CREATE INDEX idx_escalations_campaign ON campaign_escalations(campaign_id);
CREATE INDEX idx_escalations_level ON campaign_escalations(escalation_level);

-- =====================================================
-- 2. OUTREACH QUEUE FOR AUTOMATED SENDING
-- =====================================================

CREATE TABLE IF NOT EXISTS outreach_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES outreach_campaigns(id),
    contractor_id UUID NOT NULL,
    
    -- Message Details
    message_type VARCHAR(50) NOT NULL, -- 'initial', 'reminder', 'urgent_reminder', 'final_notice'
    channel VARCHAR(20) NOT NULL, -- 'email', 'sms', 'website_form'
    priority VARCHAR(10) DEFAULT 'normal', -- 'low', 'normal', 'high', 'urgent'
    
    -- Content
    subject TEXT,
    message_body TEXT,
    template_id UUID,
    personalization_data JSONB,
    
    -- Scheduling
    scheduled_for TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'sending', 'sent', 'failed', 'cancelled'
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for queue processing
CREATE INDEX idx_outreach_queue_status ON outreach_queue(status);
CREATE INDEX idx_outreach_queue_scheduled ON outreach_queue(scheduled_for);
CREATE INDEX idx_outreach_queue_priority ON outreach_queue(priority, scheduled_for);

-- =====================================================
-- 3. ENHANCED CAMPAIGN TRACKING
-- =====================================================

-- Add strategy storage to outreach_campaigns
ALTER TABLE outreach_campaigns
ADD COLUMN IF NOT EXISTS strategy_data JSONB,
ADD COLUMN IF NOT EXISTS escalated BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS priority VARCHAR(10) DEFAULT 'normal';

-- =====================================================
-- 4. REAL-TIME RESPONSE TRACKING
-- =====================================================

CREATE TABLE IF NOT EXISTS campaign_response_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES outreach_campaigns(id),
    
    -- Snapshot Time
    snapshot_time TIMESTAMP DEFAULT NOW(),
    hours_since_start DECIMAL(5,2),
    
    -- Metrics at this point
    contractors_contacted INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    links_clicked INTEGER DEFAULT 0,
    forms_viewed INTEGER DEFAULT 0,
    responses_received INTEGER DEFAULT 0,
    bids_submitted INTEGER DEFAULT 0,
    
    -- Tier Breakdown
    tier1_contacted INTEGER DEFAULT 0,
    tier1_responded INTEGER DEFAULT 0,
    tier2_contacted INTEGER DEFAULT 0,
    tier2_responded INTEGER DEFAULT 0,
    tier3_contacted INTEGER DEFAULT 0,
    tier3_responded INTEGER DEFAULT 0,
    
    -- Response Rates
    overall_response_rate DECIMAL(5,2),
    tier1_response_rate DECIMAL(5,2),
    tier2_response_rate DECIMAL(5,2),
    tier3_response_rate DECIMAL(5,2)
);

-- Index for time-based queries
CREATE INDEX idx_response_tracking_campaign_time ON campaign_response_tracking(campaign_id, snapshot_time);

-- =====================================================
-- 5. AUTOMATED CHECK-IN RESULTS
-- =====================================================

ALTER TABLE campaign_check_ins
ADD COLUMN IF NOT EXISTS contractors_added_tier1 INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS contractors_added_tier2 INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS contractors_added_tier3 INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS escalation_actions TEXT[],
ADD COLUMN IF NOT EXISTS performance_summary JSONB;

-- =====================================================
-- 6. FUNCTIONS FOR REAL-TIME TRACKING
-- =====================================================

-- Function to calculate current campaign performance
CREATE OR REPLACE FUNCTION calculate_campaign_performance(p_campaign_id UUID)
RETURNS TABLE (
    total_contractors INTEGER,
    contacted INTEGER,
    responded INTEGER,
    bids_submitted INTEGER,
    current_response_rate DECIMAL,
    projected_final_bids INTEGER
) AS $$
DECLARE
    v_start_time TIMESTAMP;
    v_total_hours DECIMAL;
    v_elapsed_hours DECIMAL;
    v_progress_ratio DECIMAL;
BEGIN
    -- Get campaign start time
    SELECT started_at INTO v_start_time
    FROM outreach_campaigns
    WHERE id = p_campaign_id;
    
    -- Calculate elapsed time
    v_elapsed_hours := EXTRACT(EPOCH FROM (NOW() - v_start_time)) / 3600;
    
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT cc.contractor_id)::INTEGER as total_contractors,
        COUNT(DISTINCT CASE WHEN bd.sent_at IS NOT NULL THEN cc.contractor_id END)::INTEGER as contacted,
        COUNT(DISTINCT CASE WHEN cr.responded_at IS NOT NULL THEN cc.contractor_id END)::INTEGER as responded,
        COUNT(DISTINCT b.contractor_id)::INTEGER as bids_submitted,
        CASE 
            WHEN COUNT(DISTINCT CASE WHEN bd.sent_at IS NOT NULL THEN cc.contractor_id END) > 0
            THEN ROUND((COUNT(DISTINCT CASE WHEN cr.responded_at IS NOT NULL THEN cc.contractor_id END)::DECIMAL / 
                  COUNT(DISTINCT CASE WHEN bd.sent_at IS NOT NULL THEN cc.contractor_id END)) * 100, 2)
            ELSE 0
        END as current_response_rate,
        -- Project final bids based on current rate
        CASE 
            WHEN v_elapsed_hours > 0 AND COUNT(DISTINCT b.contractor_id) > 0
            THEN ROUND(COUNT(DISTINCT b.contractor_id)::DECIMAL / v_elapsed_hours * 24)::INTEGER
            ELSE 0
        END as projected_final_bids
    FROM campaign_contractors cc
    LEFT JOIN bid_card_distributions bd ON bd.contractor_id = cc.contractor_id 
        AND bd.campaign_id = cc.campaign_id
    LEFT JOIN contractor_responses cr ON cr.contractor_id = cc.contractor_id 
        AND cr.campaign_id = cc.campaign_id
    LEFT JOIN bids b ON b.contractor_id = cc.contractor_id 
        AND b.bid_card_id = (SELECT bid_card_id FROM outreach_campaigns WHERE id = p_campaign_id)
    WHERE cc.campaign_id = p_campaign_id;
END;
$$ LANGUAGE plpgsql;

-- Function to record response tracking snapshot
CREATE OR REPLACE FUNCTION record_campaign_snapshot(p_campaign_id UUID)
RETURNS VOID AS $$
DECLARE
    v_snapshot RECORD;
    v_start_time TIMESTAMP;
BEGIN
    -- Get campaign start time
    SELECT started_at INTO v_start_time
    FROM outreach_campaigns
    WHERE id = p_campaign_id;
    
    -- Calculate current metrics
    WITH metrics AS (
        SELECT 
            p_campaign_id as campaign_id,
            EXTRACT(EPOCH FROM (NOW() - v_start_time)) / 3600 as hours_since_start,
            COUNT(DISTINCT CASE WHEN bd.sent_at IS NOT NULL THEN cc.contractor_id END) as contractors_contacted,
            COUNT(DISTINCT CASE WHEN et.event_type = 'opened' THEN cc.contractor_id END) as emails_opened,
            COUNT(DISTINCT CASE WHEN et.event_type = 'clicked' THEN cc.contractor_id END) as links_clicked,
            COUNT(DISTINCT CASE WHEN bcv.viewed_at IS NOT NULL THEN cc.contractor_id END) as forms_viewed,
            COUNT(DISTINCT CASE WHEN cr.responded_at IS NOT NULL THEN cc.contractor_id END) as responses_received,
            COUNT(DISTINCT b.contractor_id) as bids_submitted,
            -- Tier breakdowns
            COUNT(DISTINCT CASE WHEN ct.tier = 1 AND bd.sent_at IS NOT NULL THEN cc.contractor_id END) as tier1_contacted,
            COUNT(DISTINCT CASE WHEN ct.tier = 1 AND cr.responded_at IS NOT NULL THEN cc.contractor_id END) as tier1_responded,
            COUNT(DISTINCT CASE WHEN ct.tier = 2 AND bd.sent_at IS NOT NULL THEN cc.contractor_id END) as tier2_contacted,
            COUNT(DISTINCT CASE WHEN ct.tier = 2 AND cr.responded_at IS NOT NULL THEN cc.contractor_id END) as tier2_responded,
            COUNT(DISTINCT CASE WHEN ct.tier = 3 AND bd.sent_at IS NOT NULL THEN cc.contractor_id END) as tier3_contacted,
            COUNT(DISTINCT CASE WHEN ct.tier = 3 AND cr.responded_at IS NOT NULL THEN cc.contractor_id END) as tier3_responded
        FROM campaign_contractors cc
        LEFT JOIN contractor_tiers ct ON ct.id = cc.contractor_id
        LEFT JOIN bid_card_distributions bd ON bd.contractor_id = cc.contractor_id 
            AND bd.campaign_id = cc.campaign_id
        LEFT JOIN email_tracking_events et ON et.distribution_id = bd.id
        LEFT JOIN bid_card_views bcv ON bcv.bid_card_id = bd.bid_card_id 
            AND bcv.contractor_id = cc.contractor_id
        LEFT JOIN contractor_responses cr ON cr.contractor_id = cc.contractor_id 
            AND cr.campaign_id = cc.campaign_id
        LEFT JOIN bids b ON b.contractor_id = cc.contractor_id 
            AND b.bid_card_id = (SELECT bid_card_id FROM outreach_campaigns WHERE id = p_campaign_id)
        WHERE cc.campaign_id = p_campaign_id
    )
    INSERT INTO campaign_response_tracking (
        campaign_id,
        hours_since_start,
        contractors_contacted,
        emails_opened,
        links_clicked,
        forms_viewed,
        responses_received,
        bids_submitted,
        tier1_contacted,
        tier1_responded,
        tier2_contacted,
        tier2_responded,
        tier3_contacted,
        tier3_responded,
        overall_response_rate,
        tier1_response_rate,
        tier2_response_rate,
        tier3_response_rate
    )
    SELECT 
        campaign_id,
        hours_since_start,
        contractors_contacted,
        emails_opened,
        links_clicked,
        forms_viewed,
        responses_received,
        bids_submitted,
        tier1_contacted,
        tier1_responded,
        tier2_contacted,
        tier2_responded,
        tier3_contacted,
        tier3_responded,
        CASE WHEN contractors_contacted > 0 
            THEN ROUND((responses_received::DECIMAL / contractors_contacted) * 100, 2)
            ELSE 0 END,
        CASE WHEN tier1_contacted > 0 
            THEN ROUND((tier1_responded::DECIMAL / tier1_contacted) * 100, 2)
            ELSE 0 END,
        CASE WHEN tier2_contacted > 0 
            THEN ROUND((tier2_responded::DECIMAL / tier2_contacted) * 100, 2)
            ELSE 0 END,
        CASE WHEN tier3_contacted > 0 
            THEN ROUND((tier3_responded::DECIMAL / tier3_contacted) * 100, 2)
            ELSE 0 END
    FROM metrics;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 7. TRIGGERS FOR AUTOMATIC TRACKING
-- =====================================================

-- Trigger to update campaign priority on escalation
CREATE OR REPLACE FUNCTION update_campaign_priority()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.escalation_level IN ('severe', 'critical') THEN
        UPDATE outreach_campaigns
        SET priority = 'urgent',
            escalated = TRUE
        WHERE id = NEW.campaign_id;
    ELSIF NEW.escalation_level = 'moderate' THEN
        UPDATE outreach_campaigns
        SET priority = 'high'
        WHERE id = NEW.campaign_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_campaign_priority
    AFTER INSERT ON campaign_escalations
    FOR EACH ROW
    EXECUTE FUNCTION update_campaign_priority();

-- =====================================================
-- 8. VIEWS FOR MONITORING
-- =====================================================

-- Real-time campaign status view
CREATE OR REPLACE VIEW campaign_status_realtime AS
SELECT 
    oc.id as campaign_id,
    oc.name as campaign_name,
    oc.status,
    oc.priority,
    oc.escalated,
    oc.bid_card_id,
    oc.started_at,
    EXTRACT(EPOCH FROM (NOW() - oc.started_at)) / 3600 as hours_elapsed,
    oc.strategy_data->>'timeline_hours' as timeline_hours,
    oc.strategy_data->>'bids_needed' as bids_needed,
    oc.strategy_data->>'expected_responses' as expected_responses,
    oc.strategy_data->>'confidence_score' as confidence_score,
    perf.contacted,
    perf.responded,
    perf.bids_submitted,
    perf.current_response_rate,
    perf.projected_final_bids,
    CASE 
        WHEN perf.bids_submitted >= (oc.strategy_data->>'bids_needed')::INTEGER THEN 'SUCCESS'
        WHEN perf.projected_final_bids >= (oc.strategy_data->>'bids_needed')::INTEGER THEN 'ON_TRACK'
        WHEN oc.escalated THEN 'ESCALATED'
        ELSE 'AT_RISK'
    END as performance_status
FROM outreach_campaigns oc
CROSS JOIN LATERAL calculate_campaign_performance(oc.id) perf
WHERE oc.status = 'active';

-- Campaign escalation history view
CREATE OR REPLACE VIEW campaign_escalation_history AS
SELECT 
    ce.campaign_id,
    oc.name as campaign_name,
    ce.check_in_id,
    ce.escalation_level,
    ce.performance_ratio,
    ce.bids_expected,
    ce.bids_received,
    ce.actions_taken,
    ce.contractors_added_tier1 + ce.contractors_added_tier2 + ce.contractors_added_tier3 as total_contractors_added,
    ce.escalation_successful,
    ce.created_at as escalated_at,
    ce.resolved_at
FROM campaign_escalations ce
JOIN outreach_campaigns oc ON oc.id = ce.campaign_id
ORDER BY ce.created_at DESC;

-- =====================================================
-- 9. INDEXES FOR PERFORMANCE
-- =====================================================

CREATE INDEX idx_outreach_campaigns_status_priority ON outreach_campaigns(status, priority);
CREATE INDEX idx_outreach_campaigns_escalated ON outreach_campaigns(escalated) WHERE escalated = TRUE;
CREATE INDEX idx_campaign_response_tracking_recent ON campaign_response_tracking(campaign_id, snapshot_time DESC);

COMMENT ON TABLE campaign_escalations IS 'Tracks when campaigns need additional contractors due to low response';
COMMENT ON TABLE outreach_queue IS 'Queue for automated message sending across all channels';
COMMENT ON TABLE campaign_response_tracking IS 'Time-series data for campaign performance monitoring';
COMMENT ON VIEW campaign_status_realtime IS 'Real-time view of active campaign performance';
COMMENT ON FUNCTION calculate_campaign_performance IS 'Calculate current performance metrics for a campaign';
COMMENT ON FUNCTION record_campaign_snapshot IS 'Record a point-in-time snapshot of campaign metrics';