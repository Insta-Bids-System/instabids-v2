"""
Admin Monitoring Service
Coordinates all admin dashboard components and provides unified system monitoring
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException

# from production_database_solution import get_production_db
import database_simple


get_production_db = database_simple.get_client

from .auth_service import admin_auth_service
from .database_watcher import database_watcher
from .websocket_manager import MessageType, admin_websocket_manager


logger = logging.getLogger(__name__)


@dataclass
class AgentStatus:
    """Agent health status information"""
    name: str
    status: str  # online, offline, error, unknown
    last_seen: datetime
    response_time: float
    error_count: int
    success_count: int
    health_score: float  # 0-100


@dataclass
class SystemMetrics:
    """System performance metrics"""
    bid_cards_active: int
    campaigns_running: int
    contractors_total: int
    emails_sent_today: int
    forms_filled_today: int
    database_operations_today: int
    average_response_time: float
    error_rate: float
    uptime_seconds: int


class AdminMonitoringService:
    """Unified admin monitoring service that coordinates all admin components"""

    def __init__(self):
        self.db = get_production_db()
        self.start_time = datetime.now()
        self.monitoring_enabled = False

        # Agent monitoring
        self.agent_statuses: dict[str, AgentStatus] = {}
        
        # Use centralized configuration for agent endpoints
        try:
            from config.service_urls import ServiceEndpoints
            base = ServiceEndpoints.API_BASE
        except ImportError:
            import os
            base = os.getenv("BACKEND_URL", get_backend_url()) + "/api"
        
        self.agent_endpoints = {
            "CIA": f"{base}/agents/cia/health",
            "JAA": f"{base}/agents/jaa/health",
            "CDA": f"{base}/agents/cda/health",
            "EAA": f"{base}/agents/eaa/health",
            "WFA": f"{base}/agents/wfa/health"
        }

        # Metrics tracking
        self.metrics_history: list[SystemMetrics] = []
        self.max_history_size = 1000

        # Performance tracking
        self.operation_counts = {
            "database_operations": 0,
            "emails_sent": 0,
            "forms_filled": 0,
            "api_calls": 0,
            "errors": 0
        }

        # Alert thresholds
        self.alert_thresholds = {
            "error_rate": 0.05,  # 5% error rate
            "response_time": 5.0,  # 5 seconds
            "agent_offline_minutes": 5,
            "bid_card_stall_minutes": 30
        }

    async def initialize(self):
        """Initialize the monitoring service"""
        try:
            # Initialize all components
            await admin_auth_service.initialize_admin_table()
            await database_watcher.enable_monitoring()

            # Set up agent status tracking
            await self._initialize_agent_monitoring()

            # Start background monitoring tasks
            self.monitoring_enabled = True

            logger.info("Admin monitoring service initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize monitoring service: {e}")
            return False

    async def _initialize_agent_monitoring(self):
        """Initialize agent status tracking"""
        for agent_name in self.agent_endpoints.keys():
            self.agent_statuses[agent_name] = AgentStatus(
                name=agent_name,
                status="unknown",
                last_seen=datetime.now(),
                response_time=0.0,
                error_count=0,
                success_count=0,
                health_score=0.0
            )

    async def check_agent_health(self, agent_name: str) -> AgentStatus:
        """Check health of a specific agent"""
        try:
            if agent_name not in self.agent_endpoints:
                raise ValueError(f"Unknown agent: {agent_name}")

            # For now, simulate agent health checks
            # In production, this would make HTTP requests to agent health endpoints

            start_time = time.time()

            # Make actual HTTP request to agent health endpoint
            import aiohttp
            async with aiohttp.ClientSession() as session:
                try:
                    # Use the actual health endpoint we just created
                    url = f"{base}/agents/{agent_name}/health"
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            data = await response.json()

                            response_time = time.time() - start_time

                            # Create status from real data
                            status = AgentStatus(
                                name=agent_name,
                                status=data.get("status", "unknown"),
                                last_seen=datetime.fromisoformat(data.get("last_operation", datetime.now().isoformat())),
                                response_time=data.get("avg_response_time", response_time),
                                error_count=data.get("errors_today", 0),
                                success_count=data.get("operations_today", 0),
                                health_score=float(data.get("health_score", 0))
                            )
                        else:
                            # Non-200 response
                            response_time = time.time() - start_time
                            status = AgentStatus(
                                name=agent_name,
                                status="error",
                                last_seen=datetime.now(),
                                response_time=response_time,
                                error_count=self.agent_statuses[agent_name].error_count + 1,
                                success_count=self.agent_statuses[agent_name].success_count,
                                health_score=0.0
                            )
                except TimeoutError:
                    # Timeout
                    status = AgentStatus(
                        name=agent_name,
                        status="offline",
                        last_seen=self.agent_statuses[agent_name].last_seen,
                        response_time=5.0,  # timeout value
                        error_count=self.agent_statuses[agent_name].error_count + 1,
                        success_count=self.agent_statuses[agent_name].success_count,
                        health_score=0.0
                    )
                except Exception as e:
                    # Other errors
                    logger.error(f"Error checking {agent_name} health: {e}")
                    status = AgentStatus(
                        name=agent_name,
                        status="error",
                        last_seen=datetime.now(),
                        response_time=time.time() - start_time,
                        error_count=self.agent_statuses[agent_name].error_count + 1,
                        success_count=self.agent_statuses[agent_name].success_count,
                        health_score=0.0
                    )

            # Update stored status
            self.agent_statuses[agent_name] = status

            # Broadcast agent status update
            await admin_websocket_manager.broadcast_agent_status(
                agent_name=agent_name,
                status=status.status,
                response_time=status.response_time,
                additional_data={
                    "health_score": status.health_score,
                    "error_count": status.error_count,
                    "success_count": status.success_count
                }
            )

            # Alert if agent is down
            if status.status == "error":
                await admin_websocket_manager.broadcast_system_alert(
                    alert_type="agent_failure",
                    message=f"Agent {agent_name} is not responding",
                    severity="error",
                    additional_data={"agent": agent_name, "response_time": response_time}
                )

            return status

        except Exception as e:
            logger.error(f"Error checking agent {agent_name} health: {e}")

            # Update status to error
            error_status = AgentStatus(
                name=agent_name,
                status="error",
                last_seen=self.agent_statuses[agent_name].last_seen,
                response_time=10.0,
                error_count=self.agent_statuses[agent_name].error_count + 1,
                success_count=self.agent_statuses[agent_name].success_count,
                health_score=0.0
            )

            self.agent_statuses[agent_name] = error_status
            return error_status

    async def check_all_agents_health(self) -> dict[str, AgentStatus]:
        """Check health of all agents"""
        results = {}

        # Check all agents concurrently
        tasks = [
            self.check_agent_health(agent_name)
            for agent_name in self.agent_endpoints.keys()
        ]

        agent_results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, agent_name in enumerate(self.agent_endpoints.keys()):
            result = agent_results[i]
            if isinstance(result, Exception):
                logger.error(f"Failed to check {agent_name}: {result}")
                results[agent_name] = self.agent_statuses[agent_name]
            else:
                results[agent_name] = result

        return results

    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # Get database counts using ACTUAL tables that exist
            bid_cards_result = self.db.table("bid_cards").select("id,status,created_at").execute()

            # Query followup_logs for email tracking (EAA outreach)
            followup_logs_result = self.db.table("followup_logs").select("id,created_at").execute()

            # Query potential_contractors for contractor counts
            contractors_result = self.db.table("potential_contractors").select("id,created_at").execute()

            # Count active bid cards
            bid_cards_active = len([
                bc for bc in (bid_cards_result.data or [])
                if bc.get("status") in ["generated", "collecting_bids"]
            ])

            # Since campaigns table doesn't exist, count unique bid cards being processed
            campaigns_running = bid_cards_active  # Each active bid card is essentially a campaign

            # Total contractors discovered
            contractors_total = len(contractors_result.data or [])

            # Count today's activities
            today_str = datetime.now().date().isoformat()

            # Get real email stats from the email tracking endpoint
            try:
                async with aiohttp.ClientSession() as session:
                    # Use same base URL from agent endpoints
                    try:
                        from config.service_urls import ServiceEndpoints
                        base = ServiceEndpoints.API_BASE
                    except ImportError:
                        import os
                        base = os.getenv("BACKEND_URL", get_backend_url()) + "/api"
                    
                    url = f"{base}/email-tracking/stats"
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            email_stats = await response.json()
                            emails_sent_today = email_stats.get("emails_sent_today", 0)
                        else:
                            # Fallback to counting from followup_logs
                            emails_sent_today = len([
                                log for log in (followup_logs_result.data or [])
                                if log.get("created_at", "").startswith(today_str)
                            ])
            except:
                # Fallback to counting from followup_logs
                emails_sent_today = len([
                    log for log in (followup_logs_result.data or [])
                    if log.get("created_at", "").startswith(today_str)
                ])

            # Get real form stats from the form tracking endpoint
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{base}/form-tracking/stats"
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            form_stats = await response.json()
                            forms_filled_today = form_stats.get("forms_submitted_today", 0)
                        else:
                            forms_filled_today = 0
            except:
                forms_filled_today = 0

            # Calculate performance metrics
            uptime_seconds = int((datetime.now() - self.start_time).total_seconds())

            # Get agent response times
            agent_response_times = [
                status.response_time for status in self.agent_statuses.values()
                if status.response_time > 0
            ]
            average_response_time = sum(agent_response_times) / len(agent_response_times) if agent_response_times else 0.0

            # Calculate error rate
            total_operations = sum(self.operation_counts.values())
            error_rate = self.operation_counts["errors"] / max(total_operations, 1)

            # Count database operations today (for now, use operation counts)
            database_operations_today = self.operation_counts.get("database_operations", 0)

            metrics = SystemMetrics(
                bid_cards_active=bid_cards_active,
                campaigns_running=campaigns_running,
                contractors_total=contractors_total,
                emails_sent_today=emails_sent_today,
                forms_filled_today=forms_filled_today,
                database_operations_today=database_operations_today,
                average_response_time=average_response_time,
                error_rate=error_rate,
                uptime_seconds=uptime_seconds
            )

            # Store in history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history.pop(0)

            return metrics

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                bid_cards_active=0,
                campaigns_running=0,
                contractors_total=0,
                emails_sent_today=0,
                forms_filled_today=0,
                database_operations_today=0,
                average_response_time=0.0,
                error_rate=1.0,
                uptime_seconds=0
            )

    async def check_for_alerts(self, metrics: SystemMetrics):
        """Check if any alert conditions are met"""
        alerts = []

        # High error rate alert
        if metrics.error_rate > self.alert_thresholds["error_rate"]:
            alerts.append({
                "type": "high_error_rate",
                "message": f"Error rate is {metrics.error_rate:.1%} (threshold: {self.alert_thresholds['error_rate']:.1%})",
                "severity": "warning"
            })

        # Slow response time alert
        if metrics.average_response_time > self.alert_thresholds["response_time"]:
            alerts.append({
                "type": "slow_response",
                "message": f"Average response time is {metrics.average_response_time:.1f}s (threshold: {self.alert_thresholds['response_time']}s)",
                "severity": "warning"
            })

        # Agent offline alerts
        for agent_name, status in self.agent_statuses.items():
            if status.status in ["error", "offline"]:
                minutes_since_seen = (datetime.now() - status.last_seen).total_seconds() / 60
                if minutes_since_seen > self.alert_thresholds["agent_offline_minutes"]:
                    alerts.append({
                        "type": "agent_offline",
                        "message": f"Agent {agent_name} has been offline for {minutes_since_seen:.0f} minutes",
                        "severity": "error"
                    })

        # Send alerts
        for alert in alerts:
            await admin_websocket_manager.broadcast_system_alert(
                alert_type=alert["type"],
                message=alert["message"],
                severity=alert["severity"]
            )

    async def get_recent_bid_cards(self, limit: int = 20) -> list:
        """Get recent bid cards from database"""
        try:
            # Query real bid cards from Supabase
            response = self.db.table("bid_cards").select(
                "id, bid_card_number, project_type, status, contractor_count_needed, "
                "budget_min, budget_max, location_city, location_state, "
                "created_at, updated_at, bid_count, interested_contractors"
            ).order("created_at", desc=True).limit(limit).execute()

            bid_cards = []
            for card in response.data or []:
                bid_cards.append({
                    "id": card["id"],
                    "bid_card_number": card.get("bid_card_number", "Unknown"),
                    "project_type": card.get("project_type", "Unknown Project"),
                    "status": card.get("status", "unknown"),
                    "progress": card.get("bid_count", 0),
                    "target_bids": card.get("contractor_count_needed", 0),
                    "budget_min": card.get("budget_min", 0),
                    "budget_max": card.get("budget_max", 0),
                    "location": f"{card.get('location_city', '')}, {card.get('location_state', '')}".strip(", "),
                    "created_at": card.get("created_at", "")
                })

            print(f"[MONITORING] Retrieved {len(bid_cards)} recent bid cards from database")
            return bid_cards

        except Exception as e:
            print(f"[MONITORING] Error getting recent bid cards: {e}")
            return []

    async def get_dashboard_overview(self) -> dict:
        """Get complete dashboard overview data"""
        try:
            # Get current metrics
            metrics = await self.collect_system_metrics()

            # Get agent statuses
            agent_statuses = {name: {
                "status": status.status,
                "health_score": status.health_score,
                "response_time": status.response_time,
                "last_seen": status.last_seen.isoformat()
            } for name, status in self.agent_statuses.items()}

            # Get database stats
            db_stats = await database_watcher.get_database_stats()

            # Get WebSocket stats
            ws_stats = admin_websocket_manager.get_connection_stats()

            # Get auth stats
            auth_stats = await admin_auth_service.get_admin_stats()

            return {
                "timestamp": datetime.now().isoformat(),
                "system_metrics": {
                    "bid_cards_active": metrics.bid_cards_active,
                    "campaigns_running": metrics.campaigns_running,
                    "contractors_total": metrics.contractors_total,
                    "emails_sent_today": metrics.emails_sent_today,
                    "forms_filled_today": metrics.forms_filled_today,
                    "database_operations_today": metrics.database_operations_today,
                    "average_response_time": metrics.average_response_time,
                    "error_rate": metrics.error_rate,
                    "uptime_seconds": metrics.uptime_seconds
                },
                "agent_statuses": agent_statuses,
                "database_stats": db_stats,
                "websocket_stats": ws_stats,
                "auth_stats": auth_stats,
                "monitoring_enabled": self.monitoring_enabled
            }

        except Exception as e:
            logger.error(f"Error getting dashboard overview: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "monitoring_enabled": self.monitoring_enabled
            }

    async def restart_agent(self, agent_name: str, admin_session_id: str) -> bool:
        """Restart a specific agent (admin action)"""
        try:
            # Verify admin permissions
            admin_user = await admin_auth_service.validate_session(admin_session_id)
            if not admin_user:
                raise HTTPException(status_code=401, detail="Invalid admin session")

            if not await admin_auth_service.check_permission(admin_session_id, "manage_system"):
                raise HTTPException(status_code=403, detail="Insufficient permissions")

            # In production, this would make API call to restart the agent
            logger.info(f"Admin {admin_user.email} restarting agent {agent_name}")

            # Simulate restart
            await asyncio.sleep(1.0)

            # Update agent status
            if agent_name in self.agent_statuses:
                self.agent_statuses[agent_name].status = "online"
                self.agent_statuses[agent_name].last_seen = datetime.now()
                self.agent_statuses[agent_name].health_score = 100.0

            # Broadcast restart notification
            await admin_websocket_manager.broadcast_system_alert(
                alert_type="agent_restart",
                message=f"Agent {agent_name} restarted by admin {admin_user.email}",
                severity="info"
            )

            # Log admin activity
            await admin_auth_service._log_admin_activity(
                admin_user.id,
                "restart_agent",
                {"agent_name": agent_name}
            )

            return True

        except Exception as e:
            logger.error(f"Error restarting agent {agent_name}: {e}")
            return False

    async def pause_campaign(self, campaign_id: str, admin_session_id: str) -> bool:
        """Pause a specific campaign (admin action)"""
        try:
            # Verify admin permissions
            admin_user = await admin_auth_service.validate_session(admin_session_id)
            if not admin_user:
                raise HTTPException(status_code=401, detail="Invalid admin session")

            if not await admin_auth_service.check_permission(admin_session_id, "control_campaigns"):
                raise HTTPException(status_code=403, detail="Insufficient permissions")

            # Update campaign status in database
            result = self.db.table("outreach_campaigns").update({
                "status": "paused",
                "updated_at": datetime.now().isoformat()
            }).eq("id", campaign_id).execute()

            if result.data:
                # Broadcast campaign update
                await admin_websocket_manager.broadcast_message(
                    MessageType.CAMPAIGN_UPDATE,
                    {
                        "campaign_id": campaign_id,
                        "status": "paused",
                        "admin_action": True,
                        "admin_user": admin_user.email
                    }
                )

                # Log admin activity
                await admin_auth_service._log_admin_activity(
                    admin_user.id,
                    "pause_campaign",
                    {"campaign_id": campaign_id}
                )

                logger.info(f"Campaign {campaign_id} paused by admin {admin_user.email}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error pausing campaign {campaign_id}: {e}")
            return False


# Global monitoring service instance
admin_monitoring_service = AdminMonitoringService()


async def start_admin_monitoring():
    """Start the complete admin monitoring system"""
    try:
        # Initialize monitoring service
        success = await admin_monitoring_service.initialize()
        if not success:
            logger.error("Failed to initialize admin monitoring service")
            return

        logger.info("Admin monitoring system started successfully")

        # Main monitoring loop
        while admin_monitoring_service.monitoring_enabled:
            try:
                # Check agent health
                await admin_monitoring_service.check_all_agents_health()

                # Collect system metrics
                metrics = await admin_monitoring_service.collect_system_metrics()

                # Check for alerts
                await admin_monitoring_service.check_for_alerts(metrics)

                # Broadcast system overview
                overview = await admin_monitoring_service.get_dashboard_overview()
                await admin_websocket_manager.broadcast_message(
                    MessageType.PERFORMANCE_METRIC,
                    {
                        "metric_type": "system_overview",
                        "data": overview
                    }
                )

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                admin_monitoring_service.operation_counts["errors"] += 1

            # Wait before next cycle
            await asyncio.sleep(15)  # Monitor every 15 seconds

    except Exception as e:
        logger.error(f"Admin monitoring system failed: {e}")


# Usage example
async def example_monitoring_usage():
    """Example of how to use the monitoring service"""

    # Initialize the service
    await admin_monitoring_service.initialize()

    # Get dashboard overview
    overview = await admin_monitoring_service.get_dashboard_overview()
    print(f"Dashboard overview: {json.dumps(overview, default=str, indent=2)}")

    # Check specific agent health
    cia_status = await admin_monitoring_service.check_agent_health("CIA")
    print(f"CIA Agent Status: {cia_status}")

    # Simulate admin action (restart agent)
    # Note: This would require a valid admin session in practice
    # success = await admin_monitoring_service.restart_agent("CIA", "admin-session-id")
    # print(f"Agent restart successful: {success}")
