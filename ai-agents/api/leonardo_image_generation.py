"""
Leonardo.ai Image Generation API - REAL Professional Image Transformation
Replaces DALL-E system with structure-preserving multi-reference image generation
"""

import os
import json
import asyncio
import aiohttp
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import Client, create_client
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(env_path, override=True)

router = APIRouter(prefix="/api/leonardo", tags=["leonardo-ai"])

# Leonardo.ai Configuration
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
LEONARDO_BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"

if not LEONARDO_API_KEY:
    print("WARNING: LEONARDO_API_KEY not found in environment")

# Supabase Configuration
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Leonardo.ai Models
LEONARDO_MODELS = {
    "phoenix": "aa77f04e-3eec-4034-9c07-d0f619684628",  # Best for photorealism
    "sdxl": "e316348f-7773-490e-adcd-46757c738eb7",     # Alternative high quality
}

# Preprocessor IDs for different control types
PREPROCESSORS = {
    "structure": 19,    # Edge to Image - preserves layout/structure  
    "style": 67,        # Style Reference - transfers texture/appearance
    "character": 133,   # Character Reference - for people/objects
    "depth": 8,         # Depth to Image - 3D structure preservation
}

class MultiImageGenerationRequest(BaseModel):
    board_id: str
    base_image_id: str  # The "current" image to transform
    reference_images: List[Dict[str, Any]]  # [{"id": "...", "tags": [...], "purpose": "..."}]
    prompt: str = "professional landscape photo, artificial turf, perfect lighting"
    custom_prompt: Optional[str] = None
    user_preferences: Optional[str] = None

class LeonardoGenerationResponse(BaseModel):
    success: bool
    generation_id: Optional[str] = None
    generated_image_url: Optional[str] = None
    leonardo_generation_id: Optional[str] = None
    message: str
    processing_time: Optional[float] = None

async def upload_image_to_leonardo(image_url: str) -> str:
    """
    Upload an image from Supabase to Leonardo.ai for use as reference
    Returns Leonardo image ID
    """
    async with aiohttp.ClientSession() as session:
        try:
            # Download image from Supabase URL
            async with session.get(image_url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to download image: {response.status}")
                image_data = await response.read()
            
            # Upload to Leonardo.ai
            form_data = aiohttp.FormData()
            form_data.add_field('image', image_data, filename='reference.jpg', content_type='image/jpeg')
            
            async with session.post(
                f"{LEONARDO_BASE_URL}/init-image",
                data=form_data,
                headers={"Authorization": f"Bearer {LEONARDO_API_KEY}"}
            ) as upload_response:
                if upload_response.status != 200:
                    error_text = await upload_response.text()
                    raise Exception(f"Leonardo upload failed: {upload_response.status} - {error_text}")
                
                upload_result = await upload_response.json()
                return upload_result["uploadInitImageId"]
                
        except Exception as e:
            print(f"Error uploading image to Leonardo: {str(e)}")
            raise

def classify_reference_for_controlnet(image_tags: List[str], purpose: str) -> Dict[str, Any]:
    """
    Classify reference image and determine ControlNet parameters
    """
    # Base image (current backyard) - preserve structure
    if "current" in image_tags or purpose == "base":
        return {
            "preprocessorId": PREPROCESSORS["structure"],  # Edge detection
            "strengthType": "High",  # Rigid structure preservation
            "influence": 1.0
        }
    
    # Texture references (artificial turf, materials)
    elif any(tag in image_tags for tag in ["turf_texture", "texture", "material"]):
        return {
            "preprocessorId": PREPROCESSORS["style"],  # Style transfer
            "strengthType": "Mid",
            "influence": 0.8  # Strong texture influence
        }
    
    # Color references  
    elif any(tag in image_tags for tag in ["color_reference", "color", "palette"]):
        return {
            "preprocessorId": PREPROCESSORS["style"],
            "strengthType": "Low", 
            "influence": 0.6  # Moderate color influence
        }
    
    # Overall style/aesthetic references
    elif any(tag in image_tags for tag in ["overall_style", "style", "professional"]):
        return {
            "preprocessorId": PREPROCESSORS["style"],
            "strengthType": "Low",
            "influence": 0.3  # Subtle overall influence
        }
    
    # Default for any other reference
    else:
        return {
            "preprocessorId": PREPROCESSORS["style"],
            "strengthType": "Mid",
            "influence": 0.5
        }

async def generate_with_leonardo(
    base_leonardo_id: str,
    reference_leonardo_ids: List[Dict[str, Any]],
    prompt: str
) -> Dict[str, Any]:
    """
    Generate image using Leonardo.ai with multiple ControlNets
    """
    # Build ControlNet array
    controlnets = []
    
    # Add base image for structure preservation
    controlnets.append({
        "initImageId": base_leonardo_id,
        "initImageType": "UPLOADED", 
        "preprocessorId": PREPROCESSORS["structure"],
        "strengthType": "High",
        "influence": 1.0
    })
    
    # Add reference images
    for ref in reference_leonardo_ids:
        controlnet_params = classify_reference_for_controlnet(
            ref.get("tags", []), 
            ref.get("purpose", "")
        )
        
        controlnets.append({
            "initImageId": ref["leonardo_id"],
            "initImageType": "UPLOADED",
            **controlnet_params
        })
    
    # Generation payload
    generation_payload = {
        "height": 1024,
        "width": 1024, 
        "modelId": LEONARDO_MODELS["phoenix"],  # Use Phoenix for best photorealism
        "prompt": prompt,
        "alchemy": True,  # Enhanced quality
        "photoReal": True,
        "photoRealVersion": "v2",
        "controlnets": controlnets,
        "num_images": 1
    }
    
    print(f"Leonardo generation payload: {json.dumps(generation_payload, indent=2)}")
    
    # Make generation request
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{LEONARDO_BASE_URL}/generations",
            json=generation_payload,
            headers={
                "Authorization": f"Bearer {LEONARDO_API_KEY}",
                "Content-Type": "application/json"
            }
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Leonardo generation failed: {response.status} - {error_text}")
            
            result = await response.json()
            return result

async def poll_leonardo_generation(generation_id: str, max_attempts: int = 60) -> Optional[str]:
    """
    Poll Leonardo.ai for generation completion and return image URL
    """
    async with aiohttp.ClientSession() as session:
        for attempt in range(max_attempts):
            try:
                async with session.get(
                    f"{LEONARDO_BASE_URL}/generations/{generation_id}",
                    headers={"Authorization": f"Bearer {LEONARDO_API_KEY}"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        generation_data = result.get("generations_by_pk", {})
                        status = generation_data.get("status")
                        
                        if status == "COMPLETE":
                            generated_images = generation_data.get("generated_images", [])
                            if generated_images:
                                return generated_images[0]["url"]
                        
                        elif status == "FAILED":
                            raise Exception("Leonardo generation failed")
                        
                        # Still processing, wait and retry
                        await asyncio.sleep(2)
                        
            except Exception as e:
                print(f"Error polling generation {generation_id}: {str(e)}")
                await asyncio.sleep(2)
    
    raise Exception("Generation timed out")

@router.post("/generate-dream-space", response_model=LeonardoGenerationResponse)
async def generate_dream_space_leonardo(request: MultiImageGenerationRequest):
    """
    Generate dream space using Leonardo.ai multi-reference workflow
    This replaces the DALL-E 3 system with real image transformation
    """
    start_time = datetime.now()
    
    try:
        # 1. Get base image from database
        base_image = supabase.table("inspiration_images").select("*").eq("id", request.base_image_id).single().execute()
        if not base_image.data:
            raise HTTPException(status_code=404, detail="Base image not found")
        
        print(f"Base image found: {request.base_image_id}")
        
        # 2. Upload base image to Leonardo
        base_leonardo_id = await upload_image_to_leonardo(base_image.data["image_url"])
        print(f"Base image uploaded to Leonardo: {base_leonardo_id}")
        
        # 3. Process reference images
        reference_leonardo_ids = []
        for ref_img in request.reference_images:
            # Get reference image from database
            ref_data = supabase.table("inspiration_images").select("*").eq("id", ref_img["id"]).single().execute()
            if ref_data.data:
                # Upload to Leonardo
                leonardo_id = await upload_image_to_leonardo(ref_data.data["image_url"])
                reference_leonardo_ids.append({
                    "leonardo_id": leonardo_id,
                    "tags": ref_img.get("tags", []),
                    "purpose": ref_img.get("purpose", "")
                })
                print(f"Reference image {ref_img['id']} uploaded: {leonardo_id}")
        
        # 4. Generate with Leonardo.ai
        generation_prompt = request.custom_prompt or request.prompt
        if request.user_preferences:
            generation_prompt += f". {request.user_preferences}"
        
        leonardo_result = await generate_with_leonardo(
            base_leonardo_id,
            reference_leonardo_ids, 
            generation_prompt
        )
        
        leonardo_generation_id = leonardo_result["sdGenerationJob"]["generationId"]
        print(f"Leonardo generation started: {leonardo_generation_id}")
        
        # 5. Poll for completion
        generated_image_url = await poll_leonardo_generation(leonardo_generation_id)
        print(f"Generation complete: {generated_image_url[:50]}...")
        
        # 6. Save to database
        generation_record = {
            "board_id": request.board_id,
            "ideal_image_id": request.reference_images[0]["id"] if request.reference_images else request.base_image_id,
            "current_image_id": request.base_image_id,
            "generated_image_url": generated_image_url,
            "dalle_prompt": generation_prompt,  # Keep field name for compatibility
            "generation_metadata": {
                "model": "leonardo-phoenix",
                "controlnets": len(reference_leonardo_ids) + 1,
                "leonardo_generation_id": leonardo_generation_id,
                "base_image_id": request.base_image_id,
                "reference_count": len(request.reference_images),
                "timestamp": datetime.now().isoformat()
            },
            "status": "generated"
        }
        
        db_result = supabase.table("generated_dream_spaces").insert(generation_record).execute()
        db_generation_id = db_result.data[0]["id"] if db_result.data else None
        
        # 7. Also save as vision image
        vision_record = {
            "board_id": request.board_id,
            "user_id": "550e8400-e29b-41d4-a716-446655440001",  # Demo user
            "image_url": generated_image_url,
            "thumbnail_url": generated_image_url,
            "source": "url",
            "tags": ["vision", "ai_generated", "leonardo_ai", "multi_reference"],
            "ai_analysis": {
                "description": "Leonardo.ai generated transformation with multiple references",
                "method": "Leonardo.ai Phoenix + ControlNet",
                "base_image_id": request.base_image_id,
                "reference_count": len(request.reference_images),
                "controlnet_types": ["structure_preservation", "style_transfer"]
            },
            "category": "ideal",
            "position": 0
        }
        
        vision_result = supabase.table("inspiration_images").insert(vision_record).execute()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return LeonardoGenerationResponse(
            success=True,
            generation_id=db_generation_id,
            generated_image_url=generated_image_url,
            leonardo_generation_id=leonardo_generation_id,
            message="Professional image transformation completed successfully using Leonardo.ai",
            processing_time=processing_time
        )
        
    except Exception as e:
        print(f"Leonardo generation error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return LeonardoGenerationResponse(
            success=False,
            message=f"Generation failed: {str(e)}"
        )

@router.get("/generation-status/{leonardo_generation_id}")
async def get_generation_status(leonardo_generation_id: str):
    """
    Check the status of a Leonardo.ai generation
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{LEONARDO_BASE_URL}/generations/{leonardo_generation_id}",
                headers={"Authorization": f"Bearer {LEONARDO_API_KEY}"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    raise HTTPException(status_code=response.status, detail="Failed to get generation status")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def get_available_models():
    """
    Get available Leonardo.ai models
    """
    return {
        "available_models": LEONARDO_MODELS,
        "preprocessors": PREPROCESSORS,
        "recommended": "phoenix"
    }