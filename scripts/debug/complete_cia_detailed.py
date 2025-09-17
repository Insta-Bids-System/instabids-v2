#!/usr/bin/env python3
"""
Provide all remaining information needed by CIA to complete the conversation
"""

import requests
import json
from datetime import datetime

def complete_cia_with_all_details():
    """Provide all missing information at once"""
    
    base_url = "http://localhost:8003"
    session_id = "test_session_1753815084"
    
    # Provide all missing information in one comprehensive message
    complete_message = """
    Here are all the remaining details:

    PROJECT TYPE: Mold Remediation
    
    PROJECT DESCRIPTION: Emergency black mold remediation in child's bedroom including pre-testing, containment setup, complete mold removal, sanitization, air quality verification, and post-remediation testing. Child safety protocols required.
    
    TIMELINE START: Tomorrow (immediate start needed due to child health concern)
    
    BUDGET: Minimum $3,000, Maximum $8,000 (flexible for child safety)
    
    ADDRESS: 1234 Pine Street, Seattle, WA 98101
    
    PROPERTY TYPE: Single-family detached home, 2-story, built 2020, 2,400 sq ft
    
    This is complete information - please proceed with generating the bid card.
    """
    
    print("PROVIDING ALL MISSING CIA INFORMATION")
    print("=" * 50)
    print(f"Session: {session_id}")
    print(f"Message length: {len(complete_message)} characters")
    print()
    
    try:
        cia_payload = {
            "message": complete_message,
            "session_id": session_id,
            "user_id": "test_user_123"
        }
        
        print("[API CALL] Sending complete information to CIA...")
        response = requests.post(f"{base_url}/api/cia/chat", json=cia_payload)
        cia_result = response.json()
        
        print(f"[RESPONSE] Status: {response.status_code}")
        print(f"  Current Phase: {cia_result.get('current_phase', 'unknown')}")
        print(f"  Ready for JAA: {cia_result.get('ready_for_jaa', False)}")
        print(f"  Missing Fields: {cia_result.get('missing_fields', [])}")
        print(f"  Response: {cia_result.get('response', '')[:200]}...")
        print()
        
        if cia_result.get('ready_for_jaa', False):
            print("[SUCCESS] CIA conversation is now complete!")
            return session_id
        else:
            print(f"[STILL MISSING] {cia_result.get('missing_fields', [])}")
            
            # Try one more time with explicit field values
            final_message = """
            Let me be explicit about each field:
            - project_type: "Mold Remediation"
            - project_description: "Emergency black mold remediation in child's bedroom"
            - timeline_start: "2025-07-30" (tomorrow)
            - budget_min: 3000
            - budget_max: 8000
            - address: "1234 Pine Street, Seattle, WA 98101"
            - property_type: "Single-family home"
            
            Please confirm this conversation is ready for JAA processing.
            """
            
            print("[RETRY] Sending explicit field values...")
            cia_payload = {
                "message": final_message,
                "session_id": session_id,
                "user_id": "test_user_123"
            }
            
            response = requests.post(f"{base_url}/api/cia/chat", json=cia_payload)
            cia_result = response.json()
            
            print(f"  Final Ready for JAA: {cia_result.get('ready_for_jaa', False)}")
            print(f"  Final Missing Fields: {cia_result.get('missing_fields', [])}")
            
            if cia_result.get('ready_for_jaa', False):
                print("[SUCCESS] CIA conversation completed on retry!")
                return session_id
            else:
                print("[FAILED] Still not ready after providing all information")
                return None
        
    except Exception as e:
        print(f"[ERROR] Failed to complete CIA conversation: {e}")
        return None

def test_complete_flow(session_id):
    """Test the complete flow once CIA is ready"""
    
    if not session_id:
        print("[SKIP] No valid session ID")
        return False
    
    base_url = "http://localhost:8003"
    
    print(f"[JAA TEST] Processing session {session_id}")
    try:
        response = requests.post(f"{base_url}/api/jaa/process/{session_id}")
        
        if response.status_code == 200:
            jaa_result = response.json()
            print(f"[JAA SUCCESS] Bid card created: {jaa_result.get('bid_card_number', 'unknown')}")
            
            bid_card_id = jaa_result.get('database_id')
            
            if bid_card_id:
                print(f"[CDA TEST] Discovering contractors for {bid_card_id}")
                response = requests.post(f"{base_url}/api/cda/discover/{bid_card_id}")
                
                if response.status_code == 200:
                    cda_result = response.json()
                    print(f"[CDA SUCCESS] Found {cda_result.get('contractors_found', 0)} contractors")
                    
                    print()
                    print("COMPLETE FLOW TEST SUCCESSFUL!")
                    print("- CIA: Conversation ready")
                    print("- JAA: Bid card generated")
                    print("- CDA: Contractors discovered")
                    print("- All using real Claude Opus 4 API calls")
                    return True
                else:
                    print(f"[CDA FAILED] {response.json().get('detail', 'Unknown error')}")
            else:
                print("[ERROR] No bid card ID returned from JAA")
        else:
            print(f"[JAA FAILED] {response.json().get('detail', 'Unknown error')}")
    
    except Exception as e:
        print(f"[FLOW ERROR] {e}")
    
    return False

def main():
    """Main execution"""
    print(f"Starting complete CIA flow test at {datetime.now()}")
    print()
    
    # Step 1: Complete CIA conversation
    session_id = complete_cia_with_all_details()
    
    # Step 2: Test complete flow
    success = test_complete_flow(session_id)
    
    if success:
        print()
        print("SYSTEM VALIDATION COMPLETE")
        print("All agents working with real Claude Opus 4!")
    else:
        print()
        print("Flow incomplete - debugging needed")

if __name__ == "__main__":
    main()