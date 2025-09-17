-- Create a contractor account with proper password encryption
-- Using Supabase's built-in functions

-- First create the user with extensions
DO $$
DECLARE
    new_user_id uuid;
BEGIN
    -- Generate a new UUID
    new_user_id := gen_random_uuid();
    
    -- Insert the user with properly encrypted password
    -- Password: Contractor2025!
    INSERT INTO auth.users (
        id,
        instance_id,
        email,
        encrypted_password,
        email_confirmed_at,
        created_at,
        updated_at,
        raw_app_meta_data,
        raw_user_meta_data,
        aud,
        role
    ) VALUES (
        new_user_id,
        '00000000-0000-0000-0000-000000000000',
        'contractor@instabids.com',
        crypt('Contractor2025!', gen_salt('bf')),
        NOW(),
        NOW(),
        NOW(),
        '{"provider": "email", "providers": ["email"]}',
        '{}',
        'authenticated',
        'authenticated'
    );
    
    -- Create the profile
    INSERT INTO profiles (
        id,
        email,
        role,
        full_name,
        created_at
    ) VALUES (
        new_user_id,
        'contractor@instabids.com',
        'contractor',
        'JM Holiday Lighting Demo',
        NOW()
    );
    
    RAISE NOTICE 'User created with ID: %', new_user_id;
END $$;