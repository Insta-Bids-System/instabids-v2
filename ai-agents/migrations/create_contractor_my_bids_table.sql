-- Create contractor_my_bids table for tracking contractor bid interactions
-- This table powers the "My Bids" section in the contractor portal

CREATE TABLE IF NOT EXISTS contractor_my_bids (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contractor_id TEXT NOT NULL,
    bid_card_id UUID NOT NULL REFERENCES bid_cards(id) ON DELETE CASCADE,
    
    -- Interaction tracking
    first_interaction TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_interaction TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    interaction_count INTEGER DEFAULT 1,
    last_interaction_type TEXT, -- 'viewed', 'message_sent', 'quote_submitted', 'question_asked'
    
    -- Status tracking
    status TEXT DEFAULT 'viewed', -- 'viewed', 'engaged', 'quoted', 'selected', 'completed'
    
    -- Cached bid card info for fast display
    bid_card_title TEXT,
    project_type TEXT,
    location_zip TEXT,
    
    -- Interaction history (JSONB array)
    interaction_history JSONB DEFAULT '[]'::jsonb,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint to prevent duplicates
    UNIQUE(contractor_id, bid_card_id)
);

-- Create indexes for performance
CREATE INDEX idx_contractor_my_bids_contractor ON contractor_my_bids(contractor_id);
CREATE INDEX idx_contractor_my_bids_bid_card ON contractor_my_bids(bid_card_id);
CREATE INDEX idx_contractor_my_bids_status ON contractor_my_bids(status);
CREATE INDEX idx_contractor_my_bids_last_interaction ON contractor_my_bids(last_interaction DESC);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_contractor_my_bids_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER contractor_my_bids_updated_at
    BEFORE UPDATE ON contractor_my_bids
    FOR EACH ROW
    EXECUTE FUNCTION update_contractor_my_bids_updated_at();

-- Add RLS policies
ALTER TABLE contractor_my_bids ENABLE ROW LEVEL SECURITY;

-- Contractors can see their own My Bids
CREATE POLICY "Contractors can view own my bids" ON contractor_my_bids
    FOR SELECT USING (auth.uid()::text = contractor_id);

-- Contractors can update their own My Bids  
CREATE POLICY "Contractors can update own my bids" ON contractor_my_bids
    FOR UPDATE USING (auth.uid()::text = contractor_id);

-- System can insert/update any My Bids (for backend operations)
CREATE POLICY "System can manage all my bids" ON contractor_my_bids
    FOR ALL USING (true);