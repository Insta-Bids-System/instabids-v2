"""
Manual CIA Flow Test with Proper UUIDs
Test conversation -> bid card creation -> memory with correct UUID format
"""
import requests
import json
import uuid

def test_cia_with_proper_uuid():
    """Test CIA conversation with proper UUID session format"""
    
    # Generate proper UUIDs
    session_id = str(uuid.uuid4())
    user_id = "00000000-0000-0000-0000-000000000000"
    
    print("Manual CIA Test with Proper UUIDs")
    print("=" * 50)
    print(f"Session ID: {session_id}")
    print(f"User ID: {user_id}")
    
    # Test message about deck rebuilding
    test_message = "My deck is falling apart and needs to be rebuilt in Manhattan, NY 10001. It's about 12x16 feet and completely unsafe."
    print(f"Message: {test_message}")
    
    # Prepare request with proper UUID format
    request_data = {
        "messages": [{"role": "user", "content": test_message}],
        "user_id": user_id,
        "session_id": session_id,
        "conversation_id": session_id
    }
    
    try:
        print("\nSending to CIA streaming endpoint...")
        response = requests.post(
            "http://localhost:8008/api/cia/stream",
            json=request_data,
            timeout=20
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("\nProcessing streaming response...")
            
            full_response = ""
            chunk_count = 0
            
            for line in response.text.split('\n'):
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        if data.get('content'):
                            full_response += data['content']
                            chunk_count += 1
                    except:
                        continue
            
            print(f"Received {chunk_count} chunks")
            print(f"Response length: {len(full_response)} characters")
            print("\nCIA Response Preview:")
            print("-" * 30)
            print(full_response[:300] + "..." if len(full_response) > 300 else full_response)
            
            # Check if response mentions key pain points
            pain_points_found = []
            pain_points = [
                "photo", "neighbor", "group", "save", "privacy", "sales"
            ]
            
            for point in pain_points:
                if point.lower() in full_response.lower():
                    pain_points_found.append(point)
            
            print(f"\nPain points mentioned: {pain_points_found}")
            
            # Check for potential bid card creation
            if any(keyword in full_response.lower() for keyword in ['project', 'contractor', 'quote', 'bid']):
                print("✅ Response shows bid card context")
                
                # Now check if potential bid card was created
                print("\nChecking for potential bid card...")
                time.sleep(2)  # Give it time to process
                
                bid_card_response = requests.get(f"http://localhost:8008/api/cia/conversation/{session_id}/potential-bid-card")
                
                if bid_card_response.status_code == 200:
                    bid_data = bid_card_response.json()
                    print("✅ Potential bid card created!")
                    print(f"  Completion: {bid_data.get('completion_percentage', 0)}%")
                    print(f"  Fields: {list(bid_data.get('fields_collected', {}).keys())}")
                    
                    return session_id, bid_data.get('id')
                else:
                    print(f"❌ No bid card found: {bid_card_response.status_code}")
                    return session_id, None
            else:
                print("⚠️ Response doesn't show bid card context")
                return session_id, None
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print("Response:", response.text[:500])
            return None, None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None

def test_opening_message_frontend():
    """Test that opening message shows new pain-point approach"""
    print("\n" + "=" * 50)
    print("TESTING OPENING MESSAGE (Should Show New Pain Points)")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8008/api/cia/opening-message")
        if response.status_code == 200:
            data = response.json()
            message = data.get('message', '')
            
            # Check for new pain-point elements
            new_elements = [
                "Save 10-25%",
                "Photos = Accurate Quotes",
                "Group Bidding = 15-25% MORE Savings", 
                "Zero Sales Pressure",
                "AI That Remembers Everything"
            ]
            
            print("Opening message verification:")
            for element in new_elements:
                if element in message:
                    print(f"  ✅ {element}")
                else:
                    print(f"  ❌ {element} - MISSING")
            
            # Check that old elements are gone
            old_elements = ["Alex", "AI project assistant"]
            for old_element in old_elements:
                if old_element in message:
                    print(f"  ⚠️  Still contains old element: {old_element}")
                    
            print(f"\nMessage length: {len(message)} characters")
            return True
        else:
            print(f"❌ API failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    import time
    
    # Test 1: Opening message verification
    opening_works = test_opening_message_frontend()
    
    # Test 2: Full conversation flow
    session_id, bid_card_id = test_cia_with_proper_uuid()
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Opening message: {'✅ Working' if opening_works else '❌ Failed'}")
    print(f"CIA conversation: {'✅ Working' if session_id else '❌ Failed'}")
    print(f"Bid card creation: {'✅ Working' if bid_card_id else '❌ Failed'}")
    
    if session_id and bid_card_id:
        print(f"\nNext steps:")
        print(f"1. Use session {session_id} to continue conversation")
        print(f"2. Use bid card {bid_card_id} for signup flow")
        print(f"3. Test memory persistence with returning user")