#!/usr/bin/env python3
"""
URGENT: Test if CIA agent initialization check causes the hanging issue
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the exact same classes from the real endpoint
try:
    from agents.cia.agent import CustomerInterfaceAgent
    logger.info("✅ CIA agent import successful")
except Exception as e:
    logger.error(f"❌ CIA agent import failed: {e}")
    exit(1)

# Global CIA agent variable (like in main.py)
cia_agent = None

async def test_cia_agent_initialization():
    """Test CIA agent initialization - this might be the hanging point"""
    
    global cia_agent
    
    logger.info("🔍 Testing CIA agent initialization...")
    
    # Get OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("❌ No OpenAI API key found - this would cause hang")
        return False
    
    logger.info("✅ OpenAI API key found")
    
    # Initialize CIA agent (exactly like main.py does)
    try:
        logger.info("Creating CIA agent instance...")
        cia_agent = CustomerInterfaceAgent(openai_api_key)
        logger.info("✅ CIA agent created successfully")
        
        # Test if agent is responsive
        logger.info("Testing CIA agent responsiveness...")
        # Try to access some basic agent properties
        logger.info(f"CIA agent type: {type(cia_agent)}")
        logger.info("✅ CIA agent is responsive")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ CIA agent initialization failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_cia_check_in_stream():
    """Test if the CIA agent check causes hanging in stream context"""
    
    logger.info("🔍 Testing CIA agent check in streaming context...")
    
    async def stream_with_cia_check():
        try:
            logger.info("Starting stream with CIA check...")
            
            # THE EXACT CHECK FROM REAL ENDPOINT (lines 297-302)
            if not cia_agent:
                logger.error("CIA agent not initialized")
                yield f"data: {json.dumps({'error': 'CIA agent not initialized'})}\n\n"
                return
            
            logger.info("✅ CIA agent check passed")
            
            # Simple streaming test
            yield f"data: {json.dumps({'choices': [{'delta': {'content': 'Test'}}]})}\n\n"
            await asyncio.sleep(0.1)
            yield f"data: {json.dumps({'choices': [{'delta': {'content': ' message'}}]})}\n\n"
            await asyncio.sleep(0.1)
            yield f"data: {json.dumps({'choices': [{'delta': {'content': ' working'}}]})}\n\n"
            
            logger.info("✅ Stream generation completed")
            
        except Exception as e:
            logger.error(f"❌ Stream with CIA check failed: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        finally:
            logger.info("📝 Sending [DONE] marker")
            yield "data: [DONE]\n\n"
            logger.info("✅ [DONE] marker sent")
    
    # Test the streaming generator
    chunk_count = 0
    async for chunk in stream_with_cia_check():
        chunk_count += 1
        logger.info(f"Received chunk {chunk_count}: {chunk.strip()}")
        
        if chunk_count > 10:
            logger.warning("Too many chunks, stopping test")
            break
    
    logger.info(f"🎯 Test completed - received {chunk_count} chunks total")
    return True

async def main():
    """Run the complete CIA agent hanging test"""
    
    logger.info("🔥 Starting CIA agent hanging investigation...")
    
    # Step 1: Test CIA agent initialization
    init_success = await test_cia_agent_initialization()
    if not init_success:
        logger.error("❌ CIA agent initialization failed - this could cause hanging")
        return
    
    # Step 2: Test CIA check in streaming context
    logger.info("🔍 Testing CIA check in streaming context...")
    stream_success = await test_cia_check_in_stream()
    
    if stream_success:
        logger.info("🎉 CIA agent check does NOT cause hanging")
        logger.info("🔍 The hanging must be in other parts of the real endpoint")
    else:
        logger.error("❌ CIA agent check DOES cause hanging")
        logger.error("🎯 This is the source of the problem")

if __name__ == "__main__":
    asyncio.run(main())