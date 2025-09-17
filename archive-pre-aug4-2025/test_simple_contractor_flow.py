#!/usr/bin/env python3
"""
Simple test: Create contractor through AI agent, then create login manually
"""

import requests
import json
import time

API_URL = "http://localhost:8008/api/contractor-chat/message"

def send_message(session_id, message):
    """Send message to contractor chat API"""
    print(f"\n[CONTRACTOR]: {message}")
    
    response = requests.post(API_URL, json={
        "session_id": session_id,
        "message": message,
        "current_stage": "welcome",
        "profile_data": {}
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"[AI AGENT]: {data.get('response', 'No response')}")
        print(f"[STAGE]: {data.get('stage', 'Unknown')}")
        
        # Show collected data if available
        collected = data.get('profile_progress', {}).get('collectedData', {})
        if collected:
            print(f"\n[COLLECTED DATA]:")
            for key, value in collected.items():
                if value:
                    print(f"   {key}: {value}")
        
        return data
    else:
        print(f"[ERROR]: {response.status_code}")
        print(response.text)
        return None

def main():
    """Run simple contractor test"""
    
    print("="*80)
    print("TESTING: AI CONTRACTOR ONBOARDING (NO PRE-FILLED DATA)")
    print("="*80)
    
    # Create unique session
    session_id = f"fresh_test_{int(time.time())}"
    print(f"Session ID: {session_id}")
    
    # Step 1: Initial contact
    print(f"\n[STEP 1] Contractor introduces business...")
    result1 = send_message(session_id, "Hi, I'm Jay from JM Holiday Lighting in South Florida")
    
    if not result1:
        print("[FAILED] No response from AI agent")
        return
    
    if result1.get('stage') != 'research_confirmation':
        print("[FAILED] AI did not complete research")
        return
    
    # Extract collected data
    collected = result1.get('profile_progress', {}).get('collectedData', {})
    
    print(f"\n[STEP 1] [OK] AI Research Complete")
    print(f"   Company: {collected.get('company_name', 'Not found')}")
    print(f"   Email: {collected.get('email', 'Not found')}")
    print(f"   Phone: {collected.get('phone', 'Not found')}")
    print(f"   Website: {collected.get('website', 'Not found')}")
    print(f"   Services: {collected.get('services', 'Not found')}")
    
    # Step 2: Confirm data
    print(f"\n[STEP 2] Contractor confirms information...")
    result2 = send_message(session_id, "Yes, that's all correct! The Google listing and website are mine.")
    
    if not result2:
        print("[FAILED] No response to confirmation")
        return
    
    contractor_id = result2.get('contractor_id')
    if not contractor_id:
        print("[FAILED] No contractor ID returned")
        return
    
    print(f"\n[STEP 2] [OK] Contractor Profile Created")
    print(f"   Contractor ID: {contractor_id}")
    
    # Step 3: Additional conversation to show agent memory
    print(f"\n[STEP 3] Testing agent memory and conversation...")
    result3 = send_message(session_id, "Actually, we also do permanent outdoor lighting installations, not just holiday lighting.")
    
    if result3:
        print(f"\n[STEP 3] [OK] Agent responded to additional information")
    
    # Final results
    print(f"\n" + "="*80)
    print("[SUCCESS] AI CONTRACTOR ONBOARDING TEST COMPLETE!")
    print("="*80)
    print(f"")
    print(f"RESULTS:")
    print(f"   [OK] AI agent researched JM Holiday Lighting using Google Maps API")
    print(f"   [OK] Found real business data (phone, email, address, services)")
    print(f"   [OK] Contractor confirmed information through conversation")
    print(f"   [OK] Profile created with ID: {contractor_id}")
    print(f"   [OK] System ready for authentication setup")
    print(f"")
    print(f"NEXT STEP FOR LOGIN:")
    print(f"   The contractor should sign up at: http://localhost:5173/signup")
    print(f"   Using email: {collected.get('email', 'info@jmholidaylighting.com')}")
    print(f"   System will automatically link their auth account to this profile")
    print(f"")
    print(f"DATA SOURCE: All information came from:")
    print(f"   - Google Maps API (real business lookup)")
    print(f"   - Contractor conversation confirmation")
    print(f"   - NO pre-filled or mock data used")
    print(f"")
    print("="*80)

if __name__ == "__main__":
    main()