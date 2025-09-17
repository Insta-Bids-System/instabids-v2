#!/usr/bin/env python3
"""
Reset password for JM Holiday Lighting contractor account
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai-agents', '.env')
load_dotenv(env_path, override=True)

def reset_password():
    """Reset password for info@jmholidaylighting.com"""
    
    # Initialize Supabase with service role key
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("[ERROR] Missing Supabase credentials")
        return None
        
    supabase = create_client(supabase_url, supabase_key)
    
    user_id = "c24d60b5-5469-4207-a364-f20363422d8a"
    email = "info@jmholidaylighting.com"
    new_password = "Instabids2025!"  # New simple password
    
    print(f"[RESET] Resetting password for: {email}")
    
    try:
        # Update user password using admin API
        result = supabase.auth.admin.update_user_by_id(
            user_id,
            {
                'password': new_password
            }
        )
        
        if result:
            print(f"[SUCCESS] Password reset successfully!")
            print(f"\nNEW LOGIN CREDENTIALS:")
            print(f"   Email: {email}")
            print(f"   Password: {new_password}")
            print(f"   Login URL: http://localhost:5177/login")
            return True
        else:
            print(f"[ERROR] Failed to reset password")
            return False
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

if __name__ == "__main__":
    reset_password()