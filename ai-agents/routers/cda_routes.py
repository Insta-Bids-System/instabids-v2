"""
CDA Routes - Contractor Discovery Agent API Endpoints
Owner: Agent 2 (Backend Core)
"""

from typing import Optional

from fastapi import APIRouter, HTTPException

# Import CDA agent
from agents.cda.agent import ContractorDiscoveryAgent


# Create router
router = APIRouter()

# Global CDA agent instance (initialized in main.py)
cda_agent: Optional[ContractorDiscoveryAgent] = None

def set_cda_agent(agent: ContractorDiscoveryAgent):
    """Set the CDA agent instance"""
    global cda_agent
    cda_agent = agent

@router.post("/discover/{bid_card_id}")
async def discover_contractors(bid_card_id: str, contractors_needed: int = 5):
    """Discover contractors for a bid card using Opus 4 intelligent matching"""
    if not cda_agent:
        raise HTTPException(500, "CDA agent not initialized")

    try:
        result = cda_agent.discover_contractors(bid_card_id, contractors_needed)

        if result["success"]:
            return {
                "success": True,
                "bid_card_id": result["bid_card_id"],
                "contractors_found": len(result.get("selected_contractors", [])),
                "selected_contractors": result["selected_contractors"],
                "tier_breakdown": result.get("tier_results", {}),
                "processing_time_ms": result.get("processing_time_ms", 0),
                "opus4_analysis": result.get("bid_analysis"),
                "cache_id": result.get("cache_id")
            }
        else:
            raise HTTPException(500, result.get("error", "Unknown error discovering contractors"))

    except Exception as e:
        print(f"[CDA API ERROR] {e}")
        raise HTTPException(500, f"CDA discovery failed: {e!s}")

@router.get("/cache/{bid_card_id}")
async def get_discovery_cache(bid_card_id: str):
    """Get cached contractor discovery results for a bid card"""
    if not cda_agent:
        raise HTTPException(500, "CDA agent not initialized")

    try:
        cache_data = cda_agent.get_discovery_cache(bid_card_id)

        if cache_data:
            return {
                "success": True,
                "cache_data": cache_data
            }
        else:
            raise HTTPException(404, "No discovery cache found for this bid card")

    except Exception as e:
        print(f"[CDA CACHE ERROR] {e}")
        raise HTTPException(500, f"Failed to get discovery cache: {e!s}")
