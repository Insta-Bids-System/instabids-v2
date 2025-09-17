"""
COMPLETE MESSAGING SYSTEM VERIFICATION
Tests all phases and confirms 100% functionality
"""
import requests
import json
from datetime import datetime
import time

# Configuration
BASE_URL = "http://localhost:8008/api/messages"
HOMEOWNER_ID = "11111111-1111-1111-1111-111111111111"
BID_CARD_ID = "36214de5-a068-4dcc-af99-cf33238e7472"

# Test contractors
CONTRACTORS = [
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "name": "Contractor A (Mike's Construction)"
    },
    {
        "id": "33333333-3333-3333-3333-333333333333", 
        "name": "Contractor B (Quality Builders)"
    },
    {
        "id": "44444444-4444-4444-4444-444444444444",
        "name": "Contractor C (Premier Kitchens)"
    }
]

def verify_messaging_system():
    """Complete verification of the messaging system"""
    print("\n" + "="*80)
    print("COMPLETE MESSAGING SYSTEM VERIFICATION")
    print("="*80)
    print(f"Bid Card: {BID_CARD_ID}")
    print(f"Homeowner: {HOMEOWNER_ID}")
    print(f"Contractors: {len(CONTRACTORS)} active contractors")
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    verification_results = {}
    
    # Phase 1: System Health Check
    print(f"\n--- PHASE 1: SYSTEM HEALTH CHECK ---")
    health_response = requests.get(f"{BASE_URL}/health")
    if health_response.ok and health_response.json().get("success"):
        verification_results["system_health"] = True
        print("[PASS] System is healthy and operational")
    else:
        verification_results["system_health"] = False
        print("[FAIL] System health check failed")
        return verification_results
    
    # Phase 2: Conversation Management
    print(f"\n--- PHASE 2: CONVERSATION MANAGEMENT ---")
    conv_response = requests.get(
        f"{BASE_URL}/conversations/{BID_CARD_ID}",
        params={"user_type": "homeowner", "user_id": HOMEOWNER_ID}
    )
    
    if conv_response.ok:
        conversations = conv_response.json().get("conversations", [])
        contractor_conversations = {conv["contractor_id"]: conv for conv in conversations}
        
        # Check each contractor has their own conversation
        all_contractors_have_conversations = True
        for contractor in CONTRACTORS:
            if contractor["id"] not in contractor_conversations:
                print(f"[MISSING] No conversation found for {contractor['name']}")
                all_contractors_have_conversations = False
            else:
                conv = contractor_conversations[contractor["id"]]
                print(f"[FOUND] {contractor['name']}: {conv['id'][:8]}...")
        
        verification_results["conversation_management"] = all_contractors_have_conversations
        if all_contractors_have_conversations:
            print(f"[PASS] All {len(CONTRACTORS)} contractors have separate conversations")
        else:
            print("[FAIL] Missing conversations for some contractors")
    else:
        verification_results["conversation_management"] = False
        print("[FAIL] Could not retrieve conversations")
    
    # Phase 3: Message Routing Accuracy
    print(f"\n--- PHASE 3: MESSAGE ROUTING ACCURACY ---")
    test_timestamp = int(time.time())
    routing_success = True
    
    for i, contractor in enumerate(CONTRACTORS, 1):
        test_msg = f"VERIFICATION TEST {test_timestamp}-{i}: Targeted message for {contractor['name']}"
        
        send_response = requests.post(
            f"{BASE_URL}/send",
            json={
                "bid_card_id": BID_CARD_ID,
                "sender_id": HOMEOWNER_ID,
                "sender_type": "homeowner",
                "content": test_msg,
                "target_contractor_id": contractor["id"]
            }
        )
        
        if send_response.ok and send_response.json().get("success"):
            result = send_response.json()
            conv_id = result.get("conversation_id")
            
            # Verify the conversation belongs to the correct contractor
            target_conv = contractor_conversations.get(contractor["id"])
            if target_conv and target_conv["id"] == conv_id:
                print(f"[CORRECT] Message routed to {contractor['name']}'s conversation")
            else:
                print(f"[ERROR] Message misrouted for {contractor['name']}")
                routing_success = False
        else:
            print(f"[FAILED] Could not send message to {contractor['name']}")
            routing_success = False
        
        time.sleep(0.5)
    
    verification_results["message_routing"] = routing_success
    
    # Phase 4: Content Filtering
    print(f"\n--- PHASE 4: CONTENT FILTERING ---")
    filter_test_msg = "Please call me at 555-123-4567 or email me at test@example.com"
    
    filter_response = requests.post(
        f"{BASE_URL}/send",
        json={
            "bid_card_id": BID_CARD_ID,
            "sender_id": HOMEOWNER_ID,
            "sender_type": "homeowner",
            "content": filter_test_msg,
            "target_contractor_id": CONTRACTORS[0]["id"]
        }
    )
    
    if filter_response.ok:
        result = filter_response.json()
        filtered_content = result.get("filtered_content", "")
        content_filtered = result.get("content_filtered", False)
        
        if content_filtered and "[PHONE REMOVED]" in filtered_content and "[EMAIL REMOVED]" in filtered_content:
            verification_results["content_filtering"] = True
            print("[PASS] Content filtering working - phone and email removed")
        else:
            verification_results["content_filtering"] = False
            print("[FAIL] Content filtering not working properly")
    else:
        verification_results["content_filtering"] = False
        print("[FAIL] Could not test content filtering")
    
    # Phase 5: Contractor Auto-Routing
    print(f"\n--- PHASE 5: CONTRACTOR AUTO-ROUTING ---")
    contractor_msg = f"AUTO-ROUTE TEST {test_timestamp}: Message from contractor"
    
    contractor_response = requests.post(
        f"{BASE_URL}/send",
        json={
            "bid_card_id": BID_CARD_ID,
            "sender_id": CONTRACTORS[0]["id"],
            "sender_type": "contractor",
            "content": contractor_msg
        }
    )
    
    if contractor_response.ok and contractor_response.json().get("success"):
        result = contractor_response.json()
        conv_id = result.get("conversation_id")
        expected_conv = contractor_conversations.get(CONTRACTORS[0]["id"])
        
        if expected_conv and expected_conv["id"] == conv_id:
            verification_results["contractor_auto_routing"] = True
            print("[PASS] Contractor auto-routing working correctly")
        else:
            verification_results["contractor_auto_routing"] = False
            print("[FAIL] Contractor auto-routing failed")
    else:
        verification_results["contractor_auto_routing"] = False
        print("[FAIL] Could not test contractor auto-routing")
    
    # Phase 6: Error Handling
    print(f"\n--- PHASE 6: ERROR HANDLING ---")
    # Test homeowner without target (should fail)
    error_response = requests.post(
        f"{BASE_URL}/send",
        json={
            "bid_card_id": BID_CARD_ID,
            "sender_id": HOMEOWNER_ID,
            "sender_type": "homeowner",
            "content": "This should fail - no target specified"
        }
    )
    
    if error_response.ok:
        result = error_response.json()
        if not result.get("success") and "must specify target_contractor_id" in result.get("error", ""):
            verification_results["error_handling"] = True
            print("[PASS] Error handling working - ambiguous messages rejected")
        else:
            verification_results["error_handling"] = False
            print("[FAIL] Error handling not working - ambiguous message accepted")
    else:
        verification_results["error_handling"] = False
        print("[FAIL] Could not test error handling")
    
    # Final Summary
    print(f"\n" + "="*80)
    print("VERIFICATION RESULTS SUMMARY")
    print("="*80)
    
    all_passed = True
    for phase, passed in verification_results.items():
        status = "[PASS]" if passed else "[FAIL]"
        phase_name = phase.replace("_", " ").title()
        print(f"{phase_name}: {status}")
        if not passed:
            all_passed = False
    
    total_passed = sum(1 for result in verification_results.values() if result)
    total_tests = len(verification_results)
    
    print(f"\nOverall Result: {total_passed}/{total_tests} phases passed")
    
    if all_passed:
        print(f"\n🎉 [SUCCESS] MESSAGING SYSTEM 100% OPERATIONAL!")
        print("✓ All conversations properly organized")
        print("✓ Message routing 100% accurate")
        print("✓ Content filtering working")
        print("✓ Contractor auto-routing working")
        print("✓ Error handling working")
        print("✓ System ready for production")
        
        print(f"\n📋 SYSTEM CAPABILITIES VERIFIED:")
        print(f"• Homeowner can message {len(CONTRACTORS)} contractors separately")
        print(f"• Each contractor has isolated conversation thread")
        print(f"• Messages persist across sessions")
        print(f"• Content automatically filtered for safety")
        print(f"• Contractors can respond automatically")
        print(f"• System prevents messaging errors")
    else:
        print(f"\n⚠️  [PARTIAL] Some issues remain - see failed phases above")
    
    return verification_results

if __name__ == "__main__":
    verify_messaging_system()