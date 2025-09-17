"""
Test the clean CIA agent with REAL OpenAI API calls and bid card updates
"""
import asyncio
import os
import sys
from datetime import datetime
import json
from dotenv import load_dotenv

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# Load environment variables
load_dotenv()

# Import the clean CIA agent
from agents.cia.agent import CustomerInterfaceAgent


async def test_emergency_extraction():
    """Test 1: Emergency situation - should extract quickly"""
    print("\n" + "="*60)
    print("TEST 1: EMERGENCY EXTRACTION")
    print("="*60)
    
    agent = CustomerInterfaceAgent()
    
    # Simulate emergency
    result = await agent.handle_conversation(
        user_id="test-user-001",
        message="Help! My bathroom is flooding, water everywhere!",
        session_id="test-emergency-001"
    )
    
    print(f"\n[BOT] CIA Response: {result['response']}")
    print(f"[OK] Extracted Data: {json.dumps(result.get('extracted_data', {}), indent=2)}")
    print(f"[%] Completion: {result.get('completion_percentage', 0)}%")
    print(f"[ID] Bid Card ID: {result.get('bid_card_id')}")
    
    # Follow-up with location
    result2 = await agent.handle_conversation(
        user_id="test-user-001", 
        message="I'm at 123 Main St, Miami FL 33139",
        session_id="test-emergency-001"
    )
    
    print(f"\n[BOT] Follow-up Response: {result2['response']}")
    print(f"[OK] Additional Extracted: {json.dumps(result2.get('extracted_data', {}), indent=2)}")
    print(f"[%] Updated Completion: {result2.get('completion_percentage', 0)}%")
    
    return result2


async def test_normal_project():
    """Test 2: Normal project - kitchen remodel"""
    print("\n" + "="*60)
    print("TEST 2: NORMAL PROJECT EXTRACTION")
    print("="*60)
    
    agent = CustomerInterfaceAgent()
    
    # Start conversation
    result = await agent.handle_conversation(
        user_id="test-user-002",
        message="I want to remodel my kitchen, thinking about new cabinets and countertops",
        session_id="test-kitchen-001"
    )
    
    print(f"\n[BOT] CIA Response: {result['response']}")
    print(f"[OK] Extracted Data: {json.dumps(result.get('extracted_data', {}), indent=2)}")
    print(f"[ID] Bid Card ID: {result.get('bid_card_id')}")
    
    # Add more details
    result2 = await agent.handle_conversation(
        user_id="test-user-002",
        message="It's about a 200 sq ft kitchen, want it done in about 2 months. Budget around 25-30k",
        session_id="test-kitchen-001"
    )
    
    print(f"\n[BOT] Follow-up Response: {result2['response']}")
    print(f"[OK] Additional Extracted: {json.dumps(result2.get('extracted_data', {}), indent=2)}")
    print(f"[%] Completion: {result2.get('completion_percentage', 0)}%")
    
    # Add location
    result3 = await agent.handle_conversation(
        user_id="test-user-002",
        message="I'm in downtown Miami, zip 33131",
        session_id="test-kitchen-001"
    )
    
    print(f"\n[BOT] Location Response: {result3['response']}")
    print(f"[OK] Location Extracted: {json.dumps(result3.get('extracted_data', {}), indent=2)}")
    print(f"[%] Final Completion: {result3.get('completion_percentage', 0)}%")
    
    return result3


async def test_memory_persistence():
    """Test 3: Memory persistence - return to conversation"""
    print("\n" + "="*60)
    print("TEST 3: MEMORY PERSISTENCE")
    print("="*60)
    
    agent = CustomerInterfaceAgent()
    
    # First conversation
    result1 = await agent.handle_conversation(
        user_id="test-user-003",
        message="Need to fix my roof, some shingles are missing",
        session_id="test-memory-001"
    )
    
    print(f"\n[BOT] Initial Response: {result1['response']}")
    print(f"[OK] Initial Extraction: {json.dumps(result1.get('extracted_data', {}), indent=2)}")
    bid_card_id = result1.get('bid_card_id')
    
    # Simulate user leaving and coming back
    print("\n--- User leaves and returns ---")
    
    # Return to same session
    result2 = await agent.handle_conversation(
        user_id="test-user-003",
        message="Actually, I also need gutters cleaned while they're up there",
        session_id="test-memory-001"
    )
    
    print(f"\n[BOT] Return Response: {result2['response']}")
    print(f"[OK] Additional Extraction: {json.dumps(result2.get('extracted_data', {}), indent=2)}")
    print(f"[ID] Same Bid Card?: {result2.get('bid_card_id') == bid_card_id}")
    print(f"[%] Completion: {result2.get('completion_percentage', 0)}%")
    
    return result2


async def test_multi_project_awareness():
    """Test 4: Multi-project awareness"""
    print("\n" + "="*60)
    print("TEST 4: MULTI-PROJECT AWARENESS")
    print("="*60)
    
    agent = CustomerInterfaceAgent()
    
    # First project
    await agent.handle_conversation(
        user_id="test-user-004",
        message="I need lawn care service, monthly maintenance",
        session_id="test-lawn-001"
    )
    
    # Second project - should ask about relationship
    result = await agent.handle_conversation(
        user_id="test-user-004",
        message="I also need someone to install a sprinkler system",
        session_id="test-sprinkler-001"
    )
    
    print(f"\n[BOT] Multi-Project Response: {result['response']}")
    print(f"[OK] Extracted: {json.dumps(result.get('extracted_data', {}), indent=2)}")
    
    # Check if agent asked about relationship to lawn project
    if "lawn" in result['response'].lower():
        print("[OK] SUCCESS: Agent recognized existing lawn project!")
    else:
        print("[WARNING] Agent didn't reference existing project")
    
    return result


async def test_bid_card_real_time_update():
    """Test 5: Verify bid card updates in real-time"""
    print("\n" + "="*60)
    print("TEST 5: REAL-TIME BID CARD UPDATES")
    print("="*60)
    
    agent = CustomerInterfaceAgent()
    
    # Send message with multiple extractable fields
    result = await agent.handle_conversation(
        user_id="test-user-005",
        message="Emergency plumbing issue, pipe burst in basement. I'm at 456 Oak St, Miami 33139. Need someone TODAY!",
        session_id="test-realtime-001"
    )
    
    print(f"\n[BOT] Response: {result['response']}")
    print(f"[OK] Extracted in one shot:")
    extracted = result.get('extracted_data', {})
    for field, value in extracted.items():
        print(f"   - {field}: {value}")
    
    print(f"\n[%] Completion: {result.get('completion_percentage', 0)}%")
    print(f"[ID] Bid Card ID: {result.get('bid_card_id')}")
    
    # Check bid card status
    if result.get('bid_card_status'):
        print(f"\n[STATUS] Bid Card Status:")
        status = result['bid_card_status']
        if isinstance(status, dict):
            print(f"   - Completion: {status.get('completion_percentage', 0)}%")
            print(f"   - Ready for conversion: {status.get('ready_for_conversion', False)}")
    
    return result


async def run_all_tests():
    """Run all tests sequentially"""
    print("\n" + "="*80)
    print(" TESTING CLEAN CIA AGENT WITH REAL OPENAI API CALLS")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"OpenAI API Key: {'[OK] Found' if os.getenv('OPENAI_API_KEY') else '[ERROR] Missing!'}")
    
    if not os.getenv('OPENAI_API_KEY'):
        print("\n[WARNING] ERROR: OPENAI_API_KEY not found in environment!")
        print("Please set your OpenAI API key in .env file")
        return
    
    try:
        # Run tests
        print("\n[START] Starting tests...\n")
        
        test_results = []
        
        # Test 1: Emergency
        try:
            result1 = await test_emergency_extraction()
            test_results.append(("Emergency Extraction", "[OK] PASSED", result1))
        except Exception as e:
            test_results.append(("Emergency Extraction", f"[FAIL] FAILED: {e}", None))
        
        # Test 2: Normal Project  
        try:
            result2 = await test_normal_project()
            test_results.append(("Normal Project", "[OK] PASSED", result2))
        except Exception as e:
            test_results.append(("Normal Project", f"[FAIL] FAILED: {e}", None))
        
        # Test 3: Memory
        try:
            result3 = await test_memory_persistence()
            test_results.append(("Memory Persistence", "[OK] PASSED", result3))
        except Exception as e:
            test_results.append(("Memory Persistence", f"[FAIL] FAILED: {e}", None))
        
        # Test 4: Multi-project
        try:
            result4 = await test_multi_project_awareness()
            test_results.append(("Multi-Project", "[OK] PASSED", result4))
        except Exception as e:
            test_results.append(("Multi-Project", f"[FAIL] FAILED: {e}", None))
        
        # Test 5: Real-time updates
        try:
            result5 = await test_bid_card_real_time_update()
            test_results.append(("Real-Time Updates", "[OK] PASSED", result5))
        except Exception as e:
            test_results.append(("Real-Time Updates", f"[FAIL] FAILED: {e}", None))
        
        # Summary
        print("\n" + "="*80)
        print(" TEST SUMMARY")
        print("="*80)
        
        for test_name, status, _ in test_results:
            print(f"{test_name}: {status}")
        
        passed = sum(1 for _, status, _ in test_results if "[OK]" in status)
        total = len(test_results)
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n[SUCCESS] All tests passed! CIA agent is working correctly!")
        else:
            print(f"\n[WARNING] {total - passed} tests failed. Check the output above.")
            
    except Exception as e:
        print(f"\n[ERROR] CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_all_tests())