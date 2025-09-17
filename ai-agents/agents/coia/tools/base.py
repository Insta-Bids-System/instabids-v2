"""
Base tool class for COIA tools
Provides common initialization and configuration
"""

import logging
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class BaseTool:
    """Base class for all COIA tools with common configuration"""
    
    def __init__(self):
        """Initialize base tool with environment variables"""
        self._initialized = False
        
        # Load from .env file if not already in environment
        env_path = Path(__file__).parent.parent.parent.parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
    
    async def __aenter__(self):
        """Async context manager entry"""
        if not self._initialized:
            logger.info(f"Activating {self.__class__.__name__} context")
            self._initialized = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        logger.info(f"Deactivating {self.__class__.__name__} context")
        return False