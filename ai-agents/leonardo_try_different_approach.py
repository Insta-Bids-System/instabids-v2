"""
Try different Leonardo approaches for multi-reference
"""

import asyncio
import os
import aiohttp
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

async def upload_image(image_path, description):
    """Upload image"""
    LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
    headers = {"Authorization": f"Bearer {LEONARDO_API_KEY}", "Content-Type": "application/json"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("https://cloud.leonardo.ai/api/rest/v1/init-image", headers=headers, json={"extension": "jpg"}) as response:
                if response.status != 200: return None
                result = await response.json()
                upload_data = result.get("uploadInitImage", {})
                upload_id, upload_url, upload_fields = upload_data.get("id"), upload_data.get("url"), upload_data.get("fields", {})
                
                with open(image_path, "rb") as f: image_data = f.read()
                form_data = aiohttp.FormData()
                if isinstance(upload_fields, str): upload_fields = json.loads(upload_fields)
                for key, value in upload_fields.items(): form_data.add_field(key, value)
                form_data.add_field('file', image_data, filename='image.jpg', content_type='image/jpeg')
                
                async with session.post(upload_url, data=form_data) as s3_response:
                    if s3_response.status in [200, 201, 204]:
                        print(f"[SUCCESS] {description}: {upload_id}")
                        return upload_id
                    return None
    except Exception as e:
        print(f"[ERROR] {description}: {e}")
        return None

async def test_different_approaches():
    """Test different Leonardo approaches"""
    print("=" * 60)
    print("TESTING DIFFERENT LEONARDO APPROACHES")
    print("=" * 60)
    
    backyard_path = r"C:\Users\Not John Or Justin\Documents\instabids\test-images\YOUR_ACTUAL_BACKYARD.jpg"
    turf_path = r"C:\Users\Not John Or Justin\Documents\instabids\test-images\YOUR_IDEAL_TURF.jpg"
    
    backyard_id = await upload_image(backyard_path, "Backyard")
    turf_id = await upload_image(turf_path, "Turf")
    
    if not backyard_id or not turf_id:
        print("[ERROR] Upload failed")
        return
    
    LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
    headers = {"Authorization": f"Bearer {LEONARDO_API_KEY}", "Content-Type": "application/json"}
    
    # Test 1: Try SDXL model instead of Phoenix
    print("\nTest 1: Using SDXL model with Style Reference...")
    test1_data = {
        "height": 768, "width": 1024,
        "modelId": "5c232a9e-9061-4777-980a-ddc8e65647c6",  # SDXL Fine-tuned
        "prompt": "Transform backyard to artificial turf matching reference style",
        "negative_prompt": "brown grass, dead patches",
        "num_images": 1,
        "init_image_id": backyard_id,
        "init_strength": 0.3,
        "guidance_scale": 7,
        "controlnets": [{"initImageId": turf_id, "initImageType": "UPLOADED", "preprocessorId": 67, "strengthType": "High"}]
    }
    
    result1 = await test_generation("SDXL with Style Reference", test1_data, headers)
    if result1: return result1
    
    # Test 2: Try different preprocessor
    print("\nTest 2: Using Character Reference preprocessor...")
    test2_data = {
        "height": 768, "width": 1024,
        "modelId": "5c232a9e-9061-4777-980a-ddc8e65647c6",  # SDXL
        "prompt": "Transform backyard grass to artificial turf",
        "negative_prompt": "brown grass, natural grass",
        "num_images": 1,
        "init_image_id": backyard_id,
        "init_strength": 0.25,
        "guidance_scale": 7,
        "controlnets": [{"initImageId": turf_id, "initImageType": "UPLOADED", "preprocessorId": 133, "strengthType": "High"}]
    }
    
    result2 = await test_generation("Character Reference", test2_data, headers)
    if result2: return result2
    
    # Test 3: Try without ControlNet but with stronger prompt mentioning both images
    print("\nTest 3: Strong prompt without ControlNet...")
    test3_data = {
        "height": 768, "width": 1024,
        "modelId": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",  # Phoenix
        "prompt": "Transform this exact backyard layout to have perfect artificial turf. Replace ALL grass areas - green healthy grass AND brown dead patchy areas - with vibrant emerald artificial turf exactly like premium synthetic grass. Keep soccer goal and all structures in exact positions. Professional turf installation covering entire lawn.",
        "negative_prompt": "brown grass, dead patches, natural grass, patchy lawn, inconsistent turf",
        "num_images": 1,
        "init_image_id": backyard_id,
        "init_strength": 0.28,
        "guidance_scale": 8
    }
    
    result3 = await test_generation("Strong prompt only", test3_data, headers)
    return result3

async def test_generation(name, data, headers):
    """Test a generation approach"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("https://cloud.leonardo.ai/api/rest/v1/generations", headers=headers, json=data) as response:
                if response.status != 200:
                    error = await response.text()
                    print(f"[FAILED] {name}: {response.status} - {error}")
                    return None
                
                result = await response.json()
                generation_id = result.get("sdGenerationJob", {}).get("generationId")
                
                if not generation_id:
                    print(f"[FAILED] {name}: No generation ID")
                    return None
                
                print(f"[SUCCESS] {name} started: {generation_id}")
                print("Waiting", end="")
                
                # Wait for completion
                for attempt in range(30):
                    await asyncio.sleep(8)
                    print(".", end="", flush=True)
                    
                    async with session.get(f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}", headers=headers) as status_response:
                        if status_response.status == 200:
                            status_result = await status_response.json()
                            generation = status_result.get("generations_by_pk", {})
                            status = generation.get("status", "UNKNOWN")
                            
                            if status == "COMPLETE":
                                images = generation.get("generated_images", [])
                                if images:
                                    image_url = images[0].get("url")
                                    print(f"\n[RESULT] {name} complete!")
                                    print(f"[URL] {image_url}")
                                    return image_url
                            elif status == "FAILED":
                                print(f"\n[FAILED] {name} generation failed")
                                return None
                
                print(f"\n[TIMEOUT] {name} timed out")
                return None
                
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(test_different_approaches())