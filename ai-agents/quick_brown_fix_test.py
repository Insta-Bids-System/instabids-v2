"""
Quick test with improved prompt for brown grass issue
"""

import asyncio
import os
import aiohttp
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

async def test_brown_grass_fix():
    """Test one improved configuration"""
    
    LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
    backyard_path = r"C:\Users\Not John Or Justin\Documents\instabids\test-images\YOUR_ACTUAL_BACKYARD.jpg"
    
    headers = {
        "Authorization": f"Bearer {LEONARDO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    print("=" * 60)
    print("BROWN GRASS FIX TEST")
    print("=" * 60)
    
    # Upload image
    print("Uploading your backyard...")
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://cloud.leonardo.ai/api/rest/v1/init-image",
            headers=headers,
            json={"extension": "jpg"}
        ) as response:
            if response.status != 200:
                print("[ERROR] Upload failed")
                return
            
            result = await response.json()
            upload_data = result.get("uploadInitImage", {})
            upload_id = upload_data.get("id")
            upload_url = upload_data.get("url")
            upload_fields = upload_data.get("fields", {})
            
            with open(backyard_path, "rb") as f:
                image_data = f.read()
            
            form_data = aiohttp.FormData()
            if isinstance(upload_fields, str):
                upload_fields = json.loads(upload_fields)
            for key, value in upload_fields.items():
                form_data.add_field(key, value)
            form_data.add_field('file', image_data, filename='image.jpg', content_type='image/jpeg')
            
            async with session.post(upload_url, data=form_data) as s3_response:
                if s3_response.status not in [200, 201, 204]:
                    print("[ERROR] S3 upload failed")
                    return    
    print(f"[SUCCESS] Uploaded! ID: {upload_id}")
    
    # Generate with improved prompt
    print("\nGenerating with IMPROVED prompt targeting brown grass...")
    
    improved_prompt = "Replace ALL grass areas with artificial turf - both the green healthy grass AND the brown dead dying patchy areas. The brown patches and dead spots must become green synthetic turf too. Complete lawn transformation to uniform emerald artificial turf covering entire yard. Keep soccer goal in exact same position, preserve house and trees. Professional artificial turf installation."
    
    negative_prompt = "brown grass remaining, dead patches left behind, partial turf coverage, patchy installation, inconsistent grass, keep brown areas"
    
    generation_data = {
        "prompt": improved_prompt,
        "negative_prompt": negative_prompt,
        "modelId": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",
        "width": 1024,
        "height": 768,
        "num_images": 1,
        "init_image_id": upload_id,
        "init_strength": 0.23,  # Balanced
        "guidance_scale": 8
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://cloud.leonardo.ai/api/rest/v1/generations",
            headers=headers,
            json=generation_data
        ) as response:
            if response.status != 200:
                print("[ERROR] Generation failed")
                return
            
            result = await response.json()
            generation_id = result.get("sdGenerationJob", {}).get("generationId")
            
            if not generation_id:
                print("[ERROR] No generation ID")
                return
            
            print(f"Generation started: {generation_id}")
            print("Waiting for completion", end="")
            
            # Poll for result
            max_attempts = 30
            attempt = 0
            
            while attempt < max_attempts:
                await asyncio.sleep(10)
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
                                print(f"\n\n[SUCCESS] Brown grass fix complete!")
                                print(f"[RESULT] {image_url}")
                                print("\n[CHECK FOR]:")
                                print("1. Are brown/dead areas now GREEN turf?")
                                print("2. Is entire lawn uniform artificial turf?")
                                print("3. Soccer goal in same position?")
                                return
                        elif status == "FAILED":
                            print(f"\n[ERROR] Generation failed")
                            return
                
                attempt += 1
            
            print(f"\n[TIMEOUT] Check Leonardo app for generation {generation_id}")

if __name__ == "__main__":
    asyncio.run(test_brown_grass_fix())