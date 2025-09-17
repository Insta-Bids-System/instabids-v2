#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import requests
import time
sys.path.append('C:/Users/Not John Or Justin/Documents/instabids/ai-agents')

from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

print("COMPREHENSIVE END-TO-END IMAGE GENERATION TEST")
print("=" * 60)
print("Testing: Iris Chat -> Image Generation -> Database Save -> Frontend Display")
print("=" * 60)

# Load environment variables
load_dotenv('C:/Users/Not John Or Justin/Documents/instabids/.env', override=True)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Step 1: Test Iris Chat Image Generation
print("\nStep 1: Test Iris Chat with Image Generation Request")
print("-" * 50)

iris_payload = {
    "message": "I want to see my kitchen with exposed brick walls and pendant lighting",
    "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3",
    "user_id": "550e8400-e29b-41d4-a716-446655440001"
}

try:
    print("Sending image generation request to Iris...")
    iris_response = requests.post('http://localhost:8008/api/iris/chat', json=iris_payload, timeout=30)
    
    if iris_response.ok:
        iris_data = iris_response.json()
        print(f"✅ Iris Response Status: {iris_response.status_code}")
        print(f"   Response Length: {len(iris_data.get('response', ''))}")
        print(f"   Image Generated: {iris_data.get('image_generated', False)}")
        print(f"   Image URL: {iris_data.get('image_url', 'None')[:50]}...")
        
        if iris_data.get('image_generated') and iris_data.get('image_url'):
            generated_image_url = iris_data.get('image_url')
            print("✅ SUCCESS: Iris generated an image!")
        else:
            print("⚠️ WARNING: Iris did not generate an image")
            generated_image_url = None
    else:
        print(f"❌ ERROR: Iris request failed with status {iris_response.status_code}")
        print(f"   Response: {iris_response.text}")
        generated_image_url = None
        
except Exception as e:
    print(f"❌ ERROR: Iris request failed: {e}")
    generated_image_url = None

# Step 2: Test Direct Image Generation API
print(f"\nStep 2: Test Direct Image Generation API")
print("-" * 50)

direct_payload = {
    "board_id": "26cf972b-83e4-484c-98b6-a5d1a4affee3",
    "ideal_image_id": "inspiration_1",
    "current_image_id": "current_1",
    "user_preferences": "Add industrial pendant lighting and exposed brick accent wall"
}

try:
    print("Sending direct image generation request...")
    direct_response = requests.post('http://localhost:8008/api/image-generation/generate-dream-space', 
                                   json=direct_payload, timeout=60)
    
    if direct_response.ok:
        direct_data = direct_response.json()
        print(f"✅ Direct API Status: {direct_response.status_code}")
        print(f"   Success: {direct_data.get('success', False)}")
        print(f"   Generated URL: {direct_data.get('generated_image_url', 'None')[:50]}...")
        print(f"   Generation ID: {direct_data.get('generation_id', 'None')}")
        print(f"   Saved as Vision: {direct_data.get('saved_as_vision', False)}")
        
        if direct_data.get('success') and direct_data.get('generated_image_url'):
            direct_image_url = direct_data.get('generated_image_url')
            direct_generation_id = direct_data.get('generation_id')
            print("✅ SUCCESS: Direct API generated an image!")
        else:
            print("⚠️ WARNING: Direct API did not generate an image")
            direct_image_url = None
            direct_generation_id = None
    else:
        print(f"❌ ERROR: Direct API failed with status {direct_response.status_code}")
        print(f"   Response: {direct_response.text}")
        direct_image_url = None
        direct_generation_id = None
        
except Exception as e:
    print(f"❌ ERROR: Direct API request failed: {e}")
    direct_image_url = None
    direct_generation_id = None

# Step 3: Check Database for New Images
print(f"\nStep 3: Check Database for Generated Images")
print("-" * 50)

try:
    # Check inspiration_images table
    result = supabase.table("inspiration_images").select("*").eq("board_id", "26cf972b-83e4-484c-98b6-a5d1a4affee3").execute()
    
    vision_images = [img for img in result.data if 'vision' in str(img.get('tags', [])).lower()]
    ai_generated_images = [img for img in result.data if 'ai_generated' in str(img.get('tags', [])).lower()]
    recent_images = [img for img in result.data if img.get('created_at', '').startswith('2025-08-01')]
    
    print(f"Total images in database: {len(result.data)}")
    print(f"Vision-tagged images: {len(vision_images)}")
    print(f"AI-generated tagged images: {len(ai_generated_images)}")
    print(f"Images created today: {len(recent_images)}")
    
    if recent_images:
        print(f"\n✅ Recent Images Found:")
        for img in recent_images[-3:]:  # Show last 3
            print(f"   ID: {img.get('id')}")
            print(f"   Category: {img.get('category')}")  
            print(f"   Source: {img.get('source')}")
            print(f"   Tags: {img.get('tags')}")
            print(f"   Created: {img.get('created_at')}")
            print(f"   URL: {img.get('image_url', '')[:50]}...")
            print()
    else:
        print("⚠️ No recent images found in database")
        
except Exception as e:
    print(f"❌ ERROR: Database check failed: {e}")

# Step 4: Test Frontend Demo API
print(f"\nStep 4: Test Frontend Demo API")
print("-" * 50)

try:
    demo_response = requests.get('http://localhost:8008/api/demo/inspiration/images', 
                               params={'board_id': '26cf972b-83e4-484c-98b6-a5d1a4affee3'})
    
    if demo_response.ok:
        demo_images = demo_response.json()
        vision_demo_images = [img for img in demo_images if 'vision' in str(img.get('tags', [])).lower()]
        
        print(f"✅ Demo API Response: {demo_response.status_code}")
        print(f"   Total images returned: {len(demo_images)}")
        print(f"   Vision images: {len(vision_demo_images)}")
        
        if vision_demo_images:
            print(f"\n✅ Vision Images Available for Frontend:")
            for img in vision_demo_images:
                print(f"   ID: {img.get('id')}")
                print(f"   Category: {img.get('category')}")
                print(f"   Source: {img.get('source')}")
                print(f"   Created: {img.get('created_at', '')[:19]}")
                
                # Test image URL accessibility
                try:
                    url_test = requests.head(img.get('image_url', ''), timeout=5)
                    if url_test.status_code == 200:
                        print(f"   URL Status: ✅ Accessible")
                    else:
                        print(f"   URL Status: ⚠️ {url_test.status_code}")
                except:
                    print(f"   URL Status: ❌ Not accessible")
                print()
        else:
            print("⚠️ No vision images available for frontend")
    else:
        print(f"❌ ERROR: Demo API failed with status {demo_response.status_code}")
        
except Exception as e:
    print(f"❌ ERROR: Demo API test failed: {e}")

# Step 5: Summary and Recommendations
print(f"\nStep 5: Test Summary and Status")
print("-" * 50)

iris_working = bool(generated_image_url)
direct_api_working = bool(direct_image_url)
database_saves_working = len(recent_images) > 0 if 'recent_images' in locals() else False
frontend_ready = len(vision_demo_images) > 0 if 'vision_demo_images' in locals() else False

print(f"✅ Component Status:")
print(f"   Iris Chat Image Generation: {'✅ WORKING' if iris_working else '❌ FAILED'}")
print(f"   Direct Image Generation API: {'✅ WORKING' if direct_api_working else '❌ FAILED'}")
print(f"   Database Image Persistence: {'✅ WORKING' if database_saves_working else '❌ FAILED'}")
print(f"   Frontend Demo API: {'✅ WORKING' if frontend_ready else '❌ FAILED'}")

if iris_working and direct_api_working and database_saves_working and frontend_ready:
    print(f"\n🎉 SUCCESS: COMPLETE END-TO-END SYSTEM WORKING!")
    print(f"   ✅ Images are being generated")
    print(f"   ✅ Images are being saved to database")
    print(f"   ✅ Images are accessible to frontend")
    print(f"   ✅ System ready for user testing")
elif direct_api_working and database_saves_working:
    print(f"\n✅ CORE SYSTEM WORKING:")
    print(f"   ✅ Image generation and database saves operational")
    print(f"   ⚠️ May need Iris chat integration fixes")
else:
    print(f"\n⚠️ SYSTEM NEEDS ATTENTION:")
    if not direct_api_working:
        print(f"   ❌ Core image generation not working")
    if not database_saves_working:
        print(f"   ❌ Database persistence not working")
    if not frontend_ready:
        print(f"   ❌ Frontend integration not ready")

print(f"\n" + "=" * 60)
print("COMPREHENSIVE TEST COMPLETE")  
print("=" * 60)