"""
Production-ready configuration management
Handles multiple environments with proper precedence
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration with validation"""
    url: str
    anon_key: str
    service_role_key: str

    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.url or not self.url.startswith("https://"):
            raise ValueError(f"Invalid SUPABASE_URL: {self.url}")

        if not self.anon_key or not self.anon_key.startswith("eyJ"):
            raise ValueError("Invalid SUPABASE_ANON_KEY")

        if not self.service_role_key or not self.service_role_key.startswith("eyJ"):
            raise ValueError("Invalid SUPABASE_SERVICE_ROLE_KEY")

        # Extract project ID from URL for validation
        try:
            project_id = self.url.split("//")[1].split(".")[0]
            logger.info(f"Database config validated for project: {project_id}")
        except:
            raise ValueError(f"Cannot extract project ID from URL: {self.url}")

@dataclass
class AIConfig:
    """AI service configuration"""
    anthropic_api_key: str
    openai_api_key: Optional[str] = None

    def __post_init__(self):
        if not self.anthropic_api_key or not self.anthropic_api_key.startswith("sk-ant-"):
            raise ValueError("Invalid ANTHROPIC_API_KEY")

@dataclass
class AppConfig:
    """Complete application configuration"""
    database: DatabaseConfig
    ai: AIConfig
    environment: str
    port: int = 8008
    debug: bool = False

    @classmethod
    def load(cls, env_file: Optional[str] = None) -> "AppConfig":
        """Load configuration with proper precedence"""

        # 1. Load from .env file (if specified)
        if env_file and os.path.exists(env_file):
            load_dotenv(env_file, override=True)
            logger.info(f"Loaded config from: {env_file}")
        else:
            # Try standard locations
            for env_path in [".env", "../.env", "../../.env"]:
                if os.path.exists(env_path):
                    load_dotenv(env_path, override=True)
                    logger.info(f"Loaded config from: {env_path}")
                    break

        # 2. Override with explicit values for known conflicts
        # This handles the Windows environment variable issue
        environment = os.getenv("ENVIRONMENT", "development")

        # For InstaBids production project (hardcoded to prevent conflicts)
        if environment in ["production", "development"]:
            supabase_url = "https://xrhgrthdcaymxuqcgrmj.supabase.co"
        else:
            supabase_url = os.getenv("SUPABASE_URL")

        # 3. Build configuration
        try:
            database_config = DatabaseConfig(
                url=supabase_url,
                anon_key=os.getenv("SUPABASE_ANON_KEY"),
                service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            )

            ai_config = AIConfig(
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )

            return cls(
                database=database_config,
                ai=ai_config,
                environment=environment,
                port=int(os.getenv("PORT", 8008)),
                debug=os.getenv("DEBUG", "false").lower() == "true"
            )

        except Exception as e:
            logger.error(f"Configuration error: {e}")
            raise ValueError(f"Invalid configuration: {e}")

# Global configuration instance
_config: Optional[AppConfig] = None

def get_config() -> AppConfig:
    """Get application configuration (singleton pattern)"""
    global _config
    if _config is None:
        _config = AppConfig.load()
    return _config

def reload_config(env_file: Optional[str] = None):
    """Reload configuration (useful for testing)"""
    global _config
    _config = AppConfig.load(env_file)
    return _config
