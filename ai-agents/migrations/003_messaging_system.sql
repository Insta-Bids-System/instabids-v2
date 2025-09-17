-- Messaging System Database Schema
-- Phase 1: Core messaging infrastructure

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bid_card_id UUID NOT NULL REFERENCES bid_cards(id) ON DELETE CASCADE,
    homeowner_id UUID NOT NULL,
    contractor_id UUID NOT NULL,
    contractor_alias VARCHAR(50) NOT NULL, -- "Contractor A", "Contractor B", etc.
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'blocked')),
    last_message_at TIMESTAMP WITH TIME ZONE,
    homeowner_unread_count INTEGER DEFAULT 0,
    contractor_unread_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique conversation per contractor per bid card
    UNIQUE(bid_card_id, contractor_id)
);

-- Enhanced messages table with content filtering
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL CHECK (sender_type IN ('homeowner', 'contractor')),
    sender_id UUID NOT NULL,
    original_content TEXT NOT NULL,
    filtered_content TEXT NOT NULL, -- Content after filtering
    content_filtered BOOLEAN DEFAULT FALSE, -- Flag if content was modified
    filter_reasons JSONB DEFAULT '[]', -- Array of reasons why content was filtered
    message_type VARCHAR(50) DEFAULT 'text' CHECK (message_type IN ('text', 'system', 'bid_update', 'status_change')),
    metadata JSONB DEFAULT '{}', -- Additional message data
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Content filter rules table
CREATE TABLE IF NOT EXISTS content_filter_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_type VARCHAR(50) NOT NULL CHECK (rule_type IN ('regex', 'keyword', 'pattern')),
    pattern TEXT NOT NULL,
    replacement TEXT,
    severity VARCHAR(20) DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high')),
    category VARCHAR(50) NOT NULL, -- 'phone', 'email', 'address', 'name', 'social_media', etc.
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Broadcast messages for 1-to-many communication
CREATE TABLE IF NOT EXISTS broadcast_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bid_card_id UUID NOT NULL REFERENCES bid_cards(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL,
    sender_type VARCHAR(20) NOT NULL CHECK (sender_type IN ('homeowner', 'contractor')),
    original_content TEXT NOT NULL,
    filtered_content TEXT NOT NULL,
    recipient_type VARCHAR(20) NOT NULL CHECK (recipient_type IN ('all_contractors', 'bidding_contractors', 'selected_contractors')),
    recipient_ids UUID[] DEFAULT '{}', -- For selected_contractors type
    total_recipients INTEGER DEFAULT 0,
    read_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Track read receipts for broadcast messages
CREATE TABLE IF NOT EXISTS broadcast_read_receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    broadcast_message_id UUID NOT NULL REFERENCES broadcast_messages(id) ON DELETE CASCADE,
    recipient_id UUID NOT NULL,
    read_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure one receipt per recipient per broadcast
    UNIQUE(broadcast_message_id, recipient_id)
);

-- Message attachments (for future file sharing)
CREATE TABLE IF NOT EXISTS message_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    broadcast_message_id UUID REFERENCES broadcast_messages(id) ON DELETE CASCADE,
    file_type VARCHAR(50) NOT NULL, -- 'image', 'document', 'video'
    file_name TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    file_url TEXT NOT NULL,
    thumbnail_url TEXT,
    is_filtered BOOLEAN DEFAULT FALSE, -- If attachment contains sensitive info
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure attachment belongs to either message or broadcast, not both
    CHECK ((message_id IS NOT NULL AND broadcast_message_id IS NULL) OR 
           (message_id IS NULL AND broadcast_message_id IS NOT NULL))
);

-- Insert default content filter rules
INSERT INTO content_filter_rules (rule_type, pattern, replacement, severity, category, description) VALUES
-- Phone numbers
('regex', '\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE REMOVED]', 'high', 'phone', 'US phone number format'),
('regex', '\b\(\d{3}\)\s?\d{3}[-.\s]?\d{4}\b', '[PHONE REMOVED]', 'high', 'phone', 'US phone with parentheses'),
('regex', '\b\+?1?\s?\d{10,14}\b', '[PHONE REMOVED]', 'high', 'phone', 'International phone format'),

-- Email addresses
('regex', '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL REMOVED]', 'high', 'email', 'Email address'),

-- Social media
('regex', '@[A-Za-z0-9_]+', '[SOCIAL HANDLE REMOVED]', 'medium', 'social_media', 'Social media handles'),
('keyword', 'instagram.com/', '[SOCIAL LINK REMOVED]', 'medium', 'social_media', 'Instagram links'),
('keyword', 'facebook.com/', '[SOCIAL LINK REMOVED]', 'medium', 'social_media', 'Facebook links'),
('keyword', 'twitter.com/', '[SOCIAL LINK REMOVED]', 'medium', 'social_media', 'Twitter links'),

-- Address patterns
('regex', '\b\d+\s+[A-Za-z\s]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir|Plaza|Pl)\b', '[ADDRESS REMOVED]', 'medium', 'address', 'Street addresses'),

-- Contact phrases
('keyword', 'call me at', '[CONTACT REQUEST REMOVED]', 'high', 'contact_request', 'Direct contact requests'),
('keyword', 'text me at', '[CONTACT REQUEST REMOVED]', 'high', 'contact_request', 'Text contact requests'),
('keyword', 'email me at', '[CONTACT REQUEST REMOVED]', 'high', 'contact_request', 'Email contact requests'),
('keyword', 'reach me at', '[CONTACT REQUEST REMOVED]', 'high', 'contact_request', 'General contact requests'),
('keyword', 'contact me at', '[CONTACT REQUEST REMOVED]', 'high', 'contact_request', 'Contact requests'),
('keyword', 'whatsapp', '[CONTACT METHOD REMOVED]', 'medium', 'contact_request', 'WhatsApp mentions');

-- Create indexes for better query performance
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at DESC);
CREATE INDEX idx_conversations_bid_card ON conversations(bid_card_id);
CREATE INDEX idx_conversations_homeowner ON conversations(homeowner_id);
CREATE INDEX idx_conversations_contractor ON conversations(contractor_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX idx_broadcast_messages_bid_card ON broadcast_messages(bid_card_id);

-- Create function to update conversation last_message_at
CREATE OR REPLACE FUNCTION update_conversation_last_message() 
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations 
    SET last_message_at = NEW.created_at,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update last_message_at
CREATE TRIGGER update_conversation_on_message
AFTER INSERT ON messages
FOR EACH ROW
EXECUTE FUNCTION update_conversation_last_message();

-- Create function to increment unread counts
CREATE OR REPLACE FUNCTION increment_unread_count()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.sender_type = 'homeowner' THEN
        UPDATE conversations 
        SET contractor_unread_count = contractor_unread_count + 1
        WHERE id = NEW.conversation_id;
    ELSE
        UPDATE conversations 
        SET homeowner_unread_count = homeowner_unread_count + 1
        WHERE id = NEW.conversation_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for unread counts
CREATE TRIGGER increment_unread_on_message
AFTER INSERT ON messages
FOR EACH ROW
WHEN (NEW.is_read = FALSE)
EXECUTE FUNCTION increment_unread_count();

-- Add RLS policies (disabled by default as requested)
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE broadcast_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_filter_rules ENABLE ROW LEVEL SECURITY;

-- But create permissive policies for now
CREATE POLICY "Allow all operations on conversations" ON conversations FOR ALL USING (true);
CREATE POLICY "Allow all operations on messages" ON messages FOR ALL USING (true);
CREATE POLICY "Allow all operations on broadcast_messages" ON broadcast_messages FOR ALL USING (true);
CREATE POLICY "Allow all operations on content_filter_rules" ON content_filter_rules FOR ALL USING (true);