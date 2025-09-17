"""
Async wrappers for AI API calls to prevent blocking the event loop.
"""

import asyncio
import functools
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional
import openai
from anthropic import Anthropic
import httpx

logger = logging.getLogger(__name__)

# Thread pool for running sync AI calls
_executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="ai_worker")

# Circuit breaker settings
MAX_FAILURES = 3
RESET_TIMEOUT = 60  # seconds


class AICircuitBreaker:
    """Circuit breaker for AI API calls."""
    
    def __init__(self):
        self.failures = 0
        self.last_failure_time = None
        self.is_open = False
        
    def record_success(self):
        self.failures = 0
        self.is_open = False
        
    def record_failure(self):
        self.failures += 1
        if self.failures >= MAX_FAILURES:
            self.is_open = True
            logger.warning(f"Circuit breaker opened after {MAX_FAILURES} failures")
            
    def can_attempt(self) -> bool:
        if not self.is_open:
            return True
            
        # Check if we should try to reset
        if self.last_failure_time:
            import time
            if time.time() - self.last_failure_time > RESET_TIMEOUT:
                logger.info("Circuit breaker attempting reset")
                self.is_open = False
                self.failures = 0
                return True
                
        return False


# Circuit breakers for different services
openai_breaker = AICircuitBreaker()
anthropic_breaker = AICircuitBreaker()


async def async_openai_completion(
    model: str,
    messages: List[Dict[str, str]],
    **kwargs
) -> Dict[str, Any]:
    """
    Async wrapper for OpenAI completion calls.
    Runs the sync call in a thread pool to avoid blocking.
    """
    if not openai_breaker.can_attempt():
        raise Exception("OpenAI circuit breaker is open - service unavailable")
    
    try:
        # Run sync OpenAI call in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            _executor,
            functools.partial(
                openai.ChatCompletion.create,
                model=model,
                messages=messages,
                **kwargs
            )
        )
        
        openai_breaker.record_success()
        return result
        
    except Exception as e:
        openai_breaker.record_failure()
        logger.error(f"OpenAI API error: {str(e)}")
        raise


async def async_anthropic_completion(
    model: str,
    messages: List[Dict[str, str]],
    max_tokens: int = 4096,
    **kwargs
) -> str:
    """
    Async wrapper for Anthropic completion calls.
    Runs the sync call in a thread pool to avoid blocking.
    """
    if not anthropic_breaker.can_attempt():
        raise Exception("Anthropic circuit breaker is open - service unavailable")
    
    try:
        # Run sync Anthropic call in thread pool
        loop = asyncio.get_event_loop()
        client = Anthropic()
        
        result = await loop.run_in_executor(
            _executor,
            functools.partial(
                client.messages.create,
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                **kwargs
            )
        )
        
        anthropic_breaker.record_success()
        return result.content[0].text if result.content else ""
        
    except Exception as e:
        anthropic_breaker.record_failure()
        logger.error(f"Anthropic API error: {str(e)}")
        raise


async def async_leonardo_generation(
    prompt: str,
    api_key: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Async wrapper for Leonardo AI image generation.
    Uses httpx async client from lifespan.
    """
    from utils.lifespan import get_http_client
    
    client = get_http_client()
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": prompt,
        **kwargs
    }
    
    try:
        response = await client.post(
            "https://cloud.leonardo.ai/api/rest/v1/generations",
            headers=headers,
            json=payload,
            timeout=30.0
        )
        
        response.raise_for_status()
        return response.json()
        
    except httpx.TimeoutException:
        logger.error("Leonardo API timeout")
        raise Exception("Leonardo API timeout - request took too long")
    except Exception as e:
        logger.error(f"Leonardo API error: {str(e)}")
        raise


# Helper function to run any sync function async
async def run_sync_async(func, *args, **kwargs):
    """
    Run any synchronous function asynchronously in the thread pool.
    Useful for database operations or other blocking I/O.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor,
        functools.partial(func, *args, **kwargs)
    )