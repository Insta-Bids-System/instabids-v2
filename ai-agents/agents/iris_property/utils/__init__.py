"""
IRIS Utils Package
Utility functions and database connections
"""

from .supabase_client import get_supabase_client

__all__ = [
    'get_supabase_client'
]