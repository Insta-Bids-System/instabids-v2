"""
Database Watcher Service
Monitors database changes and broadcasts real-time updates to admin dashboard
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime

from supabase import Client

# from production_database_solution import get_production_db
import database_simple


get_production_db = database_simple.get_client

from .websocket_manager import MessageType, admin_websocket_manager


logger = logging.getLogger(__name__)


class DatabaseWatcher:
    """Monitors database changes and broadcasts to admin dashboard"""

    def __init__(self):
        self.db = get_production_db()
        self.client: Client = self.db
        self.subscriptions = {}
        self.change_handlers: dict[str, Callable] = {}
        self.monitoring_enabled = True

        # Statistics
        self.changes_processed = 0
        self.errors_count = 0
        self.last_change_time = None

    def register_change_handler(self, table_name: str, handler: Callable):
        """Register custom handler for table changes"""
        self.change_handlers[table_name] = handler
        logger.info(f"Registered change handler for table: {table_name}")

    async def setup_realtime_subscriptions(self):
        """Set up Supabase real-time subscriptions for key tables"""
        try:
            # Bid cards changes
            await self._subscribe_to_table(
                "bid_cards",
                self._handle_bid_card_change
            )

            # Campaign changes
            await self._subscribe_to_table(
                "outreach_campaigns",
                self._handle_campaign_change
            )

            # Contractor leads changes
            await self._subscribe_to_table(
                "contractor_leads",
                self._handle_contractor_change
            )

            # Outreach attempts changes
            await self._subscribe_to_table(
                "contractor_outreach_attempts",
                self._handle_outreach_attempt_change
            )

            logger.info("Database real-time subscriptions established")

        except Exception as e:
            logger.error(f"Failed to setup real-time subscriptions: {e}")
            self.errors_count += 1

    async def _subscribe_to_table(self, table_name: str, handler: Callable):
        """Subscribe to real-time changes for a specific table"""
        try:
            # Create subscription
            subscription = self.client.table(table_name).on("*", handler).subscribe()
            self.subscriptions[table_name] = subscription

            logger.info(f"Subscribed to real-time changes for table: {table_name}")

        except Exception as e:
            logger.error(f"Failed to subscribe to table {table_name}: {e}")
            self.errors_count += 1

    async def _handle_bid_card_change(self, payload):
        """Handle bid card table changes"""
        try:
            event_type = payload.get("eventType")
            record = payload.get("new") or payload.get("old")

            if not record:
                return

            self.changes_processed += 1
            self.last_change_time = datetime.now()

            # Extract key information
            bid_card_id = record.get("id")
            status = record.get("status")
            project_type = record.get("project_type")

            # Get bid progress information
            bid_document = record.get("bid_document", {})
            bids_received = len(bid_document.get("submitted_bids", []))
            contractor_count_needed = record.get("contractor_count_needed", 5)

            progress = {
                "current": bids_received,
                "target": contractor_count_needed,
                "percentage": int((bids_received / contractor_count_needed) * 100) if contractor_count_needed > 0 else 0
            }

            # Broadcast bid card update
            await admin_websocket_manager.broadcast_bid_card_update(
                bid_card_id=bid_card_id,
                status=status,
                progress=progress,
                additional_data={
                    "event_type": event_type,
                    "project_type": project_type,
                    "bid_card_number": record.get("bid_card_number"),
                    "created_at": record.get("created_at"),
                    "updated_at": record.get("updated_at")
                }
            )

            # Broadcast database operation
            await admin_websocket_manager.broadcast_database_operation(
                operation=event_type,
                table="bid_cards",
                record_id=bid_card_id,
                additional_data={
                    "project_type": project_type,
                    "status": status
                }
            )

            logger.info(f"Processed bid card change: {event_type} - {bid_card_id}")

        except Exception as e:
            logger.error(f"Error handling bid card change: {e}")
            self.errors_count += 1

    async def _handle_campaign_change(self, payload):
        """Handle campaign table changes"""
        try:
            event_type = payload.get("eventType")
            record = payload.get("new") or payload.get("old")

            if not record:
                return

            self.changes_processed += 1
            self.last_change_time = datetime.now()

            campaign_id = record.get("id")
            campaign_name = record.get("name")
            status = record.get("status")
            bid_card_id = record.get("bid_card_id")

            # Broadcast campaign update
            await admin_websocket_manager.broadcast_message(
                MessageType.CAMPAIGN_UPDATE,
                {
                    "campaign_id": campaign_id,
                    "name": campaign_name,
                    "status": status,
                    "bid_card_id": bid_card_id,
                    "event_type": event_type,
                    "contractors_targeted": record.get("contractors_targeted"),
                    "created_at": record.get("created_at"),
                    "updated_at": record.get("updated_at")
                }
            )

            # Broadcast database operation
            await admin_websocket_manager.broadcast_database_operation(
                operation=event_type,
                table="outreach_campaigns",
                record_id=campaign_id,
                additional_data={
                    "campaign_name": campaign_name,
                    "status": status,
                    "bid_card_id": bid_card_id
                }
            )

            logger.info(f"Processed campaign change: {event_type} - {campaign_id}")

        except Exception as e:
            logger.error(f"Error handling campaign change: {e}")
            self.errors_count += 1

    async def _handle_contractor_change(self, payload):
        """Handle contractor leads table changes"""
        try:
            event_type = payload.get("eventType")
            record = payload.get("new") or payload.get("old")

            if not record:
                return

            self.changes_processed += 1
            self.last_change_time = datetime.now()

            contractor_id = record.get("id")
            business_name = record.get("business_name")
            tier = record.get("tier")

            # Broadcast database operation
            await admin_websocket_manager.broadcast_database_operation(
                operation=event_type,
                table="contractor_leads",
                record_id=contractor_id,
                additional_data={
                    "business_name": business_name,
                    "tier": tier,
                    "specialties": record.get("specialties"),
                    "location": f"{record.get('location_city')}, {record.get('location_state')}"
                }
            )

            logger.info(f"Processed contractor change: {event_type} - {contractor_id}")

        except Exception as e:
            logger.error(f"Error handling contractor change: {e}")
            self.errors_count += 1

    async def _handle_outreach_attempt_change(self, payload):
        """Handle outreach attempts table changes"""
        try:
            event_type = payload.get("eventType")
            record = payload.get("new") or payload.get("old")

            if not record:
                return

            self.changes_processed += 1
            self.last_change_time = datetime.now()

            attempt_id = record.get("id")
            method = record.get("outreach_method")
            status = record.get("status")
            campaign_id = record.get("campaign_id")

            # Broadcast email event if it's email outreach
            if method == "email":
                await admin_websocket_manager.broadcast_message(
                    MessageType.EMAIL_EVENT,
                    {
                        "event_type": event_type,
                        "attempt_id": attempt_id,
                        "status": status,
                        "method": method,
                        "campaign_id": campaign_id,
                        "contractor_email": record.get("contact_email"),
                        "sent_at": record.get("sent_at"),
                        "delivered_at": record.get("delivered_at"),
                        "opened_at": record.get("opened_at")
                    }
                )

            # Broadcast form submission if it's form outreach
            elif method == "website_form":
                await admin_websocket_manager.broadcast_message(
                    MessageType.FORM_SUBMISSION,
                    {
                        "event_type": event_type,
                        "attempt_id": attempt_id,
                        "status": status,
                        "method": method,
                        "campaign_id": campaign_id,
                        "website_url": record.get("website_url"),
                        "submitted_at": record.get("sent_at"),
                        "response_received": record.get("response_received")
                    }
                )

            # Always broadcast database operation
            await admin_websocket_manager.broadcast_database_operation(
                operation=event_type,
                table="contractor_outreach_attempts",
                record_id=attempt_id,
                additional_data={
                    "method": method,
                    "status": status,
                    "campaign_id": campaign_id
                }
            )

            logger.info(f"Processed outreach attempt change: {event_type} - {attempt_id}")

        except Exception as e:
            logger.error(f"Error handling outreach attempt change: {e}")
            self.errors_count += 1

    async def get_database_stats(self) -> dict:
        """Get database monitoring statistics"""
        try:
            # Get table row counts using tables that actually exist
            bid_cards_result = self.db.table("bid_cards").select("id").execute()
            bid_cards_count = len(bid_cards_result.data) if bid_cards_result.data else 0

            # Use potential_contractors instead of contractor_leads (which doesn't exist)
            contractors_result = self.db.table("potential_contractors").select("id").execute()
            contractors_count = len(contractors_result.data) if contractors_result.data else 0

            # Use followup_logs for tracking outreach attempts
            followup_result = self.db.table("followup_logs").select("id").execute()
            attempts_count = len(followup_result.data) if followup_result.data else 0

            # Count unique campaigns from bid_cards (since outreach_campaigns doesn't exist)
            campaigns_count = bid_cards_count  # Each bid card is essentially a campaign

            return {
                "monitoring_enabled": self.monitoring_enabled,
                "changes_processed": self.changes_processed,
                "errors_count": self.errors_count,
                "last_change_time": self.last_change_time.isoformat() if self.last_change_time else None,
                "subscriptions_active": len(self.subscriptions),
                "table_counts": {
                    "bid_cards": bid_cards_count,
                    "outreach_campaigns": campaigns_count,
                    "contractor_leads": contractors_count,
                    "contractor_outreach_attempts": attempts_count
                }
            }

        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {
                "error": str(e),
                "monitoring_enabled": self.monitoring_enabled,
                "changes_processed": self.changes_processed,
                "errors_count": self.errors_count + 1,
                "last_change_time": self.last_change_time.isoformat() if self.last_change_time else None,
                "subscriptions_active": 0,
                "table_counts": {
                    "bid_cards": 0,
                    "outreach_campaigns": 0,
                    "contractor_leads": 0,
                    "contractor_outreach_attempts": 0
                }
            }

    async def enable_monitoring(self):
        """Enable database monitoring"""
        self.monitoring_enabled = True
        await self.setup_realtime_subscriptions()
        logger.info("Database monitoring enabled")

    async def disable_monitoring(self):
        """Disable database monitoring"""
        self.monitoring_enabled = False

        # Unsubscribe from all tables
        for table_name, subscription in self.subscriptions.items():
            try:
                await subscription.unsubscribe()
                logger.info(f"Unsubscribed from {table_name}")
            except Exception as e:
                logger.error(f"Error unsubscribing from {table_name}: {e}")

        self.subscriptions.clear()
        logger.info("Database monitoring disabled")

    async def create_admin_triggers(self):
        """Create database triggers for admin dashboard notifications"""

        # SQL to create admin notification function
        admin_function_sql = """
        CREATE OR REPLACE FUNCTION notify_admin_dashboard()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Use broadcast for admin dashboard updates
            PERFORM realtime.broadcast_changes(
                'admin_dashboard',      -- topic
                TG_OP,                  -- event type
                TG_OP,                  -- operation
                TG_TABLE_NAME,          -- table name
                TG_TABLE_SCHEMA,        -- schema
                NEW,                    -- new record
                OLD                     -- old record
            );
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        """

        # Trigger creation SQL for key tables
        trigger_sqls = [
            """
            DROP TRIGGER IF EXISTS admin_bid_cards_changes ON bid_cards;
            CREATE TRIGGER admin_bid_cards_changes
                AFTER INSERT OR UPDATE OR DELETE ON bid_cards
                FOR EACH ROW EXECUTE FUNCTION notify_admin_dashboard();
            """,
            """
            DROP TRIGGER IF EXISTS admin_campaigns_changes ON outreach_campaigns;
            CREATE TRIGGER admin_campaigns_changes
                AFTER INSERT OR UPDATE OR DELETE ON outreach_campaigns
                FOR EACH ROW EXECUTE FUNCTION notify_admin_dashboard();
            """,
            """
            DROP TRIGGER IF EXISTS admin_contractors_changes ON contractor_leads;
            CREATE TRIGGER admin_contractors_changes
                AFTER INSERT OR UPDATE OR DELETE ON contractor_leads
                FOR EACH ROW EXECUTE FUNCTION notify_admin_dashboard();
            """,
            """
            DROP TRIGGER IF EXISTS admin_attempts_changes ON contractor_outreach_attempts;
            CREATE TRIGGER admin_attempts_changes
                AFTER INSERT OR UPDATE OR DELETE ON contractor_outreach_attempts
                FOR EACH ROW EXECUTE FUNCTION notify_admin_dashboard();
            """
        ]

        try:
            # Note: In production, these would be executed via database admin tools
            # For now, we'll log them and they should be run manually

            logger.info("Admin dashboard triggers SQL generated:")
            logger.info("Execute the following SQL in your Supabase dashboard:")
            logger.info(admin_function_sql)

            for i, sql in enumerate(trigger_sqls, 1):
                logger.info(f"Trigger {i}:")
                logger.info(sql)

            return {
                "status": "triggers_ready",
                "message": "SQL generated for manual execution",
                "function_sql": admin_function_sql,
                "trigger_sqls": trigger_sqls
            }

        except Exception as e:
            logger.error(f"Error creating admin triggers: {e}")
            return {
                "status": "error",
                "message": str(e)
            }


# Global database watcher instance
database_watcher = DatabaseWatcher()


async def start_database_monitoring():
    """Start database monitoring service"""
    try:
        await database_watcher.enable_monitoring()
        logger.info("Database monitoring service started")

        # Periodically broadcast database stats
        while database_watcher.monitoring_enabled:
            try:
                stats = await database_watcher.get_database_stats()

                await admin_websocket_manager.broadcast_message(
                    MessageType.PERFORMANCE_METRIC,
                    {
                        "metric_type": "database_stats",
                        "data": stats
                    }
                )

            except Exception as e:
                logger.error(f"Error broadcasting database stats: {e}")

            # Wait before next broadcast
            await asyncio.sleep(30)  # Every 30 seconds

    except Exception as e:
        logger.error(f"Database monitoring service failed: {e}")


# Usage example
async def example_database_monitoring():
    """Example of how to use database monitoring"""

    # Start monitoring
    await database_watcher.enable_monitoring()

    # Get current stats
    stats = await database_watcher.get_database_stats()
    print(f"Database stats: {stats}")

    # Create triggers (returns SQL to execute manually)
    trigger_info = await database_watcher.create_admin_triggers()
    print(f"Trigger setup: {trigger_info}")
