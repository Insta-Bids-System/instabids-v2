#!/usr/bin/env python3
"""
Test the file flagged notification system
"""
import sys
import asyncio
sys.path.append('C:/Users/Not John Or Justin/Documents/instabids/ai-agents')

from services.file_flagged_notification_service import send_file_flagged_notification


async def test_notification_system():
    """Test sending file flagged notification"""
    
    print("=" * 60)
    print("TESTING FILE FLAGGED NOTIFICATION SYSTEM")
    print("=" * 60)
    
    # Test notification data
    test_data = {
        "contractor_id": "36fab309-1b11-4826-b108-dda79e12ce0d",  # Contractor with email
        "bid_card_id": "b3d32a5d-c5fb-491b-be86-a87edf4fb3b1",   # Existing bid card
        "file_name": "test_proposal_with_contact.pdf",
        "flagged_reason": "Contains phone number: 555-123-4567 and email: john@contractor.com",
        "confidence_score": 0.95,
        "review_queue_id": "test-queue-id-12345"
    }
    
    print(f"Testing notification for:")
    print(f"  Contractor: {test_data['contractor_id']}")
    print(f"  Bid Card: {test_data['bid_card_id']}")
    print(f"  File: {test_data['file_name']}")
    print(f"  Reason: {test_data['flagged_reason']}")
    print(f"  Confidence: {test_data['confidence_score']*100:.0f}%")
    
    try:
        result = await send_file_flagged_notification(**test_data)
        
        print(f"\nNOTIFICATION RESULT:")
        print(f"  Success: {result.get('success')}")
        print(f"  Notification ID: {result.get('notification_id')}")
        print(f"  Email Sent: {result.get('email_sent')}")
        print(f"  Contractor Email: {result.get('contractor_email')}")
        print(f"  Message: {result.get('message')}")
        
        if result.get('success'):
            print("\nSUCCESS: NOTIFICATION SYSTEM WORKING!")
        else:
            print(f"\nFAILED: NOTIFICATION ERROR: {result.get('error')}")
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_notification_system())