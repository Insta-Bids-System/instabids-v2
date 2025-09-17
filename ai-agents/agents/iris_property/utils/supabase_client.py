"""
Supabase Client for IRIS Property Agent
Provides database connection using the unified database system
"""

from database_simple import db

def get_supabase_client():
    """
    Get Supabase client using the unified database system
    Returns the same database connection used by other agents
    """
    return db.client