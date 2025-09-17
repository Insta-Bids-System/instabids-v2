#!/usr/bin/env python3
"""
COMPREHENSIVE BSA DELEGATION PROOF TEST
Shows exactly how main agent delegates to sub-agent with timing and flow
"""

import os
import sys
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

import requests
import json
import time
from datetime import datetime
import threading

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def monitor_stream(url, payload, test_name):
    """Monitor the streaming response and track delegation"""
    
    print(f"\n📋 TEST: {test_name}")
    print(f"🧑 User Message: {payload['message']}")
    print("-" * 60)
    
    # Tracking variables
    start_time = time.time()
    first_chunk_time = None
    delegation_time = None
    sub_agent_start = None
    sub_agent_end = None
    
    # State tracking
    main_agent_chunks = []
    sub_agent_activity = []
    statuses = []
    tools_used = []
    
    # Flags
    delegation_detected = False
    sub_agent_working = False
    conversation_continues = False
    
    try:
        response = requests.post(url, json=payload, stream=True, timeout=30)
        
        print("\n⏱️ REAL-TIME ACTIVITY LOG:")
        print("-" * 40)
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        current_time = time.time() - start_time
                        
                        # Track status changes
                        if 'status' in data:
                            status = data['status']
                            statuses.append((current_time, status))
                            print(f"[{current_time:5.2f}s] 📊 Status: {status}")
                            
                            # Check for delegation indicators
                            if 'delegat' in status.lower() or 'sub' in status.lower():
                                delegation_detected = True
                                delegation_time = current_time
                                sub_agent_start = current_time
                                print(f"[{current_time:5.2f}s] 🚀 DELEGATION DETECTED!")
                        
                        # Track message chunks
                        if 'chunk' in data:
                            chunk = data['chunk']
                            if not first_chunk_time:
                                first_chunk_time = current_time
                                print(f"[{current_time:5.2f}s] 💬 First response chunk received")
                            
                            # Analyze chunk content
                            if 'searching' in chunk.lower() or 'looking' in chunk.lower():
                                print(f"[{current_time:5.2f}s] 🔍 Sub-agent searching...")
                                sub_agent_working = True
                            
                            if 'found' in chunk.lower() or 'BC-' in chunk:
                                print(f"[{current_time:5.2f}s] ✅ Sub-agent found results!")
                                if sub_agent_working:
                                    sub_agent_end = current_time
                            
                            # Check if main agent continues talking
                            if delegation_detected and not sub_agent_working:
                                conversation_continues = True
                                print(f"[{current_time:5.2f}s] 💭 Main agent continues conversation")
                            
                            # Store chunks
                            if sub_agent_working:
                                sub_agent_activity.append((current_time, chunk[:50]))
                            else:
                                main_agent_chunks.append((current_time, chunk[:50]))
                        
                        # Track tool usage
                        if 'tools' in data or 'tool' in data:
                            tool_info = data.get('tools') or data.get('tool')
                            tools_used.append((current_time, tool_info))
                            print(f"[{current_time:5.2f}s] 🔧 Tool used: {tool_info}")
                        
                        # Check for completion
                        if 'completed' in data or 'done' in data:
                            total_time = current_time
                            print(f"[{current_time:5.2f}s] ✅ Response complete")
                            
                    except json.JSONDecodeError:
                        pass
        
        # Analysis Report
        print_section("DELEGATION ANALYSIS REPORT")
        
        print("📊 TIMING ANALYSIS:")
        print(f"  • Total response time: {time.time() - start_time:.2f}s")
        if first_chunk_time:
            print(f"  • Time to first response: {first_chunk_time:.2f}s")
        if delegation_time:
            print(f"  • Time to delegation: {delegation_time:.2f}s")
        if sub_agent_start and sub_agent_end:
            print(f"  • Sub-agent work duration: {sub_agent_end - sub_agent_start:.2f}s")
        
        print("\n🤖 AGENT BEHAVIOR:")
        print(f"  • Delegation detected: {'YES' if delegation_detected else 'NO'}")
        print(f"  • Sub-agent worked: {'YES' if sub_agent_working else 'NO'}")
        print(f"  • Main agent continued during delegation: {'YES' if conversation_continues else 'NO'}")
        
        print("\n📝 ACTIVITY SUMMARY:")
        print(f"  • Main agent chunks: {len(main_agent_chunks)}")
        print(f"  • Sub-agent activities: {len(sub_agent_activity)}")
        print(f"  • Status changes: {len(statuses)}")
        print(f"  • Tools used: {len(tools_used)}")
        
        if tools_used:
            print("\n🔧 TOOLS BREAKDOWN:")
            for t, tool in tools_used:
                print(f"  [{t:5.2f}s] {tool}")
        
        return delegation_detected
        
    except requests.exceptions.Timeout:
        print("\n⏱️ Request timed out - might be processing complex query")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def test_multi_turn_conversation():
    """Test multi-turn conversation with delegation"""
    print_section("MULTI-TURN CONVERSATION TEST")
    
    url = "http://localhost:8008/api/bsa/unified-stream"
    contractor_id = "test-contractor-multi"
    session_id = "multi-turn-test"
    
    conversations = [
        "I'm looking for projects in the 33442 area",
        "Can you search for turf installation opportunities?",
        "What about lawn care projects?",
        "Do you see any that need urgent work?"
    ]
    
    for i, message in enumerate(conversations, 1):
        payload = {
            "contractor_id": contractor_id,
            "message": message,
            "session_id": session_id  # Same session for context
        }
        
        print(f"\n🔄 TURN {i}/{len(conversations)}")
        delegation = monitor_stream(url, payload, f"Turn {i}")
        
        if delegation:
            print("  ✅ Delegation occurred in this turn")
        
        # Brief pause between turns
        time.sleep(2)

def test_sub_agent_questions():
    """Test if sub-agent can ask questions through main agent"""
    print_section("SUB-AGENT QUESTION FLOW TEST")
    
    url = "http://localhost:8008/api/bsa/unified-stream"
    
    # Message that might trigger sub-agent to need clarification
    payload = {
        "contractor_id": "test-contractor-question",
        "message": "Find projects but I only work with specific materials",
        "session_id": "question-test"
    }
    
    monitor_stream(url, payload, "Sub-Agent Question Test")

if __name__ == "__main__":
    print_section("BSA DELEGATION PROOF TEST SUITE")
    print("Testing real sub-agent delegation with timing and flow analysis")
    
    # Check backend
    try:
        health = requests.get("http://localhost:8008/health")
        if health.status_code == 200:
            print("✅ Backend running on port 8008")
        else:
            print("⚠️ Backend status:", health.status_code)
    except:
        print("❌ Backend not running!")
        exit(1)
    
    # Run tests
    print("\n" + "="*70)
    print("  STARTING COMPREHENSIVE TESTS")
    print("="*70)
    
    # Test 1: Single delegation with timing
    print_section("TEST 1: SINGLE DELEGATION WITH TIMING")
    payload = {
        "contractor_id": "test-timing",
        "message": "Search for turf installation projects near 33442",
        "session_id": "timing-test"
    }
    monitor_stream("http://localhost:8008/api/bsa/unified-stream", payload, "Delegation Timing Test")
    
    # Test 2: Multi-turn conversation
    test_multi_turn_conversation()
    
    # Test 3: Sub-agent questions
    test_sub_agent_questions()
    
    print_section("ALL TESTS COMPLETE")
    print("Check the analysis above for proof of delegation behavior")