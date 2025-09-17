"""
Test the new opening message API endpoint
This allows the frontend to retrieve the pre-loaded opening message
"""
import requests
import json

# Test the opening message endpoint
def test_opening_message():
    try:
        response = requests.get("http://localhost:8008/api/cia/opening-message")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Opening Message API Working!")
            print("-" * 60)
            print("Success:", data.get("success"))
            print("Timestamp:", data.get("timestamp"))
            print("-" * 60)
            print("Message Preview (first 500 chars):")
            print(data.get("message", "")[:500] + "...")
            print("-" * 60)
            print("Full message length:", len(data.get("message", "")), "characters")
            
            # Verify it contains key pain points
            message = data.get("message", "")
            pain_points = [
                "Save 10-25%",
                "Photos = Accurate Quotes",
                "Group Bidding",
                "Zero Sales Pressure",
                "AI That Remembers"
            ]
            
            print("\nPain Point Verification:")
            for point in pain_points:
                if point in message:
                    print(f"  ✅ {point}")
                else:
                    print(f"  ❌ {point} - MISSING!")
                    
        else:
            print(f"❌ API returned status code: {response.status_code}")
            print("Response:", response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend at http://localhost:8008")
        print("Make sure the backend is running: cd ai-agents && python main.py")
    except Exception as e:
        print(f"❌ Error testing opening message API: {e}")

if __name__ == "__main__":
    print("Testing CIA Opening Message API Endpoint")
    print("=" * 60)
    test_opening_message()