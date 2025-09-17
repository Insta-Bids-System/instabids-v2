-- Enhanced Bid Cards Schema Migration
-- Adds support for multiple UI variants, messaging, and group bidding

-- Add new columns to existing bid_cards table
ALTER TABLE bid_cards
ADD COLUMN IF NOT EXISTS title VARCHAR(255),
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS budget_min DECIMAL(10, 2),
ADD COLUMN IF NOT EXISTS budget_max DECIMAL(10, 2),
ADD COLUMN IF NOT EXISTS timeline_start DATE,
ADD COLUMN IF NOT EXISTS timeline_end DATE,
ADD COLUMN IF NOT EXISTS timeline_flexibility VARCHAR(20) DEFAULT 'flexible',
ADD COLUMN IF NOT EXISTS location_address TEXT,
ADD COLUMN IF NOT EXISTS location_city VARCHAR(100),
ADD COLUMN IF NOT EXISTS location_state VARCHAR(50),
ADD COLUMN IF NOT EXISTS location_zip VARCHAR(20),
ADD COLUMN IF NOT EXISTS location_lat DECIMAL(10, 8),
ADD COLUMN IF NOT EXISTS location_lng DECIMAL(11, 8),
ADD COLUMN IF NOT EXISTS project_type VARCHAR(100),
ADD COLUMN IF NOT EXISTS categories TEXT[], -- Array of categories
ADD COLUMN IF NOT EXISTS requirements TEXT[], -- Array of requirements
ADD COLUMN IF NOT EXISTS preferred_schedule TEXT[], -- Array of schedule preferences
ADD COLUMN IF NOT EXISTS visibility VARCHAR(20) DEFAULT 'public',
ADD COLUMN IF NOT EXISTS group_bid_eligible BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS group_bid_id UUID REFERENCES group_bids(id),
ADD COLUMN IF NOT EXISTS bid_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS interested_contractors INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS bid_deadline TIMESTAMP,
ADD COLUMN IF NOT EXISTS auto_close_after_bids INTEGER,
ADD COLUMN IF NOT EXISTS allows_questions BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS requires_bid_before_message BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS published_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';

-- Create bid_card_images table
CREATE TABLE IF NOT EXISTS bid_card_images (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bid_card_id UUID NOT NULL REFERENCES bid_cards(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  thumbnail_url TEXT,
  caption TEXT,
  is_primary BOOLEAN DEFAULT false,
  upload_date TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create bid_card_documents table
CREATE TABLE IF NOT EXISTS bid_card_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bid_card_id UUID NOT NULL REFERENCES bid_cards(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  url TEXT NOT NULL,
  type VARCHAR(50),
  size INTEGER,
  upload_date TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create contractor_bids table
CREATE TABLE IF NOT EXISTS contractor_bids (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bid_card_id UUID NOT NULL REFERENCES bid_cards(id) ON DELETE CASCADE,
  contractor_id UUID NOT NULL,
  amount DECIMAL(10, 2) NOT NULL,
  timeline_start DATE NOT NULL,
  timeline_end DATE NOT NULL,
  proposal TEXT NOT NULL,
  approach TEXT,
  materials_included BOOLEAN DEFAULT false,
  warranty_details TEXT,
  status VARCHAR(20) DEFAULT 'draft',
  allows_messages BOOLEAN DEFAULT true,
  last_message_at TIMESTAMP,
  submitted_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  -- Ensure one bid per contractor per bid card
  UNIQUE(bid_card_id, contractor_id)
);

-- Create bid_milestones table
CREATE TABLE IF NOT EXISTS bid_milestones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bid_id UUID NOT NULL REFERENCES contractor_bids(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  amount DECIMAL(10, 2) NOT NULL,
  estimated_completion DATE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create bid_card_messages table
CREATE TABLE IF NOT EXISTS bid_card_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bid_card_id UUID NOT NULL REFERENCES bid_cards(id) ON DELETE CASCADE,
  bid_id UUID REFERENCES contractor_bids(id) ON DELETE CASCADE,
  sender_id UUID NOT NULL,
  sender_type VARCHAR(20) NOT NULL CHECK (sender_type IN ('homeowner', 'contractor')),
  recipient_id UUID NOT NULL,
  recipient_type VARCHAR(20) NOT NULL CHECK (recipient_type IN ('homeowner', 'contractor')),
  content TEXT NOT NULL,
  is_read BOOLEAN DEFAULT false,
  read_at TIMESTAMP,
  thread_id UUID,
  reply_to_id UUID REFERENCES bid_card_messages(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create message_attachments table
CREATE TABLE IF NOT EXISTS message_attachments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id UUID NOT NULL REFERENCES bid_card_messages(id) ON DELETE CASCADE,
  type VARCHAR(20) NOT NULL CHECK (type IN ('image', 'document', 'bid_update')),
  url TEXT NOT NULL,
  name VARCHAR(255) NOT NULL,
  size INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create group_bids table
CREATE TABLE IF NOT EXISTS group_bids (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  location_city VARCHAR(100) NOT NULL,
  location_state VARCHAR(50) NOT NULL,
  location_zip_codes TEXT[] NOT NULL,
  radius_miles INTEGER DEFAULT 25,
  total_budget_min DECIMAL(10, 2),
  total_budget_max DECIMAL(10, 2),
  estimated_savings_percentage DECIMAL(5, 2) DEFAULT 15.0,
  bulk_discount_available BOOLEAN DEFAULT true,
  coordinator_id UUID,
  status VARCHAR(20) DEFAULT 'forming',
  min_participants INTEGER DEFAULT 5,
  current_participants INTEGER DEFAULT 0,
  join_deadline TIMESTAMP NOT NULL,
  bid_deadline TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_bid_cards_status ON bid_cards(status);
CREATE INDEX idx_bid_cards_location ON bid_cards(location_city, location_state, location_zip);
CREATE INDEX idx_bid_cards_project_type ON bid_cards(project_type);
CREATE INDEX idx_bid_cards_group_bid ON bid_cards(group_bid_eligible, group_bid_id);
CREATE INDEX idx_contractor_bids_contractor ON contractor_bids(contractor_id);
CREATE INDEX idx_contractor_bids_status ON contractor_bids(bid_card_id, status);
CREATE INDEX idx_messages_participants ON bid_card_messages(sender_id, recipient_id);
CREATE INDEX idx_messages_unread ON bid_card_messages(recipient_id, is_read);
CREATE INDEX idx_group_bids_location ON group_bids(location_city, location_state);

-- Add triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_bid_cards_updated_at BEFORE UPDATE ON bid_cards
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contractor_bids_updated_at BEFORE UPDATE ON contractor_bids
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bid_card_messages_updated_at BEFORE UPDATE ON bid_card_messages
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_group_bids_updated_at BEFORE UPDATE ON group_bids
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();