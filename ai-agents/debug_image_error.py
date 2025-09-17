#!/usr/bin/env python3
"""
Debug the exact error in image analysis
"""

import asyncio
import traceback
from agents.intelligent_messaging_agent import GPT5SecurityAnalyzer

async def debug_image_error():
    """Debug what's causing the image analysis error"""
    
    try:
        # Create the analyzer
        analyzer = GPT5SecurityAnalyzer()
        
        # Test with minimal data
        print("Creating analyzer...")
        print("Testing image analysis...")
        
        # Test image analysis with dummy data
        result = await analyzer.analyze_image_content("fake_base64_data", "png")
        
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        print("\nFULL TRACEBACK:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_image_error())