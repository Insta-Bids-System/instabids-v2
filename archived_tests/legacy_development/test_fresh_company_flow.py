#!/usr/bin/env python3
"""Test COIA complete flow with a FRESH company name."""

import requests
import json
import uuid
import time
from datetime import datetime

def test_complete_flow():
    """Test the complete 6-stage COIA flow with a fresh company."""
    
    # Use a FRESH company name for clean testing
    company_name = "Premier Landscaping Solutions"
    session_id = str(uuid.uuid4())
    contractor_lead_id = str(uuid.uuid4())
    
    print("=" * 80)
    print("COIA COMPLETE FLOW TEST WITH FRESH DATA")
    print("=" * 80)
    print(f"Company: {company_name}")
    print(f"Session ID: {session_id}")
    print(f"Contractor Lead ID: {contractor_lead_id}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # Stage 1: Initial contact with business name
    print("\n" + "="*50)
    print("STAGE 1: INITIAL BUSINESS NAME")
    print("="*50)
    
    stage1_request = {
        "message": f"I'm {company_name}",
        "session_id": session_id,
        "contractor_lead_id": contractor_lead_id
    }
    
    print(f"Sending: {stage1_request['message']}")
    
    try:
        response1 = requests.post(
            "http://localhost:8008/api/cia/converse-unified",
            json=stage1_request,
            timeout=60
        )
        
        if response1.status_code == 200:
            data = response1.json()
            print(f"Status: SUCCESS")
            print(f"Company extracted: {data.get('conversation_state', {}).get('company_name')}")
            print(f"Research completed: {data.get('conversation_state', {}).get('research_completed', False)}")
            
            # Check if we got research findings
            research_findings = data.get('conversation_state', {}).get('research_findings', {})
            if research_findings:
                print(f"Google Places data found:")
                print(f"  - Name: {research_findings.get('name')}")
                print(f"  - Address: {research_findings.get('address')}")
                print(f"  - Phone: {research_findings.get('phone')}")
                print(f"  - Website: {research_findings.get('website')}")
            
            print("\nAI Response:")
            print("-" * 40)
            print(data.get('response', '')[:800])
            print("-" * 40)
            
            # Check for confirmation prompt
            if "confirm" in data.get('response', '').lower() or "is this your business" in data.get('response', '').lower():
                print("\n✅ Stage 1 PASSED: Business confirmation prompt received")
                
                # Stage 2: Confirm business
                print("\n" + "="*50)
                print("STAGE 2: BUSINESS CONFIRMATION")
                print("="*50)
                
                time.sleep(2)  # Brief pause between stages
                
                stage2_request = {
                    "message": "Yes, that's my business",
                    "session_id": session_id,
                    "contractor_lead_id": contractor_lead_id
                }
                
                print(f"Sending: {stage2_request['message']}")
                
                response2 = requests.post(
                    "http://localhost:8008/api/cia/converse-unified",
                    json=stage2_request,
                    timeout=60
                )
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    print(f"Status: SUCCESS")
                    print(f"Research completed: {data2.get('conversation_state', {}).get('research_completed', False)}")
                    
                    print("\nAI Response:")
                    print("-" * 40)
                    print(data2.get('response', '')[:800])
                    print("-" * 40)
                    
                    # Check if we should continue to service expansion
                    if "service" in data2.get('response', '').lower() or "area" in data2.get('response', '').lower():
                        print("\n✅ Stage 2 PASSED: Deep research triggered")
                        
                        # Stage 3: Service information
                        print("\n" + "="*50)
                        print("STAGE 3: SERVICE INFORMATION")
                        print("="*50)
                        
                        time.sleep(2)
                        
                        stage3_request = {
                            "message": "We do full landscaping - design, installation, maintenance, hardscaping, irrigation",
                            "session_id": session_id,
                            "contractor_lead_id": contractor_lead_id
                        }
                        
                        print(f"Sending: {stage3_request['message']}")
                        
                        response3 = requests.post(
                            "http://localhost:8008/api/cia/converse-unified",
                            json=stage3_request,
                            timeout=60
                        )
                        
                        if response3.status_code == 200:
                            data3 = response3.json()
                            print(f"Status: SUCCESS")
                            
                            print("\nAI Response:")
                            print("-" * 40)
                            print(data3.get('response', '')[:800])
                            print("-" * 40)
                            
                            # Check for account creation prompt
                            if "create" in data3.get('response', '').lower() and "profile" in data3.get('response', '').lower():
                                print("\n✅ Stage 3 PASSED: Account creation prompt received")
                                
                                # Stage 4: Confirm account creation
                                print("\n" + "="*50)
                                print("STAGE 4: ACCOUNT CREATION CONFIRMATION")
                                print("="*50)
                                
                                time.sleep(2)
                                
                                stage4_request = {
                                    "message": "Yes, create my profile",
                                    "session_id": session_id,
                                    "contractor_lead_id": contractor_lead_id
                                }
                                
                                print(f"Sending: {stage4_request['message']}")
                                
                                response4 = requests.post(
                                    "http://localhost:8008/api/cia/converse-unified",
                                    json=stage4_request,
                                    timeout=60
                                )
                                
                                if response4.status_code == 200:
                                    data4 = response4.json()
                                    print(f"Status: SUCCESS")
                                    print(f"Contractor created: {data4.get('conversation_state', {}).get('contractor_created', False)}")
                                    print(f"Contractor ID: {data4.get('conversation_state', {}).get('contractor_id')}")
                                    
                                    print("\nAI Response:")
                                    print("-" * 40)
                                    print(data4.get('response', '')[:800])
                                    print("-" * 40)
                                    
                                    if data4.get('conversation_state', {}).get('contractor_created'):
                                        print("\n✅ Stage 4 PASSED: Account created successfully!")
                                        print("\n🎉 COMPLETE FLOW TEST PASSED!")
                                    else:
                                        print("\n❌ Stage 4 FAILED: Account not created")
                                else:
                                    print(f"❌ Stage 4 request failed: {response4.status_code}")
                            else:
                                print("\n⚠️ No account creation prompt received yet")
                        else:
                            print(f"❌ Stage 3 request failed: {response3.status_code}")
                    else:
                        print("\n⚠️ Expected service questions, got different response")
                else:
                    print(f"❌ Stage 2 request failed: {response2.status_code}")
            else:
                print("\n⚠️ No confirmation prompt in Stage 1 response")
        else:
            print(f"❌ Stage 1 request failed: {response1.status_code}")
            print(f"Error: {response1.text}")
    
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    test_complete_flow()