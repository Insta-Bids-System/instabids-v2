import asyncio
import aiohttp
import json
import base64

async def test_backend_with_image():
    """Test backend with image upload to diagnose crash"""
    
    # Read test image
    with open(r"C:\Users\Not John Or Justin\Documents\instabids\test-images\current-state\kitchen-outdated-1.webp", "rb") as f:
        image_data = f.read()
        base64_image = f"data:image/webp;base64,{base64.b64encode(image_data).decode('utf-8')}"
    
    # Test API endpoint
    url = "http://localhost:8008/api/cia/chat"
    
    # Create session
    session_id = f"test_session_{int(asyncio.get_event_loop().time() * 1000)}"
    
    # Message 1 - Simple text
    print("Sending message 1...")
    payload1 = {
        "message": "I need help with a kitchen renovation",
        "images": [],
        "session_id": session_id
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload1) as response:
            result1 = await response.json()
            print(f"Response 1: {result1['response'][:100]}...")
    
    # Message 2 - Simple text  
    print("\nSending message 2...")
    payload2 = {
        "message": "It's about 200 sq ft, needs complete remodel",
        "images": [],
        "session_id": session_id
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload2) as response:
            result2 = await response.json()
            print(f"Response 2: {result2['response'][:100]}...")
    
    # Message 3 - With image
    print("\nSending message 3 with image...")
    payload3 = {
        "message": "Here's a photo of my current kitchen",
        "images": [base64_image],
        "session_id": session_id
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload3, timeout=aiohttp.ClientTimeout(total=30)) as response:
                result3 = await response.json()
                print(f"Response 3: {result3['response'][:100]}...")
    except Exception as e:
        print(f"ERROR on message 3: {type(e).__name__}: {e}")
        
        # Try to check if server is still alive
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8008/") as response:
                    health = await response.json()
                    print(f"Server still alive: {health}")
        except:
            print("Server appears to be down!")

if __name__ == "__main__":
    asyncio.run(test_backend_with_image())