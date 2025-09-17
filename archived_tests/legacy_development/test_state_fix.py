#!/usr/bin/env python3
"""
Test the state persistence fix
"""

import requests
import json
import uuid

def test_state_persistence_fix():
    session_id = f"test-fix-{uuid.uuid4().hex[:8]}"
    contractor_lead_id = f"landing-{uuid.uuid4().hex[:12]}"
    
    print("TESTING STATE PERSISTENCE FIX")
    print("=" * 50)
    print(f"Session: {session_id}")
    print(f"Lead ID: {contractor_lead_id}")
    print()
    
    # Stage 1: Company Introduction
    print("STAGE 1: Company Introduction")
    print("-" * 30)
    
    request1 = {
        "message": "Hi, I'm from TurfGrass Artificial Solutions. We install artificial turf in Phoenix.",
        "session_id": session_id,
        "contractor_lead_id": contractor_lead_id
    }
    
    try:
        response1 = requests.post(
            "http://localhost:8008/api/coia/landing",
            json=request1,
            timeout=60
        )
        
        if response1.status_code == 200:
            data1 = response1.json()
            state1 = data1.get('state', {})
            
            print(f"Status: SUCCESS")
            print(f"Company extracted: '{state1.get('company_name', 'NOT FOUND')}'")
            print(f"Research completed: {state1.get('research_completed', False)}")
            print()
            
            # Stage 2: Follow-up message
            print("STAGE 2: Follow-up message (STATE PERSISTENCE TEST)")
            print("-" * 30)
            
            request2 = {
                "message": "Yes, please show me projects I can bid on!",
                "session_id": session_id,
                "contractor_lead_id": contractor_lead_id
            }
            
            response2 = requests.post(
                "http://localhost:8008/api/coia/landing",
                json=request2,
                timeout=60
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                state2 = data2.get('state', {})
                
                print(f"Status: SUCCESS")
                print(f"Company preserved: '{state2.get('company_name', 'LOST!')}'")
                print(f"Research still completed: {state2.get('research_completed', False)}")
                print(f"Current mode: {state2.get('current_mode', 'UNKNOWN')}")
                
                # Check if state was preserved
                company1 = state1.get('company_name', '')
                company2 = state2.get('company_name', '')
                
                print("\n" + "=" * 50)
                print("STATE PERSISTENCE TEST RESULTS")
                print("=" * 50)
                
                if company1 and company2 and company1 == company2:
                    print("SUCCESS: Company name preserved between messages")
                    print(f"  Stage 1: '{company1}'")
                    print(f"  Stage 2: '{company2}'")
                    
                    if state1.get('research_completed') and state2.get('research_completed'):
                        print("SUCCESS: Research state preserved")
                    else:
                        print("PARTIAL: Research state lost")
                        
                    print("\nFULL STATE PERSISTENCE: WORKING!")
                    return True
                    
                elif company1 and not company2:
                    print("FAILURE: Company name lost in Stage 2")
                    print(f"  Stage 1: '{company1}'")
                    print(f"  Stage 2: '{company2}' (LOST)")
                    return False
                    
                else:
                    print("FAILURE: Company name not extracted in Stage 1")
                    print(f"  Stage 1: '{company1}'")
                    print(f"  Stage 2: '{company2}'")
                    return False
                    
            else:
                print(f"FAILURE: Stage 2 failed ({response2.status_code})")
                return False
        else:
            print(f"FAILURE: Stage 1 failed ({response1.status_code})")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_state_persistence_fix()
    exit(0 if success else 1)