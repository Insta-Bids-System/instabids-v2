"""
Test the Fixed Message Routing System
Ensures messages go to the correct contractor conversation 100% of the time
"""
import requests
import json
from datetime import datetime
import time

# Configuration
BASE_URL = "http://localhost:8008/api/messages"
HOMEOWNER_ID = "11111111-1111-1111-1111-111111111111"
BID_CARD_ID = "36214de5-a068-4dcc-af99-cf33238e7472"  # Our test bid card

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

def test_explicit_conversation_routing():
    """Test Option 1: Explicit conversation_id targeting"""
    print("\n" + "="*80)
    print("TEST 1: EXPLICIT CONVERSATION_ID TARGETING")
    print("="*80)
    
    # First, get all conversations
    response = requests.get(
        f"{BASE_URL}/conversations/{BID_CARD_ID}",
        params={
            "user_type": "homeowner",
            "user_id": HOMEOWNER_ID
        }
    )
    
    if not response.ok:
        print("ERROR: Could not get conversations")
        return False
    
    conversations = response.json().get("conversations", [])
    print(f"Found {len(conversations)} existing conversations")
    
    # Test sending to specific conversation
    if conversations:
        target_conv = conversations[0]
        conv_id = target_conv["id"]
        contractor_id = target_conv["contractor_id"]
        
        print(f"\nSending to explicit conversation_id: {conv_id}")
        
        # Send message with explicit conversation_id
        send_response = requests.post(
            f"{BASE_URL}/send",
            json={
                "bid_card_id": BID_CARD_ID,
                "sender_id": HOMEOWNER_ID,
                "sender_type": "homeowner",
                "content": f"Testing explicit routing to conversation {conv_id[:8]}...",
                "conversation_id": conv_id  # EXPLICIT TARGETING
            }
        )
        
        if send_response.ok:
            result = send_response.json()
            if result.get("success"):
                print(f"[SUCCESS] Message sent successfully")
                print(f"  Returned conversation_id: {result.get('conversation_id')}")
                print(f"  Matches requested: {result.get('conversation_id') == conv_id}")
                return result.get('conversation_id') == conv_id
            else:
                print(f"[FAILED] Send failed: {result.get('error')}")
        else:
            print(f"[ERROR] API error: {send_response.status_code}")
    
    return False

def test_target_contractor_routing():
    """Test Option 2: target_contractor_id for homeowners"""
    print("\n" + "="*80)
    print("TEST 2: TARGET_CONTRACTOR_ID ROUTING")
    print("="*80)
    
    success_count = 0
    
    for contractor in CONTRACTORS[:3]:
        print(f"\nTesting routing to {contractor['name']}...")
        
        # Send message with target_contractor_id
        send_response = requests.post(
            f"{BASE_URL}/send",
            json={
                "bid_card_id": BID_CARD_ID,
                "sender_id": HOMEOWNER_ID,
                "sender_type": "homeowner",
                "content": f"Testing target routing to {contractor['name']}",
                "target_contractor_id": contractor["id"]  # TARGET SPECIFIC CONTRACTOR
            }
        )
        
        if send_response.ok:
            result = send_response.json()
            if result.get("success"):
                conv_id = result.get("conversation_id")
                print(f"[SUCCESS] Message sent to conversation: {conv_id}")
                
                # Verify it went to correct contractor
                msg_response = requests.get(f"{BASE_URL}/{conv_id}")
                if msg_response.ok:
                    messages = msg_response.json().get("messages", [])
                    # Check conversation has correct contractor
                    conv_response = requests.get(
                        f"{BASE_URL}/conversations/{BID_CARD_ID}",
                        params={
                            "user_type": "homeowner",
                            "user_id": HOMEOWNER_ID
                        }
                    )
                    if conv_response.ok:
                        convs = conv_response.json().get("conversations", [])
                        target_conv = next((c for c in convs if c["id"] == conv_id), None)
                        if target_conv and target_conv["contractor_id"] == contractor["id"]:
                            print(f"[VERIFIED] Message in correct contractor conversation")
                            success_count += 1
                        else:
                            print(f"[ERROR] Message went to wrong contractor!")
            else:
                print(f"[FAILED] Send failed: {result.get('error')}")
        
        time.sleep(0.5)
    
    print(f"\nSuccess rate: {success_count}/{len(CONTRACTORS[:3])}")
    return success_count == len(CONTRACTORS[:3])

def test_contractor_automatic_routing():
    """Test Option 3: Contractors get automatic routing"""
    print("\n" + "="*80)
    print("TEST 3: CONTRACTOR AUTOMATIC ROUTING")
    print("="*80)
    
    contractor = CONTRACTORS[0]
    print(f"\nTesting contractor {contractor['name']} sending without targeting...")
    
    # Contractor sends without any targeting info
    send_response = requests.post(
        f"{BASE_URL}/send",
        json={
            "bid_card_id": BID_CARD_ID,
            "sender_id": contractor["id"],
            "sender_type": "contractor",
            "content": f"This is {contractor['name']}. My message should auto-route correctly."
        }
    )
    
    if send_response.ok:
        result = send_response.json()
        if result.get("success"):
            conv_id = result.get("conversation_id")
            print(f"[SUCCESS] Message sent to conversation: {conv_id}")
            
            # Verify conversation belongs to this contractor
            conv_response = requests.get(
                f"{BASE_URL}/conversations/{BID_CARD_ID}",
                params={
                    "user_type": "contractor",
                    "user_id": contractor["id"]
                }
            )
            if conv_response.ok:
                convs = conv_response.json().get("conversations", [])
                if any(c["id"] == conv_id for c in convs):
                    print(f"[VERIFIED] Contractor's message in their own conversation")
                    return True
                else:
                    print(f"[ERROR] Contractor's message went to wrong conversation!")
        else:
            print(f"✗ Send failed: {result.get('error')}")
    
    return False

def test_ambiguous_homeowner_rejection():
    """Test Option 4: Homeowner without target should be rejected"""
    print("\n" + "="*80)
    print("TEST 4: AMBIGUOUS HOMEOWNER ROUTING REJECTION")
    print("="*80)
    
    print("\nTesting homeowner sending without target (should fail)...")
    
    # Homeowner sends without targeting info (SHOULD FAIL)
    send_response = requests.post(
        f"{BASE_URL}/send",
        json={
            "bid_card_id": BID_CARD_ID,
            "sender_id": HOMEOWNER_ID,
            "sender_type": "homeowner",
            "content": "This message has no target and should be rejected"
            # NO conversation_id or target_contractor_id
        }
    )
    
    if send_response.ok:
        result = send_response.json()
        if not result.get("success"):
            error = result.get("error", "")
            if "must specify target_contractor_id or conversation_id" in error:
                print(f"[CORRECT] Correctly rejected: {error}")
                return True
            else:
                print(f"[WRONG] Rejected but wrong error: {error}")
        else:
            print(f"[ERROR] Message was accepted when it should have been rejected!")
    
    return False

def test_cross_conversation_verification():
    """Verify messages stay in their assigned conversations"""
    print("\n" + "="*80)
    print("TEST 5: CROSS-CONVERSATION VERIFICATION")
    print("="*80)
    
    # Send unique messages to each contractor
    message_map = {}
    
    for i, contractor in enumerate(CONTRACTORS[:3], 1):
        unique_msg = f"Unique message #{i} for {contractor['name']} - timestamp {int(time.time())}"
        
        send_response = requests.post(
            f"{BASE_URL}/send",
            json={
                "bid_card_id": BID_CARD_ID,
                "sender_id": HOMEOWNER_ID,
                "sender_type": "homeowner",
                "content": unique_msg,
                "target_contractor_id": contractor["id"]
            }
        )
        
        if send_response.ok and send_response.json().get("success"):
            conv_id = send_response.json().get("conversation_id")
            message_map[contractor["id"]] = {
                "conv_id": conv_id,
                "unique_msg": unique_msg
            }
            print(f"[SENT] Unique message to {contractor['name']}")
        
        time.sleep(0.5)
    
    # Verify each conversation has ONLY its messages
    print("\nVerifying message isolation...")
    all_correct = True
    
    for contractor_id, data in message_map.items():
        conv_id = data["conv_id"]
        expected_msg = data["unique_msg"]
        
        msg_response = requests.get(f"{BASE_URL}/{conv_id}")
        if msg_response.ok:
            messages = msg_response.json().get("messages", [])
            
            # Check this conversation has the expected message
            has_expected = any(
                expected_msg in msg.get("filtered_content", "")
                for msg in messages
            )
            
            # Check it doesn't have other contractors' messages
            has_wrong = any(
                other_data["unique_msg"] in msg.get("filtered_content", "")
                for other_id, other_data in message_map.items()
                if other_id != contractor_id
                for msg in messages
            )
            
            if has_expected and not has_wrong:
                print(f"[CORRECT] Conversation {conv_id[:8]}... has correct messages only")
            else:
                print(f"[CONTAMINATED] Conversation {conv_id[:8]}... has message cross-contamination!")
                all_correct = False
    
    return all_correct

def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*80)
    print("FIXED MESSAGE ROUTING SYSTEM - COMPLETE TEST SUITE")
    print("="*80)
    print(f"Testing with bid card: {BID_CARD_ID}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check health first
    health_response = requests.get(f"{BASE_URL}/health")
    if not health_response.ok or not health_response.json().get("success"):
        print("\nERROR: Messaging system not healthy!")
        return
    
    print("\n[HEALTHY] Messaging system is healthy")
    
    # Run all tests
    test_results = {
        "Explicit conversation_id": test_explicit_conversation_routing(),
        "Target contractor_id": test_target_contractor_routing(),
        "Contractor auto-routing": test_contractor_automatic_routing(),
        "Ambiguous rejection": test_ambiguous_homeowner_rejection(),
        "Cross-conversation isolation": test_cross_conversation_verification()
    }
    
    # Summary
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    
    for test_name, passed in test_results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{test_name}: {status}")
    
    all_passed = all(test_results.values())
    total_passed = sum(1 for v in test_results.values() if v)
    
    print(f"\nOverall: {total_passed}/{len(test_results)} tests passed")
    
    if all_passed:
        print("\n[SUCCESS] Message routing is 100% ACCURATE!")
        print("\nThe fixed system ensures:")
        print("- Explicit conversation_id always routes correctly")
        print("- Target contractor_id creates/finds correct conversation")
        print("- Contractors automatically route to their conversation")
        print("- Ambiguous homeowner messages are rejected")
        print("- Messages stay isolated in their conversations")
    else:
        print("\n[PARTIAL] Some routing issues remain")

if __name__ == "__main__":
    run_all_tests()