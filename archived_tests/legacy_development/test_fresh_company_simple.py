#!/usr/bin/env python3
"""Test COIA complete flow with a FRESH company name."""

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

def test_complete_flow():
    """Test the complete 6-stage COIA flow with a fresh company."""
    
    # Use a FRESH company name for clean testing
    company_name = "Premier Landscaping Solutions"
    session_id = str(uuid.uuid4())
    contractor_lead_id = str(uuid.uuid4())
    
    safe_print("="*80)
    safe_print("COIA COMPLETE FLOW TEST WITH FRESH DATA")
    safe_print("="*80)
    safe_print(f"Company: {company_name}")
    safe_print(f"Session ID: {session_id}")
    safe_print(f"Contractor Lead ID: {contractor_lead_id}")
    safe_print(f"Timestamp: {datetime.now().isoformat()}")
    safe_print("="*80)
    
    # Stage 1: Initial contact with business name
    safe_print("\n" + "="*50)
    safe_print("STAGE 1: INITIAL BUSINESS NAME")
    safe_print("="*50)
    
    stage1_request = {
        "message": f"I'm {company_name}",
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
            data = response1.json()
            safe_print(f"Status: SUCCESS")
            safe_print(f"Company extracted: {data.get('contractor_profile', {}).get('company_name')}")
            safe_print(f"Research completed: {data.get('research_completed', False)}")
            
            # Check if we got research findings
            research_findings = data.get('research_findings', {})
            if research_findings:
                safe_print(f"Google Places data found:")
                safe_print(f"  - Name: {research_findings.get('name')}")
                safe_print(f"  - Address: {research_findings.get('address')}")
                safe_print(f"  - Phone: {research_findings.get('phone')}")
                safe_print(f"  - Website: {research_findings.get('website')}")
            
            safe_print("\nAI Response:")
            safe_print("-" * 40)
            safe_print(data.get('response', '')[:800])
            safe_print("-" * 40)
            
            # Check for confirmation prompt
            response_text = data.get('response', '').lower()
            if "confirm" in response_text or "is this your business" in response_text or "your business" in response_text:
                safe_print("\n[PASS] Stage 1: Business confirmation prompt received")
                
                # Stage 2: Confirm business
                safe_print("\n" + "="*50)
                safe_print("STAGE 2: BUSINESS CONFIRMATION")
                safe_print("="*50)
                
                time.sleep(2)  # Brief pause between stages
                
                stage2_request = {
                    "message": "Yes, that's my business",
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
                    
                    safe_print("\nAI Response:")
                    safe_print("-" * 40)
                    safe_print(data2.get('response', '')[:800])
                    safe_print("-" * 40)
                    
                    # Check if we should continue to service expansion
                    response2_text = data2.get('response', '').lower()
                    if "service" in response2_text or "area" in response2_text or "tell me more" in response2_text:
                        safe_print("\n[PASS] Stage 2: Deep research triggered")
                        
                        # Stage 3: Service information
                        safe_print("\n" + "="*50)
                        safe_print("STAGE 3: SERVICE INFORMATION")
                        safe_print("="*50)
                        
                        time.sleep(2)
                        
                        stage3_request = {
                            "message": "We do full landscaping - design, installation, maintenance, hardscaping, irrigation",
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
                            
                            safe_print("\nAI Response:")
                            safe_print("-" * 40)
                            safe_print(data3.get('response', '')[:800])
                            safe_print("-" * 40)
                            
                            # Check for account creation prompt
                            response3_text = data3.get('response', '').lower()
                            if ("create" in response3_text and "profile" in response3_text) or "make you a profile" in response3_text:
                                safe_print("\n[PASS] Stage 3: Account creation prompt received")
                                
                                # Stage 4: Confirm account creation
                                safe_print("\n" + "="*50)
                                safe_print("STAGE 4: ACCOUNT CREATION CONFIRMATION")
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
                                    safe_print(f"Contractor ID: {data4.get('contractor_id')}")
                                    
                                    safe_print("\nAI Response:")
                                    safe_print("-" * 40)
                                    safe_print(data4.get('response', '')[:800])
                                    safe_print("-" * 40)
                                    
                                    if data4.get('contractor_created'):
                                        safe_print("\n[PASS] Stage 4: Account created successfully!")
                                        safe_print("\n*** COMPLETE FLOW TEST PASSED! ***")
                                    else:
                                        safe_print("\n[FAIL] Stage 4: Account not created")
                                else:
                                    safe_print(f"[FAIL] Stage 4 request failed: {response4.status_code}")
                                    safe_print(f"Error: {response4.text}")
                            else:
                                safe_print("\n[WARNING] No account creation prompt received yet")
                                safe_print("Response did not contain 'create profile' keywords")
                        else:
                            safe_print(f"[FAIL] Stage 3 request failed: {response3.status_code}")
                            safe_print(f"Error: {response3.text}")
                    else:
                        safe_print("\n[WARNING] Expected service questions, got different response")
                else:
                    safe_print(f"[FAIL] Stage 2 request failed: {response2.status_code}")
                    safe_print(f"Error: {response2.text}")
            else:
                safe_print("\n[WARNING] No confirmation prompt in Stage 1 response")
                safe_print("Response did not contain 'confirm' or 'your business' keywords")
        else:
            safe_print(f"[FAIL] Stage 1 request failed: {response1.status_code}")
            safe_print(f"Error: {response1.text}")
    
    except requests.exceptions.Timeout:
        safe_print("[FAIL] Request timed out")
    except Exception as e:
        safe_print(f"[FAIL] Error: {e}")
    
    safe_print("\n" + "="*80)
    safe_print("TEST COMPLETE")
    safe_print("="*80)

if __name__ == "__main__":
    test_complete_flow()