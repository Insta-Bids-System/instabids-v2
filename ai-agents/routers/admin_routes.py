"""
Admin Routes - Admin Dashboard and Management API Endpoints
Owner: Agent 2 (Backend Core) - Currently building admin dashboard
"""

from datetime import datetime
from typing import Optional

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)

import database_simple as database
from admin.auth_service import admin_auth_service

# Import admin monitoring components
from admin.monitoring_service import AdminMonitoringService
from admin.websocket_manager import AdminWebSocketManager

# Import Redis cache
from utils.redis_cache import cache


# Create router
router = APIRouter()

# Initialize admin services
admin_websocket_manager = AdminWebSocketManager()
admin_monitoring_service = AdminMonitoringService()

# Admin WebSocket endpoint for real-time dashboard
@router.websocket("/ws/admin")
async def admin_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for admin dashboard real-time updates"""
    # Don't accept here - let the manager handle it

    client_id = f"admin_{datetime.now().timestamp()}"
    admin_user_id = None

    try:
        # Accept connection first
        await websocket.accept()
        print(f"[ADMIN WS] Connection accepted for {client_id}")

        # Don't send test message immediately - wait for auth first
        print("[ADMIN WS] Connection established, waiting for authentication...")

        # Wait for authentication message
        print("[ADMIN WS] Waiting for auth message...")
        auth_data = await websocket.receive_json()
        print(f"[ADMIN WS] Received data: {auth_data}")

        if auth_data.get("type") != "auth":
            await websocket.send_json({
                "type": "error",
                "message": "Authentication required"
            })
            await websocket.close()
            return

        # Verify admin session
        session_id = auth_data.get("session_id")
        if not session_id:
            await websocket.send_json({
                "type": "error",
                "message": "Session ID required"
            })
            await websocket.close()
            return

        # Validate session
        print(f"[ADMIN WS] Validating session: {session_id}")
        admin_user = await admin_auth_service.validate_session(session_id)
        if not admin_user:
            print("[ADMIN WS] Session validation failed")
            await websocket.send_json({
                "type": "error",
                "message": "Invalid or expired session"
            })
            await websocket.close()
            return

        print(f"[ADMIN WS] Session validated for user: {admin_user.email}")
        admin_user_id = admin_user.id

        # Register connection with correct parameter order
        connection_success = await admin_websocket_manager.connect(websocket, client_id, admin_user_id)

        # Send authentication success
        await websocket.send_json({
            "type": "auth_success",
            "client_id": client_id,
            "admin_user": {
                "id": admin_user.id,
                "email": admin_user.email,
                "full_name": admin_user.full_name,
                "role": admin_user.role,
                "permissions": admin_user.permissions
            }
        })

        # Send initial dashboard data
        try:
            dashboard_data = await admin_monitoring_service.get_dashboard_overview()
            await websocket.send_json({
                "type": "dashboard_overview",
                "data": dashboard_data,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"[ADMIN WS] Error getting dashboard data: {e}")
            # Send minimal dashboard data on error
            await websocket.send_json({
                "type": "dashboard_overview",
                "data": {
                    "error": "Failed to load dashboard data",
                    "metrics": {},
                    "agent_statuses": {},
                    "recent_activity": []
                },
                "timestamp": datetime.now().isoformat()
            })

        # Keep connection alive and handle messages
        while True:
            try:
                message = await websocket.receive_json()
                message_type = message.get("type")

                if message_type == "subscribe":
                    # Handle subscription to specific data types
                    subscriptions = message.get("subscriptions", [])
                    # Subscribe to each subscription type
                    for subscription in subscriptions:
                        await admin_websocket_manager.subscribe_client(client_id, subscription)

                elif message_type == "ping":
                    # Handle ping for connection health
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })

                elif message_type == "get_data":
                    # Handle specific data requests
                    data_type = message.get("data_type")

                    if data_type == "agent_status":
                        agent_statuses = await admin_monitoring_service.get_all_agent_statuses()
                        await websocket.send_json({
                            "type": "agent_status_data",
                            "data": agent_statuses,
                            "timestamp": datetime.now().isoformat()
                        })

                    elif data_type == "system_metrics":
                        metrics = await admin_monitoring_service.collect_system_metrics()
                        await websocket.send_json({
                            "type": "system_metrics_data",
                            "data": metrics,
                            "timestamp": datetime.now().isoformat()
                        })

                    elif data_type == "bid_cards":
                        # Get recent bid cards
                        try:
                            bid_cards = await admin_monitoring_service.get_recent_bid_cards(limit=20)
                        except Exception as e:
                            print(f"[ADMIN WS] Bid cards error: {e}")
                            bid_cards = []
                        await websocket.send_json({
                            "type": "bid_cards_data",
                            "data": {"bid_cards": bid_cards},
                            "timestamp": datetime.now().isoformat()
                        })

            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"[ADMIN WS] Error handling message: {e}")
                # Don't send error message on broken connection - just log
                break

    except WebSocketDisconnect:
        print(f"[ADMIN WS] WebSocket disconnected for {client_id}")
    except Exception as e:
        print(f"[ADMIN WS] Connection error: {e}")
        # Don't try to send on broken connection - just log and clean up
    finally:
        # Clean up connection
        if client_id:
            print(f"[ADMIN WS] Cleaning up connection for {client_id}")
            await admin_websocket_manager.disconnect(client_id)

# Admin API endpoints
@router.post("/login")
async def admin_login(request: Request, response: Response, login_data: dict):
    """Admin login endpoint"""
    try:
        email = login_data.get("email")
        password = login_data.get("password")
        remember_me = login_data.get("remember_me", False)

        if not email or not password:
            return {"success": False, "error": "Email and password required"}

        # Simple hardcoded auth for development
        if email == "admin@instabids.com" and password == "admin123":
            import uuid
            from datetime import datetime, timedelta

            session_id = f"admin-{uuid.uuid4()}"

            # Set session cookie
            response.set_cookie(
                key="admin_session_id",
                value=session_id,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite="lax",
                max_age=30 * 24 * 60 * 60 if remember_me else 8 * 60 * 60  # 30 days or 8 hours
            )

            # Return expected response format
            return {
                "success": True,
                "session": {
                    "session_id": session_id,
                    "admin_user_id": "admin-user",
                    "email": email,
                    "created_at": datetime.now().isoformat(),
                    "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
                    "last_activity": datetime.now().isoformat(),
                    "is_active": True
                },
                "admin_user": {
                    "id": "admin-user",
                    "email": email,
                    "full_name": "Admin User",
                    "role": "admin",
                    "permissions": ["all"],
                    "created_at": datetime.now().isoformat(),
                    "is_active": True
                }
            }
        else:
            return {"success": False, "error": "Invalid email or password"}

    except Exception as e:
        print(f"[ADMIN LOGIN ERROR] {e}")
        return {"success": False, "error": "Login failed"}

@router.post("/logout")
async def admin_logout(response: Response, logout_data: dict):
    """Admin logout endpoint"""
    try:
        session_id = logout_data.get("session_id")
        if not session_id:
            return {"success": False, "error": "Session ID required"}

        success = await admin_auth_service.invalidate_session(session_id)

        # Clear session cookie
        response.delete_cookie(key="admin_session_id")

        return {"success": success}

    except Exception as e:
        print(f"[ADMIN LOGOUT ERROR] {e}")
        return {"success": False, "error": "Logout failed"}

@router.get("/session/validate")
async def validate_admin_session(session_id: str):
    """Validate admin session"""
    try:
        print(f"[ADMIN SESSION VALIDATION] Validating session: {session_id}")
        admin_user = await admin_auth_service.validate_session(session_id)
        if admin_user:
            print(f"[ADMIN SESSION VALIDATION] Session valid for user: {admin_user.email}")
            return {
                "valid": True,
                "session": {
                    "session_id": session_id,
                    "admin_user_id": admin_user.id,
                    "email": admin_user.email
                },
                "admin_user": {
                    "id": admin_user.id,
                    "email": admin_user.email,
                    "full_name": admin_user.full_name,
                    "role": admin_user.role,
                    "permissions": admin_user.permissions
                }
            }
        else:
            print("[ADMIN SESSION VALIDATION] Session invalid or expired")
            return {"valid": False}

    except Exception as e:
        print(f"[ADMIN SESSION VALIDATION ERROR] {e}")
        import traceback
        traceback.print_exc()
        # Write error to file for debugging
        with open("validation_error.log", "a") as f:
            f.write(f"\n[{datetime.now()}] Session validation error for {session_id}: {e}\n")
            f.write(traceback.format_exc())
        return {"valid": False, "error": "Validation failed"}

@router.get("/session")
async def get_current_session(request: Request):
    """Get current admin session from cookies or header"""
    try:
        # Try to get session ID from X-Session-ID header first
        session_id = request.headers.get("X-Session-ID")

        # If not in header, try to get from cookie
        if not session_id:
            session_id = request.cookies.get("admin_session_id")

        # If not in cookie, try Authorization header
        if not session_id:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                session_id = auth_header.replace("Bearer ", "")

        if not session_id:
            return {"success": False, "error": "No session"}

        # Validate session
        admin_user = await admin_auth_service.validate_session(session_id)

        if admin_user:
            return {
                "success": True,
                "session": {
                    "session_id": session_id,
                    "admin_user_id": admin_user.id,
                    "email": admin_user.email,
                    "created_at": admin_user.created_at.isoformat(),
                    "expires_at": datetime.now().isoformat(),  # Could be improved to get actual expiry
                    "is_active": True
                },
                "admin_user": {
                    "id": admin_user.id,
                    "email": admin_user.email,
                    "full_name": admin_user.full_name,
                    "role": admin_user.role,
                    "permissions": admin_user.permissions,
                    "created_at": admin_user.created_at.isoformat(),
                    "last_login": admin_user.last_login.isoformat() if admin_user.last_login else None,
                    "is_active": admin_user.is_active
                }
            }
        else:
            return {"success": False, "error": "Invalid session"}

    except Exception as e:
        print(f"[ADMIN SESSION ERROR] {e}")
        return {"success": False, "error": "Session validation failed"}

@router.get("/bid-cards")
async def get_admin_bid_cards(request: Request):
    """Get bid cards for admin dashboard"""
    try:
        # Skip auth validation for development
        # Get session ID from Authorization header
        auth_header = request.headers.get("authorization", "")
        # For development, accept any Bearer token
        if auth_header and not auth_header.startswith("Bearer "):
            raise HTTPException(401, "Authorization header required")

        # Get recent bid cards from Supabase database
        try:
            # Define desc for ordering
            desc = True
            # Query real bid cards from Supabase  
            response = database.db.client.table("bid_cards").select(
                "id, bid_card_number, project_type, status, contractor_count_needed, "
                "budget_min, budget_max, location_city, location_state, urgency_level, "
                "created_at, updated_at, bid_count, interested_contractors, bid_deadline, "
                "service_complexity, trade_count, primary_trade, secondary_trades"
            ).order("created_at", desc=desc).execute()

            bid_cards = []
            for card in response.data:
                # Calculate progress percentage
                bid_count = card.get("bid_count", 0)
                contractor_count_needed = card.get("contractor_count_needed", 1)
                progress_percentage = (bid_count / contractor_count_needed * 100) if contractor_count_needed > 0 else 0

                # Set intelligent urgency if null based on project type and timeline
                urgency_level = card.get("urgency_level")
                if not urgency_level:
                    project_type = card.get("project_type", "").lower()

                    # Intelligent urgency assignment based on project type
                    if any(keyword in project_type for keyword in ["emergency", "leak", "flood", "urgent", "asap"]):
                        urgency_level = "emergency"
                    elif any(keyword in project_type for keyword in ["roof", "plumbing", "electrical", "hvac"]):
                        urgency_level = "urgent"  # Infrastructure projects are usually urgent
                    elif any(keyword in project_type for keyword in ["kitchen", "bathroom", "remodel"]):
                        urgency_level = "week"  # Major remodels need planning but have deadlines
                    elif any(keyword in project_type for keyword in ["landscape", "paint", "deck", "fence"]):
                        urgency_level = "month"  # Exterior/aesthetic projects more flexible
                    else:
                        urgency_level = "week"  # Default to week (not standard) for active projects

                bid_cards.append({
                    "id": card["id"],
                    "bid_card_number": card.get("bid_card_number", "Unknown"),
                    "project_type": card.get("project_type", "Unknown Project"),
                    "status": card.get("status", "unknown"),
                    "bids_received": bid_count,  # Fix: use correct field name
                    "contractor_count_needed": contractor_count_needed,
                    "progress_percentage": round(progress_percentage, 1),  # Fix: calculate percentage
                    "urgency_level": urgency_level,  # Fix: include urgency level
                    "budget_min": card.get("budget_min", 0),
                    "budget_max": card.get("budget_max", 0),
                    "location": f"{card.get('location_city', '')}, {card.get('location_state', '')}".strip(", "),
                    "created_at": card.get("created_at", ""),
                    "updated_at": card.get("updated_at", ""),
                    "last_activity": "Database sync"  # Frontend expects this
                })

            print(f"[ADMIN BID CARDS] Retrieved {len(bid_cards)} real bid cards from database")

        except Exception as e:
            print(f"[ADMIN BID CARDS] Database error: {e}")
            # Return empty array if database fails
            bid_cards = []

        return {
            "success": True,
            "bid_cards": bid_cards,
            "count": len(bid_cards)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ADMIN BID CARDS ERROR] {e}")
        raise HTTPException(500, "Failed to get bid cards")

@router.post("/restart-agent")
async def restart_agent(restart_data: dict):
    """Restart a specific agent"""
    try:
        session_id = restart_data.get("session_id")
        agent_name = restart_data.get("agent_name")

        if not session_id or not agent_name:
            raise HTTPException(400, "Session ID and agent name required")

        # Validate admin session and permissions
        admin_user = await admin_auth_service.validate_session(session_id)
        if not admin_user:
            raise HTTPException(401, "Invalid session")

        # Check if user has system management permission
        if "manage_system" not in admin_user.permissions:
            raise HTTPException(403, "Insufficient permissions")

        # Restart agent (placeholder - would implement actual restart logic)
        success = await admin_monitoring_service.restart_agent(agent_name)

        if success:
            # Broadcast agent restart to all admin connections
            restart_message = {
                "type": "agent_status",
                "data": {
                    "agent": agent_name,
                    "status": "online",
                    "health_score": 100,
                    "response_time": 0.1,
                    "last_seen": datetime.now().isoformat()
                },
                "timestamp": datetime.now().isoformat()
            }
            await admin_websocket_manager.broadcast_to_all(restart_message)

            return {"success": True, "message": f"Agent {agent_name} restarted successfully"}
        else:
            return {"success": False, "error": f"Failed to restart agent {agent_name}"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ADMIN RESTART AGENT ERROR] {e}")
        raise HTTPException(500, "Failed to restart agent")

@router.get("/dashboard")
async def get_admin_dashboard(request: Request):
    """Get admin dashboard data"""
    try:
        # Try to get session ID from X-Session-ID header first
        session_id = request.headers.get("X-Session-ID")

        # If not in header, try Authorization header
        if not session_id:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                session_id = auth_header.replace("Bearer ", "")

        # If not in Authorization header, try cookie
        if not session_id:
            session_id = request.cookies.get("admin_session_id")

        if not session_id:
            raise HTTPException(401, "No session provided")

        # Validate admin session
        admin_user = await admin_auth_service.validate_session(session_id)
        if not admin_user:
            raise HTTPException(401, "Invalid session")

        # Get real dashboard data from the monitoring service
        dashboard_data = await admin_monitoring_service.get_dashboard_overview()

        return dashboard_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ADMIN DASHBOARD ERROR] {e}")
        raise HTTPException(500, "Failed to get dashboard data")

@router.get("/bid-cards-fixed")
async def get_admin_bid_cards_fixed(request: Request):
    """Get bid cards for admin dashboard - FIXED VERSION with correct field names and calculations"""
    try:
        # Get session ID from Authorization header
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(401, "Authorization header required")

        session_id = auth_header.replace("Bearer ", "")
        admin_user = await admin_auth_service.validate_session(session_id)
        if not admin_user:
            raise HTTPException(401, "Invalid session")

        # Get recent bid cards from Supabase database
        try:
            # Define desc for ordering
            desc = True
            # Query real bid cards from Supabase with FIXED logic
            response = database.db.client.table("bid_cards").select(
                "id, bid_card_number, project_type, status, contractor_count_needed, "
                "budget_min, budget_max, location_city, location_state, urgency_level, "
                "created_at, updated_at, bid_count, interested_contractors, bid_deadline, "
                "service_complexity, trade_count, primary_trade, secondary_trades"
            ).order("created_at", desc=desc).execute()

            bid_cards = []
            for card in response.data:
                # Calculate progress percentage - FIXED CALCULATION
                bid_count = card.get("bid_count", 0)
                contractor_count_needed = card.get("contractor_count_needed", 1)
                progress_percentage = (bid_count / contractor_count_needed * 100) if contractor_count_needed > 0 else 0

                # Set intelligent urgency if null based on project type - FIXED URGENCY
                urgency_level = card.get("urgency_level")
                if not urgency_level:
                    project_type = card.get("project_type", "").lower()

                    # Intelligent urgency assignment based on project type
                    if any(keyword in project_type for keyword in ["emergency", "leak", "flood", "urgent", "asap"]):
                        urgency_level = "emergency"
                    elif any(keyword in project_type for keyword in ["roof", "plumbing", "electrical", "hvac"]):
                        urgency_level = "urgent"  # Infrastructure projects are usually urgent
                    elif any(keyword in project_type for keyword in ["kitchen", "bathroom", "remodel"]):
                        urgency_level = "week"  # Major remodels need planning but have deadlines
                    elif any(keyword in project_type for keyword in ["landscape", "paint", "deck", "fence"]):
                        urgency_level = "month"  # Exterior/aesthetic projects more flexible
                    else:
                        urgency_level = "week"  # Default to week (not standard) for active projects

                bid_cards.append({
                    "id": card["id"],
                    "bid_card_number": card.get("bid_card_number", "Unknown"),
                    "project_type": card.get("project_type", "Unknown Project"),
                    "status": card.get("status", "unknown"),
                    "bids_received": bid_count,  # FIXED: use correct field name
                    "contractor_count_needed": contractor_count_needed,  # FIXED: include this field
                    "progress_percentage": round(progress_percentage, 1),  # FIXED: calculate percentage
                    "urgency_level": urgency_level,  # FIXED: include urgency level
                    "budget_min": card.get("budget_min", 0),
                    "budget_max": card.get("budget_max", 0),
                    "location": f"{card.get('location_city', '')}, {card.get('location_state', '')}"
                        .strip(", "),
                    "created_at": card.get("created_at", ""),
                    "updated_at": card.get("updated_at", ""),
                    "last_activity": "Database sync"  # Frontend expects this
                })

            print(f"[ADMIN BID CARDS FIXED] Retrieved {len(bid_cards)} real bid cards from database")

        except Exception as e:
            print(f"[ADMIN BID CARDS FIXED] Database error: {e}")
            # Return empty array if database fails
            bid_cards = []

        return {
            "success": True,
            "bid_cards": bid_cards,
            "count": len(bid_cards),
            "message": "FIXED VERSION - Correct field names and calculations"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ADMIN BID CARDS FIXED ERROR] {e}")
        raise HTTPException(500, "Failed to get bid cards")


# ============================================================================
# CAMPAIGN MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/bid-cards/{bid_card_id}/lifecycle")
async def get_bid_card_lifecycle(bid_card_id: str):
    """Get complete lifecycle data for a bid card including campaigns"""
    try:
        from database_simple import get_client
        db = get_client()

        # Get bid card data
        bid_card_result = db.table("bid_cards").select("*").eq("id", bid_card_id).single().execute()
        if not bid_card_result.data:
            raise HTTPException(status_code=404, detail="Bid card not found")

        # Get campaigns for this bid card
        campaigns_result = db.table("outreach_campaigns").select("*").eq("bid_card_id", bid_card_id).execute()

        # Get discovery data
        discovery_result = db.table("contractor_discovery_cache").select("*").eq("bid_card_id", bid_card_id).execute()

        # Get outreach attempts with contractor details
        outreach_result = db.table("contractor_outreach_attempts").select(
            "*, contractor_leads!inner(company_name, contractor_size, specialties, rating, city, state, phone, email)"
        ).eq("bid_card_id", bid_card_id).execute()

        # Get contractor leads from discovery runs
        contractor_leads_result = db.table("contractor_leads").select("*").in_(
            "discovery_run_id",
            [dr["id"] for dr in discovery_result.data] if discovery_result.data else []
        ).execute()

        # Format contractor leads for the UI with tier classification
        formatted_contractor_leads = []
        for cl in contractor_leads_result.data:
            # Determine contractor tier
            tier = 3  # Default to tier 3 (cold lead)

            # Check if internal contractor (tier 1)
            internal_check = db.table("contractors").select("id").eq("id", cl["id"]).limit(1).execute()
            if internal_check.data:
                tier = 1
            else:
                # Check for previous outreach (tier 2)
                previous_outreach = db.table("contractor_outreach_attempts").select("id").eq(
                    "contractor_lead_id", cl["id"]
                ).limit(1).execute()
                if previous_outreach.data:
                    tier = 2

            formatted_contractor_leads.append({
                "id": cl["id"],
                "company_name": cl.get("company_name"),
                "contact_name": cl.get("contact_name"),
                "phone": cl.get("phone"),
                "email": cl.get("email"),
                "city": cl.get("city"),
                "state": cl.get("state"),
                "specialties": cl.get("specialties", []),
                "rating": cl.get("rating"),
                "tier": tier,
                "contractor_size": cl.get("contractor_size"),
                "years_in_business": cl.get("years_in_business")
            })

        # Format outreach attempts for the UI
        formatted_outreach_attempts = []
        for attempt in outreach_result.data:
            contractor_info = attempt.get("contractor_leads", {}) if attempt.get("contractor_leads") else {}
            formatted_outreach_attempts.append({
                "id": attempt["id"],
                "channel": attempt.get("channel"),
                "status": attempt.get("status"),
                "sent_at": attempt.get("sent_at"),
                "responded_at": attempt.get("responded_at"),
                "response_channel": attempt.get("response_channel"),
                "contractor": {
                    "company_name": contractor_info.get("company_name"),
                    "city": contractor_info.get("city"),
                    "state": contractor_info.get("state"),
                    "phone": contractor_info.get("phone"),
                    "email": contractor_info.get("email"),
                    "specialties": contractor_info.get("specialties", []),
                    "rating": contractor_info.get("rating")
                }
            })

        # Get bids (from bid_document JSONB)
        bids = []
        if bid_card_result.data.get("bid_document") and bid_card_result.data["bid_document"].get("submitted_bids"):
            bids = bid_card_result.data["bid_document"]["submitted_bids"]

        # Get timeline events (from bid_document JSONB)
        timeline = []
        if bid_card_result.data.get("bid_document") and bid_card_result.data["bid_document"].get("timeline"):
            # Sort timeline by timestamp (most recent first for display)
            timeline = sorted(
                bid_card_result.data["bid_document"]["timeline"],
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )

        return {
            "bid_card": bid_card_result.data,
            "campaigns": campaigns_result.data if campaigns_result.data else [],
            "discovery": {
                "discovery_cache": discovery_result.data[0] if discovery_result.data else None,
                "potential_contractors": [],
                "contractor_leads": formatted_contractor_leads
            },
            "outreach": {
                "outreach_attempts": formatted_outreach_attempts
            },
            "engagement": {
                "views": [],
                "events": []
            },
            "bids": bids,
            "timeline": timeline
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching bid card lifecycle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaigns")
async def get_campaigns(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get all campaigns with their current status"""
    try:
        # Try to get from cache first
        cache_params = {"status": status, "limit": limit, "offset": offset}
        cached_result = cache.get("campaigns", cache_params)
        if cached_result:
            print(f"[CAMPAIGNS] Cache hit, returning cached data")
            return cached_result
        from database_simple import get_client
        db = get_client()

        # Build query
        query = db.table("outreach_campaigns").select(
            "*, bid_cards!inner(bid_card_number, project_type, urgency_level)"
        )

        if status:
            query = query.eq("status", status)

        # Define desc for ordering
        desc = True
        # Get campaigns with bid card info
        result = query.order("created_at", desc=desc).range(offset, offset + limit - 1).execute()

        campaigns = []
        for campaign in result.data:
            # Get check-ins for this campaign
            check_ins_result = db.table("campaign_check_ins")\
                .select("*")\
                .eq("campaign_id", campaign["id"])\
                .order("check_in_percentage").execute()

            # Format campaign data
            formatted_campaign = {
                "campaign_id": campaign["id"],
                "bid_card_id": campaign["bid_card_id"],
                "bid_card_number": campaign["bid_cards"]["bid_card_number"],
                "project_type": campaign["bid_cards"]["project_type"],
                "urgency_level": campaign["bid_cards"].get("urgency_level"),
                "max_contractors": campaign.get("max_contractors", 0),
                "contractors_targeted": campaign.get("contractors_targeted", 0),
                "responses_received": campaign.get("responses_received", 0),
                "campaign_status": campaign.get("status", "active"),
                "created_at": campaign["created_at"],
                "check_ins": []
            }

            # Add check-in data
            for check_in in check_ins_result.data:
                formatted_campaign["check_ins"].append({
                    "id": check_in["id"],
                    "check_in_percentage": check_in.get("check_in_percentage", 0),
                    "scheduled_time": check_in.get("scheduled_time"),
                    "bids_expected": check_in.get("bids_expected", 0),
                    "bids_received": check_in.get("bids_received", 0),
                    "on_track": check_in.get("on_track", False),
                    "escalation_needed": check_in.get("escalation_needed", False),
                    "additional_contractors_needed": check_in.get("additional_contractors_needed", 0),
                    "status": check_in.get("status", "pending")
                })

            campaigns.append(formatted_campaign)

        # Count active campaigns
        active_count = len([c for c in campaigns if c["campaign_status"] == "active"])

        result = {
            "campaigns": campaigns,
            "total": len(campaigns),
            "active_count": active_count
        }
        
        # Cache the result for 60 seconds
        cache_params = {"status": status, "limit": limit, "offset": offset}
        cache.set("campaigns", result, cache_params, ttl_seconds=60)
        print(f"[CAMPAIGNS] Cached result for 60 seconds")
        
        return result

    except Exception as e:
        print(f"Error fetching campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaigns/{campaign_id}/details")
async def get_campaign_details(campaign_id: str):
    """Get detailed information about a specific campaign including all contractors"""
    try:
        # Try to get from cache first
        cache_params = {"campaign_id": campaign_id}
        cached_result = cache.get("campaign_details", cache_params)
        if cached_result:
            print(f"[CAMPAIGN DETAILS] Cache hit for campaign {campaign_id}")
            return cached_result
        from database_simple import get_client
        db = get_client()

        # Get campaign info
        campaign_result = db.table("outreach_campaigns")\
            .select("*, bid_cards!inner(bid_card_number, project_type, urgency_level)")\
            .eq("id", campaign_id).single().execute()

        if not campaign_result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")

        campaign = campaign_result.data

        # Get check-ins
        check_ins_result = db.table("campaign_check_ins")\
            .select("*")\
            .eq("campaign_id", campaign_id)\
            .order("check_in_percentage").execute()

        # Get contractors in campaign
        contractors_result = db.table("campaign_contractors")\
            .select("*, contractor_leads!inner(company_name, contractor_size, specialties, google_rating)")\
            .eq("campaign_id", campaign_id).execute()

        # Determine tier for each contractor
        contractors = []
        for cc in contractors_result.data:
            contractor_data = {
                "id": cc["id"],
                "contractor_id": cc["contractor_id"],
                "company_name": cc["contractor_leads"]["company_name"],
                "contractor_size": cc["contractor_leads"].get("contractor_size"),
                "specialties": cc["contractor_leads"].get("specialties", []),
                "tier": 1,  # Default to tier 1
                "status": cc.get("status", "pending"),
                "contacted_at": cc.get("sent_at"),
                "responded_at": cc.get("responded_at")
            }

            # Check if internal contractor
            internal_check = db.table("contractors")\
                .select("id")\
                .eq("id", cc["contractor_id"])\
                .limit(1).execute()

            if internal_check.data:
                contractor_data["tier"] = 1
            else:
                # Check for previous outreach
                outreach_check = db.table("contractor_outreach_attempts")\
                    .select("id")\
                    .eq("contractor_lead_id", cc["contractor_id"])\
                    .neq("campaign_id", campaign_id)\
                    .limit(1).execute()

                if outreach_check.data:
                    contractor_data["tier"] = 2
                else:
                    contractor_data["tier"] = 3

            contractors.append(contractor_data)

        # Format response
        response = {
            "campaign_id": campaign["id"],
            "bid_card_id": campaign["bid_card_id"],
            "bid_card_number": campaign["bid_cards"]["bid_card_number"],
            "project_type": campaign["bid_cards"]["project_type"],
            "urgency_level": campaign["bid_cards"].get("urgency_level"),
            "max_contractors": campaign.get("max_contractors", 0),
            "contractors_targeted": campaign.get("contractors_targeted", 0),
            "responses_received": campaign.get("responses_received", 0),
            "campaign_status": campaign.get("status", "active"),
            "created_at": campaign["created_at"],
            "check_ins": [],
            "contractors": contractors
        }

        # Add check-in data
        for check_in in check_ins_result.data:
            response["check_ins"].append({
                "id": check_in["id"],
                "check_in_percentage": check_in.get("check_in_percentage", 0),
                "scheduled_time": check_in.get("scheduled_time"),
                "bids_expected": check_in.get("bids_expected", 0),
                "bids_received": check_in.get("bids_received", 0),
                "on_track": check_in.get("on_track", False),
                "escalation_needed": check_in.get("escalation_needed", False),
                "additional_contractors_needed": check_in.get("additional_contractors_needed", 0),
                "status": check_in.get("status", "pending")
            })

        # Cache the result for 60 seconds
        cache_params = {"campaign_id": campaign_id}
        cache.set("campaign_details", response, cache_params, ttl_seconds=60)
        print(f"[CAMPAIGN DETAILS] Cached result for campaign {campaign_id}")
        
        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching campaign details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONTRACTOR CLEANUP ENDPOINTS
# ============================================================================

@router.post("/delete-fake-contractors")
async def delete_fake_contractors(request: Request, delete_data: dict):
    """Delete fake contractors from the system - BYPASS AUTH FOR CLEANUP"""
    try:
        # Skip authentication for this cleanup operation
        print("[ADMIN DELETE] Starting fake contractor cleanup...")

        # Get fake contractor patterns from request
        fake_patterns = delete_data.get("fake_patterns", [
            "Premium Kitchen%",
            "Budget%",
            "Modern Design%"
        ])

        # Use database client directly
        from database_simple import get_client
        db = get_client()

        deleted_count = 0
        deleted_names = []

        # Delete contractor proposals matching fake patterns
        for pattern in fake_patterns:
            # Find matching proposals first
            find_response = db.table("contractor_proposals").select("*").ilike("contractor_name", pattern).execute()

            if find_response.data:
                for proposal in find_response.data:
                    deleted_names.append(proposal["contractor_name"])

                # Delete the proposals
                delete_response = db.table("contractor_proposals").delete().ilike("contractor_name", pattern).execute()
                deleted_count += len(delete_response.data or [])

        print(f"[ADMIN DELETE] Deleted {deleted_count} fake contractor proposals: {deleted_names}")

        return {
            "success": True,
            "deleted_count": deleted_count,
            "deleted_contractors": deleted_names,
            "message": f"Successfully deleted {deleted_count} fake contractor proposals"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ADMIN DELETE ERROR] {e}")
        raise HTTPException(500, f"Failed to delete fake contractors: {e!s}")
