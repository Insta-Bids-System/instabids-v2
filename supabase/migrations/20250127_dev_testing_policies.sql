-- DEVELOPMENT ONLY: Allow anonymous access for testing
-- This should be removed or modified for production

-- Allow anonymous users to create profiles for testing
CREATE POLICY "Allow anonymous profile creation (DEV ONLY)" ON public.profiles
    FOR INSERT WITH CHECK (email LIKE 'test%@instabids.com');

-- Allow anonymous users to manage AI conversations for testing
CREATE POLICY "Allow anonymous AI conversations (DEV ONLY)" ON public.ai_conversations
    FOR ALL USING (
        user_id IN (
            SELECT id FROM public.profiles WHERE email LIKE 'test%@instabids.com'
        )
    );

-- Note: These policies are for development only and should be removed in production