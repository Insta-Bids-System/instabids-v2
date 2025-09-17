"""
Realtime Poller for Admin Dashboard
Polls database for changes and broadcasts to WebSocket clients
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import database_simple


logger = logging.getLogger(__name__)


class RealtimePoller:
    """Polls database for changes and broadcasts to admin dashboard"""

    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager
        self.db = database_simple.get_client()
        self.running = False
        self.poll_interval = 2  # seconds
        self.last_check_times = {
            "bid_cards": datetime.now(),
            "outreach_campaigns": datetime.now(),
            "contractor_outreach_attempts": datetime.now(),
            "bids": datetime.now()
        }
        self.known_records: dict[str, set[str]] = {
            "bid_cards": set(),
            "outreach_campaigns": set(),
            "contractor_outreach_attempts": set(),
            "bids": set()
        }

    async def start_polling(self):
        """Start polling for database changes"""
        self.running = True
        logger.info("Started realtime polling for admin dashboard")

        # Initialize known records
        await self._initialize_known_records()

        # Start polling tasks
        tasks = [
            asyncio.create_task(self._poll_bid_cards()),
            asyncio.create_task(self._poll_campaigns()),
            asyncio.create_task(self._poll_outreach()),
            asyncio.create_task(self._poll_bids())
        ]

        # Wait for all tasks
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Polling error: {e}")

    async def stop_polling(self):
        """Stop polling"""
        self.running = False
        logger.info("Stopped realtime polling")

    async def _initialize_known_records(self):
        """Initialize known records to prevent false updates on startup"""
        try:
            # Get all existing bid cards
            result = self.db.table("bid_cards").select("id").execute()
            self.known_records["bid_cards"] = {r["id"] for r in result.data}

            # Get all campaigns
            result = self.db.table("outreach_campaigns").select("id").execute()
            self.known_records["outreach_campaigns"] = {r["id"] for r in result.data}

            # Get recent outreach attempts (last hour)
            one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
            result = self.db.table("contractor_outreach_attempts").select("id").gte("created_at", one_hour_ago).execute()
            self.known_records["contractor_outreach_attempts"] = {r["id"] for r in result.data}

            # Get recent bids (last hour)
            result = self.db.table("bids").select("id").gte("created_at", one_hour_ago).execute()
            self.known_records["bids"] = {r["id"] for r in result.data}

            logger.info(f"Initialized known records: {sum(len(v) for v in self.known_records.values())} total")

        except Exception as e:
            logger.error(f"Error initializing known records: {e}")

    async def _poll_bid_cards(self):
        """Poll bid_cards table for changes"""
        while self.running:
            try:
                # Get bid cards updated since last check
                last_check = self.last_check_times["bid_cards"]
                result = self.db.table("bid_cards").select("*").gte("updated_at", last_check.isoformat()).execute()

                for record in result.data:
                    record_id = record["id"]

                    # Check if this is a new record or update
                    is_new = record_id not in self.known_records["bid_cards"]
                    self.known_records["bid_cards"].add(record_id)

                    # Broadcast update
                    await self._broadcast_bid_card_update(record, "INSERT" if is_new else "UPDATE")

                # Update last check time
                self.last_check_times["bid_cards"] = datetime.now()

            except Exception as e:
                logger.error(f"Error polling bid_cards: {e}")

            await asyncio.sleep(self.poll_interval)

    async def _poll_campaigns(self):
        """Poll outreach_campaigns table for changes"""
        while self.running:
            try:
                last_check = self.last_check_times["outreach_campaigns"]
                result = self.db.table("outreach_campaigns").select("*").gte("updated_at", last_check.isoformat()).execute()

                for record in result.data:
                    record_id = record["id"]
                    is_new = record_id not in self.known_records["outreach_campaigns"]
                    self.known_records["outreach_campaigns"].add(record_id)

                    # Broadcast campaign update
                    from admin.websocket_manager import MessageType
                    await self.websocket_manager.broadcast_message(
                        MessageType.CAMPAIGN_UPDATE,
                        {
                            "event_type": "INSERT" if is_new else "UPDATE",
                            "campaign_id": record.get("id"),
                            "bid_card_id": record.get("bid_card_id"),
                            "status": record.get("status"),
                            "contractors_targeted": record.get("contractors_targeted"),
                            "responses_received": record.get("responses_received"),
                            "bids_received": record.get("bids_received")
                        }
                    )

                self.last_check_times["outreach_campaigns"] = datetime.now()

            except Exception as e:
                logger.error(f"Error polling campaigns: {e}")

            await asyncio.sleep(self.poll_interval)

    async def _poll_outreach(self):
        """Poll contractor_outreach_attempts for new records"""
        while self.running:
            try:
                # Only check for new records in last 5 minutes
                five_min_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
                result = self.db.table("contractor_outreach_attempts").select("*").gte("created_at", five_min_ago).execute()

                for record in result.data:
                    record_id = record["id"]
                    if record_id not in self.known_records["contractor_outreach_attempts"]:
                        self.known_records["contractor_outreach_attempts"].add(record_id)

                        # Broadcast outreach update
                        await self.websocket_manager.broadcast_database_operation(
                            operation="INSERT",
                            table="contractor_outreach_attempts",
                            record_id=record_id,
                            additional_data={
                                "bid_card_id": record.get("bid_card_id"),
                                "contractor_lead_id": record.get("contractor_lead_id"),
                                "channel": record.get("channel"),
                                "status": record.get("status"),
                                "sent_at": record.get("sent_at")
                            }
                        )

            except Exception as e:
                logger.error(f"Error polling outreach: {e}")

            await asyncio.sleep(self.poll_interval * 2)  # Poll less frequently

    async def _poll_bids(self):
        """Poll bids table for new submissions"""
        while self.running:
            try:
                # Check for new bids in last 5 minutes
                five_min_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
                result = self.db.table("bids").select("*").gte("created_at", five_min_ago).execute()

                for record in result.data:
                    record_id = record["id"]
                    if record_id not in self.known_records["bids"]:
                        self.known_records["bids"].add(record_id)

                        # Get the bid card for this bid
                        bid_card_id = record.get("bid_card_id")
                        if bid_card_id:
                            # Broadcast bid submission alert
                            await self.websocket_manager.broadcast_system_alert(
                                alert_type="bid_submission",
                                message="New bid submitted",
                                severity="info",
                                additional_data={
                                    "bid_card_id": bid_card_id,
                                    "contractor_id": record.get("contractor_id"),
                                    "bid_amount": record.get("bid_amount"),
                                    "timeline_days": record.get("timeline_days")
                                }
                            )

                            # Also update the bid card
                            await self._fetch_and_broadcast_bid_card(bid_card_id)

            except Exception as e:
                logger.error(f"Error polling bids: {e}")

            await asyncio.sleep(self.poll_interval)

    async def _broadcast_bid_card_update(self, record: dict[str, Any], event_type: str):
        """Broadcast bid card update to WebSocket clients"""
        try:
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
                    "bid_card_data": bid_card_data
                }
            )

            logger.info(f"Broadcast bid card update: {bid_card_data['bid_card_number']} - {event_type}")

        except Exception as e:
            logger.error(f"Error broadcasting bid card update: {e}")

    async def _fetch_and_broadcast_bid_card(self, bid_card_id: str):
        """Fetch fresh bid card data and broadcast update"""
        try:
            result = self.db.table("bid_cards").select("*").eq("id", bid_card_id).single().execute()
            if result.data:
                await self._broadcast_bid_card_update(result.data, "UPDATE")
        except Exception as e:
            logger.error(f"Error fetching bid card {bid_card_id}: {e}")


# Global poller instance
realtime_poller: Optional[RealtimePoller] = None


def initialize_realtime_poller(websocket_manager):
    """Initialize the global realtime poller"""
    global realtime_poller
    realtime_poller = RealtimePoller(websocket_manager)
    return realtime_poller


async def start_realtime_polling(websocket_manager):
    """Start realtime polling with the provided WebSocket manager"""
    poller = initialize_realtime_poller(websocket_manager)
    if poller:
        asyncio.create_task(poller.start_polling())
        return poller
    return None
