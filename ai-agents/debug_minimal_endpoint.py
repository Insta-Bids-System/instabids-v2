#!/usr/bin/env python3
"""
URGENT: Minimal replica of CIA streaming endpoint to find hanging point
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

# Simulate the exact same request structure
class SSEChatRequest:
    def __init__(self):
        self.messages = [{"role": "user", "content": "test message"}]
        self.conversation_id = "test-conv"
        self.user_id = "test-user"
        self.project_id = None
        self.images = []
        self.rfi_context = None

async def minimal_cia_stream_replica():
    """Exact replica of the hanging CIA stream endpoint"""
    
    request = SSEChatRequest()
    
    async def generate_universal_sse_stream():
        try:
            logger.info("🚀 Starting minimal stream generation")
            
            # === STEP 1: Extract user info ===
            logger.info("📝 Step 1: Extracting user info")
            if not request.user_id or request.user_id == "00000000-0000-0000-0000-000000000000":
                user_id = "00000000-0000-0000-0000-000000000000" 
                session_id = request.conversation_id or f"anon_{datetime.now().timestamp()}"
            else:
                user_id = request.user_id
                session_id = request.conversation_id or f"auth_{user_id}_{datetime.now().timestamp()}"
            logger.info(f"✅ User info: {user_id}, {session_id}")
            
            # === STEP 2: Extract message and images ===
            logger.info("📝 Step 2: Extracting message and images")
            latest_message = ""
            images = []
            if request.messages:
                last_msg = request.messages[-1]
                latest_message = last_msg.get("content", "")
                images = last_msg.get("images", [])
            
            if not images and request.images:
                images = request.images
            logger.info(f"✅ Message: '{latest_message}', Images: {len(images)}")
            
            # === STEP 3: Project context loading ===
            logger.info("📝 Step 3: Project context loading")
            project_id = request.project_id
            bid_card_context = None
            if project_id:
                logger.info(f"Loading project context for: {project_id}")
                # THIS MIGHT BE THE HANGING POINT - async executor
                from database_simple import db
                try:
                    bid_card_result = await asyncio.get_event_loop().run_in_executor(
                        None, 
                        lambda: db.client.table("bid_cards").select("*").eq("id", project_id).execute()
                    )
                    logger.info("✅ Project context query completed")
                except Exception as e:
                    logger.error(f"❌ Project context query failed: {e}")
            else:
                logger.info("✅ No project context needed")
            
            # === STEP 4: RFI context handling ===
            logger.info("📝 Step 4: RFI context handling")
            if request.rfi_context:
                logger.info("Processing RFI context")
            else:
                logger.info("✅ No RFI context")
            
            # === STEP 5: Image analysis ===
            logger.info("📝 Step 5: Image analysis")
            if images:
                logger.info("Would analyze images here")
            else:
                logger.info("✅ No images to analyze")
            
            # === STEP 6: Load conversation state ===
            logger.info("📝 Step 6: Loading conversation state")
            try:
                from database_simple import db
                existing_conversation = await db.load_conversation_state(session_id)
                logger.info("✅ Conversation state loaded")
            except Exception as e:
                logger.error(f"❌ Conversation state loading failed: {e}")
                existing_conversation = None
            
            # === STEP 7: OpenAI streaming ===
            logger.info("📝 Step 7: OpenAI streaming setup")
            from openai import AsyncOpenAI
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("❌ No OpenAI API key")
                yield f"data: {json.dumps({'error': 'No OpenAI API key configured'})}\n\n"
                return
            
            logger.info("Creating OpenAI client")
            openai_client = AsyncOpenAI(api_key=api_key)
            
            # === STEP 8: Prepare messages ===
            logger.info("📝 Step 8: Preparing messages")
            messages = [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": latest_message}
            ]
            logger.info("✅ Messages prepared")
            
            # === STEP 9: CRITICAL - Make OpenAI streaming call ===
            logger.info("📝 Step 9: Making OpenAI streaming call - THIS MIGHT HANG")
            try:
                response_stream = await openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_completion_tokens=100,
                    temperature=0.7,
                    stream=True
                )
                logger.info("✅ OpenAI stream created successfully")
                
                # === STEP 10: Stream chunks ===
                logger.info("📝 Step 10: Streaming chunks")
                chunk_count = 0
                async for chunk in response_stream:
                    chunk_count += 1
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if delta and delta.content:
                            chunk_data = {
                                "choices": [{"delta": {"content": delta.content}, "index": 0}],
                                "model": "gpt-4o"
                            }
                            yield f"data: {json.dumps(chunk_data)}\n\n"
                    
                    if chunk_count > 20:  # Limit for testing
                        break
                
                logger.info(f"✅ Streamed {chunk_count} chunks successfully")
                
            except Exception as stream_error:
                logger.error(f"❌ OpenAI streaming failed: {stream_error}")
                yield f"data: {json.dumps({'error': str(stream_error)})}\n\n"
                return
            
            # === STEP 11: Post-processing ===
            logger.info("📝 Step 11: Post-processing - THIS MIGHT HANG")
            try:
                # This section has complex async operations that might hang
                logger.info("Starting state management...")
                
                # Simulate the CIA agent call that might hang
                logger.info("Would call CIA agent here...")
                
                # Simulate the unified conversation save that might hang
                logger.info("Would save to unified conversation here...")
                
                logger.info("✅ Post-processing completed")
                
            except Exception as post_error:
                logger.error(f"❌ Post-processing failed: {post_error}")
            
            logger.info("🎉 Stream generation completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Stream generation failed: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        finally:
            logger.info("📝 Finally block: Sending [DONE] marker")
            yield "data: [DONE]\n\n"
            logger.info("✅ [DONE] marker sent")
    
    # Test the generator
    logger.info("🔥 Testing minimal stream replica...")
    
    chunk_count = 0
    async for chunk in generate_universal_sse_stream():
        chunk_count += 1
        logger.info(f"Received chunk {chunk_count}: {chunk[:50]}...")
        
        if chunk_count > 50:  # Safety limit
            logger.warning("Too many chunks, stopping test")
            break
    
    logger.info(f"🎯 Test completed - received {chunk_count} chunks total")

if __name__ == "__main__":
    asyncio.run(minimal_cia_stream_replica())