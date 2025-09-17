#!/usr/bin/env python3
"""
Test improved CIA field extraction with progressive updates
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

def send_message_and_consume_stream(session_id, user_id, message):
    """Send message and consume full response stream"""
    request_data = {
        "messages": [{"role": "user", "content": message}],
        "user_id": user_id,
        "session_id": session_id,
        "conversation_id": session_id
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/cia/stream",
            json=request_data,
            timeout=30,
            stream=True
        )
        
        if response.status_code == 200:
            # Consume stream until [DONE]
            for line in response.iter_lines():
                if line and "[DONE]" in line.decode():
                    break
            return "✅ Stream consumed"
        else:
            return f"❌ Failed: {response.status_code}"
    except Exception as e:
        return f"❌ Error: {e}"

def get_bid_card_fields(session_id):
    """Get current bid card state"""
    try:
        response = requests.get(f"{BASE_URL}/api/cia/conversation/{session_id}/potential-bid-card")
        if response.status_code == 200:
            data = response.json()
            fields = data.get('fields_collected', {})
            filled = {k: v for k, v in fields.items() if v not in [None, "", [], {}]}
            return {
                'completion': data.get('completion_percentage', 0),
                'filled_fields': filled,
                'field_count': len(filled),
                'id': data.get('id')
            }
        return None
    except:
        return None

def print_field_changes(before, after, turn_num):
    """Print field changes between turns"""
    before_fields = before['filled_fields'] if before else {}
    after_fields = after['filled_fields'] if after else {}
    
    before_completion = before['completion'] if before else 0
    after_completion = after['completion'] if after else 0
    
    print(f"\n📊 TURN {turn_num} FIELD ANALYSIS:")
    print(f"   Completion: {before_completion}% → {after_completion}%")
    print(f"   Field Count: {len(before_fields)} → {len(after_fields)}")
    
    # Show new fields
    for field, value in after_fields.items():
        if field not in before_fields:
            print(f"   ✅ NEW: {field} = {value}")
        elif before_fields[field] != value:
            print(f"   🔄 UPDATED: {field} = {before_fields[field]} → {value}")

def test_progressive_field_extraction():
    """Test progressive field extraction with strategic messages"""
    session_id = str(uuid.uuid4())
    user_id = "00000000-0000-0000-0000-000000000000"
    
    print("=" * 70)
    print("🧪 CIA PROGRESSIVE FIELD EXTRACTION TEST")
    print("=" * 70)
    print(f"Session ID: {session_id}")
    
    # Strategic conversation turns designed to progressively build detailed bid card
    turns = [
        {
            "message": "I need bathroom renovation in Manhattan 10001",
            "description": "Initial: project type, location, zip code",
            "expected_fields": ["project_type", "zip_code", "location"]
        },
        {
            "message": "Budget is $30,000 to $45,000, timeline is 6 weeks",
            "description": "Budget range and timeline",
            "expected_fields": ["budget_min", "budget_max", "timeline"]
        },
        {
            "message": "It's a master bathroom, about 100 square feet, currently outdated from the 1990s",
            "description": "Property details and condition",
            "expected_fields": ["property_type", "property_size", "current_condition"]
        },
        {
            "message": "I want marble countertops, subway tile shower, and premium fixtures", 
            "description": "Materials and quality preferences",
            "expected_fields": ["materials", "quality_expectations"]
        },
        {
            "message": "Need licensed contractors with insurance, prefer established local companies",
            "description": "Contractor requirements and preferences",
            "expected_fields": ["contractor_requirements", "contractor_size"]
        }
    ]
    
    previous_bid_card = None
    all_improvements = []
    
    for i, turn in enumerate(turns, 1):
        print(f"\n{'='*20} TURN {i}/5 {'='*20}")
        print(f"🎯 Expected Fields: {', '.join(turn['expected_fields'])}")
        print(f"💬 Message: {turn['message']}")
        
        # Send message
        result = send_message_and_consume_stream(session_id, user_id, turn['message'])
        print(f"📡 Stream: {result}")
        
        # Wait for state management
        time.sleep(4)
        
        # Get updated bid card
        current_bid_card = get_bid_card_fields(session_id)
        
        if current_bid_card:
            print_field_changes(previous_bid_card, current_bid_card, i)
            
            # Check if expected fields were extracted
            new_fields = []
            if previous_bid_card:
                for field in current_bid_card['filled_fields']:
                    if field not in previous_bid_card['filled_fields']:
                        new_fields.append(field)
            else:
                new_fields = list(current_bid_card['filled_fields'].keys())
            
            improvements = {
                'turn': i,
                'new_fields': new_fields,
                'expected_fields': turn['expected_fields'],
                'completion_gain': (current_bid_card['completion'] - (previous_bid_card['completion'] if previous_bid_card else 0))
            }
            all_improvements.append(improvements)
            
            # Check if we got expected fields
            found_expected = [f for f in turn['expected_fields'] if f in new_fields]
            if found_expected:
                print(f"   🎉 SUCCESS: Found expected fields: {found_expected}")
            else:
                print(f"   ⚠️  MISS: Expected {turn['expected_fields']}, got {new_fields}")
        else:
            print("   ❌ No bid card found")
            
        previous_bid_card = current_bid_card
    
    # Final analysis
    print(f"\n{'='*70}")
    print("🎯 PROGRESSIVE EXTRACTION ANALYSIS")
    print(f"{'='*70}")
    
    if current_bid_card:
        print(f"✅ FINAL RESULT:")
        print(f"   Bid Card ID: {current_bid_card['id']}")
        print(f"   Final Completion: {current_bid_card['completion']}%")
        print(f"   Total Fields: {current_bid_card['field_count']}")
        
        print(f"\n📋 ALL EXTRACTED FIELDS:")
        for field, value in current_bid_card['filled_fields'].items():
            print(f"   ✅ {field}: {value}")
        
        print(f"\n📈 TURN-BY-TURN PROGRESSION:")
        total_new_fields = 0
        for improvement in all_improvements:
            turn_num = improvement['turn']
            new_count = len(improvement['new_fields'])
            expected_count = len(improvement['expected_fields'])
            completion_gain = improvement['completion_gain']
            
            total_new_fields += new_count
            print(f"   Turn {turn_num}: +{new_count} fields ({completion_gain:+.0f}% completion)")
            print(f"            Expected: {expected_count}, Got: {new_count}")
        
        # Success criteria
        success_criteria = {
            'final_completion': current_bid_card['completion'] >= 70,
            'total_fields': current_bid_card['field_count'] >= 8,
            'progressive_updates': total_new_fields >= 8,
            'specific_extraction': any('bathroom' in str(v) for v in current_bid_card['filled_fields'].values())
        }
        
        passing_criteria = sum(success_criteria.values())
        print(f"\n🎯 SUCCESS CRITERIA: {passing_criteria}/4 PASSED")
        for criterion, passed in success_criteria.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {criterion}: {passed}")
        
        if passing_criteria >= 3:
            print(f"\n🎉 PROGRESSIVE EXTRACTION TEST PASSED!")
            print(f"✅ CIA builds detailed bid cards through conversation")
            print(f"✅ Field extraction works progressively")
            print(f"✅ Specific information correctly captured")
            return True
        else:
            print(f"\n⚠️  PROGRESSIVE EXTRACTION TEST NEEDS IMPROVEMENT")
            print(f"Need at least 3/4 success criteria")
            return False
    else:
        print("❌ FAILED: No bid card created")
        return False

def main():
    print("🚀 Testing progressive CIA field extraction")
    success = test_progressive_field_extraction()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 PROGRESSIVE FIELD EXTRACTION TEST PASSED!")
        print("✅ Real-time bid card updates working correctly")
    else:
        print("❌ PROGRESSIVE FIELD EXTRACTION TEST FAILED!")
        print("⚠️  Field extraction or update logic needs fixes")

if __name__ == "__main__":
    main()