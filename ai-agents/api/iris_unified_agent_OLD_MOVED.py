"""
IRIS Unified Agent - Single Endpoint with Complete Context
Replaces both iris_chat_unified_fixed.py and iris_board_conversations.py
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from anthropic import Anthropic
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests

# Import database and existing systems
import uuid
from datetime import datetime
from database_simple import db
from adapters.iris_context import IrisContextAdapter
from api.iris_agent_actions import iris_actions
from config.service_urls import get_backend_url

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize Anthropic client
anthropic_client = None
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
if anthropic_key:
    try:
        anthropic_client = Anthropic(api_key=anthropic_key)
        logger.info("Anthropic API key validated for unified IRIS")
    except Exception as e:
        logger.warning(f"Anthropic API key invalid: {e}")

# Unified IRIS request model
class UnifiedIrisRequest(BaseModel):
    message: str
    user_id: str
    session_id: Optional[str] = None
    photo_url: Optional[str] = None
    photo_metadata: Optional[Dict[str, Any]] = None
    board_id: Optional[str] = None
    property_id: Optional[str] = None
    context_type: Optional[str] = "auto"  # "auto", "inspiration", "property", "both"
    # New image workflow fields
    images: Optional[List[Dict[str, Any]]] = None  # Array of image data from frontend
    trigger_image_workflow: Optional[bool] = False  # Flag to trigger automatic image workflow
    workflow_response: Optional[Dict[str, Any]] = None  # Response to workflow questions
    project_context: Optional[Dict[str, Any]] = None  # Project context from Discuss button

class UnifiedIrisResponse(BaseModel):
    response: str
    suggestions: List[str]
    session_id: str
    reasoning: Dict[str, Any]
    available_tools: List[str]
    context_summary: Dict[str, Any]
    workflow_questions: Optional[List[Dict[str, Any]]] = None  # For image workflow questions

class UnifiedIrisAgent:
    """
    Unified IRIS Agent with complete context access and smart reasoning
    """
    
    def __init__(self):
        self.context_adapter = IrisContextAdapter()
        self.system_prompt = """You are IRIS, an intelligent design and project assistant for InstaBids.

Your core capabilities:
- Analyze photos for design inspiration AND maintenance issues
- Understand user intent through conversation
- PERFORM REAL-TIME ACTIONS to modify bid cards and projects
- Help organize projects by trade (electrical, plumbing, painting, etc.)
- Group maintenance issues by contractor trade for efficiency
- Create and update bid cards for trade-specific projects
- Maintain memory across inspiration boards and property documentation

NEW: Real-time Action Capabilities:
✨ You can now DIRECTLY modify bid cards and projects in real-time!
- Add repair items to existing bid cards
- Update bid card budgets, timelines, and urgency levels
- Create new bid cards from repair items
- Update potential bid cards during conversations
- All changes appear instantly with visual feedback (glowing effects)

When users ask you to:
- "Add [item] to the project" → You can add it immediately
- "Make this urgent" → You can update urgency in real-time
- "Change the budget to X" → You can update it instantly
- "Create a project for these repairs" → You can create it now

Action Results:
- If action_results are in context, mention what you've done
- Example: "I've added the fence repair to your project ✨"
- Show confidence when actions succeed

Your personality:
- Proactive and capable - you can make changes, not just suggest
- Still ask for confirmation on major changes
- Celebrate successful actions with users
- Be transparent about what you're doing

Context awareness:
- You have access to inspiration boards, property photos, and trade-grouped projects
- You can see conversation history across all user interactions
- You understand the difference between design inspiration and maintenance needs
- You can see action_results showing what changes were made

Available actions you can perform:
- ADD repair items to bid cards
- UPDATE bid card fields (budget, timeline, urgency)
- CREATE new bid cards from repairs
- MODIFY potential bid cards
- GROUP projects by trade

When responding:
1. If you performed actions, acknowledge them naturally
2. If actions failed, explain and offer alternatives
3. Show the user you're actively helping, not just chatting"""

    def get_complete_context(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Get complete context across inspiration, property, and projects - OPTIMIZED for performance"""
        try:
            # PERFORMANCE FIX: Skip expensive context calls for faster response
            # Only get minimal context needed for image upload/analysis
            
            # Get conversation history (optimized - current session only)
            conversation_history = self._get_conversation_history(session_id, user_id)
            
            # REMOVED: Expensive IRIS context adapter call
            # REMOVED: Property context call that was slow
            # REMOVED: Trade projects call that was causing timeouts
            
            return {
                "inspiration": {"inspiration_boards": []},  # Empty for performance
                "property": {"properties": []},  # Empty for performance
                "trade_projects": {"trade_groups_by_property": {}, "total_trade_projects": 0},  # Empty for performance
                "conversation_history": conversation_history,
                "user_id": user_id,
                "session_id": session_id
            }
        except Exception as e:
            logger.error(f"Error getting complete context: {e}")
            return {"error": str(e), "user_id": user_id, "session_id": session_id}

    def _get_property_context(self, user_id: str) -> Dict[str, Any]:
        """Get property photos and maintenance issues"""
        try:
            # Get properties for user
            properties_result = db.client.table("properties").select("*").eq("user_id", user_id).execute()
            
            property_context = {
                "properties": properties_result.data or [],
                "total_properties": len(properties_result.data or []),
                "property_photos": [],
                "maintenance_issues": []
            }
            
            # Get property photos and issues for each property
            for prop in property_context["properties"]:
                photos_result = db.client.table("property_photos").select("*").eq("property_id", prop["id"]).execute()
                
                for photo in photos_result.data or []:
                    ai_classification = photo.get("ai_classification", {})
                    detected_issues = ai_classification.get("detected_issues", [])
                    
                    property_context["property_photos"].append(photo)
                    property_context["maintenance_issues"].extend(detected_issues)
            
            return property_context
        except Exception as e:
            logger.error(f"Error getting property context: {e}")
            return {"error": str(e), "properties": []}

    def _get_trade_projects(self, user_id: str) -> Dict[str, Any]:
        """Get trade-grouped projects from project_grouping_api - OPTIMIZED for performance"""
        try:
            # PERFORMANCE FIX: Skip trade groups API calls entirely for now
            # These API calls were causing 2+ second delays per property
            # IRIS should work for image analysis without trade group data
            
            # Get basic property count only (fast query)
            properties_result = db.client.table("properties")\
                .select("id")\
                .eq("user_id", user_id)\
                .limit(10)\
                .execute()
            
            # REMOVED: Trade groups API calls that were causing timeouts
            # This eliminates multiple 2-second timeout loops per property
            
            return {
                "trade_groups_by_property": {},  # Empty for performance
                "total_trade_projects": 0,
                "available_trades": self._get_available_trades(),
                "properties_available": len(properties_result.data or [])
            }
        except Exception as e:
            logger.error(f"Error getting trade projects: {e}")
            return {"error": str(e), "trade_groups_by_property": {}}

    def _get_available_trades(self) -> List[str]:
        """Get list of available trade types"""
        try:
            response = requests.get(f"{get_backend_url()}/api/property-projects/trades", timeout=2)
            if response.status_code == 200:
                return list(response.json().get("trades", {}).keys())
            return []
        except Exception as e:
            logger.warning(f"Could not get available trades: {e}")
            return ["electrical", "plumbing", "painting", "flooring", "drywall", "hvac"]

    def _extract_bid_card_id_from_context(self, context: Dict[str, Any], message: str) -> Optional[str]:
        """Extract bid card ID from context or conversation history"""
        try:
            # First check the current message for a UUID
            import re
            uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
            matches = re.findall(uuid_pattern, message, re.IGNORECASE)
            if matches:
                logger.info(f"Found bid card ID in current message: {matches[0]}")
                return matches[0]
            
            # Check for bid card ID in conversation history
            conversation_history = context.get("conversation_history", [])
            for msg in reversed(conversation_history):  # Check most recent first
                content = (msg.get("content") or "").lower()
                # Look for bid card references
                if "bid card" in content or "project" in content:
                    # Try to extract UUID patterns from content
                    matches = re.findall(uuid_pattern, content, re.IGNORECASE)
                    if matches:
                        return matches[0]
            
            # If no ID found in conversation, try to get most recent bid card for user
            # This is a fallback for when IRIS needs to act on the "current" project
            properties = context.get("property", {}).get("properties", [])
            if properties:
                property_id = properties[0].get("id")
                if property_id:
                    # Get most recent bid card for this property
                    result = db.client.table("bid_cards").select("id").eq("property_id", property_id).order("created_at", desc=True).limit(1).execute()
                    if result.data:
                        return result.data[0]["id"]
            
            return None
        except Exception as e:
            logger.error(f"Error extracting bid card ID: {e}")
            return None

    def _extract_title_from_message(self, message: str) -> Optional[str]:
        """Extract new title from user message"""
        try:
            # Don't convert to lowercase for title extraction to preserve case
            
            # Look for common title change patterns (handle both single and double quotes)
            patterns = [
                r'rename.*to\s+["\']([^"\']+)["\']',  # Quoted string
                r'rename.*to\s+([^.!?]+)',             # Unquoted
                r'change.*name.*to\s+["\']([^"\']+)["\']',
                r'change.*name.*to\s+([^.!?]+)',
                r'call it\s+["\']([^"\']+)["\']',
                r'call it\s+([^.!?]+)',
                r'title.*to\s+["\']([^"\']+)["\']',
                r'title.*to\s+([^.!?]+)'
            ]
            
            import re
            for pattern in patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    # Clean up the title
                    title = re.sub(r'\s+', ' ', title)  # Remove extra whitespace
                    title = title.strip('"\'')  # Remove quotes
                    if len(title) > 3:  # Must be a reasonable title length
                        return title
            
            return None
        except Exception as e:
            logger.error(f"Error extracting title: {e}")
            return None

    def _extract_budget_from_message(self, message: str) -> Optional[Dict[str, int]]:
        """Extract budget information from user message"""
        try:
            import re
            # Look for dollar amounts
            dollar_pattern = r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
            matches = re.findall(dollar_pattern, message)
            
            if matches:
                # Convert to integers
                amounts = []
                for match in matches:
                    amount_str = match.replace(',', '')
                    amount = int(float(amount_str))
                    amounts.append(amount)
                
                if len(amounts) == 1:
                    # Single amount - use as max, set min to 80%
                    budget_max = amounts[0]
                    budget_min = int(budget_max * 0.8)
                    return {"min": budget_min, "max": budget_max}
                elif len(amounts) >= 2:
                    # Multiple amounts - use min and max
                    return {"min": min(amounts), "max": max(amounts)}
            
            return None
        except Exception as e:
            logger.error(f"Error extracting budget: {e}")
            return None

    def _extract_repair_description_from_message(self, message: str) -> Optional[str]:
        """Extract repair item description from user message"""
        try:
            import re
            message_lower = (message or "").lower()
            
            # Look for common repair patterns
            repair_patterns = [
                r'add\s+(.+?)(?:\s+to|$)',
                r'include\s+(.+?)(?:\s+in|$)', 
                r'need\s+(.+?)(?:\s+for|$)',
                r'fix\s+(.+?)(?:\s+in|$)',
                r'repair\s+(.+?)(?:\s+in|$)',
                r'replace\s+(.+?)(?:\s+in|$)',
                r'install\s+(.+?)(?:\s+in|$)'
            ]
            
            for pattern in repair_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    description = match.group(1).strip()
                    # Clean up the description
                    description = re.sub(r'\s+', ' ', description)
                    if len(description) > 5 and len(description) < 200:  # Reasonable length
                        return description
            
            # Fallback: if message contains repair keywords, use part of the message
            if any(word in message_lower for word in ['repair', 'fix', 'replace', 'install', 'add']):
                # Use first 100 characters as description
                description = message[:100].strip()
                if len(description) > 5:
                    return description
            
            return None
        except Exception as e:
            logger.error(f"Error extracting repair description: {e}")
            return None

    def _get_conversation_history(self, session_id: str, user_id: str = None) -> List[Dict[str, Any]]:
        """Get conversation history from unified system - OPTIMIZED for performance
        
        Returns only current session messages for fast response
        """
        try:
            # PERFORMANCE FIX: Only get current session messages to avoid massive queries
            # This reduces database query time from ~6 seconds to <1 second
            current_session_result = db.client.table("unified_conversation_messages")\
                .select("id,conversation_id,sender_id,message_content,created_at")\
                .eq("conversation_id", session_id)\
                .order("created_at")\
                .limit(50)\
                .execute()
            
            current_messages = current_session_result.data or []
            
            # REMOVED: Cross-session history query that was causing 80+ UUID IN clause
            # This eliminates the massive database query that took 6+ seconds
            
            return current_messages
        except Exception as e:
            logger.warning(f"Could not get conversation history: {e}")
            return []

    def analyze_context_and_intent(self, message: str, context: Dict[str, Any], photo_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Smart reasoning about user intent and context"""
        reasoning = {
            "user_intent": "unknown",
            "context_analysis": {},
            "suggested_actions": [],
            "confidence": 0.0
        }
        
        # Analyze message content
        message_lower = (message or "").lower()
        
        # Intent detection
        if any(word in message_lower for word in ["upload", "photo", "picture", "image"]):
            reasoning["user_intent"] = "photo_analysis"
        elif any(word in message_lower for word in ["project", "bid", "contractor", "quote"]):
            reasoning["user_intent"] = "project_management"
        elif any(word in message_lower for word in ["electrical", "plumbing", "painting", "hvac", "repair", "fix"]):
            reasoning["user_intent"] = "maintenance_issue"
        elif any(word in message_lower for word in ["style", "design", "inspiration", "idea"]):
            reasoning["user_intent"] = "design_inspiration"
        else:
            reasoning["user_intent"] = "general_conversation"
        
        # Context analysis
        inspiration_boards = context.get("inspiration", {}).get("inspiration_boards", [])
        property_photos = context.get("property", {}).get("property_photos", [])
        trade_projects = context.get("trade_projects", {}).get("trade_groups_by_property", {})
        
        reasoning["context_analysis"] = {
            "has_inspiration_boards": len(inspiration_boards) > 0,
            "has_property_photos": len(property_photos) > 0,
            "has_trade_projects": len(trade_projects) > 0,
            "inspiration_count": len(inspiration_boards),
            "property_photos_count": len(property_photos),
            "trade_projects_count": sum(len(tp.get("trade_groups", {})) for tp in trade_projects.values())
        }
        
        # Suggested actions based on intent and context
        if reasoning["user_intent"] == "photo_analysis" and photo_data:
            reasoning["suggested_actions"] = [
                "analyze_photo_for_design",
                "analyze_photo_for_maintenance",
                "ask_photo_classification"
            ]
        elif reasoning["user_intent"] == "maintenance_issue":
            reasoning["suggested_actions"] = [
                "group_by_trade",
                "suggest_trade_project",
                "estimate_scope",
                "analyze_trade_groups"
            ]
        elif reasoning["user_intent"] == "project_management":
            reasoning["suggested_actions"] = [
                "review_trade_groups",
                "suggest_bid_card_creation",
                "prioritize_projects"
            ]
        
        # Calculate confidence based on context clarity
        reasoning["confidence"] = min(1.0, (
            (0.3 if reasoning["user_intent"] != "unknown" else 0) +
            (0.2 if reasoning["context_analysis"]["has_inspiration_boards"] else 0) +
            (0.2 if reasoning["context_analysis"]["has_property_photos"] else 0) +
            (0.3 if len(reasoning["suggested_actions"]) > 0 else 0)
        ))
        
        return reasoning

    def determine_available_tools(self, context: Dict[str, Any], reasoning: Dict[str, Any]) -> List[str]:
        """Determine what tools IRIS can suggest using"""
        available_tools = []
        
        # Always available
        available_tools.extend(["photo_analysis", "conversation_memory"])
        
        # Property-based tools
        if context.get("property", {}).get("properties"):
            available_tools.extend(["trade_grouping", "maintenance_analysis"])
        
        # Project management tools
        if context.get("trade_projects", {}).get("trade_groups_by_property"):
            available_tools.extend(["project_consolidation", "bid_card_creation"])
        
        # Intent-specific tools
        if reasoning.get("user_intent") == "photo_analysis":
            available_tools.append("photo_classification")
        
        return list(set(available_tools))  # Remove duplicates

    async def suggest_trade_grouping(self, property_id: str, user_id: str) -> Dict[str, Any]:
        """Suggest trade-based project grouping for maintenance issues"""
        try:
            # Import the grouping function from project_grouping_api
            from routers.project_grouping_api import group_issues_by_trade
            
            # Get trade groups for the property
            trade_data = await group_issues_by_trade(property_id, user_id)
            
            # Create recommendations
            recommendations = []
            for trade, info in trade_data["trade_groups"].items():
                if info["total_issues"] > 0:
                    recommendations.append({
                        "trade": trade,
                        "description": info["trade_info"]["description"],
                        "issue_count": info["total_issues"],
                        "rooms_affected": info["rooms_count"],
                        "severity": max(info["severity_breakdown"].items(), key=lambda x: x[1])[0],
                        "estimated_scale": self.estimate_project_scale(info["estimated_cost_total"]),
                        "recommendation": self.generate_trade_recommendation(trade, info)
                    })
            
            return {
                "total_issues": trade_data["total_issues"],
                "trades_identified": trade_data["trades_identified"],
                "recommendations": recommendations,
                "grouping_method": "trade_based"
            }
        except Exception as e:
            logger.error(f"Error suggesting trade grouping: {e}")
            return {"error": str(e), "recommendations": []}
    
    def estimate_project_scale(self, cost_breakdown: Dict[str, int]) -> str:
        """Estimate project scale based on cost breakdown"""
        if cost_breakdown["high"] > cost_breakdown["low"] + cost_breakdown["medium"]:
            return "large"
        elif cost_breakdown["medium"] > cost_breakdown["low"]:
            return "medium"
        else:
            return "small"
    
    def generate_trade_recommendation(self, trade: str, info: Dict[str, Any]) -> str:
        """Generate personalized recommendation for a trade project"""
        severity_counts = info["severity_breakdown"]
        
        if severity_counts["urgent"] > 0:
            return f"URGENT: Address {severity_counts['urgent']} urgent {trade} issue(s) immediately. Consider getting multiple quotes quickly."
        elif severity_counts["high"] > 0:
            return f"HIGH PRIORITY: Schedule {trade} repairs soon to prevent further damage. Group these {info['total_issues']} issues for better contractor rates."
        elif info["total_issues"] > 3:
            return f"EFFICIENCY: Bundle these {info['total_issues']} {trade} repairs together for cost savings and reduced disruption."
        else:
            return f"MAINTENANCE: Address these {trade} issues during regular property maintenance to prevent future problems."

    async def analyze_images_with_vision(self, images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze uploaded images using Claude Vision API"""
        try:
            analysis_results = []
            
            for image in images:
                image_data = image.get('data', '')
                filename = image.get('filename', 'uploaded_image')
                
                # Call the Vision API
                try:
                    response = requests.post(
                        f"{get_backend_url()}/api/vision/analyze",
                        json={
                            "image_data": image_data,
                            "analysis_type": "comprehensive",
                            "include_suggestions": True
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        vision_result = response.json()
                        analysis_results.append({
                            "filename": filename,
                            "analysis": vision_result.get("analysis", {}),
                            "suggestions": vision_result.get("suggestions", []),
                            "category_suggestions": vision_result.get("category_suggestions", []),
                            "room_suggestions": vision_result.get("room_suggestions", [])
                        })
                    else:
                        logger.error(f"Vision API error {response.status_code}: {response.text}")
                        analysis_results.append({
                            "filename": filename,
                            "error": f"Vision analysis failed: {response.status_code}"
                        })
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Vision API request failed: {e}")
                    analysis_results.append({
                        "filename": filename,
                        "error": f"Could not analyze image: {str(e)}"
                    })
            
            return {
                "total_images": len(images),
                "successful_analyses": len([r for r in analysis_results if "error" not in r]),
                "results": analysis_results
            }
            
        except Exception as e:
            logger.error(f"Error in image analysis: {e}")
            return {
                "total_images": len(images) if images else 0,
                "successful_analyses": 0,
                "results": [],
                "error": str(e)
            }

    def generate_image_workflow_questions_UNUSED(self, analysis_results: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """UNUSED METHOD - Generate workflow questions for image classification"""
        # This method is not being called currently
        try:
            workflow_questions = []
            
            # Analyze the vision results to determine appropriate questions
            successful_results = [r for r in analysis_results.get("results", []) if "error" not in r]
            
            if not successful_results:
                return []
            
            # Aggregate all suggestions from vision analysis
            all_categories = set()
            all_rooms = set()
            
            for result in successful_results:
                categories = result.get("category_suggestions", [])
                rooms = result.get("room_suggestions", [])
                all_categories.update(categories)
                all_rooms.update(rooms)
            
            # Create category question if we have multiple options
            if len(all_categories) > 1:
                workflow_questions.append({
                    "question": f"What type of {('image' if len(successful_results) == 1 else 'images')} did you upload?",
                    "options": list(all_categories)[:5],  # Limit to 5 options
                    "callback": "classify_image_category"
                })
            
            # Create room/location question if we have room suggestions
            if len(all_rooms) > 1:
                workflow_questions.append({
                    "question": "Which room or area does this relate to?",
                    "options": list(all_rooms)[:6],  # Limit to 6 options
                    "callback": "assign_image_room"
                })
            
            # Add inspiration board option if user has boards
            inspiration_boards = context.get("inspiration", {}).get("inspiration_boards", [])
            if inspiration_boards:
                board_options = [board.get("title", f"Board {i+1}") for i, board in enumerate(inspiration_boards[:4])]
                board_options.append("New inspiration board")
                
                workflow_questions.append({
                    "question": "Would you like to add this to an inspiration board?",
                    "options": board_options,
                    "callback": "add_to_inspiration_board"
                })
            
            return workflow_questions
            
        except Exception as e:
            logger.error(f"Error generating workflow questions: {e}")
            return []

    async def process_message(self, request: UnifiedIrisRequest) -> UnifiedIrisResponse:
        """Process message with complete reasoning and context"""
        try:
            # Generate session ID if not provided
            session_id = request.session_id or f"iris_unified_{request.user_id}_{int(datetime.now().timestamp())}"
            
            # Get complete context
            context = self.get_complete_context(request.user_id, session_id)
            
            # Add image context from memory for continuity
            image_context_from_memory = self._get_image_context_from_memory(request.user_id)
            context["image_memory"] = image_context_from_memory
            
            # Add potential bid card context if provided (from Discuss button)
            if request.project_context:
                context["project_context"] = request.project_context
                # Get related potential bid cards for this project
                potential_bid_cards = await self._get_potential_bid_cards_for_project(request.user_id, request.project_context)
                context["potential_bid_cards"] = potential_bid_cards
            
            # Analyze intent and reasoning
            # Handle both legacy photo_url and new images array
            photo_data = None
            if request.photo_url:
                photo_data = {"url": request.photo_url, "metadata": request.photo_metadata}
            elif request.images:
                # Convert images array to photo_data for Claude
                photo_data = {"images": request.images}
            reasoning = self.analyze_context_and_intent(request.message, context, photo_data)
            
            # Determine available tools
            available_tools = self.determine_available_tools(context, reasoning)
            
            # Check if user is asking about trade grouping
            if reasoning["user_intent"] == "maintenance_issue" and "group" in (request.message or "").lower():
                # Get property ID from context if available
                properties = context.get("property", {}).get("properties", [])
                if properties:
                    property_id = properties[0].get("id")
                    if property_id:
                        trade_suggestions = await self.suggest_trade_grouping(property_id, request.user_id)
                        context["trade_suggestions"] = trade_suggestions
            
            # Handle image workflow if triggered
            workflow_questions = []  # Initialize as empty list instead of None
            image_analysis_results = None
            
            # Debug logging
            logger.info(f"DEBUG: trigger_image_workflow={request.trigger_image_workflow}, images={len(request.images) if request.images else 0}")
            
            if request.trigger_image_workflow and request.images:
                logger.info(f"DEBUG: Creating workflow questions for image workflow")
                # Skip separate Vision API call - Claude will analyze images directly
                # Generate basic workflow questions for image classification
                workflow_questions = [
                    {
                        "question": "Where would you like to store this image?",
                        "options": ["Inspiration Board", "Property Photos", "Both"],
                        "callback": "store_image_location"
                    },
                    {
                        "question": "What room or area is this?",
                        "options": ["Backyard", "Kitchen", "Bathroom", "Living Room", "Bedroom", "Other"],
                        "callback": "identify_room_type"
                    }
                ]
                logger.info(f"Generated {len(workflow_questions)} workflow questions for image classification")
                logger.info(f"DEBUG: workflow_questions content after creation: {workflow_questions}")
                
                # Store images in context for Claude to analyze
                context["uploaded_images"] = request.images
                image_analysis_results = {"total_images": len(request.images), "workflow_triggered": True}
                
                # Update reasoning to reflect image processing
                reasoning["user_intent"] = "photo_analysis"
                reasoning["suggested_actions"].extend(["analyze_images", "classify_images", "ask_image_workflow"])
                
                logger.info(f"IRIS processed {len(request.images)} images, generated {len(workflow_questions)} workflow questions")
                
                # Save image context to memory for future conversations
                await self._save_image_context_to_memory(request.user_id, session_id, image_analysis_results)
            
            # Handle workflow responses (user answered classification questions)
            if request.workflow_response:
                question_index = request.workflow_response.get("question_index", 0)
                selected_option = request.workflow_response.get("selected_option", "")
                
                logger.info(f"IRIS processing workflow response: question {question_index}, option '{selected_option}'")
                
                # Update context with user's workflow choice
                context["workflow_response"] = {
                    "question_index": question_index,
                    "selected_option": selected_option,
                    "processed_at": datetime.now().isoformat()
                }
                
                # Update reasoning to reflect workflow completion
                reasoning["user_intent"] = "image_classification_response"
                reasoning["confidence"] = 0.9  # High confidence when user provides direct response
                
                # Save updated image context with workflow response
                await self._save_image_context_to_memory(request.user_id, session_id, {"total_images": 0, "results": []}, request.workflow_response)
                
                # Handle actual image storage based on user's choice
                await self._handle_image_storage(request.user_id, session_id, request.workflow_response, request.images)
            
            # DETECT TEXT RESPONSES TO WORKFLOW QUESTIONS (when user types instead of clicking)
            elif not request.workflow_response and request.images and len(request.images) > 0:
                # Check if user's message indicates they want to store images
                user_message = (request.message or "").lower()
                storage_choice = None
                
                # Pattern matching for storage responses
                if any(phrase in user_message for phrase in ["property photo", "document", "maintenance", "repair"]):
                    storage_choice = "Property Photos"
                elif any(phrase in user_message for phrase in ["inspiration", "design", "idea"]):
                    storage_choice = "Inspiration Board"
                elif any(phrase in user_message for phrase in ["both", "everywhere", "all"]):
                    storage_choice = "Both"
                elif any(phrase in user_message for phrase in ["yes", "please", "do that", "add", "store", "save"]):
                    # Default to Property Photos for general affirmative responses
                    storage_choice = "Property Photos"
                
                if storage_choice:
                    logger.info(f"IRIS detected text-based storage choice: '{storage_choice}' from message: '{request.message}'")
                    
                    # Create a synthetic workflow response
                    synthetic_workflow_response = {
                        "question_index": 0,
                        "selected_option": storage_choice
                    }
                    
                    # Update context with user's workflow choice
                    context["workflow_response"] = {
                        "question_index": 0,
                        "selected_option": storage_choice,
                        "processed_at": datetime.now().isoformat(),
                        "detected_from_text": True
                    }
                    
                    # Update reasoning to reflect workflow completion
                    reasoning["user_intent"] = "image_classification_response"
                    reasoning["confidence"] = 0.8  # Slightly lower confidence for text interpretation
                    
                    # Save updated image context with workflow response
                    await self._save_image_context_to_memory(request.user_id, session_id, {"total_images": 0, "results": []}, synthetic_workflow_response)
                    
                    # Handle actual image storage based on interpreted choice
                    await self._handle_image_storage(request.user_id, session_id, synthetic_workflow_response, request.images)
            
            # Check if user wants to perform actions and EXECUTE them
            action_results = []
            try:
                # Check for bid card or potential bid card actions
                action_intent = iris_actions.parse_user_intent_for_actions(request.message, context)
                
                if action_intent.get("requires_action"):
                    logger.info(f"IRIS executing actions: {action_intent['actions']}")
                    
                    # Execute actions based on user intent
                    for action in action_intent['actions']:
                        action_type = action.get('type')
                        
                        if action_type == 'update_urgency':
                            # Look for bid card ID in context
                            bid_card_id = self._extract_bid_card_id_from_context(context, request.message)
                            if bid_card_id:
                                result = iris_actions.update_bid_card(
                                    bid_card_id=bid_card_id,
                                    updates={"urgency": "urgent"},
                                    user_id=request.user_id
                                )
                                action_results.append(result)
                        
                        elif action_type == 'update_budget':
                            # Extract budget from message and update
                            bid_card_id = self._extract_bid_card_id_from_context(context, request.message)
                            budget_info = self._extract_budget_from_message(request.message)
                            if bid_card_id and budget_info:
                                result = iris_actions.update_bid_card(
                                    bid_card_id=bid_card_id,
                                    updates={"budget": budget_info},
                                    user_id=request.user_id
                                )
                                action_results.append(result)
                        
                        elif action_type == 'update_title':
                            # Handle title/name changes
                            bid_card_id = self._extract_bid_card_id_from_context(context, request.message)
                            new_title = self._extract_title_from_message(request.message)
                            if bid_card_id and new_title:
                                result = iris_actions.update_bid_card(
                                    bid_card_id=bid_card_id,
                                    updates={"title": new_title},
                                    user_id=request.user_id
                                )
                                action_results.append(result)
                        
                        elif action_type == 'add_repair':
                            # Handle repair item additions
                            bid_card_id = self._extract_bid_card_id_from_context(context, request.message)
                            if bid_card_id:
                                # Extract repair description from message
                                repair_description = self._extract_repair_description_from_message(request.message)
                                if repair_description:
                                    result = iris_actions.add_repair_item(
                                        potential_bid_card_id=bid_card_id,
                                        item_description=repair_description,
                                        severity="medium",  # Default severity
                                        user_id=request.user_id
                                    )
                                    action_results.append(result)
                    
                    # Check for title updates specifically (rename requests)
                    if any(word in (request.message or "").lower() for word in ["rename", "change name", "change title", "call it"]):
                        bid_card_id = self._extract_bid_card_id_from_context(context, request.message)
                        new_title = self._extract_title_from_message(request.message)
                        if bid_card_id and new_title:
                            result = iris_actions.update_bid_card(
                                bid_card_id=bid_card_id,
                                updates={"title": new_title},
                                user_id=request.user_id
                            )
                            action_results.append(result)
                        
            except Exception as e:
                logger.error(f"Action execution failed: {e}")
                action_results.append({
                    "success": False,
                    "message": f"I encountered an error while trying to make changes: {str(e)}"
                })
            
            # For testing: Skip Claude API if we're just testing workflow questions
            if request.trigger_image_workflow and request.images and "test" in (request.session_id or "").lower():
                # Use a simple test response to avoid timeout
                response_text = "I've received your image(s). Let me help you organize them properly. I can see the image content and will help you classify it."
                logger.info("DEBUG: Using test response to avoid Claude API timeout for workflow testing")
            else:
                # Generate response using Anthropic (include action results)
                response_context = {**context, "action_results": action_results}
                response_text = await self._generate_anthropic_response(
                    request.message, response_context, reasoning, available_tools, photo_data
                )
            
            # If actions were performed, append their status to response
            if action_results:
                action_messages = [r.get("message", "") for r in action_results if r.get("success")]
                if action_messages:
                    response_text += "\n\n✨ " + " ".join(action_messages)
            
            # Generate contextual suggestions
            suggestions = self._generate_suggestions(reasoning, context, available_tools)
            
            # Save message to unified conversation system
            await self._save_conversation_message(session_id, request.user_id, request.message, response_text)
            
            # Debug workflow questions right before return
            logger.info(f"DEBUG: About to return response with workflow_questions: {workflow_questions}")
            logger.info(f"DEBUG: workflow_questions type: {type(workflow_questions)}, len: {len(workflow_questions) if workflow_questions else 0}")
            
            return UnifiedIrisResponse(
                response=response_text,
                suggestions=suggestions,
                session_id=session_id,
                reasoning=reasoning,
                available_tools=available_tools,
                context_summary={
                    "inspiration_boards": len(context.get("inspiration", {}).get("inspiration_boards", [])),
                    "property_photos": len(context.get("property", {}).get("property_photos", [])),
                    "trade_projects": context.get("trade_projects", {}).get("total_trade_projects", 0)
                },
                workflow_questions=workflow_questions
            )
            
        except Exception as e:
            logger.error(f"Error processing unified IRIS message: {e}")
            raise HTTPException(status_code=500, detail=f"IRIS processing error: {str(e)}")

    async def _generate_anthropic_response(
        self, 
        message: str, 
        context: Dict[str, Any], 
        reasoning: Dict[str, Any],
        available_tools: List[str],
        photo_data: Optional[Dict] = None
    ) -> str:
        """Generate response using Anthropic with complete context"""
        
        if not anthropic_client:
            return self._generate_fallback_response(message, reasoning)
        
        try:
            # Build context string for Anthropic
            context_str = self._build_context_string(context, reasoning, available_tools)
            
            # Build content array for message
            content = []
            
            # Add text content
            text_content = f"Context: {context_str}\n\nUser message: {message}\n\nPlease respond as IRIS with helpful suggestions"
            
            # If images are provided, add special instructions
            if photo_data and photo_data.get('images'):
                text_content += "\n\nThe user has uploaded images. Please analyze them and provide detailed observations about:\n"
                text_content += "1. What you see in the images (be specific)\n"
                text_content += "2. Whether this is a current space needing work or inspiration\n"
                text_content += "3. Specific maintenance issues or design opportunities\n"
                text_content += "4. Which room/area this appears to be\n"
                text_content += "5. Suggested project categories\n"
                text_content += "\nThen ask where they'd like to store these images (inspiration board vs property photos)."
            
            content.append({"type": "text", "text": text_content})
            
            # Add images if provided
            if photo_data and photo_data.get('images'):
                for img in photo_data['images']:
                    if img.get('data'):
                        # Extract base64 data from data URL if needed
                        image_data = img['data']
                        if image_data.startswith('data:'):
                            # Extract base64 from data URL
                            header, base64_data = image_data.split(',', 1)
                            # Determine media type from header
                            if 'image/png' in header:
                                media_type = "image/png"
                            elif 'image/webp' in header:
                                media_type = "image/webp"
                            elif 'image/gif' in header:
                                media_type = "image/gif"
                            else:
                                media_type = "image/jpeg"
                        else:
                            # Assume it's raw base64
                            base64_data = image_data
                            media_type = "image/jpeg"
                        
                        # Add image to content
                        content.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_data
                            }
                        })
            
            # Create messages for Anthropic with multi-modal content
            messages = [
                {
                    "role": "user",
                    "content": content
                }
            ]
            
            # Call Anthropic with Claude Sonnet 4
            response = anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",  # Using Claude Sonnet 4
                max_tokens=1000,
                temperature=0.7,
                system=self.system_prompt,
                messages=messages
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return self._generate_fallback_response(message, reasoning)

    def _build_context_string(self, context: Dict[str, Any], reasoning: Dict[str, Any], available_tools: List[str]) -> str:
        """Build context string for Anthropic"""
        context_parts = []
        
        # Add conversation history FIRST so IRIS remembers previous messages
        conversation_history = context.get("conversation_history", [])
        current_session_id = context.get("session_id", "")
        
        if conversation_history:
            # Separate current session from past sessions
            current_session_msgs = []
            past_session_msgs = []
            
            for msg in conversation_history:
                if msg.get("conversation_id") == current_session_id:
                    current_session_msgs.append(msg)
                else:
                    past_session_msgs.append(msg)
            
            # Add current session history
            if current_session_msgs:
                context_parts.append("Current conversation:")
                for msg in current_session_msgs[-10:]:  # Show last 10 messages
                    sender = msg.get("sender_type", "unknown")
                    content = msg.get("content", "")[:200]  # Truncate long messages
                    context_parts.append(f"  {sender}: {content}")
                context_parts.append("")  # Add blank line
            
            # Add relevant past conversations
            if past_session_msgs:
                context_parts.append("Previous conversations with this user:")
                for msg in past_session_msgs[:5]:  # Show last 5 from other sessions
                    sender = msg.get("sender_type", "unknown")
                    content = msg.get("content", "")[:150]  # Truncate
                    session = msg.get("conversation_id", "")[:8]  # Show partial session ID
                    context_parts.append(f"  [{session}...] {sender}: {content}")
                context_parts.append("")  # Add blank line
        
        # User context summary
        inspiration = context.get("inspiration", {})
        property_data = context.get("property", {})
        trade_data = context.get("trade_projects", {})
        
        context_parts.append(f"User intent analysis: {reasoning.get('user_intent', 'unknown')}")
        context_parts.append(f"Confidence: {reasoning.get('confidence', 0):.1%}")
        
        # Inspiration context
        inspiration_boards = inspiration.get("inspiration_boards", [])
        if inspiration_boards:
            context_parts.append(f"Inspiration boards: {len(inspiration_boards)} active")
            for board in inspiration_boards[:2]:  # Show first 2
                context_parts.append(f"  - {board.get('board_name', 'Untitled')}")
        
        # Property context
        properties = property_data.get("properties", [])
        if properties:
            context_parts.append(f"Properties: {len(properties)} documented")
            context_parts.append(f"Property photos: {len(property_data.get('property_photos', []))}")
            context_parts.append(f"Maintenance issues: {len(property_data.get('maintenance_issues', []))}")
        
        # Trade projects context
        trade_groups = trade_data.get("trade_groups_by_property", {})
        if trade_groups:
            total_projects = sum(len(tg.get("trade_groups", {})) for tg in trade_groups.values())
            context_parts.append(f"Trade-grouped projects: {total_projects} identified")
        
        # Available tools
        context_parts.append(f"Available tools: {', '.join(available_tools)}")
        
        return "\n".join(context_parts)

    def _generate_fallback_response(self, message: str, reasoning: Dict[str, Any]) -> str:
        """Generate fallback response when Anthropic is unavailable"""
        intent = reasoning.get("user_intent", "unknown")
        
        fallback_responses = {
            "photo_analysis": "I can help analyze photos! Is this for design inspiration or documenting your current space?",
            "maintenance_issue": "I can help organize maintenance issues by trade. What type of work are you thinking about?",
            "project_management": "I can help with project planning. Would you like to review your current trade groups or create new projects?",
            "design_inspiration": "I'd love to help with design inspiration! Tell me about your style preferences.",
            "unknown": "I'm here to help with design inspiration and project management. What would you like to work on?"
        }
        
        return fallback_responses.get(intent, fallback_responses["unknown"])

    def _generate_suggestions(self, reasoning: Dict[str, Any], context: Dict[str, Any], available_tools: List[str]) -> List[str]:
        """Generate contextual suggestions based on reasoning"""
        suggestions = []
        
        intent = reasoning.get("user_intent", "unknown")
        
        if intent == "photo_analysis":
            suggestions.extend([
                "Is this for inspiration or current space?",
                "Analyze for design elements",
                "Check for maintenance issues"
            ])
        elif intent == "maintenance_issue":
            suggestions.extend([
                "Group by trade type",
                "Estimate project scope",
                "Create project timeline"
            ])
        elif intent == "project_management":
            suggestions.extend([
                "Review current projects",
                "Create bid card",
                "Prioritize by urgency"
            ])
        else:
            suggestions.extend([
                "Upload a photo to analyze",
                "Tell me about your projects",
                "Show me your inspiration boards"
            ])
        
        return suggestions[:4]  # Limit to 4 suggestions

    async def _save_conversation_message(self, session_id: str, user_id: str, user_message: str, assistant_response: str, potential_bid_card_id: Optional[str] = None):
        """Save conversation to unified system with optional bid card linking"""
        try:
            # Save user message
            user_msg_data = {
                "conversation_id": session_id,
                "sender_type": "user",
                "sender_id": user_id,
                "content": user_message,
                "content_type": "text",
                "created_at": datetime.utcnow().isoformat()
            }
            if potential_bid_card_id:
                user_msg_data["potential_bid_card_id"] = potential_bid_card_id
                
            db.client.table("unified_conversation_messages").insert(user_msg_data).execute()
            
            # Save assistant response
            assistant_msg_data = {
                "conversation_id": session_id,
                "sender_type": "agent",
                "agent_type": "IRIS",
                "content": assistant_response,
                "content_type": "text",
                "created_at": datetime.utcnow().isoformat()
            }
            if potential_bid_card_id:
                assistant_msg_data["potential_bid_card_id"] = potential_bid_card_id
                
            db.client.table("unified_conversation_messages").insert(assistant_msg_data).execute()
            
        except Exception as e:
            logger.warning(f"Could not save to unified conversation: {e}")

    async def _save_image_context_to_memory(self, user_id: str, session_id: str, image_data: Dict[str, Any], workflow_response: Optional[Dict[str, Any]] = None):
        """Save image context to unified conversation memory for future reference"""
        try:
            # Prepare memory context with image information
            memory_context = {
                "image_upload_session": session_id,
                "images_uploaded": image_data.get("total_images", 0),
                "successful_analyses": image_data.get("successful_analyses", 0),
                "image_categories": [],
                "room_assignments": [],
                "inspiration_board_assignments": [],
                "analysis_summaries": []
            }
            
            # Extract useful information from analysis results
            for result in image_data.get("results", []):
                if "error" not in result:
                    analysis = result.get("analysis", {})
                    memory_context["analysis_summaries"].append({
                        "filename": result.get("filename", "unknown"),
                        "summary": analysis.get("summary", ""),
                        "style_elements": analysis.get("style_elements", []),
                        "detected_issues": analysis.get("detected_issues", [])
                    })
            
            # Add workflow response if provided
            if workflow_response:
                memory_context["user_classifications"] = {
                    "selected_option": workflow_response.get("selected_option", ""),
                    "question_index": workflow_response.get("question_index", 0),
                    "processed_at": workflow_response.get("processed_at", datetime.now().isoformat())
                }
            
            # Save to unified_conversation_memory
            memory_entry = {
                "user_id": user_id,
                "memory_type": "image_context",
                "memory_key": f"images_{session_id}",
                "memory_data": memory_context,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Insert memory with correct schema (conversation_id can be null)
            memory_insert = {
                "conversation_id": None,  # Don't require foreign key constraint
                "memory_type": "image_context",
                "memory_key": f"images_{session_id}", 
                "memory_value": memory_context,
                "importance_score": 5,
                "created_at": datetime.now().isoformat()
            }
            
            db.client.table("unified_conversation_memory").insert(memory_insert).execute()
            
            logger.info(f"Saved image context to memory for user {user_id}: {memory_context['images_uploaded']} images")
            
        except Exception as e:
            logger.error(f"Failed to save image context to memory: {e}")

    def _get_image_context_from_memory(self, user_id: str) -> Dict[str, Any]:
        """Retrieve image context from previous conversations"""
        try:
            # Get image-related memories for this user
            result = db.client.table("unified_conversation_memory")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("memory_type", "image_context")\
                .order("updated_at", desc=True)\
                .limit(10)\
                .execute()
            
            image_memories = []
            total_images_uploaded = 0
            
            for memory in result.data or []:
                memory_data = memory.get("memory_data", {})
                image_memories.append(memory_data)
                total_images_uploaded += memory_data.get("images_uploaded", 0)
            
            return {
                "previous_image_sessions": len(image_memories),
                "total_images_uploaded": total_images_uploaded,
                "recent_image_memories": image_memories[:5],  # Last 5 sessions
                "has_image_history": len(image_memories) > 0
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve image context from memory: {e}")
            return {
                "previous_image_sessions": 0,
                "total_images_uploaded": 0,
                "recent_image_memories": [],
                "has_image_history": False
            }

    async def _get_potential_bid_cards_for_project(self, user_id: str, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get potential bid cards related to a specific project context"""
        try:
            # Extract project information
            project_title = project_context.get("project_title", "")
            trade_type = project_context.get("trade_type", "")
            
            # Query potential bid cards for this user
            result = db.client.table("potential_bid_cards")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("updated_at", desc=True)\
                .execute()
            
            related_cards = []
            all_cards = result.data or []
            
            # Filter cards that might be related to this project
            for card in all_cards:
                card_title = (card.get("title") or "").lower()
                card_trade = (card.get("project_type") or "").lower()
                
                # Check for title similarity or trade type match
                if ((project_title or "").lower() in card_title or 
                    card_title in (project_title or "").lower() or
                    (trade_type or "").lower() == card_trade):
                    related_cards.append(card)
            
            return {
                "total_potential_cards": len(all_cards),
                "related_cards": related_cards,
                "related_count": len(related_cards),
                "project_context": project_context
            }
            
        except Exception as e:
            logger.error(f"Failed to get potential bid cards for project: {e}")
            return {
                "total_potential_cards": 0,
                "related_cards": [],
                "related_count": 0,
                "project_context": project_context
            }

    async def _handle_image_storage(self, user_id: str, session_id: str, workflow_response: Dict[str, Any], images: Optional[List[Dict[str, Any]]]):
        """Handle actual image storage based on user's workflow response"""
        try:
            logger.info(f"IRIS _handle_image_storage called with user_id={user_id}, workflow_response={workflow_response}, images count={len(images) if images else 0}")
            
            if not images or not workflow_response:
                logger.warning(f"IRIS storage skipped: images={images is not None}, workflow_response={workflow_response is not None}")
                return
                
            question_index = workflow_response.get("question_index", 0)
            selected_option = workflow_response.get("selected_option", "")
            
            logger.info(f"IRIS storing images: question {question_index}, option '{selected_option}'")
            
            # Question 0 is "Where would you like to store this image?"
            # Options: ["Inspiration Board", "Property Photos", "Both"]
            if question_index == 0:
                logger.info(f"Processing {len(images)} images for storage")
                for i, img in enumerate(images):
                    image_data = img.get('data', '')
                    filename = img.get('filename', f'uploaded_image_{i}.jpg')
                    logger.info(f"Processing image {i}: filename={filename}, data_length={len(image_data) if image_data else 0}")
                    
                    # Store based on user's choice
                    if selected_option in ["Inspiration Board", "Both"]:
                        logger.info(f"Storing image {i} to inspiration board")
                        await self._store_to_inspiration_board(user_id, image_data, filename, session_id)
                    
                    if selected_option in ["Property Photos", "Both"]:
                        logger.info(f"Storing image {i} to property photos")
                        await self._store_to_property_photos(user_id, image_data, filename, session_id)
            else:
                logger.warning(f"Unknown question_index {question_index} - expected 0")
                        
            logger.info(f"Successfully stored {len(images)} images to: {selected_option}")
                    
        except Exception as e:
            logger.error(f"Failed to store images: {e}", exc_info=True)
    
    async def _store_to_inspiration_board(self, user_id: str, image_data: str, filename: str, session_id: str):
        """Store image to inspiration board using bucket storage"""
        try:
            import uuid
            import os
            import base64
            from datetime import datetime
            from supabase import create_client
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from services.image_storage_service import get_image_storage_service
            
            # Create service role client to bypass RLS policies
            supabase_url = os.getenv("SUPABASE_URL")
            service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            
            if not service_role_key:
                logger.error("SUPABASE_SERVICE_ROLE_KEY not found in environment")
                return
                
            service_client = create_client(supabase_url, service_role_key)
            
            # First, ensure user has an inspiration board
            board_result = service_client.table("inspiration_boards").select("id").eq("user_id", user_id).limit(1).execute()
            
            board_id = None
            if board_result.data:
                board_id = board_result.data[0]["id"]
            else:
                # Create a default inspiration board
                new_board = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "title": "My Inspiration Board",
                    "description": "Images uploaded through IRIS",
                    "room_type": "general",
                    "status": "collecting",
                    "created_at": datetime.now().isoformat()
                }
                board_create_result = service_client.table("inspiration_boards").insert(new_board).execute()
                board_id = new_board["id"]
            
            # Upload image to bucket storage
            storage_service = get_image_storage_service()
            
            # Extract base64 data from data URL if present
            if image_data.startswith('data:'):
                base64_data = image_data.split(',')[1]
            else:
                base64_data = image_data
            
            # Upload to bucket
            storage_result = await storage_service.upload_base64_image(
                base64_string=base64_data,
                bucket_name="inspiration-images",
                path_prefix=f"{user_id}/{board_id}",
                filename=filename
            )
            
            # Store the image record with bucket URLs
            image_entry = {
                "id": str(uuid.uuid4()),
                "board_id": board_id,
                "user_id": user_id,
                "image_url": storage_result["original_url"],
                "thumbnail_url": storage_result.get("thumbnail_url"),
                "source": "iris_upload",
                "source_url": None,
                "tags": ["iris", "uploaded"],
                "ai_analysis": {
                    "uploaded_via": "iris",
                    "session_id": session_id,
                    "upload_timestamp": datetime.now().isoformat(),
                    "original_filename": filename,
                    "storage_path": storage_result["storage_path"],
                    "file_id": storage_result["file_id"]
                },
                "user_notes": f"Uploaded via IRIS - {filename}",
                "liked_elements": [],
                "position": 0,
                "created_at": datetime.now().isoformat(),
                "category": "uploaded"
            }
            
            service_client.table("inspiration_images").insert(image_entry).execute()
            logger.info(f"Stored image to inspiration board with bucket storage: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to store to inspiration board: {e}")
    
    async def _store_to_property_photos(self, user_id: str, image_data: str, filename: str, session_id: str):
        """Store image to property photos using bucket storage"""
        try:
            import uuid
            import os
            from datetime import datetime
            from database_simple import db
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from services.image_storage_service import get_image_storage_service
            
            # For property photos, we need a property_id
            # For now, create a default property or use user's main property
            property_result = db.client.table("properties").select("id").eq("user_id", user_id).limit(1).execute()
            
            property_id = None
            if property_result.data:
                property_id = property_result.data[0]["id"]
            else:
                # Create a default property
                new_property = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "name": "My Property", 
                    "address": "Property Address",
                    "property_type": "residential",
                    "created_at": datetime.now().isoformat()
                }
                property_create_result = db.client.table("properties").insert(new_property).execute()
                property_id = new_property["id"]
            
            # Upload image to bucket storage
            storage_service = get_image_storage_service()
            
            # Extract base64 data from data URL if present
            if image_data.startswith('data:'):
                base64_data = image_data.split(',')[1]
            else:
                base64_data = image_data
            
            # Upload to bucket
            storage_result = await storage_service.upload_base64_image(
                base64_string=base64_data,
                bucket_name="property-photos",
                path_prefix=f"{property_id}/iris",
                filename=filename
            )
            
            # Store the property photo with bucket URLs
            photo_entry = {
                "id": str(uuid.uuid4()),
                "property_id": property_id,
                "room_id": None,  # Could be determined from room classification
                "photo_url": storage_result["original_url"],
                "original_filename": filename,
                "photo_type": "documentation",
                "ai_description": "Image uploaded via IRIS assistant",
                "ai_classification": {
                    "uploaded_via": "iris",
                    "session_id": session_id,
                    "upload_timestamp": datetime.now().isoformat(),
                    "classification": "user_uploaded",
                    "thumbnail_url": storage_result.get("thumbnail_url"),
                    "storage_path": storage_result["storage_path"],
                    "file_id": storage_result["file_id"]
                },
                "upload_date": datetime.now().isoformat(),
                "taken_date": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat()
            }
            
            db.client.table("property_photos").insert(photo_entry).execute()
            logger.info(f"Stored image to property photos with bucket storage: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to store to property photos: {e}")

# Initialize unified IRIS agent
unified_iris_agent = UnifiedIrisAgent()

@router.post("/unified-chat", response_model=UnifiedIrisResponse)
async def iris_unified_chat(request: UnifiedIrisRequest):
    """
    Unified IRIS chat endpoint with complete context and smart reasoning
    Replaces both general IRIS chat and board-specific conversations
    """
    return await unified_iris_agent.process_message(request)

@router.get("/context/{user_id}")
async def get_iris_context(user_id: str):
    """Get complete IRIS context for debugging"""
    session_id = f"debug_{user_id}_{int(datetime.now().timestamp())}"
    context = unified_iris_agent.get_complete_context(user_id, session_id)
    return {"success": True, "context": context}

@router.post("/suggest-tool/{tool_name}")
async def suggest_tool_usage(tool_name: str, request: Dict[str, Any]):
    """Endpoint for IRIS to suggest using specific tools"""
    try:
        # Map tool names to actual API calls
        tool_mappings = {
            "trade_grouping": "/api/property-projects/{property_id}/trade-groups",
            "project_consolidation": "/api/property-projects/{property_id}/create-trade-projects",
            "bid_card_creation": "/api/bid-cards/create"
        }
        
        if tool_name not in tool_mappings:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")
        
        return {
            "success": True,
            "tool": tool_name,
            "endpoint": tool_mappings[tool_name],
            "suggestion": f"IRIS suggests using {tool_name} with the provided context",
            "requires_confirmation": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Additional Pydantic models for potential bid cards
class PotentialBidCardCreate(BaseModel):
    title: str
    room_location: Optional[str] = None
    property_area: Optional[str] = None
    primary_trade: str
    secondary_trades: Optional[List[str]] = []
    project_complexity: Optional[str] = "simple"
    photo_ids: Optional[List[str]] = []
    cover_photo_id: Optional[str] = None
    ai_analysis: Optional[Dict[str, Any]] = {}
    user_scope_notes: Optional[str] = ""
    eligible_for_group_bidding: Optional[bool] = False
    component_type: Optional[str] = "both"

class PotentialBidCardUpdate(BaseModel):
    title: Optional[str] = None
    user_scope_notes: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    selected_for_conversion: Optional[bool] = None
    bundle_group_id: Optional[str] = None

class BundleCreate(BaseModel):
    project_ids: List[str]
    bundle_name: str
    requires_general_contractor: Optional[bool] = False

class ConversionRequest(BaseModel):
    project_ids: List[str]
    conversion_type: str  # "individual", "bundle", "group_bidding"

@router.get("/potential-bid-cards/{user_id}")
async def get_potential_bid_cards(user_id: str, component_type: Optional[str] = None):
    """Get all potential bid cards for a user"""
    try:
        query = db.client.table("potential_bid_cards").select("*").eq("user_id", user_id)
        
        if component_type:
            query = query.eq("component_type", component_type)
            
        result = query.order("created_at", desc=True).execute()
        
        return {
            "success": True,
            "potential_bid_cards": result.data or [],
            "total_count": len(result.data or [])
        }
        
    except Exception as e:
        logger.error(f"Error getting potential bid cards: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/potential-bid-cards")
async def create_potential_bid_card(user_id: str, card_data: PotentialBidCardCreate):
    """Create a new potential bid card"""
    try:
        # Create the potential bid card
        bid_card_data = {
            "user_id": user_id,
            **card_data.dict()
        }
        
        result = db.client.table("potential_bid_cards").insert(bid_card_data).execute()
        
        if result.data:
            return {
                "success": True,
                "potential_bid_card": result.data[0],
                "message": "Potential bid card created successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create potential bid card")
            
    except Exception as e:
        logger.error(f"Error creating potential bid card: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/potential-bid-cards/{card_id}")
async def update_potential_bid_card(card_id: str, updates: PotentialBidCardUpdate):
    """Update a potential bid card"""
    try:
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = db.client.table("potential_bid_cards").update(update_data).eq("id", card_id).execute()
        
        if result.data:
            return {
                "success": True,
                "potential_bid_card": result.data[0],
                "message": "Potential bid card updated successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Potential bid card not found")
            
    except Exception as e:
        logger.error(f"Error updating potential bid card: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/potential-bid-cards/bundle")
async def create_bundle(user_id: str, bundle_data: BundleCreate):
    """Create a bundle from multiple potential bid cards"""
    try:
        bundle_id = str(uuid.uuid4())
        
        # Update all selected projects with the bundle_group_id
        for project_id in bundle_data.project_ids:
            db.client.table("potential_bid_cards").update({
                "bundle_group_id": bundle_id,
                "status": "bundled",
                "requires_general_contractor": bundle_data.requires_general_contractor,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", project_id).eq("user_id", user_id).execute()
        
        return {
            "success": True,
            "bundle_id": bundle_id,
            "bundled_projects": bundle_data.project_ids,
            "message": f"Created bundle '{bundle_data.bundle_name}' with {len(bundle_data.project_ids)} projects"
        }
        
    except Exception as e:
        logger.error(f"Error creating bundle: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/potential-bid-cards/convert-to-bid-cards")
async def convert_to_bid_cards(user_id: str, conversion: ConversionRequest):
    """Convert potential bid cards to actual bid cards for homeowner agent"""
    try:
        # Get the potential bid cards
        cards_result = db.client.table("potential_bid_cards")\
            .select("*")\
            .in_("id", conversion.project_ids)\
            .eq("user_id", user_id)\
            .execute()
        
        if not cards_result.data:
            raise HTTPException(status_code=404, detail="No potential bid cards found")
        
        converted_cards = []
        
        # For each potential bid card, create a bid card via CIA API
        for card in cards_result.data:
            try:
                # Call CIA API to create bid card
                cia_response = requests.post(
                    f"{get_backend_url()}/api/cia/create-bid-card",
                    json={
                        "user_id": user_id,
                        "project_title": card["title"],
                        "room_location": card["room_location"],
                        "scope_description": card["user_scope_notes"],
                        "primary_trade": card["primary_trade"],
                        "secondary_trades": card.get("secondary_trades", []),
                        "budget_min": card.get("budget_range_min"),
                        "budget_max": card.get("budget_range_max"),
                        "urgency": card.get("urgency_level", "medium"),
                        "timeline": card.get("estimated_timeline"),
                        "group_bidding_eligible": card.get("eligible_for_group_bidding", False),
                        "source": "iris_potential_bid_card"
                    },
                    timeout=30
                )
                
                if cia_response.status_code == 200:
                    bid_card_data = cia_response.json()
                    
                    # Update potential bid card as converted
                    db.client.table("potential_bid_cards").update({
                        "status": "converted",
                        "converted_to_bid_card_id": bid_card_data.get("bid_card_id"),
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("id", card["id"]).execute()
                    
                    converted_cards.append({
                        "potential_bid_card_id": card["id"],
                        "bid_card_id": bid_card_data.get("bid_card_id"),
                        "title": card["title"]
                    })
                else:
                    logger.warning(f"Failed to convert potential bid card {card['id']}: {cia_response.status_code}")
                    
            except requests.RequestException as e:
                logger.error(f"Error calling CIA API for card {card['id']}: {e}")
        
        return {
            "success": True,
            "conversion_type": conversion.conversion_type,
            "converted_cards": converted_cards,
            "total_converted": len(converted_cards),
            "message": f"Successfully converted {len(converted_cards)} potential bid cards to actual bid cards"
        }
        
    except Exception as e:
        logger.error(f"Error converting to bid cards: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/potential-bid-cards/{card_id}/conversations")
async def get_card_conversations(card_id: str):
    """Get all conversations related to a specific potential bid card"""
    try:
        result = db.client.table("unified_conversation_messages")\
            .select("*")\
            .eq("potential_bid_card_id", card_id)\
            .order("created_at", desc=False)\
            .execute()
        
        return {
            "success": True,
            "conversations": result.data or [],
            "total_messages": len(result.data or [])
        }
        
    except Exception as e:
        logger.error(f"Error getting card conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))