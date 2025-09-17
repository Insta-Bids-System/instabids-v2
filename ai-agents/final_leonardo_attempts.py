"""
Final attempts with different Leonardo settings
If these don't work, we need a different solution
"""

import asyncio
import os
import aiohttp
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

async def quick_test_different_settings():
    """Try completely different parameter combinations"""
    
    LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
    headers = {"Authorization": f"Bearer {LEONARDO_API_KEY}", "Content-Type": "application/json"}
    backyard_path = r"C:\Users\Not John Or Justin\Documents\instabids\test-images\YOUR_ACTUAL_BACKYARD.jpg"
    
    print("FINAL LEONARDO ATTEMPTS")
    print("=" * 50)
    
    # Upload backyard once
    async with aiohttp.ClientSession() as session:
        async with session.post("https://cloud.leonardo.ai/api/rest/v1/init-image", headers=headers, json={"extension": "jpg"}) as response:
            result = await response.json()
            upload_data = result.get("uploadInitImage", {})
            upload_id, upload_url, upload_fields = upload_data.get("id"), upload_data.get("url"), upload_data.get("fields", {})
            
            with open(backyard_path, "rb") as f: image_data = f.read()
            form_data = aiohttp.FormData()
            if isinstance(upload_fields, str): upload_fields = json.loads(upload_fields)
            for key, value in upload_fields.items(): form_data.add_field(key, value)
            form_data.add_field('file', image_data, filename='image.jpg', content_type='image/jpeg')
            
            await session.post(upload_url, data=form_data)
    
    # Test different approaches quickly
    tests = [
        {
            "name": "Very low strength - minimal change",
            "init_strength": 0.10,
            "guidance_scale": 6,
            "prompt": "Replace grass with artificial turf, preserve everything else exactly"
        },
        {
            "name": "Different model - DreamShaper",
            "modelId": "ac614f96-1082-45bf-be9d-757f2d31c174",
            "init_strength": 0.15,
            "guidance_scale": 7,
            "prompt": "Artificial turf lawn, keep structures identical"
        }
    ]
    
    results = []
    for i, test in enumerate(tests):
        print(f"\nTest {i+1}: {test['name']}")
        
        gen_data = {
            "height": 768, "width": 1024,
            "modelId": test.get("modelId", "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3"),
            "prompt": test["prompt"],
            "negative_prompt": "changed layout, different structures, altered buildings",
            "num_images": 1,
            "init_image_id": upload_id,
            "init_strength": test["init_strength"],
            "guidance_scale": test["guidance_scale"]
        }
        
        try:
            async with session.post("https://cloud.leonardo.ai/api/rest/v1/generations", headers=headers, json=gen_data) as response:
                if response.status == 200:
                    result = await response.json()
                    gen_id = result.get("sdGenerationJob", {}).get("generationId")
                    if gen_id:
                        print(f"Started: {gen_id}")
                        # Quick check after 30 seconds
                        await asyncio.sleep(30)
                        async with session.get(f"https://cloud.leonardo.ai/api/rest/v1/generations/{gen_id}", headers=headers) as status_resp:
                            if status_resp.status == 200:
                                status_result = await status_resp.json()
                                if status_result.get("generations_by_pk", {}).get("status") == "COMPLETE":
                                    images = status_result.get("generations_by_pk", {}).get("generated_images", [])
                                    if images:
                                        results.append({"name": test["name"], "url": images[0].get("url")})
                                        print(f"Result: {images[0].get('url')}")
        except:
            print(f"Failed")
    
    print(f"\nFINAL RESULTS: {len(results)} completed")
    for result in results:
        print(f"{result['name']}: {result['url']}")
    
    if len(results) == 0:
        print("\nLEONARDO ISN'T WORKING FOR THIS USE CASE")
        print("Need to explore alternatives:")
        print("1. Different AI service (Midjourney, RunwayML, etc.)")  
        print("2. Specialized image editing tools")
        print("3. Different approach entirely")

if __name__ == "__main__":
    asyncio.run(quick_test_different_settings())