#!/usr/bin/env python3
"""
Test CIA Agent Unified Image Attachment System
Simple test without emoji characters
"""
import asyncio
import base64
import sys
import os

# Add the ai-agents directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

from agents.cia.agent import CustomerInterfaceAgent
from supabase import create_client

async def test_cia_unified_images():
    """Test CIA agent with images using unified attachment system"""
    print("Testing CIA Unified Image System")
    print("=" * 40)
    
    # Initialize CIA agent with API key from environment
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: No OPENAI_API_KEY found in environment")
        return False
        
    cia = CustomerInterfaceAgent(f"openai:{api_key}")
    print("CIA agent initialized")
    
    # Create test image (simple 1x1 PNG)
    test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    test_image = f"data:image/png;base64,{test_image_b64}"
    
    user_id = "test-unified-user"
    session_id = f"test-session-{int(asyncio.get_event_loop().time())}"
    message = "Here is a test image for the unified system"
    images = [test_image]
    
    print(f"User: {user_id}")
    print(f"Session: {session_id}")
    print(f"Images: {len(images)}")
    
    try:
        print("\nTesting CIA conversation with image...")
        result = await cia.handle_conversation(
            user_id=user_id,
            message=message,
            session_id=session_id,
            images=images
        )
        
        print("SUCCESS: CIA conversation completed")
        print(f"Response: {result.get('response', '')[:100]}...")
        
        # Verify unified system
        print("\nVerifying unified system...")
        supabase = create_client(
            "https://xrhgrthdcaymxuqcgrmj.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhyaGdydGhkY2F5bXh1cWNncm1qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM2NTcyMDYsImV4cCI6MjA2OTIzMzIwNn0.BriGLA2FE_e_NJl8B-3ps1W6ZAuK6a5HpTwBGy-6rmE"
        )
        
        # Check unified_conversations
        conversations = supabase.table("unified_conversations").select("*").eq("metadata->>session_id", session_id).execute()
        print(f"Conversations found: {len(conversations.data)}")
        
        if conversations.data:
            conversation_id = conversations.data[0]["id"]
            print(f"Conversation ID: {conversation_id}")
            
            # Check unified_messages
            messages = supabase.table("unified_messages").select("*").eq("conversation_id", conversation_id).execute()
            print(f"Messages found: {len(messages.data)}")
            
            # Check unified_message_attachments
            print(f"Checking attachments for {len(messages.data)} messages")
            for i, msg in enumerate(messages.data):
                print(f"Message {i+1}: {msg['sender_type']} - ID: {msg['id']}")
                if msg['sender_type'] == 'user':
                    attachments = supabase.table("unified_message_attachments").select("*").eq("message_id", msg["id"]).execute()
                    print(f"Attachments for user message {msg['id']}: {len(attachments.data)}")
                    
                    if attachments.data:
                        att = attachments.data[0]
                        print(f"Attachment ID: {att.get('id', 'N/A')}")
                        print(f"Storage path: {att.get('storage_path', 'N/A')}")
                        print(f"File size: {att.get('file_size', 0)} bytes")
                        print("SUCCESS: Unified image system working!")
                        return True
                        
            # If no attachments found, check all attachments in table
            all_attachments = supabase.table("unified_message_attachments").select("*").execute()
            print(f"Total attachments in system: {len(all_attachments.data)}")
            if all_attachments.data:
                for att in all_attachments.data:
                    print(f"  - ID: {att['id']}, Message: {att['message_id']}, Size: {att.get('file_size', 0)}")
            
            print("FAILED: No attachments found for user messages")
            return False
        
        print("FAILED: No conversation found")
        return False
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_cia_unified_images())
    if success:
        print("\nALL TESTS PASSED!")
    else:
        print("\nTESTS FAILED!")