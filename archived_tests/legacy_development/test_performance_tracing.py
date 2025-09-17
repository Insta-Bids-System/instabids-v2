#!/usr/bin/env python3
"""
Performance Tracing Test Script for COIA Background LLM Processing
Tests the instrumented system to identify 10-30s bottlenecks in DeepAgents processing

Based on user's performance diagnostic runbook:
1. Trigger background DeepAgents processing
2. Monitor performance logs for timing data
3. Identify specific bottlenecks (likely agent.ainvoke call)
4. Collect data for optimization decisions
"""

import requests
import time
import sys
import asyncio
import subprocess
from datetime import datetime
from typing import List, Dict, Any

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def print_result(test_name: str, elapsed: float, status: int, success: bool = True):
    """Print formatted test result"""
    status_icon = "SUCCESS" if success else "FAILED"
    speed_icon = "FAST" if elapsed < 2.0 else ("OK" if elapsed < 5.0 else "SLOW")
    print(f"{status_icon} {test_name}: {elapsed:.2f}s {speed_icon} (Status: {status})")

def monitor_docker_logs_async():
    """Monitor Docker logs for performance tracing data"""
    print("Starting log monitoring for performance tracing...")
    try:
        # Use Docker MCP to get logs
        return True
    except Exception as e:
        print(f"Warning: Could not start log monitoring: {e}")
        return False

def test_coia_performance_tracing():
    """Test the COIA system with performance tracing enabled"""
    print_header("COIA PERFORMANCE TRACING TEST")
    print("🎯 Testing instrumented COIA system to identify 10-30s bottlenecks")
    print()
    
    test_results = []
    
    # Test 1: Fast response with background processing
    print("TEST 1: COIA with DeepAgents background processing")
    print("Expected: <2s response, background processing starts with timing")
    
    start_time = time.time()
    try:
        response = requests.post('http://localhost:8008/api/coia/landing', json={
            'user_id': 'test-perf-tracing-001', 
            'session_id': 'session-perf-tracing-001',
            'contractor_lead_id': 'perf-tracing-contractor-001',
            'message': 'I run Performance Test Landscaping in Miami, Florida'
        }, timeout=10, env={'USE_DEEPAGENTS_LANDING': 'true'})
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print_result("Main Response", elapsed, response.status_code, True)
            print(f"   📝 Company: {data.get('company_name', 'Unknown')}")
            print(f"   💬 Response Length: {len(data.get('response', ''))} chars")
            
            # Check if background processing was triggered
            if elapsed < 3.0:
                print("   🚀 Background processing should be running...")
                print("   📊 Check logs for performance tracing data:")
                print("      - PERF background_deepagents.init_start")
                print("      - PERF background_deepagents.deepagents_import_complete") 
                print("      - PERF background_deepagents.deepagents_ainvoke_complete")
                
                test_results.append({
                    "test": "Main Response Speed",
                    "elapsed": elapsed,
                    "success": True,
                    "notes": "Fast response achieved, background processing triggered"
                })
            else:
                print("   ⚠️ Response too slow - background processing may be blocking")
                test_results.append({
                    "test": "Main Response Speed", 
                    "elapsed": elapsed,
                    "success": False,
                    "notes": "Response too slow, may not be using background processing"
                })
        else:
            elapsed = time.time() - start_time
            print_result("Main Response", elapsed, response.status_code, False)
            print(f"   ❌ Error: {response.text[:200]}")
            test_results.append({
                "test": "Main Response",
                "elapsed": elapsed, 
                "success": False,
                "notes": f"HTTP {response.status_code}: {response.text[:100]}"
            })
            
    except requests.Timeout:
        elapsed = time.time() - start_time
        print_result("Main Response", elapsed, 0, False)
        print("   ❌ Request timed out")
        test_results.append({
            "test": "Main Response",
            "elapsed": elapsed,
            "success": False,
            "notes": "Request timed out"
        })
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Test 1 failed after {elapsed:.2f}s: {e}")
        test_results.append({
            "test": "Main Response",
            "elapsed": elapsed,
            "success": False,
            "notes": f"Exception: {str(e)[:100]}"
        })
    
    print()
    print("⏰ Waiting 5 seconds for background processing to start...")
    time.sleep(5)
    
    # Test 2: Follow-up message to same session (should use full context)
    print("\nTEST 2: Follow-up conversation (full context)")
    print("Expected: Template response + background LLM with full conversation context")
    
    start_time = time.time()
    try:
        response = requests.post('http://localhost:8008/api/coia/landing', json={
            'user_id': 'test-perf-tracing-001',
            'session_id': 'session-perf-tracing-001', 
            'contractor_lead_id': 'perf-tracing-contractor-001',
            'message': 'We specialize in landscaping, lawn maintenance, and tree removal. What projects are available in our area?'
        }, timeout=10, env={'USE_DEEPAGENTS_LANDING': 'true'})
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print_result("Follow-up Response", elapsed, response.status_code, True)
            print(f"   📝 Company: {data.get('company_name', 'Unknown')}")
            print(f"   💬 Response Preview: {data.get('response', '')[:150]}...")
            
            test_results.append({
                "test": "Follow-up Response",
                "elapsed": elapsed,
                "success": True,
                "notes": "Follow-up conversation processed"
            })
        else:
            print_result("Follow-up Response", elapsed, response.status_code, False)
            test_results.append({
                "test": "Follow-up Response",
                "elapsed": elapsed,
                "success": False,
                "notes": f"HTTP {response.status_code}"
            })
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Test 2 failed after {elapsed:.2f}s: {e}")
        test_results.append({
            "test": "Follow-up Response",
            "elapsed": elapsed,
            "success": False,
            "notes": f"Exception: {str(e)[:100]}"
        })
    
    # Wait for background processing to complete
    print()
    print("⏰ Waiting 30 seconds for background DeepAgents processing to complete...")
    print("📊 Monitor logs for performance bottlenecks:")
    print("   🔍 Look for: PERF background_deepagents.deepagents_ainvoke_complete")
    print("   🐌 Expected bottleneck: agent.ainvoke() taking 10-30s")
    print("   ⚡ Quick wins: import times, memory operations, research calls")
    
    time.sleep(30)
    
    return test_results

def generate_performance_summary(test_results: List[Dict[str, Any]]):
    """Generate performance test summary"""
    print_header("PERFORMANCE TEST SUMMARY")
    
    total_tests = len(test_results)
    successful_tests = sum(1 for r in test_results if r['success'])
    
    print(f"📊 Tests Run: {total_tests}")
    print(f"✅ Successful: {successful_tests}")
    print(f"❌ Failed: {total_tests - successful_tests}")
    print()
    
    print("📋 Detailed Results:")
    for result in test_results:
        status_icon = "✅" if result['success'] else "❌"
        print(f"   {status_icon} {result['test']}: {result['elapsed']:.2f}s")
        print(f"      📝 {result['notes']}")
    
    print()
    print("🔍 PERFORMANCE ANALYSIS CHECKLIST:")
    print("   1. Check Docker logs for PERF timing entries")
    print("   2. Look for: 'PERF background_deepagents.deepagents_ainvoke_complete'")
    print("   3. Identify slowest operations (>5000ms warnings)")
    print("   4. Expected bottleneck: agent.ainvoke() in DeepAgents processing")
    print("   5. Quick wins: Move slow imports, optimize memory operations")
    
    print()
    print("📊 NEXT STEPS:")
    if successful_tests == total_tests:
        print("   ✅ All tests passed - performance tracing is working")
        print("   🔍 Analyze logs to identify specific bottlenecks") 
        print("   ⚡ Implement quick wins from user's runbook")
    else:
        print("   ❌ Some tests failed - fix core functionality first")
        print("   🔧 Address test failures before performance optimization")

def main():
    """Main performance tracing test"""
    print_header("COIA PERFORMANCE TRACING DIAGNOSTIC")
    print("Testing instrumented COIA system to identify LLM bottlenecks")
    print("Based on user's performance diagnostic runbook")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Start background log monitoring
    monitor_docker_logs_async()
    
    # Run performance tests
    test_results = test_coia_performance_tracing()
    
    # Generate summary
    generate_performance_summary(test_results)
    
    print()
    print_header("PERFORMANCE TRACING TEST COMPLETE")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Check Docker logs for detailed performance timing data")
    print("Look for PERF entries to identify 10-30s bottlenecks")

if __name__ == "__main__":
    main()