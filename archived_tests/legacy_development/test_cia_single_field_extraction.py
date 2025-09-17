#!/usr/bin/env python3
"""
Simple test: One CIA conversation turn to test improved field extraction
"""
import requests
import json
import uuid
import sys
import io
import time

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8008"

def test_single_extraction():
    """Test single conversation turn with detailed message"""
    session_id = str(uuid.uuid4())
    user_id = "00000000-0000-0000-0000-000000000000"
    
    print("🧪 CIA SINGLE FIELD EXTRACTION TEST")
    print(f"Session ID: {session_id}")
    
    # Detailed message with multiple extractable fields
    message = "I need bathroom renovation in Manhattan 10001, budget $30,000 to $45,000, timeline 6 weeks, marble countertops"
    
    print(f"💬 Message: {message}")
    
    request_data = {
        "messages": [{"role": "user", "content": message}],
        "user_id": user_id,
        "session_id": session_id,
        "conversation_id": session_id
    }
    
    try:
        print("📡 Sending request...")
        response = requests.post(
            f"{BASE_URL}/api/cia/stream",
            json=request_data,
            timeout=45,
            stream=True
        )
        
        if response.status_code == 200:
            print("✅ Stream started, consuming...")
            # Consume stream until [DONE]
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    chunk_count += 1
                    if "[DONE]" in line.decode():
                        print(f"✅ Stream completed ({chunk_count} chunks)")
                        break
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Wait for state management
    print("⏳ Waiting for state management...")
    time.sleep(5)
    
    # Check bid card
    try:
        print("📋 Checking bid card...")
        response = requests.get(f"{BASE_URL}/api/cia/conversation/{session_id}/potential-bid-card")
        if response.status_code == 200:
            data = response.json()
            fields = data.get('fields_collected', {})
            filled = {k: v for k, v in fields.items() if v not in [None, "", [], {}]}
            completion = data.get('completion_percentage', 0)
            
            print(f"✅ BID CARD CREATED!")
            print(f"   ID: {data.get('id')}")
            print(f"   Completion: {completion}%")
            print(f"   Fields: {len(filled)}")
            
            print(f"\n📋 EXTRACTED FIELDS:")
            for field, value in filled.items():
                print(f"   ✅ {field}: {value}")
            
            # Check for specific fields we expect
            expected_fields = {
                'project_type': 'bathroom',
                'zip_code': '10001', 
                'location': 'Manhattan',
                'budget_min': 30000,
                'budget_max': 45000,
                'timeline': '6 weeks',
                'materials': 'marble'
            }
            
            matches = 0
            print(f"\n🎯 EXTRACTION ACCURACY:")
            for field, expected in expected_fields.items():
                actual = filled.get(field)
                if actual and str(expected).lower() in str(actual).lower():
                    matches += 1
                    print(f"   ✅ {field}: Found '{expected}' in '{actual}'")
                else:
                    print(f"   ❌ {field}: Expected '{expected}', got '{actual}'")
            
            accuracy = (matches / len(expected_fields)) * 100
            print(f"\n📊 EXTRACTION ACCURACY: {accuracy:.0f}% ({matches}/{len(expected_fields)})")
            
            if accuracy >= 70 and len(filled) >= 5:
                print(f"\n🎉 EXTRACTION TEST PASSED!")
                print(f"✅ High accuracy field extraction working")
                print(f"✅ Specific information correctly captured")
                return True
            else:
                print(f"\n⚠️  EXTRACTION TEST NEEDS IMPROVEMENT")
                print(f"Need 70%+ accuracy and 5+ fields")
                return False
        else:
            print(f"❌ Failed to get bid card: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking bid card: {e}")
        return False

def main():
    print("🚀 Testing improved CIA field extraction")
    success = test_single_extraction()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 FIELD EXTRACTION TEST PASSED!")
    else:
        print("❌ FIELD EXTRACTION TEST FAILED!")

if __name__ == "__main__":
    main()