"""
Clean CIA Agent - Using OpenAI tool calling with real-time bid card updates
"""
import json
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Use the actual unified memory system like other agents!
from database_simple import db
from agents.cia.potential_bid_card_integration import PotentialBidCardManager
from agents.cia.schemas import BidCardUpdate
from agents.cia.store import CIAStore

# Import categorization tool integration
from agents.project_categorization.cia_integration import (
    get_categorization_tool,
    handle_categorization_tool_call,
    get_categorization_response
)
from agents.project_categorization.tool_definition import CATEGORIZATION_SYSTEM_PROMPT

load_dotenv()
logger = logging.getLogger(__name__)


class CustomerInterfaceAgent:
    """Clean CIA implementation with real-time bid card updates"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        bid_card_manager: Optional[PotentialBidCardManager] = None,
    ):
        """Initialize with OpenAI and existing systems"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key)

        # KEEP THESE - They work!
        self.db = db  # Use same database instance as other agents
        self.bid_cards = bid_card_manager or PotentialBidCardManager()  # This updates the UI!
        self.store = CIAStore()
        
        # Define BOTH tools - extraction AND categorization
        self.tools = [
            # Tool 1: Field extraction tool - 18 PRIORITY FIELDS for photo-oriented conversations
            {
                "type": "function",
                "function": {
                    "name": "update_bid_card",
                    "description": "Update bid card with extracted project information from photo-oriented conversations. Use intelligent deduction from natural conversation flow rather than hard-coded trigger words.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            # REQUIRED FIELDS FOR CONVERSION (5 fields)
                            "title": {"type": "string", "description": "Project title/name (REQUIRED for conversion) - Short descriptive name like 'Kitchen Remodel' or 'Fence Installation'"},
                            "description": {"type": "string", "description": "Detailed project description (REQUIRED) - What work needs to be done and current situation"},
                            "location_zip": {"type": "string", "description": "5-digit ZIP code (REQUIRED for contractor matching)"},
                            "urgency_level": {
                                "type": "string",
                                "enum": ["emergency", "urgent", "week", "month", "flexible"],
                                "description": "Timeline urgency level (REQUIRED) - Use bid_cards schema: emergency, urgent, week, month, flexible"
                            },
                            "contractor_count_needed": {"type": "integer", "description": "How many bids they want (REQUIRED for outreach planning) - typically 3-5"},
                            
                            # LOCATION FIELDS (3 fields)
                            "location_city": {"type": "string", "description": "City name for contractor matching"},
                            "location_state": {"type": "string", "description": "State code (CA, NY, TX, etc.) for contractor matching"},
                            "room_location": {"type": "string", "description": "Which room/area of property (kitchen, bathroom, backyard, etc.)"},
                            
                            # BUDGET & VALUE FIELDS (3 fields)
                            "budget_min": {"type": "number", "description": "Minimum budget if mentioned in conversation"},
                            "budget_max": {"type": "number", "description": "Maximum budget if mentioned in conversation"},
                            "budget_context": {"type": "string", "description": "Budget stage: 'just exploring' vs 'ready to hire' - extracted for backend, not shown in UI"},
                            
                            # PROJECT CLASSIFICATION FIELDS (4 fields)
                            "project_type": {"type": "string", "description": "Main project type (e.g., 'Bathroom Remodel', 'Fence Installation') - will be used by Tool 2 for categorization"},
                            "service_type": {
                                "type": "string", 
                                "description": "Service category - should intelligently match one of 14 backend service_categories options (kitchen, bathroom, landscaping, roofing, etc.)"
                            },
                            "estimated_timeline": {"type": "string", "description": "When project should be completed ('2 weeks', 'next month', 'by summer', etc.)"},
                            "contractor_size_preference": {
                                "type": "string",
                                "enum": ["solo_handyman", "owner_operator", "small_business", "regional_company", "national_chain"],
                                "description": "Preferred contractor size - 5 options matching bid_cards schema. Deduce from conversation cues about budget, project size, insurance needs"
                            },
                            
                            # PROJECT REQUIREMENTS FIELDS (2 fields)
                            "materials_specified": {"type": "array", "items": {"type": "string"}, "description": "Array of specific material preferences mentioned (granite, tile, sod, etc.)"},
                            "special_requirements": {"type": "array", "items": {"type": "string"}, "description": "Array of special requirements (permits, HOA approval, access issues, etc.)"},
                            
                            # COMMUNICATION FIELDS (1 field) - Group bidding focus
                            "eligible_for_group_bidding": {"type": "boolean", "description": "Suitable for neighbor bulk pricing - deduce from timeline flexibility and project type"}
                        }
                    }
                }
            },
            # Tool 2: Project categorization tool (CRITICAL FOR CONTRACTOR MATCHING!)
            get_categorization_tool()
        ]
    
    async def handle_conversation(
        self,
        user_id: Optional[str],  # Can be None for landing profile
        message: str,
        session_id: str,
        profile: str = "landing",  # NEW: Profile parameter
        conversation_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main conversation handler with real-time bid card updates
        THIS IS WHAT CONNECTS TO YOUR UI!
        """
        bid_card_error: Optional[str] = None
        bid_card_id: Optional[str] = None
        try:
            logger.info(f"CIA handling conversation with profile: {profile}")
            
            # 1. PROFILE-BASED MEMORY LOADING
            context = {}
            if profile == "app" and user_id:
                # APP PROFILE: Load full user context
                context = await self.store.get_user_context(user_id)
                logger.info(f"App profile - loaded user context for {user_id}")
            elif profile == "landing":
                # LANDING PROFILE: Skip context loading for speed
                logger.info("Landing profile - skipping user context loading")
            
            # 2. Generate conversation_id (ensure it's a valid UUID)
            if not conversation_id:
                import uuid
                # Create a deterministic UUID from the session_id
                conversation_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"cia_{session_id}"))
            
            # 3. Get or create potential bid card (THIS IS CRITICAL FOR UI!)
            try:
                bid_card_id = await self.bid_cards.create_potential_bid_card(
                    conversation_id=conversation_id,
                    session_id=session_id,
                    user_id=user_id
                )
                if bid_card_id:
                    logger.info(f"Created potential bid card: {bid_card_id}")
                else:
                    logger.error("Failed to create potential bid card!")
                    bid_card_error = "failed_to_create"
            except Exception as e:
                logger.error(f"Error creating bid card: {e}")
                bid_card_error = str(e)
            
            # 4. HISTORY LOADING FOR BOTH PROFILES
            previous_messages = []
            conversation_state = await self.db.load_conversation_state(session_id)
            if conversation_state and conversation_state.get("messages"):
                previous_messages = conversation_state["messages"]
                logger.info(f"{profile} profile - loaded {len(previous_messages)} previous messages")
            else:
                logger.info(f"{profile} profile - no previous conversation found")
            
            # 5. Build conversation history for OpenAI (now includes previous messages!)
            messages = self._build_messages(context, message, previous_messages, profile)
            
            # 6. PROFILE-BASED TOOL FILTERING - RE-ENABLED FOR FIELD EXTRACTION
            if profile == "landing":
                # LANDING PROFILE: Enable field extraction tools
                available_tools = self.tools  # Re-enabled for field extraction
                logger.info("Landing profile - tools enabled for field extraction")
            else:
                # APP PROFILE: Enable full tools
                available_tools = self.tools  # Re-enabled for field extraction
                logger.info(f"App profile - tools enabled for field extraction")
            
            # 7. Call OpenAI with profile-filtered tools - RE-ENABLED
            logger.info(f"Calling OpenAI GPT-4o with {len(available_tools)} tools for field extraction")
            logger.info(f"Tool names available: {[tool['function']['name'] for tool in available_tools]}")
            logger.info(f"First 200 chars of user message: {message[:200]}")
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=available_tools,  # Re-enabled for field extraction
                tool_choice="auto",  # Re-enabled for field extraction
                temperature=0.7,  # Increased for more natural responses
                max_tokens=500
            )
            
            # 8. Process tool calls - RE-ENABLED FOR FIELD EXTRACTION
            extracted_data = {}
            categorization_response = None
            categorization_result = None  # Store categorization result for return
            tool_calls_made = []  # Track all tool calls for streaming
            
            # Log the response details
            logger.info(f"OpenAI response received. Has tool calls: {response.choices[0].message.tool_calls is not None}")
            if response.choices[0].message.tool_calls:
                logger.info(f"Number of tool calls: {len(response.choices[0].message.tool_calls)}")
            
            # Tool processing re-enabled for field extraction
            if response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    # Track this tool call for streaming
                    tool_calls_made.append({
                        "tool_name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments)
                    })
                    
                    if tool_call.function.name == "update_bid_card":
                        extracted_data = json.loads(tool_call.function.arguments)
                        logger.info(f"Extracted data: {extracted_data}")
                        
                        # DIRECT DATABASE UPDATE - Bypass BidCardUpdate schema and update database directly
                        if bid_card_id:
                            # Direct field mapping for all 17 extracted fields to 84-field schema
                            field_updates = {}
                            
                            # REQUIRED FIELDS (5 fields)
                            if extracted_data.get('title'):
                                field_updates['title'] = extracted_data['title']
                            if extracted_data.get('description'):
                                field_updates['description'] = extracted_data['description']
                            if extracted_data.get('location_zip'):
                                field_updates['location_zip'] = extracted_data['location_zip']
                            if extracted_data.get('urgency_level'):
                                field_updates['urgency_level'] = extracted_data['urgency_level']
                            if extracted_data.get('contractor_count_needed'):
                                field_updates['contractor_count_needed'] = extracted_data['contractor_count_needed']
                            
                            # LOCATION FIELDS (3 fields)
                            if extracted_data.get('location_city'):
                                field_updates['location_city'] = extracted_data['location_city']
                            if extracted_data.get('location_state'):
                                field_updates['location_state'] = extracted_data['location_state']
                            if extracted_data.get('room_location'):
                                field_updates['room_location'] = extracted_data['room_location']
                                
                            # BUDGET & VALUE FIELDS (3 fields)
                            if extracted_data.get('budget_min'):
                                field_updates['budget_min'] = extracted_data['budget_min']
                            if extracted_data.get('budget_max'):
                                field_updates['budget_max'] = extracted_data['budget_max']
                            if extracted_data.get('budget_context'):
                                field_updates['budget_context'] = extracted_data['budget_context']
                                
                            # PROJECT CLASSIFICATION FIELDS (3 fields)
                            if extracted_data.get('service_type'):
                                field_updates['service_type'] = {"category": extracted_data['service_type']}  # JSONB format
                            if extracted_data.get('estimated_timeline'):
                                field_updates['estimated_timeline'] = extracted_data['estimated_timeline']
                            if extracted_data.get('contractor_size_preference'):
                                field_updates['contractor_size_preference'] = extracted_data['contractor_size_preference']
                                
                            # PROJECT REQUIREMENTS FIELDS (2 fields) - Handle JSONB arrays
                            if extracted_data.get('materials_specified'):
                                materials = extracted_data['materials_specified']
                                if isinstance(materials, list):
                                    field_updates['materials_specified'] = materials
                                elif isinstance(materials, str):
                                    field_updates['materials_specified'] = [item.strip() for item in materials.split(',') if item.strip()]
                                    
                            if extracted_data.get('special_requirements'):
                                requirements = extracted_data['special_requirements']
                                if isinstance(requirements, list):
                                    field_updates['special_requirements'] = requirements  
                                elif isinstance(requirements, str):
                                    field_updates['special_requirements'] = [item.strip() for item in requirements.split(',') if item.strip()]
                                    
                            # COMMUNICATION FIELDS (1 field)
                            if extracted_data.get('eligible_for_group_bidding') is not None:
                                field_updates['eligible_for_group_bidding'] = extracted_data['eligible_for_group_bidding']
                            
                            # Update all extracted fields directly in database
                            for field_name, field_value in field_updates.items():
                                success = await self.bid_cards.update_bid_card_field(
                                    bid_card_id=bid_card_id,
                                    field_name=field_name,
                                    field_value=field_value,
                                    confidence=0.9
                                )
                                if success:
                                    logger.info(f"✅ Updated {field_name}: {field_value}")
                                else:
                                    logger.error(f"❌ Failed to update {field_name}")
                                    
                            logger.info(f"🎯 Updated {len(field_updates)} fields from 17-field extraction")
                        
                        # FORCE CATEGORIZATION after update_bid_card
                        if bid_card_id and extracted_data.get('description'):
                            logger.info("Auto-triggering categorization after update_bid_card")
                            try:
                                categorization_args = {
                                    'description': extracted_data['description'],
                                    'bid_card_id': bid_card_id,
                                    'context': f"urgency: {extracted_data.get('urgency_level', 'normal')} service: {extracted_data.get('service_type', 'general')}"
                                }
                                
                                categorization_result = await handle_categorization_tool_call(
                                    tool_call_args=categorization_args,
                                    bid_card_id=bid_card_id
                                )
                                
                                categorization_response = get_categorization_response(categorization_result)
                                logger.info(f"Auto-categorization result: {categorization_result}")
                                logger.info(f"Auto-categorization response: {categorization_response}")
                                
                            except Exception as e:
                                logger.error(f"Auto-categorization failed: {e}")
                    
                    elif tool_call.function.name == "categorize_project":
                        logger.info("Processing categorization tool call")
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        # Track this tool call for streaming
                        tool_calls_made.append({
                            "tool_name": tool_call.function.name,
                            "arguments": tool_args
                        })
                        
                        if bid_card_id:
                            # Handle categorization tool call
                            categorization_result = await handle_categorization_tool_call(
                                tool_call_args=tool_args,
                                bid_card_id=bid_card_id
                            )
                            
                            # Get natural language response for conversation
                            categorization_response = get_categorization_response(categorization_result)
                            logger.info(f"Categorization result: {categorization_result}")
                            logger.info(f"Categorization response: {categorization_response}")
                        else:
                            logger.warning("Categorization tool called but no bid_card_id available")
            
            # 8. Get the response text from GPT-4o
            response_text = response.choices[0].message.content
            
            # If GPT-4o didn't provide content (happens with tool calls), 
            # make a second call to get a conversational response
            if not response_text and (extracted_data or categorization_response):
                logger.info("GPT-4o made tool calls without content - making follow-up call for conversation")
                
                # Build context about what was just extracted
                context_msg = "I've extracted the following information from the user:\n"
                if extracted_data:
                    for key, value in extracted_data.items():
                        if value:
                            context_msg += f"- {key}: {value}\n"
                
                # Add message to conversation asking for response
                follow_up_messages = messages + [
                    {"role": "assistant", "content": context_msg},
                    {"role": "system", "content": "Based on what you've learned, provide a warm, intelligent response to the user. Acknowledge what they told you, and ask relevant follow-up questions if needed. Be conversational and helpful as Alex."}
                ]
                
                # Make follow-up call WITHOUT tools to get pure conversation
                follow_up_response = await self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=follow_up_messages,
                    temperature=0.7,
                    max_tokens=300
                )
                
                response_text = follow_up_response.choices[0].message.content
                if not response_text:
                    response_text = "I've updated your project details. Let me continue gathering information."
            
            # If we have both regular response and categorization, combine them
            elif categorization_response:
                response_text = response_text + " " + categorization_response
            
            # 9. Get updated bid card status for UI
            bid_card_status = None
            completion_percentage = 0
            if bid_card_id:
                bid_card_status = await self.bid_cards.get_bid_card_status(bid_card_id)
                if bid_card_status:
                    # Calculate completion based on filled fields
                    completion_percentage = bid_card_status.get("completion_percentage", 0)
                    logger.info(f"Bid card completion: {completion_percentage}%")
            
            # 10. Save conversation state to unified memory system (CRITICAL FOR PERSISTENCE!)
            # Build complete conversation state with current turn
            conversation_messages = previous_messages + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": response_text}
            ]
            
            # Save conversation state using the same mechanism that load_conversation_state uses
            conversation_state = {
                "messages": conversation_messages,
                "extracted_data": extracted_data,
                "bid_card_id": bid_card_id,
                "agent_type": "CIA",
                "profile": profile,
                "user_id": user_id
            }
            
            await self.db.save_conversation_state(
                user_id=user_id or "anonymous",
                thread_id=session_id,
                agent_type="CIA",
                state=conversation_state
            )
            
            # 12. Return response with bid card info for UI
            return {
                "response": response_text,
                "success": True,
                "session_id": session_id,
                "conversation_id": conversation_id,
                "bid_card_id": bid_card_id,  # UI needs this!
                "bid_card_created": bool(bid_card_id),
                "bid_card_error": bid_card_error,
                "extracted_data": extracted_data,  # What we just extracted
                "tool_calls": tool_calls_made,  # All tool calls made (for streaming)
                "completion_percentage": completion_percentage,  # UI progress bar!
                "bid_card_status": bid_card_status,  # Full bid card state
                "categorization_result": categorization_result,  # Project categorization result
                "fields_extracted": len([v for v in extracted_data.values() if v]),
                "profile_used": profile,  # Which profile was used
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in CIA conversation: {str(e)}", exc_info=True)
            return {
                "response": "I'm having trouble processing that. Could you please try again?",
                "success": False,
                "error": str(e),
                "session_id": session_id,
                "bid_card_id": bid_card_id,
                "bid_card_created": bool(bid_card_id),
                "bid_card_error": bid_card_error
            }
    
    def _extract_context_from_history(self, previous_messages: List[Dict]) -> Dict[str, Any]:
        """Extract key information from conversation history to prevent redundant questions"""
        logger.info(f"🔍 EXTRACTING CONTEXT from {len(previous_messages)} previous messages")
        
        extracted_context = {
            "zip_code": None,
            "location": None,
            "project_type": None,
            "budget_min": None,
            "budget_max": None,
            "timeline": None,
            "urgency": None,
            "scope_details": None,
            "materials": None,
            "property_type": None
        }
        
        if not previous_messages:
            logger.info("No previous messages to extract context from")
            return extracted_context
            
        # Scan all previous messages for key information
        for msg in previous_messages:
            if msg.get("role") == "user":
                content = msg.get("content", "").lower()
                
                # Extract zip code (5 digit pattern)
                import re
                zip_match = re.search(r'\b(\d{5})\b', msg.get("content", ""))
                if zip_match:
                    extracted_context["zip_code"] = zip_match.group(1)
                    logger.info(f"📍 EXTRACTED ZIP CODE: {zip_match.group(1)}")
                
                # Extract location mentions
                for city in ["beverly hills", "los angeles", "malibu", "santa monica"]:
                    if city in content:
                        extracted_context["location"] = city.title()
                
                # Extract project type
                for project in ["kitchen", "bathroom", "roof", "lawn", "plumbing", "electrical"]:
                    if project in content:
                        extracted_context["project_type"] = project
                
                # Extract budget mentions
                budget_match = re.search(r'\$?([\d,]+)(?:k|,000)?', msg.get("content", ""))
                if budget_match and ("budget" in content or "spend" in content or "cost" in content):
                    amount = budget_match.group(1).replace(",", "")
                    if amount and amount.isdigit():  # Check if amount is valid
                        if "k" in msg.get("content", "").lower():
                            amount = str(int(amount) * 1000)
                        extracted_context["budget_max"] = amount
                
                # Extract urgency
                for urgency in ["emergency", "urgent", "asap", "immediately", "leak", "damage"]:
                    if urgency in content:
                        extracted_context["urgency"] = "urgent" if urgency != "emergency" else "emergency"
        
        # Log what was extracted
        non_null_items = {k: v for k, v in extracted_context.items() if v is not None}
        if non_null_items:
            logger.info(f"🎯 EXTRACTED ITEMS: {non_null_items}")
        else:
            logger.info("🔍 No context items extracted")
        
        return extracted_context
    
    def _build_messages(
        self, 
        context: Dict,
        current_message: str,
        previous_messages: List[Dict] = None,
        profile: str = "landing"  # NEW: Profile parameter
    ) -> List[Dict]:
        """Build message history for OpenAI including previous conversation context"""
        
        # Extract key information from history to inject into prompt
        extracted_info = self._extract_context_from_history(previous_messages)
        
        # System prompt with profile-specific additions
        system_prompt = self._get_system_prompt(context, profile)
        
        # Add extracted context summary to system prompt
        logger.info(f"🔍 CONTEXT CHECK: any(extracted_info.values()) = {any(extracted_info.values())}")
        if any(extracted_info.values()):
            logger.info(f"💡 CONTEXT INJECTION: Adding context summary to system prompt")
            context_summary = "\n\n## INFORMATION ALREADY PROVIDED BY USER:\n"
            if extracted_info["zip_code"]:
                context_summary += f"- Zip Code: {extracted_info['zip_code']}\n"
            if extracted_info["location"]:
                context_summary += f"- Location: {extracted_info['location']}\n"
            if extracted_info["project_type"]:
                context_summary += f"- Project Type: {extracted_info['project_type']}\n"
            if extracted_info["budget_max"]:
                context_summary += f"- Budget: ${extracted_info['budget_max']}\n"
            if extracted_info["urgency"]:
                context_summary += f"- Urgency: {extracted_info['urgency']}\n"
            context_summary += "\n⚠️ DO NOT ASK FOR ANY OF THE ABOVE INFORMATION AGAIN!\n"
            
            system_prompt += context_summary
            logger.info(f"Injected extracted context into system prompt: {extracted_info}")
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add previous conversation history for continuity
        if previous_messages:
            # Limit to last 10 messages to avoid token limits
            recent_messages = previous_messages[-10:] if len(previous_messages) > 10 else previous_messages
            messages.extend(recent_messages)
            logger.info(f"Added {len(recent_messages)} previous messages to context")
        
        # Add current user message
        messages.append({"role": "user", "content": current_message})
        
        return messages
    
    def _get_system_prompt(self, context: Dict, profile: str = "landing") -> str:
        """Generate system prompt with complete business logic and profile-specific instructions"""
        
        # Import the unified prompt
        from agents.cia.UNIFIED_PROMPT_FINAL import get_unified_prompt
        
        # Get the base unified prompt (has ALL business logic + tool instructions)
        base_prompt = get_unified_prompt()
        
        # CRITICAL: Tell GPT-4o to ALWAYS provide conversational content
        base_prompt += "\n\n## CRITICAL RESPONSE REQUIREMENT:\n"
        base_prompt += "You MUST ALWAYS provide a conversational response to the user, even when calling tools.\n"
        base_prompt += "- When extracting data with tools, still respond naturally to what they said\n"
        base_prompt += "- Acknowledge their information: 'I understand your toilet is leaking...'\n"
        base_prompt += "- Reference context from the conversation\n"
        base_prompt += "- Ask intelligent follow-up questions based on what's missing\n"
        base_prompt += "- NEVER return empty content when calling tools\n"
        base_prompt += "- BE ALEX - warm, intelligent, and helpful\n"
        
        # Add categorization tool instructions
        base_prompt += "\n\n" + CATEGORIZATION_SYSTEM_PROMPT
        
        # Add profile-specific instructions
        profile_additions = []
        
        if profile == "landing":
            profile_additions.append("## LANDING PROFILE INSTRUCTIONS:")
            profile_additions.append("- You are helping an ANONYMOUS user who hasn't created an account yet")
            profile_additions.append("- Focus on capturing project details quickly and efficiently")
            profile_additions.append("- Do NOT reference any previous projects or history")
            profile_additions.append("- Encourage account creation to save their project")
            profile_additions.append("- Keep conversations focused on their immediate project need")
            profile_additions.append("- Only use the update_bid_card tool for extraction")
        
        elif profile == "app":
            profile_additions.append("## APP PROFILE INSTRUCTIONS:")
            profile_additions.append("- This user is LOGGED IN with full account access")
            profile_additions.append("- You have access to their complete project history and preferences")
            profile_additions.append("- Reference previous projects when relevant")
            profile_additions.append("- You can ask questions like 'Is this for your kitchen project?'")
            profile_additions.append("- You have access to all tools including bid card management, RFI, and IRIS")
            profile_additions.append("- Provide rich, contextual responses based on their history")
            profile_additions.append("")
            profile_additions.append("## CRITICAL CONTEXT AWARENESS (APP PROFILE ONLY):")
            profile_additions.append("⚠️ MANDATORY: Before asking ANY question, MUST check conversation history above for the answer.")
            profile_additions.append("- NEVER ask for information that has already been provided")
            profile_additions.append("- ALWAYS reference information from previous messages when relevant")
            profile_additions.append("- If user provided zip code, location, budget, project type, or ANY detail earlier, DO NOT ask again")
            profile_additions.append("- Instead of asking 'What's your zip code?', say 'Based on your location in [zip/city from history]...'")
            profile_additions.append("- Build upon previous context: 'For your kitchen remodel in Beverly Hills 90210 with $50,000 budget...'")
            profile_additions.append("")
            profile_additions.append("CONTEXT CHECK REQUIRED:")
            profile_additions.append("1. Before asking about location → Check if zip code/city was mentioned")
            profile_additions.append("2. Before asking about project → Check if project type was specified")
            profile_additions.append("3. Before asking about budget → Check if budget was discussed")
            profile_additions.append("4. Before asking about timeline → Check if timeline was mentioned")
            profile_additions.append("5. Before asking about urgency → Check if urgency was stated")
            profile_additions.append("")
            profile_additions.append("If ongoing conversation, acknowledge context: 'I see you're working on [project] in [location]...')")
        
        # Add returning user context for app profile only
        if profile == "app" and not context.get("new_user"):
            profile_additions.append("- This is a returning user - be warm and reference previous conversations")
        
        # Add profile additions to prompt
        if profile_additions:
            base_prompt += "\n\n" + "\n".join(profile_additions)
        
        return base_prompt
    
    def _generate_follow_up_response(self, extracted_data: Dict[str, Any], profile: str = "landing") -> str:
        """Generate conversational response based on extracted data and profile"""
        
        # Build response based on what was extracted
        response_parts = []
        
        # Acknowledge what we learned
        if extracted_data.get("project_type"):
            project_type = extracted_data["project_type"]
            response_parts.append(f"Got it! I understand you need help with a {project_type} project.")
        
        # Address urgency if mentioned
        if extracted_data.get("urgency"):
            urgency = extracted_data["urgency"]
            if urgency == "emergency":
                response_parts.append("I see this is an emergency situation. I'll prioritize finding contractors who can respond quickly.")
            elif urgency == "urgent":
                response_parts.append("Since this is urgent, I'll focus on contractors who can start soon.")
            elif urgency == "flexible":
                response_parts.append("It's great that you have flexibility with timing - this gives us more options.")
        
        # Ask follow-up questions based on what's missing
        follow_up_questions = []
        
        # Location is critical for contractor matching
        if not extracted_data.get("zip_code") and not extracted_data.get("location"):
            follow_up_questions.append("What's your zip code or general location?")
        
        # Project scope details help with accurate bids
        if not extracted_data.get("scope_details"):
            if extracted_data.get("project_type"):
                project_type = extracted_data["project_type"]
                if "kitchen" in project_type.lower():
                    follow_up_questions.append("Can you tell me more about what you want to update in your kitchen?")
                elif "bathroom" in project_type.lower():
                    follow_up_questions.append("What specific bathroom improvements are you looking for?")
                elif "lawn" in project_type.lower() or "landscaping" in project_type.lower():
                    follow_up_questions.append("What size area are we talking about, and what type of work do you need?")
                elif "roof" in project_type.lower():
                    follow_up_questions.append("Is this for repairs, replacement, or something else?")
                else:
                    follow_up_questions.append("Can you describe what specific work needs to be done?")
        
        # Timeline helps with contractor scheduling
        if not extracted_data.get("timeline") and extracted_data.get("urgency") != "emergency":
            follow_up_questions.append("When would you ideally like this project completed?")
        
        # Property type affects project complexity
        if not extracted_data.get("property_type"):
            follow_up_questions.append("Is this for a house, condo, or commercial property?")
        
        # Combine response parts
        if response_parts:
            response = " ".join(response_parts)
        else:
            response = "I'm gathering details about your project."
        
        # Add follow-up questions
        if follow_up_questions:
            if len(follow_up_questions) == 1:
                response += f" {follow_up_questions[0]}"
            else:
                # Ask the most important question first
                response += f" {follow_up_questions[0]}"
        
        # Profile-specific additions
        if profile == "landing":
            # Encourage engagement for anonymous users
            if not follow_up_questions:
                response += " I'm building your project details so we can connect you with the right contractors."
        elif profile == "app":
            # More personalized for logged-in users
            if not follow_up_questions:
                response += " I'm updating your project profile with this information."
        
        return response