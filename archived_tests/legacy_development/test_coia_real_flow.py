#!/usr/bin/env python3
"""
REAL COIA Flow Test - Verify actual business logic works
Tests the complete flow from landing page to contractor creation
"""

import requests
import json
import uuid
from datetime import datetime

def test_real_coia_flow():
    """Test the actual COIA business flow with real company research"""
    
    print("TESTING REAL COIA BUSINESS FLOW")
    print("="*60)
    
    # Generate unique session for this test
    session_id = f"test-session-{uuid.uuid4().hex[:8]}"
    contractor_lead_id = f"landing-{uuid.uuid4().hex[:12]}"
    
    print(f"Session ID: {session_id}")
    print(f"Contractor Lead ID: {contractor_lead_id}")
    print()
    
    try:
        # STAGE 1: Company Introduction
        print("STAGE 1: Company Introduction")
        print("-" * 30)
        
        stage1_request = {
            "message": "Hi, I'm from TurfGrass Artificial Solutions. We do artificial turf installation in Phoenix.",
            "session_id": session_id,
            "contractor_lead_id": contractor_lead_id
        }
        
        response1 = requests.post(
            "http://localhost:8008/api/coia/landing",
            json=stage1_request,
            timeout=120
        )
        
        if response1.status_code == 200:
            data1 = response1.json()
            response1_text = data1.get('response', '')
            
            print(f"API Call Success")
            print(f"Response length: {len(response1_text)} chars")
            print(f"Company extracted: {data1.get('state', {}).get('company_name', 'NOT FOUND')}")
            
            # Check if COIA actually understood the company
            if "TurfGrass" in response1_text or "artificial turf" in response1_text.lower():
                print("✅ COIA understood the company context")
            else:
                print("❌ COIA failed to understand company context")
                
            print(f"\n💬 COIA Response Preview:")
            print(f"   {response1_text[:200]}...")
            print()
            
        else:
            print(f"❌ Stage 1 failed: {response1.status_code}")
            return False
            
        # STAGE 2: Research Authorization
        print("🔍 STAGE 2: Research Authorization") 
        print("-" * 30)
        
        stage2_request = {
            "message": "Yes, please research my company! I want to see what you can find.",
            "session_id": session_id,
            "contractor_lead_id": contractor_lead_id
        }
        
        response2 = requests.post(
            "http://localhost:8008/api/coia/landing",
            json=stage2_request,
            timeout=120
        )
        
        if response2.status_code == 200:
            data2 = response2.json()
            response2_text = data2.get('response', '')
            state2 = data2.get('state', {})
            
            print(f"✅ API Call Success")
            print(f"📄 Response length: {len(response2_text)} chars")
            print(f"🔬 Research completed: {state2.get('research_completed', False)}")
            print(f"🌐 Website found: {state2.get('website_url', 'NOT FOUND')}")
            
            # Check for actual research content
            research_indicators = [
                "website", "business", "services", "Phoenix", "Arizona", 
                "turf", "installation", "years", "experience"
            ]
            
            found_research = sum(1 for indicator in research_indicators 
                               if indicator.lower() in response2_text.lower())
            
            print(f"🧪 Research indicators found: {found_research}/{len(research_indicators)}")
            
            if found_research >= 3:
                print("✅ REAL research data detected in response")
            else:
                print("❌ Response appears generic - no real research")
                
            print(f"\n💬 Research Response Preview:")
            print(f"   {response2_text[:300]}...")
            print()
            
        else:
            print(f"❌ Stage 2 failed: {response2.status_code}")
            return False
            
        # STAGE 3: Business Details Request
        print("📊 STAGE 3: Business Details Request")
        print("-" * 30)
        
        stage3_request = {
            "message": "That's great! Can you tell me about current projects I might be good for?",
            "session_id": session_id, 
            "contractor_lead_id": contractor_lead_id
        }
        
        response3 = requests.post(
            "http://localhost:8008/api/coia/landing",
            json=stage3_request,
            timeout=120
        )
        
        if response3.status_code == 200:
            data3 = response3.json()
            response3_text = data3.get('response', '')
            state3 = data3.get('state', {})
            
            print(f"✅ API Call Success") 
            print(f"📄 Response length: {len(response3_text)} chars")
            print(f"💼 Intelligence completed: {state3.get('intelligence_completed', False)}")
            
            # Check for bid card presentation
            bid_indicators = [
                "project", "bid", "$", "budget", "timeline", "backyard", 
                "landscape", "residential", "commercial"
            ]
            
            found_bids = sum(1 for indicator in bid_indicators 
                           if indicator.lower() in response3_text.lower())
            
            print(f"🎯 Bid card indicators found: {found_bids}/{len(bid_indicators)}")
            
            if found_bids >= 4:
                print("✅ REAL bid cards/projects presented")
            else:
                print("❌ No real project data - generic response")
                
            print(f"\n💬 Project Response Preview:")
            print(f"   {response3_text[:300]}...")
            print()
            
        else:
            print(f"❌ Stage 3 failed: {response3.status_code}")
            return False
            
        # STAGE 4: Account Creation
        print("👤 STAGE 4: Account Creation")
        print("-" * 30)
        
        stage4_request = {
            "message": "Perfect! I'm interested in these projects. Let's create my contractor account.",
            "session_id": session_id,
            "contractor_lead_id": contractor_lead_id
        }
        
        response4 = requests.post(
            "http://localhost:8008/api/coia/landing", 
            json=stage4_request,
            timeout=120
        )
        
        if response4.status_code == 200:
            data4 = response4.json()
            response4_text = data4.get('response', '')
            state4 = data4.get('state', {})
            
            print(f"✅ API Call Success")
            print(f"📄 Response length: {len(response4_text)} chars")
            print(f"🏗️  Contractor created: {state4.get('contractor_created', False)}")
            print(f"✅ Account confirmed: {data4.get('account_creation_confirmed', False)}")
            
            # Check for actual account creation content
            account_indicators = [
                "account", "profile", "created", "welcome", "dashboard", 
                "login", "email", "password", "verification"
            ]
            
            found_account = sum(1 for indicator in account_indicators 
                              if indicator.lower() in response4_text.lower())
            
            print(f"👤 Account creation indicators: {found_account}/{len(account_indicators)}")
            
            if found_account >= 3:
                print("✅ REAL account creation process triggered")
            else:
                print("❌ Generic response - no actual account creation")
                
            print(f"\n💬 Account Response Preview:")
            print(f"   {response4_text[:300]}...")
            print()
            
            # Final verification
            if state4.get('contractor_created') and data4.get('account_creation_confirmed'):
                print("🎉 COMPLETE SUCCESS: Full business flow working!")
                return True
            else:
                print("⚠️  PARTIAL SUCCESS: Flow progressed but needs completion")
                return False
                
        else:
            print(f"❌ Stage 4 failed: {response4.status_code}")
            return False
            
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return False
        
    finally:
        print("\n" + "="*60)
        print("REAL FLOW TEST COMPLETE")
        print("="*60)

if __name__ == "__main__":
    test_real_coia_flow()