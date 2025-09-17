#!/usr/bin/env python3
"""Test COIA conversation progression through specific stages."""

import requests
import json
import uuid
import time
from datetime import datetime

def safe_print(text):
    """Print with ASCII encoding fallback."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', errors='replace').decode('ascii'))

def test_conversation_progression():
    """Test that COIA conversation progresses through different stages."""
    
    # Use a fresh company and IDs
    company_name = "Elite Roofing Services"
    session_id = str(uuid.uuid4())
    contractor_lead_id = str(uuid.uuid4())
    
    safe_print("="*80)
    safe_print("COIA CONVERSATION PROGRESSION TEST")
    safe_print("="*80)
    safe_print(f"Company: {company_name}")
    safe_print(f"Session ID: {session_id}")
    safe_print(f"Contractor Lead ID: {contractor_lead_id}")
    safe_print("="*80)
    
    # Stage 1: Introduce business name
    safe_print("\n" + "="*50)
    safe_print("STAGE 1: BUSINESS NAME INTRODUCTION")
    safe_print("="*50)
    
    stage1_request = {
        "message": f"Hi, I'm {company_name}",
        "session_id": session_id,
        "contractor_lead_id": contractor_lead_id
    }
    
    safe_print(f"Sending: {stage1_request['message']}")
    
    try:
        response1 = requests.post(
            "http://localhost:8008/api/coia/landing",
            json=stage1_request,
            timeout=60
        )
        
        if response1.status_code == 200:
            data1 = response1.json()
            safe_print(f"Status: SUCCESS")
            safe_print(f"Research completed: {data1.get('research_completed', False)}")
            safe_print(f"Company name: {data1.get('contractor_profile', {}).get('company_name')}")
            
            safe_print("\nResponse preview:")
            safe_print("-" * 40)
            safe_print(data1.get('response', '')[:400] + "...")
            safe_print("-" * 40)
            
            # Stage 2: Try explicit research confirmation (as mentioned in design doc)
            safe_print("\n" + "="*50)
            safe_print("STAGE 2: EXPLICIT RESEARCH CONFIRMATION")
            safe_print("="*50)
            
            time.sleep(2)
            
            stage2_request = {
                "message": "Yes, that's correct! Can you research more details about my business?",
                "session_id": session_id,
                "contractor_lead_id": contractor_lead_id
            }
            
            safe_print(f"Sending: {stage2_request['message']}")
            
            response2 = requests.post(
                "http://localhost:8008/api/coia/landing",
                json=stage2_request,
                timeout=60
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                safe_print(f"Status: SUCCESS")
                safe_print(f"Research completed: {data2.get('research_completed', False)}")
                
                safe_print("\nResponse preview:")
                safe_print("-" * 40)
                response2_text = data2.get('response', '')
                safe_print(response2_text[:400] + "...")
                safe_print("-" * 40)
                
                # Check if response changed from Stage 1
                response1_text = data1.get('response', '')
                if response1_text == response2_text:
                    safe_print("\n[WARNING] Same response as Stage 1 - conversation not progressing")
                else:
                    safe_print("\n[PASS] Response changed - conversation progressing")
                
                # Stage 3: Service information
                safe_print("\n" + "="*50)
                safe_print("STAGE 3: SERVICE INFORMATION")
                safe_print("="*50)
                
                time.sleep(2)
                
                stage3_request = {
                    "message": "We specialize in residential and commercial roofing - new installation, repairs, maintenance, and storm damage restoration. We serve a 25-mile radius.",
                    "session_id": session_id,
                    "contractor_lead_id": contractor_lead_id
                }
                
                safe_print(f"Sending: {stage3_request['message']}")
                
                response3 = requests.post(
                    "http://localhost:8008/api/coia/landing",
                    json=stage3_request,
                    timeout=60
                )
                
                if response3.status_code == 200:
                    data3 = response3.json()
                    safe_print(f"Status: SUCCESS")
                    
                    safe_print("\nResponse preview:")
                    safe_print("-" * 40)
                    response3_text = data3.get('response', '')
                    safe_print(response3_text[:400] + "...")
                    safe_print("-" * 40)
                    
                    # Check for progression
                    if response2_text == response3_text:
                        safe_print("\n[WARNING] Same response as Stage 2 - conversation stuck")
                    else:
                        safe_print("\n[PASS] Response changed - conversation progressing")
                    
                    # Stage 4: Account creation request (using specific phrase from code)
                    safe_print("\n" + "="*50)
                    safe_print("STAGE 4: ACCOUNT CREATION REQUEST")
                    safe_print("="*50)
                    
                    time.sleep(2)
                    
                    stage4_request = {
                        "message": "Yes, create my profile",
                        "session_id": session_id,
                        "contractor_lead_id": contractor_lead_id
                    }
                    
                    safe_print(f"Sending: {stage4_request['message']}")
                    
                    response4 = requests.post(
                        "http://localhost:8008/api/coia/landing",
                        json=stage4_request,
                        timeout=60
                    )
                    
                    if response4.status_code == 200:
                        data4 = response4.json()
                        safe_print(f"Status: SUCCESS")
                        safe_print(f"Contractor created: {data4.get('contractor_created', False)}")
                        safe_print(f"Account creation confirmed: {data4.get('account_creation_confirmed', False)}")
                        
                        safe_print("\nResponse preview:")
                        safe_print("-" * 40)
                        response4_text = data4.get('response', '')
                        safe_print(response4_text[:400] + "...")
                        safe_print("-" * 40)
                        
                        # Check for progression
                        if response3_text == response4_text:
                            safe_print("\n[FAIL] Same response as Stage 3 - account creation not triggered")
                        else:
                            safe_print("\n[PASS] Response changed - account creation flow triggered")
                        
                        # Final check
                        if data4.get('contractor_created'):
                            safe_print("\n*** COMPLETE SUCCESS: Contractor account created! ***")
                        else:
                            safe_print("\n[PARTIAL] Conversation progressed but account not created yet")
                    else:
                        safe_print(f"[FAIL] Stage 4 failed: {response4.status_code}")
                        safe_print(f"Error: {response4.text}")
                else:
                    safe_print(f"[FAIL] Stage 3 failed: {response3.status_code}")
            else:
                safe_print(f"[FAIL] Stage 2 failed: {response2.status_code}")
        else:
            safe_print(f"[FAIL] Stage 1 failed: {response1.status_code}")
            safe_print(f"Error: {response1.text}")
    
    except Exception as e:
        safe_print(f"[FAIL] Error: {e}")
    
    safe_print("\n" + "="*80)
    safe_print("TEST COMPLETE")
    safe_print("="*80)

if __name__ == "__main__":
    test_conversation_progression()