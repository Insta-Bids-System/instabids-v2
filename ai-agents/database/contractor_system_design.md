# Complete Contractor System Database Design

## Overview
This document outlines the complete contractor data management system for Instabids, including discovery, tracking, and onboarding.

## Contractor Size Classification

### Size Categories:
1. **solo_handyman** - Individual with truck/tools
2. **owner_operator** - Small local business, owner does work  
3. **small_business** - Has crews/teams (2-10 employees)
4. **regional_company** - Multi-location (10-50 employees)
5. **national_chain** - Large franchises (50+ employees)

## Database Tables

### 1. Contractor Leads (Discovery Phase)
```sql
CREATE TABLE contractor_leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Discovery Info
    source VARCHAR(50) NOT NULL, -- 'google_maps', 'yelp', 'bbb', 'angi', 'facebook'
    source_url TEXT,
    source_id VARCHAR(255), -- External ID from source
    discovery_run_id UUID,
    discovered_at TIMESTAMP DEFAULT NOW(),
    
    -- Basic Info
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(255),
    website TEXT,
    
    -- Location
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    service_radius_miles INT,
    service_zip_codes TEXT[],
    
    -- Business Classification
    contractor_size VARCHAR(20), -- 'solo_handyman', 'owner_operator', etc
    estimated_employees VARCHAR(20), -- '1', '2-5', '6-10', '11-25', '26-50', '50+'
    years_in_business INT,
    
    -- Capabilities
    specialties TEXT[], -- ['kitchen', 'bathroom', 'plumbing', 'electrical']
    certifications TEXT[],
    license_number VARCHAR(100),
    license_verified BOOLEAN DEFAULT FALSE,
    insurance_verified BOOLEAN DEFAULT FALSE,
    bonded BOOLEAN DEFAULT FALSE,
    
    -- Ratings/Reviews
    rating DECIMAL(3,2), -- 0.00 to 5.00
    review_count INT,
    recent_reviews JSONB, -- Last 5 reviews with dates
    
    -- Raw Data
    raw_data JSONB, -- Complete scraped data
    enrichment_data JSONB, -- Additional data from enrichment
    
    -- Status
    lead_status VARCHAR(50) DEFAULT 'new', -- 'new', 'enriched', 'qualified', 'disqualified'
    lead_score INT, -- 0-100 quality score
    disqualification_reason TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_contractor_leads_location ON contractor_leads(state, city, zip_code);
CREATE INDEX idx_contractor_leads_size ON contractor_leads(contractor_size);
CREATE INDEX idx_contractor_leads_specialties ON contractor_leads USING GIN(specialties);
```

### 2. Discovery Runs (Search Tracking)
```sql
CREATE TABLE discovery_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bid_card_id UUID,
    search_parameters JSONB, -- All search criteria
    
    -- Search Criteria
    location VARCHAR(255),
    radius_miles INT,
    project_type VARCHAR(100),
    contractor_sizes TEXT[], -- Array of acceptable sizes
    minimum_rating DECIMAL(3,2),
    license_required BOOLEAN,
    
    -- Results
    total_found INT DEFAULT 0,
    qualified_count INT DEFAULT 0,
    disqualified_count INT DEFAULT 0,
    
    -- Timing
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_seconds INT,
    
    -- Status
    status VARCHAR(50) DEFAULT 'running', -- 'running', 'completed', 'failed'
    error_message TEXT
);
```

### 3. Contractor Outreach History
```sql
CREATE TABLE contractor_outreach_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_lead_id UUID REFERENCES contractor_leads(id),
    bid_card_id UUID,
    campaign_id UUID,
    
    -- Message Details
    channel VARCHAR(20) NOT NULL, -- 'email', 'sms', 'phone', 'mail'
    message_template_id VARCHAR(100),
    message_content TEXT,
    personalization_score INT, -- 0-100
    
    -- Delivery
    sent_at TIMESTAMP DEFAULT NOW(),
    delivered_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    
    -- Response
    responded_at TIMESTAMP,
    response_content TEXT,
    response_channel VARCHAR(20),
    response_sentiment VARCHAR(20), -- 'positive', 'negative', 'neutral', 'question'
    
    -- Status
    status VARCHAR(50), -- 'queued', 'sent', 'delivered', 'bounced', 'responded'
    error_details TEXT,
    
    -- Tracking
    email_message_id VARCHAR(255), -- SendGrid ID
    sms_message_id VARCHAR(255), -- Twilio SID
    tracking_opens BOOLEAN DEFAULT TRUE,
    tracking_clicks BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_outreach_contractor ON contractor_outreach_attempts(contractor_lead_id);
CREATE INDEX idx_outreach_campaign ON contractor_outreach_attempts(campaign_id);
```

### 4. Contractor Engagement Summary
```sql
CREATE TABLE contractor_engagement_summary (
    contractor_lead_id UUID PRIMARY KEY REFERENCES contractor_leads(id),
    
    -- Contact History
    first_contacted_at TIMESTAMP,
    last_contacted_at TIMESTAMP,
    last_responded_at TIMESTAMP,
    
    -- Outreach Counts
    total_outreach_count INT DEFAULT 0,
    email_sent_count INT DEFAULT 0,
    email_opened_count INT DEFAULT 0,
    email_clicked_count INT DEFAULT 0,
    sms_sent_count INT DEFAULT 0,
    sms_responded_count INT DEFAULT 0,
    phone_call_count INT DEFAULT 0,
    
    -- Response Analysis
    total_responses INT DEFAULT 0,
    positive_responses INT DEFAULT 0,
    negative_responses INT DEFAULT 0,
    questions_asked INT DEFAULT 0,
    
    -- Engagement Scoring
    engagement_score DECIMAL(5,2), -- 0-100
    responsiveness_score DECIMAL(5,2), -- 0-100
    interest_level VARCHAR(20), -- 'high', 'medium', 'low', 'none'
    
    -- Preferences
    preferred_contact_method VARCHAR(20),
    best_contact_time VARCHAR(50),
    communication_language VARCHAR(10) DEFAULT 'en',
    
    -- Opt-out Status
    opt_out_email BOOLEAN DEFAULT FALSE,
    opt_out_sms BOOLEAN DEFAULT FALSE,
    opt_out_all BOOLEAN DEFAULT FALSE,
    opt_out_date TIMESTAMP,
    opt_out_reason TEXT,
    
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 5. Onboarded Contractors (Active in System)
```sql
CREATE TABLE contractors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Business Identity
    company_name VARCHAR(255) NOT NULL,
    legal_business_name VARCHAR(255),
    business_type VARCHAR(50), -- 'sole_prop', 'llc', 'corp', 's_corp'
    tax_id_type VARCHAR(20), -- 'ein', 'ssn'
    tax_id_hash VARCHAR(255), -- Encrypted
    
    -- Size Classification
    contractor_size VARCHAR(20) NOT NULL, -- Our 5 categories
    employee_count INT,
    crew_count INT,
    office_staff_count INT,
    
    -- Licensing & Insurance
    license_number VARCHAR(100),
    license_state VARCHAR(2),
    license_expiry DATE,
    license_verified BOOLEAN DEFAULT FALSE,
    license_verified_at TIMESTAMP,
    insurance_carrier VARCHAR(255),
    insurance_policy_number VARCHAR(100),
    insurance_expiry DATE,
    insurance_coverage_amount DECIMAL(12,2),
    insurance_verified BOOLEAN DEFAULT FALSE,
    bonded BOOLEAN DEFAULT FALSE,
    bond_amount DECIMAL(12,2),
    
    -- Contact Information
    primary_contact_name VARCHAR(255) NOT NULL,
    primary_contact_role VARCHAR(100), -- 'owner', 'manager', 'sales'
    primary_email VARCHAR(255) UNIQUE NOT NULL,
    primary_phone VARCHAR(20) NOT NULL,
    secondary_contacts JSONB, -- Array of {name, role, email, phone}
    
    -- Location & Service Area
    headquarters_address TEXT,
    headquarters_city VARCHAR(100),
    headquarters_state VARCHAR(2),
    headquarters_zip VARCHAR(10),
    service_states TEXT[], -- ['FL', 'GA']
    service_cities TEXT[],
    service_zip_codes TEXT[],
    max_travel_distance_miles INT,
    
    -- Capabilities & Specializations
    primary_specialty VARCHAR(100), -- Main focus
    specialties TEXT[], -- All capabilities
    certifications JSONB, -- [{name, issuer, expiry, number}]
    years_in_business INT,
    year_established INT,
    
    -- Capacity & Availability
    max_concurrent_projects INT,
    average_project_duration_days INT,
    minimum_project_size DECIMAL(10,2),
    maximum_project_size DECIMAL(10,2),
    emergency_available BOOLEAN DEFAULT FALSE,
    weekend_available BOOLEAN DEFAULT FALSE,
    
    -- Performance Metrics
    total_projects_completed INT DEFAULT 0,
    total_revenue DECIMAL(12,2) DEFAULT 0,
    average_project_value DECIMAL(10,2),
    average_rating DECIMAL(3,2) DEFAULT 0,
    total_ratings INT DEFAULT 0,
    on_time_completion_rate DECIMAL(5,2), -- Percentage
    customer_satisfaction_score DECIMAL(5,2), -- 0-100
    response_time_minutes INT, -- Average response time
    
    -- Financial Information
    payment_terms TEXT[], -- ['net30', 'deposit_required']
    accepts_credit_cards BOOLEAN DEFAULT TRUE,
    requires_deposit BOOLEAN DEFAULT TRUE,
    typical_deposit_percentage INT DEFAULT 30,
    financing_available BOOLEAN DEFAULT FALSE,
    
    -- Platform Integration
    stripe_account_id VARCHAR(255),
    stripe_onboarding_complete BOOLEAN DEFAULT FALSE,
    quickbooks_integration BOOLEAN DEFAULT FALSE,
    
    -- Account Status
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'active', 'suspended', 'inactive'
    onboarding_status VARCHAR(50) DEFAULT 'started',
    onboarding_completed_at TIMESTAMP,
    suspension_reason TEXT,
    suspension_date TIMESTAMP,
    
    -- Subscription & Billing
    subscription_plan VARCHAR(50) DEFAULT 'basic', -- 'basic', 'pro', 'enterprise'
    subscription_status VARCHAR(20) DEFAULT 'trial', -- 'trial', 'active', 'past_due'
    trial_ends_at TIMESTAMP,
    next_billing_date DATE,
    monthly_lead_limit INT,
    commission_rate DECIMAL(5,2), -- Platform fee percentage
    
    -- Profile Completeness
    profile_completeness INT DEFAULT 0, -- 0-100
    missing_profile_fields TEXT[],
    has_profile_photo BOOLEAN DEFAULT FALSE,
    has_company_logo BOOLEAN DEFAULT FALSE,
    has_insurance_docs BOOLEAN DEFAULT FALSE,
    has_license_docs BOOLEAN DEFAULT FALSE,
    portfolio_project_count INT DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_active_at TIMESTAMP,
    last_project_at TIMESTAMP
);

CREATE INDEX idx_contractors_size ON contractors(contractor_size);
CREATE INDEX idx_contractors_location ON contractors(headquarters_state, headquarters_city);
CREATE INDEX idx_contractors_specialties ON contractors USING GIN(specialties);
CREATE INDEX idx_contractors_status ON contractors(status, onboarding_status);
```

### 6. Contractor Journey Tracking
```sql
CREATE TABLE contractor_lifecycle_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_lead_id UUID,
    contractor_id UUID,
    
    -- Event Details
    event_type VARCHAR(50) NOT NULL, -- 'discovered', 'contacted', 'responded', etc
    event_subtype VARCHAR(50), -- More specific categorization
    event_data JSONB, -- Event-specific data
    
    -- Status Transition
    previous_status VARCHAR(50),
    new_status VARCHAR(50),
    
    -- Attribution
    triggered_by VARCHAR(50), -- 'system', 'user', 'contractor', 'admin'
    triggered_by_id UUID, -- User/admin ID if applicable
    related_bid_card_id UUID,
    related_campaign_id UUID,
    
    -- Timestamps
    occurred_at TIMESTAMP DEFAULT NOW(),
    
    -- Notes
    notes TEXT,
    internal_notes TEXT -- Not shown to contractor
);

CREATE INDEX idx_lifecycle_contractor ON contractor_lifecycle_events(contractor_lead_id, contractor_id);
CREATE INDEX idx_lifecycle_event ON contractor_lifecycle_events(event_type, occurred_at);
```

### 7. Lead Enrichment Queue
```sql
CREATE TABLE lead_enrichment_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_lead_id UUID REFERENCES contractor_leads(id),
    
    -- Enrichment Tasks
    enrichment_type VARCHAR(50), -- 'license_verify', 'insurance_check', 'reviews_fetch'
    priority INT DEFAULT 5, -- 1-10, 1 is highest
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    attempts INT DEFAULT 0,
    max_attempts INT DEFAULT 3,
    
    -- Results
    enrichment_data JSONB,
    error_message TEXT,
    
    -- Timing
    queued_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    next_retry_at TIMESTAMP
);
```

## Discovery Sources & Methods

### 1. Google Places API
- Search for businesses by category and location
- Get ratings, reviews, contact info
- Identify contractor size by review patterns

### 2. Web Scraping Targets
- **Yelp**: Reviews, ratings, project photos
- **Angi (Angie's List)**: Verified contractors, specialties
- **BBB**: Accreditation, complaints, years in business
- **HomeAdvisor**: Service areas, project types
- **Thumbtack**: Active contractors, response times
- **Facebook**: Local business pages, recommendations

### 3. Data Enrichment Sources
- State license databases
- Insurance verification services
- Business entity lookups
- Social media presence
- Website technology analysis

## Contractor Lifecycle States

```
DISCOVERED → ENRICHED → QUALIFIED → CONTACTED → ENGAGED → INTERESTED → ONBOARDING → ACTIVE

Side paths:
- DISQUALIFIED (failed requirements)
- OPT_OUT (requested removal)
- INACTIVE (no response/engagement)
- SUSPENDED (violations)
```

## Implementation Priority

1. **Phase 1: Core Tables**
   - contractor_leads
   - contractor_outreach_attempts
   - contractors (onboarded)

2. **Phase 2: Tracking & Analytics**
   - contractor_engagement_summary
   - contractor_lifecycle_events
   - discovery_runs

3. **Phase 3: Advanced Features**
   - lead_enrichment_queue
   - Automated enrichment pipelines
   - Scoring algorithms