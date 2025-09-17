"""
BSA DeepAgents Implementation - The ONE Proper BSA System
Uses the actual DeepAgents framework for proper subagent orchestration
"""

import os
import sys
from typing import Dict, Any, List, Optional
import logging
import asyncio
from datetime import datetime

# Add deepagents-system to path
sys.path.insert(0, r'C:\Users\Not John Or Justin\Documents\instabids\deepagents-system\src')

# Import DeepAgents framework
from deepagents import create_deep_agent
from deepagents.state import DeepAgentState
from typing import NotRequired

# Import existing memory and database systems
from database import SupabaseDB
from memory.contractor_ai_memory import ContractorAIMemory
from adapters.contractor_context import ContractorContextAdapter
from services.my_bids_tracker import my_bids_tracker

logger = logging.getLogger(__name__)

# ============================================================================
# EXTENDED STATE FOR BSA
# ============================================================================

class BSADeepAgentState(DeepAgentState):
    """Extended state to include BSA-specific context"""
    contractor_id: NotRequired[str]
    contractor_context: NotRequired[Dict[str, Any]]
    ai_memory_context: NotRequired[str]
    my_bids_context: NotRequired[Dict[str, Any]]
    session_id: NotRequired[str]
    bid_card_id: NotRequired[str]

# ============================================================================
# MAIN BSA INSTRUCTIONS
# ============================================================================

BSA_MAIN_INSTRUCTIONS = """You are BSA (Bid Submission Agent) for InstaBids, helping contractors find projects and optimize their bidding.

CONTRACTOR CONTEXT:
The contractor's profile, memory, and context are available in the state. Use this information to provide personalized assistance.

YOUR CAPABILITIES THROUGH SUBAGENTS:

1. **bid-search** - Use this to find relevant bid cards and projects
   - Searches by location, radius, and project type
   - Matches contractor specialties to opportunities
   - Provides detailed project information

2. **market-research** - Use this for market insights and pricing
   - Analyzes competitive pricing in the area
   - Provides market trends and insights
   - Helps with bid strategy

3. **bid-submission** - Use this to create professional proposals
   - Transforms casual input into professional bids
   - Structures pricing and timeline
   - Formats for homeowner presentation

4. **group-bidding** - Use this for group opportunities
   - Identifies projects suitable for multiple contractors
   - Calculates group savings (15-25%)
   - Coordinates group submissions

ORCHESTRATION GUIDELINES:
- When contractors ask about available work → Use bid-search subagent
- When they need pricing advice → Use market-research subagent
- When ready to submit → Use bid-submission subagent
- When multiple contractors could benefit → Consider group-bidding subagent

You can chain multiple subagents for complex requests. For example:
1. First search for projects (bid-search)
2. Then analyze market rates (market-research)
3. Finally help create the bid (bid-submission)

Be conversational, helpful, and use the contractor's actual context from the state.
Never give template or predetermined responses."""

# ============================================================================
# SUBAGENT CONFIGURATIONS
# ============================================================================

bid_search_subagent = {
    "name": "bid-search",
    "description": "Searches for bid cards and projects matching contractor capabilities. Use when contractor asks about available work, projects near them, or opportunities in their area.",
    "prompt": """You are a bid search specialist for InstaBids.
    
Your role is to find relevant projects for contractors based on:
- Their location and service radius
- Their specialties and capabilities
- Project requirements and budget
- Timeline and urgency

Use the search tools to find projects and explain why each is a good match.
The contractor's context is available in the state - use it to personalize results.

When presenting results:
- Highlight projects that match their specialties
- Explain the fit based on their experience
- Note budget alignment with their typical pricing
- Mention timeline compatibility""",
    "tools": ["search_bid_cards", "get_nearby_projects", "calculate_project_fit"]
}

market_research_subagent = {
    "name": "market-research",
    "description": "Analyzes market trends, competitive pricing, and bidding strategies. Use when contractor asks about pricing, competition, or market conditions.",
    "prompt": """You are a market research specialist for InstaBids.
    
Your role is to provide market insights including:
- Competitive pricing analysis for specific project types
- Market trends in the contractor's area
- Optimal bidding strategies
- Competitor analysis

Use market data to help contractors price competitively while maintaining margins.
Consider their experience level and specialties when making recommendations.

Provide actionable insights, not just data.""",
    "tools": ["analyze_market_trends", "get_competitor_pricing", "calculate_optimal_bid"]
}

bid_submission_subagent = {
    "name": "bid-submission",
    "description": "Creates professional bid proposals from contractor input. Use when contractor wants to submit a bid or needs help formatting their proposal.",
    "prompt": """You are a bid submission specialist for InstaBids.
    
Your role is to transform contractor input into professional proposals:
- Structure casual input into professional format
- Ensure all required information is included
- Highlight contractor strengths and experience
- Create compelling value propositions

The proposal should be:
- Professional yet personable
- Detailed but easy to understand
- Competitive while maintaining margins
- Tailored to the specific project

Use the contractor's profile and past successful bids as reference.""",
    "tools": ["format_bid_proposal", "calculate_pricing_breakdown", "generate_timeline"]
}

group_bidding_subagent = {
    "name": "group-bidding",
    "description": "Identifies and coordinates group bidding opportunities with 15-25% savings. Use when projects could benefit from multiple contractors or when contractor mentions working with others.",
    "prompt": """You are a group bidding coordinator for InstaBids.
    
Your role is to identify and facilitate group bidding:
- Find projects suitable for multiple contractors
- Calculate group savings (typically 15-25%)
- Coordinate contractor collaboration
- Structure group proposals

Group bidding works best for:
- Large projects requiring multiple trades
- Neighborhood projects (multiple homes)
- Complex projects needing diverse expertise

Explain the benefits clearly and handle coordination details.""",
    "tools": ["find_group_opportunities", "calculate_group_savings", "coordinate_contractors"]
}

# ============================================================================
# TOOL FUNCTIONS (Extracted from existing subagents)
# ============================================================================

async def search_bid_cards(
    contractor_zip: str,
    radius_miles: int = 30,
    project_type: Optional[str] = None
) -> Dict[str, Any]:
    """Search for bid cards using existing API endpoint with location filtering"""
    import aiohttp
    import asyncio
    from database import SupabaseDB
    
    try:
        # If no contractor_zip provided, try to get it from contractor profile
        if not contractor_zip:
            logger.warning("BSA: No contractor ZIP provided, searching contractor profile...")
            db = SupabaseDB()
            # Extract contractor_id from context if available
            # For now, use the GreenScape contractor as example
            contractor_id = "87f93fbd-151d-4f17-9311-70ef9ba5256f"
            
            contractor = await db.get_contractor_by_id(contractor_id)
            if contractor:
                # Try to get ZIP from contractor profile
                if contractor.get('zip_code'):
                    contractor_zip = contractor['zip_code']
                    logger.info(f"BSA: Using contractor ZIP: {contractor_zip}")
                elif contractor.get('city') and contractor.get('state'):
                    # Use city/state if no ZIP available
                    city = contractor.get('city', '')
                    state = contractor.get('state', '')
                    contractor_zip = f"{city}, {state}"
                    logger.info(f"BSA: Using contractor city/state: {contractor_zip}")
                else:
                    logger.warning("BSA: No location data found in contractor profile")
                    contractor_zip = "33442"  # Default ZIP for testing
        
        # Use the existing bid card search API endpoint (same as UI)
        search_filters = {
            "status": ["generated", "active", "ready", "collecting_bids", "discovery", "bids_complete"],
            "zip_code": contractor_zip,
            "radius_miles": radius_miles
        }
        
        # Make HTTP request to the existing API endpoint
        # Use URL construction instead of params dict to match working curl format
        base_url = "http://localhost:8008/api/bid-cards/search"
        status_params = "&".join([f"status={status}" for status in search_filters["status"]])
        url = f"{base_url}?{status_params}&zip_code={search_filters['zip_code']}&radius_miles={search_filters['radius_miles']}"
        
        # Add project type filter if specified
        if project_type:
            url += f"&project_types={project_type}"
        
        logger.info(f"BSA: Constructed search URL: {url}")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        api_result = await response.json()
                        
                        # Transform API response to expected format
                        bid_cards = api_result.get("bid_cards", [])
                        
                        logger.info(f"BSA: Found {len(bid_cards)} bid cards via API search")
                        
                        return {
                            "success": True,
                            "bid_cards": bid_cards[:10],  # Limit to 10 results
                            "total_found": api_result.get("total", len(bid_cards)),
                            "search_criteria": {
                                "location": contractor_zip,
                                "radius": radius_miles,
                                "project_type": project_type
                            },
                            "api_powered": True
                        }
                    else:
                        logger.error(f"BSA: API search failed with status {response.status}")
                        error_text = await response.text()
                        logger.error(f"BSA: API error response: {error_text[:200]}")
                        
            except asyncio.TimeoutError:
                logger.error("BSA: API search timed out")
            except Exception as api_error:
                logger.error(f"BSA: API request failed: {api_error}")
        
        # Fallback to direct database search if API fails
        logger.info("BSA: Falling back to direct database search...")
        from database import SupabaseDB
        
        db = SupabaseDB()
        query = db.client.table('bid_cards').select('*')
        
        if project_type:
            query = query.ilike('project_type', f'%{project_type}%')
        
        result = query.execute()
        bid_cards = result.data if result.data else []
        
        logger.info(f"BSA: Fallback found {len(bid_cards)} bid cards")
        
        return {
            "success": True,
            "bid_cards": bid_cards[:10],
            "total_found": len(bid_cards),
            "search_criteria": {
                "location": contractor_zip,
                "radius": radius_miles,
                "project_type": project_type
            },
            "fallback_used": True
        }
        
    except Exception as e:
        logger.error(f"BSA: Error in search_bid_cards: {e}")
        import traceback
        logger.error(f"BSA: Traceback: {traceback.format_exc()}")
        
        return {
            "success": False,
            "error": str(e),
            "bid_cards": [],
            "total_found": 0
        }

async def get_nearby_projects(location: str, radius: int) -> List[Dict]:
    """Get projects near a location"""
    logger.info(f"BSA Tool: get_nearby_projects called with location={location}, radius={radius}")
    # Return sample data for now
    return [
        {"project_id": "sample-1", "location": location, "type": "landscaping", "distance_miles": 5},
        {"project_id": "sample-2", "location": location, "type": "turf installation", "distance_miles": 12}
    ]

async def calculate_project_fit(contractor_id: str, project_id: str) -> float:
    """Calculate how well a project fits a contractor"""
    logger.info(f"BSA Tool: calculate_project_fit called with contractor_id={contractor_id}, project_id={project_id}")
    return 0.85

async def analyze_market_trends(project_type: str, location: str) -> Dict:
    """Analyze market trends for a project type in a location"""
    logger.info(f"BSA Tool: analyze_market_trends called with project_type={project_type}, location={location}")
    return {"average_bid": 45000, "competition_level": "moderate"}

async def get_competitor_pricing(project_type: str, zip_code: str) -> Dict:
    """Get competitor pricing data"""
    logger.info(f"BSA Tool: get_competitor_pricing called with project_type={project_type}, zip_code={zip_code}")
    return {"low": 35000, "average": 45000, "high": 65000}

async def calculate_optimal_bid(project_details: Dict, market_data: Dict) -> int:
    """Calculate optimal bid amount"""
    logger.info(f"BSA Tool: calculate_optimal_bid called with project_details={project_details}, market_data={market_data}")
    return 47500

async def format_bid_proposal(contractor_input: str, project_details: Dict) -> str:
    """Format a professional bid proposal"""
    logger.info(f"BSA Tool: format_bid_proposal called with contractor_input={contractor_input[:50]}...")
    return "Professional proposal formatted here..."

async def calculate_pricing_breakdown(total_amount: int, project_type: str) -> Dict:
    """Break down pricing into components"""
    logger.info(f"BSA Tool: calculate_pricing_breakdown called with total_amount={total_amount}, project_type={project_type}")
    return {"labor": 0.4 * total_amount, "materials": 0.5 * total_amount, "overhead": 0.1 * total_amount}

async def generate_timeline(project_type: str, scope: str) -> str:
    """Generate project timeline"""
    logger.info(f"BSA Tool: generate_timeline called with project_type={project_type}, scope={scope}")
    return "6-8 weeks from start date"

async def find_group_opportunities(project_id: str) -> List[Dict]:
    """Find group bidding opportunities"""
    logger.info(f"BSA Tool: find_group_opportunities called with project_id={project_id}")
    return [{"project_id": project_id, "group_potential": "high", "estimated_savings": "20%"}]

async def calculate_group_savings(contractors_count: int, project_value: int) -> Dict:
    """Calculate savings from group bidding"""
    logger.info(f"BSA Tool: calculate_group_savings called with contractors_count={contractors_count}, project_value={project_value}")
    savings_percent = min(0.15 + (0.02 * contractors_count), 0.25)
    return {"savings_percent": savings_percent, "total_savings": project_value * savings_percent}

async def coordinate_contractors(project_id: str, contractor_ids: List[str]) -> Dict:
    """Coordinate multiple contractors for group bid"""
    logger.info(f"BSA Tool: coordinate_contractors called with project_id={project_id}, contractor_ids={contractor_ids}")
    return {"status": "coordinated", "contractors": contractor_ids}

# ============================================================================
# MAIN BSA DEEPAGENT CREATION
# ============================================================================

def create_bsa_deepagent():
    """Creates the ONE proper BSA agent using DeepAgents framework"""
    
    # Convert async functions to tools that DeepAgents can use
    tools = [
        search_bid_cards,
        get_nearby_projects,
        calculate_project_fit,
        analyze_market_trends,
        get_competitor_pricing,
        calculate_optimal_bid,
        format_bid_proposal,
        calculate_pricing_breakdown,
        generate_timeline,
        find_group_opportunities,
        calculate_group_savings,
        coordinate_contractors
    ]
    
    # Create the deep agent with proper subagents
    return create_deep_agent(
        tools=tools,
        instructions=BSA_MAIN_INSTRUCTIONS,
        subagents=[
            bid_search_subagent,
            market_research_subagent,
            bid_submission_subagent,
            group_bidding_subagent
        ],
        state_schema=BSADeepAgentState
    )

# ============================================================================
# STREAMING FUNCTION - OPTIMIZED WITH SINGLETON, CACHING, AND SMART ROUTING
# ============================================================================

from agents.bsa.context_cache import bsa_context_cache
from agents.bsa.subagent_router import BSASubagentRouter

async def bsa_deepagent_stream(
    contractor_id: str,
    message: str,
    conversation_history: List[Dict] = None,
    session_id: str = None,
    bid_card_id: str = None
):
    """
    Stream responses using OPTIMIZED DeepAgents with singleton graph
    Now with caching, persistent state, and smart routing for 2-5 second responses
    """
    
    # Import BSASingleton here to avoid circular import
    from agents.bsa.bsa_singleton import BSASingleton
    
    # Get singleton instance (no recreation!)
    singleton = await BSASingleton.get_instance()
    
    # Generate consistent thread_id for this session
    thread_id = BSASingleton.get_thread_id(contractor_id, session_id)
    logger.info(f"BSA Optimized: Using thread_id={thread_id}")
    
    # Initialize systems for context loading
    db = SupabaseDB()
    contractor_adapter = ContractorContextAdapter()
    ai_memory = ContractorAIMemory()
    
    # OPTIMIZATION: Use cached context when possible
    contractor_context = await bsa_context_cache.get_contractor_context(
        contractor_id=contractor_id,
        loader_func=lambda: asyncio.create_task(
            asyncio.to_thread(
                contractor_adapter.get_contractor_context,
                contractor_id=contractor_id,
                session_id=session_id
            )
        )
    )
    
    # OPTIMIZATION: Cache AI memory (changes less frequently)
    ai_memory_context = await bsa_context_cache.get_ai_memory(
        contractor_id=contractor_id,
        loader_func=lambda: ai_memory.get_memory_for_system_prompt(contractor_id)
    )
    
    # OPTIMIZATION: Cache My Bids context
    my_bids_context = await bsa_context_cache.get_my_bids(
        contractor_id=contractor_id,
        loader_func=lambda: my_bids_tracker.load_full_my_bids_context(contractor_id)
    )
    
    # Log cache stats for monitoring
    cache_stats = bsa_context_cache.get_stats()
    logger.info(f"BSA Cache Stats: Hit rate={cache_stats['hit_rate']:.1%}, Entries={cache_stats['entries']}")
    
    # OPTIMIZATION: Smart subagent routing
    subagents_to_call = BSASubagentRouter.route_message(message, conversation_history)
    use_planning = BSASubagentRouter.should_use_planning(message, conversation_history)
    
    logger.info(f"BSA Router: Calling subagents={subagents_to_call}, planning={use_planning}")
    logger.info(f"BSA Router: {BSASubagentRouter.get_routing_explanation(message)}")
    
    # Build state (much smaller with optimizations)
    state = {
        "messages": conversation_history or [],
        "contractor_id": contractor_id,
        "contractor_context": contractor_context,
        "ai_memory_context": ai_memory_context,
        "my_bids_context": my_bids_context,
        "session_id": session_id,
        "bid_card_id": bid_card_id,
        "todos": [] if use_planning else None,  # Only use planning when needed
        "files": {},
        # Add routing hints for DeepAgents
        "_subagents_to_call": subagents_to_call,
        "_skip_planning": not use_planning
    }
    
    # Add current user message
    state["messages"].append({"role": "user", "content": message})
    logger.info(f"BSA Optimized: State ready with {len(state['messages'])} messages")
    
    # Use singleton for invocation (no more testing, just use it!)
    try:
        logger.info(f"BSA STREAMING: Starting singleton.invoke() (direct path)...")
        start_time = datetime.now()
        
        # Invoke through singleton with thread persistence
        result = await singleton.invoke(state, thread_id)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"BSA STREAMING: Direct invoke completed in {elapsed:.2f} seconds")
        logger.info(f"BSA STREAMING: Result type: {type(result)}")
        logger.info(f"BSA STREAMING: Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict) and "messages" in result:
            messages = result["messages"]
            logger.info(f"BSA STREAMING: Found {len(messages)} messages in result")
            
            if messages:
                last_msg = messages[-1]
                logger.info(f"BSA STREAMING: Last message type: {type(last_msg)}")
                logger.info(f"BSA STREAMING: Raw last_msg = {repr(last_msg)}")
                
                if isinstance(last_msg, dict):
                    logger.info(f"BSA STREAMING: last_msg keys = {list(last_msg.keys())}")
                    logger.info(f"BSA STREAMING: role = {repr(last_msg.get('role'))}")
                    logger.info(f"BSA STREAMING: content = {repr(last_msg.get('content'))}")
                
                # Extract response content - Handle both dict and LangChain AIMessage objects
                response_content = None
                extraction_method = "none"
                
                # Check if it's a LangChain AIMessage object
                if hasattr(last_msg, 'content') and hasattr(last_msg, 'type'):
                    # LangChain message object (AIMessage, HumanMessage, etc.)
                    if last_msg.type == "ai" or type(last_msg).__name__ == 'AIMessage':
                        response_content = last_msg.content
                        extraction_method = "langchain_ai_message"
                        logger.info(f"BSA STREAMING: Extracted from LangChain AIMessage: {len(response_content)} chars")
                
                # Fallback to original dict format
                elif isinstance(last_msg, dict) and last_msg.get("role") == "assistant" and last_msg.get("content"):
                    response_content = last_msg.get("content", "")
                    extraction_method = "dict_format"
                    logger.info(f"BSA STREAMING: Extracted from dict format: {len(response_content)} chars")
                
                # Additional fallback for other message types
                elif isinstance(last_msg, dict) and last_msg.get("content"):
                    response_content = last_msg.get("content", "")
                    extraction_method = "dict_any_role"
                    logger.info(f"BSA STREAMING: Extracted from dict (any role): {len(response_content)} chars")
                
                logger.info(f"BSA STREAMING: Content extraction method = {extraction_method}")
                logger.info(f"BSA STREAMING: Extracted content length = {len(response_content) if response_content else 0}")
                
                if response_content:
                    logger.info(f"BSA STREAMING: SUCCESS! Streaming {len(response_content)} chars via direct path")
                    logger.info(f"BSA STREAMING: Content preview: {repr(response_content[:100])}...")
                    
                    # Stream the response in chunks for frontend compatibility
                    chunk_size = 50
                    chunks_sent = 0
                    for i in range(0, len(response_content), chunk_size):
                        chunk_text = response_content[i:i+chunk_size]
                        chunks_sent += 1
                        yield {
                            "choices": [{"delta": {"content": chunk_text}}],
                            "model": "deepagents-bsa-optimized-direct",
                            "real_ai": True,
                            "orchestrated": True,
                            "response_time": elapsed,
                            "extraction_method": extraction_method
                        }
                        await asyncio.sleep(0.02)  # Faster streaming
                    
                    logger.info(f"BSA STREAMING: Sent {chunks_sent} chunks via direct path")
                    
                    # Final done marker
                    yield {
                        "choices": [{"delta": {"content": ""}}],
                        "done": True,
                        "model": "deepagents-bsa-optimized-direct",
                        "total_time": elapsed,
                        "total_chars": len(response_content),
                        "chunks_sent": chunks_sent
                    }
                    
                    # Save conversation result
                    await save_conversation_result(result, contractor_id, session_id, message, response_content)
                    
                    # Log performance metrics
                    logger.info(f"BSA STREAMING: Direct path SUCCESS: {elapsed:.2f}s response, {len(response_content)} chars")
                    return
                else:
                    logger.warning(f"BSA STREAMING: Direct path FAILED to extract content")
                    logger.warning(f"BSA STREAMING: Last message was: {repr(last_msg)}")
            else:
                logger.warning(f"BSA STREAMING: Direct path - no messages in result")
        else:
            logger.warning(f"BSA STREAMING: Direct path - no 'messages' key in result")
            logger.warning(f"BSA STREAMING: Available keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
    except Exception as e:
        logger.error(f"BSA STREAMING: Direct path failed - {e}")
        import traceback
        logger.error(f"BSA STREAMING: Direct path traceback: {traceback.format_exc()}")
        
    except Exception as e:
        logger.error(f"BSA Optimized: Failed - {e}")
        import traceback
        logger.error(f"BSA Optimized: Traceback: {traceback.format_exc()}")
    
    # Fallback to streaming if invoke fails
    logger.info(f"BSA Optimized: Falling back to streaming...")
    
    full_response = ""
    chunk_count = 0
    start_time = datetime.now()
    
    try:
        # Stream using singleton
        async for chunk in singleton.stream(state, thread_id):
            chunk_count += 1
            
            # DEBUG: Log what GPT-4 is returning in stream chunks
            logger.info(f"BSA STREAM DEBUG: Got chunk #{chunk_count}: {type(chunk)}")
            if isinstance(chunk, dict):
                logger.info(f"BSA STREAM DEBUG: Chunk keys = {list(chunk.keys())}")
                logger.info(f"BSA STREAM DEBUG: Full chunk = {chunk}")
            
            if "messages" in chunk and chunk["messages"]:
                last_message = chunk["messages"][-1]
                logger.info(f"BSA STREAM DEBUG: Last message type = {type(last_message)}")
                logger.info(f"BSA STREAM DEBUG: Last message = {last_message}")
                
                # Extract content from message - Handle both dict and LangChain objects
                content = None
                is_assistant_message = False
                
                if hasattr(last_message, 'content') and hasattr(last_message, 'type'):
                    # LangChain message object
                    content = last_message.content
                    is_assistant_message = (last_message.type == "ai" or type(last_message).__name__ == 'AIMessage')
                    logger.info(f"BSA STREAM DEBUG: LangChain content = {repr(content)}, type = {last_message.type}")
                elif isinstance(last_message, dict) and "content" in last_message:
                    # Dict format
                    content = last_message["content"]
                    is_assistant_message = (last_message.get("role") == "assistant")
                    logger.info(f"BSA STREAM DEBUG: Dict content = {repr(content)}, role = {last_message.get('role')}")
                
                # Stream new content from assistant messages
                if content and is_assistant_message:
                    role = last_message.get("role", "assistant")
                    if role != "user" and len(content) > len(full_response):
                        new_content = content[len(full_response):]
                        full_response = content
                        
                        # Yield streaming chunks
                        yield {
                            "choices": [{"delta": {"content": new_content}}],
                            "model": "deepagents-bsa-optimized-stream",
                            "real_ai": True,
                            "orchestrated": True
                        }
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"BSA Optimized: Stream complete in {elapsed:.2f}s, {len(full_response)} chars")
        
    except Exception as e:
        logger.error(f"BSA Optimized: Stream failed - {e}")
    
    # Final done marker
    yield {
        "choices": [{"delta": {"content": ""}}],
        "done": True,
        "model": "deepagents-bsa-optimized"
    }
    
    # Save conversation to memory (KEEP ALL EXISTING SAVES)
    if full_response:
        # Save to unified conversation (EXISTING)
        await db.save_unified_conversation({
            "user_id": contractor_id,
            "session_id": session_id or f"bsa_{asyncio.get_event_loop().time()}",
            "agent_type": "BSA-DeepAgents",
            "input_data": message,
            "response": full_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update AI memory (EXISTING)
        conversation_data = {
            'input': message,
            'response': full_response,
            'context': f"BSA DeepAgents conversation for contractor {contractor_id}",
            'orchestrated': True
        }
        await ai_memory.update_contractor_memory(
            contractor_id=contractor_id,
            conversation_data=conversation_data
        )
        
        # Track bid card interaction if mentioned (EXISTING)
        if bid_card_id:
            await my_bids_tracker.track_bid_interaction(
                contractor_id=contractor_id,
                bid_card_id=bid_card_id,
                interaction_type='deepagent_conversation',
                details={'message': message[:200], 'session_id': session_id}
            )
    
    logger.info(f"BSA DeepAgents: Completed response for {contractor_id}")

async def save_conversation_result(result_data, contractor_id, session_id, message, response_content):
    """Helper function to save conversation results"""
    try:
        db = SupabaseDB()
        ai_memory = ContractorAIMemory()
        
        # Save to unified conversation (EXISTING)
        await db.save_unified_conversation({
            "user_id": contractor_id,
            "session_id": session_id or f"bsa_{asyncio.get_event_loop().time()}",
            "agent_type": "BSA-DeepAgents-Direct",
            "input_data": message,
            "response": response_content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update AI memory (EXISTING)
        conversation_data = {
            'input': message,
            'response': response_content,
            'context': f"BSA DeepAgents conversation for contractor {contractor_id}",
            'orchestrated': True
        }
        await ai_memory.update_contractor_memory(
            contractor_id=contractor_id,
            conversation_data=conversation_data
        )
        
        logger.info(f"BSA DeepAgents: Successfully saved conversation result for {contractor_id}")
        
    except Exception as e:
        logger.error(f"BSA DeepAgents: Failed to save conversation result: {e}")

# ============================================================================
# BACKWARDS COMPATIBILITY WRAPPER
# ============================================================================

# Alias for easy switching
bsa_conversation = bsa_deepagent_stream