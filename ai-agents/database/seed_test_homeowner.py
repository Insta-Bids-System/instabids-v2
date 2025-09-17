"""
Seed test homeowner user for development
"""
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client


# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL", "")
# Try service key first, fallback to anon key
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "") or os.environ.get("SUPABASE_SERVICE_KEY", "") or os.environ.get("SUPABASE_ANON_KEY", "")

if not url or not key:
    print("❌ Missing Supabase credentials in environment variables")
    print("   Please ensure SUPABASE_URL and SUPABASE_ANON_KEY are set in .env")
    sys.exit(1)

supabase: Client = create_client(url, key)

def create_test_homeowner():
    """Create a test homeowner user"""

    # Test user data
    test_email = "test.homeowner@instabids.com"
    test_password = "TestHome123!"

    try:
        # Check if user already exists
        existing_user = supabase.auth.admin.list_users()
        for user in existing_user.users:
            if user.email == test_email:
                print(f"✓ Test homeowner already exists: {test_email}")
                print(f"  User ID: {user.id}")
                print(f"  Login with: {test_email} / {test_password}")
                return user.id

        # Create new user
        auth_response = supabase.auth.admin.create_user({
            "email": test_email,
            "password": test_password,
            "email_confirm": True,
            "user_metadata": {
                "role": "homeowner"
            }
        })

        if auth_response.user:
            user_id = auth_response.user.id

            # Create profile
            profile_data = {
                "id": user_id,
                "email": test_email,
                "full_name": "Test Homeowner",
                "role": "homeowner",
                "phone": "+1234567890",
                "address": {
                    "street": "123 Test Street",
                    "city": "Test City",
                    "state": "CA",
                    "zip": "90210"
                },
                "created_at": datetime.utcnow().isoformat()
            }

            profile_response = supabase.table("profiles").upsert(profile_data).execute()

            if profile_response.data:
                print("✓ Test homeowner created successfully!")
                print(f"  Email: {test_email}")
                print(f"  Password: {test_password}")
                print(f"  User ID: {user_id}")
                print("  Role: homeowner")
                print("\n📝 Login Instructions:")
                print("  1. Go to http://localhost:3000")
                print("  2. Click 'Sign In'")
                print(f"  3. Use email: {test_email}")
                print(f"  4. Use password: {test_password}")

                # Create a sample project for the test user
                sample_project = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "title": "Kitchen Renovation",
                    "description": "Complete kitchen remodel including cabinets, countertops, and appliances",
                    "status": "draft",
                    "category": "Kitchen",
                    "timeline": "flexible",
                    "budget_range": {
                        "min": 15000,
                        "max": 25000
                    },
                    "created_at": datetime.utcnow().isoformat()
                }

                project_response = supabase.table("projects").insert(sample_project).execute()

                if project_response.data:
                    print(f"\n✓ Sample project created: {sample_project['title']}")

                return user_id
            else:
                print("❌ Failed to create profile")
                return None

        else:
            print("❌ Failed to create auth user")
            return None

    except Exception as e:
        print(f"❌ Error creating test homeowner: {e!s}")
        return None

def create_additional_test_users():
    """Create additional test users for different scenarios"""

    additional_users = [
        {
            "email": "sarah.johnson@example.com",
            "password": "TestUser123!",
            "full_name": "Sarah Johnson",
            "phone": "+1415555001"
        },
        {
            "email": "mike.chen@example.com",
            "password": "TestUser123!",
            "full_name": "Mike Chen",
            "phone": "+1415555002"
        }
    ]

    for user_data in additional_users:
        try:
            # Check if user exists
            existing_user = supabase.auth.admin.list_users()
            user_exists = any(u.email == user_data["email"] for u in existing_user.users)

            if not user_exists:
                # Create user
                auth_response = supabase.auth.admin.create_user({
                    "email": user_data["email"],
                    "password": user_data["password"],
                    "email_confirm": True,
                    "user_metadata": {
                        "role": "homeowner"
                    }
                })

                if auth_response.user:
                    user_id = auth_response.user.id

                    # Create profile
                    profile_data = {
                        "id": user_id,
                        "email": user_data["email"],
                        "full_name": user_data["full_name"],
                        "role": "homeowner",
                        "phone": user_data["phone"],
                        "created_at": datetime.utcnow().isoformat()
                    }

                    supabase.table("profiles").upsert(profile_data).execute()
                    print(f"✓ Created user: {user_data['full_name']} ({user_data['email']})")

        except Exception as e:
            print(f"❌ Error creating {user_data['email']}: {e!s}")

if __name__ == "__main__":
    print("🏠 Creating test homeowner users...")
    print("-" * 50)

    # Create main test user
    test_user_id = create_test_homeowner()

    # Create additional test users
    print("\n📋 Creating additional test users...")
    create_additional_test_users()

    print("\n✅ Test user setup complete!")
    print("\n🚀 You can now:")
    print("  1. Login at http://localhost:3000")
    print("  2. Access the dashboard")
    print("  3. Switch to 'My Inspiration' tab")
    print("  4. Create inspiration boards")
    print("  5. Upload images to test the feature")
