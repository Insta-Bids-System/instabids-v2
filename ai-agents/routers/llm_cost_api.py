"""
LLM Cost Monitoring API
Provides endpoints for tracking and analyzing LLM usage costs
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List
import json

from database_simple import SupabaseDB

router = APIRouter(prefix="/api/llm-costs", tags=["LLM Cost Monitoring"])

# Helper function to execute SQL queries via Supabase client
async def execute_sql_query(query: str):
    """Execute SQL query using Supabase client"""
    db = SupabaseDB()
    try:
        # Use the rpc method for raw SQL queries
        result = db.client.rpc('execute_sql', {'query': query}).execute()
        return result.data
    except Exception as e:
        # If RPC doesn't work, fall back to simpler table operations
        print(f"SQL query failed: {e}")
        return []

@router.get("/dashboard")
async def get_cost_dashboard():
    """
    Get comprehensive LLM cost dashboard data
    Shows today's costs, trends, and breakdowns by agent/model
    """
    db = SupabaseDB()
    
    try:
        # For now, return mock data until we have real usage
        # Later this will query: SELECT * FROM llm_usage_log WHERE DATE(timestamp) = CURRENT_DATE
        today_data = []
        
        # Check if we have any data
        result = db.client.table("llm_usage_log").select("count", count="exact").execute()
        total_records = result.count if hasattr(result, 'count') else 0
        
        # Calculate totals
        total_cost_today = sum(row["daily_cost"] or 0 for row in today_data)
        total_calls_today = sum(row["total_calls"] or 0 for row in today_data)
        total_tokens_today = sum(row["total_tokens"] or 0 for row in today_data)
        
        # Get 7-day trend
        trend_query = """
        SELECT 
            DATE(timestamp) as date,
            SUM(cost_usd) as daily_cost,
            COUNT(*) as daily_calls,
            SUM(total_tokens) as daily_tokens
        FROM llm_usage_log 
        WHERE timestamp >= NOW() - INTERVAL '7 days'
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
        """
        
        trend_data = await db.execute_query(trend_query)
        
        # Get agent breakdown
        agent_breakdown = {}
        for row in today_data:
            agent = row["agent_name"]
            if agent not in agent_breakdown:
                agent_breakdown[agent] = {
                    "cost": 0,
                    "calls": 0,
                    "tokens": 0,
                    "models": {}
                }
            
            agent_breakdown[agent]["cost"] += row["daily_cost"] or 0
            agent_breakdown[agent]["calls"] += row["total_calls"] or 0
            agent_breakdown[agent]["tokens"] += row["total_tokens"] or 0
            
            model = f"{row['provider']}/{row['model']}"
            if model not in agent_breakdown[agent]["models"]:
                agent_breakdown[agent]["models"][model] = {
                    "cost": 0,
                    "calls": 0
                }
            agent_breakdown[agent]["models"][model]["cost"] += row["daily_cost"] or 0
            agent_breakdown[agent]["models"][model]["calls"] += row["total_calls"] or 0
        
        return {
            "summary": {
                "date": date.today().isoformat(),
                "total_cost_usd": round(total_cost_today, 4),
                "total_calls": total_calls_today,
                "total_tokens": total_tokens_today,
                "average_cost_per_call": round(total_cost_today / total_calls_today, 6) if total_calls_today > 0 else 0
            },
            "agent_breakdown": agent_breakdown,
            "trend_7_days": trend_data,
            "details_by_model": today_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/{agent_name}")
async def get_agent_costs(
    agent_name: str,
    days: int = Query(7, ge=1, le=30)
):
    """Get detailed cost analysis for a specific agent"""
    db = SupabaseDB()
    
    try:
        query = f"""
        SELECT 
            DATE(timestamp) as date,
            model,
            provider,
            COUNT(*) as calls,
            SUM(cost_usd) as cost,
            SUM(total_tokens) as tokens,
            AVG(duration_ms) as avg_duration
        FROM llm_usage_log 
        WHERE agent_name = '{agent_name}'
            AND timestamp >= NOW() - INTERVAL '{days} days'
        GROUP BY DATE(timestamp), model, provider
        ORDER BY date DESC, cost DESC
        """
        
        result = await db.execute_query(query)
        
        # Calculate totals
        total_cost = sum(row["cost"] or 0 for row in result)
        total_calls = sum(row["calls"] or 0 for row in result)
        total_tokens = sum(row["tokens"] or 0 for row in result)
        
        return {
            "agent": agent_name,
            "period_days": days,
            "summary": {
                "total_cost": round(total_cost, 4),
                "total_calls": total_calls,
                "total_tokens": total_tokens,
                "avg_cost_per_call": round(total_cost / total_calls, 6) if total_calls > 0 else 0
            },
            "daily_breakdown": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/expensive")
async def get_expensive_sessions(
    limit: int = Query(10, ge=1, le=50),
    min_cost: float = Query(1.0, ge=0)
):
    """Find the most expensive user sessions"""
    db = SupabaseDB()
    
    try:
        query = f"""
        SELECT 
            session_id,
            user_id,
            COUNT(DISTINCT agent_name) as agents_used,
            SUM(cost_usd) as session_cost,
            COUNT(*) as total_calls,
            SUM(total_tokens) as total_tokens,
            MIN(timestamp) as session_start,
            MAX(timestamp) as session_end,
            EXTRACT(EPOCH FROM (MAX(timestamp) - MIN(timestamp)))/60 as duration_minutes
        FROM llm_usage_log
        WHERE session_id IS NOT NULL
        GROUP BY session_id, user_id
        HAVING SUM(cost_usd) >= {min_cost}
        ORDER BY session_cost DESC
        LIMIT {limit}
        """
        
        result = await db.execute_query(query)
        
        return {
            "expensive_sessions": result,
            "min_cost_threshold": min_cost,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/comparison")
async def compare_model_costs():
    """Compare costs across different models"""
    db = SupabaseDB()
    
    try:
        query = """
        SELECT 
            provider,
            model,
            COUNT(*) as total_calls,
            SUM(cost_usd) as total_cost,
            SUM(total_tokens) as total_tokens,
            AVG(cost_usd) as avg_cost_per_call,
            AVG(total_tokens) as avg_tokens_per_call,
            AVG(duration_ms) as avg_duration_ms
        FROM llm_usage_log
        WHERE timestamp >= NOW() - INTERVAL '7 days'
        GROUP BY provider, model
        ORDER BY total_cost DESC
        """
        
        result = await db.execute_query(query)
        
        # Calculate cost per 1K tokens for each model
        for row in result:
            if row["total_tokens"] and row["total_tokens"] > 0:
                row["cost_per_1k_tokens"] = round((row["total_cost"] / row["total_tokens"]) * 1000, 6)
            else:
                row["cost_per_1k_tokens"] = 0
        
        return {
            "model_comparison": result,
            "period": "last_7_days"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/status")
async def check_cost_alerts():
    """Check if any cost thresholds have been exceeded"""
    db = SupabaseDB()
    
    try:
        # Get today's total
        today_query = """
        SELECT SUM(cost_usd) as total_cost
        FROM llm_usage_log
        WHERE DATE(timestamp) = CURRENT_DATE
        """
        
        today_result = await db.execute_query(today_query)
        today_cost = today_result[0]["total_cost"] if today_result else 0
        
        # Get current hour total
        hour_query = """
        SELECT SUM(cost_usd) as hour_cost
        FROM llm_usage_log
        WHERE timestamp >= NOW() - INTERVAL '1 hour'
        """
        
        hour_result = await db.execute_query(hour_query)
        hour_cost = hour_result[0]["hour_cost"] if hour_result else 0
        
        # Define thresholds (these could come from config)
        thresholds = {
            "daily_limit": 200.00,
            "hourly_spike": 50.00,
            "daily_warning": 150.00
        }
        
        alerts = []
        
        if today_cost >= thresholds["daily_limit"]:
            alerts.append({
                "type": "CRITICAL",
                "message": f"Daily limit exceeded: ${today_cost:.2f} / ${thresholds['daily_limit']:.2f}",
                "threshold": "daily_limit"
            })
        elif today_cost >= thresholds["daily_warning"]:
            alerts.append({
                "type": "WARNING",
                "message": f"Approaching daily limit: ${today_cost:.2f} / ${thresholds['daily_limit']:.2f}",
                "threshold": "daily_warning"
            })
        
        if hour_cost >= thresholds["hourly_spike"]:
            alerts.append({
                "type": "WARNING",
                "message": f"Unusual hourly spend: ${hour_cost:.2f}",
                "threshold": "hourly_spike"
            })
        
        return {
            "current_status": {
                "today_cost": round(today_cost, 2),
                "hour_cost": round(hour_cost, 2),
                "thresholds": thresholds
            },
            "alerts": alerts,
            "alert_count": len(alerts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/realtime/stream")
async def get_realtime_costs():
    """Get costs for the last 5 minutes for real-time monitoring"""
    db = SupabaseDB()
    
    try:
        query = """
        SELECT 
            agent_name,
            provider,
            model,
            cost_usd,
            total_tokens,
            duration_ms,
            timestamp,
            error_occurred
        FROM llm_usage_log
        WHERE timestamp >= NOW() - INTERVAL '5 minutes'
        ORDER BY timestamp DESC
        LIMIT 50
        """
        
        result = await db.execute_query(query)
        
        # Calculate 5-minute totals
        total_cost = sum(row["cost_usd"] or 0 for row in result)
        total_calls = len(result)
        
        return {
            "realtime_data": result,
            "five_minute_summary": {
                "total_cost": round(total_cost, 4),
                "total_calls": total_calls,
                "calls_per_minute": round(total_calls / 5, 1) if total_calls > 0 else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))