"""
MCP Bridge API - Allows Python backend to request MCP tool execution
This solves the fundamental problem of MCP tools not being callable from Python
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio
import uuid
import json
from datetime import datetime
from config.service_urls import get_backend_url

router = APIRouter(prefix="/api/mcp", tags=["mcp-bridge"])

# In-memory store for MCP requests (in production, use Redis)
pending_requests = {}
completed_requests = {}

class MCPToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    timeout_seconds: Optional[int] = 30
    request_id: Optional[str] = None

class MCPToolResponse(BaseModel):
    request_id: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    completed_at: str

@router.post("/request-tool-execution", response_model=Dict[str, str])
async def request_tool_execution(request: MCPToolRequest):
    """
    Request MCP tool execution - Claude will see this and execute the tool
    
    This creates a pending request that Claude can pick up and execute
    """
    if not request.request_id:
        request.request_id = str(uuid.uuid4())
    
    pending_requests[request.request_id] = {
        "tool_name": request.tool_name,
        "parameters": request.parameters,
        "created_at": datetime.now().isoformat(),
        "timeout_seconds": request.timeout_seconds,
        "status": "pending"
    }
    
    return {
        "request_id": request.request_id,
        "status": "pending",
        "message": f"MCP tool request {request.tool_name} queued for execution"
    }

@router.get("/pending-requests")
async def get_pending_requests():
    """
    Get all pending MCP requests - Claude calls this to see what needs execution
    """
    return {
        "pending_requests": pending_requests,
        "count": len(pending_requests)
    }

@router.post("/complete-request/{request_id}")
async def complete_request(request_id: str, response: Dict[str, Any]):
    """
    Complete a request - Claude calls this after executing the MCP tool
    """
    if request_id not in pending_requests:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Move from pending to completed
    completed_requests[request_id] = {
        **pending_requests[request_id],
        "result": response.get("result"),
        "error": response.get("error"),
        "success": response.get("success", True),
        "completed_at": datetime.now().isoformat(),
        "status": "completed"
    }
    
    del pending_requests[request_id]
    
    return {"message": "Request completed successfully"}

@router.get("/request-status/{request_id}")
async def get_request_status(request_id: str):
    """
    Check status of a request - Python backend calls this to get results
    """
    # Check if completed
    if request_id in completed_requests:
        return completed_requests[request_id]
    
    # Check if still pending
    if request_id in pending_requests:
        return {
            **pending_requests[request_id],
            "status": "pending"
        }
    
    raise HTTPException(status_code=404, detail="Request not found")

@router.get("/health")
async def health_check():
    """Health check for MCP bridge"""
    return {
        "status": "operational",
        "pending_count": len(pending_requests),
        "completed_count": len(completed_requests),
        "timestamp": datetime.now().isoformat()
    }

# Utility functions for common MCP operations
class MCPClient:
    """Helper class for making MCP tool requests from Python code"""
    
    @staticmethod
    async def execute_supabase_sql(project_id: str, query: str, timeout: int = 30):
        """Execute Supabase SQL via MCP bridge"""
        import httpx
        
        # Create request
        async with httpx.AsyncClient() as client:
            request_response = await client.post(f"{get_backend_url()}/api/mcp/request-tool-execution", 
                json={
                    "tool_name": "mcp__supabase__execute_sql",
                    "parameters": {
                        "project_id": project_id,
                        "query": query
                    },
                    "timeout_seconds": timeout
                }
            )
            
            if request_response.status_code != 200:
                raise Exception(f"Failed to create MCP request: {request_response.text}")
            
            request_id = request_response.json()["request_id"]
            
            # Poll for completion
            for _ in range(timeout):
                await asyncio.sleep(1)
                
                status_response = await client.get(f"{get_backend_url()}/api/mcp/request-status/{request_id}")
                
                if status_response.status_code == 200:
                    result = status_response.json()
                    if result["status"] == "completed":
                        if result["success"]:
                            return result["result"]
                        else:
                            raise Exception(f"MCP tool failed: {result['error']}")
            
            raise Exception(f"MCP request timed out after {timeout} seconds")
    
    @staticmethod
    async def web_search(query: str, timeout: int = 30):
        """Execute web search via MCP bridge"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            request_response = await client.post(f"{get_backend_url()}/api/mcp/request-tool-execution",
                json={
                    "tool_name": "WebSearch",
                    "parameters": {"query": query},
                    "timeout_seconds": timeout
                }
            )
            
            request_id = request_response.json()["request_id"]
            
            # Poll for completion
            for _ in range(timeout):
                await asyncio.sleep(1)
                
                status_response = await client.get(f"{get_backend_url()}/api/mcp/request-status/{request_id}")
                
                if status_response.status_code == 200:
                    result = status_response.json()
                    if result["status"] == "completed":
                        return result["result"] if result["success"] else None
            
            return None