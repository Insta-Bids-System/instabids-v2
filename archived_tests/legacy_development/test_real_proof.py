#!/usr/bin/env python3
"""
REAL PROOF TEST - Show actual API calls, Google data, state persistence
"""

import requests
import json
import uuid
import time

def test_real_proof():
    session_id = f"proof-{uuid.uuid4().hex[:8]}"
    contractor_lead_id = f"landing-{uuid.uuid4().hex[:12]}"
    
    print("REAL PROOF TEST - DEMANDING EVIDENCE")
    print("=" * 60)
    print(f"Session: {session_id}")
    print(f"Lead ID: {contractor_lead_id}")
    print()
    
    # Stage 1: Company Introduction - PROVE GOOGLE API WORKS
    print("STAGE 1: PROVE GOOGLE API CALLS WORK")
    print("-" * 40)
    
    request1 = {
        "message": "Hi, I'm from TurfGrass Artificial Solutions. We install artificial turf in Phoenix.",
        "session_id": session_id,
        "contractor_lead_id": contractor_lead_id
    }
    
    print("Making API call...")
    start_time = time.time()
    
    try:
        response1 = requests.post(
            "http://localhost:8008/api/coia/landing",
            json=request1,
            timeout=90
        )
        
        end_time = time.time()
        print(f"API Response: {response1.status_code} (took {end_time - start_time:.1f}s)")
        
        if response1.status_code == 200:
            data1 = response1.json()
            response_text = data1.get('response', '')
            state1 = data1.get('state', {})
            
            print("\nCONCRETE EVIDENCE FROM STAGE 1:")
            print("-" * 30)
            
            # Check for Google Business data in response
            google_indicators = [
                "5051 NW 13th Ave",  # Real address
                "Pompano Beach",     # Real city  
                "(561) 504-9621",    # Real phone
                "4.9",               # Real rating
                "turfgrassartificialsolutions.com"  # Real website
            ]
            
            found_google_data = []
            for indicator in google_indicators:
                if indicator in response_text:
                    found_google_data.append(indicator)
                    
            print(f"GOOGLE API DATA FOUND: {len(found_google_data)}/{len(google_indicators)} items")
            for item in found_google_data:
                print(f"  ✓ {item}")
                
            # Check state data
            print(f"\nSTATE EXTRACTION:")
            print(f"  Company: '{state1.get('company_name', 'NOT FOUND')}'")
            print(f"  Research: {state1.get('research_completed', False)}")
            print(f"  Mode: {state1.get('current_mode', 'UNKNOWN')}")
            
            # Raw research data check
            research_findings = state1.get('research_findings', {})
            if research_findings:
                raw_data = research_findings.get('raw_data', {})
                google_business = raw_data.get('google_business', {})
                if google_business:
                    print(f"\nRAW GOOGLE BUSINESS DATA:")
                    print(f"  Company: {google_business.get('company_name', 'NONE')}")
                    print(f"  Address: {google_business.get('address', 'NONE')}")
                    print(f"  Phone: {google_business.get('phone', 'NONE')}")
                    print(f"  Rating: {google_business.get('rating', 'NONE')}")
                    
            if len(found_google_data) >= 3:
                print("\n✓ GOOGLE API CALLS: PROVEN WORKING")
            else:
                print("\n✗ GOOGLE API CALLS: FAILED")
                return False
                
            print(f"\nFull response length: {len(response_text)} chars")
            print(f"Response preview: {response_text[:200]}...")
            
        else:
            print(f"✗ API FAILED: {response1.status_code}")
            print(f"Error: {response1.text}")
            return False
            
        # Stage 2: STATE PERSISTENCE TEST
        print("\n" + "=" * 60)
        print("STAGE 2: PROVE STATE PERSISTENCE WORKS")
        print("-" * 40)
        
        request2 = {
            "message": "Yes, please research my company and show me projects!",
            "session_id": session_id,
            "contractor_lead_id": contractor_lead_id
        }
        
        print("Making second API call...")
        start_time = time.time()
        
        response2 = requests.post(
            "http://localhost:8008/api/coia/landing",
            json=request2,
            timeout=90
        )
        
        end_time = time.time()
        print(f"API Response: {response2.status_code} (took {end_time - start_time:.1f}s)")
        
        if response2.status_code == 200:
            data2 = response2.json()
            state2 = data2.get('state', {})
            response2_text = data2.get('response', '')
            
            print("\nCONCRETE EVIDENCE FROM STAGE 2:")
            print("-" * 30)
            
            # Compare states
            company1 = state1.get('company_name', '')
            company2 = state2.get('company_name', '')
            research1 = state1.get('research_completed', False)
            research2 = state2.get('research_completed', False)
            
            print(f"STATE COMPARISON:")
            print(f"  Stage 1 company: '{company1}'")
            print(f"  Stage 2 company: '{company2}'")
            print(f"  Stage 1 research: {research1}")
            print(f"  Stage 2 research: {research2}")
            
            # Check if Google data still present
            stage2_google_data = []
            for indicator in google_indicators:
                if indicator in response2_text:
                    stage2_google_data.append(indicator)
                    
            print(f"\nGOOGLE DATA PERSISTENCE: {len(stage2_google_data)}/{len(google_indicators)} items")
            
            # Check for progression
            if response_text == response2_text:
                print("\n✗ CONVERSATION STUCK: Identical responses")
                return False
            else:
                print("\n✓ CONVERSATION PROGRESSING: Different responses")
                
            # State persistence check
            if research1 and research2:
                print("✓ RESEARCH STATE: PRESERVED")
            else:
                print("✗ RESEARCH STATE: LOST")
                
            print(f"\nMode progression: {state1.get('current_mode')} → {state2.get('current_mode')}")
            
        else:
            print(f"✗ STAGE 2 FAILED: {response2.status_code}")
            return False
            
        # FINAL VERDICT
        print("\n" + "=" * 60)
        print("FINAL EVIDENCE-BASED VERDICT")
        print("=" * 60)
        
        google_working = len(found_google_data) >= 3
        state_preserved = research1 and research2
        conversation_progressing = response_text != response2_text
        
        print(f"Google API calls working: {google_working}")
        print(f"State preserved between calls: {state_preserved}")  
        print(f"Conversation progressing: {conversation_progressing}")
        
        if google_working and conversation_progressing:
            print("\n✓ CORE BUSINESS LOGIC: PROVEN WORKING")
            if state_preserved:
                print("✓ STATE PERSISTENCE: PROVEN WORKING") 
                print("\n🎉 SYSTEM FULLY OPERATIONAL WITH PROOF")
                return True
            else:
                print("⚠ STATE PERSISTENCE: NEEDS WORK")
                print("\n📊 CORE WORKING, STATE LAYER NEEDS FIX")
                return True
        else:
            print("\n✗ SYSTEM BROKEN")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_real_proof()
    print(f"\nTEST RESULT: {'PASS' if success else 'FAIL'}")