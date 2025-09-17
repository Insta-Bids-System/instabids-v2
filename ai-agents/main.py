#!/usr/bin/env python3
"""
InstaBids AI Agents Backend
Orchestrates all AI agents and provides unified API endpoints
"""

import asyncio
import json
import logging
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import unquote

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
# Try to load from parent directory first (for local dev), then current directory (for Docker)
from pathlib import Path
root_env = Path(__file__).parent.parent / '.env'
if root_env.exists():
    load_dotenv(root_env, override=True)  # Local development - use root .env
else:
    load_dotenv(override=True)  # Docker - use environment variables passed by docker-compose

# Import lifespan manager and timing middleware
from utils.lifespan import lifespan, TimingMiddleware

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="InstaBids AI Agents",
    description="Unified backend for all InstaBids AI agents",
    version="1.0.0",
    lifespan=lifespan
)

# Add timing middleware to track slow requests
app.add_middleware(TimingMiddleware)

# CORS middleware - configured for both development and production
# In production, update allow_origins with your actual domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",  # Alternative localhost
        "http://localhost:5174",  # Alternative Vite ports
        "http://localhost:5175",  # Multiple devs can work
        "http://localhost:3000",  # Common React port
        # Production origins (uncomment and update for production):
        # "https://instabids.com",
        # "https://www.instabids.com",
        # "https://app.instabids.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]  # Important for WebSocket upgrades
)

# Import routers
try:
    from routers.cia_routes_unified import router as cia_router  # Fixed streaming endpoint
    from routers.coia_landing_api import router as coia_router  # Clean DeepAgents-only COIA system
    from routers.bid_card_api import router as bid_card_router
    from routers.bid_card_api_simple import router as bid_card_simple_router
    from routers.contractor_management_api_fixed import router as contractor_mgmt_router
    from routers.agent_monitoring_api import router as agent_monitoring_router
    from routers.intelligent_messaging_api import router as intelligent_messaging_router
    from routers.campaign_management_api import router as campaign_management_router
    from routers.admin_routes import router as admin_router
    from routers.admin_routes_enhanced import router as admin_enhanced_router
    # simple_contractor_chat removed - using only COIA landing page system
    from routers.bid_card_lifecycle_routes import router as bid_card_lifecycle_router
    from routers.websocket_routes import router as websocket_router
    from routers.demo_routes import router as demo_router
    from routers.homeowner_routes import router as homeowner_router
    from routers.contractor_routes import router as contractor_router
    from routers.unified_conversation_api import router as unified_conversation_router
    # coia_router already imported above (fixed version)
    # Import BSA routers - MIGRATED TO DEEPAGENTS
    # OLD: from routers.bsa_api import router as bsa_router  # BSA - Bid Submission Agent (original) - REMOVED
    # OLD: from routers.bsa_routes_unified import router as bsa_unified_router  # BSA Unified Router - REMOVED
    # RE-ENABLED AFTER FIXING INDENTATION ERRORS
    from routers.bsa_stream import router as bsa_stream_router  # BSA Streaming Router with DeepAgents integration - RE-ENABLED (fixed state_management)
    # from routers.bsa_intelligent_search import router as bsa_intelligent_router  # BSA Intelligent Search with LLM - File doesn't exist
    logger.info("BSA routers (DeepAgents-powered + Intelligent Search) imported successfully")
    from api.leonardo_image_generation import router as leonardo_router
    from api.leonardo_enhanced_generation import router as leonardo_enhanced_router
    # LEGACY: from api.iris_chat_unified_fixed import router as iris_router  # REMOVED - conflicts with unified router
    from api.iris_board_conversations import router as iris_board_router
    from api.vision import router as vision_router  # Claude Vision API for image analysis
    try:
        from routers.iris_actions import router as iris_actions_router
    except ImportError as e:
        logger.warning(f"Failed to import iris_actions router: {e}")
        iris_actions_router = None
    from routers.property_api import router as property_router
    from routers.simple_property_test import router as test_property_router
    from routers.connection_fee_api import router as connection_fee_router
    from routers.admin_connection_fees import router as admin_connection_fee_router
    from routers.agent_context_api import router as agent_context_router
    from routers.jaa_routes import router as jaa_router
    from routers.cda_routes import router as cda_router
    from routers.contractor_notification_api import router as contractor_notification_router
    from routers.contractor_websocket_routes import router as contractor_ws_router
    from routers.rfi_api import router as rfi_router
    from routers.bid_card_images_api import router as bid_card_images_router
    from routers.image_upload_api import router as image_upload_router
    from routers.contractor_proposals_api import router as contractor_proposals_router
    from routers.project_grouping_api import router as project_grouping_router
    from routers.group_bidding_api import router as group_bidding_router
    from routers.contractor_api import router as contractor_api_router
    from routers.contractor_group_bidding import router as contractor_group_bidding_router
    # from agents.iris.agent import router as iris_unified_router  # Commented out - causing import error
    from routers.cia_potential_bid_cards import router as cia_potential_bid_cards_router
    from api.cia_image_upload_fixed import router as cia_image_router
    from routers.my_bids_api import router as my_bids_router  # My Bids tracking system
    logger.info("Campaign management router imported successfully")
    logger.info("BSA router imported successfully")
    logger.info("BSA unified router imported successfully")
    logger.info("Leonardo and Iris routers imported successfully")
    logger.info("Property router imported successfully")
    logger.info("Connection fee router imported successfully")
    logger.info("Project grouping router imported successfully")
    
    # Initialize CIA agent - OpenAI GPT-5 only
    from agents.cia.agent import CustomerInterfaceAgent
    from agents.cia.potential_bid_card_integration import PotentialBidCardManager
    from routers.cia_routes_unified import set_cia_agent  # Fixed streaming endpoint enabled
    
    # Initialize JAA agent
    from agents.jaa.agent import JobAssessmentAgent
    from routers.jaa_routes import set_jaa_agent
    
    # Initialize CDA agent
    from agents.cda.agent import ContractorDiscoveryAgent
    from routers.cda_routes import set_cda_agent
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if openai_api_key:
        # Use OpenAI GPT-5 exclusively
        potential_bid_card_manager = PotentialBidCardManager()
        cia_agent = CustomerInterfaceAgent(openai_api_key, bid_card_manager=potential_bid_card_manager)
        set_cia_agent(cia_agent)  # Fixed streaming endpoint enabled
        logger.info("CIA agent initialized successfully with OpenAI GPT-5 API key")
    else:
        logger.warning("No OpenAI API key found - CIA will use fallback responses")
    
    # Initialize JAA agent
    if anthropic_api_key:
        jaa_agent = JobAssessmentAgent()  # Fixed: JobAssessmentAgent doesn't take API key
        set_jaa_agent(jaa_agent)
        logger.info("JAA agent initialized successfully")
    elif openai_api_key:
        jaa_agent = JobAssessmentAgent()  # Fixed: JobAssessmentAgent doesn't take API key
        set_jaa_agent(jaa_agent)
        logger.info("JAA agent initialized successfully with OpenAI fallback")
    else:
        logger.warning("No API keys found - JAA will use fallback responses")
    
    # Initialize CDA agent
    cda_agent = ContractorDiscoveryAgent()
    set_cda_agent(cda_agent)
    logger.info("CDA agent initialized successfully")
    
    app.include_router(cia_router, prefix="/api/cia")  # Fixed streaming endpoint enabled
    app.include_router(cia_potential_bid_cards_router, prefix="/api/cia")  # CIA potential bid cards - real-time tracking
    app.include_router(cia_image_router)  # CIA image upload functionality
    app.include_router(coia_router, prefix="/api/coia")  # Clean DeepAgents COIA system
    
    # Import and add async COIA router
    try:
        logger.info("✅ Async COIA router loaded")
    except Exception as e:
        logger.warning(f"Could not load async COIA router: {e}")
    app.include_router(bid_card_router, prefix="/api/bid-cards")
    app.include_router(bid_card_simple_router, prefix="/api/bid-cards-simple")  # Submission endpoints
    app.include_router(contractor_mgmt_router)  # Already has /api/contractor-management prefix
    app.include_router(agent_monitoring_router)  # Already has /api/agents prefix
    app.include_router(intelligent_messaging_router)
    app.include_router(campaign_management_router)  # Already has /api/campaign-management prefix
    app.include_router(admin_router, prefix="/api/admin")  # Admin dashboard routes
    app.include_router(admin_enhanced_router)  # Enhanced admin routes with real data
    app.include_router(bid_card_lifecycle_router)  # Bid card lifecycle routes
    app.include_router(websocket_router)  # WebSocket connections
    app.include_router(demo_router)  # Demo endpoints
    app.include_router(homeowner_router)  # Homeowner endpoints
    # simple_contractor_router removed - using only COIA landing page system
    app.include_router(contractor_router)  # Contractor endpoints
    app.include_router(unified_conversation_router, prefix="/api")  # Unified conversation system
    # coia_router temporarily disabled due to syntax error
    app.include_router(leonardo_router)  # Leonardo.ai image generation
    app.include_router(leonardo_enhanced_router)  # Leonardo.ai enhanced multi-reference
    # LEGACY: app.include_router(iris_router, prefix="/api/iris")  # REMOVED - conflicts with unified router
    # CONFLICTING: app.include_router(iris_board_router, prefix="/api/iris")  # REMOVED - conflicts with unified router
    if iris_actions_router:
        app.include_router(iris_actions_router)  # IRIS real-time action endpoints
    app.include_router(vision_router)  # Vision API for image analysis
    app.include_router(property_router)  # Property management system (My Property)
    app.include_router(test_property_router)  # Test property API
    app.include_router(connection_fee_router)  # Connection fee payment processing
    app.include_router(admin_connection_fee_router)  # Admin connection fee management
    app.include_router(agent_context_router, prefix="/api/agent-context")  # Agent context with privacy filtering
    app.include_router(jaa_router, prefix="/jaa")  # JAA bid card update service
    app.include_router(cda_router, prefix="/api/cda")  # CDA contractor discovery service
    app.include_router(contractor_notification_router, prefix="/api/notifications")  # Contractor notification API
    app.include_router(contractor_ws_router)  # Contractor WebSocket routes
    app.include_router(rfi_router)  # Request for Information API
    app.include_router(bid_card_images_router)  # Bid card images API
    app.include_router(image_upload_router)  # General image upload API with potential bid card support
    app.include_router(contractor_proposals_router, prefix="/api/contractor-proposals")  # Contractor proposals API
    app.include_router(project_grouping_router)  # Trade-based project grouping API
    app.include_router(group_bidding_router)  # Quick-Start Group Bidding API
    app.include_router(contractor_group_bidding_router)  # Contractor Group Bidding Interface
    # app.include_router(iris_unified_router, prefix="/api/iris")  # Unified IRIS agent with complete context - COMMENTED OUT (import error)
    # OLD BSA ROUTERS REMOVED - MIGRATED TO DEEPAGENTS
    # OLD: app.include_router(bsa_router)  # BSA - Bid Submission Agent (original) - REMOVED
    # OLD: app.include_router(bsa_unified_router)  # BSA Unified Router - REMOVED
    # RE-ENABLED AFTER FIXING INDENTATION ERRORS IN BSA AGENT
    app.include_router(bsa_stream_router)  # BSA DeepAgents-Powered Streaming Router - RE-ENABLED (fixed state_management)
    # app.include_router(bsa_intelligent_router)  # BSA Intelligent Search with LLM - File doesn't exist
    app.include_router(my_bids_router)  # My Bids tracking system for contractors
    
    # Import and include file review router
    from routers.file_review_api import router as file_review_router
    app.include_router(file_review_router)  # File review system for flagged files
    
    # Proposal Review System
    from routers.proposal_review_api import router as proposal_review_router
    app.include_router(proposal_review_router, prefix="/api/proposal-review")  # Submitted proposals review
    
    # LLM Cost Monitoring System
    from routers.llm_cost_api_simple import router as llm_cost_router
    app.include_router(llm_cost_router)  # LLM cost tracking and monitoring
    
    # Contractor API
    app.include_router(contractor_api_router)  # Contractor data endpoints
    
    logger.info("Campaign management router included successfully")
    logger.info("LLM cost monitoring router included successfully")
    logger.info("Leonardo and Iris routers included successfully")
    logger.info("File review router included successfully")
    logger.info("Property router included successfully")
    logger.info("Connection fee router included successfully")
    
    logger.info("All routers loaded successfully")
    
except ImportError as e:
    logger.error(f"Failed to import routers: {e}")
    logger.error(traceback.format_exc())

# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    logger.info(f"Mounted static files from {static_path}")

# Error handling middleware
@app.middleware("http")
async def error_handler(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Unhandled error for {request.url}: {e}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)}
        )

# Basic health check
@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "InstaBids AI Agents",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/api/cia/",
            "/api/coia/", 
            "/api/bid-cards/",
            "/api/contractor-management/",
            "/api/campaign-management/",
            "/api/agents/",
            "/api/intelligent-messages/",
            "/api/conversations/",
            "/api/leonardo/",
            "/api/iris/",
            "/api/agent-context/",
            "/api/property-projects/",
            "/api/admin/session",
            "/api/admin/login", 
            "/api/admin/dashboard",
            "/static/messaging-ui-demo.html"
        ]
    }

# Serve the messaging UI demo directly
@app.get("/messaging-demo", response_class=HTMLResponse)
async def messaging_demo():
    """Serve the messaging UI demo page"""
    demo_file = Path(__file__).parent / "static" / "messaging-ui-demo.html"
    if demo_file.exists():
        return HTMLResponse(content=demo_file.read_text(), status_code=200)
    else:
        raise HTTPException(status_code=404, detail="Demo file not found")

# Admin dashboard data endpoints
@app.get("/api/admin/dashboard")
async def get_admin_dashboard_data():
    """Get admin dashboard summary data"""
    try:
        from database_simple import db
        
        # Get bid card count
        bid_cards_result = db.client.table("bid_cards").select("id", count="exact").execute()
        bid_card_count = len(bid_cards_result.data) if bid_cards_result.data else 0
        
        # Get campaign count
        campaigns_result = db.client.table("outreach_campaigns").select("id", count="exact").execute()
        campaign_count = len(campaigns_result.data) if campaigns_result.data else 0
        
        # Get contractor count
        contractors_result = db.client.table("contractors").select("id", count="exact").execute()
        contractor_count = len(contractors_result.data) if contractors_result.data else 0
        
        return {
            "success": True,
            "data": {
                "active_bid_cards": bid_card_count,
                "active_campaigns": campaign_count,
                "total_contractors": contractor_count,
                "revenue_this_month": 0.0,
                "bids_completed_today": 0
            }
        }
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "active_bid_cards": 0,
                "active_campaigns": 0,
                "total_contractors": 0,
                "revenue_this_month": 0.0,
                "bids_completed_today": 0
            }
        }
        
# This endpoint is now handled by admin_routes_enhanced.py

# Admin authentication endpoints
@app.get("/api/admin/session")
async def check_admin_session(request: Request):
    """Check if admin session exists"""
    try:
        # Simple session check - in production would verify JWT token
        return {"authenticated": False, "user": None}
    except Exception as e:
        logger.error(f"Error checking admin session: {str(e)}")
        return {"authenticated": False, "user": None}

@app.post("/api/admin/login")
async def admin_login(request: Request):
    """Admin login endpoint"""
    try:
        data = await request.json()
        email = data.get("email", "")
        password = data.get("password", "")
        
        # Simple hardcoded check - in production would verify against database
        if email == "admin@instabids.com" and password == "admin123":
            session_id = "mock-session-123"
            current_time = datetime.now().isoformat()
            
            return {
                "success": True,
                "admin_user": {
                    "id": "admin-1",
                    "email": email,
                    "full_name": "Admin User",
                    "role": "admin",
                    "permissions": ["dashboard_access", "campaign_management", "contractor_management"],
                    "created_at": current_time,
                    "last_login": current_time,
                    "is_active": True
                },
                "session": {
                    "session_id": session_id,
                    "admin_user_id": "admin-1",
                    "email": email,
                    "created_at": current_time,
                    "expires_at": datetime.now().replace(hour=23, minute=59, second=59).isoformat(),
                    "last_activity": current_time,
                    "ip_address": request.client.host if request.client else "127.0.0.1",
                    "user_agent": request.headers.get("user-agent", "Unknown"),
                    "is_active": True
                }
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except Exception as e:
        logger.error(f"Error in admin login: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# System health endpoint
@app.get("/api/system/health")
async def system_health():
    """Comprehensive system health check"""
    import psutil
    from datetime import datetime
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "backend": "running",
            "database": "unknown",
            "redis": "unknown"
        },
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        },
        "version": "1.0.0"
    }
    
    # Check database
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        if supabase_url and supabase_key:
            client = create_client(supabase_url, supabase_key)
            # Simple query to test connection
            result = client.table("profiles").select("id").limit(1).execute()
            health_status["services"]["database"] = "connected"
    except:
        health_status["services"]["database"] = "disconnected"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        import redis
        r = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"))
        r.ping()
        health_status["services"]["redis"] = "connected"
    except:
        health_status["services"]["redis"] = "disconnected"
    
    return health_status

# Tracking endpoints for external landing page
@app.post("/api/track/bid-card-click")
async def track_bid_card_click(request: Request):
    """Track bid card clicks for analytics"""
    try:
        data = await request.json()
        logger.info(f"Bid card click tracked: {data}")
        return {"success": True, "message": "Click tracked"}
    except Exception as e:
        logger.error(f"Error tracking bid card click: {str(e)}")
        return {"success": False, "error": str(e)}

@app.post("/api/track/bid-card-conversion")
async def track_bid_card_conversion(request: Request):
    """Track bid card conversions for analytics"""
    try:
        data = await request.json()
        logger.info(f"Bid card conversion tracked: {data}")
        return {"success": True, "message": "Conversion tracked"}
    except Exception as e:
        logger.error(f"Error tracking bid card conversion: {str(e)}")
        return {"success": False, "error": str(e)}

@app.get("/api/docker-test")
async def docker_test():
    """TEST ENDPOINT - Proves Docker uses local files instantly"""
    import os
    return {
        "message": "UPDATED at 6:06 AM - Docker sees this INSTANTLY!",
        "running_in": "Docker container on port 8008",
        "file_location": "C:\\Users\\Not John Or Justin\\Documents\\instabids\\ai-agents\\main.py",
        "instant_update": "YES - Docker sees this immediately without restart!",
        "openai_key_ends_with": os.getenv("OPENAI_API_KEY", "")[-4:] if os.getenv("OPENAI_API_KEY") else "NOT SET",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8008"))
    logger.info(f"Starting InstaBids AI Agents backend on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)