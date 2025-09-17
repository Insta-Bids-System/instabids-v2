#!/usr/bin/env python3
"""
URGENT: Find the exact operation that causes CIA endpoint hanging
Add operations one by one until we find the hanging point
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

# Global CIA agent (like real endpoint)
cia_agent = None

async def test_progressive_complexity():
    """Add complexity progressively until we find what hangs"""
    
    global cia_agent
    
    logger.info("🔍 Step 1: Initialize CIA agent")
    try:
        from agents.cia.agent import CustomerInterfaceAgent
        openai_api_key = os.getenv("OPENAI_API_KEY")
        cia_agent = CustomerInterfaceAgent(openai_api_key)
        logger.info("✅ CIA agent initialized")
    except Exception as e:
        logger.error(f"❌ CIA init failed: {e}")
        return
    
    logger.info("🔍 Step 2: Test basic async executor database call")
    try:
        from database_simple import db
        
        # This is the type of call in the real endpoint that might hang
        result = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: db.client.table("bid_cards").select("id").limit(1).execute()
        )
        logger.info(f"✅ Database executor call works: {len(result.data)} records")
    except Exception as e:
        logger.error(f"❌ Database executor failed: {e}")
        return
    
    logger.info("🔍 Step 3: Test complex database state loading")
    try:
        session_id = "test-session-123"
        existing_conversation = await db.load_conversation_state(session_id)
        logger.info("✅ Conversation state loading works")
    except Exception as e:
        logger.error(f"❌ Conversation state loading failed: {e}")
        # This is expected to fail, continue
    
    logger.info("🔍 Step 4: Test CIA agent call with timeout")
    try:
        # This is the complex operation from lines 645-657 that might hang
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: cia_agent.handle_conversation_with_state_management(
                    user_id="test-user",
                    message="test message",
                    images=[],
                    session_id="test-session",
                    existing_state=None,
                    project_id=None
                )
            ),
            timeout=10.0  # Short timeout to catch hanging
        )
        logger.info("✅ CIA agent state management works")
    except asyncio.TimeoutError:
        logger.error("❌ CIA agent state management TIMED OUT - THIS IS THE HANGING OPERATION!")
        return
    except Exception as e:
        logger.error(f"❌ CIA agent state management failed: {e}")
        # Could be method doesn't exist, continue
    
    logger.info("🔍 Step 5: Test bid card creation function")
    try:
        # This is from lines 679-685 that might hang
        from routers.cia_potential_bid_cards import update_potential_bid_card_from_conversation
        
        await update_potential_bid_card_from_conversation(
            session_id="test-session",
            user_id="test-user", 
            latest_message="test message",
            conversation_state=None,
            llm_response="test response"
        )
        logger.info("✅ Bid card creation works")
    except Exception as e:
        logger.error(f"❌ Bid card creation failed: {e}")
        # Continue testing
    
    logger.info("🔍 Step 6: Test streaming with all complex operations")
    
    async def complex_stream_test():
        try:
            logger.info("Starting complex stream with all operations...")
            
            # CIA agent check (we know this works)
            if not cia_agent:
                yield f"data: {json.dumps({'error': 'CIA agent not initialized'})}\n\n"
                return
            
            # Step 1: Basic streaming test
            yield f"data: {json.dumps({'choices': [{'delta': {'content': 'Starting'}}]})}\n\n"
            await asyncio.sleep(0.1)
            
            # Step 2: Add database operation during streaming
            logger.info("Adding database operation...")
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: db.client.table("bid_cards").select("id").limit(1).execute()
            )
            yield f"data: {json.dumps({'choices': [{'delta': {'content': ' db-ok'}}]})}\n\n"
            await asyncio.sleep(0.1)
            
            # Step 3: Add state management (this might hang)
            logger.info("Adding state management...")
            try:
                # Try the CIA agent operation with very short timeout
                await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: cia_agent.handle_conversation_with_state_management(
                            user_id="test-user",
                            message="test",
                            images=[],
                            session_id="test-session",
                            existing_state=None,
                            project_id=None
                        )
                    ),
                    timeout=2.0  # Very short timeout to catch hanging quickly
                )
                yield f"data: {json.dumps({'choices': [{'delta': {'content': ' state-ok'}}]})}\n\n"
            except asyncio.TimeoutError:
                logger.error("❌ STATE MANAGEMENT HANGS DURING STREAMING!")
                yield f"data: {json.dumps({'choices': [{'delta': {'content': ' state-HANG'}}]})}\n\n"
                # Continue without state management
            except Exception as state_err:
                logger.error(f"State management error: {state_err}")
                yield f"data: {json.dumps({'choices': [{'delta': {'content': ' state-error'}}]})}\n\n"
            
            await asyncio.sleep(0.1)
            yield f"data: {json.dumps({'choices': [{'delta': {'content': ' complete'}}]})}\n\n"
            
            logger.info("✅ Complex stream completed")
            
        except Exception as e:
            logger.error(f"❌ Complex stream failed: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        finally:
            logger.info("📝 Sending [DONE] marker")
            yield "data: [DONE]\n\n"
    
    # Test complex streaming
    chunk_count = 0
    async for chunk in complex_stream_test():
        chunk_count += 1
        logger.info(f"Stream chunk {chunk_count}: {chunk.strip()}")
        
        if chunk_count > 20:
            logger.warning("Too many chunks, stopping")
            break
    
    logger.info(f"🎯 Complex streaming test completed - {chunk_count} chunks")

async def main():
    logger.info("🔥 Starting progressive complexity test to find hanging operation...")
    await test_progressive_complexity()
    logger.info("🎯 Investigation complete")

if __name__ == "__main__":
    asyncio.run(main())