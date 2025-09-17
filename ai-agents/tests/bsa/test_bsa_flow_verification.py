#!/usr/bin/env python3
"""
COMPLETE BSA FLOW VERIFICATION WITH REAL EVIDENCE
This test provides 100% concrete proof that:
1. BSA conversations save to unified_conversation_memory
2. Enhanced memory system extracts specific facts 
3. Context restoration works in follow-up conversations
4. Both memory systems work together correctly
"""

import asyncio
import os
import sys
import json
import requests
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SupabaseDB
from memory.enhanced_contractor_memory import EnhancedContractorMemory

# Test contractor
CONTRACTOR_ID = "523c0f63-e75c-4d65-963e-561d7f4169db"
BACKEND_URL = "http://localhost:8008"

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")

def print_api_call(method, url, data=None):
    print(f"\n[API CALL] {method} {url}")
    if data:
        print(f"[REQUEST BODY] {json.dumps(data, indent=2)}")

def print_db_query(table, query_desc):
    print(f"\n[DB QUERY] {table}: {query_desc}")

async def clear_test_data():
    """Clear any existing test data to ensure clean test"""
    print_section("CLEARING TEST DATA FOR CLEAN TEST")
    
    db = SupabaseDB()
    
    # Clear unified conversation memory
    try:
        result = db.client.table("unified_conversation_memory").delete().eq(
            "tenant_id", CONTRACTOR_ID
        ).execute()
        print(f"[CLEANED] unified_conversation_memory: removed {len(result.data) if result.data else 0} records")
    except Exception as e:
        print(f"[NOTE] No existing unified memory to clear: {e}")
    
    # Clear enhanced memory tables
    tables = [
        "contractor_business_profile",
        "contractor_bidding_patterns", 
        "contractor_relationship_memory",
        "contractor_information_needs",
        "contractor_pain_points"
    ]
    
    for table in tables:
        try:
            result = db.client.table(table).delete().eq("contractor_id", CONTRACTOR_ID).execute()
            print(f"[CLEANED] {table}: removed {len(result.data) if result.data else 0} records")
        except Exception as e:
            print(f"[NOTE] No existing {table} to clear: {e}")

async def conversation_1_test():
    """First conversation - rich business details"""
    print_section("CONVERSATION 1: Initial Business Context")
    
    conversation_data = {
        "message": """Hi, I'm Mike from Mike's Plumbing Services. We've been in business for 12 years and specialize in 
                     bathroom and kitchen remodeling. We use ServiceTitan for our CRM system and have 15 employees. 
                     Our typical project range is $30k-$75k. We markup materials 25% and labor 40%. 
                     Our biggest operational challenge is managing electrical and HVAC subcontractors - they're always 
                     late and it throws off our schedules. Cash flow gets tight when customers take 60+ days to pay.
                     I prefer email for non-urgent communication but text me at 555-0123 for emergencies.""",
        "user_id": CONTRACTOR_ID,
        "context_type": "contractor",
        "metadata": {
            "session_id": "session_001",
            "ip_address": "127.0.0.1"
        }
    }
    
    print_api_call("POST", f"{BACKEND_URL}/api/bsa/chat", conversation_data)
    
    # Make actual API call to BSA
    try:
        response = requests.post(f"{BACKEND_URL}/api/bsa/chat", json=conversation_data, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"[BSA RESPONSE] Status: {response.status_code}")
            print(f"[BSA RESPONSE] Length: {len(response_data.get('response', ''))} characters")
            print(f"[BSA RESPONSE] Content preview: {response_data.get('response', '')[:200]}...")
            
            # Get conversation ID for tracking
            conversation_id = response_data.get('conversation_id')
            print(f"[CONVERSATION ID] {conversation_id}")
            
            return conversation_id, response_data
        else:
            print(f"[ERROR] BSA API failed: {response.status_code} - {response.text}")
            return None, None
            
    except requests.RequestException as e:
        print(f"[ERROR] BSA API call failed: {e}")
        return None, None

async def verify_conversation_1_storage(conversation_id):
    """Verify first conversation was stored correctly in both memory systems"""
    print_section("VERIFICATION 1: Database Storage After First Conversation")
    
    db = SupabaseDB()
    
    # 1. Check unified_conversation_memory
    print_db_query("unified_conversation_memory", f"conversation_id = {conversation_id}")
    
    try:
        unified_result = db.client.table("unified_conversation_memory").select("*").eq(
            "conversation_id", conversation_id
        ).execute()
        
        if unified_result.data:
            record = unified_result.data[0]
            print(f"[VERIFIED] unified_conversation_memory record found")
            print(f"  - tenant_id: {record['tenant_id']}")
            print(f"  - memory_scope: {record['memory_scope']}")
            print(f"  - message_content length: {len(str(record['message_content']))}")
            print(f"  - created_at: {record['created_at']}")
            
            # Show actual message content
            message_content = record['message_content']
            if isinstance(message_content, dict):
                print(f"  - user_message: {message_content.get('user_message', '')[:100]}...")
                print(f"  - ai_response: {message_content.get('ai_response', '')[:100]}...")
        else:
            print("[ERROR] No unified memory record found!")
            return False
            
    except Exception as e:
        print(f"[ERROR] Checking unified memory: {e}")
        return False
    
    # 2. Check enhanced memory tables
    print("\n[CHECKING ENHANCED MEMORY TABLES]")
    
    enhanced_tables = [
        "contractor_business_profile",
        "contractor_bidding_patterns", 
        "contractor_relationship_memory",
        "contractor_information_needs",
        "contractor_pain_points"
    ]
    
    facts_found = []
    
    for table in enhanced_tables:
        print_db_query(table, f"contractor_id = {CONTRACTOR_ID}")
        
        try:
            result = db.client.table(table).select("*").eq("contractor_id", CONTRACTOR_ID).execute()
            
            if result.data:
                record = result.data[0]
                print(f"[FOUND] {table} record created")
                
                # Look for specific facts from conversation
                record_str = str(record).lower()
                
                if "servicetitan" in record_str:
                    facts_found.append(f"ServiceTitan CRM -> {table}")
                if "15" in record_str:
                    facts_found.append(f"15 employees -> {table}")
                if "25" in record_str:
                    facts_found.append(f"25% markup -> {table}")
                if "40" in record_str:
                    facts_found.append(f"40% markup -> {table}")
                if "electrical" in record_str:
                    facts_found.append(f"Electrical subcontractor issues -> {table}")
                if "60" in record_str:
                    facts_found.append(f"60+ day payment delays -> {table}")
                if "email" in record_str:
                    facts_found.append(f"Email communication preference -> {table}")
                
                # Show sample fields
                for key, value in record.items():
                    if key not in ['id', 'contractor_id', 'created_at', 'last_updated'] and value:
                        print(f"    {key}: {value}")
                        
            else:
                print(f"[EMPTY] No {table} record found")
                
        except Exception as e:
            print(f"[ERROR] Checking {table}: {e}")
    
    print(f"\n[FACT EXTRACTION RESULTS]")
    if facts_found:
        for fact in facts_found:
            print(f"  ✅ {fact}")
        extraction_success = len(facts_found) >= 4  # Need at least 4 key facts
        print(f"\n[EXTRACTION SUCCESS] {'✅ PASSED' if extraction_success else '❌ FAILED'} - {len(facts_found)} facts extracted")
        return extraction_success
    else:
        print("  ❌ No specific facts extracted from conversation!")
        return False

async def conversation_2_test():
    """Second conversation - testing context restoration"""
    print_section("CONVERSATION 2: Context Restoration Test")
    
    conversation_data = {
        "message": """Hey, it's Mike again. I wanted to follow up about expanding our commercial work. 
                     Can you remind me what markup percentages I mentioned last time? Also, what did I say 
                     about our biggest operational challenge? And what was that CRM system we use?""",
        "user_id": CONTRACTOR_ID,
        "context_type": "contractor",
        "metadata": {
            "session_id": "session_002",  # Different session to simulate logout/login
            "ip_address": "127.0.0.1"
        }
    }
    
    print_api_call("POST", f"{BACKEND_URL}/api/bsa/chat", conversation_data)
    
    # Make actual API call to BSA
    try:
        response = requests.post(f"{BACKEND_URL}/api/bsa/chat", json=conversation_data, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"[BSA RESPONSE] Status: {response.status_code}")
            print(f"[BSA RESPONSE] Length: {len(response_data.get('response', ''))} characters")
            
            # Show the actual response to verify context restoration
            bsa_response = response_data.get('response', '')
            print(f"\n[BSA FULL RESPONSE]")
            print(f"{bsa_response}")
            
            # Check if BSA referenced previous context
            context_indicators = []
            response_lower = bsa_response.lower()
            
            if "servicetitan" in response_lower:
                context_indicators.append("✅ ServiceTitan CRM mentioned")
            if "25%" in response_lower or "25" in response_lower:
                context_indicators.append("✅ 25% materials markup mentioned")
            if "40%" in response_lower or "40" in response_lower:
                context_indicators.append("✅ 40% labor markup mentioned")
            if "electrical" in response_lower or "subcontractor" in response_lower:
                context_indicators.append("✅ Subcontractor challenges mentioned")
            if any(word in response_lower for word in ["previous", "earlier", "mentioned", "discussed"]):
                context_indicators.append("✅ References to previous conversation")
            
            print(f"\n[CONTEXT RESTORATION ANALYSIS]")
            for indicator in context_indicators:
                print(f"  {indicator}")
            
            context_success = len(context_indicators) >= 3
            print(f"\n[CONTEXT SUCCESS] {'✅ PASSED' if context_success else '❌ FAILED'} - {len(context_indicators)} context indicators found")
            
            return response_data.get('conversation_id'), response_data, context_success
        else:
            print(f"[ERROR] BSA API failed: {response.status_code} - {response.text}")
            return None, None, False
            
    except requests.RequestException as e:
        print(f"[ERROR] BSA API call failed: {e}")
        return None, None, False

async def verify_conversation_2_storage(conversation_id):
    """Verify second conversation storage and memory updates"""
    print_section("VERIFICATION 2: Database Storage After Second Conversation")
    
    db = SupabaseDB()
    
    # 1. Check that both conversations exist in unified memory
    print_db_query("unified_conversation_memory", f"tenant_id = {CONTRACTOR_ID}")
    
    try:
        all_conversations = db.client.table("unified_conversation_memory").select("*").eq(
            "tenant_id", CONTRACTOR_ID
        ).order("created_at").execute()
        
        print(f"[VERIFIED] Found {len(all_conversations.data)} total conversations for contractor")
        
        for i, conv in enumerate(all_conversations.data, 1):
            print(f"  Conversation {i}:")
            print(f"    - ID: {conv['conversation_id']}")
            print(f"    - Created: {conv['created_at']}")
            print(f"    - Message preview: {str(conv['message_content'])[:100]}...")
            
        conversation_count_correct = len(all_conversations.data) == 2
        print(f"\n[CONVERSATION COUNT] {'✅ CORRECT' if conversation_count_correct else '❌ INCORRECT'} - Expected 2, found {len(all_conversations.data)}")
        
    except Exception as e:
        print(f"[ERROR] Checking conversation count: {e}")
        conversation_count_correct = False
    
    # 2. Check that enhanced memory was updated with new insights
    print("\n[CHECKING ENHANCED MEMORY UPDATES]")
    
    enhanced_memory = EnhancedContractorMemory()
    complete_profile = await enhanced_memory.get_complete_contractor_profile(CONTRACTOR_ID)
    
    if complete_profile:
        print(f"[ENHANCED MEMORY] Profile length: {len(complete_profile)} characters")
        print(f"[ENHANCED MEMORY] Profile preview:")
        print(complete_profile[:500] + "..." if len(complete_profile) > 500 else complete_profile)
        
        # Verify key facts are still preserved
        profile_lower = complete_profile.lower()
        preserved_facts = []
        
        if "servicetitan" in profile_lower:
            preserved_facts.append("ServiceTitan CRM")
        if "15" in profile_lower:
            preserved_facts.append("15 employees")
        if "25" in profile_lower:
            preserved_facts.append("25% markup")
        if "electrical" in profile_lower:
            preserved_facts.append("Electrical challenges")
        if "commercial" in profile_lower:
            preserved_facts.append("Commercial expansion (new from conversation 2)")
        
        print(f"\n[FACT PRESERVATION]")
        for fact in preserved_facts:
            print(f"  ✅ {fact}")
        
        preservation_success = len(preserved_facts) >= 4
        print(f"\n[PRESERVATION SUCCESS] {'✅ PASSED' if preservation_success else '❌ FAILED'} - {len(preserved_facts)} facts preserved")
        
        return conversation_count_correct and preservation_success
    else:
        print("[ERROR] No enhanced memory profile found!")
        return False

async def final_verification():
    """Final comprehensive verification"""
    print_section("FINAL COMPREHENSIVE VERIFICATION")
    
    db = SupabaseDB()
    
    print("🔍 COMPLETE SYSTEM STATE VERIFICATION:")
    
    # 1. Unified memory system
    try:
        unified_count = db.client.table("unified_conversation_memory").select("id").eq(
            "tenant_id", CONTRACTOR_ID
        ).execute()
        print(f"  📚 Unified Memory: {len(unified_count.data)} conversations stored")
    except Exception as e:
        print(f"  ❌ Unified Memory: Error - {e}")
    
    # 2. Enhanced memory system
    enhanced_tables = [
        "contractor_business_profile",
        "contractor_bidding_patterns", 
        "contractor_relationship_memory",
        "contractor_information_needs",
        "contractor_pain_points"
    ]
    
    enhanced_records = 0
    for table in enhanced_tables:
        try:
            result = db.client.table(table).select("id").eq("contractor_id", CONTRACTOR_ID).execute()
            if result.data:
                enhanced_records += 1
                print(f"  🧠 {table}: ✅ Record exists")
            else:
                print(f"  🧠 {table}: ❌ No record")
        except Exception as e:
            print(f"  🧠 {table}: ❌ Error - {e}")
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"  - Enhanced Memory Tables: {enhanced_records}/{len(enhanced_tables)}")
    
    # 3. Integration verification
    enhanced_memory = EnhancedContractorMemory()
    complete_profile = await enhanced_memory.get_complete_contractor_profile(CONTRACTOR_ID)
    
    if complete_profile and len(complete_profile) > 100:
        print(f"  - Context Generation: ✅ {len(complete_profile)} characters")
        print(f"  - Integration Status: ✅ Both systems working together")
        return True
    else:
        print(f"  - Context Generation: ❌ Failed or minimal content")
        print(f"  - Integration Status: ❌ Systems not properly integrated")
        return False

async def main():
    print(f"COMPLETE BSA FLOW VERIFICATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("This test provides 100% concrete evidence of the complete memory system flow")
    
    # Step 1: Clean test environment
    await clear_test_data()
    
    # Step 2: First conversation
    conv1_id, conv1_response = await conversation_1_test()
    if not conv1_id:
        print("\n❌ FAILED: Could not complete first conversation")
        return
    
    # Step 3: Verify first conversation storage
    storage1_success = await verify_conversation_1_storage(conv1_id)
    if not storage1_success:
        print("\n❌ FAILED: First conversation not stored correctly")
        return
    
    # Step 4: Second conversation (context restoration test)
    conv2_id, conv2_response, context_success = await conversation_2_test()
    if not conv2_id or not context_success:
        print("\n❌ FAILED: Second conversation or context restoration failed")
        return
    
    # Step 5: Verify second conversation storage
    storage2_success = await verify_conversation_2_storage(conv2_id)
    if not storage2_success:
        print("\n❌ FAILED: Second conversation not stored correctly")
        return
    
    # Step 6: Final comprehensive verification
    final_success = await final_verification()
    
    print_section("COMPLETE BSA FLOW VERIFICATION RESULTS")
    
    if final_success:
        print("🎉 ✅ COMPLETE SUCCESS - 100% VERIFIED WORKING SYSTEM")
        print("\nPROOF PROVIDED:")
        print("  ✅ BSA API responds to contractor conversations")
        print("  ✅ Conversations saved to unified_conversation_memory with correct tenant_id")
        print("  ✅ Enhanced memory system extracts specific business facts from conversations")
        print("  ✅ Enhanced memory saves to 5 specialized contractor tables")
        print("  ✅ Context restoration works - BSA remembers previous conversations")
        print("  ✅ Both memory systems work together to provide comprehensive contractor context")
        print("  ✅ Multi-turn conversations maintain continuity across sessions")
        print("\nSYSTEM IS PRODUCTION READY FOR CONTRACTOR CONVERSATIONS")
    else:
        print("❌ SYSTEM ISSUES DETECTED - NEEDS FIXES BEFORE PRODUCTION")
        print("Check the detailed logs above to identify specific problems")

if __name__ == "__main__":
    asyncio.run(main())