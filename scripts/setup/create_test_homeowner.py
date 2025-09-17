"""
Create a test homeowner user in Supabase
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
anon_key = os.getenv("SUPABASE_ANON_KEY") 
supabase: Client = create_client(url, anon_key)

def create_test_homeowner():
    """Create a test homeowner account"""
    try:
        # Sign up the user
        print("Creating test homeowner user...")
        auth_response = supabase.auth.sign_up({
            "email": "test.homeowner@instabids.com",
            "password": "TestHome123!",
            "options": {
                "data": {
                    "full_name": "Test Homeowner",
                    "role": "homeowner"
                }
            }
        })
        
        if auth_response.user:
            print(f"✓ User created successfully: {auth_response.user.email}")
            print(f"  User ID: {auth_response.user.id}")
            
            # Create profile entry
            profile_data = {
                "id": auth_response.user.id,
                "email": "test.homeowner@instabids.com",
                "full_name": "Test Homeowner",
                "role": "homeowner"
            }
            
            profile_response = supabase.table('profiles').insert(profile_data).execute()
            
            if profile_response.data:
                print("✓ Profile created successfully")
            else:
                print("! Profile creation failed")
                
            print("\nTest Homeowner Credentials:")
            print("Email: test.homeowner@instabids.com")
            print("Password: TestHome123!")
            print("\nNote: User may need to verify email before logging in")
            
            return True
        else:
            print("✗ Failed to create user")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        # If user already exists, just print the credentials
        if "User already registered" in str(e):
            print("\nTest homeowner already exists!")
            print("\nTest Homeowner Credentials:")
            print("Email: test.homeowner@instabids.com")
            print("Password: TestHome123!")
            return True
        return False

if __name__ == "__main__":
    create_test_homeowner()