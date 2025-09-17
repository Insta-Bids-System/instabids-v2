#!/usr/bin/env python3
"""
Direct database check for conversation state
"""
import asyncio
from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

async def check_conversation_in_database():
    """Check if conversations are being saved to database"""
    
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("ERROR: Missing Supabase credentials")
        return
    
    print(f"Supabase URL from env: {supabase_url}")
    print(f"Has service key: {'Yes' if supabase_key else 'No'}")
    
    if supabase_url != "https://xrhgrthdcaymxuqcgrmj.supabase.co":
        print(f"WARNING: URL mismatch! Expected xrhgrthdcaymxuqcgrmj but got {supabase_url}")
        supabase_url = "https://xrhgrthdcaymxuqcgrmj.supabase.co"
        print(f"Using correct URL: {supabase_url}")
        
    supabase = create_client(supabase_url, supabase_key)
    
    # Check agent_conversations table
    print("\n1. Checking agent_conversations table...")
    try:
        # Get recent conversations
        response = supabase.table("agent_conversations").select("*").order("created_at", desc=True).limit(5).execute()
        
        if response.data:
            print(f"   Found {len(response.data)} recent conversations:")
            for conv in response.data:
                print(f"   - Thread: {conv.get('thread_id', 'N/A')}")
                print(f"     User: {conv.get('user_id', 'N/A')}")
                print(f"     Agent: {conv.get('agent_type', 'N/A')}")
                print(f"     Created: {conv.get('created_at', 'N/A')}")
                
                # Check if conversation_data has actual messages
                conv_data = conv.get('conversation_data', {})
                if isinstance(conv_data, dict):
                    state = conv_data.get('state', {})
                    messages = state.get('messages', []) if isinstance(state, dict) else []
                    print(f"     Messages: {len(messages)}")
                print()
        else:
            print("   No conversations found in database")
            
    except Exception as e:
        print(f"   ERROR checking agent_conversations: {e}")
    
    # Check if our test session exists
    print("\n2. Checking for our test sessions...")
    try:
        response = supabase.table("agent_conversations").select("*").ilike("thread_id", "real_test_session_%").execute()
        
        if response.data:
            print(f"   Found {len(response.data)} test sessions:")
            for conv in response.data:
                print(f"   - {conv.get('thread_id')}: {conv.get('created_at')}")
        else:
            print("   No test sessions found - conversations not being saved!")
            
    except Exception as e:
        print(f"   ERROR checking test sessions: {e}")
    
    # Check users table for test users
    print("\n3. Checking for test users...")
    try:
        response = supabase.table("homeowners").select("*").eq("email", "test@example.com").execute()
        
        if response.data:
            print(f"   Found {len(response.data)} test users")
            for user in response.data:
                print(f"   - ID: {user.get('id')}")
                print(f"     Email: {user.get('email')}")
        else:
            print("   No test users found")
            
    except Exception as e:
        print(f"   ERROR checking users: {e}")
        
    # Direct check for any agent_conversations with 'cia' type
    print("\n4. Checking for ANY CIA conversations...")
    try:
        response = supabase.table("agent_conversations").select("*").eq("agent_type", "cia").limit(3).execute()
        
        if response.data:
            print(f"   Found {len(response.data)} CIA conversations")
        else:
            print("   NO CIA CONVERSATIONS IN DATABASE AT ALL!")
            print("   This confirms conversations are not being saved.")
            
    except Exception as e:
        print(f"   ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(check_conversation_in_database())