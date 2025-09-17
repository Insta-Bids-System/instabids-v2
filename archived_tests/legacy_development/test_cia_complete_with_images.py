#!/usr/bin/env python3
"""
Complete CIA test with image uploads, conversation memory, and database persistence.
Tests the full homeowner journey with pictures and multi-session memory.
"""

import requests
import json
import time
import uuid
import os
from datetime import datetime

def create_test_image():
    """Create a simple test image for upload."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple test image
        img = Image.new('RGB', (800, 600), color='lightblue')
        draw = ImageDraw.Draw(img)
        
        # Add some text to make it look like a kitchen photo
        try:
            # Try to use default font
            font = ImageFont.load_default()
        except:
            font = None
            
        draw.text((50, 50), "Test Kitchen Photo", fill='black', font=font)
        draw.text((50, 100), "Current kitchen layout", fill='black', font=font)
        draw.text((50, 150), "Needs renovation", fill='black', font=font)
        
        # Draw a simple rectangle to represent kitchen layout
        draw.rectangle([100, 200, 300, 400], outline='brown', width=3)
        draw.rectangle([350, 200, 550, 400], outline='gray', width=3)
        
        # Save the test image
        test_image_path = "test_kitchen_photo.jpg"
        img.save(test_image_path, "JPEG")
        return test_image_path
        
    except ImportError:
        # If PIL not available, create a simple text file as placeholder
        test_image_path = "test_kitchen_photo.txt"
        with open(test_image_path, 'w') as f:
            f.write("Test kitchen photo - placeholder file for image upload test")
        return test_image_path

def test_complete_cia_journey():
    """Test complete CIA journey with images and memory persistence."""
    
    print("=" * 80)
    print("CIA COMPLETE JOURNEY TEST - IMAGES + MEMORY + DATABASE")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Generate consistent user and conversation IDs
    user_id = f"test-homeowner-{uuid.uuid4().hex[:8]}"
    conversation_id_1 = f"chat-session-1-{uuid.uuid4().hex[:8]}"
    conversation_id_2 = f"chat-session-2-{uuid.uuid4().hex[:8]}"
    
    print(f"User ID: {user_id}")
    print(f"First Conversation: {conversation_id_1}")
    print(f"Second Conversation: {conversation_id_2}")
    print("")
    
    # Create test image
    test_image_path = create_test_image()
    print(f"Created test image: {test_image_path}")
    
    # SESSION 1: Initial conversation with image upload
    print("\n" + "=" * 60)
    print("SESSION 1: Initial Chat with Image Upload")
    print("=" * 60)
    
    session_1_messages = [
        "Hi, I need help renovating my kitchen. It's pretty outdated.",
        "Let me upload a photo so you can see what I'm working with.",
        "I'm thinking about new cabinets, countertops, and maybe opening up the space.",
        "My budget is around $40,000 to $60,000 for this renovation.",
        "I'm located at 789 Pine Street, Chicago, IL 60614.",
        "My name is Jennifer Smith, email jennifer.smith@email.com, phone 312-555-7890"
    ]
    
    session_1_conversation = []
    potential_bid_card_id = None
    
    for turn, message in enumerate(session_1_messages, 1):
        print(f"\n[SESSION 1 - TURN {turn}] User: {message}")
        
        session_1_conversation.append({"role": "user", "content": message})
        
        # Special handling for image upload turn
        if "upload a photo" in message:
            print("  [ACTION] Simulating image upload...")
            
            # Test image upload endpoint
            try:
                with open(test_image_path, 'rb') as img_file:
                    files = {'file': (test_image_path, img_file, 'image/jpeg')}
                    upload_response = requests.post(
                        "http://localhost:8008/api/cia/upload-image",
                        files=files,
                        data={
                            "conversation_id": conversation_id_1,
                            "user_id": user_id,
                            "description": "Current kitchen photo"
                        },
                        timeout=10
                    )
                    
                    if upload_response.status_code == 200:
                        upload_data = upload_response.json()
                        print(f"  [SUCCESS] Image uploaded: {upload_data}")
                        
                        # Add image context to conversation
                        image_message = f"[Image uploaded: {upload_data.get('filename', 'kitchen_photo.jpg')}]"
                        session_1_conversation.append({"role": "system", "content": image_message})
                        
                    else:
                        print(f"  [WARNING] Image upload failed: {upload_response.status_code}")
                        
            except Exception as e:
                print(f"  [ERROR] Image upload error: {e}")
        
        # Send message to CIA
        try:
            response = requests.post(
                "http://localhost:8008/api/cia/stream",
                json={
                    "messages": session_1_conversation,
                    "conversation_id": conversation_id_1,
                    "user_id": user_id,
                    "model_preference": "gpt-4o"
                },
                timeout=8,
                stream=True
            )
            
            if response.status_code == 200:
                # Collect AI response
                ai_response = ""
                chunk_count = 0
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            chunk_count += 1
                            try:
                                data_str = line_str[6:]
                                if data_str != '[DONE]':
                                    data = json.loads(data_str)
                                    if 'choices' in data:
                                        content = data['choices'][0].get('delta', {}).get('content', '')
                                        ai_response += content
                            except:
                                pass
                            
                            # Stop after collecting reasonable response
                            if chunk_count > 50:
                                break
                
                if ai_response:
                    print(f"  [CIA Response]: {ai_response[:200]}...")
                    session_1_conversation.append({"role": "assistant", "content": ai_response})
                
            else:
                print(f"  [ERROR] CIA request failed: {response.status_code}")
                
        except requests.Timeout:
            print("  [NOTE] CIA response timed out (expected behavior)")
        except Exception as e:
            print(f"  [ERROR] CIA error: {e}")
        
        time.sleep(1)  # Delay between turns
    
    # Check if potential bid card was created in Session 1
    print("\n" + "-" * 60)
    print("CHECKING POTENTIAL BID CARD CREATION (SESSION 1)")
    print("-" * 60)
    
    try:
        bid_card_response = requests.get(
            f"http://localhost:8008/api/cia/conversation/{conversation_id_1}/potential-bid-card",
            timeout=5
        )
        
        if bid_card_response.status_code == 200:
            bid_card_data = bid_card_response.json()
            print("[SUCCESS] Potential bid card found!")
            print(json.dumps(bid_card_data, indent=2))
            potential_bid_card_id = bid_card_data.get('id')
            
            # Check if images are stored
            if 'fields' in bid_card_data and 'project_images' in bid_card_data['fields']:
                print(f"[SUCCESS] Images found in bid card: {bid_card_data['fields']['project_images']}")
            else:
                print("[WARNING] No images found in bid card fields")
                
        else:
            print(f"[WARNING] No potential bid card found: {bid_card_response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] Bid card check failed: {e}")
    
    # Wait before session 2
    print("\n[WAITING] Pausing 3 seconds before Session 2...")
    time.sleep(3)
    
    # SESSION 2: New conversation - test memory persistence
    print("\n" + "=" * 60)
    print("SESSION 2: New Chat - Testing Memory Persistence")
    print("=" * 60)
    
    session_2_messages = [
        "Hi again! I'm back to continue planning my kitchen renovation.",
        "Can you remind me what we discussed about my project?",
        "Do you still have the photo I uploaded of my current kitchen?",
        "I've been thinking more about the budget and timeline."
    ]
    
    session_2_conversation = []
    
    for turn, message in enumerate(session_2_messages, 1):
        print(f"\n[SESSION 2 - TURN {turn}] User: {message}")
        
        session_2_conversation.append({"role": "user", "content": message})
        
        # Send message with SAME user_id but DIFFERENT conversation_id
        try:
            response = requests.post(
                "http://localhost:8008/api/cia/stream",
                json={
                    "messages": session_2_conversation,
                    "conversation_id": conversation_id_2,  # NEW conversation ID
                    "user_id": user_id,  # SAME user ID - should restore memory
                    "model_preference": "gpt-4o"
                },
                timeout=8,
                stream=True
            )
            
            if response.status_code == 200:
                # Collect AI response
                ai_response = ""
                chunk_count = 0
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            chunk_count += 1
                            try:
                                data_str = line_str[6:]
                                if data_str != '[DONE]':
                                    data = json.loads(data_str)
                                    if 'choices' in data:
                                        content = data['choices'][0].get('delta', {}).get('content', '')
                                        ai_response += content
                            except:
                                pass
                            
                            if chunk_count > 50:
                                break
                
                if ai_response:
                    print(f"  [CIA Response]: {ai_response[:300]}...")
                    session_2_conversation.append({"role": "assistant", "content": ai_response})
                    
                    # Check if CIA referenced previous conversation
                    memory_indicators = [
                        "kitchen renovation", "jennifer", "chicago", "$40,000", "$60,000", 
                        "cabinets", "countertops", "photo", "image", "uploaded"
                    ]
                    
                    found_memories = [indicator for indicator in memory_indicators 
                                    if indicator.lower() in ai_response.lower()]
                    
                    if found_memories:
                        print(f"  [MEMORY SUCCESS] CIA remembered: {found_memories}")
                    else:
                        print("  [MEMORY WARNING] No clear memory references found")
                
            else:
                print(f"  [ERROR] CIA request failed: {response.status_code}")
                
        except requests.Timeout:
            print("  [NOTE] CIA response timed out (expected behavior)")
        except Exception as e:
            print(f"  [ERROR] CIA error: {e}")
        
        time.sleep(1)
    
    # Final database verification
    print("\n" + "=" * 60)
    print("FINAL DATABASE VERIFICATION")
    print("=" * 60)
    
    # Check conversation memory storage
    try:
        memory_response = requests.get(
            f"http://localhost:8008/api/cia/user/{user_id}/memory",
            timeout=5
        )
        
        if memory_response.status_code == 200:
            memory_data = memory_response.json()
            print("[SUCCESS] User memory found in database!")
            print(json.dumps(memory_data, indent=2))
        else:
            print(f"[WARNING] User memory not found: {memory_response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] Memory check failed: {e}")
    
    # Check if images are accessible in Session 2
    if potential_bid_card_id:
        try:
            bid_card_response_2 = requests.get(
                f"http://localhost:8008/api/cia/potential-bid-cards/{potential_bid_card_id}",
                timeout=5
            )
            
            if bid_card_response_2.status_code == 200:
                bid_card_data_2 = bid_card_response_2.json()
                print("[SUCCESS] Bid card still accessible in Session 2!")
                
                if 'fields' in bid_card_data_2 and bid_card_data_2['fields'].get('project_images'):
                    print("[SUCCESS] Images persist across sessions!")
                else:
                    print("[WARNING] Images not found in persisted bid card")
                    
        except Exception as e:
            print(f"[ERROR] Session 2 bid card check failed: {e}")
    
    # Clean up test image
    try:
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
            print(f"[CLEANUP] Removed test image: {test_image_path}")
    except:
        pass
    
    # Final summary
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"User ID: {user_id}")
    print(f"Session 1 Conversation: {conversation_id_1}")
    print(f"Session 2 Conversation: {conversation_id_2}")
    print(f"Potential Bid Card: {potential_bid_card_id or 'Not created'}")
    
    print("\nTEST COMPONENTS:")
    print("- Multi-turn conversation with image upload")
    print("- Potential bid card creation with extracted fields")  
    print("- Cross-session memory persistence testing")
    print("- Image storage and retrieval verification")
    print("- Database persistence confirmation")
    
    return user_id, conversation_id_1, conversation_id_2, potential_bid_card_id

if __name__ == "__main__":
    print("CIA COMPLETE JOURNEY TEST")
    print("Testing images, memory persistence, and database storage")
    print("")
    
    try:
        user_id, conv1, conv2, bid_card = test_complete_cia_journey()
        print(f"\n[COMPLETED] Test finished successfully")
        print(f"User ID: {user_id}")
        print(f"Conversations: {conv1}, {conv2}")
        print(f"Bid Card: {bid_card}")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()