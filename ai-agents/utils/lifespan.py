"""
Lifespan management for FastAPI app with shared resources.
Handles async HTTP client and other application-wide resources.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any
import httpx
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

# Global async HTTP client
_http_client: httpx.AsyncClient = None

def get_http_client() -> httpx.AsyncClient:
    """Get the global async HTTP client."""
    if _http_client is None:
        raise RuntimeError("HTTP client not initialized. Is the app running?")
    return _http_client


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware to track request timing and log slow requests."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Add timing info to request state
        request.state.start_time = start_time
        
        try:
            response = await call_next(request)
            
            # Calculate request time
            process_time = time.time() - start_time
            
            # Log slow requests
            if process_time > 1.0:  # Log requests taking more than 1 second
                logger.warning(
                    f"Slow request: {request.method} {request.url.path} "
                    f"took {process_time:.2f}s"
                )
            
            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"after {process_time:.2f}s - {str(e)}"
            )
            raise


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Lifespan context manager for FastAPI app.
    Sets up and tears down shared resources.
    """
    global _http_client
    
    logger.info("Starting up FastAPI application...")
    
    # Create async HTTP client with connection pooling
    _http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=5.0),
        limits=httpx.Limits(
            max_keepalive_connections=20,
            max_connections=50,
            keepalive_expiry=30.0
        ),
        follow_redirects=True
    )
    
    # Store in app state for easy access
    app.state.http_client = _http_client
    
    logger.info("Async HTTP client initialized with connection pooling")
    
    # Initialize database connection pool
    try:
        from utils.database_pool import init_db_pool
        await init_db_pool()
        logger.info("Database connection pool initialized")
    except Exception as e:
        logger.warning(f"Database pool initialization failed: {e}")
    
    yield {
        "http_client": _http_client
    }
    
    # Cleanup on shutdown
    logger.info("Shutting down FastAPI application...")
    
    if _http_client:
        await _http_client.aclose()
        logger.info("Async HTTP client closed")
    
    # Close database pool
    try:
        from utils.database_pool import close_db_pool
        await close_db_pool()
    except Exception as e:
        logger.warning(f"Database pool cleanup failed: {e}")
    
    logger.info("Shutdown complete")


# Helper function to make async HTTP requests
async def async_request(
    method: str,
    url: str,
    **kwargs
) -> httpx.Response:
    """
    Make an async HTTP request using the global client.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: URL to request
        **kwargs: Additional arguments for httpx request
        
    Returns:
        httpx.Response object
    """
    client = get_http_client()
    return await client.request(method, url, **kwargs)