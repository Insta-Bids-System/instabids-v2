#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.append('C:/Users/Not John Or Justin/Documents/instabids/ai-agents')

# Import the actual API function
from api.image_generation import generate_dream_space, GenerateDreamSpaceRequest, supabase

import asyncio

async def test_api_directly():
    print("TESTING API FUNCTION DIRECTLY")
    print("=" * 60)
    
    # Check Supabase client
    print(f"Supabase client exists: {supabase is not None}")
    print(f"Supabase URL: {os.getenv('SUPABASE_URL')}")
    
    # Create request object
    request = GenerateDreamSpaceRequest(
        board_id="26cf972b-83e4-484c-98b6-a5d1a4affee3",
        ideal_image_id="115f9265-e462-458f-a159-568790fc6941",
        current_image_id="5d46e708-3f0c-4985-9617-68afd8e2892b",
        user_preferences="DIRECT TEST: Add modern pendant lighting"
    )
    
    print(f"\nCalling generate_dream_space directly...")
    
    # Call the API function directly
    try:
        result = await generate_dream_space(request)
        
        print(f"\nRESULT:")
        print(f"Success: {result.get('success')}")
        print(f"Generated URL: {result.get('generated_image_url', '')[:50]}...")
        print(f"Saved as Vision: {result.get('saved_as_vision')}")
        print(f"Debug Info: {result.get('debug_vision_save')}")
        
        # Check database directly
        print(f"\nChecking database for new images...")
        from datetime import datetime, timedelta
        
        # Look for images created in last 5 minutes
        five_min_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
        
        db_result = supabase.table("inspiration_images").select("*").eq("board_id", request.board_id).gte("created_at", five_min_ago).execute()
        
        print(f"Recent images in database: {len(db_result.data)}")
        
        if db_result.data:
            for img in db_result.data:
                print(f"  - {img.get('id')}: created {img.get('created_at')}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

# Run the async test
asyncio.run(test_api_directly())