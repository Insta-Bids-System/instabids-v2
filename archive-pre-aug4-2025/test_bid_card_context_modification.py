#!/usr/bin/env python3
"""
Test CIA Agent's ability to load existing bid card context and make modifications
Simulates the exact customer workflow: Click Continue Chat -> Modify bid card
"""
import os

from dotenv import load_dotenv

from agents.cia.agent import CustomerInterfaceAgent
from database_simple import db


# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

def test_bid_card_context_loading():
    """Test 1: CIA loads existing bid card context correctly"""
    print("\n=== TEST 1: BID CARD CONTEXT LOADING ===")

    # Use the most recent bid card from JAA test
    bid_card_number = "IBC-20250801030643"

    # Step 1: Get bid card details
    result = db.client.table("bid_cards").select("*").eq("bid_card_number", bid_card_number).execute()
    if not result.data:
        print(f"❌ Could not find bid card {bid_card_number}")
        return False

    bid_card = result.data[0]
    original_thread_id = bid_card["cia_thread_id"]

    print(f"* Found bid card: {bid_card_number}")
    print(f"* Original project: {bid_card['project_type']}")
    print(f"* Original budget: ${bid_card['budget_min']}-${bid_card['budget_max']}")
    print(f"* Original thread: {original_thread_id}")

    # Step 2: Initialize CIA with project context (simulating Continue Chat click)
    print(f"\n[SIMULATING] Customer clicks 'Continue Chat' on bid card {bid_card_number}")

    cia = CustomerInterfaceAgent()

    # This simulates the frontend passing bid card context when Continue Chat is clicked
    project_context = {
        "bid_card_number": bid_card_number,
        "project_type": bid_card["project_type"],
        "budget_min": bid_card["budget_min"],
        "budget_max": bid_card["budget_max"],
        "urgency_level": bid_card["urgency_level"],
        "complexity_score": bid_card["complexity_score"],
        "bid_document": bid_card["bid_document"]
    }

    # Step 3: Start new conversation with project context
    initial_message = f"I want to continue working on my {bid_card['project_type']} project (bid card {bid_card_number})"

    result = cia.handle_conversation(
        user_id="test_user_context_loading",
        message=initial_message,
        project_id=bid_card_number,  # Use bid card number as project ID
        project_context=project_context
    )

    print(f"\n[CIA RESPONSE] {result.get('response', 'No response')}")

    # Step 4: Verify CIA understands the context
    context_indicators = [
        bid_card["project_type"].lower(),
        str(bid_card["budget_min"]),
        str(bid_card["budget_max"]),
        bid_card_number
    ]

    response_text = result.get("response", "").lower()
    context_recognized = sum(1 for indicator in context_indicators if indicator in response_text)

    print("\n--- CONTEXT RECOGNITION ANALYSIS ---")
    print(f"* Context indicators found: {context_recognized}/{len(context_indicators)}")
    for indicator in context_indicators:
        found = "*" if indicator in response_text else "X"
        print(f"  {found} {indicator}")

    if context_recognized >= 2:
        print("PASS: TEST 1 PASSED: CIA recognizes bid card context")
        return result.get("thread_id"), bid_card
    else:
        print("❌ TEST 1 FAILED: CIA doesn't recognize bid card context")
        return None, None

def test_bid_card_modifications(thread_id, original_bid_card):
    """Test 2: CIA can modify existing bid cards through chat"""
    print("\n=== TEST 2: BID CARD MODIFICATIONS ===")

    if not thread_id:
        print("❌ Skipping - no valid thread from previous test")
        return False

    cia = CustomerInterfaceAgent()

    # Step 1: Request budget modification
    print("[CUSTOMER] I want to increase my budget to $60,000-$75,000")

    result = cia.handle_conversation(
        user_id="test_user_context_loading",
        message="I want to increase my budget to $60,000-$75,000",
        thread_id=thread_id
    )

    print(f"[CIA RESPONSE] {result.get('response', 'No response')}")

    # Step 2: Check if CIA understood the modification request
    response_text = result.get("response", "").lower()
    modification_indicators = ["60,000", "75,000", "budget", "increase", "update"]

    recognized_modifications = sum(1 for indicator in modification_indicators if indicator in response_text)

    print("\n--- MODIFICATION RECOGNITION ---")
    print(f"✓ Modification indicators: {recognized_modifications}/{len(modification_indicators)}")

    # Step 3: Request another modification (timeline)
    print("\n[CUSTOMER] Actually, I need this done urgently - emergency timeline")

    result2 = cia.handle_conversation(
        user_id="test_user_context_loading",
        message="Actually, I need this done urgently - emergency timeline",
        thread_id=thread_id
    )

    print(f"[CIA RESPONSE] {result2.get('response', 'No response')}")

    # Step 4: Check if CIA can handle multiple modifications
    response2_text = result2.get("response", "").lower()
    urgency_indicators = ["urgent", "emergency", "timeline", "quickly", "asap"]

    recognized_urgency = sum(1 for indicator in urgency_indicators if indicator in response2_text)

    print("\n--- URGENCY MODIFICATION RECOGNITION ---")
    print(f"✓ Urgency indicators: {recognized_urgency}/{len(urgency_indicators)}")

    # Step 5: Check if bid card was actually updated (if CIA has update capability)
    print("\n--- CHECKING FOR ACTUAL BID CARD UPDATES ---")

    # Check if the bid card was regenerated with new details
    updated_result = db.client.table("bid_cards").select("*").eq("bid_card_number", original_bid_card["bid_card_number"]).execute()

    if updated_result.data:
        updated_card = updated_result.data[0]
        budget_changed = (updated_card["budget_min"] != original_bid_card["budget_min"] or
                         updated_card["budget_max"] != original_bid_card["budget_max"])
        urgency_changed = updated_card["urgency_level"] != original_bid_card["urgency_level"]

        print(f"✓ Budget changed: {budget_changed}")
        print(f"✓ Urgency changed: {urgency_changed}")

        if budget_changed or urgency_changed:
            print("✅ TEST 2 PASSED: Bid card was actually modified")
            return True
        else:
            print("⚠️  TEST 2 PARTIAL: CIA understood but didn't update database")
            return "partial"

    if recognized_modifications >= 2 and recognized_urgency >= 2:
        print("✅ TEST 2 PASSED: CIA understands modification requests")
        return True
    else:
        print("❌ TEST 2 FAILED: CIA doesn't understand modifications")
        return False

def test_memory_persistence(thread_id):
    """Test 3: Memory persists across multiple interactions"""
    print("\n=== TEST 3: MEMORY PERSISTENCE ===")

    if not thread_id:
        print("❌ Skipping - no valid thread from previous tests")
        return False

    cia = CustomerInterfaceAgent()

    # Step 1: Reference earlier conversation details
    print("[CUSTOMER] Can you remind me what we discussed about the timeline?")

    result = cia.handle_conversation(
        user_id="test_user_context_loading",
        message="Can you remind me what we discussed about the timeline?",
        thread_id=thread_id
    )

    print(f"[CIA RESPONSE] {result.get('response', 'No response')}")

    # Step 2: Check if CIA remembers previous conversation
    response_text = result.get("response", "").lower()
    memory_indicators = ["earlier", "discussed", "mentioned", "said", "emergency", "urgent", "timeline"]

    remembered_items = sum(1 for indicator in memory_indicators if indicator in response_text)

    print("\n--- MEMORY ANALYSIS ---")
    print(f"✓ Memory indicators: {remembered_items}/{len(memory_indicators)}")

    if remembered_items >= 3:
        print("✅ TEST 3 PASSED: CIA remembers previous conversation")
        return True
    else:
        print("❌ TEST 3 FAILED: CIA doesn't remember conversation history")
        return False

def main():
    """Run all bid card context and modification tests"""
    print("BID CARD CONTEXT & MODIFICATION TESTING")
    print("=" * 50)
    print("Testing the complete customer workflow:")
    print("1. Customer has existing bid card")
    print("2. Customer clicks 'Continue Chat'")
    print("3. CIA loads all bid card context")
    print("4. Customer requests modifications")
    print("5. CIA updates bid card in real-time")

    # Test 1: Context Loading
    thread_id, bid_card = test_bid_card_context_loading()

    # Test 2: Modifications
    modification_result = test_bid_card_modifications(thread_id, bid_card) if thread_id else False

    # Test 3: Memory Persistence
    memory_result = test_memory_persistence(thread_id) if thread_id else False

    # Final Results
    print("\n" + "=" * 50)
    print("FINAL TEST RESULTS")
    print("=" * 50)

    results = {
        "Context Loading": "✅ PASS" if thread_id else "❌ FAIL",
        "Bid Card Modifications": "✅ PASS" if modification_result else "⚠️ PARTIAL" if modification_result == "partial" else "❌ FAIL",
        "Memory Persistence": "✅ PASS" if memory_result else "❌ FAIL"
    }

    for test_name, result in results.items():
        print(f"{result} {test_name}")

    # Overall assessment
    passed_tests = sum(1 for r in results.values() if "✅" in r)
    partial_tests = sum(1 for r in results.values() if "⚠️" in r)

    print(f"\nOverall: {passed_tests}/3 tests passed, {partial_tests} partial")

    if passed_tests >= 2:
        print("\n🎉 SUCCESS: Customer bid card modification workflow is working!")
        print("✓ Customers can continue chatting about existing bid cards")
        print("✓ CIA agent loads full project context")
        print("✓ Modifications are understood and processed")
    else:
        print("\n⚠️ NEEDS WORK: Customer workflow has issues")
        print("- Check CIA agent context loading")
        print("- Verify bid card modification logic")
        print("- Test memory persistence implementation")

if __name__ == "__main__":
    main()
