"""
Enhanced Supabase database connection with service role support
Allows backend operations to bypass RLS when needed
"""

import logging
import os
from datetime import datetime
from typing import Any, Optional

from dotenv import load_dotenv
from supabase import Client, create_client


# Load environment variables
load_dotenv(override=True)

logger = logging.getLogger(__name__)

class SupabaseService:
    """Database client with service role capabilities for backend operations"""

    def __init__(self, use_service_role: bool = False):
        """
        Initialize Supabase client

        Args:
            use_service_role: If True, uses service role key to bypass RLS
        """
        # Force correct URL to override Windows system environment
        supabase_url = "https://xrhgrthdcaymxuqcgrmj.supabase.co"

        # Choose which key to use based on context
        if use_service_role:
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            if not supabase_key:
                logger.warning("Service role key not found, falling back to anon key")
                supabase_key = os.getenv("SUPABASE_ANON_KEY")
        else:
            supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

        self.client: Client = create_client(supabase_url, supabase_key)
        self.use_service_role = use_service_role
        logger.info(f"Supabase client initialized (service_role={use_service_role})")

    async def create_campaign(self, campaign_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create an outreach campaign (requires service role to bypass RLS)
        """
        try:
            if not self.use_service_role:
                logger.warning("Creating campaign without service role - may fail due to RLS")

            result = self.client.table("outreach_campaigns").insert(
                campaign_data
            ).execute()

            if result.data:
                logger.info(f"Created campaign: {result.data[0]['id']}")
                return result.data[0]
            else:
                raise Exception("Failed to create campaign")

        except Exception as e:
            logger.error(f"Error creating campaign: {e!s}")
            raise

    async def create_contractor_outreach_attempt(self, attempt_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create contractor outreach attempt record
        """
        try:
            result = self.client.table("contractor_outreach_attempts").insert(
                attempt_data
            ).execute()

            if result.data:
                logger.info(f"Created outreach attempt: {result.data[0]['id']}")
                return result.data[0]
            else:
                raise Exception("Failed to create outreach attempt")

        except Exception as e:
            logger.error(f"Error creating outreach attempt: {e!s}")
            raise

    async def update_campaign_status(self, campaign_id: str, status: str, stats: Optional[dict] = None) -> dict[str, Any]:
        """
        Update campaign status and statistics
        """
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }

            if stats:
                update_data["campaign_stats"] = stats

            result = self.client.table("outreach_campaigns").update(
                update_data
            ).eq("id", campaign_id).execute()

            if result.data:
                logger.info(f"Updated campaign {campaign_id} status to {status}")
                return result.data[0]
            else:
                raise Exception("Failed to update campaign")

        except Exception as e:
            logger.error(f"Error updating campaign: {e!s}")
            raise

    async def create_check_in(self, check_in_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create campaign check-in record
        """
        try:
            result = self.client.table("campaign_check_ins").insert(
                check_in_data
            ).execute()

            if result.data:
                logger.info(f"Created check-in: {result.data[0]['id']}")
                return result.data[0]
            else:
                raise Exception("Failed to create check-in")

        except Exception as e:
            logger.error(f"Error creating check-in: {e!s}")
            raise

    async def get_bid_card(self, bid_card_id: str) -> Optional[dict[str, Any]]:
        """
        Get bid card by ID
        """
        try:
            result = self.client.table("bid_cards").select("*").eq(
                "id", bid_card_id
            ).execute()

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Error getting bid card: {e!s}")
            return None

    async def get_potential_contractors(self, filters: Optional[dict] = None) -> list:
        """
        Get potential contractors with optional filters
        """
        try:
            query = self.client.table("potential_contractors").select("*")

            if filters:
                if "tier" in filters:
                    query = query.eq("tier", filters["tier"])
                if "project_type" in filters:
                    query = query.contains("specialties", [filters["project_type"]])
                if "location" in filters:
                    query = query.eq("location", filters["location"])

            result = query.execute()
            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error getting contractors: {e!s}")
            return []

# Create singleton instances
db_anon = SupabaseService(use_service_role=False)  # For user-facing operations
db_service = SupabaseService(use_service_role=True)  # For backend operations
