#!/usr/bin/env python3
"""
Test IRIS Board Management and Organization Features
Tests board creation, organization, and design preference extraction
"""

import requests
import json
import time

def test_iris_board_management():
    """Test IRIS board management and organization features"""
    
    print("IRIS BOARD MANAGEMENT TEST")
    print("=" * 50)
    
    # Test session
    session_id = f"iris_board_test_{int(time.time())}"
    user_id = f"homeowner_{int(time.time())}"
    
    print(f"Session: {session_id}")
    print(f"Homeowner: {user_id}")
    print("-" * 50)
    
    # Test 1: Create inspiration board with collecting status
    print("\nTEST 1: Board Creation - Collecting Phase")
    
    collecting_msg = {
        "message": "I'm starting a modern kitchen renovation and collecting inspiration. Here are some images I love!",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "kitchen",
        "board_id": "board_kitchen_modern_001",
        "board_title": "Modern Kitchen Renovation",
        "board_description": "Collecting inspiration for a complete kitchen makeover",
        "board_status": "collecting",
        "uploaded_images": ["modern_kitchen_1.jpg", "modern_kitchen_2.jpg"]
    }
    
    try:
        response1 = requests.post("http://localhost:8008/api/iris/chat", json=collecting_msg, timeout=30)
        
        if response1.status_code == 200:
            result1 = response1.json()
            print("SUCCESS: IRIS processed collecting phase board")
            print(f"Response: {result1['response'][:150]}...")
            print(f"Suggestions: {result1['suggestions']}")
            
            # Check for collecting-phase specific suggestions
            suggestions = result1['suggestions']
            collecting_keywords = ['organize', 'style', 'similar', 'palette']
            if any(any(keyword in suggestion.lower() for keyword in collecting_keywords) for suggestion in suggestions):
                print("GOOD: IRIS provided collecting-phase appropriate suggestions")
            else:
                print("NOTE: Suggestions may not be collecting-phase specific")
                
            conversation_id = result1.get('conversation_id')
        else:
            print(f"FAILED: Status {response1.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    
    time.sleep(3)
    
    # Test 2: Organizing phase - ask for help organizing images
    print("\nTEST 2: Board Organization - Organizing Phase")
    
    organizing_msg = {
        "message": "I have 15 kitchen images now but they're all mixed up. Can you help me organize them by categories?",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "kitchen",
        "board_id": "board_kitchen_modern_001",
        "board_title": "Modern Kitchen Renovation",
        "board_status": "organizing"
    }
    
    try:
        response2 = requests.post("http://localhost:8008/api/iris/chat", json=organizing_msg, timeout=30)
        
        if response2.status_code == 200:
            result2 = response2.json()
            print("SUCCESS: IRIS provided organization guidance")
            print(f"Response: {result2['response'][:200]}...")
            print(f"Suggestions: {result2['suggestions']}")
            
            # Check for organization categories in response
            response_text = result2['response'].lower()
            organization_keywords = ['cabinet', 'countertop', 'hardware', 'layout', 'category', 'group']
            found_categories = [keyword for keyword in organization_keywords if keyword in response_text]
            
            print(f"Organization categories mentioned: {found_categories}")
            
            if len(found_categories) >= 3:
                print("EXCELLENT: IRIS provided comprehensive organization categories")
            elif len(found_categories) >= 1:
                print("GOOD: IRIS provided some organization guidance")
            else:
                print("NOTE: Organization categories may not be explicit")
                
        else:
            print(f"FAILED: Status {response2.status_code}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    time.sleep(3)
    
    # Test 3: Refining phase - create vision summary
    print("\nTEST 3: Board Refinement - Refining Phase")
    
    refining_msg = {
        "message": "I've organized my inspiration into categories. Can you help me create a clear vision summary for contractors?",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "kitchen",
        "board_id": "board_kitchen_modern_001",
        "board_title": "Modern Kitchen Renovation",
        "board_status": "refining"
    }
    
    try:
        response3 = requests.post("http://localhost:8008/api/iris/chat", json=refining_msg, timeout=30)
        
        if response3.status_code == 200:
            result3 = response3.json()
            print("SUCCESS: IRIS provided vision summary guidance")
            print(f"Response: {result3['response'][:200]}...")
            print(f"Suggestions: {result3['suggestions']}")
            
            # Check for contractor-ready elements
            response_text = result3['response'].lower()
            contractor_keywords = ['contractor', 'summary', 'budget', 'priority', 'vision', 'requirements']
            found_elements = [keyword for keyword in contractor_keywords if keyword in response_text]
            
            print(f"Contractor-ready elements mentioned: {found_elements}")
            
            # Check suggestions for CIA agent connection
            suggestions_text = ' '.join(result3['suggestions']).lower()
            if 'cia' in suggestions_text or 'connect' in suggestions_text or 'project' in suggestions_text:
                print("EXCELLENT: IRIS suggested connecting with CIA agent")
            else:
                print("NOTE: CIA agent connection not explicitly suggested")
                
        else:
            print(f"FAILED: Status {response3.status_code}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    time.sleep(3)
    
    # Test 4: Design preference extraction test
    print("\nTEST 4: Design Preference Extraction")
    
    preference_msg = {
        "message": "I love modern farmhouse style with white shaker cabinets, black hardware, marble countertops, and warm wood accents. My budget is around $35,000-45,000.",
        "user_id": user_id,
        "session_id": session_id,
        "room_type": "kitchen",
        "board_id": "board_kitchen_modern_001",
        "board_title": "Modern Kitchen Renovation"
    }
    
    try:
        response4 = requests.post("http://localhost:8008/api/iris/chat", json=preference_msg, timeout=30)
        
        if response4.status_code == 200:
            result4 = response4.json()
            print("SUCCESS: IRIS processed design preferences")
            print(f"Response: {result4['response'][:200]}...")
            
            # Check if IRIS extracted key preferences
            response_text = result4['response'].lower()
            
            extracted_elements = {
                'style': any(style in response_text for style in ['modern farmhouse', 'farmhouse', 'modern']),
                'cabinets': 'white' in response_text and 'shaker' in response_text,
                'hardware': 'black' in response_text and 'hardware' in response_text,
                'countertops': 'marble' in response_text,
                'accents': 'wood' in response_text,
                'budget': any(budget in response_text for budget in ['35', '45', 'budget'])
            }
            
            print("Preference extraction results:")
            for element, extracted in extracted_elements.items():
                status = "YES" if extracted else "NO"
                print(f"  {element}: {status}")
            
            extracted_count = sum(extracted_elements.values())
            if extracted_count >= 4:
                print("EXCELLENT: IRIS extracted most design preferences")
            elif extracted_count >= 2:
                print("GOOD: IRIS extracted some design preferences")
            else:
                print("NOTE: IRIS may not be explicitly extracting preferences")
                
        else:
            print(f"FAILED: Status {response4.status_code}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 5: Board status progression test
    print("\nTEST 5: Board Status Progression Test")
    
    status_progression = ["collecting", "organizing", "refining", "ready"]
    
    for status in status_progression:
        test_msg = {
            "message": f"My board is now in {status} status. What should I focus on next?",
            "user_id": user_id,
            "session_id": f"{session_id}_{status}",
            "room_type": "kitchen",
            "board_status": status
        }
        
        try:
            response = requests.post("http://localhost:8008/api/iris/chat", json=test_msg, timeout=20)
            
            if response.status_code == 200:
                result = response.json()
                suggestions = result.get('suggestions', [])
                
                print(f"Status '{status}' - Suggestions: {suggestions}")
                
                # Check if suggestions match the status
                suggestions_text = ' '.join(suggestions).lower()
                
                if status == "collecting":
                    appropriate = any(word in suggestions_text for word in ['organize', 'style', 'color'])
                elif status == "organizing":
                    appropriate = any(word in suggestions_text for word in ['group', 'identify', 'mood'])
                elif status == "refining":
                    appropriate = any(word in suggestions_text for word in ['summary', 'budget', 'priority'])
                elif status == "ready":
                    appropriate = any(word in suggestions_text for word in ['connect', 'cia', 'start'])
                else:
                    appropriate = False
                
                if appropriate:
                    print(f"  GOOD: Suggestions appropriate for {status} status")
                else:
                    print(f"  NOTE: Suggestions may not be status-specific")
                    
        except Exception as e:
            print(f"  ERROR for {status}: {e}")
    
    print("\n" + "=" * 50)
    print("IRIS BOARD MANAGEMENT TEST COMPLETE")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    test_iris_board_management()