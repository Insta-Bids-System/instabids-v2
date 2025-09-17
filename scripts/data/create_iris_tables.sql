-- Create table for Iris conversation storage
CREATE TABLE IF NOT EXISTS inspiration_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    homeowner_id UUID REFERENCES homeowners(id),
    board_id UUID REFERENCES inspiration_boards(id),
    user_message TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    conversation_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_inspiration_conversations_board_id ON inspiration_conversations(board_id);
CREATE INDEX IF NOT EXISTS idx_inspiration_conversations_homeowner_id ON inspiration_conversations(homeowner_id);
CREATE INDEX IF NOT EXISTS idx_inspiration_conversations_created_at ON inspiration_conversations(created_at);

-- Enable RLS
ALTER TABLE inspiration_conversations ENABLE ROW LEVEL SECURITY;

-- Create policy for inspiration_conversations
CREATE POLICY "Users can access their own conversations" ON inspiration_conversations
    FOR ALL USING (homeowner_id = auth.uid() OR homeowner_id = '550e8400-e29b-41d4-a716-446655440001');

-- Insert demo homeowner if not exists
INSERT INTO homeowners (id, email, full_name, phone, created_at)
VALUES (
    '550e8400-e29b-41d4-a716-446655440001',
    'demo.homeowner@instabids.com', 
    'Demo Homeowner',
    '+1-555-DEMO',
    NOW()
) ON CONFLICT (id) DO NOTHING;