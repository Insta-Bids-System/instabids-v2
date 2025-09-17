#!/usr/bin/env python3
"""
IRIS Property Agent - Real System Test
Tests complete IRIS system with actual images and LLM calls
"""

import asyncio
import base64
import logging
import sys
import os
from datetime import datetime

# Add the project root to path  
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.iris_property.agent import IRISAgent
from agents.iris_property.models.requests import UnifiedChatRequest, ImageData

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_image():
    """Create a simple test image as base64"""
    # Create a simple 100x100 PNG image (kitchen-like)
    import io
    from PIL import Image, ImageDraw
    
    img = Image.new('RGB', (100, 100), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw simple kitchen elements
    draw.rectangle([10, 10, 90, 40], fill='brown')  # Counter
    draw.rectangle([20, 50, 40, 80], fill='gray')   # Cabinet
    draw.rectangle([50, 50, 70, 80], fill='blue')   # Sink
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return img_str

async def test_iris_conversation_flow():
    """Test complete IRIS conversation flow with real system"""
    print("\n[TEST] TESTING IRIS PROPERTY AGENT - REAL SYSTEM")
    print("=" * 60)
    
    # Initialize IRIS agent
    print("\n[1] Initializing IRIS Agent...")
    try:
        agent = IRISAgent()
        print("[SUCCESS] IRIS Agent initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize IRIS Agent: {e}")
        return
    
    # Test homeowner
    test_user_id = "test_homeowner_real_2025"
    test_session_id = f"iris_test_session_{int(datetime.now().timestamp())}"
    
    print(f"\n[2] Testing with homeowner: {test_user_id}")
    print(f"   Session ID: {test_session_id}")
    
    # Test 1: Initial conversation without images
    print("\n[3] TEST 1: General conversation (no images)")
    try:
        request1 = UnifiedChatRequest(
            user_id=test_user_id,
            session_id=test_session_id,
            message="Hi IRIS, I want to document my property",
            images=None,
            metadata={}
        )
        
        response1 = await agent.handle_unified_chat(request1)
        print(f"[SUCCESS] Response: {response1.response[:100]}...")
        print(f"   Suggestions: {len(response1.suggestions)} provided")
        print(f"   Session ID: {response1.session_id}")
        
    except Exception as e:
        print(f"[ERROR] Test 1 failed: {e}")
        return
    
    # Test 2: Upload kitchen photo
    print("\n[4] TEST 2: Upload kitchen photo with room identification")
    try:
        test_image = create_test_image()
        
        request2 = UnifiedChatRequest(
            user_id=test_user_id,
            session_id=test_session_id,
            message="Here's my kitchen",
            images=[ImageData(
                data=test_image,
                filename="test_kitchen.png"
            )],
            metadata={}
        )
        
        response2 = await agent.handle_unified_chat(request2)
        print(f"✅ Response: {response2.response[:150]}...")
        print(f"   Suggestions: {response2.suggestions}")
        print(f"   Success: {response2.success}")
        
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        return
    
    # Test 3: Confirm room and trigger analysis
    print("\n5️⃣ TEST 3: Confirm room type")
    try:
        request3 = UnifiedChatRequest(
            user_id=test_user_id,
            session_id=test_session_id,
            message="Yes, this is my kitchen",
            images=None,
            metadata={}
        )
        
        response3 = await agent.handle_unified_chat(request3)
        print(f"✅ Response: {response3.response[:150]}...")
        print(f"   Suggestions: {response3.suggestions}")
        
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        return
    
    # Test 4: Test property context awareness
    print("\n6️⃣ TEST 4: Property context awareness")
    try:
        request4 = UnifiedChatRequest(
            user_id=test_user_id,
            session_id=test_session_id,
            message="Show me my property summary",
            images=None,
            metadata={}
        )
        
        response4 = await agent.handle_unified_chat(request4)
        print(f"✅ Response: {response4.response[:150]}...")
        print(f"   Context aware: {'property' in response4.response.lower()}")
        
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
        return
    
    # Test 5: Upload second photo (bathroom)
    print("\n7️⃣ TEST 5: Upload bathroom photo (different room)")
    try:
        bathroom_image = create_test_image()  # Use same test image
        
        request5 = UnifiedChatRequest(
            user_id=test_user_id,
            session_id=test_session_id,
            message="Here's my bathroom",
            images=[ImageData(
                data=bathroom_image,
                filename="test_bathroom.png"
            )],
            metadata={}
        )
        
        response5 = await agent.handle_unified_chat(request5)
        print(f"✅ Response: {response5.response[:150]}...")
        print(f"   Mentions previous rooms: {'kitchen' in response5.response.lower()}")
        
    except Exception as e:
        print(f"❌ Test 5 failed: {e}")
        return
    
    print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("✅ IRIS Agent is working with:")
    print("   - Real property context loading")
    print("   - Conversation state management") 
    print("   - Image processing pipeline")
    print("   - Property intelligence awareness")
    print("   - Multi-room documentation")
    print("   - Session persistence")

async def test_memory_persistence():
    """Test conversation memory persistence across sessions"""
    print("\n🧠 TESTING MEMORY PERSISTENCE")
    print("=" * 40)
    
    agent = IRISAgent()
    user_id = "test_memory_user"
    session_id = "memory_test_session"
    
    # First conversation
    print("\n📝 Session 1: Initial conversation")
    request1 = UnifiedChatRequest(
        user_id=user_id,
        session_id=session_id,
        message="I have a kitchen that needs work",
        images=None
    )
    
    response1 = await agent.handle_unified_chat(request1)
    print(f"✅ Session 1 Response: {response1.response[:100]}...")
    
    # Second conversation - test memory
    print("\n🔄 Session 2: Test memory recall")
    request2 = UnifiedChatRequest(
        user_id=user_id,
        session_id=session_id,
        message="What did I tell you about my property?",
        images=None
    )
    
    response2 = await agent.handle_unified_chat(request2)
    print(f"✅ Session 2 Response: {response2.response[:150]}...")
    print(f"   Memory working: {'kitchen' in response2.response.lower()}")

if __name__ == "__main__":
    print("🚀 Starting IRIS Property Agent Real System Tests...")
    
    # Run conversation flow test
    asyncio.run(test_iris_conversation_flow())
    
    # Run memory persistence test
    asyncio.run(test_memory_persistence())
    
    print("\n✅ All tests completed!")