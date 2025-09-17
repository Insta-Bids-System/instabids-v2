"""
FINALLY using Leonardo properly with BOTH images
- Base image: Your backyard (structure/layout)  
- Reference image: Your ideal turf (style/texture to copy)
"""

import asyncio
import os
import aiohttp
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

async def upload_image(image_path, description):
    """Upload image to Leonardo and return ID"""
    LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
    
    headers = {
        "Authorization": f"Bearer {LEONARDO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Get upload URL
            async with session.post(
                "https://cloud.leonardo.ai/api/rest/v1/init-image",
                headers=headers,
                json={"extension": "jpg"}
            ) as response:
                if response.status != 200:
                    print(f"[ERROR] Failed to get upload URL for {description}")
                    return None
                
                result = await response.json()
                upload_data = result.get("uploadInitImage", {})
                upload_id = upload_data.get("id")
                upload_url = upload_data.get("url")
                upload_fields = upload_data.get("fields", {})
                
                # Read image
                with open(image_path, "rb") as f:
                    image_data = f.read()
                
                # Upload to S3
                form_data = aiohttp.FormData()
                if isinstance(upload_fields, str):
                    upload_fields = json.loads(upload_fields)
                for key, value in upload_fields.items():
                    form_data.add_field(key, value)
                form_data.add_field('file', image_data, filename='image.jpg', content_type='image/jpeg')
                
                async with session.post(upload_url, data=form_data) as s3_response:
                    if s3_response.status in [200, 201, 204]:
                        print(f"[SUCCESS] Uploaded {description} - ID: {upload_id}")
                        return upload_id
                    else:
                        print(f"[ERROR] S3 upload failed for {description}")
                        return None
    except Exception as e:
        print(f"[ERROR] Upload failed for {description}: {e}")
        return None

async def generate_with_multi_reference():
    """Generate using BOTH images properly"""
    
    print("=" * 70)
    print("LEONARDO MULTI-REFERENCE GENERATION")
    print("Using BOTH your backyard AND turf images properly")
    print("=" * 70)
    
    # Image paths
    backyard_path = r"C:\Users\Not John Or Justin\Documents\instabids\test-images\YOUR_ACTUAL_BACKYARD.jpg"
    turf_path = r"C:\Users\Not John Or Justin\Documents\instabids\test-images\YOUR_IDEAL_TURF.jpg"
    
    # Upload BOTH images
    print("\nStep 1: Uploading BOTH images...")
    backyard_id = await upload_image(backyard_path, "your actual backyard")
    turf_id = await upload_image(turf_path, "your ideal turf reference")
    
    if not backyard_id or not turf_id:
        print("[ERROR] Failed to upload one or both images")
        return
    
    print(f"\n[SUCCESS] Both images uploaded!")
    print(f"  Backyard ID: {backyard_id}")  
    print(f"  Turf ID: {turf_id}")
    
    # Generate with multi-reference
    LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
    headers = {
        "Authorization": f"Bearer {LEONARDO_API_KEY}",
        "Content-Type": "application/json"
    }    
    print("\nStep 2: Generating with PROPER multi-reference setup...")
    
    # Multi-reference generation data
    generation_data = {
        "prompt": "Transform this backyard lawn to match the artificial turf reference image. Replace all grass areas - green and brown - with the exact same type of artificial turf shown in the reference. Keep soccer goal and all structures in exact same positions.",
        "negative_prompt": "brown grass, dead patches, natural grass, different turf style",
        "modelId": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",  # Leonardo Phoenix
        "width": 1024,
        "height": 768,
        "num_images": 1,
        "init_image_id": backyard_id,  # Base structure
        "init_strength": 0.25,
        "guidance_scale": 7,
        "imageReferences": [
            {
                "image_id": turf_id,
                "weight": 0.8  # Strong influence from turf reference
            }
        ]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print("Sending generation request with BOTH images...")
            async with session.post(
                "https://cloud.leonardo.ai/api/rest/v1/generations",
                headers=headers,
                json=generation_data
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    print(f"[ERROR] Generation failed: {response.status}")
                    print(f"Response: {error_text}")
                    
                    # Try alternative format
                    print("\nTrying alternative multi-reference format...")
                    alt_generation_data = {
                        "prompt": "Transform lawn to artificial turf matching the reference style",
                        "negative_prompt": "brown grass, dead patches",
                        "modelId": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",
                        "width": 1024,
                        "height": 768,
                        "num_images": 1,
                        "init_image_id": backyard_id,
                        "init_strength": 0.25,
                        "guidance_scale": 7,
                        "controlnets": [
                            {
                                "image_id": turf_id,
                                "preprocessor_id": 67,  # Style transfer
                                "strengthType": "Mid",
                                "weight": 0.8
                            }
                        ]
                    }
                    
                    async with session.post(
                        "https://cloud.leonardo.ai/api/rest/v1/generations",
                        headers=headers,
                        json=alt_generation_data
                    ) as alt_response:                        
                        if alt_response.status != 200:
                            alt_error = await alt_response.text()
                            print(f"[ERROR] Alternative format also failed: {alt_response.status}")
                            print(f"Alt Response: {alt_error}")
                            return
                        else:
                            result = await alt_response.json()
                else:
                    result = await response.json()
                
                generation_id = result.get("sdGenerationJob", {}).get("generationId")
                
                if not generation_id:
                    print(f"[ERROR] No generation ID returned")
                    print(f"Full response: {result}")
                    return
                
                print(f"[SUCCESS] Multi-reference generation started!")
                print(f"Generation ID: {generation_id}")
                print("\nStep 3: Waiting for completion...")
                print("This should produce MUCH better results using your turf as reference")
                print("Waiting", end="")
                
                # Poll for completion
                for attempt in range(40):  # Longer timeout
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
                                    print("MULTI-REFERENCE RESULT COMPLETE!")
                                    print("=" * 70)
                                    print(f"\n[RESULT] {image_url}")
                                    print(f"\nThis used BOTH images:")
                                    print(f"✓ Your backyard as base structure")  
                                    print(f"✓ Your turf image as style reference")
                                    print(f"\nThis should be MUCH better at:")
                                    print(f"1. Matching your exact turf style/color")
                                    print(f"2. Replacing ALL grass areas (green AND brown)")
                                    print(f"3. Preserving your backyard layout perfectly")
                                    return
                            elif status == "FAILED":
                                print(f"\n[FAILED] Multi-reference generation failed")
                                return
                
                print(f"\n[TIMEOUT] Check Leonardo app for generation {generation_id}")
                
    except Exception as e:
        print(f"[ERROR] Generation exception: {e}")

if __name__ == "__main__":
    asyncio.run(generate_with_multi_reference())