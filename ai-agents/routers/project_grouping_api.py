"""
Property Project Grouping API - Trade-Based Project Organization
Agent 3: Homeowner Experience UX

Groups maintenance issues by contractor trade/specialty instead of room.
Integrates CIA agent for project conversations and refinement.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
import uuid
import logging

# Import database using existing project pattern
from database_simple import db

# Initialize router
router = APIRouter(prefix="/api/property-projects", tags=["Property Project Grouping"])

logger = logging.getLogger(__name__)

# Use existing database client
supabase = db.client

# ===== TRADE CLASSIFICATION SYSTEM =====

CONTRACTOR_TRADES = {
    "electrical": {
        "keywords": ["outlet", "switch", "wiring", "electrical", "circuit", "breaker", "lighting", "fixture", "electrical panel", "gfci"],
        "description": "Electrical work including outlets, switches, lighting, and circuits",
        "contractor_types": ["electrician", "electrical contractor"],
        "typical_scope": "Install, repair, or upgrade electrical systems and fixtures"
    },
    "plumbing": {
        "keywords": ["plumbing", "pipe", "faucet", "toilet", "sink", "drain", "water", "leak", "pressure", "shower", "bathtub"],
        "description": "Plumbing repairs and installations",
        "contractor_types": ["plumber", "plumbing contractor"],
        "typical_scope": "Fix leaks, install fixtures, repair pipes and drainage"
    },
    "painting": {
        "keywords": ["paint", "painting", "wall", "ceiling", "primer", "color", "finish", "trim", "stain", "coating"],
        "description": "Interior and exterior painting projects",
        "contractor_types": ["painter", "painting contractor"],
        "typical_scope": "Prep and paint walls, ceilings, trim, and exteriors"
    },
    "flooring": {
        "keywords": ["floor", "flooring", "carpet", "tile", "hardwood", "laminate", "vinyl", "subfloor", "grout", "refinish"],
        "description": "Flooring installation and repair",
        "contractor_types": ["flooring contractor", "tile installer", "carpet installer"],
        "typical_scope": "Install, repair, or replace various flooring materials"
    },
    "drywall": {
        "keywords": ["drywall", "wall", "ceiling", "patch", "hole", "crack", "texture", "joint", "compound", "tape"],
        "description": "Drywall repair and installation",
        "contractor_types": ["drywall contractor", "handyman"],
        "typical_scope": "Patch holes, repair cracks, install new drywall"
    },
    "hvac": {
        "keywords": ["hvac", "heating", "cooling", "air conditioning", "furnace", "duct", "vent", "thermostat", "filter"],
        "description": "Heating, ventilation, and air conditioning work",
        "contractor_types": ["hvac contractor", "heating contractor"],
        "typical_scope": "Install, repair, or maintain HVAC systems"
    },
    "roofing": {
        "keywords": ["roof", "roofing", "shingle", "gutter", "chimney", "flashing", "leak", "eave", "soffit"],
        "description": "Roofing and gutter work",
        "contractor_types": ["roofer", "roofing contractor"],
        "typical_scope": "Repair or replace roofing materials and gutters"
    },
    "general_contractor": {
        "keywords": ["renovation", "remodel", "construction", "addition", "structural", "foundation", "framing"],
        "description": "Large-scale renovation and construction projects",
        "contractor_types": ["general contractor", "construction company"],
        "typical_scope": "Manage complex multi-trade projects and renovations"
    },
    "handyman": {
        "keywords": ["handyman", "minor repair", "small job", "maintenance", "quick fix", "touch-up"],
        "description": "Small repairs and maintenance tasks",
        "contractor_types": ["handyman", "maintenance contractor"],
        "typical_scope": "Handle small repairs and maintenance across multiple trades"
    },
    "landscaping": {
        "keywords": ["landscaping", "yard", "garden", "lawn", "sprinkler", "fence", "deck", "patio", "outdoor"],
        "description": "Outdoor and landscaping work",
        "contractor_types": ["landscaper", "lawn care", "deck builder"],
        "typical_scope": "Maintain and improve outdoor spaces and structures"
    }
}

def classify_issue_by_trade(issue_description: str, issue_type: str = "maintenance") -> str:
    """Classify a maintenance issue into contractor trade category"""
    description_lower = issue_description.lower()
    
    # Check each trade for keyword matches
    trade_scores = {}
    for trade, info in CONTRACTOR_TRADES.items():
        score = 0
        for keyword in info["keywords"]:
            if keyword in description_lower:
                score += 1
        trade_scores[trade] = score
    
    # Return trade with highest score, or handyman as default
    best_trade = max(trade_scores.items(), key=lambda x: x[1])
    return best_trade[0] if best_trade[1] > 0 else "handyman"

async def group_issues_by_trade(property_id: str, user_id: str) -> Dict[str, Any]:
    """Group all maintenance issues by contractor trade instead of room"""
    try:
        # Get all maintenance issues for the property
        photos_result = supabase.table("property_photos").select("*").eq("property_id", property_id).execute()
        
        # Extract and classify all issues
        trade_groups = {}
        all_issues = []
        
        for photo in photos_result.data:
            ai_classification = photo.get("ai_classification", {})
            detected_issues = ai_classification.get("detected_issues", [])
            
            for issue in detected_issues:
                if isinstance(issue, str):
                    issue_data = {
                        "id": f"{photo['id']}-{len(all_issues)}",
                        "photo_id": photo["id"],
                        "photo_url": photo.get("photo_url", ""),
                        "photo_filename": photo.get("original_filename", "unknown.jpg"),
                        "room_type": ai_classification.get("room_type", "unknown"),
                        "description": issue,
                        "severity": "medium",
                        "type": "maintenance",
                        "confidence": 0.8,
                        "estimated_cost": "medium",
                        "detected_at": photo.get("created_at", datetime.now()).isoformat()
                    }
                elif isinstance(issue, dict):
                    issue_data = {
                        "id": f"{photo['id']}-{len(all_issues)}",
                        "photo_id": photo["id"],
                        "photo_url": photo.get("photo_url", ""),
                        "photo_filename": photo.get("original_filename", "unknown.jpg"),
                        "room_type": ai_classification.get("room_type", "unknown"),
                        "description": issue.get("description", str(issue)),
                        "severity": issue.get("severity", "medium"),
                        "type": issue.get("type", "maintenance"),
                        "confidence": issue.get("confidence", 0.8),
                        "estimated_cost": issue.get("estimated_cost", "medium"),
                        "detected_at": photo.get("created_at", datetime.now()).isoformat()
                    }
                
                # Classify by trade
                trade = classify_issue_by_trade(issue_data["description"], issue_data["type"])
                issue_data["trade"] = trade
                
                all_issues.append(issue_data)
                
                # Group by trade
                if trade not in trade_groups:
                    trade_groups[trade] = {
                        "trade": trade,
                        "trade_info": CONTRACTOR_TRADES[trade],
                        "issues": [],
                        "total_issues": 0,
                        "severity_breakdown": {"low": 0, "medium": 0, "high": 0, "urgent": 0},
                        "estimated_cost_total": {"low": 0, "medium": 0, "high": 0},
                        "rooms_affected": set(),
                        "photos_involved": set()
                    }
                
                trade_groups[trade]["issues"].append(issue_data)
                trade_groups[trade]["total_issues"] += 1
                trade_groups[trade]["severity_breakdown"][issue_data["severity"]] += 1
                trade_groups[trade]["estimated_cost_total"][issue_data["estimated_cost"]] += 1
                trade_groups[trade]["rooms_affected"].add(issue_data["room_type"])
                trade_groups[trade]["photos_involved"].add(issue_data["photo_id"])
        
        # Convert sets to lists for JSON serialization
        for trade in trade_groups.values():
            trade["rooms_affected"] = list(trade["rooms_affected"])
            trade["photos_involved"] = list(trade["photos_involved"])
            trade["rooms_count"] = len(trade["rooms_affected"])
            trade["photos_count"] = len(trade["photos_involved"])
        
        return {
            "property_id": property_id,
            "total_issues": len(all_issues),
            "trades_identified": len(trade_groups),
            "trade_groups": trade_groups,
            "grouping_method": "trade_based",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error grouping issues by trade: {e}")
        raise HTTPException(status_code=500, detail="Failed to group maintenance issues by trade")

# ===== API ENDPOINTS =====

@router.get("/{property_id}/trade-groups")
async def get_property_trade_groups(property_id: str, user_id: str):
    """Get maintenance issues grouped by contractor trade instead of room"""
    return await group_issues_by_trade(property_id, user_id)

@router.post("/{property_id}/create-trade-projects") 
async def create_trade_based_projects(
    property_id: str, 
    user_id: str, 
    selected_trades: List[str] = None
):
    """Create bid cards for selected trades or all identified trades"""
    try:
        # Get trade groups
        trade_data = await group_issues_by_trade(property_id, user_id)
        trade_groups = trade_data["trade_groups"]
        
        # Use all trades if none specified
        if not selected_trades:
            selected_trades = list(trade_groups.keys())
        
        created_projects = []
        
        for trade in selected_trades:
            if trade not in trade_groups:
                continue
                
            trade_info = trade_groups[trade]
            issues = trade_info["issues"]
            
            # Create project description for this trade
            project_description = f"{trade_info['trade_info']['description']}\n\n"
            project_description += f"Issues identified across {trade_info['rooms_count']} room(s):\n"
            
            for issue in issues:
                project_description += f"- {issue['description']} (from {issue['room_type']})\n"
            
            # Determine overall severity and cost
            severity_counts = trade_info["severity_breakdown"]
            overall_severity = "standard"
            if severity_counts["urgent"] > 0:
                overall_severity = "emergency"
            elif severity_counts["high"] > 0:
                overall_severity = "urgent"
            
            cost_counts = trade_info["estimated_cost_total"]
            budget_multiplier = 1
            if cost_counts["high"] > cost_counts["low"] + cost_counts["medium"]:
                budget_multiplier = 3
            elif cost_counts["medium"] > cost_counts["low"]:
                budget_multiplier = 2
            
            # Create bid card data
            bid_card_data = {
                "id": str(uuid.uuid4()),
                "bid_card_number": f"BC-{trade.upper()}-{int(datetime.now().timestamp())}",
                "user_id": user_id,
                "property_id": property_id,
                "project_type": f"{trade}_project",
                "project_description": project_description,
                "urgency_level": overall_severity,
                "status": "generated",
                "contractor_count_needed": 4,
                "budget_min": 200 * budget_multiplier,
                "budget_max": 800 * budget_multiplier,
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "source": "trade_grouping",
                    "trade": trade,
                    "issues_count": trade_info["total_issues"],
                    "rooms_affected": trade_info["rooms_affected"],
                    "photos_involved": trade_info["photos_involved"]
                }
            }
            
            created_projects.append(bid_card_data)
        
        return {
            "success": True,
            "projects_created": len(created_projects),
            "projects": created_projects,
            "message": f"Created {len(created_projects)} trade-based project bid cards"
        }
        
    except Exception as e:
        logger.error(f"Error creating trade-based projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to create trade-based projects")

@router.post("/{property_id}/refine-project")
async def refine_project_with_cia(
    property_id: str,
    user_id: str,
    trade: str,
    conversation_message: str
):
    """Use CIA agent to refine and discuss a specific trade project"""
    try:
        # Get the trade group for context
        trade_data = await group_issues_by_trade(property_id, user_id)
        trade_groups = trade_data["trade_groups"]
        
        if trade not in trade_groups:
            raise HTTPException(status_code=404, detail=f"Trade '{trade}' not found")
        
        trade_info = trade_groups[trade]
        
        # Prepare context for CIA agent
        project_context = {
            "property_id": property_id,
            "trade": trade,
            "trade_description": trade_info["trade_info"]["description"],
            "issues": trade_info["issues"],
            "rooms_affected": trade_info["rooms_affected"],
            "severity_breakdown": trade_info["severity_breakdown"],
            "user_message": conversation_message
        }
        
        # Call CIA agent for project refinement
        # This would integrate with the existing CIA agent
        cia_response = await call_cia_for_project_refinement(project_context)
        
        return {
            "success": True,
            "trade": trade,
            "cia_response": cia_response,
            "project_context": project_context
        }
        
    except Exception as e:
        logger.error(f"Error refining project with CIA: {e}")
        raise HTTPException(status_code=500, detail="Failed to refine project")

async def call_cia_for_project_refinement(project_context: Dict[str, Any]) -> str:
    """Call CIA agent to discuss and refine a specific trade project"""
    # This would integrate with the existing CIA agent
    # For now, return a structured response
    
    trade = project_context["trade"]
    issues_count = len(project_context["issues"])
    rooms = ", ".join(project_context["rooms_affected"])
    user_message = project_context["user_message"]
    
    # Simulate CIA response - in production this would call the actual CIA agent
    return f"""I understand you want to discuss the {trade} project. I can see we've identified {issues_count} {trade}-related issues across these areas: {rooms}.

Based on your message: "{user_message}"

Let me help you refine this project scope. Would you like to:
1. Combine this with other trades for a larger renovation project?
2. Split these issues into immediate repairs vs. future upgrades?
3. Prioritize certain rooms or issues first?
4. Get recommendations for the best contractor type for this work?

What's most important to you for this {trade} project?"""

@router.get("/trades")
async def get_available_trades():
    """Get list of all available contractor trades with descriptions"""
    return {
        "trades": CONTRACTOR_TRADES,
        "total_trades": len(CONTRACTOR_TRADES)
    }

@router.post("/{property_id}/merge-trades")
async def merge_trade_projects(
    property_id: str,
    user_id: str,
    trades_to_merge: List[str],
    project_name: str = "Combined Project"
):
    """Merge multiple trade projects into a single general contractor project"""
    try:
        # Get trade groups
        trade_data = await group_issues_by_trade(property_id, user_id)
        trade_groups = trade_data["trade_groups"]
        
        merged_issues = []
        total_cost_multiplier = 0
        highest_severity = "standard"
        rooms_affected = set()
        
        for trade in trades_to_merge:
            if trade in trade_groups:
                trade_info = trade_groups[trade]
                merged_issues.extend(trade_info["issues"])
                
                # Accumulate cost
                cost_counts = trade_info["estimated_cost_total"]
                if cost_counts["high"] > 0:
                    total_cost_multiplier += 3
                elif cost_counts["medium"] > 0:
                    total_cost_multiplier += 2
                else:
                    total_cost_multiplier += 1
                
                # Get highest severity
                severity_counts = trade_info["severity_breakdown"]
                if severity_counts["urgent"] > 0:
                    highest_severity = "emergency"
                elif severity_counts["high"] > 0 and highest_severity != "emergency":
                    highest_severity = "urgent"
                
                rooms_affected.update(trade_info["rooms_affected"])
        
        # Create merged project description
        project_description = f"Multi-trade project combining {len(trades_to_merge)} different specialties:\n\n"
        
        for trade in trades_to_merge:
            if trade in trade_groups:
                trade_info = trade_groups[trade]
                project_description += f"{trade_info['trade_info']['description']}:\n"
                for issue in trade_info["issues"][:3]:  # Show first 3 issues per trade
                    project_description += f"  - {issue['description']}\n"
                if len(trade_info["issues"]) > 3:
                    project_description += f"  - Plus {len(trade_info['issues']) - 3} more {trade} issues\n"
                project_description += "\n"
        
        # Create combined bid card
        bid_card_data = {
            "id": str(uuid.uuid4()),
            "bid_card_number": f"BC-COMBINED-{int(datetime.now().timestamp())}",
            "user_id": user_id,
            "property_id": property_id,
            "project_type": "general_contractor_project",
            "project_description": project_description,
            "urgency_level": highest_severity,
            "status": "generated",
            "contractor_count_needed": 3,  # Fewer contractors for larger projects
            "budget_min": 500 * total_cost_multiplier,
            "budget_max": 2000 * total_cost_multiplier,
            "created_at": datetime.now().isoformat(),
            "metadata": {
                "source": "trade_merging",
                "merged_trades": trades_to_merge,
                "total_issues": len(merged_issues),
                "rooms_affected": list(rooms_affected),
                "project_name": project_name
            }
        }
        
        return {
            "success": True,
            "merged_project": bid_card_data,
            "trades_merged": trades_to_merge,
            "total_issues": len(merged_issues),
            "message": f"Created combined project from {len(trades_to_merge)} trades"
        }
        
    except Exception as e:
        logger.error(f"Error merging trade projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to merge trade projects")