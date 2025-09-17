"""
Supabase Realtime Integration for Admin Dashboard
Monitors database changes and broadcasts to WebSocket clients
"""

import asyncio
import logging
import os
from typing import Any, Optional

from supabase import create_client
from supabase._async.client import AsyncClient
from supabase._async.client import create_client as create_async_client


logger = logging.getLogger(__name__)


class SupabaseRealtimeMonitor:
    """Monitors Supabase realtime events and broadcasts to admin dashboard"""

    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager
        self.supabase: Optional[AsyncClient] = None
        self.supabase_sync = None
        self.channels = {}
        self.running = False

    def initialize(self):
        """Initialize Supabase client with credentials"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            logger.error("Supabase credentials not found in environment")
            return False

        try:
            # Create async client for realtime
            self.supabase = create_async_client(supabase_url, supabase_key)
            # Create sync client for queries
            self.supabase_sync = create_client(supabase_url, supabase_key)
            logger.info("Supabase realtime monitor initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            return False

    async def start_monitoring(self):
        """Start monitoring realtime changes"""
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return

        self.running = True

        # Subscribe to bid_cards table changes
        await self.subscribe_to_bid_cards()

        # Subscribe to contractor_outreach_attempts changes
        await self.subscribe_to_outreach()

        # Subscribe to bids table changes (bid submissions)
        await self.subscribe_to_bids()

        # Subscribe to campaign changes
        await self.subscribe_to_campaigns()

        logger.info("Started Supabase realtime monitoring")

    async def stop_monitoring(self):
        """Stop monitoring and clean up channels"""
        self.running = False

        # Unsubscribe from all channels
        for channel_name, channel in self.channels.items():
            try:
                await channel.unsubscribe()
                logger.info(f"Unsubscribed from channel: {channel_name}")
            except Exception as e:
                logger.error(f"Error unsubscribing from {channel_name}: {e}")

        self.channels.clear()
        logger.info("Stopped Supabase realtime monitoring")

    async def subscribe_to_bid_cards(self):
        """Subscribe to bid_cards table changes"""
        try:
            channel = self.supabase.channel("bid_cards_changes")

            # Subscribe to all changes on bid_cards table
            channel.on(
                event="*",
                schema="public",
                table="bid_cards",
                callback=lambda payload: asyncio.create_task(self.handle_bid_card_change(payload))
            )

            await channel.subscribe()
            self.channels["bid_cards"] = channel
            logger.info("Subscribed to bid_cards table changes")

        except Exception as e:
            logger.error(f"Failed to subscribe to bid_cards: {e}")

    async def subscribe_to_outreach(self):
        """Subscribe to contractor_outreach_attempts table changes"""
        try:
            channel = self.supabase.channel("outreach_changes")

            channel.on(
                event="*",
                schema="public",
                table="contractor_outreach_attempts",
                callback=lambda payload: asyncio.create_task(self.handle_outreach_change(payload))
            )

            await channel.subscribe()
            self.channels["outreach"] = channel
            logger.info("Subscribed to contractor_outreach_attempts table changes")

        except Exception as e:
            logger.error(f"Failed to subscribe to outreach: {e}")

    async def subscribe_to_bids(self):
        """Subscribe to bids table changes"""
        try:
            channel = self.supabase.channel("bids_changes")

            channel.on(
                event="*",
                schema="public",
                table="bids",
                callback=lambda payload: asyncio.create_task(self.handle_bid_submission(payload))
            )

            await channel.subscribe()
            self.channels["bids"] = channel
            logger.info("Subscribed to bids table changes")

        except Exception as e:
            logger.error(f"Failed to subscribe to bids: {e}")

    async def subscribe_to_campaigns(self):
        """Subscribe to outreach_campaigns table changes"""
        try:
            channel = self.supabase.channel("campaign_changes")

            channel.on(
                event="*",
                schema="public",
                table="outreach_campaigns",
                callback=lambda payload: asyncio.create_task(self.handle_campaign_change(payload))
            )

            await channel.subscribe()
            self.channels["campaigns"] = channel
            logger.info("Subscribed to outreach_campaigns table changes")

        except Exception as e:
            logger.error(f"Failed to subscribe to campaigns: {e}")

    async def handle_bid_card_change(self, payload: dict[str, Any]):
        """Handle bid card table changes"""
        try:
            event_type = payload.get("type")
            record = payload.get("record") or payload.get("new_record")
            old_record = payload.get("old_record")

            if not record:
                return

            # Extract relevant bid card data
            bid_card_data = {
                "id": record.get("id"),
                "bid_card_number": record.get("bid_card_number"),
                "status": record.get("status"),
                "project_type": record.get("project_type"),
                "urgency_level": record.get("urgency_level"),
                "contractor_count_needed": record.get("contractor_count_needed"),
                "bids_received_count": record.get("bids_received_count", 0),
                "bids_target_met": record.get("bids_target_met", False),
                "created_at": record.get("created_at"),
                "updated_at": record.get("updated_at")
            }

            # Check if bid document has submitted bids
            bid_document = record.get("bid_document", {})
            if bid_document and isinstance(bid_document, dict):
                submitted_bids = bid_document.get("submitted_bids", [])
                bid_card_data["submitted_bids_count"] = len(submitted_bids)

            # Broadcast the update
            await self.websocket_manager.broadcast_bid_card_update(
                bid_card_id=bid_card_data["id"],
                status=bid_card_data["status"],
                progress={
                    "current": bid_card_data["bids_received_count"],
                    "target": bid_card_data["contractor_count_needed"],
                    "percentage": (bid_card_data["bids_received_count"] / bid_card_data["contractor_count_needed"] * 100)
                                if bid_card_data["contractor_count_needed"] > 0 else 0
                },
                additional_data={
                    "event_type": event_type,
                    "bid_card_data": bid_card_data,
                    "old_status": old_record.get("status") if old_record else None
                }
            )

            logger.info(f"Broadcast bid card update: {bid_card_data['bid_card_number']} - {event_type}")

        except Exception as e:
            logger.error(f"Error handling bid card change: {e}")

    async def handle_outreach_change(self, payload: dict[str, Any]):
        """Handle contractor outreach attempts changes"""
        try:
            event_type = payload.get("type")
            record = payload.get("record") or payload.get("new_record")

            if not record:
                return

            # Broadcast database operation
            await self.websocket_manager.broadcast_database_operation(
                operation=event_type,
                table="contractor_outreach_attempts",
                record_id=record.get("id"),
                additional_data={
                    "bid_card_id": record.get("bid_card_id"),
                    "contractor_lead_id": record.get("contractor_lead_id"),
                    "channel": record.get("channel"),
                    "status": record.get("status"),
                    "sent_at": record.get("sent_at")
                }
            )

        except Exception as e:
            logger.error(f"Error handling outreach change: {e}")

    async def handle_bid_submission(self, payload: dict[str, Any]):
        """Handle bid submissions"""
        try:
            event_type = payload.get("type")
            record = payload.get("record") or payload.get("new_record")

            if not record or event_type != "INSERT":
                return

            # Get the bid card to broadcast update
            bid_card_id = record.get("bid_card_id")
            if bid_card_id:
                # Fetch updated bid card data
                result = self.supabase.table("bid_cards").select("*").eq("id", bid_card_id).single().execute()
                if result.data:
                    bid_card = result.data

                    # Broadcast bid submission alert
                    await self.websocket_manager.broadcast_system_alert(
                        alert_type="bid_submission",
                        message=f"New bid submitted for {bid_card.get('project_type')}",
                        severity="info",
                        additional_data={
                            "bid_card_id": bid_card_id,
                            "contractor_id": record.get("contractor_id"),
                            "bid_amount": record.get("bid_amount"),
                            "timeline_days": record.get("timeline_days")
                        }
                    )

                    # Also broadcast bid card update
                    await self.handle_bid_card_change({
                        "type": "UPDATE",
                        "record": bid_card
                    })

        except Exception as e:
            logger.error(f"Error handling bid submission: {e}")

    async def handle_campaign_change(self, payload: dict[str, Any]):
        """Handle campaign changes"""
        try:
            event_type = payload.get("type")
            record = payload.get("record") or payload.get("new_record")

            if not record:
                return

            # Broadcast campaign update
            from admin.websocket_manager import MessageType
            await self.websocket_manager.broadcast_message(
                MessageType.CAMPAIGN_UPDATE,
                {
                    "event_type": event_type,
                    "campaign_id": record.get("id"),
                    "bid_card_id": record.get("bid_card_id"),
                    "status": record.get("status"),
                    "contractors_targeted": record.get("contractors_targeted"),
                    "responses_received": record.get("responses_received"),
                    "bids_received": record.get("bids_received")
                }
            )

        except Exception as e:
            logger.error(f"Error handling campaign change: {e}")

    async def fetch_and_broadcast_bid_card(self, bid_card_id: str):
        """Fetch fresh bid card data and broadcast update"""
        try:
            result = self.supabase.table("bid_cards").select("*").eq("id", bid_card_id).single().execute()
            if result.data:
                await self.handle_bid_card_change({
                    "type": "MANUAL_UPDATE",
                    "record": result.data
                })
        except Exception as e:
            logger.error(f"Error fetching bid card {bid_card_id}: {e}")


# Global realtime monitor instance
realtime_monitor: Optional[SupabaseRealtimeMonitor] = None


def initialize_realtime_monitor(websocket_manager):
    """Initialize the global realtime monitor"""
    global realtime_monitor
    realtime_monitor = SupabaseRealtimeMonitor(websocket_manager)
    if realtime_monitor.initialize():
        return realtime_monitor
    return None


async def start_realtime_monitoring(websocket_manager):
    """Start realtime monitoring with the provided WebSocket manager"""
    monitor = initialize_realtime_monitor(websocket_manager)
    if monitor:
        await monitor.start_monitoring()
        return monitor
    return None
