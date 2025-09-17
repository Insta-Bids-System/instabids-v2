-- Migration: Add public URLs and view tracking for bid cards
-- Date: 2025-01-29

-- Add public URL to bid_cards table
ALTER TABLE bid_cards ADD COLUMN IF NOT EXISTS
  public_url VARCHAR(255) GENERATED ALWAYS AS 
  ('https://instabids.com/bid-cards/' || id::text) STORED;

-- Add short URL slug for prettier URLs (optional)
ALTER TABLE bid_cards ADD COLUMN IF NOT EXISTS
  url_slug VARCHAR(50) UNIQUE;

-- Create bid card views tracking table
CREATE TABLE IF NOT EXISTS bid_card_views (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  bid_card_id UUID REFERENCES bid_cards(id) ON DELETE CASCADE,
  contractor_lead_id UUID REFERENCES contractor_leads(id),
  ip_address INET,
  user_agent TEXT,
  referrer TEXT,
  session_id VARCHAR(100),
  view_duration_seconds INTEGER,
  clicked_cta BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for analytics queries
CREATE INDEX IF NOT EXISTS idx_bid_card_views_bid_card_id ON bid_card_views(bid_card_id);
CREATE INDEX IF NOT EXISTS idx_bid_card_views_created_at ON bid_card_views(created_at);
CREATE INDEX IF NOT EXISTS idx_bid_card_views_contractor ON bid_card_views(contractor_lead_id);

-- Create bid card engagement events table for detailed analytics
CREATE TABLE IF NOT EXISTS bid_card_engagement_events (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  bid_card_view_id UUID REFERENCES bid_card_views(id) ON DELETE CASCADE,
  event_type VARCHAR(50) NOT NULL, -- 'photo_view', 'contact_click', 'share', 'save'
  event_data JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add photo gallery support to bid_cards
ALTER TABLE bid_cards ADD COLUMN IF NOT EXISTS
  photo_urls TEXT[] DEFAULT '{}';

ALTER TABLE bid_cards ADD COLUMN IF NOT EXISTS
  hero_image_url TEXT;

ALTER TABLE bid_cards ADD COLUMN IF NOT EXISTS
  cover_photo_url TEXT;

-- Add view count cache for performance
ALTER TABLE bid_cards ADD COLUMN IF NOT EXISTS
  view_count INTEGER DEFAULT 0;

ALTER TABLE bid_cards ADD COLUMN IF NOT EXISTS
  unique_view_count INTEGER DEFAULT 0;

-- Create a view for bid card analytics
CREATE OR REPLACE VIEW bid_card_analytics AS
SELECT 
  bc.id,
  bc.project_type,
  bc.timeline,
  bc.created_at,
  COUNT(DISTINCT bcv.id) as total_views,
  COUNT(DISTINCT bcv.contractor_lead_id) as unique_contractor_views,
  COUNT(DISTINCT CASE WHEN bcv.clicked_cta THEN bcv.contractor_lead_id END) as contractors_interested,
  AVG(bcv.view_duration_seconds) as avg_view_duration,
  MAX(bcv.created_at) as last_viewed_at
FROM bid_cards bc
LEFT JOIN bid_card_views bcv ON bc.id = bcv.bid_card_id
GROUP BY bc.id, bc.project_type, bc.timeline, bc.created_at;

-- Add RLS policies for public access
ALTER TABLE bid_card_views ENABLE ROW LEVEL SECURITY;
ALTER TABLE bid_card_engagement_events ENABLE ROW LEVEL SECURITY;

-- Allow public to view bid cards (no auth required)
CREATE POLICY "Bid cards are publicly viewable" ON bid_cards
  FOR SELECT USING (true);

-- Allow public to track views
CREATE POLICY "Anyone can track bid card views" ON bid_card_views
  FOR INSERT WITH CHECK (true);

-- Allow view owners to see their own engagement
CREATE POLICY "Users can see their own engagement events" ON bid_card_engagement_events
  FOR ALL USING (
    bid_card_view_id IN (
      SELECT id FROM bid_card_views WHERE session_id = current_setting('app.session_id', true)
    )
  );