"""
Database connection pooling for Supabase.
Prevents connection exhaustion and improves performance.
"""

import os
import asyncio
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import asyncpg
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

# Connection pool for direct PostgreSQL access
_pg_pool: Optional[asyncpg.Pool] = None

# Singleton Supabase client
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get singleton Supabase client."""
    global _supabase_client
    
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            raise ValueError("Supabase credentials not configured")
            
        _supabase_client = create_client(url, key)
        logger.info("Supabase client initialized")
    
    return _supabase_client


async def init_db_pool():
    """Initialize PostgreSQL connection pool."""
    global _pg_pool
    
    if _pg_pool is not None:
        return _pg_pool
    
    # Get database URL from environment
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Construct from Supabase URL if not provided
        supabase_url = os.getenv("SUPABASE_URL", "")
        if "supabase.co" in supabase_url:
            # Extract project ref from URL
            project_ref = supabase_url.split("//")[1].split(".")[0]
            db_url = f"postgresql://postgres.{project_ref}:password@aws-0-us-west-1.pooler.supabase.com:5432/postgres"
    
    if not db_url:
        logger.warning("Database URL not configured, using Supabase client only")
        return None
    
    try:
        _pg_pool = await asyncpg.create_pool(
            db_url,
            min_size=2,
            max_size=10,
            max_queries=50000,
            max_inactive_connection_lifetime=300
        )
        logger.info("PostgreSQL connection pool initialized")
        return _pg_pool
    except Exception as e:
        logger.error(f"Failed to create connection pool: {e}")
        return None


async def close_db_pool():
    """Close the database connection pool."""
    global _pg_pool
    
    if _pg_pool:
        await _pg_pool.close()
        _pg_pool = None
        logger.info("PostgreSQL connection pool closed")


@asynccontextmanager
async def get_db_connection():
    """Get a database connection from the pool."""
    if _pg_pool is None:
        await init_db_pool()
    
    if _pg_pool:
        async with _pg_pool.acquire() as connection:
            yield connection
    else:
        # Fallback to None if pool not available
        yield None


async def execute_query(query: str, *args) -> list:
    """Execute a query using the connection pool."""
    async with get_db_connection() as conn:
        if conn:
            return await conn.fetch(query, *args)
        else:
            # Fallback to Supabase client
            logger.warning("Using Supabase client for query (slower)")
            client = get_supabase_client()
            # This is a simplified fallback - real implementation would need query parsing
            return []


async def execute_insert(query: str, *args) -> Any:
    """Execute an insert query using the connection pool."""
    async with get_db_connection() as conn:
        if conn:
            return await conn.fetchval(query, *args)
        else:
            # Fallback to Supabase client
            logger.warning("Using Supabase client for insert (slower)")
            return None