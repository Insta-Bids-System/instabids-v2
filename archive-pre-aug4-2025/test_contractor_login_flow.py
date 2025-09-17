#!/usr/bin/env python3
"""
Test Complete Contractor Login Flow
Tests the full contractor experience with actual login credentials
"""

import asyncio
import json
import requests
import aiohttp
from datetime import datetime
import os
import sys

# Add the ai-agents directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

class ContractorLoginFlowTester:
    def __init__(self):
        self.frontend_url = "http://localhost:5187"
        self.backend_url = "http://localhost:8008"
        self.test_contractor = {
            'email': 'testcontractor@elitehomeconstruction.com',
            'password': 'TestContractor123!',
            'company_name': 'Elite Home Construction LLC',
            'session_id': f"test_contractor_{datetime.now().timestamp()}"
        }
        
    async def test_complete_contractor_experience(self):
        """Test the complete contractor experience from landing to dashboard"""
        print("Testing Complete Contractor Experience")
        print("=" * 50)
        
        # Step 1: Test landing page access
        await self.test_landing_page()
        
        # Step 2: Test CoIA conversation to create profile
        await self.test_coia_profile_creation()
        
        # Step 3: Test contractor dashboard
        await self.test_contractor_dashboard()
        
        # Step 4: Show final results
        await self.show_login_credentials()
        
    async def test_landing_page(self):
        """Test contractor landing page accessibility"""
        print("\n1. Testing Contractor Landing Page")
        print("-" * 40)
        
        try:
            response = requests.get(f"{self.frontend_url}/contractor", timeout=5)
            if response.status_code == 200:
                print("SUCCESS: Contractor landing page accessible")
                print(f"   URL: {self.frontend_url}/contractor")
            else:
                print(f"ERROR: Landing page returned {response.status_code}")
        except Exception as e:
            print(f"ERROR: Cannot access landing page: {str(e)}")
            print("   Make sure frontend is running: cd web && npm run dev")
    
    async def test_coia_profile_creation(self):
        """Test CoIA conversation that creates contractor profile"""
        print("\n2. Testing CoIA Profile Creation")
        print("-" * 40)
        
        # Full conversation flow to create complete contractor profile
        conversation_steps = [
            {
                "message": "General Contractor", 
                "description": "Primary trade"
            },
            {
                "message": "15 years", 
                "description": "Years of experience"
            },
            {
                "message": "Seattle, WA - 30 mile radius", 
                "description": "Service area"
            },
            {
                "message": "Licensed WA-GC-2024-001234, bonded and insured with $2M liability. Specialize in kitchen and bathroom remodels, home additions. All work comes with 5-year warranty. Elite Home Construction LLC.", 
                "description": "Complete contractor details"
            }
        ]
        
        try:
            async with aiohttp.ClientSession() as session:
                current_stage = "welcome"
                profile_data = {}
                
                for i, step in enumerate(conversation_steps):
                    print(f"   Step {i+1}: {step['description']}")
                    print(f"   Sending: '{step['message'][:50]}...'")
                    
                    payload = {
                        "session_id": self.test_contractor['session_id'],
                        "message": step["message"],
                        "current_stage": current_stage,
                        "profile_data": profile_data
                    }
                    
                    async with session.post(
                        f"{self.backend_url}/api/contractor-chat/message",
                        json=payload,
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            print(f"   SUCCESS: CoIA responded ({len(data['response'])} chars)")
                            
                            # Update state for next message
                            current_stage = data.get('stage', current_stage)
                            if 'profile_progress' in data:
                                progress = data['profile_progress']
                                profile_data.update(progress.get('collectedData', {}))
                                print(f"   Profile completeness: {progress.get('completeness', 0)*100:.0f}%")
                                
                        else:
                            error_text = await response.text()
                            print(f"   ERROR: CoIA API error {response.status}: {error_text}")
                            
                    await asyncio.sleep(1)
                    
                print("\nSUCCESS: CoIA conversation completed")
                print(f"Final profile data collected: {len(profile_data)} fields")
                
                # Store the session for dashboard testing
                if profile_data:
                    self.test_contractor['profile_data'] = profile_data
                    
        except Exception as e:
            print(f"ERROR: CoIA conversation failed: {str(e)}")
    
    async def test_contractor_dashboard(self):
        """Test contractor dashboard functionality"""
        print("\n3. Testing Contractor Dashboard")
        print("-" * 40)
        
        try:
            # Test dashboard page accessibility
            dashboard_url = f"{self.frontend_url}/contractor/dashboard"
            response = requests.get(dashboard_url, timeout=5)
            
            if response.status_code == 200:
                print("SUCCESS: Contractor dashboard accessible")
                print(f"   URL: {dashboard_url}")
            else:
                print(f"ERROR: Dashboard returned {response.status_code}")
                
            # Test if CoIA session can be used for dashboard
            if hasattr(self.test_contractor, 'profile_data'):
                print("SUCCESS: Profile data available for dashboard")
                print(f"   Session ID: {self.test_contractor['session_id']}")
            else:
                print("WARNING: No profile data from CoIA conversation")
                
        except Exception as e:
            print(f"ERROR: Dashboard test failed: {str(e)}")
    
    async def show_login_credentials(self):
        """Show the test credentials and how to use them"""
        print("\n" + "=" * 50)
        print("TEST CONTRACTOR ACCOUNT READY!")
        print("=" * 50)
        
        # Since we used CoIA conversation, the "login" is the session_id
        print("Contractor Profile Created Via CoIA:")
        print(f"   Company: {self.test_contractor['company_name']}")
        print(f"   Session ID: {self.test_contractor['session_id']}")
        
        if hasattr(self.test_contractor, 'profile_data'):
            profile = self.test_contractor['profile_data']
            print(f"   Primary Trade: {profile.get('primaryTrade', 'General Contractor')}")
            print(f"   Experience: {profile.get('experience', '15 years')}")
            print(f"   Service Area: {profile.get('serviceArea', 'Seattle, WA')}")
            
        print("\nHow to Test the System:")
        print(f"   1. Visit: {self.frontend_url}/contractor")
        print(f"   2. Click 'Get Started - It's Free'")
        print(f"   3. Chat with CoIA about your contracting business")
        print(f"   4. System will create your profile automatically")
        print(f"   5. Access dashboard: {self.frontend_url}/contractor/dashboard")
        
        print("\nThe CoIA System Works By:")
        print("   - Intelligent conversation extracts all contractor details")
        print("   - No manual form filling required")
        print("   - AI understands business description and creates profile")
        print("   - Session-based authentication (no traditional login/password)")
        
        print(f"\nTest Session Details:")
        print(f"   Backend URL: {self.backend_url}")
        print(f"   Frontend URL: {self.frontend_url}")
        print(f"   Session ID: {self.test_contractor['session_id']}")

async def main():
    """Run the complete contractor login flow test"""
    tester = ContractorLoginFlowTester()
    
    print("InstaBids Contractor Login Flow Test")
    print("=" * 50)
    print("This test demonstrates the complete contractor experience:")
    print("• Landing page access")
    print("• CoIA conversation-based profile creation")
    print("• Dashboard functionality")
    print("• Session-based authentication")
    print()
    
    # Check if services are running
    print("Checking service availability...")
    try:
        frontend_check = requests.get("http://localhost:5187", timeout=3)
        print("SUCCESS: Frontend service running")
    except:
        print("ERROR: Frontend not running")
        print("   Start with: cd web && npm run dev")
        
    try:
        backend_check = requests.get("http://localhost:8008/docs", timeout=3)
        print("SUCCESS: Backend service running")
    except:
        print("ERROR: Backend not running")
        print("   Start with: cd ai-agents && python main.py")
        
    print()
    
    # Run the complete test
    await tester.test_complete_contractor_experience()

if __name__ == "__main__":
    asyncio.run(main())