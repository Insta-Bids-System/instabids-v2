"""
Script to create a test user in Supabase for development
Run this once to set up the test user
"""

import os
import sys
from datetime import datetime
from uuid import uuid4

from dotenv import load_dotenv


# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client


# Load environment variables
load_dotenv("../.env")

def create_test_user():
    """Create a test user directly in the database"""
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        return

    client = create_client(supabase_url, supabase_key)

    # Generate a test user ID
    test_user_id = str(uuid4())

    try:
        # Check if test user already exists
        existing = client.table("profiles").select("*").eq("email", "test@instabids.com").execute()

        if existing.data:
            print(f"Test user already exists with ID: {existing.data[0]['id']}")
            return existing.data[0]["id"]

        # Create test user profile
        profile_data = {
            "id": test_user_id,
            "email": "test@instabids.com",
            "full_name": "Test User",
            "role": "homeowner",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        result = client.table("profiles").insert(profile_data).execute()

        if result.data:
            print(f"Successfully created test user with ID: {test_user_id}")
            print("Email: test@instabids.com")
            print("Role: homeowner")
            return test_user_id
        else:
            print("Failed to create test user")

    except Exception as e:
        print(f"Error creating test user: {e}")

        # Try simplified approach
        try:
            # Generate a simpler test user
            simple_user_id = "test-user-" + datetime.now().strftime("%Y%m%d%H%M%S")

            profile_data = {
                "id": simple_user_id,
                "email": f"test-{datetime.now().timestamp()}@instabids.com",
                "full_name": "Test User",
                "role": "homeowner"
            }

            result = client.table("profiles").insert(profile_data).execute()

            if result.data:
                print(f"Created alternative test user with ID: {simple_user_id}")
                return simple_user_id

        except Exception as e2:
            print(f"Alternative approach also failed: {e2}")

if __name__ == "__main__":
    create_test_user()
