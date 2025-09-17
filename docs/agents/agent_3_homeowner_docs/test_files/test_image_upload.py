#!/usr/bin/env python3

import requests
import io
from PIL import Image
import json

def create_test_image():
    """Create a simple test image"""
    # Create a 200x200 red square image
    img = Image.new('RGB', (200, 200), color='red')
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='JPEG')
    img_buffer.seek(0)
    return img_buffer

def test_image_upload():
    """Test image upload to messaging system"""
    
    # First send a message so we have a message_id to attach to
    message_url = "http://localhost:8008/api/messages/send"
    message_payload = {
        "bid_card_id": "2cb6e43a-2c92-4e30-93f2-e44629f8975f",
        "content": "I'd like to share a photo of what I'm looking for in the kitchen remodel",
        "sender_type": "homeowner", 
        "sender_id": "11111111-1111-1111-1111-111111111111",
        "conversation_id": "5034dc04-4f70-4375-a442-b80817346906"
    }
    
    try:
        # Send message first
        print("Sending message...")
        message_response = requests.post(message_url, json=message_payload)
        print(f"Message Status: {message_response.status_code}")
        message_result = message_response.json()
        print(f"Message Result: {json.dumps(message_result, indent=2)}")
        
        if not message_result.get('success'):
            print("❌ Failed to send message, cannot test upload")
            return
            
        message_id = message_result['id']
        conversation_id = message_result['conversation_id']
        
        # Now test image upload
        print(f"\nTesting image upload for message_id: {message_id}")
        
        upload_url = "http://localhost:8008/api/messages/upload-image"
        
        # Create test image
        test_image = create_test_image()
        
        # Prepare upload data
        files = {
            'file': ('test_kitchen.jpg', test_image, 'image/jpeg')
        }
        data = {
            'message_id': message_id,
            'conversation_id': conversation_id,
            'sender_type': 'homeowner',
            'sender_id': '11111111-1111-1111-1111-111111111111'
        }
        
        # Upload image
        upload_response = requests.post(upload_url, files=files, data=data)
        print(f"Upload Status: {upload_response.status_code}")
        upload_result = upload_response.json()
        print(f"Upload Result: {json.dumps(upload_result, indent=2)}")
        
        if upload_result.get('success'):
            print(f"\n✅ Image uploaded successfully!")
            print(f"URL: {upload_result.get('url')}")
            print(f"Attachment ID: {upload_result.get('attachment_id')}")
            
            # Test getting message with attachments
            print(f"\nTesting message retrieval with attachments...")
            messages_url = f"http://localhost:8008/api/messages/{conversation_id}"
            messages_response = requests.get(messages_url)
            messages_result = messages_response.json()
            
            if messages_result.get('success'):
                # Find our message and check if it has attachments
                for msg in messages_result['messages']:
                    if msg['id'] == message_id:
                        attachments = msg.get('attachments', [])
                        print(f"Message has {len(attachments)} attachment(s)")
                        if attachments:
                            print(f"Attachment details: {json.dumps(attachments[0], indent=2)}")
                        break
            
        else:
            print(f"❌ Image upload failed: {upload_result.get('error')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_image_upload()