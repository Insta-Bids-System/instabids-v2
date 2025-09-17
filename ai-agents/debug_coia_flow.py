"""
Debug COIA flow to understand why research findings are not reaching conversation
"""
import requests
import json
from config.service_urls import get_backend_url

def debug_coia_flow():
    """Debug the complete COIA flow"""
    
    print("\n" + "="*80)
    print("DEBUGGING COIA FLOW")
    print("="*80)
    
    # Use a fresh session
    test_data = {
        "message": "Hello, I'm with JM Holiday Lighting, we install christmas lights in South Florida",
        "contractor_id": "debug-flow-test",
        "session_id": "debug-session-456"
    }
    
    url = f"{get_backend_url()}/api/coia/landing"
    
    print("\nStep 1: Fresh conversation with business introduction")
    print("Expected flow: extraction -> mode_detector -> research -> conversation")
    
    try:
        # Make the request
        response = requests.post(url, json=test_data, timeout=300)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"[SUCCESS] Response received")
            
            # Analyze all the state
            print("\n" + "="*60)
            print("COMPLETE STATE ANALYSIS")
            print("="*60)
            
            # Core state
            print(f"interface: {data.get('interface')}")
            print(f"current_mode: {data.get('current_mode')}")
            print(f"session_id: {data.get('session_id')}")
            print(f"contractor_lead_id: {data.get('contractor_lead_id')}")
            
            # Company extraction
            company_name = data.get("contractor_profile", {}).get("company_name")
            print(f"company_name (from profile): {company_name}")
            print(f"company_name (direct): {data.get('company_name')}")
            
            # Research status
            print(f"research_completed: {data.get('research_completed')}")
            print(f"research_findings: {data.get('research_findings')}")
            
            # Completion status
            print(f"completion_ready: {data.get('completion_ready')}")
            print(f"contractor_created: {data.get('contractor_created')}")
            
            # Check extraction status
            extraction_completed = data.get('extraction_completed', False)
            print(f"extraction_completed: {extraction_completed}")
            
            # Mode detector decision
            mode_detector_decision = data.get('mode_detector_decision')
            print(f"mode_detector_decision: {mode_detector_decision}")
            
            # Previous mode
            previous_mode = data.get('previous_mode')
            print(f"previous_mode: {previous_mode}")
            
            print("\n" + "="*60)
            print("FLOW ANALYSIS")
            print("="*60)
            
            # Check what should have happened
            if company_name and not data.get('research_completed'):
                print("EXPECTED: Should have triggered research because:")
                print(f"  - Company name extracted: {company_name}")
                print(f"  - Research not completed: {not data.get('research_completed')}")
                print("PROBLEM: Research was not triggered")
            
            elif data.get('research_completed') and not data.get('research_findings'):
                print("PROBLEM IDENTIFIED: Research completed but no findings!")
                print("This means:")
                print("  1. Research node ran and set research_completed=True")
                print("  2. But research_findings is missing/null")
                print("  3. Data was lost between research node and final state")
                
            elif data.get('research_completed') and data.get('research_findings'):
                print("SUCCESS: Research completed with findings")
                research_findings = data.get('research_findings')
                raw_data = research_findings.get("raw_data", {})
                google_data = raw_data.get("google_business", {})
                print(f"Google data present: {bool(google_data)}")
                
            else:
                print("UNCLEAR: Unexpected state combination")
            
            # Check AI response for hallucination
            ai_response = data.get("response", "")
            print(f"\nAI Response includes real data:")
            print(f"  - Mentions Pompano Beach: {'Pompano Beach' in ai_response}")
            print(f"  - Mentions website: {'jmholidaylighting.com' in ai_response}")
            print(f"  - Mentions 'Not found': {'Not found' in ai_response or 'not found' in ai_response}")
            
            return data
                
        else:
            print(f"[ERROR] Request failed: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        return None

if __name__ == "__main__":
    result = debug_coia_flow()
    if result:
        print(f"\nDEBUG COMPLETE: Found the flow issue")
    else:
        print(f"\nDEBUG FAILED: Could not analyze flow")