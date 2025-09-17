"""
Simple database wrapper to fix import issues.
This module provides a compatibility layer for routers expecting database_simple.
"""

# Import the actual database module
from database import SupabaseDB


# Create a singleton instance
db = SupabaseDB()

# Add get_client function for compatibility
def get_client():
    """Get the Supabase client instance."""
    return db.client

# Export for compatibility
__all__ = ["SupabaseDB", "db", "get_client"]
