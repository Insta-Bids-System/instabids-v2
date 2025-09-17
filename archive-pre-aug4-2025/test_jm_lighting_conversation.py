#!/usr/bin/env python3
"""
Act as JM Holiday Lighting contractor and test complete conversation flow
"""

import requests
import json
import time

API_URL = "http://localhost:8008/api/contractor-chat/message"

def send_message(session_id, message):
    """Send message to contractor chat API"""
    print(f"\n[JM HOLIDAY LIGHTING]: {message}")
    
    response = requests.post(API_URL, json={
        "session_id": session_id,
        "message": message,
        "current_stage": "welcome",
        "profile_data": {}
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"[COIA AGENT]: {data.get('response', 'No response')}")
        print(f"[STAGE]: {data.get('stage', 'Unknown')}")
        
        # Show collected data if available
        collected = data.get('profile_progress', {}).get('collectedData', {})
        if collected:
            print(f"[COLLECTED DATA]:")
            for key, value in collected.items():
                if value:
                    print(f"   {key}: {value}")
        
        return data
    else:
        print(f"[ERROR]: {response.status_code}")
        print(response.text)
        return None

def main():
    """Test complete JM Holiday Lighting conversation"""
    
    print("[TESTING] INTELLIGENT CONTRACTOR ONBOARDING - JM HOLIDAY LIGHTING")
    print("=" * 80)
    
    # Generate unique session ID
    session_id = f"jm_lighting_test_{int(time.time())}"
    print(f"Session ID: {session_id}")
    
    # Conversation 1: Initial onboarding
    print("\n[CONVERSATION 1] INITIAL CONTRACTOR ONBOARDING")
    print("-" * 60)
    
    # Step 1: Introduce business
    result1 = send_message(session_id, "Hi, I'm Jay from JM Holiday Lighting in South Florida")
    
    if result1 and result1.get('stage') == 'research_confirmation':
        print("\n[SUCCESS] Research completed! Agent found our business information.")
        
        # Step 2: Confirm information
        result2 = send_message(session_id, "Yes, that's all correct! The Google listing and website are mine.")
        
        if result2 and result2.get('contractor_id'):
            contractor_id = result2.get('contractor_id')
            print(f"\n[SUCCESS] Contractor profile created: {contractor_id}")
            
            # Step 3: Ask about additional services  
            result3 = send_message(session_id, "Actually, we also do permanent outdoor lighting installations, not just holiday lighting.")
            
            print("\n" + "="*60)
            print("CONVERSATION 1 COMPLETE")
            print("="*60)
            
            # Wait a moment
            time.sleep(2)
            
            # Conversation 2: Returning contractor (new session)
            print("\n[CONVERSATION 2] RETURNING CONTRACTOR (NEW SESSION)")
            print("-" * 60)
            
            new_session_id = f"jm_lighting_return_{int(time.time())}"
            
            # Step 1: Return as same business
            result4 = send_message(new_session_id, "Hi, this is JM Holiday Lighting again")
            
            if result4 and 'returning' in result4.get('stage', ''):
                print("\n[SUCCESS] System recognized returning contractor!")
                
                # Step 2: Update information
                result5 = send_message(new_session_id, "I want to update my service areas to include Palm Beach County")
                
                # Step 3: Ask about projects
                result6 = send_message(new_session_id, "Do you have any new holiday lighting projects for this season?")
                
                print("\n" + "="*60)
                print("CONVERSATION 2 COMPLETE - RETURNING CONTRACTOR FLOW TESTED")
                print("="*60)
            else:
                print("\n[WARNING] System did not recognize returning contractor")
            
            # Conversation 3: Business inquiry
            print("\n[CONVERSATION 3] BUSINESS INQUIRY")
            print("-" * 60)
            
            inquiry_session_id = f"jm_lighting_inquiry_{int(time.time())}"
            
            # Step 1: Ask about platform
            result7 = send_message(inquiry_session_id, "How does InstaBids work for contractors like us?")
            
            # Step 2: Ask about pricing
            result8 = send_message(inquiry_session_id, "What does it cost to join?")
            
            print("\n" + "="*60)
            print("ALL CONVERSATIONS COMPLETE")
            print("="*60)
            
            return True
        
        else:
            print("\n[ERROR] Profile creation failed")
            return False
    
    else:
        print("\n[ERROR] Initial research failed")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n[FINAL] JM HOLIDAY LIGHTING CONTRACTOR ONBOARDING TEST: PASSED")
    else:
        print("\n[FINAL] JM HOLIDAY LIGHTING CONTRACTOR ONBOARDING TEST: FAILED")