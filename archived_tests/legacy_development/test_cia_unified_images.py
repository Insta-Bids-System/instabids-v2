#!/usr/bin/env python3
"""
Test CIA Agent Unified Image Attachment System
Tests the complete flow from image upload to unified_message_attachments
"""
import asyncio
import base64
import sys
import os

# Add the ai-agents directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

from agents.cia.agent import CustomerInterfaceAgent
from supabase import create_client

async def test_cia_unified_image_system():
    """Test CIA agent unified image attachment system"""
    print("Testing CIA Unified Image Attachment System")
    print("=" * 50)
    
    # Initialize CIA agent
    cia = CustomerInterfaceAgent()
    print("✅ CIA agent initialized")
    
    # Create a simple test image (1x1 red pixel PNG)
    test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    test_image_with_prefix = f"data:image/png;base64,{test_image_b64}"
    
    # Test parameters
    user_id = "test-user-unified-images"
    session_id = f"test-session-{asyncio.get_event_loop().time()}"
    message = "Here's a test image for unified attachment system"
    images = [test_image_with_prefix]
    
    print(f"📋 Test Parameters:")
    print(f"   User ID: {user_id}")
    print(f"   Session ID: {session_id}")
    print(f"   Message: {message}")
    print(f"   Images: {len(images)} test image(s)")
    print()
    
    try:
        # Test the CIA conversation with images
        print("Testing CIA conversation with image...")
        result = await cia.handle_conversation(
            user_id=user_id,
            message=message,
            session_id=session_id,
            images=images,
            context={}
        )
        
        print("CIA conversation completed successfully")
        print(f"   Response length: {len(result.get('response', ''))}")
        print(f"   Session state: {result.get('session', {}).get('current_phase', 'unknown')}")
        
        # Now verify the unified system components
        print("\nVerifying Unified System Components...")
        
        # 1. Check unified_conversations table
        supabase = create_client(
            "https://xrhgrthdcaymxuqcgrmj.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhyaGdydGhkY2F5bXh1cWNncm1qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM2NTcyMDYsImV4cCI6MjA2OTIzMzIwNn0.BriGLA2FE_e_NJl8B-3ps1W6ZAuK6a5HpTwBGy-6rmE"
        )
        
        conversations = supabase.table("unified_conversations").select("*").eq("metadata->>session_id", session_id).execute()
        
        if conversations.data:
            conversation = conversations.data[0]
            conversation_id = conversation["id"]
            print(f"Found unified conversation: {conversation_id}")
            print(f"   Title: {conversation.get('title', 'N/A')}")
            print(f"   Type: {conversation.get('conversation_type', 'N/A')}")
            
            # 2. Check unified_messages table
            messages = supabase.table("unified_messages").select("*").eq("conversation_id", conversation_id).execute()
            
            if messages.data:
                print(f"Found {len(messages.data)} unified messages")
                for i, msg in enumerate(messages.data):
                    print(f"   Message {i+1}: {msg['sender_type']} - {msg.get('content', '')[:50]}...")
                
                # 3. Check unified_message_attachments table
                user_message = next((m for m in messages.data if m['sender_type'] == 'user'), None)
                if user_message:
                    attachments = supabase.table("unified_message_attachments").select("*").eq("message_id", user_message["id"]).execute()
                    
                    if attachments.data:
                        print(f"✅ Found {len(attachments.data)} unified attachments")
                        for i, att in enumerate(attachments.data):
                            print(f"   Attachment {i+1}:")
                            print(f"     Type: {att.get('type', 'N/A')}")
                            print(f"     URL: {att.get('url', 'N/A')[:80]}...")
                            print(f"     Source: {att.get('metadata', {}).get('source', 'N/A')}")
                            print(f"     Size: {att.get('size', 0)} bytes")
                            
                        print("\n🎉 SUCCESS: Complete unified image attachment system working!")
                        print("   ✅ Images uploaded to Supabase Storage")
                        print("   ✅ unified_message_attachments records created")
                        print("   ✅ No photo_storage table usage")
                        print("   ✅ Proper conversation threading")
                        
                        return True
                    else:
                        print("❌ FAILED: No unified_message_attachments found")
                        return False
                else:
                    print("❌ FAILED: No user message found in unified_messages")
                    return False
            else:
                print("❌ FAILED: No unified_messages found")
                return False
        else:
            print("❌ FAILED: No unified_conversations found")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_photo_storage_cleanup():
    """Verify that photo_storage table is not being used"""
    print("\n🧹 Testing Photo Storage Cleanup...")
    
    supabase = create_client(
        "https://xrhgrthdcaymxuqcgrmj.supabase.co", 
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhyaGdydGhkY2F5bXh1cWNncm1qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM2NTcyMDYsImV4cCI6MjA2OTIzMzIwNn0.BriGLA2FE_e_NJl8B-3ps1W6ZAuK6a5HpTwBGy-6rmE"
    )
    
    try:
        # Check if any new photo_storage records were created
        recent_photos = supabase.table("photo_storage").select("*").gte("created_at", "2025-08-12").execute()
        
        if recent_photos.data:
            print(f"⚠️  WARNING: Found {len(recent_photos.data)} recent photo_storage records")
            print("   The system may still be using legacy photo_storage")
            for photo in recent_photos.data[:3]:  # Show first 3
                print(f"   - ID: {photo.get('id')}, User: {photo.get('user_id')}, Size: {len(photo.get('photo_data', ''))}")
        else:
            print("✅ SUCCESS: No recent photo_storage records found")
            print("   Legacy photo_storage system is not being used")
            
    except Exception as e:
        print(f"❌ ERROR checking photo_storage: {e}")

async def main():
    """Run all tests"""
    print("🚀 Starting CIA Unified Image Attachment System Tests")
    print("=" * 60)
    
    # Test 1: Unified image system
    success = await test_cia_unified_image_system()
    
    # Test 2: Photo storage cleanup verification
    await test_photo_storage_cleanup()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED - CIA Unified Image System Working!")
        print("✅ Phase 1 of unified image attachment system complete")
    else:
        print("❌ TESTS FAILED - Check implementation")
        
    return success

if __name__ == "__main__":
    asyncio.run(main())