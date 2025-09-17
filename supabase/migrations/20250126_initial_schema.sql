-- Instabids Database Schema
-- This migration creates all necessary tables for the Instabids marketplace

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create custom types
CREATE TYPE user_role AS ENUM ('homeowner', 'contractor', 'admin');
CREATE TYPE project_status AS ENUM ('draft', 'active', 'in_progress', 'completed', 'cancelled');
CREATE TYPE bid_status AS ENUM ('pending', 'accepted', 'rejected', 'withdrawn');
CREATE TYPE payment_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'refunded');

-- Users table (extends Supabase auth.users)
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    phone TEXT,
    role user_role NOT NULL DEFAULT 'homeowner',
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Contractors table (additional info for contractor profiles)
CREATE TABLE public.contractors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    business_name TEXT NOT NULL,
    license_number TEXT,
    insurance_info JSONB,
    service_areas TEXT[],
    specialties TEXT[],
    years_experience INTEGER,
    rating DECIMAL(3,2) DEFAULT 0.00,
    total_reviews INTEGER DEFAULT 0,
    verified BOOLEAN DEFAULT FALSE,
    stripe_account_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(profile_id)
);

-- Projects table (homeowner projects)
CREATE TABLE public.projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    homeowner_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    urgency TEXT CHECK (urgency IN ('emergency', 'urgent', 'flexible')),
    budget_range JSONB, -- {min: number, max: number}
    location JSONB, -- {address: string, city: string, state: string, zip: string, coordinates: {lat, lng}}
    images TEXT[],
    status project_status NOT NULL DEFAULT 'draft',
    ai_analysis JSONB, -- Store JAA agent analysis
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Bids table
CREATE TABLE public.bids (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    contractor_id UUID NOT NULL REFERENCES public.contractors(id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL,
    description TEXT NOT NULL,
    timeline TEXT,
    status bid_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, contractor_id)
);

-- Messages table (secure messaging between parties)
CREATE TABLE public.messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL,
    sender_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    recipient_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    encrypted BOOLEAN DEFAULT TRUE,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Conversations table
CREATE TABLE public.conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    homeowner_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    contractor_id UUID NOT NULL REFERENCES public.contractors(id) ON DELETE CASCADE,
    last_message_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, contractor_id)
);

-- Payments table
CREATE TABLE public.payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    bid_id UUID NOT NULL REFERENCES public.bids(id) ON DELETE CASCADE,
    payer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    recipient_contractor_id UUID NOT NULL REFERENCES public.contractors(id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL,
    stripe_payment_intent_id TEXT UNIQUE,
    status payment_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- AI Agent Conversations (store LangGraph conversation state)
CREATE TABLE public.ai_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    agent_type TEXT NOT NULL CHECK (agent_type IN ('CIA', 'CoIA', 'JAA', 'CDA', 'EAA', 'SMA', 'CHO', 'CRA')),
    thread_id TEXT NOT NULL, -- LangGraph thread ID
    state JSONB NOT NULL, -- Serialized conversation state
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Contractor discovery cache (for CDA agent efficiency)
CREATE TABLE public.contractor_discovery_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_hash TEXT NOT NULL,
    results JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    UNIQUE(query_hash)
);

-- Reviews table
CREATE TABLE public.reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    contractor_id UUID NOT NULL REFERENCES public.contractors(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, reviewer_id)
);

-- Create indexes for performance
CREATE INDEX idx_profiles_role ON public.profiles(role);
CREATE INDEX idx_contractors_verified ON public.contractors(verified);
CREATE INDEX idx_contractors_service_areas ON public.contractors USING GIN(service_areas);
CREATE INDEX idx_contractors_specialties ON public.contractors USING GIN(specialties);
CREATE INDEX idx_projects_homeowner_id ON public.projects(homeowner_id);
CREATE INDEX idx_projects_status ON public.projects(status);
CREATE INDEX idx_bids_project_id ON public.bids(project_id);
CREATE INDEX idx_bids_contractor_id ON public.bids(contractor_id);
CREATE INDEX idx_bids_status ON public.bids(status);
CREATE INDEX idx_messages_conversation_id ON public.messages(conversation_id);
CREATE INDEX idx_messages_created_at ON public.messages(created_at);
CREATE INDEX idx_ai_conversations_user_id ON public.ai_conversations(user_id);
CREATE INDEX idx_ai_conversations_thread_id ON public.ai_conversations(thread_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contractors_updated_at BEFORE UPDATE ON public.contractors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON public.projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bids_updated_at BEFORE UPDATE ON public.bids
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_conversations_updated_at BEFORE UPDATE ON public.ai_conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();