-- Row Level Security Policies for Instabids
-- This migration sets up RLS policies to ensure data isolation and security

-- Enable RLS on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contractors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bids ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contractor_discovery_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view their own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Public profiles are viewable by authenticated users" ON public.profiles
    FOR SELECT USING (auth.role() = 'authenticated');

-- Contractors policies
CREATE POLICY "Contractors can view their own contractor profile" ON public.contractors
    FOR SELECT USING (
        profile_id = auth.uid() OR
        verified = true -- Verified contractors are public
    );

CREATE POLICY "Contractors can update their own contractor profile" ON public.contractors
    FOR UPDATE USING (profile_id = auth.uid());

CREATE POLICY "Contractors can insert their own contractor profile" ON public.contractors
    FOR INSERT WITH CHECK (profile_id = auth.uid());

-- Projects policies
CREATE POLICY "Homeowners can view their own projects" ON public.projects
    FOR SELECT USING (homeowner_id = auth.uid());

CREATE POLICY "Active projects are viewable by verified contractors" ON public.projects
    FOR SELECT USING (
        status = 'active' AND 
        EXISTS (
            SELECT 1 FROM public.contractors c
            JOIN public.profiles p ON c.profile_id = p.id
            WHERE p.id = auth.uid() AND c.verified = true
        )
    );

CREATE POLICY "Homeowners can create projects" ON public.projects
    FOR INSERT WITH CHECK (
        homeowner_id = auth.uid() AND
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND role = 'homeowner'
        )
    );

CREATE POLICY "Homeowners can update their own projects" ON public.projects
    FOR UPDATE USING (homeowner_id = auth.uid());

-- Bids policies
CREATE POLICY "Contractors can view their own bids" ON public.bids
    FOR SELECT USING (
        contractor_id IN (
            SELECT id FROM public.contractors WHERE profile_id = auth.uid()
        )
    );

CREATE POLICY "Homeowners can view bids on their projects" ON public.bids
    FOR SELECT USING (
        project_id IN (
            SELECT id FROM public.projects WHERE homeowner_id = auth.uid()
        )
    );

CREATE POLICY "Verified contractors can create bids" ON public.bids
    FOR INSERT WITH CHECK (
        contractor_id IN (
            SELECT id FROM public.contractors 
            WHERE profile_id = auth.uid() AND verified = true
        )
    );

CREATE POLICY "Contractors can update their own pending bids" ON public.bids
    FOR UPDATE USING (
        contractor_id IN (
            SELECT id FROM public.contractors WHERE profile_id = auth.uid()
        ) AND status = 'pending'
    );

-- Messages policies
CREATE POLICY "Users can view messages they sent or received" ON public.messages
    FOR SELECT USING (
        sender_id = auth.uid() OR recipient_id = auth.uid()
    );

CREATE POLICY "Users can send messages in their conversations" ON public.messages
    FOR INSERT WITH CHECK (
        sender_id = auth.uid() AND
        EXISTS (
            SELECT 1 FROM public.conversations
            WHERE id = conversation_id AND 
            (homeowner_id = auth.uid() OR 
             contractor_id IN (
                SELECT id FROM public.contractors WHERE profile_id = auth.uid()
             ))
        )
    );

-- Conversations policies
CREATE POLICY "Users can view their own conversations" ON public.conversations
    FOR SELECT USING (
        homeowner_id = auth.uid() OR
        contractor_id IN (
            SELECT id FROM public.contractors WHERE profile_id = auth.uid()
        )
    );

-- Payments policies
CREATE POLICY "Users can view their own payments" ON public.payments
    FOR SELECT USING (
        payer_id = auth.uid() OR
        recipient_contractor_id IN (
            SELECT id FROM public.contractors WHERE profile_id = auth.uid()
        )
    );

CREATE POLICY "Homeowners can create payments for accepted bids" ON public.payments
    FOR INSERT WITH CHECK (
        payer_id = auth.uid() AND
        EXISTS (
            SELECT 1 FROM public.bids b
            JOIN public.projects p ON b.project_id = p.id
            WHERE b.id = bid_id AND 
                  p.homeowner_id = auth.uid() AND 
                  b.status = 'accepted'
        )
    );

-- AI Conversations policies
CREATE POLICY "Users can view their own AI conversations" ON public.ai_conversations
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can create their own AI conversations" ON public.ai_conversations
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own AI conversations" ON public.ai_conversations
    FOR UPDATE USING (user_id = auth.uid());

-- Contractor discovery cache policies (public read for efficiency)
CREATE POLICY "Anyone can read contractor discovery cache" ON public.contractor_discovery_cache
    FOR SELECT USING (expires_at > NOW());

CREATE POLICY "System can manage contractor discovery cache" ON public.contractor_discovery_cache
    FOR ALL USING (auth.role() = 'service_role');

-- Reviews policies
CREATE POLICY "Anyone can view reviews" ON public.reviews
    FOR SELECT USING (true);

CREATE POLICY "Homeowners can create reviews for completed projects" ON public.reviews
    FOR INSERT WITH CHECK (
        reviewer_id = auth.uid() AND
        EXISTS (
            SELECT 1 FROM public.projects p
            JOIN public.payments pay ON p.id = pay.project_id
            WHERE p.id = project_id AND 
                  p.homeowner_id = auth.uid() AND 
                  p.status = 'completed' AND
                  pay.status = 'completed'
        )
    );

-- Create helper functions for common RLS checks
CREATE OR REPLACE FUNCTION is_verified_contractor(user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.contractors c
        JOIN public.profiles p ON c.profile_id = p.id
        WHERE p.id = user_id AND c.verified = true
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION owns_project(user_id UUID, project_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.projects
        WHERE id = project_id AND homeowner_id = user_id
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;