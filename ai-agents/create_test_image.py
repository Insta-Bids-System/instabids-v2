#!/usr/bin/env python3
"""
Create a test image file and upload it to Supabase storage for testing inline viewing
"""

from PIL import Image, ImageDraw, ImageFont
import io
import base64
import requests
from database_simple import db

supabase_client = db.client

def create_test_kitchen_image():
    """Create a simple kitchen design mockup image"""
    # Create a 800x600 image with white background
    width, height = 800, 600
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a nice font, fall back to default if not available
    try:
        font_title = ImageFont.truetype("arial.ttf", 36)
        font_text = ImageFont.truetype("arial.ttf", 24)
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()
    
    # Draw kitchen layout mockup
    # Kitchen island
    draw.rectangle([200, 250, 600, 350], fill='#8B4513', outline='black', width=2)
    draw.text((350, 290), "Kitchen Island", fill='white', font=font_text, anchor='mm')
    
    # Cabinets - Upper
    draw.rectangle([50, 50, 750, 150], fill='#F5F5DC', outline='black', width=2)
    draw.text((400, 100), "Upper Cabinets", fill='black', font=font_text, anchor='mm')
    
    # Cabinets - Lower left
    draw.rectangle([50, 400, 350, 550], fill='#F5F5DC', outline='black', width=2)
    draw.text((200, 475), "Base Cabinets", fill='black', font=font_text, anchor='mm')
    
    # Cabinets - Lower right
    draw.rectangle([450, 400, 750, 550], fill='#F5F5DC', outline='black', width=2)
    draw.text((600, 475), "Base Cabinets", fill='black', font=font_text, anchor='mm')
    
    # Appliances
    # Refrigerator
    draw.rectangle([650, 200, 750, 400], fill='#C0C0C0', outline='black', width=2)
    draw.text((700, 300), "Fridge", fill='black', font=font_text, anchor='mm')
    
    # Stove/Range
    draw.rectangle([350, 400, 450, 550], fill='#2F4F4F', outline='black', width=2)
    draw.text((400, 475), "Range", fill='white', font=font_text, anchor='mm')
    
    # Sink
    draw.ellipse([100, 420, 200, 520], fill='#E6E6FA', outline='black', width=2)
    draw.text((150, 470), "Sink", fill='black', font=font_text, anchor='mm')
    
    # Title
    draw.text((400, 20), "Kitchen Design Mockup", fill='black', font=font_title, anchor='mm')
    
    # Add some design notes
    notes = [
        "• Modern white cabinets with soft-close doors",
        "• Quartz countertops with waterfall edge on island", 
        "• Stainless steel appliance package",
        "• Undermount sink with pull-down faucet",
        "• Recessed LED lighting throughout"
    ]
    
    for i, note in enumerate(notes):
        draw.text((50, 570 + i * 25), note, fill='#333333', font=font_text)
    
    return image

def upload_to_supabase_storage(image, filename="kitchen_design_mockup.jpg"):
    """Upload the image to Supabase storage"""
    try:
        # Convert image to bytes
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=90)
        buffer.seek(0)
        
        # Upload to Supabase storage
        bucket_name = 'project-images'
        file_path = f'bid_attachments/303afce1-2de4-418a-bb9a-03775d89f62b/{filename}'
        
        # Upload file
        response = supabase_client.storage.from_(bucket_name).upload(
            file_path,
            buffer.getvalue(),
            file_options={
                'content-type': 'image/jpeg',
                'cache-control': '3600'
            }
        )
        
        if hasattr(response, 'error') and response.error:
            print(f"Upload error: {response.error}")
            return None
        
        # Get public URL
        public_url = supabase_client.storage.from_(bucket_name).get_public_url(file_path)
        print(f"Image uploaded successfully!")
        print(f"Public URL: {public_url}")
        
        return public_url
        
    except Exception as e:
        print(f"Error uploading to Supabase: {e}")
        return None

def update_attachment_record(image_url):
    """Update the contractor_proposal_attachments record with the new image"""
    try:
        # Update the existing attachment record
        response = supabase_client.table('contractor_proposal_attachments').update({
            'url': image_url,
            'mime_type': 'image/jpeg',
            'size': 0,  # We could calculate this but for testing it's fine
            'name': 'kitchen_design_mockup.jpg'
        }).eq('id', '82fb2e6c-c319-4ef1-a70d-cd80ac2aa676').execute()
        
        print("Updated attachment record in database")
        print(f"Response: {response.data}")
        
    except Exception as e:
        print(f"Error updating database record: {e}")

if __name__ == "__main__":
    print("Creating test kitchen design image...")
    
    # Create the image
    image = create_test_kitchen_image()
    
    # Save locally for reference
    image.save("test_kitchen_design.jpg", quality=90)
    print("Saved test image locally as test_kitchen_design.jpg")
    
    # Upload to Supabase
    image_url = upload_to_supabase_storage(image, "kitchen_design_mockup.jpg")
    
    if image_url:
        # Update the database record
        update_attachment_record(image_url)
        print("\n✅ Test image creation and upload complete!")
        print(f"Image URL: {image_url}")
    else:
        print("❌ Failed to upload image to Supabase")