#!/usr/bin/env python3
"""
Simple COIA Flow Test - Check actual business logic
"""

import requests
import json
import uuid

def test_simple_flow():
    session_id = f"test-{uuid.uuid4().hex[:8]}"
    contractor_lead_id = f"landing-{uuid.uuid4().hex[:12]}"
    
    print("TESTING REAL COIA FLOW")
    print("=" * 50)
    print(f"Session: {session_id}")
    print(f"Lead ID: {contractor_lead_id}")
    print()
    
    # Test 1: Company Introduction
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
            response_text = data1.get('response', '')
            state = data1.get('state', {})
            
            print(f"Status: SUCCESS ({response1.status_code})")
            print(f"Response length: {len(response_text)} chars")
            print(f"Company in state: {state.get('company_name', 'NOT EXTRACTED')}")
            print(f"Current mode: {state.get('current_mode', 'UNKNOWN')}")
            
            # Check if response mentions the company
            company_mentioned = "TurfGrass" in response_text or "turf" in response_text.lower()
            print(f"Company context understood: {company_mentioned}")
            
            print("\nResponse preview:")
            print(response_text[:300] + "..." if len(response_text) > 300 else response_text)
            print()
            
            # Test 2: Research Request
            print("STAGE 2: Research Request")
            print("-" * 30)
            
            request2 = {
                "message": "Yes, please research my company and find projects for me!",
                "session_id": session_id,
                "contractor_lead_id": contractor_lead_id
            }
            
            response2 = requests.post(
                "http://localhost:8008/api/coia/landing",
                json=request2,
                timeout=90
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                response2_text = data2.get('response', '')
                state2 = data2.get('state', {})
                
                print(f"Status: SUCCESS ({response2.status_code})")
                print(f"Response length: {len(response2_text)} chars")
                print(f"Research completed: {state2.get('research_completed', False)}")
                print(f"Website found: {state2.get('website_url', 'NONE')}")
                
                # Check for research indicators
                research_words = ["website", "business", "Phoenix", "Arizona", "services", "experience"]
                research_count = sum(1 for word in research_words if word.lower() in response2_text.lower())
                print(f"Research indicators found: {research_count}/{len(research_words)}")
                
                print("\nResearch response preview:")
                print(response2_text[:400] + "..." if len(response2_text) > 400 else response2_text)
                print()
                
                # Test 3: Project Request  
                print("STAGE 3: Project Request")
                print("-" * 30)
                
                request3 = {
                    "message": "Great! Show me current projects I can bid on.",
                    "session_id": session_id,
                    "contractor_lead_id": contractor_lead_id
                }
                
                response3 = requests.post(
                    "http://localhost:8008/api/coia/landing",
                    json=request3,
                    timeout=90
                )
                
                if response3.status_code == 200:
                    data3 = response3.json()
                    response3_text = data3.get('response', '')
                    state3 = data3.get('state', {})
                    
                    print(f"Status: SUCCESS ({response3.status_code})")
                    print(f"Response length: {len(response3_text)} chars")
                    print(f"Intelligence completed: {state3.get('intelligence_completed', False)}")
                    
                    # Check for project/bid indicators
                    project_words = ["project", "bid", "backyard", "landscape", "$", "budget", "timeline"]
                    project_count = sum(1 for word in project_words if word.lower() in response3_text.lower())
                    print(f"Project indicators found: {project_count}/{len(project_words)}")
                    
                    print("\nProject response preview:")
                    print(response3_text[:400] + "..." if len(response3_text) > 400 else response3_text)
                    
                    # FINAL ASSESSMENT
                    print("\n" + "=" * 50)
                    print("FINAL ASSESSMENT")
                    print("=" * 50)
                    
                    if response_text == response2_text == response3_text:
                        print("FAILURE: All responses identical - conversation stuck")
                    elif research_count >= 3 and project_count >= 3:
                        print("SUCCESS: Real business logic working")
                        print("- Company context understood")
                        print("- Research actually performed") 
                        print("- Projects presented")
                    elif research_count >= 3:
                        print("PARTIAL: Research working, projects need work")
                    elif project_count >= 3:
                        print("PARTIAL: Projects working, research needs work")
                    else:
                        print("FAILURE: Generic responses - no real business logic")
                        
                else:
                    print(f"FAILURE: Stage 3 failed ({response3.status_code})")
            else:
                print(f"FAILURE: Stage 2 failed ({response2.status_code})")
        else:
            print(f"FAILURE: Stage 1 failed ({response1.status_code})")
            print(f"Error: {response1.text}")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_simple_flow()