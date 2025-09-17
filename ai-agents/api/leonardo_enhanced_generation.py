"""
Leonardo.ai Enhanced Image Generation API with Multi-Reference Support
For Agent 3 (Homeowner UX) - Iris System

This enhanced version provides:
1. Automatic image classification by purpose
2. Multi-reference support with proper tags
3. Optimal ControlNet configuration per image type
4. Progress tracking and status updates
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import aiohttp
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import Client, create_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Leonardo.ai API Configuration
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
LEONARDO_API_BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"

# Initialize Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None

# Image classification rules
IMAGE_CLASSIFICATION_RULES = {
    "current": {
        "tags": ["current", "current-state", "before", "existing"],
        "purpose": "structure_reference",
        "controlnet_config": {
            "preprocessor_id": 19,  # Canny edge detection for structure
            "strength": 0.8
        }
    },
    "turf_texture": {
        "tags": ["turf", "artificial-grass", "texture", "material"],
        "purpose": "texture_reference",
        "controlnet_config": {
            "preprocessor_id": 67,  # Style transfer
            "strength": 0.9
        }
    },
    "color_reference": {
        "tags": ["color", "palette", "tone", "mood"],
        "purpose": "color_reference",
        "controlnet_config": {
            "preprocessor_id": 133,  # Character reference
            "strength": 0.6
        }
    },
    "overall_style": {
        "tags": ["style", "inspiration", "ideal", "goal"],
        "purpose": "style_reference",
        "controlnet_config": {
            "preprocessor_id": 67,  # Style transfer
            "strength": 0.7
        }
    }
}

class ImageUploadRequest(BaseModel):
    """Request model for image upload with classification"""
    image_url: str
    tags: List[str]
    board_id: str
    title: Optional[str] = None
    description: Optional[str] = None

class MultiReferenceGenerationRequest(BaseModel):
    """Request for multi-reference image generation"""
    board_id: str
    base_image_id: str  # Current backyard image
    reference_image_ids: List[str]  # Multiple reference images
    prompt: str
    user_preferences: Optional[str] = None

class GenerationStatusResponse(BaseModel):
    """Response model for generation status"""
    generation_id: str
    status: str
    progress: int
    message: str
    generated_images: Optional[List[str]] = None
    error: Optional[str] = None

async def classify_image_purpose(tags: List[str]) -> Dict[str, Any]:
    """
    Classify image purpose based on tags for optimal ControlNet configuration
    """
    # Check each classification rule
    for purpose, config in IMAGE_CLASSIFICATION_RULES.items():
        # Check if any of the image's tags match the rule's tags
        if any(tag.lower() in [t.lower() for t in config["tags"]] for tag in tags):
            return {
                "purpose": config["purpose"],
                "controlnet_config": config["controlnet_config"],
                "classification": purpose
            }
    
    # Default classification
    return {
        "purpose": "general_reference",
        "controlnet_config": {
            "preprocessor_id": 67,
            "strength": 0.5
        },
        "classification": "general"
    }

async def upload_and_classify_image(image_url: str, tags: List[str]) -> Dict[str, Any]:
    """
    Upload image to Leonardo and classify its purpose
    """
    try:
        # Upload to Leonardo
        headers = {
            "Authorization": f"Bearer {LEONARDO_API_KEY}",
            "Content-Type": "application/json"
        }
        
        upload_data = {
            "imageUrl": image_url
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{LEONARDO_API_BASE_URL}/generations/image2image/upload",
                headers=headers,
                json=upload_data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(status_code=response.status, detail=f"Leonardo upload failed: {error_text}")
                
                result = await response.json()
                leonardo_id = result.get("uploadInitImage", {}).get("id")
                
                if not leonardo_id:
                    raise HTTPException(status_code=500, detail="Failed to get Leonardo image ID")
                
                # Classify the image purpose
                classification = await classify_image_purpose(tags)
                
                return {
                    "leonardo_id": leonardo_id,
                    "original_url": image_url,
                    "tags": tags,
                    **classification
                }
                
    except Exception as e:
        logger.error(f"Error uploading/classifying image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/leonardo/upload-and-classify", response_model=Dict[str, Any])
async def upload_and_classify_endpoint(request: ImageUploadRequest):
    """
    Upload an image to Leonardo and classify its purpose for transformation
    """
    try:
        result = await upload_and_classify_image(request.image_url, request.tags)
        
        # Store classification in database if board_id provided
        if request.board_id and supabase:
            classification_record = {
                "id": str(uuid4()),
                "board_id": request.board_id,
                "leonardo_id": result["leonardo_id"],
                "original_url": request.image_url,
                "tags": request.tags,
                "classification": result["classification"],
                "purpose": result["purpose"],
                "title": request.title,
                "description": request.description,
                "created_at": datetime.now().isoformat()
            }
            
            # Store in a new table for Leonardo classifications
            supabase.table("leonardo_image_classifications").insert(classification_record).execute()
        
        return result
        
    except Exception as e:
        logger.error(f"Upload and classification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/leonardo/generate-multi-reference", response_model=GenerationStatusResponse)
async def generate_with_multiple_references(request: MultiReferenceGenerationRequest):
    """
    Generate image using multiple reference images with different purposes
    """
    try:
        # Get base image info from database
        base_image_result = supabase.table("inspiration_images").select("*").eq("id", request.base_image_id).execute()
        if not base_image_result.data:
            raise HTTPException(status_code=404, detail="Base image not found")
        base_image = base_image_result.data[0]
        
        # Upload base image to Leonardo
        base_leonardo = await upload_and_classify_image(
            base_image.get("image_url"),
            base_image.get("generated_tags", ["current"])
        )
        
        # Process reference images
        reference_configs = []
        for ref_id in request.reference_image_ids:
            ref_result = supabase.table("inspiration_images").select("*").eq("id", ref_id).execute()
            if ref_result.data:
                ref_image = ref_result.data[0]
                ref_leonardo = await upload_and_classify_image(
                    ref_image.get("image_url"),
                    ref_image.get("generated_tags", [])
                )
                reference_configs.append(ref_leonardo)
        
        # Build generation request with multi-reference support
        generation_data = {
            "prompt": request.prompt,
            "negative_prompt": "blurry, low quality, distorted, unrealistic",
            "modelId": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",  # Leonardo Phoenix
            "width": 1024,
            "height": 768,
            "num_images": 1,
            "init_image_id": base_leonardo["leonardo_id"],
            "init_strength": 0.3,  # Keep structure from base image
            "controlnets": []
        }
        
        # Add ControlNet configurations for each reference
        for ref_config in reference_configs:
            controlnet = {
                "initImageId": ref_config["leonardo_id"],
                "preprocessorId": ref_config["controlnet_config"]["preprocessor_id"],
                "strengthType": "High",
                "weight": ref_config["controlnet_config"]["strength"]
            }
            generation_data["controlnets"].append(controlnet)
        
        # Start generation
        headers = {
            "Authorization": f"Bearer {LEONARDO_API_KEY}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{LEONARDO_API_BASE_URL}/generations",
                headers=headers,
                json=generation_data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(status_code=response.status, detail=f"Generation failed: {error_text}")
                
                result = await response.json()
                generation_id = result.get("sdGenerationJob", {}).get("generationId")
                
                if not generation_id:
                    raise HTTPException(status_code=500, detail="Failed to start generation")
                
                # Store generation record
                if supabase:
                    generation_record = {
                        "id": generation_id,
                        "board_id": request.board_id,
                        "base_image_id": request.base_image_id,
                        "reference_image_ids": request.reference_image_ids,
                        "prompt": request.prompt,
                        "user_preferences": request.user_preferences,
                        "status": "processing",
                        "created_at": datetime.now().isoformat()
                    }
                    supabase.table("leonardo_generations").insert(generation_record).execute()
                
                return GenerationStatusResponse(
                    generation_id=generation_id,
                    status="processing",
                    progress=0,
                    message="Generation started with multi-reference configuration"
                )
                
    except Exception as e:
        logger.error(f"Multi-reference generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/leonardo/status/{generation_id}", response_model=GenerationStatusResponse)
async def check_generation_status(generation_id: str):
    """
    Check the status of a Leonardo generation
    """
    try:
        headers = {
            "Authorization": f"Bearer {LEONARDO_API_KEY}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{LEONARDO_API_BASE_URL}/generations/{generation_id}",
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(status_code=response.status, detail=f"Status check failed: {error_text}")
                
                result = await response.json()
                generation = result.get("generations_by_pk", {})
                
                status = generation.get("status", "UNKNOWN")
                
                # Map Leonardo status to our status
                if status == "COMPLETE":
                    # Get generated images
                    images = generation.get("generated_images", [])
                    image_urls = [img.get("url") for img in images if img.get("url")]
                    
                    # Update database record
                    if supabase:
                        supabase.table("leonardo_generations").update({
                            "status": "completed",
                            "generated_images": image_urls,
                            "completed_at": datetime.now().isoformat()
                        }).eq("id", generation_id).execute()
                    
                    return GenerationStatusResponse(
                        generation_id=generation_id,
                        status="completed",
                        progress=100,
                        message="Generation completed successfully",
                        generated_images=image_urls
                    )
                elif status == "FAILED":
                    error_msg = generation.get("error", "Unknown error")
                    
                    # Update database record
                    if supabase:
                        supabase.table("leonardo_generations").update({
                            "status": "failed",
                            "error": error_msg
                        }).eq("id", generation_id).execute()
                    
                    return GenerationStatusResponse(
                        generation_id=generation_id,
                        status="failed",
                        progress=0,
                        message="Generation failed",
                        error=error_msg
                    )
                else:
                    # Still processing
                    progress = 50 if status == "PROCESSING" else 25
                    
                    return GenerationStatusResponse(
                        generation_id=generation_id,
                        status="processing",
                        progress=progress,
                        message=f"Generation in progress: {status}"
                    )
                    
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/leonardo/generate-backyard-transformation")
async def generate_backyard_transformation(request: Dict[str, Any]):
    """
    Specialized endpoint for backyard turf transformations
    Automatically classifies and processes images for optimal results
    """
    try:
        board_id = request.get("board_id")
        
        # Get all images for the board
        images_result = supabase.table("inspiration_images").select("*").eq("board_id", board_id).execute()
        if not images_result.data:
            raise HTTPException(status_code=404, detail="No images found for board")
        
        images = images_result.data
        
        # Classify images by their tags
        current_image = None
        turf_images = []
        style_images = []
        
        for img in images:
            tags = img.get("generated_tags", [])
            tags_lower = [t.lower() for t in tags]
            
            if any(tag in tags_lower for tag in ["current", "before", "existing"]):
                current_image = img
            elif any(tag in tags_lower for tag in ["turf", "artificial", "grass", "texture"]):
                turf_images.append(img)
            elif any(tag in tags_lower for tag in ["style", "inspiration", "ideal"]):
                style_images.append(img)
        
        if not current_image:
            raise HTTPException(status_code=400, detail="No current backyard image found")
        
        # Build optimized prompt for backyard transformation
        prompt = f"""Transform this backyard with artificial turf installation.
        Maintain exact layout, soccer goal position, and all existing structures.
        Replace patchy grass areas with lush, realistic artificial turf.
        Keep surrounding landscaping, trees, and features unchanged.
        Professional landscape transformation, photorealistic quality.
        {request.get('user_preferences', '')}"""
        
        # Prepare reference images
        reference_ids = []
        if turf_images:
            reference_ids.extend([img["id"] for img in turf_images[:2]])  # Max 2 turf references
        if style_images:
            reference_ids.extend([img["id"] for img in style_images[:1]])  # Max 1 style reference
        
        # Generate with multi-reference
        generation_request = MultiReferenceGenerationRequest(
            board_id=board_id,
            base_image_id=current_image["id"],
            reference_image_ids=reference_ids,
            prompt=prompt,
            user_preferences=request.get("user_preferences")
        )
        
        result = await generate_with_multiple_references(generation_request)
        
        return {
            "success": True,
            "generation_id": result.generation_id,
            "message": "Backyard transformation started with optimized settings",
            "image_classification": {
                "current": current_image["id"],
                "turf_references": [img["id"] for img in turf_images],
                "style_references": [img["id"] for img in style_images]
            }
        }
        
    except Exception as e:
        logger.error(f"Backyard transformation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Create database tables if they don't exist
async def create_leonardo_tables():
    """Create Leonardo-specific tables in Supabase"""
    if not supabase:
        logger.warning("Supabase not configured, skipping table creation")
        return
    
    try:
        # These would normally be created via Supabase migrations
        # Including here for documentation purposes
        leonardo_classifications_schema = """
        CREATE TABLE IF NOT EXISTS leonardo_image_classifications (
            id UUID PRIMARY KEY,
            board_id UUID REFERENCES inspiration_boards(id),
            leonardo_id TEXT NOT NULL,
            original_url TEXT NOT NULL,
            tags TEXT[],
            classification TEXT,
            purpose TEXT,
            title TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
        
        leonardo_generations_schema = """
        CREATE TABLE IF NOT EXISTS leonardo_generations (
            id TEXT PRIMARY KEY,
            board_id UUID REFERENCES inspiration_boards(id),
            base_image_id UUID,
            reference_image_ids UUID[],
            prompt TEXT,
            user_preferences TEXT,
            status TEXT,
            generated_images TEXT[],
            error TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            completed_at TIMESTAMP
        );
        """
        
        logger.info("Leonardo tables schema defined (create via Supabase dashboard)")
        
    except Exception as e:
        logger.error(f"Error defining Leonardo tables: {e}")

# Initialize tables on startup
@router.on_event("startup")
async def startup_event():
    await create_leonardo_tables()