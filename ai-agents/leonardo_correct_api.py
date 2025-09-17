"""
Leonardo with CORRECT API format for multi-reference images
"""

import asyncio
import os
import aiohttp
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

async def upload_image(image_path, description):
    """Upload image and return ID"""
    LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
    
    headers = {
        "Authorization": f"Bearer {LEONARDO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://cloud.leonardo.ai/api/rest/v1/init-image",
                headers=headers,
                json={"extension": "jpg"}
            ) as response:
                if response.status != 200:
                    return None
                
                result = await response.json()
                upload_data = result.get("uploadInitImage", {})
                upload_id = upload_data.get("id")
                upload_url = upload_data.get("url")
                upload_fields = upload_data.get("fields", {})
                
                with open(image_path, "rb") as f:
                    image_data = f.read()
                
                form_data = aiohttp.FormData()
                if isinstance(upload_fields, str):
                    upload_fields = json.loads(upload_fields)
                for key, value in upload_fields.items():
                    form_data.add_field(key, value)
                form_data.add_field('file', image_data, filename='image.jpg', content_type='image/jpeg')
                
                async with session.post(upload_url, data=form_data) as s3_response:
                    if s3_response.status in [200, 201, 204]:
                        print(f"[SUCCESS] {description} uploaded - ID: {upload_id}")
                        return upload_id
                    return None
    except Exception as e:
        print(f"[ERROR] {description} upload failed: {e}")
        return None

async def generate_with_correct_format():
    """Generate using CORRECT Leonardo API format"""
    
    print("=" * 70)
    print("LEONARDO CORRECT MULTI-REFERENCE API")
    print("=" * 70)
    
    # Upload both images
    backyard_path = r"C:\Users\Not John Or Justin\Documents\instabids\test-images\YOUR_ACTUAL_BACKYARD.jpg"
    turf_path = r"C:\Users\Not John Or Justin\Documents\instabids\test-images\YOUR_IDEAL_TURF.jpg"
    
    print("\nUploading both images...")
    backyard_id = await upload_image(backyard_path, "Backyard")
    turf_id = await upload_image(turf_path, "Turf reference")
    
    if not backyard_id or not turf_id:
        print("[ERROR] Failed to upload images")
        return
    
    print(f"\nReady to generate:")
    print(f"  Base image (backyard): {backyard_id}")
    print(f"  Style reference (turf): {turf_id}")
    
    # CORRECT API format from Leonardo docs
    generation_data = {
        "height": 768,
        "width": 1024,
        "modelId": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",  # Leonardo Phoenix
        "prompt": "Transform this backyard to have artificial turf lawn matching the reference turf style. Replace all grass areas with the exact artificial turf shown in reference image.",
        "negative_prompt": "brown grass, dead patches, natural grass",
        "num_images": 1,
        "init_image_id": backyard_id,
        "init_strength": 0.25,
        "guidance_scale": 7,
        "controlnets": [
            {
                "initImageId": turf_id,
                "initImageType": "UPLOADED",
                "preprocessorId": 67,  # Style Reference
                "strengthType": "High",
                "influence": 0.7
            }
        ]
    }    
    LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
    headers = {
        "Authorization": f"Bearer {LEONARDO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    print("\nGenerating with CORRECT multi-reference format...")
    print("This should FINALLY work properly!")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://cloud.leonardo.ai/api/rest/v1/generations",
                headers=headers,
                json=generation_data
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    print(f"[ERROR] Generation failed: {response.status}")
                    print(f"Response: {error_text}")
                    return
                
                result = await response.json()
                generation_id = result.get("sdGenerationJob", {}).get("generationId")
                
                if not generation_id:
                    print(f"[ERROR] No generation ID")
                    print(f"Response: {result}")
                    return
                
                print(f"[SUCCESS] Multi-reference generation started!")
                print(f"Generation ID: {generation_id}")
                print("\nWaiting for completion (this should be MUCH better)...")
                print("Using your turf image as style reference", end="")
                
                # Wait for completion
                for attempt in range(40):
                    await asyncio.sleep(8)
                    print(".", end="", flush=True)
                    
                    async with session.get(
                        f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}",
                        headers=headers
                    ) as status_response:
                        if status_response.status == 200:
                            status_result = await status_response.json()
                            generation = status_result.get("generations_by_pk", {})
                            status = generation.get("status", "UNKNOWN")
                            
                            if status == "COMPLETE":
                                images = generation.get("generated_images", [])
                                if images:
                                    image_url = images[0].get("url")
                                    print(f"\n\n" + "=" * 70)
                                    print("MULTI-REFERENCE RESULT - USING BOTH IMAGES!")
                                    print("=" * 70)
                                    print(f"\n[RESULT] {image_url}")
                                    print(f"\nThis FINALLY uses both images correctly:")
                                    print(f"✓ Your backyard as base (layout/structure)")  
                                    print(f"✓ Your turf as style reference (texture/color)")
                                    print(f"✓ ControlNet Style Reference for precise matching")
                                    print(f"\nThis should solve:")
                                    print(f"1. Brown grass issue (uses turf as reference)")
                                    print(f"2. Exact turf color/texture matching")
                                    print(f"3. Better structure preservation")
                                    return image_url
                            elif status == "FAILED":
                                print(f"\n[FAILED] Generation failed")
                                return None
                
                print(f"\n[TIMEOUT] Generation taking too long")
                return None
                
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(generate_with_correct_format())