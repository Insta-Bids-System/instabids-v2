#!/usr/bin/env python3
"""
Simple Contractor Onboarding Test
Tests basic contractor experience without Unicode characters
"""

import asyncio
import json
import aiohttp
import requests
from datetime import datetime
import os
import sys

class ContractorOnboardingTester:
    def __init__(self):
        self.frontend_url = "http://localhost:5187"
        self.backend_url = "http://localhost:8008"
        self.session_id = f"test_contractor_{datetime.now().timestamp()}"
        
    async def test_frontend_access(self):
        """Test that frontend pages are accessible"""
        print("\n1. Testing Frontend Access")
        print("-" * 40)
        
        try:
            # Test contractor landing page
            response = requests.get(f"{self.frontend_url}/contractor", timeout=5)
            if response.status_code == 200:
                print("SUCCESS: Contractor landing page accessible")
                return True
            else:
                print(f"ERROR: Contractor page returned {response.status_code}")
                return False
                
        except Exception as e:
            print(f"ERROR: Frontend test failed: {str(e)}")
            return False
    
    async def test_coia_api(self):
        """Test CoIA API endpoint"""
        print("\n2. Testing CoIA API")
        print("-" * 40)
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "session_id": self.session_id,
                    "message": "I'm a general contractor",
                    "current_stage": "welcome",
                    "profile_data": {}
                }
                
                async with session.post(
                    f"{self.backend_url}/api/contractor-chat/message",
                    json=payload,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print("SUCCESS: CoIA API working")
                        print(f"Response: {data['response'][:100]}...")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"ERROR: CoIA API returned {response.status}: {error_text}")
                        return False
                        
        except Exception as e:
            print(f"ERROR: CoIA API test failed: {str(e)}")
            return False
            
    async def test_contractor_conversation(self):
        """Test full contractor conversation flow"""
        print("\n3. Testing Contractor Conversation Flow")
        print("-" * 40)
        
        messages = [
            "General Contractor",
            "15 years", 
            "Seattle, WA - 30 miles",
            "Licensed, insured, 5-year warranty"
        ]
        
        try:
            async with aiohttp.ClientSession() as session:
                current_stage = "welcome"
                
                for i, message in enumerate(messages):
                    print(f"  Step {i+1}: Sending '{message}'")
                    
                    payload = {
                        "session_id": self.session_id,
                        "message": message,
                        "current_stage": current_stage,
                        "profile_data": {}
                    }
                    
                    async with session.post(
                        f"{self.backend_url}/api/contractor-chat/message",
                        json=payload,
                        timeout=15
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            current_stage = data.get('stage', current_stage)
                            print(f"  SUCCESS: {data['response'][:80]}...")
                        else:
                            print(f"  ERROR: Step {i+1} failed with {response.status}")
                            return False
                            
                    await asyncio.sleep(1)
                    
                print("SUCCESS: Complete conversation flow working")
                return True
                    
        except Exception as e:
            print(f"ERROR: Conversation test failed: {str(e)}")
            return False

async def main():
    """Run contractor onboarding tests"""
    print("InstaBids Contractor Onboarding Test")
    print("=" * 50)
    
    # Check services
    print("Checking services...")
    try:
        frontend_check = requests.get("http://localhost:5187", timeout=3)
        print("FOUND: Frontend running on port 5187")
    except:
        print("ERROR: Frontend not running - start with: cd web && npm run dev")
        return
        
    try:
        backend_check = requests.get("http://localhost:8008/docs", timeout=3)
        print("FOUND: Backend running on port 8008")
    except:
        print("ERROR: Backend not running - start with: cd ai-agents && python main.py")
        return
        
    # Run tests
    tester = ContractorOnboardingTester()
    
    results = []
    results.append(await tester.test_frontend_access())
    results.append(await tester.test_coia_api())
    results.append(await tester.test_contractor_conversation())
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    print(f"Frontend Access: {'PASS' if results[0] else 'FAIL'}")
    print(f"CoIA API: {'PASS' if results[1] else 'FAIL'}")
    print(f"Conversation Flow: {'PASS' if results[2] else 'FAIL'}")
    
    if all(results):
        print("\nALL TESTS PASSED - Contractor system working!")
    else:
        print("\nSOME TESTS FAILED - Check errors above")

if __name__ == "__main__":
    asyncio.run(main())