-- Migration: Contractor Outreach Tracking
-- Purpose: Track all contractor outreach attempts and engagement

-- Outreach channel enum
CREATE TYPE outreach_channel AS ENUM (
    'email',
    'sms',
    'phone',
    'whatsapp',
    'linkedin',
    'facebook',
    'mail',
    'in_person'
);

-- Outreach status enum
CREATE TYPE outreach_status AS ENUM (
    'queued',
    'sending',
    'sent',
    'delivered',
    'opened',
    'clicked',
    'responded',
    'bounced',
    'failed',
    'opted_out'
);

-- Response sentiment enum
CREATE TYPE response_sentiment AS ENUM (
    'positive',
    'negative',
    'neutral',
    'question',
    'opt_out'
);

-- Main outreach tracking table
CREATE TABLE contractor_outreach_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_lead_id UUID NOT NULL REFERENCES contractor_leads(id),
    bid_card_id UUID,
    campaign_id UUID,
    
    -- Message Information
    channel outreach_channel NOT NULL,
    message_template_id VARCHAR(100),
    message_subject TEXT,
    message_content TEXT NOT NULL,
    message_personalization JSONB, -- Variables used in template
    personalization_score INT DEFAULT 0, -- 0-100 how personalized
    
    -- Delivery Tracking
    sent_at TIMESTAMP DEFAULT NOW(),
    delivered_at TIMESTAMP,
    opened_at TIMESTAMP,
    first_opened_at TIMESTAMP,
    open_count INT DEFAULT 0,
    clicked_at TIMESTAMP,
    click_count INT DEFAULT 0,
    clicked_links JSONB, -- Array of clicked links with timestamps
    
    -- Response Tracking
    responded_at TIMESTAMP,
    response_channel outreach_channel, -- May differ from outreach channel
    response_content TEXT,
    response_sentiment response_sentiment,
    response_intent VARCHAR(50), -- 'interested', 'need_info', 'not_interested', etc
    
    -- Delivery Status
    status outreach_status DEFAULT 'queued',
    status_details JSONB, -- Provider-specific status info
    error_code VARCHAR(50),
    error_message TEXT,
    bounce_type VARCHAR(50), -- 'hard', 'soft', 'blocked'
    
    -- Provider Tracking IDs
    provider_message_id VARCHAR(255), -- SendGrid, Twilio, etc message ID
    provider_campaign_id VARCHAR(255),
    provider_webhook_data JSONB, -- Raw webhook data from provider
    
    -- Cost Tracking
    cost_cents INT DEFAULT 0, -- Cost in cents
    
    -- A/B Testing
    variant_id VARCHAR(50), -- For A/B testing different messages
    variant_group VARCHAR(20), -- 'control', 'variant_a', etc
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX idx_outreach_contractor ON contractor_outreach_attempts(contractor_lead_id);
CREATE INDEX idx_outreach_campaign ON contractor_outreach_attempts(campaign_id);
CREATE INDEX idx_outreach_status ON contractor_outreach_attempts(status, sent_at);
CREATE INDEX idx_outreach_channel ON contractor_outreach_attempts(channel, sent_at);
CREATE INDEX idx_outreach_response ON contractor_outreach_attempts(responded_at) WHERE responded_at IS NOT NULL;

-- Contractor engagement summary (aggregated view)
CREATE TABLE contractor_engagement_summary (
    contractor_lead_id UUID PRIMARY KEY REFERENCES contractor_leads(id),
    
    -- Contact History
    first_contacted_at TIMESTAMP,
    last_contacted_at TIMESTAMP,
    last_responded_at TIMESTAMP,
    days_since_last_contact INT GENERATED ALWAYS AS (
        CASE 
            WHEN last_contacted_at IS NULL THEN NULL
            ELSE EXTRACT(DAY FROM NOW() - last_contacted_at)::INT
        END
    ) STORED,
    
    -- Outreach Counts by Channel
    total_outreach_count INT DEFAULT 0,
    email_sent_count INT DEFAULT 0,
    email_delivered_count INT DEFAULT 0,
    email_opened_count INT DEFAULT 0,
    email_clicked_count INT DEFAULT 0,
    email_bounced_count INT DEFAULT 0,
    sms_sent_count INT DEFAULT 0,
    sms_delivered_count INT DEFAULT 0,
    sms_responded_count INT DEFAULT 0,
    phone_call_count INT DEFAULT 0,
    
    -- Response Metrics
    total_responses INT DEFAULT 0,
    positive_responses INT DEFAULT 0,
    negative_responses INT DEFAULT 0,
    neutral_responses INT DEFAULT 0,
    questions_asked INT DEFAULT 0,
    last_response_sentiment response_sentiment,
    
    -- Engagement Scoring
    engagement_score DECIMAL(5,2) DEFAULT 0.00, -- 0-100
    responsiveness_score DECIMAL(5,2) DEFAULT 0.00, -- 0-100
    interest_level VARCHAR(20), -- 'high', 'medium', 'low', 'none'
    average_response_time_hours DECIMAL(8,2),
    
    -- Best Practices Learned
    preferred_contact_channel outreach_channel,
    best_contact_time VARCHAR(50), -- 'morning', 'afternoon', 'evening'
    best_contact_day VARCHAR(20), -- 'weekday', 'weekend', specific day
    communication_language VARCHAR(10) DEFAULT 'en',
    
    -- Campaign Performance
    campaigns_included_in INT DEFAULT 0,
    campaigns_responded_to INT DEFAULT 0,
    last_campaign_id UUID,
    best_performing_template VARCHAR(100),
    
    -- Opt-out Preferences
    opt_out_email BOOLEAN DEFAULT FALSE,
    opt_out_sms BOOLEAN DEFAULT FALSE,
    opt_out_phone BOOLEAN DEFAULT FALSE,
    opt_out_all BOOLEAN DEFAULT FALSE,
    opt_out_date TIMESTAMP,
    opt_out_reason TEXT,
    
    -- Financial
    total_outreach_cost_cents INT DEFAULT 0,
    cost_per_response_cents INT GENERATED ALWAYS AS (
        CASE 
            WHEN total_responses = 0 THEN NULL
            ELSE total_outreach_cost_cents / total_responses
        END
    ) STORED,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_engagement_interest ON contractor_engagement_summary(interest_level);
CREATE INDEX idx_engagement_score ON contractor_engagement_summary(engagement_score DESC);
CREATE INDEX idx_engagement_last_contact ON contractor_engagement_summary(last_contacted_at);

-- Outreach campaigns
CREATE TABLE outreach_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bid_card_id UUID,
    campaign_name VARCHAR(255),
    campaign_type VARCHAR(50), -- 'initial', 'follow_up', 're_engagement'
    
    -- Target Criteria
    target_contractor_sizes contractor_size[],
    target_specialties TEXT[],
    target_locations JSONB, -- {states: [], cities: [], zips: []}
    target_min_rating DECIMAL(3,2),
    target_contractor_count INT,
    
    -- Campaign Settings
    channels outreach_channel[],
    message_templates JSONB, -- {email: template_id, sms: template_id}
    personalization_level VARCHAR(20), -- 'basic', 'medium', 'high'
    
    -- Scheduling
    scheduled_start TIMESTAMP,
    scheduled_end TIMESTAMP,
    send_time_preferences JSONB, -- {days: [], hours: []}
    
    -- Budget
    budget_cents INT,
    spent_cents INT DEFAULT 0,
    
    -- Results
    contractors_targeted INT DEFAULT 0,
    messages_sent INT DEFAULT 0,
    messages_delivered INT DEFAULT 0,
    responses_received INT DEFAULT 0,
    positive_responses INT DEFAULT 0,
    contractors_onboarded INT DEFAULT 0,
    
    -- Performance
    delivery_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE 
            WHEN messages_sent = 0 THEN 0
            ELSE (messages_delivered::DECIMAL / messages_sent * 100)
        END
    ) STORED,
    response_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE 
            WHEN messages_delivered = 0 THEN 0
            ELSE (responses_received::DECIMAL / messages_delivered * 100)
        END
    ) STORED,
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'scheduled', 'running', 'completed', 'paused'
    
    -- Metadata
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_campaigns_status ON outreach_campaigns(status, scheduled_start);
CREATE INDEX idx_campaigns_bid_card ON outreach_campaigns(bid_card_id);

-- Message templates
CREATE TABLE message_templates (
    id VARCHAR(100) PRIMARY KEY, -- e.g., 'kitchen_urgent_email_v1'
    template_name VARCHAR(255) NOT NULL,
    channel outreach_channel NOT NULL,
    
    -- Template Content
    subject_template TEXT, -- For email
    body_template TEXT NOT NULL, -- Supports variables like {{contractor_name}}
    
    -- Template Settings
    personalization_variables TEXT[], -- Available variables
    required_variables TEXT[], -- Must be provided
    
    -- Usage Tracking
    times_used INT DEFAULT 0,
    last_used_at TIMESTAMP,
    
    -- Performance Metrics
    total_sent INT DEFAULT 0,
    total_delivered INT DEFAULT 0,
    total_opened INT DEFAULT 0,
    total_responded INT DEFAULT 0,
    average_response_rate DECIMAL(5,2),
    average_sentiment_score DECIMAL(3,2), -- -1 to 1
    
    -- A/B Testing
    is_active BOOLEAN DEFAULT TRUE,
    variant_of VARCHAR(100), -- Parent template if this is a variant
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_templates_channel ON message_templates(channel, is_active);

-- Function to update engagement summary
CREATE OR REPLACE FUNCTION update_engagement_summary()
RETURNS TRIGGER AS $$
BEGIN
    -- Update or insert engagement summary
    INSERT INTO contractor_engagement_summary (
        contractor_lead_id,
        first_contacted_at,
        last_contacted_at,
        total_outreach_count
    ) VALUES (
        NEW.contractor_lead_id,
        NEW.sent_at,
        NEW.sent_at,
        1
    )
    ON CONFLICT (contractor_lead_id) DO UPDATE SET
        last_contacted_at = GREATEST(contractor_engagement_summary.last_contacted_at, NEW.sent_at),
        total_outreach_count = contractor_engagement_summary.total_outreach_count + 1,
        email_sent_count = CASE 
            WHEN NEW.channel = 'email' 
            THEN contractor_engagement_summary.email_sent_count + 1 
            ELSE contractor_engagement_summary.email_sent_count 
        END,
        sms_sent_count = CASE 
            WHEN NEW.channel = 'sms' 
            THEN contractor_engagement_summary.sms_sent_count + 1 
            ELSE contractor_engagement_summary.sms_sent_count 
        END,
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for new outreach attempts
CREATE TRIGGER update_engagement_on_outreach
    AFTER INSERT ON contractor_outreach_attempts
    FOR EACH ROW
    EXECUTE FUNCTION update_engagement_summary();

-- Function to calculate engagement score
CREATE OR REPLACE FUNCTION calculate_engagement_score(contractor_lead_id UUID)
RETURNS DECIMAL AS $$
DECLARE
    summary RECORD;
    score DECIMAL := 0.0;
BEGIN
    SELECT * INTO summary 
    FROM contractor_engagement_summary 
    WHERE contractor_engagement_summary.contractor_lead_id = calculate_engagement_score.contractor_lead_id;
    
    IF NOT FOUND THEN
        RETURN 0.0;
    END IF;
    
    -- Base score for any engagement
    IF summary.total_outreach_count > 0 THEN
        score := 10.0;
    END IF;
    
    -- Response rate (40 points max)
    IF summary.total_outreach_count > 0 THEN
        score := score + (summary.total_responses::DECIMAL / summary.total_outreach_count * 40);
    END IF;
    
    -- Positive sentiment (30 points max)
    IF summary.total_responses > 0 THEN
        score := score + (summary.positive_responses::DECIMAL / summary.total_responses * 30);
    END IF;
    
    -- Email engagement (15 points max)
    IF summary.email_sent_count > 0 THEN
        score := score + (summary.email_opened_count::DECIMAL / summary.email_sent_count * 10);
        score := score + (summary.email_clicked_count::DECIMAL / summary.email_sent_count * 5);
    END IF;
    
    -- Recency bonus (15 points max)
    IF summary.last_responded_at IS NOT NULL THEN
        IF summary.last_responded_at > NOW() - INTERVAL '7 days' THEN
            score := score + 15;
        ELSIF summary.last_responded_at > NOW() - INTERVAL '30 days' THEN
            score := score + 10;
        ELSIF summary.last_responded_at > NOW() - INTERVAL '90 days' THEN
            score := score + 5;
        END IF;
    END IF;
    
    -- Cap at 100
    score := LEAST(score, 100.0);
    
    -- Update the summary
    UPDATE contractor_engagement_summary 
    SET engagement_score = score,
        interest_level = CASE
            WHEN score >= 70 THEN 'high'
            WHEN score >= 40 THEN 'medium'
            WHEN score >= 20 THEN 'low'
            ELSE 'none'
        END,
        updated_at = NOW()
    WHERE contractor_engagement_summary.contractor_lead_id = calculate_engagement_score.contractor_lead_id;
    
    RETURN score;
END;
$$ LANGUAGE plpgsql;

-- Sample message templates (commented out for production)
/*
INSERT INTO message_templates (id, template_name, channel, subject_template, body_template, personalization_variables)
VALUES 
    ('kitchen_urgent_email_v1', 'Kitchen Remodel Urgent Email', 'email',
     'URGENT: {{project_type}} Project in {{location}} - ${{budget_min}}-${{budget_max}}',
     'Hi {{contractor_name}},\n\nWe have an urgent {{project_type}} project in {{location}} that needs immediate attention...',
     ARRAY['contractor_name', 'project_type', 'location', 'budget_min', 'budget_max']),
     
    ('kitchen_urgent_sms_v1', 'Kitchen Remodel Urgent SMS', 'sms',
     NULL,
     'URGENT: {{project_type}} in {{location}}. ${{budget_min}}-${{budget_max}}. Reply YES for details.',
     ARRAY['project_type', 'location', 'budget_min', 'budget_max']);
*/