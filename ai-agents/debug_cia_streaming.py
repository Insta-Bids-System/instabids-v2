#!/usr/bin/env python3
"""
URGENT: Debug CIA streaming endpoint hanging issue
"""

import asyncio
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_cia_streaming_step_by_step():
    """Test each step of CIA streaming to find where it hangs"""
    
    logger.info("🔍 Step 1: Testing basic async generator")
    
    async def basic_generator():
        logger.info("Generator started")
        yield "data: test1\n\n"
        await asyncio.sleep(0.1)
        yield "data: test2\n\n"
        await asyncio.sleep(0.1)
        yield "data: [DONE]\n\n"
        logger.info("Generator completed")
    
    # Test basic generator
    async for chunk in basic_generator():
        logger.info(f"Received: {chunk.strip()}")
    
    logger.info("✅ Step 1 passed - basic generator works")
    
    logger.info("🔍 Step 2: Testing imports")
    try:
        from agents.cia.agent import CustomerInterfaceAgent
        logger.info("✅ CIA agent import works")
        
        from openai import AsyncOpenAI
        logger.info("✅ OpenAI import works")
        
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            logger.info("✅ OpenAI API key found")
        else:
            logger.error("❌ No OpenAI API key")
            
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        return
    
    logger.info("🔍 Step 3: Testing OpenAI client creation")
    try:
        client = AsyncOpenAI(api_key=api_key)
        logger.info("✅ OpenAI client created successfully")
    except Exception as e:
        logger.error(f"❌ OpenAI client creation failed: {e}")
        return
    
    logger.info("🔍 Step 4: Testing simple OpenAI streaming call")
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello"}
        ]
        
        logger.info("Making OpenAI streaming request...")
        stream = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_completion_tokens=50,
            stream=True
        )
        
        logger.info("✅ OpenAI stream created, reading chunks...")
        chunk_count = 0
        async for chunk in stream:
            chunk_count += 1
            if chunk.choices and chunk.choices[0].delta.content:
                logger.info(f"Chunk {chunk_count}: {chunk.choices[0].delta.content}")
            if chunk_count > 10:  # Limit for testing
                break
                
        logger.info(f"✅ OpenAI streaming works - got {chunk_count} chunks")
        
    except Exception as e:
        logger.error(f"❌ OpenAI streaming failed: {e}")
        return
    
    logger.info("🔍 Step 5: Testing database connection")
    try:
        from database_simple import db
        
        # Test simple query
        result = db.client.table("bid_cards").select("id").limit(1).execute()
        logger.info(f"✅ Database query works - got {len(result.data)} results")
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return
    
    logger.info("🎯 All components work individually - issue must be in the endpoint logic")

if __name__ == "__main__":
    asyncio.run(test_cia_streaming_step_by_step())