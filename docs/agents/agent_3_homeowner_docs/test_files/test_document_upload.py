#!/usr/bin/env python3

import requests
import io
import json

def create_test_document():
    """Create a simple test PDF-like document"""
    # Create a simple text file to simulate a document
    content = """
Kitchen Remodel Specifications

Project Overview:
- Budget: $20,000
- Timeline: 3-4 weeks
- Space: 10x12 kitchen

Requirements:
1. New cabinets (white shaker style)
2. Granite countertops
3. New appliances (stainless steel)
4. Updated lighting
5. Backsplash tile

Notes:
- Need permits for electrical work
- Coordinate with plumber for sink installation
- Prefer eco-friendly materials where possible
"""
    
    doc_buffer = io.BytesIO(content.encode('utf-8'))
    return doc_buffer

def test_document_upload():
    """Test document upload to messaging system"""
    
    # First send a message so we have a message_id to attach to
    message_url = "http://localhost:8008/api/messages/send"
    message_payload = {
        "bid_card_id": "2cb6e43a-2c92-4e30-93f2-e44629f8975f",
        "content": "Here are my detailed kitchen remodel specifications and requirements",
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
            print("Failed to send message, cannot test upload")
            return
            
        message_id = message_result['id']
        conversation_id = message_result['conversation_id']
        
        # Now test document upload
        print(f"\nTesting document upload for message_id: {message_id}")
        
        upload_url = "http://localhost:8008/api/messages/upload-document"
        
        # Create test document
        test_doc = create_test_document()
        
        # Prepare upload data
        files = {
            'file': ('kitchen_specs.txt', test_doc, 'text/plain')
        }
        data = {
            'message_id': message_id,
            'conversation_id': conversation_id,
            'sender_type': 'homeowner',
            'sender_id': '11111111-1111-1111-1111-111111111111'
        }
        
        # Upload document
        upload_response = requests.post(upload_url, files=files, data=data)
        print(f"Upload Status: {upload_response.status_code}")
        upload_result = upload_response.json()
        print(f"Upload Result: {json.dumps(upload_result, indent=2)}")
        
        if upload_result.get('success'):
            print(f"\nDocument uploaded successfully!")
            print(f"URL: {upload_result.get('url')}")
            print(f"Attachment ID: {upload_result.get('attachment_id')}")
            
            # Test getting message with attachments
            print(f"\nTesting message retrieval with document attachment...")
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
                            for att in attachments:
                                print(f"Attachment: {att['name']} ({att['type']}) - {att['size']} bytes")
                        break
            
        else:
            print(f"Document upload failed: {upload_result.get('error')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_document_upload()