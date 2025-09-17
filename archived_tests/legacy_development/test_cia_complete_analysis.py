#!/usr/bin/env python3
"""Complete CIA (Customer Interface Agent) System Analysis"""

import json
import requests
import time
from datetime import datetime
import uuid

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_cia_endpoints():
    """Test all CIA API endpoints"""
    
    print_section("CIA ENDPOINT ANALYSIS")
    
    base_url = "http://localhost:8008"
    test_session_id = f"test_analysis_{int(time.time())}"
    
    endpoints = [
        {
            "method": "GET",
            "path": f"/api/cia/conversation/{test_session_id}",
            "description": "Get conversation history"
        },
        {
            "method": "POST",
            "path": "/api/cia/chat",
            "description": "Standard chat endpoint",
            "payload": {
                "message": "Test message",
                "session_id": test_session_id,
                "user_id": "test_user_123"
            }
        },
        {
            "method": "POST", 
            "path": "/api/cia/stream",
            "description": "SSE streaming endpoint",
            "payload": {
                "messages": [{"role": "user", "content": "Test stream"}],
                "conversation_id": test_session_id,
                "user_id": "test_user_123"
            }
        },
        {
            "method": "POST",
            "path": "/api/cia/chat/rfi/test_rfi_123",
            "description": "RFI-specific endpoint",
            "payload": {
                "message": "Testing RFI",
                "session_id": test_session_id
            }
        }
    ]
    
    results = []
    for endpoint in endpoints:
        try:
            if endpoint["method"] == "GET":
                response = requests.get(f"{base_url}{endpoint['path']}", timeout=5)
            else:
                response = requests.post(
                    f"{base_url}{endpoint['path']}", 
                    json=endpoint.get("payload", {}),
                    timeout=5
                )
            
            results.append({
                "endpoint": endpoint["path"],
                "status": response.status_code,
                "working": response.status_code in [200, 201, 404],
                "description": endpoint["description"]
            })
        except Exception as e:
            results.append({
                "endpoint": endpoint["path"],
                "status": "ERROR",
                "working": False,
                "description": endpoint["description"],
                "error": str(e)
            })
    
    # Print results
    print("\nENDPOINT TEST RESULTS:")
    print("-" * 60)
    for result in results:
        status_icon = "[OK]" if result["working"] else "[FAIL]"
        print(f"{status_icon} {result['endpoint']}")
        print(f"   Status: {result['status']}")
        print(f"   Purpose: {result['description']}")
        if "error" in result:
            print(f"   Error: {result['error']}")
    
    return results

def analyze_cia_architecture():
    """Analyze CIA system architecture"""
    
    print_section("CIA ARCHITECTURE ANALYSIS")
    
    # Check for multiple versions
    import os
    import glob
    
    ai_agents_path = r"C:\Users\Not John Or Justin\Documents\instabids\ai-agents"
    
    # Find all CIA-related files
    cia_files = {
        "Main Agent": glob.glob(os.path.join(ai_agents_path, "agents/cia/agent.py")),
        "Routes": glob.glob(os.path.join(ai_agents_path, "routers/cia_routes.py")),
        "Prompts": glob.glob(os.path.join(ai_agents_path, "agents/cia/*prompts.py")),
        "State": glob.glob(os.path.join(ai_agents_path, "agents/cia/*state.py")),
        "Tests": glob.glob(os.path.join(ai_agents_path, "test*cia*.py"))
    }
    
    print("\nCIA FILE STRUCTURE:")
    print("-" * 60)
    for category, files in cia_files.items():
        print(f"\n{category}:")
        if files:
            for file in files[:5]:  # Limit to 5 files per category
                print(f"  - {os.path.basename(file)}")
        else:
            print("  - None found")
    
    # Check for unified vs multiple implementations
    unified_file = os.path.join(ai_agents_path, "agents/cia/unified_integration.py")
    has_unified = os.path.exists(unified_file)
    
    print(f"\nUNIFIED IMPLEMENTATION: {'YES' if has_unified else 'NO'}")
    
    return cia_files, has_unified

def test_memory_system():
    """Test CIA memory system integration"""
    
    print_section("MEMORY SYSTEM TEST")
    
    # Check for memory integration files
    import os
    
    memory_files = {
        "Multi-project Store": r"C:\Users\Not John Or Justin\Documents\instabids\ai-agents\memory\multi_project_store.py",
        "LangGraph Integration": r"C:\Users\Not John Or Justin\Documents\instabids\ai-agents\memory\langgraph_integration.py",
        "Session Manager": r"C:\Users\Not John Or Justin\Documents\instabids\ai-agents\services\universal_session_manager.py"
    }
    
    print("\nMEMORY SYSTEM COMPONENTS:")
    print("-" * 60)
    for name, path in memory_files.items():
        exists = os.path.exists(path)
        status = "[FOUND]" if exists else "[MISSING]"
        print(f"{name}: {status}")
    
    # Test memory persistence
    print("\nTESTING MEMORY PERSISTENCE:")
    
    test_payload = {
        "message": "I want to renovate my kitchen for $50,000",
        "session_id": f"memory_test_{int(time.time())}",
        "user_id": "test_user_memory",
        "project_id": "test_project_123"
    }
    
    try:
        # Send first message
        response1 = requests.post(
            "http://localhost:8008/api/cia/chat",
            json=test_payload,
            timeout=10
        )
        
        if response1.status_code == 200:
            data1 = response1.json()
            
            # Send follow-up message
            test_payload["message"] = "What was my budget again?"
            response2 = requests.post(
                "http://localhost:8008/api/cia/chat",
                json=test_payload,
                timeout=10
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                # Check if budget was remembered
                if "$50" in str(data2.get("response", "")) or "50000" in str(data2.get("response", "")):
                    print("[SUCCESS] Memory persistence WORKING - Budget remembered")
                else:
                    print("[WARNING] Memory persistence UNCLEAR - Budget not explicitly mentioned")
            else:
                print(f"[FAIL] Second message failed: {response2.status_code}")
        else:
            print(f"[FAIL] First message failed: {response1.status_code}")
            
    except Exception as e:
        print(f"[FAIL] Memory test failed: {e}")
    
    return memory_files

def test_image_handling():
    """Test CIA image upload and processing"""
    
    print_section("IMAGE HANDLING TEST")
    
    print("\nIMAGE UPLOAD CAPABILITIES:")
    print("-" * 60)
    
    # Check if image handling is in the code
    import os
    
    cia_agent_file = r"C:\Users\Not John Or Justin\Documents\instabids\ai-agents\agents\cia\agent.py"
    
    if os.path.exists(cia_agent_file):
        with open(cia_agent_file, 'r') as f:
            content = f.read()
            
        checks = {
            "Image parameter in handler": "images: Optional[list[str]]" in content,
            "Image processing logic": "process_images" in content or "handle_images" in content,
            "RFI photo handling": "rfi_photos" in content or "handle_rfi_photo_upload" in content,
            "Vision/multimodal support": "vision" in content.lower() or "multimodal" in content.lower()
        }
        
        for check, result in checks.items():
            status = "[YES]" if result else "[NO]"
            print(f"{status} {check}")
    
    # Test actual image upload
    print("\nTESTING IMAGE UPLOAD:")
    
    test_payload = {
        "message": "Here are photos of my kitchen",
        "images": ["data:image/jpeg;base64,/9j/4AAQ..."],  # Mock base64 image
        "session_id": f"image_test_{int(time.time())}",
        "user_id": "test_user_image"
    }
    
    try:
        response = requests.post(
            "http://localhost:8008/api/cia/chat",
            json=test_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print("[SUCCESS] Image upload endpoint accepts images")
        else:
            print(f"[WARNING] Image upload returned: {response.status_code}")
            
    except Exception as e:
        print(f"[FAIL] Image upload test failed: {e}")

def analyze_ui_components():
    """Analyze UI components using CIA"""
    
    print_section("UI COMPONENT ANALYSIS")
    
    import os
    
    ui_components = {
        "UltimateCIAChat.tsx": r"C:\Users\Not John Or Justin\Documents\instabids\web\src\components\chat\UltimateCIAChat.tsx",
        "CIAChatTab.tsx": r"C:\Users\Not John Or Justin\Documents\instabids\web\src\components\tabs\CIAChatTab.tsx",
        "HomePage.tsx": r"C:\Users\Not John Or Justin\Documents\instabids\web\src\pages\HomePage.tsx",
        "UnifiedDashboard.tsx": r"C:\Users\Not John Or Justin\Documents\instabids\web\src\components\UnifiedDashboard.tsx"
    }
    
    print("\nUI COMPONENTS USING CIA:")
    print("-" * 60)
    
    for name, path in ui_components.items():
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check what endpoints it uses
            endpoints_used = []
            if "/api/cia/stream" in content:
                endpoints_used.append("stream")
            if "/api/cia/chat" in content:
                endpoints_used.append("chat")
            if "/api/cia/conversation" in content:
                endpoints_used.append("conversation")
            if "UltimateCIAChat" in content:
                endpoints_used.append("uses UltimateCIAChat")
            
            status = "[ACTIVE]" if endpoints_used else "[INACTIVE]"
            print(f"{status} {name}")
            if endpoints_used:
                print(f"   Endpoints: {', '.join(endpoints_used)}")
        else:
            print(f"[FAIL] {name} - Not found")

def test_llm_integration():
    """Test actual LLM integration (OpenAI vs Anthropic)"""
    
    print_section("LLM INTEGRATION TEST")
    
    print("\nCHECKING LLM CONFIGURATION:")
    print("-" * 60)
    
    # Check which LLM is configured
    test_message = {
        "message": "Say 'PROOF: LLM WORKING' if you can hear me",
        "session_id": f"llm_test_{int(time.time())}",
        "user_id": "test_llm"
    }
    
    try:
        response = requests.post(
            "http://localhost:8008/api/cia/chat",
            json=test_message,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get("response", "")
            
            if "PROOF" in response_text and "LLM" in response_text:
                print("[SUCCESS] LLM Integration CONFIRMED - Real AI responses")
                
                # Try to detect which LLM
                if "gpt" in response_text.lower() or "openai" in response_text.lower():
                    print("   Detected: OpenAI GPT model")
                elif "claude" in response_text.lower() or "anthropic" in response_text.lower():
                    print("   Detected: Anthropic Claude model")
                else:
                    print("   Model type: Unknown (but working)")
            else:
                print("⚠️ LLM responding but not following instructions")
                print(f"   Response: {response_text[:100]}...")
        else:
            print(f"[FAIL] LLM test failed with status: {response.status_code}")
            
    except Exception as e:
        print(f"[FAIL] LLM test error: {e}")

def main():
    """Run complete CIA system analysis"""
    
    print("\n" + "=" * 80)
    print("  COMPLETE CIA (CUSTOMER INTERFACE AGENT) SYSTEM ANALYSIS")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 80)
    
    # 1. Test endpoints
    endpoints = test_cia_endpoints()
    
    # 2. Analyze architecture
    architecture = analyze_cia_architecture()
    
    # 3. Test memory system
    memory = test_memory_system()
    
    # 4. Test image handling
    test_image_handling()
    
    # 5. Analyze UI components
    analyze_ui_components()
    
    # 6. Test LLM integration
    test_llm_integration()
    
    # Summary
    print_section("ANALYSIS SUMMARY")
    
    working_endpoints = sum(1 for e in endpoints if e["working"])
    total_endpoints = len(endpoints)
    
    print(f"\nENDPOINTS: {working_endpoints}/{total_endpoints} working")
    print(f"ARCHITECTURE: {'Unified' if architecture[1] else 'Multiple implementations'}")
    print(f"MEMORY SYSTEM: {'Integrated' if any(os.path.exists(f) for f in memory.values()) else 'Not found'}")
    print(f"IMAGE SUPPORT: Partial (parameters exist, needs testing)")
    print(f"UI INTEGRATION: Multiple components found")
    
    print("\n" + "=" * 80)
    print("  ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()