-- Enhanced Multi-Dimensional Contractor Memory System Tables
-- Creates 5 tables for comprehensive business intelligence gathering

-- 1. Bidding Patterns Table (Current Use)
CREATE TABLE IF NOT EXISTS contractor_bidding_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_id VARCHAR(255) NOT NULL,
    average_bid_amount DECIMAL(10,2),
    bid_range_min DECIMAL(10,2),
    bid_range_max DECIMAL(10,2),
    preferred_project_size VARCHAR(50), -- small, medium, large, enterprise
    pricing_strategy TEXT, -- competitive, premium, value, flexible
    markup_percentages JSONB, -- {"materials": 20, "labor": 35, "overhead": 15}
    sweet_spot_projects JSONB, -- ["kitchen_remodel", "bathroom", "additions"]
    success_rate DECIMAL(5,2),
    total_bids_submitted INTEGER DEFAULT 0,
    won_bids INTEGER DEFAULT 0,
    common_bid_adjustments JSONB, -- patterns in how they adjust bids
    competitive_positioning TEXT,
    seasonal_patterns JSONB,
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(contractor_id)
);

-- 2. Information Needs Table (Current Use)
CREATE TABLE IF NOT EXISTS contractor_information_needs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_id VARCHAR(255) NOT NULL,
    common_rfi_topics JSONB, -- ["materials_specs", "timeline_details", "access_requirements"]
    questions_asked_frequently JSONB, -- actual questions they ask
    information_gaps JSONB, -- what they need but don't ask for
    detail_level_preference VARCHAR(50), -- minimal, moderate, comprehensive
    visual_preference BOOLEAN DEFAULT false, -- prefers images/diagrams
    technical_depth VARCHAR(50), -- basic, intermediate, advanced
    common_concerns JSONB, -- ["permit_requirements", "hoa_restrictions", "neighbor_access"]
    clarification_patterns JSONB,
    project_scoping_approach TEXT,
    risk_assessment_focus JSONB,
    total_rfis_submitted INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(contractor_id)
);

-- 3. Relationship Memory Table (Business Intelligence)
CREATE TABLE IF NOT EXISTS contractor_relationship_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_id VARCHAR(255) NOT NULL,
    personality_traits JSONB, -- {"detail_oriented": true, "punctual": true}
    communication_style VARCHAR(100),
    work_style VARCHAR(100),
    customer_approach VARCHAR(100),
    trust_level INTEGER DEFAULT 50, -- 0-100 scale
    interaction_quality JSONB, -- history of interaction quality scores
    response_patterns JSONB,
    decision_making_style VARCHAR(100),
    stress_response VARCHAR(100),
    confidence_level VARCHAR(50),
    relationship_stage VARCHAR(50), -- new, developing, established, trusted
    key_motivators JSONB,
    pain_points JSONB,
    last_interaction TIMESTAMP,
    total_interactions INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(contractor_id)
);

-- 4. Business Profile Table (Business Intelligence)
CREATE TABLE IF NOT EXISTS contractor_business_profile (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_id VARCHAR(255) NOT NULL,
    crm_system VARCHAR(100), -- QuickBooks, Buildertrend, ServiceTitan, etc.
    company_size VARCHAR(50), -- solo, small, medium, large
    employee_count INTEGER,
    growth_trajectory VARCHAR(50), -- stable, growing, rapid_growth, scaling_back
    expansion_plans TEXT,
    target_market JSONB, -- {"residential": 70, "commercial": 30}
    service_area_radius INTEGER, -- miles
    technology_adoption VARCHAR(50), -- low, moderate, high, cutting_edge
    software_stack JSONB, -- ["QuickBooks", "Buildertrend", "CompanyCam"]
    business_challenges JSONB,
    competitive_advantages JSONB,
    certifications JSONB,
    insurance_coverage JSONB,
    annual_revenue_range VARCHAR(50),
    years_in_business INTEGER,
    business_model TEXT,
    referral_sources JSONB,
    marketing_channels JSONB,
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(contractor_id)
);

-- 5. Pain Points & Opportunities Table (Business Intelligence)
CREATE TABLE IF NOT EXISTS contractor_pain_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_id VARCHAR(255) NOT NULL,
    operational_challenges JSONB, -- ["subcontractor_management", "scheduling", "inventory"]
    technology_gaps JSONB, -- ["no_crm", "manual_estimating", "paper_invoices"]
    workflow_inefficiencies JSONB,
    customer_acquisition_challenges JSONB,
    financial_pain_points JSONB, -- ["cash_flow", "payment_delays", "estimating_accuracy"]
    compliance_concerns JSONB, -- ["permits", "licenses", "insurance"]
    resource_constraints JSONB,
    skill_gaps JSONB,
    automation_opportunities JSONB, -- where AI could help them
    immediate_needs JSONB,
    long_term_goals JSONB,
    solution_readiness VARCHAR(50), -- not_ready, exploring, ready, urgent
    budget_for_solutions VARCHAR(50),
    decision_timeline VARCHAR(50),
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(contractor_id)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_bidding_contractor_id ON contractor_bidding_patterns(contractor_id);
CREATE INDEX IF NOT EXISTS idx_info_needs_contractor_id ON contractor_information_needs(contractor_id);
CREATE INDEX IF NOT EXISTS idx_relationship_contractor_id ON contractor_relationship_memory(contractor_id);
CREATE INDEX IF NOT EXISTS idx_business_contractor_id ON contractor_business_profile(contractor_id);
CREATE INDEX IF NOT EXISTS idx_pain_points_contractor_id ON contractor_pain_points(contractor_id);

-- Create updated_at triggers for all tables
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_bidding_patterns_updated_at BEFORE UPDATE ON contractor_bidding_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_info_needs_updated_at BEFORE UPDATE ON contractor_information_needs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_relationship_updated_at BEFORE UPDATE ON contractor_relationship_memory
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_business_profile_updated_at BEFORE UPDATE ON contractor_business_profile
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pain_points_updated_at BEFORE UPDATE ON contractor_pain_points
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();