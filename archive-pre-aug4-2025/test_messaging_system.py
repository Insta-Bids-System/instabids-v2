"""
Test script for the messaging system
Tests the LangGraph content filtering and database operations
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

from agents.messaging_agent import process_message, process_broadcast
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client():
    supabase_url = os.getenv("SUPABASE_URL", "https://xrhgrthdcaymxuqcgrmj.supabase.co")
    supabase_key = os.getenv("SUPABASE_ANON_KEY", "")
    return create_client(supabase_url, supabase_key)
import json

async def test_messaging_system():
    """Test the complete messaging system"""
    
    print("Testing InstaBids Messaging System")
    print("=" * 50)
    
    # Test bid card ID (use one from the database)
    test_bid_card_id = "550e8400-e29b-41d4-a716-446655440001"
    test_user_id = "test-homeowner-123"
    test_contractor_id = "test-contractor-456"
    
    # Test 1: Send contractor message with contact info
    print("\nTest 1: Contractor message with contact info")
    contractor_message = "Hi, I'm very interested in your kitchen remodel project. Please call me at 555-123-4567 or email me at john@contractor.com"
    
    result = await process_message(
        content=contractor_message,
        sender_type="contractor",
        sender_id=test_contractor_id,
        bid_card_id=test_bid_card_id
    )
    
    print(f"Original: {contractor_message}")
    print(f"Filtered: {result['filtered_content']}")
    print(f"Content filtered: {result['content_filtered']}")
    print(f"Filter reasons: {json.dumps(result['filter_reasons'], indent=2)}")
    print(f"Conversation ID: {result.get('conversation_id', 'Not created')}")
    
    # Test 2: Homeowner response
    print("\nTest 2: Homeowner response")
    homeowner_message = "Thanks for your interest! Can you provide more details about your experience with kitchen remodels?"
    
    result2 = await process_message(
        content=homeowner_message,
        sender_type="homeowner", 
        sender_id=test_user_id,
        bid_card_id=test_bid_card_id,
        conversation_id=result.get('conversation_id')
    )
    
    print(f"Original: {homeowner_message}")
    print(f"Filtered: {result2['filtered_content']}")
    print(f"Content filtered: {result2['content_filtered']}")
    
    # Test 3: Broadcast message
    print("\nTest 3: Broadcast message from homeowner")
    broadcast_message = "Update: We've decided to expand the project scope. Reach me at 555-987-6543 for details."
    
    broadcast_result = await process_broadcast(
        content=broadcast_message,
        sender_type="homeowner",
        sender_id=test_user_id,
        bid_card_id=test_bid_card_id,
        recipient_type="all_contractors"
    )
    
    print(f"Original: {broadcast_message}")
    print(f"Filtered: {broadcast_result['filtered_content']}")
    print(f"Total recipients: {broadcast_result['total_recipients']}")
    
    # Test 4: Check database
    print("\nTest 4: Verify database storage")
    db = get_supabase_client()
    
    # Check conversations
    conversations = db.table("conversations").select("*").eq(
        "bid_card_id", test_bid_card_id
    ).execute()
    print(f"Conversations created: {len(conversations.data)}")
    
    if conversations.data:
        conv = conversations.data[0]
        print(f"Contractor alias: {conv['contractor_alias']}")
        
        # Check messages
        messages = db.table("messages").select("*").eq(
            "conversation_id", conv['id']
        ).order("created_at", desc=True).execute()
        
        print(f"Messages in conversation: {len(messages.data)}")
        for msg in messages.data[:3]:  # Show first 3 messages
            print(f"  - {msg['sender_type']}: {msg['filtered_content'][:50]}...")
    
    # Test 5: Various contact patterns
    print("\nTest 5: Testing various contact patterns")
    test_patterns = [
        "My Instagram is @contractorjohn",
        "Visit our website at contractorjohn.com",
        "Our office is at 123 Main Street, Suite 200",
        "You can text me at (555) 987-6543",
        "Send details to contractor@email.com",
        "WhatsApp me for faster response"
    ]
    
    for pattern in test_patterns:
        result = await process_message(
            content=pattern,
            sender_type="contractor",
            sender_id=test_contractor_id + "-2",
            bid_card_id=test_bid_card_id
        )
        print(f"'{pattern}' → '{result['filtered_content']}'")
    
    print("\nMessaging system test complete!")

if __name__ == "__main__":
    asyncio.run(test_messaging_system())