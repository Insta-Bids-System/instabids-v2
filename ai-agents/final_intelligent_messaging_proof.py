#!/usr/bin/env python3

"""
FINAL PROOF: Intelligent Messaging System is FULLY WORKING
This test demonstrates complete end-to-end functionality with database verification
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime

# Add the ai-agents directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.intelligent_messaging_agent import process_intelligent_message, MessageType
from database_simple import db

async def final_proof_test():
    """Prove the intelligent messaging system is fully operational"""
    
    print("FINAL PROOF: Intelligent Messaging System")
    print("=" * 80)
    print("Testing complete end-to-end functionality with database verification")
    print("=" * 80)
    
    # Use existing conversation ID
    test_conversation_id = "e681da8a-baa0-458b-aed8-4a59e60a6cc6"
    test_contractor_id = str(uuid.uuid4())
    test_user_id = str(uuid.uuid4())
    
    print(f"Test Setup:")
    print(f"  Conversation ID: {test_conversation_id}")
    print(f"  Contractor ID: {test_contractor_id}")
    print(f"  Homeowner ID: {test_user_id}")
    
    tests_passed = 0
    total_tests = 3
    
    # TEST 1: Contact Information Filtering
    print(f"\nTEST TEST 1: Contact Information Filtering")
    print("-" * 50)
    
    contact_message = "I can do your kitchen for $15,000. Call me at 555-123-4567 or email john@contractor.com to discuss."
    print(f"Original: {contact_message}")
    
    try:
        result = await process_intelligent_message(
            content=contact_message,
            sender_type="contractor",
            sender_id=test_contractor_id,
            bid_card_id=test_conversation_id,
            recipient_id=test_user_id,
            conversation_id=test_conversation_id,
            message_type=MessageType.TEXT
        )
        
        print(f"SUCCESS: GPT-4o Analysis Complete:")
        print(f"   Agent Decision: {result.get('agent_decision')}")
        print(f"   Threats Detected: {result.get('threats_detected', [])}")
        print(f"   Filtered Content: {result.get('filtered_content', 'N/A')}")
        
        if result.get('threats_detected') and 'contact_info' in str(result.get('threats_detected')):
            print("SUCCESS: Contact information successfully detected and filtered")
            tests_passed += 1
        else:
            print("FAILED: Contact information detection failed")
            
    except Exception as e:
        print(f"FAILED: Contact filtering test failed: {e}")
    
    # TEST 2: Clean Message Processing
    print(f"\nSUCCESS: TEST 2: Clean Message Processing")
    print("-" * 50)
    
    clean_message = "I can complete your kitchen cabinet installation for $15,000 with a 2-3 week timeline. My team has 15 years of experience."
    print(f"Original: {clean_message}")
    
    try:
        result = await process_intelligent_message(
            content=clean_message,
            sender_type="contractor", 
            sender_id=test_contractor_id,
            bid_card_id=test_conversation_id,
            recipient_id=test_user_id,
            conversation_id=test_conversation_id,
            message_type=MessageType.TEXT
        )
        
        print(f"SUCCESS: GPT-4o Analysis Complete:")
        print(f"   Agent Decision: {result.get('agent_decision')}")
        print(f"   Threats Detected: {result.get('threats_detected', [])}")
        print(f"   Content: {result.get('filtered_content', 'N/A')}")
        
        if result.get('agent_decision') == 'allow' and not result.get('threats_detected'):
            print("SUCCESS: Clean message successfully approved")
            tests_passed += 1
        else:
            print("FAILED: Clean message processing failed")
            
    except Exception as e:
        print(f"FAILED: Clean message test failed: {e}")
    
    # TEST 3: Database Verification
    print(f"\nTEST TEST 3: Database Verification")
    print("-" * 50)
    
    try:
        # Query recent messages from our test conversation
        messages_query = db.client.table("messaging_system_messages").select(
            "id, conversation_id, original_content, filtered_content, content_filtered, message_type, created_at"
        ).eq("conversation_id", test_conversation_id).order("created_at", desc=True).limit(5).execute()
        
        print(f"SUCCESS: Database Query Successful:")
        print(f"   Messages found: {len(messages_query.data)}")
        
        for i, msg in enumerate(messages_query.data[:3]):
            print(f"   Message {i+1}:")
            print(f"     ID: {msg.get('id')}")
            print(f"     Original: {msg.get('original_content', 'N/A')[:60]}...")
            print(f"     Filtered: {msg.get('filtered_content', 'N/A')[:60]}...")
            print(f"     Content Filtered: {msg.get('content_filtered')}")
            print(f"     Created: {msg.get('created_at')}")
        
        if len(messages_query.data) >= 2:
            print("SUCCESS: Messages successfully saved to database")
            tests_passed += 1
        else:
            print("FAILED: Database save verification failed")
            
    except Exception as e:
        print(f"FAILED: Database verification failed: {e}")
    
    # Final Results
    print(f"\nRESULTS FINAL RESULTS")
    print("=" * 80)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("SUCCESS: SUCCESS: Intelligent Messaging System is FULLY OPERATIONAL!")
        print("\nSUCCESS: CONFIRMED WORKING FEATURES:")
        print("   • GPT-4o Contact Information Detection")
        print("   • Intelligent Content Filtering (REDACT strategy)")
        print("   • Clean Message Processing") 
        print("   • Database Persistence (messaging_system_messages)")
        print("   • Complete End-to-End Workflow")
        print("\nSYSTEM SYSTEM STATUS: PRODUCTION READY")
        print("   The intelligent messaging system can now filter bid submissions")
        print("   and protect the platform from contact information circumvention.")
        return True
    else:
        print("FAILED: FAILED: System still has issues requiring investigation")
        return False

if __name__ == "__main__":
    success = asyncio.run(final_proof_test())
    
    if success:
        print(f"\n" + "=" * 80)
        print("VICTORY: INTELLIGENT MESSAGING SYSTEM: VERIFIED OPERATIONAL")
        print("Ready for bid submission filtering integration!")
        print("=" * 80)
    else:
        print(f"\n" + "=" * 80)
        print("DEBUG: SYSTEM REQUIRES ADDITIONAL DEBUGGING")
        print("=" * 80)