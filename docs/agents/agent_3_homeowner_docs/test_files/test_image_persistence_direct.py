"""
Test image persistence service directly
"""

import asyncio
import os
import sys

# Add the ai-agents directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-agents'))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_persistence():
    try:
        from services.image_persistence_service import image_service
        
        print("Testing image persistence service...")
        print(f"Service role key exists: {bool(os.getenv('SUPABASE_SERVICE_ROLE_KEY'))}")
        print(f"Anon key exists: {bool(os.getenv('SUPABASE_ANON_KEY'))}")
        
        # Test with one of the OpenAI URLs
        test_url = "https://oaidalleapiprodscus.blob.core.windows.net/private/org-XbuLu3W08vzqjwSOLNAQHWLb/user-ulYaQfAoRoaE5j0IF3KcRnA1/img-dP5BbOTjC9UTTWAXCzGr0Cnn.png?st=2025-08-04T22%3A23%3A33Z&se=2025-08-05T00%3A23%3A33Z&sp=r&sv=2024-08-04&sr=b&rscd=inline&rsct=image/png&skoid=8b33a531-2df9-46a3-bc02-d4b1430a422c&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2025-08-04T14%3A08%3A49Z&ske=2025-08-05T14%3A08%3A49Z&sks=b&skv=2024-08-04&sig=sjTm56Dlk4x4JF8LZoGUcGW/BnrdtVKSwNJFHE9IJos%3D"
        test_id = "83115cd8-0aa1-4d0f-b746-f8386dec1c4b"
        
        print(f"\nTesting with image ID: {test_id}")
        print("Attempting to make image persistent...")
        
        result = await image_service.make_image_persistent(test_id, test_url)
        
        if result:
            print(f"\nSUCCESS! Image made persistent!")
            print(f"New URL: {result}")
        else:
            print("\nFAILED to make image persistent")
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_persistence())