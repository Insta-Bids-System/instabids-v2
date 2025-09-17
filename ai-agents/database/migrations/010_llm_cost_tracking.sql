-- LLM Cost Tracking System
-- Captures all LLM API calls across OpenAI and Anthropic
-- Tracks tokens, costs, and performance metrics

-- Main tracking table
CREATE TABLE IF NOT EXISTS llm_usage_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Agent identification
    agent_name VARCHAR(50) NOT NULL,  -- CIA, JAA, IRIS, CDA, etc.
    
    -- Provider and model details
    provider VARCHAR(20) NOT NULL,    -- openai, anthropic
    model VARCHAR(100) NOT NULL,      -- gpt-5, claude-opus-4, etc.
    
    -- Token usage
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER GENERATED ALWAYS AS (prompt_tokens + completion_tokens) STORED,
    
    -- Cost tracking
    cost_usd DECIMAL(10,6) NOT NULL DEFAULT 0,
    
    -- Performance metrics
    duration_ms INTEGER,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    
    -- Business context for cost attribution
    user_id UUID,                     -- Which user triggered this
    session_id VARCHAR(100),          -- Conversation session ID
    bid_card_id UUID,                 -- Associated bid card if applicable
    conversation_turn INTEGER,        -- Turn number in conversation
    
    -- Error tracking
    error_occurred BOOLEAN DEFAULT FALSE,
    error_details TEXT,
    
    -- Flexible context storage
    context JSONB,
    
    -- Constraints
    CONSTRAINT valid_tokens CHECK (prompt_tokens >= 0 AND completion_tokens >= 0),
    CONSTRAINT valid_cost CHECK (cost_usd >= 0),
    CONSTRAINT valid_provider CHECK (provider IN ('openai', 'anthropic'))
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_llm_usage_agent_time 
    ON llm_usage_log(agent_name, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_llm_usage_provider_model 
    ON llm_usage_log(provider, model, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_llm_usage_daily_cost 
    ON llm_usage_log(DATE(timestamp), cost_usd DESC);

CREATE INDEX IF NOT EXISTS idx_llm_usage_user_session 
    ON llm_usage_log(user_id, session_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_llm_usage_bid_card 
    ON llm_usage_log(bid_card_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_llm_usage_errors 
    ON llm_usage_log(error_occurred, timestamp DESC) 
    WHERE error_occurred = TRUE;

-- Daily summary table for fast dashboard queries
CREATE TABLE IF NOT EXISTS llm_cost_daily_summary (
    date DATE PRIMARY KEY,
    total_cost_usd DECIMAL(10,2) NOT NULL DEFAULT 0,
    total_tokens BIGINT NOT NULL DEFAULT 0,
    total_calls INTEGER NOT NULL DEFAULT 0,
    
    -- Breakdown by agent
    agent_breakdown JSONB DEFAULT '{}',
    
    -- Breakdown by model
    model_breakdown JSONB DEFAULT '{}',
    
    -- Breakdown by provider
    provider_breakdown JSONB DEFAULT '{}',
    
    -- Performance metrics
    avg_duration_ms DECIMAL(10,2),
    error_count INTEGER DEFAULT 0,
    error_rate DECIMAL(5,4) DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- View for today's usage
CREATE OR REPLACE VIEW llm_usage_today AS
SELECT 
    agent_name,
    provider,
    model,
    COUNT(*) as total_calls,
    SUM(cost_usd) as daily_cost,
    SUM(total_tokens) as total_tokens,
    AVG(duration_ms) as avg_duration_ms,
    COUNT(*) FILTER (WHERE error_occurred) as error_count,
    MAX(timestamp) as last_call
FROM llm_usage_log 
WHERE DATE(timestamp) = CURRENT_DATE
GROUP BY agent_name, provider, model
ORDER BY daily_cost DESC;

-- View for hourly usage (last 24 hours)
CREATE OR REPLACE VIEW llm_usage_hourly AS
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    agent_name,
    SUM(cost_usd) as hourly_cost,
    COUNT(*) as hourly_calls,
    SUM(total_tokens) as hourly_tokens
FROM llm_usage_log 
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', timestamp), agent_name
ORDER BY hour DESC, hourly_cost DESC;

-- View for expensive sessions
CREATE OR REPLACE VIEW llm_expensive_sessions AS
SELECT 
    session_id,
    user_id,
    COUNT(DISTINCT agent_name) as agents_used,
    SUM(cost_usd) as session_cost,
    COUNT(*) as total_calls,
    SUM(total_tokens) as total_tokens,
    MIN(timestamp) as session_start,
    MAX(timestamp) as session_end,
    EXTRACT(EPOCH FROM (MAX(timestamp) - MIN(timestamp)))/60 as duration_minutes
FROM llm_usage_log
WHERE session_id IS NOT NULL
GROUP BY session_id, user_id
HAVING SUM(cost_usd) > 1.00  -- Sessions over $1
ORDER BY session_cost DESC;

-- Function to update daily summary (run via cron or trigger)
CREATE OR REPLACE FUNCTION update_llm_daily_summary()
RETURNS void AS $$
BEGIN
    INSERT INTO llm_cost_daily_summary (
        date,
        total_cost_usd,
        total_tokens,
        total_calls,
        agent_breakdown,
        model_breakdown,
        provider_breakdown,
        avg_duration_ms,
        error_count,
        error_rate
    )
    SELECT 
        CURRENT_DATE,
        COALESCE(SUM(cost_usd), 0),
        COALESCE(SUM(total_tokens), 0),
        COUNT(*),
        jsonb_object_agg(
            DISTINCT agent_name, 
            agent_totals.cost
        ) FILTER (WHERE agent_name IS NOT NULL),
        jsonb_object_agg(
            DISTINCT model,
            model_totals.cost  
        ) FILTER (WHERE model IS NOT NULL),
        jsonb_object_agg(
            DISTINCT provider,
            provider_totals.cost
        ) FILTER (WHERE provider IS NOT NULL),
        AVG(duration_ms),
        COUNT(*) FILTER (WHERE error_occurred),
        CASE 
            WHEN COUNT(*) > 0 THEN 
                COUNT(*) FILTER (WHERE error_occurred)::decimal / COUNT(*)
            ELSE 0
        END
    FROM llm_usage_log
    LEFT JOIN LATERAL (
        SELECT agent_name, SUM(cost_usd) as cost
        FROM llm_usage_log l2
        WHERE DATE(l2.timestamp) = CURRENT_DATE
        GROUP BY agent_name
    ) agent_totals ON true
    LEFT JOIN LATERAL (
        SELECT model, SUM(cost_usd) as cost
        FROM llm_usage_log l3
        WHERE DATE(l3.timestamp) = CURRENT_DATE
        GROUP BY model
    ) model_totals ON true
    LEFT JOIN LATERAL (
        SELECT provider, SUM(cost_usd) as cost
        FROM llm_usage_log l4
        WHERE DATE(l4.timestamp) = CURRENT_DATE
        GROUP BY provider
    ) provider_totals ON true
    WHERE DATE(timestamp) = CURRENT_DATE
    ON CONFLICT (date) DO UPDATE SET
        total_cost_usd = EXCLUDED.total_cost_usd,
        total_tokens = EXCLUDED.total_tokens,
        total_calls = EXCLUDED.total_calls,
        agent_breakdown = EXCLUDED.agent_breakdown,
        model_breakdown = EXCLUDED.model_breakdown,
        provider_breakdown = EXCLUDED.provider_breakdown,
        avg_duration_ms = EXCLUDED.avg_duration_ms,
        error_count = EXCLUDED.error_count,
        error_rate = EXCLUDED.error_rate,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;