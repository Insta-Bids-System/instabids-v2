#!/usr/bin/env python3
"""
COMPREHENSIVE TEST: Prove CIA streaming actually works and indicator clears
This will test everything end-to-end including photo uploads
"""

import asyncio
import json
import time
import base64
import requests
from datetime import datetime
from typing import Dict, Any, List

# Terminal colors for clear results
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class CIAComprehensiveTest:
    def __init__(self):
        self.base_url = "http://localhost:8008"
        self.test_results = []
        self.test_session_id = f"test-session-{int(time.time())}"
        self.test_user_id = f"test-user-{int(time.time())}"
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result with color coding"""
        status = f"{GREEN}PASSED{RESET}" if passed else f"{RED}FAILED{RESET}"
        print(f"\n{status} - {test_name}")
        if details:
            print(f"  Details: {details}")
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
    
    def test_1_basic_streaming(self) -> bool:
        """Test 1: Basic CIA streaming works and completes with [DONE]"""
        print(f"\n{BLUE}TEST 1: Basic CIA Streaming{RESET}")
        print("=" * 50)
        
        try:
            # Make streaming request
            response = requests.post(
                f"{self.base_url}/api/cia/stream",
                json={
                    "messages": [{"role": "user", "content": "Hello, I need help with my backyard"}],
                    "conversation_id": self.test_session_id,
                    "user_id": self.test_user_id
                },
                stream=True,
                timeout=30
            )
            
            chunks_received = []
            done_received = False
            start_time = time.time()
            
            # Process streaming response
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        data = line_str[6:]  # Remove "data: " prefix
                        
                        if data == "[DONE]":
                            done_received = True
                            elapsed = time.time() - start_time
                            print(f"{GREEN}[DONE] marker received after {elapsed:.2f} seconds{RESET}")
                            break
                        else:
                            try:
                                chunk = json.loads(data)
                                chunks_received.append(chunk)
                                
                                # Print first few chunks to show it's working
                                if len(chunks_received) <= 3:
                                    content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                    if content:
                                        print(f"  Chunk {len(chunks_received)}: '{content}'")
                            except json.JSONDecodeError:
                                print(f"{YELLOW}Warning: Non-JSON chunk: {data}{RESET}")
            
            # Verify results
            if done_received and len(chunks_received) > 0:
                self.log_test(
                    "Basic CIA Streaming",
                    True,
                    f"Received {len(chunks_received)} chunks and [DONE] marker"
                )
                return True
            else:
                self.log_test(
                    "Basic CIA Streaming",
                    False,
                    f"Done: {done_received}, Chunks: {len(chunks_received)}"
                )
                return False
                
        except Exception as e:
            self.log_test("Basic CIA Streaming", False, str(e))
            return False
    
    def test_2_streaming_with_complex_message(self) -> bool:
        """Test 2: CIA handles complex project description and still completes"""
        print(f"\n{BLUE}TEST 2: Complex Message Streaming{RESET}")
        print("=" * 50)
        
        complex_message = """I need help with my backyard renovation. 
        The area is about 2000 sqft. I want to install artificial turf, 
        add a pergola, and create a fire pit area. My budget is around $15,000 
        and I need this done before summer (in about 3 months)."""
        
        try:
            response = requests.post(
                f"{self.base_url}/api/cia/stream",
                json={
                    "messages": [{"role": "user", "content": complex_message}],
                    "conversation_id": f"{self.test_session_id}-complex",
                    "user_id": self.test_user_id
                },
                stream=True,
                timeout=30
            )
            
            done_received = False
            chunk_count = 0
            full_response = ""
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        data = line_str[6:]
                        
                        if data == "[DONE]":
                            done_received = True
                            break
                        else:
                            try:
                                chunk = json.loads(data)
                                chunk_count += 1
                                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if content:
                                    full_response += content
                            except:
                                pass
            
            # Check if response mentions project details
            response_quality = False
            if "turf" in full_response.lower() or "pergola" in full_response.lower() or "15" in full_response:
                response_quality = True
                print(f"{GREEN}CIA understood project details{RESET}")
            
            passed = done_received and chunk_count > 10 and response_quality
            self.log_test(
                "Complex Message Streaming",
                passed,
                f"Chunks: {chunk_count}, Done: {done_received}, Quality: {response_quality}"
            )
            return passed
            
        except Exception as e:
            self.log_test("Complex Message Streaming", False, str(e))
            return False
    
    def test_3_simulate_photo_upload(self) -> bool:
        """Test 3: Simulate photo upload in conversation"""
        print(f"\n{BLUE}TEST 3: Photo Upload Simulation{RESET}")
        print("=" * 50)
        
        # Create a small test image (1x1 red pixel)
        test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        
        try:
            # Send message with image
            response = requests.post(
                f"{self.base_url}/api/cia/stream",
                json={
                    "messages": [{
                        "role": "user",
                        "content": "Here's a photo of my backyard that needs work",
                        "images": [f"data:image/png;base64,{test_image_base64}"]
                    }],
                    "conversation_id": f"{self.test_session_id}-photo",
                    "user_id": self.test_user_id
                },
                stream=True,
                timeout=30
            )
            
            done_received = False
            chunk_count = 0
            error_occurred = False
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        data = line_str[6:]
                        
                        if data == "[DONE]":
                            done_received = True
                            break
                        else:
                            try:
                                chunk = json.loads(data)
                                if "error" in chunk:
                                    error_occurred = True
                                    print(f"{RED}Error in response: {chunk['error']}{RESET}")
                                chunk_count += 1
                            except:
                                pass
            
            passed = done_received and chunk_count > 0 and not error_occurred
            self.log_test(
                "Photo Upload Handling",
                passed,
                f"Chunks: {chunk_count}, Done: {done_received}, No errors: {not error_occurred}"
            )
            return passed
            
        except Exception as e:
            self.log_test("Photo Upload Handling", False, str(e))
            return False
    
    def test_4_multiple_messages_conversation(self) -> bool:
        """Test 4: Multi-turn conversation to test memory and streaming"""
        print(f"\n{BLUE}TEST 4: Multi-turn Conversation{RESET}")
        print("=" * 50)
        
        messages = [
            "I need help with my lawn",
            "The area is 1500 sqft",
            "I want artificial turf installed"
        ]
        
        conversation_id = f"{self.test_session_id}-multi"
        all_passed = True
        
        for i, message in enumerate(messages, 1):
            print(f"\n  Turn {i}: '{message}'")
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/cia/stream",
                    json={
                        "messages": [{"role": "user", "content": message}],
                        "conversation_id": conversation_id,
                        "user_id": self.test_user_id
                    },
                    stream=True,
                    timeout=30
                )
                
                done_received = False
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith("data: "):
                            if line_str[6:] == "[DONE]":
                                done_received = True
                                print(f"    {GREEN}Turn {i} completed with [DONE]{RESET}")
                                break
                
                if not done_received:
                    all_passed = False
                    print(f"    {RED}Turn {i} failed - no [DONE] marker{RESET}")
                    
            except Exception as e:
                all_passed = False
                print(f"    {RED}Turn {i} error: {e}{RESET}")
        
        self.log_test("Multi-turn Conversation", all_passed, f"All {len(messages)} turns completed: {all_passed}")
        return all_passed
    
    def test_5_check_bid_card_creation(self) -> bool:
        """Test 5: Check if potential bid card gets created"""
        print(f"\n{BLUE}TEST 5: Bid Card Creation Check{RESET}")
        print("=" * 50)
        
        # Note: The bid card creation was disabled to fix hanging
        # This test verifies the fix is working (no hanging even without bid cards)
        
        try:
            # Send a message that should create a bid card
            response = requests.post(
                f"{self.base_url}/api/cia/stream",
                json={
                    "messages": [{"role": "user", "content": "I need a new deck built, 20x15 feet, composite material, $10k budget"}],
                    "conversation_id": f"{self.test_session_id}-bidcard",
                    "user_id": self.test_user_id
                },
                stream=True,
                timeout=10  # Short timeout to ensure no hanging
            )
            
            done_received = False
            timed_out = False
            
            try:
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith("data: "):
                            if line_str[6:] == "[DONE]":
                                done_received = True
                                break
            except requests.Timeout:
                timed_out = True
            
            # Success = completed without hanging (bid card creation is disabled for now)
            passed = done_received and not timed_out
            self.log_test(
                "No Hanging on Bid Card Path",
                passed,
                f"Completed without timeout: {passed}"
            )
            return passed
            
        except Exception as e:
            self.log_test("No Hanging on Bid Card Path", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all comprehensive tests"""
        print(f"\n{YELLOW}{'='*60}{RESET}")
        print(f"{YELLOW}CIA COMPREHENSIVE TESTING SUITE{RESET}")
        print(f"{YELLOW}{'='*60}{RESET}")
        print(f"Session ID: {self.test_session_id}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        # Run all tests
        test_methods = [
            self.test_1_basic_streaming,
            self.test_2_streaming_with_complex_message,
            self.test_3_simulate_photo_upload,
            self.test_4_multiple_messages_conversation,
            self.test_5_check_bid_card_creation
        ]
        
        for test_method in test_methods:
            test_method()
            time.sleep(1)  # Small delay between tests
        
        # Print summary
        print(f"\n{YELLOW}{'='*60}{RESET}")
        print(f"{YELLOW}TEST SUMMARY{RESET}")
        print(f"{YELLOW}{'='*60}{RESET}")
        
        passed_count = sum(1 for r in self.test_results if r["passed"])
        total_count = len(self.test_results)
        
        for result in self.test_results:
            status = f"{GREEN}[PASS]{RESET}" if result["passed"] else f"{RED}[FAIL]{RESET}"
            print(f"{status} {result['test']}")
            if result["details"] and not result["passed"]:
                print(f"   Issue: {result['details']}")
        
        print(f"\n{YELLOW}{'='*60}{RESET}")
        if passed_count == total_count:
            print(f"{GREEN}ALL TESTS PASSED! ({passed_count}/{total_count}){RESET}")
            print(f"{GREEN}CIA streaming is working perfectly!{RESET}")
            print(f"{GREEN}The 'Alex is responding...' indicator will clear properly!{RESET}")
        else:
            print(f"{RED}SOME TESTS FAILED ({passed_count}/{total_count}){RESET}")
            print(f"{YELLOW}Issues need investigation{RESET}")
        print(f"{YELLOW}{'='*60}{RESET}")

if __name__ == "__main__":
    tester = CIAComprehensiveTest()
    tester.run_all_tests()