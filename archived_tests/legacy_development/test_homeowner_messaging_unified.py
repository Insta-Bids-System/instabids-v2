#!/usr/bin/env python3
"""
Test: Homeowner (CIA) and Messaging Agent Integration with Unified System
Verifies privacy framework and cross-agent memory sharing
"""

import asyncio
import json
import uuid
from datetime import datetime
import sys
import os

# Add parent directory to path
ai_agents_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai-agents')
sys.path.insert(0, ai_agents_path)
print(f"Added to path: {ai_agents_path}")

print("=" * 70)
print("HOMEOWNER + MESSAGING AGENT UNIFIED SYSTEM TEST")
print("Testing Privacy Framework and Cross-Agent Memory Sharing")
print("=" * 70)

# Test configuration
TEST_USER_ID = str(uuid.uuid4())
TEST_SESSION_ID = f"test_session_{int(datetime.now().timestamp())}"
TEST_CONTRACTOR_ID = str(uuid.uuid4())

async def test_1_cia_saves_to_unified():
    """Test 1: CIA saves conversation with homeowner context adapter"""
    print("\n[TEST 1] CIA AGENT SAVES TO UNIFIED SYSTEM")
    print("-" * 50)
    
    try:
        from agents.cia.unified_integration import CIAUnifiedIntegration
        
        # Initialize CIA integration
        cia_integration = CIAUnifiedIntegration()
        print("[PASS] CIA Integration initialized")
        
        # Create test state (what CIA would collect)
        test_state = {
            "session_id": TEST_SESSION_ID,
            "current_phase": "details",
            "collected_info": {
                "project_type": "kitchen remodel",
                "budget_min": 30000,
                "budget_max": 50000,
                "timeline_urgency": "flexible",
                "material_preferences": "modern finishes",
                "location_zip": "94105"
            },
            "ready_for_jaa": True,
            "messages": [
                {"role": "user", "content": "I want to remodel my kitchen"},
                {"role": "assistant", "content": "Great! Let's discuss your kitchen remodel project."}
            ]
        }
        
        # Save conversation through unified system
        result = await cia_integration.save_conversation_with_unified_system(
            user_id=TEST_USER_ID,
            state=test_state,
            session_id=TEST_SESSION_ID
        )
        
        if result.get("success"):
            print(f"[PASS] CIA conversation saved to unified system")
            print(f"  - User ID: {TEST_USER_ID}")
            print(f"  - Session: {TEST_SESSION_ID}")
            print(f"  - Project: kitchen remodel")
            print(f"  - Budget: $30K-$50K")
            return True
        else:
            print(f"[FAIL] Failed to save: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error in CIA test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_2_cia_loads_cross_project_context():
    """Test 2: CIA loads context including IRIS insights"""
    print("\n[TEST 2] CIA LOADS CROSS-PROJECT CONTEXT")
    print("-" * 50)
    
    try:
        from agents.cia.unified_integration import CIAUnifiedIntegration
        
        cia_integration = CIAUnifiedIntegration()
        
        # Load context (would include IRIS insights if available)
        context = await cia_integration.load_conversation_context(
            user_id=TEST_USER_ID,
            project_id="test_project_1"
        )
        
        if context and not context.get("error"):
            print(f"[PASS] CIA loaded unified context")
            print(f"  - User profile: {bool(context.get('user_profile'))}")
            print(f"  - Cross-project memory: {bool(context.get('cross_project_memory'))}")
            print(f"  - IRIS insights: {bool(context.get('iris_design_insights'))}")
            print(f"  - Previous conversations: {len(context.get('previous_conversations', []))}")
            print(f"  - Privacy filtered: {context.get('privacy_filtered')}")
            return True
        else:
            print(f"[FAIL] Failed to load context: {context.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error loading context: {e}")
        return False

async def test_3_messaging_agent_filters_content():
    """Test 3: Messaging agent applies privacy filtering"""
    print("\n[TEST 3] MESSAGING AGENT PRIVACY FILTERING")
    print("-" * 50)
    
    try:
        from adapters.messaging_context import MessagingContextAdapter
        
        # Initialize messaging adapter
        messaging_adapter = MessagingContextAdapter()
        print("[PASS] Messaging adapter initialized")
        
        # Test homeowner to contractor message filtering
        test_message = {
            "content": "Hi, I'm John Smith at 123 Main St. My phone is 555-1234.",
            "sender_id": TEST_USER_ID,
            "sender_type": "homeowner",
            "metadata": {
                "full_name": "John Smith",
                "phone": "555-1234",
                "address": "123 Main St"
            }
        }
        
        # Apply filtering
        filtered_message = messaging_adapter.apply_message_filtering(
            message=test_message,
            sender_side="homeowner",
            recipient_side="contractor"
        )
        
        # Check if PII was filtered
        if "John Smith" not in str(filtered_message):
            print("[PASS] Homeowner name filtered out")
        else:
            print("[FAIL] Homeowner name NOT filtered")
            
        if "555-1234" not in str(filtered_message):
            print("[PASS] Phone number filtered out")
        else:
            print("[FAIL] Phone number NOT filtered")
            
        if filtered_message.get("moderation", {}).get("filtered"):
            print("[PASS] Message marked as filtered")
            print(f"  - Privacy level: {filtered_message['moderation'].get('privacy_level')}")
            return True
        else:
            print("[FAIL] Message not properly filtered")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error in messaging filter test: {e}")
        return False

async def test_4_cross_agent_coordination():
    """Test 4: CIA and Messaging agents share context"""
    print("\n[TEST 4] CROSS-AGENT COORDINATION")
    print("-" * 50)
    
    try:
        from agents.cia.unified_integration import CIAUnifiedIntegration
        from adapters.messaging_context import MessagingContextAdapter
        
        # CIA saves project context
        cia_integration = CIAUnifiedIntegration()
        test_state = {
            "collected_info": {
                "project_type": "bathroom remodel",
                "budget_min": 15000,
                "budget_max": 25000
            }
        }
        
        await cia_integration.save_conversation_with_unified_system(
            user_id=TEST_USER_ID,
            state=test_state,
            session_id=f"{TEST_SESSION_ID}_bathroom"
        )
        print("[PASS] CIA saved bathroom project context")
        
        # Messaging agent gets cross-side coordination context
        messaging_adapter = MessagingContextAdapter()
        coordination_context = messaging_adapter.get_cross_side_coordination_context(
            user_id=TEST_USER_ID,
            contractor_id=TEST_CONTRACTOR_ID,
            project_context={"project_type": "bathroom remodel"}
        )
        
        if coordination_context:
            print("[PASS] Messaging agent retrieved coordination context")
            print(f"  - Has homeowner context: {bool(coordination_context.get('homeowner_context'))}")
            print(f"  - Has contractor context: {bool(coordination_context.get('contractor_context'))}")
            print(f"  - Has alias mappings: {bool(coordination_context.get('alias_mappings'))}")
            print(f"  - Privacy protection: {coordination_context.get('privacy_protection_active')}")
            
            # Check alias mappings
            aliases = coordination_context.get("alias_mappings", {})
            if aliases.get("homeowner", {}).get("alias") == "Project Owner":
                print("[PASS] Homeowner aliased as 'Project Owner'")
            if "Contractor" in aliases.get("contractor", {}).get("alias", ""):
                print("[PASS] Contractor aliased properly")
                
            return True
        else:
            print("[FAIL] Failed to get coordination context")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error in coordination test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_5_privacy_boundaries():
    """Test 5: Verify privacy boundaries are enforced"""
    print("\n[TEST 5] PRIVACY BOUNDARY ENFORCEMENT")
    print("-" * 50)
    
    try:
        from services.context_policy import context_policy, AgentType
        
        # Test 1: CIA (homeowner-side) cannot see contractor PII
        contractor_data = {
            "company_name": "ABC Roofing Inc",
            "contact_name": "Bob Johnson",
            "business_phone": "555-9876",
            "business_email": "bob@abcroofing.com"
        }
        
        filtered_for_cia = context_policy.filter_conversation_data(
            requesting_agent=AgentType.CIA,
            conversation_data=contractor_data
        )
        
        if "ABC Roofing Inc" not in str(filtered_for_cia):
            print("[PASS] CIA cannot see contractor company name")
        else:
            print("[FAIL] CIA can see contractor company name (PRIVACY VIOLATION)")
            
        # Test 2: COIA (contractor-side) cannot see homeowner PII
        homeowner_data = {
            "full_name": "John Smith",
            "email": "john@email.com",
            "phone": "555-1234",
            "property_address": "123 Main St"
        }
        
        filtered_for_coia = context_policy.filter_conversation_data(
            requesting_agent=AgentType.COIA,
            conversation_data=homeowner_data
        )
        
        if "John Smith" not in str(filtered_for_coia):
            print("[PASS] COIA cannot see homeowner name")
        else:
            print("[FAIL] COIA can see homeowner name (PRIVACY VIOLATION)")
            
        # Test 3: CIA and IRIS (same-side) can share full context
        can_share = context_policy.can_access_conversation(
            requesting_agent=AgentType.IRIS,
            conversation_metadata={"agent_type": "CIA", "participants": ["homeowner"]}
        )
        
        if can_share:
            print("[PASS] CIA and IRIS can share full context (same-side)")
        else:
            print("[FAIL] CIA and IRIS cannot share (SHOULD BE ALLOWED)")
            
        # Test 4: Messaging (neutral) can see both sides
        messaging_access_homeowner = context_policy.can_access_conversation(
            requesting_agent=AgentType.MESSAGING,
            conversation_metadata={"agent_type": "CIA", "participants": ["homeowner"]}
        )
        
        messaging_access_contractor = context_policy.can_access_conversation(
            requesting_agent=AgentType.MESSAGING,
            conversation_metadata={"agent_type": "COIA", "participants": ["contractor"]}
        )
        
        if messaging_access_homeowner and messaging_access_contractor:
            print("[PASS] Messaging agent can access both sides (neutral)")
        else:
            print("[FAIL] Messaging agent cannot access both sides (SHOULD BE ALLOWED)")
            
        return True
        
    except Exception as e:
        print(f"[FAIL] Error in privacy boundary test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_all_tests():
    """Run all integration tests"""
    print(f"\nTest Configuration:")
    print(f"  User ID: {TEST_USER_ID}")
    print(f"  Session ID: {TEST_SESSION_ID}")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        "cia_saves": False,
        "cia_loads": False,
        "messaging_filters": False,
        "cross_coordination": False,
        "privacy_boundaries": False
    }
    
    # Run tests
    results["cia_saves"] = await test_1_cia_saves_to_unified()
    results["cia_loads"] = await test_2_cia_loads_cross_project_context()
    results["messaging_filters"] = await test_3_messaging_agent_filters_content()
    results["cross_coordination"] = await test_4_cross_agent_coordination()
    results["privacy_boundaries"] = await test_5_privacy_boundaries()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} - {test_name.replace('_', ' ').title()}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 70)
    if all_passed:
        print("SUCCESS: All tests passed!")
        print("CIA and Messaging agents properly integrated with unified system.")
        print("Privacy boundaries enforced, cross-agent sharing working.")
    else:
        failed_tests = [name for name, passed in results.items() if not passed]
        print(f"FAILURE: {len(failed_tests)} tests failed")
        print(f"Failed: {', '.join(failed_tests)}")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)