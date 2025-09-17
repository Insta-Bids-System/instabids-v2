"""
Monitoring Routes - Agent Health and System Monitoring
Owner: Agent 6 (QA/Testing/Monitoring)
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException

import database_simple as database


# Create router
router = APIRouter()

# Agent Health Check Endpoints
@router.get("/agents/{agent_name}/health")
async def get_agent_health(agent_name: str):
    """Get health status for a specific agent"""
    try:
        # Track agent operation metrics
        agent_metrics = {
            "CIA": {
                "last_operation": None,
                "total_operations": 0,
                "errors_today": 0,
                "avg_response_time": 0
            },
            "JAA": {
                "last_operation": None,
                "total_operations": 0,
                "errors_today": 0,
                "avg_response_time": 0
            },
            "CDA": {
                "last_operation": None,
                "total_operations": 0,
                "errors_today": 0,
                "avg_response_time": 0
            },
            "EAA": {
                "last_operation": None,
                "total_operations": 0,
                "errors_today": 0,
                "avg_response_time": 0
            },
            "WFA": {
                "last_operation": None,
                "total_operations": 0,
                "errors_today": 0,
                "avg_response_time": 0
            }
        }

        # Get real metrics from database for the agent
        if agent_name in agent_metrics:
            # Query recent operations for this agent
            today = datetime.now().date()

            # Get operation counts from relevant tables based on agent
            if agent_name == "CIA":
                # Check agent_conversations table for recent CIA activity
                result = database.client.table("agent_conversations").select("*").eq("agent_name", "CIA").gte("created_at", str(today)).execute()
                total_ops = len(result.data) if result.data else 0

            elif agent_name == "JAA":
                # Check bid_cards table for recent JAA creations
                result = database.client.table("bid_cards").select("*").gte("created_at", str(today)).execute()
                total_ops = len(result.data) if result.data else 0

            elif agent_name == "CDA":
                # Check contractor_campaigns table for recent CDA discovery operations
                result = database.client.table("contractor_campaigns").select("*").gte("created_at", str(today)).execute()
                total_ops = len(result.data) if result.data else 0

            elif agent_name == "EAA":
                # Check external_outreach_attempts table for recent EAA outreach
                result = database.client.table("external_outreach_attempts").select("*").gte("created_at", str(today)).execute()
                total_ops = len(result.data) if result.data else 0

            elif agent_name == "WFA":
                # Check website_form_submissions table for recent WFA submissions
                result = database.client.table("website_form_submissions").select("*").gte("created_at", str(today)).execute()
                total_ops = len(result.data) if result.data else 0

            agent_metrics[agent_name]["total_operations"] = total_ops

            # Calculate health score based on recent activity
            health_score = 100 if total_ops > 0 else 85  # Reduce if no recent activity

            return {
                "agent": agent_name,
                "status": "online",
                "health_score": health_score,
                "metrics": agent_metrics[agent_name],
                "last_checked": datetime.now().isoformat()
            }
        else:
            return {
                "agent": agent_name,
                "status": "unknown",
                "health_score": 0,
                "error": "Agent not found"
            }

    except Exception as e:
        print(f"[AGENT HEALTH ERROR] {agent_name}: {e}")
        return {
            "agent": agent_name,
            "status": "error",
            "health_score": 0,
            "error": str(e)
        }

@router.get("/agents/status")
async def get_all_agents_status():
    """Get status summary for all agents"""
    try:
        agents = ["CIA", "JAA", "CDA", "EAA", "WFA", "COIA", "IRIS"]
        agent_statuses = []

        for agent in agents:
            try:
                # Get basic status for each agent
                status = {
                    "name": agent,
                    "status": "online",
                    "health_score": 100,
                    "response_time": 0.1,
                    "last_seen": datetime.now().isoformat(),
                    "operations_today": 0
                }

                # Get operation count for today
                today = datetime.now().date()

                if agent == "CIA":
                    result = database.client.table("agent_conversations").select("*").eq("agent_name", "CIA").gte("created_at", str(today)).execute()
                    status["operations_today"] = len(result.data) if result.data else 0
                elif agent == "JAA":
                    result = database.client.table("bid_cards").select("*").gte("created_at", str(today)).execute()
                    status["operations_today"] = len(result.data) if result.data else 0
                elif agent == "CDA":
                    result = database.client.table("contractor_campaigns").select("*").gte("created_at", str(today)).execute()
                    status["operations_today"] = len(result.data) if result.data else 0
                elif agent == "EAA":
                    result = database.client.table("external_outreach_attempts").select("*").gte("created_at", str(today)).execute()
                    status["operations_today"] = len(result.data) if result.data else 0
                elif agent == "WFA":
                    result = database.client.table("website_form_submissions").select("*").gte("created_at", str(today)).execute()
                    status["operations_today"] = len(result.data) if result.data else 0

                agent_statuses.append(status)

            except Exception as e:
                print(f"[AGENT STATUS ERROR] {agent}: {e}")
                agent_statuses.append({
                    "name": agent,
                    "status": "error",
                    "health_score": 0,
                    "error": str(e)
                })

        return {
            "timestamp": datetime.now().isoformat(),
            "agents": agent_statuses,
            "system_status": "operational"
        }

    except Exception as e:
        print(f"[ALL AGENTS STATUS ERROR] {e}")
        raise HTTPException(500, f"Failed to get agent statuses: {e!s}")

@router.get("/")
async def health_check():
    """Main health check endpoint"""
    return {
        "status": "online",
        "service": "Instabids API v2.0",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables"""
    import os

    # Only show non-sensitive env vars
    safe_vars = [
        "PORT", "NODE_ENV", "SUPABASE_URL", "FRONTEND_URL",
        "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB"
    ]

    env_info = {}
    for var in safe_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive parts
            if "key" in var.lower() or "password" in var.lower() or "secret" in var.lower():
                env_info[var] = f"{value[:10]}..." if len(value) > 10 else "***"
            else:
                env_info[var] = value
        else:
            env_info[var] = "NOT SET"

    # Show API key status without revealing the key
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    env_info["ANTHROPIC_API_KEY_STATUS"] = "SET" if anthropic_key else "NOT SET"

    return {
        "environment_variables": env_info,
        "python_path": os.getcwd(),
        "timestamp": datetime.now().isoformat()
    }
