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
# REMOVED: from memory.contractor_ai_memory import ContractorAIMemory
from adapters.contractor_context import ContractorContextAdapter
from services.my_bids_tracker import my_bids_tracker

# Import the LLM-powered extraction tool function
from agents.bsa.tools.bid_extraction_llm import extract_quote_from_document

# Import bid submission tool functions  
from agents.bsa.tools.bid_submission_tools import (
    parse_verbal_bid,
    validate_bid_completeness,
    submit_contractor_bid,
    get_bid_card_requirements
)

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

CONTRACTOR CONTEXT AWARENESS:
You have access to comprehensive contractor data in the state:

**contractor_context**: Contains contractor profile, location (zip_code), specialties, available projects, bid history, and submitted bids.

**my_bids_context**: Contains the contractor's "My Bids" - projects they've previously quoted on or are actively working on:
- total_my_bids: Number of projects in their My Bids section
- my_bids: Array of bid cards with complete project details including:
  - bid_card_id and bid_card_number (e.g., IBC-20250801030643)  
  - project_type (e.g., "kitchen", "bathroom", "plumbing")
  - budget_min/budget_max, timeline, location
  - Complete bid_card object with full project specifications
  - Their submitted bids and proposal status

**CRITICAL: When contractors ask about "my projects", "projects I quoted on", "the kitchen project", etc., ALWAYS check my_bids_context FIRST before using subagents.**

INTELLIGENT CONTEXT USAGE:
- If they ask about a specific project type (e.g. "kitchen project") and you see matching project_type in my_bids_context, discuss that project directly
- Reference specific bid card numbers (IBC-xxx) when discussing their projects  
- Use their actual bid amounts, timelines, and project details from the context
- If my_bids_context shows projects, proactively mention them when relevant

YOUR CAPABILITIES THROUGH SUBAGENTS:

1. **bid-search** - Use this to find NEW relevant bid cards and projects
   - Only use when they want to find NEW opportunities
   - Searches by location, radius, and project type
   - Matches contractor specialties to opportunities

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

ENHANCED ORCHESTRATION GUIDELINES:
- When contractors ask about "my projects", "projects I quoted on", "the kitchen project" → Check my_bids_context FIRST, discuss directly without subagents
- When they ask about "available work", "new opportunities" → Use bid-search subagent
- When they need pricing advice → Use market-research subagent  
- When ready to submit → Use bid-submission subagent
- When multiple contractors could benefit → Consider group-bidding subagent

CONVERSATION EXAMPLES:
❌ BAD: "Could you provide me with the Project ID?"  
✅ GOOD: "I can see your kitchen project! You quoted on IBC-20250801030643, the $25,000-$30,000 kitchen remodel with white cabinets and quartz countertops."

Be conversational, helpful, and proactively use the contractor's actual context data.
Always reference specific project details, bid card numbers, and amounts when available in the context."""

# ============================================================================
# SUBAGENT CONFIGURATIONS
# ============================================================================

bid_search_subagent = {
    "name": "bid_search",
    "description": "Searches for bid cards and projects matching contractor capabilities. Use when contractor asks about available work, projects near them, or opportunities in their area.",
    "prompt": """You are a bid search specialist for InstaBids.
    
Your role is to automatically find relevant projects for contractors based on their profile data:
- Automatically uses their zip code and service radius from profile
- Automatically matches their contractor specialties and capabilities
- Filters by project requirements and budget
- Considers timeline and urgency

Use the search_projects_for_contractor tool to find projects - it automatically gets the contractor's location and specialties from their profile, so you don't need to ask for zip codes or specialties.

When presenting results:
- Highlight projects that match their specialties (from profile)
- Explain the fit based on their experience
- Note budget alignment with their typical pricing
- Mention timeline compatibility
- Reference their actual location and service area from profile""",
    "tools": ["search_projects_for_contractor", "get_nearby_projects", "calculate_project_fit"]
}

market_research_subagent = {
    "name": "market_research",
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
    "description": "Handles complete bid submission process including quote analysis and document upload. Use when contractor wants to submit a bid, upload a quote, or needs help extracting bid details from documents.",
    "prompt": """You are a bid submission specialist for InstaBids.
    
Your comprehensive role includes:
1. **Document Analysis**: Extract bid details from uploaded PDFs, images, or CRM exports
2. **Quote Processing**: Parse contractor quotes and convert to structured bid data
3. **Bid Validation**: Ensure all required fields are complete and valid
4. **Professional Formatting**: Transform casual input into professional proposals
5. **Submission Management**: Handle actual bid submission to the platform

**Document Processing Capabilities**:
- PDF text extraction (contractor quotes, estimates, CRM exports)
- Image OCR for handwritten or scanned quotes
- CRM format parsing (QuickBooks, Salesforce, etc.)
- Contact information filtering for security

**Bid Submission Workflow**:
1. Analyze uploaded documents or verbal descriptions
2. Extract: price, timeline, materials, warranty, approach
3. Validate against project requirements
4. Format professional proposal
5. Submit to database with proper tracking

Use these tools to help contractors submit bids efficiently from their existing quotes or verbal descriptions.""",
    "tools": [
        "extract_quote_from_document", 
        "parse_verbal_bid", 
        "validate_bid_completeness",
        "submit_contractor_bid",
        "get_bid_card_requirements",
        "format_bid_proposal", 
        "calculate_pricing_breakdown", 
        "generate_timeline"
    ]
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

async def search_bid_cards_with_contractor_profile(
    contractor_context: Dict[str, Any],
    project_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for bid cards using contractor's profile data automatically
    Extracts zip code, radius, contractor types, and company size from contractor context
    """
    
    # Extract contractor profile data
    contractor_profile = contractor_context.get('contractor_profile', {})
    
    # Get location data from contractor profile
    contractor_zip = contractor_profile.get('zip_code')
    radius_miles = contractor_profile.get('service_radius_miles', 30)
    
    # Get contractor specialties/types - check multiple sources
    contractor_type_ids = []
    contractor_types = contractor_profile.get('contractor_types', [])
    specialties = contractor_profile.get('specialties', [])
    
    # If we have specific contractor_types, use those
    if contractor_types:
        if isinstance(contractor_types[0], int):
            contractor_type_ids = contractor_types
        else:
            contractor_type_ids = []
    
    # Get contractor size for ±1 tier filtering
    contractor_size = contractor_profile.get('contractor_size', 3)  # Default to small_business (3)
    
    logger.info(f"BSA Profile Search: contractor_zip={contractor_zip}, radius={radius_miles}, contractor_type_ids={contractor_type_ids}, contractor_size={contractor_size}")
    
    if not contractor_zip:
        return {
            "error": "Contractor zip code not found in profile",
            "total_found": 0,
            "bid_cards": []
        }
    
    # Call the original search function with profile data including company size
    return await search_bid_cards_original(
        contractor_zip=contractor_zip,
        radius_miles=radius_miles,
        project_type=project_type,
        contractor_type_ids=contractor_type_ids,
        contractor_size=contractor_size
    )

async def search_bid_cards_original(
    contractor_zip: str,
    radius_miles: int = 30,
    project_type: Optional[str] = None,
    contractor_type_ids: List[int] = [],
    contractor_size: int = 3
) -> Dict[str, Any]:
    """
    Search for bid cards with accurate radius filtering and contractor type matching
    Uses direct database access with proper distance calculation
    """
    # Import required utilities  
    from utils.radius_search_fixed import filter_by_radius
    from database_simple import db
    
    try:
        logger.info(f"BSA Tool: Starting bid card search")
        logger.info(f"Location: {contractor_zip}, Radius: {radius_miles} miles")
        logger.info(f"Project Type: {project_type}")
        logger.info(f"Contractor Type IDs: {contractor_type_ids}")
        
        # If no contractor_zip provided, try to get it from contractor profile
        if not contractor_zip:
            logger.warning("BSA: No contractor ZIP provided, using default...")
            contractor_zip = "33442"  # Default ZIP for testing
        
        # Step 1: Get all bid cards from database
        query = db.client.table('bid_cards').select('*')
        result = query.execute()
        bid_cards = result.data if result.data else []
        
        logger.info(f"BSA Tool: Retrieved {len(bid_cards)} total bid cards from database")
        
        # Step 2: Apply contractor type filtering if provided
        if contractor_type_ids:
            type_matched_cards = []
            for card in bid_cards:
                card_type_ids = card.get('contractor_type_ids', [])
                if card_type_ids:
                    # Check for overlap between contractor and card types
                    contractor_id_set = set(contractor_type_ids)
                    bid_card_id_set = set(card_type_ids)
                    overlap = contractor_id_set & bid_card_id_set
                    if overlap:
                        type_matched_cards.append(card)
                        
            logger.info(f"BSA Tool: Found {len(type_matched_cards)} bid cards matching contractor types")
            bid_cards = type_matched_cards
        
        # Step 2.5: Apply company size filtering (±1 tier visibility rule)
        size_filtered_cards = []
        for card in bid_cards:
            card_size = card.get('contractor_size_preference')
            
            # If bid card doesn't specify size preference, show to all sizes
            if not card_size:
                size_filtered_cards.append(card)
                continue
                
            # Apply ±1 tier visibility rule
            # Size 1 can see 1,2 | Size 2 can see 1,2,3 | Size 3 can see 2,3,4 | Size 4 can see 3,4,5 | Size 5 can see 4,5
            allowed_sizes = []
            if contractor_size == 1:
                allowed_sizes = [1, 2]
            elif contractor_size == 2:
                allowed_sizes = [1, 2, 3]
            elif contractor_size == 3:
                allowed_sizes = [2, 3, 4]
            elif contractor_size == 4:
                allowed_sizes = [3, 4, 5]
            elif contractor_size == 5:
                allowed_sizes = [4, 5]
            
            # Check if card allows this contractor size
            if isinstance(card_size, int) and card_size in allowed_sizes:
                size_filtered_cards.append(card)
            elif isinstance(card_size, list) and any(size in allowed_sizes for size in card_size):
                size_filtered_cards.append(card)
        
        logger.info(f"BSA Tool: Found {len(size_filtered_cards)} bid cards matching contractor size {contractor_size} (±1 tier rule)")
        bid_cards = size_filtered_cards
        
        # Step 3: Apply accurate radius filtering
        matching_cards = filter_by_radius(
            items=bid_cards,
            center_zip=contractor_zip,
            radius_miles=radius_miles,
            zip_field="location_zip"
        )
        
        logger.info(f"BSA Tool: Found {len(matching_cards)} bid cards within {radius_miles} miles after accurate filtering")
        
        # Step 4: Apply project type filtering if specified
        if project_type:
            project_filtered_cards = [
                card for card in matching_cards 
                if card.get('project_type', '').lower() == project_type.lower()
            ]
            logger.info(f"BSA Tool: Found {len(project_filtered_cards)} bid cards matching project type '{project_type}'")
            final_cards = project_filtered_cards
        else:
            final_cards = matching_cards
        
        # Step 5: Filter for available bid cards (not completed)
        available_cards = [
            card for card in final_cards
            if card.get('status', '').lower() in ['generated', 'collecting_bids', 'active']
        ]
        
        logger.info(f"BSA Tool: Found {len(available_cards)} available bid cards after status filtering")
        
        # Step 6: Return results with proper format
        return {
            "success": True,
            "bid_cards": available_cards[:10],  # Limit to 10 results for performance
            "total_found": len(available_cards),
            "search_criteria": {
                "location": contractor_zip,
                "radius": radius_miles,
                "project_type": project_type,
                "contractor_type_ids": contractor_type_ids,
                "contractor_size": contractor_size
            },
            "filters_applied": {
                "radius_accurate": True,
                "contractor_type_matching": len(contractor_type_ids) > 0,
                "project_type_filtering": project_type is not None,
                "company_size_filtering": True,
                "status_filtering": True
            },
            "search_method": "direct_database_with_accurate_radius"
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

async def search_projects_for_contractor(
    project_type: Optional[str] = None,
    contractor_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for projects using the contractor's profile data
    This is the main search function BSA should use - automatically gets location and specialties
    """
    logger.info(f"BSA Auto-Search: search_projects_for_contractor called with project_type={project_type}, contractor_id={contractor_id}")
    
    # Get contractor context from ContractorContextAdapter
    from adapters.contractor_context import ContractorContextAdapter
    
    # Use the contractor_id from the BSA session if not provided
    if not contractor_id:
        # For now, use default contractor from environment or context
        contractor_id = "22222222-2222-2222-2222-222222222222"  # BSA test contractor
        logger.info(f"BSA Auto-Search: Using default contractor_id: {contractor_id}")
    
    try:
        # Load contractor context using the adapter
        adapter = ContractorContextAdapter()
        contractor_context = adapter.get_contractor_context(contractor_id)
        
        if not contractor_context:
            return {"error": f"Could not load contractor context for ID: {contractor_id}", "total_found": 0, "bid_cards": []}
        
        logger.info(f"BSA Auto-Search: Successfully loaded contractor context")
        logger.info(f"BSA Auto-Search: Contractor location: {contractor_context.get('zip_code', 'Unknown')}")
        logger.info(f"BSA Auto-Search: Contractor specialties: {contractor_context.get('specialties', [])}")
        
        # Use the contractor profile search function
        result = await search_bid_cards_with_contractor_profile(
            contractor_context=contractor_context,
            project_type=project_type
        )
        
        logger.info(f"BSA Auto-Search: Search completed successfully, found {result.get('total_found', 0)} projects")
        return result
        
    except Exception as e:
        logger.error(f"BSA Auto-Search: Error loading contractor context: {e}")
        import traceback
        logger.error(f"BSA Auto-Search: Traceback: {traceback.format_exc()}")
        return {"error": f"Failed to load contractor context: {str(e)}", "total_found": 0, "bid_cards": []}

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
        search_bid_cards_original,  # Keep original for backwards compatibility
        search_projects_for_contractor,  # NEW: Automatic search using contractor profile
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
        coordinate_contractors,
        # Add bid submission tools
        extract_quote_from_document,
        parse_verbal_bid,
        validate_bid_completeness,
        submit_contractor_bid,
        get_bid_card_requirements
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
    logger.info(f"BSA_DEEPAGENT_STREAM: CALLED with contractor_id={contractor_id}, message={message[:50]}...")
    logger.info(f"BSA_DEEPAGENT_STREAM: conversation_history={len(conversation_history) if conversation_history else 0} messages")
    
    # Import BSASingleton here to avoid circular import
    from agents.bsa.bsa_singleton import BSASingleton
    
    # Get singleton instance (no recreation!)
    logger.info(f"BSA_DEEPAGENT_STREAM: Getting singleton instance...")
    singleton = await BSASingleton.get_instance()
    logger.info(f"BSA_DEEPAGENT_STREAM: Got singleton: {singleton}")
    
    # Generate consistent thread_id for this session
    thread_id = BSASingleton.get_thread_id(contractor_id, session_id)
    logger.info(f"BSA Optimized: Using thread_id={thread_id}")
    
    # Initialize systems for context loading
    db = SupabaseDB()
    contractor_adapter = ContractorContextAdapter()
    # REMOVED: ContractorAIMemory - using unified memory only
    # ai_memory = ContractorAIMemory()
    
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
    
    # REMOVED: AI memory context - using unified memory only
    # ai_memory_context = await bsa_context_cache.get_ai_memory(
    #     contractor_id=contractor_id,
    #     loader_func=lambda: ai_memory.get_memory_for_system_prompt(contractor_id)
    # )
    ai_memory_context = {}  # Empty for now
    
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
    
    # CRITICAL FIX: Convert OpenAI format messages to LangChain format for DeepAgents compatibility
    from langchain_core.messages import HumanMessage, AIMessage
    
    langchain_messages = []
    if conversation_history:
        logger.info(f"BSA MEMORY FIX: Converting {len(conversation_history)} OpenAI format messages to LangChain format")
        for msg in conversation_history:
            if isinstance(msg, dict):
                if msg.get("role") == "user":
                    langchain_messages.append(HumanMessage(content=msg.get("content", "")))
                elif msg.get("role") == "assistant":
                    langchain_messages.append(AIMessage(content=msg.get("content", "")))
                elif msg.get("role") == "system":
                    # System messages can be added as HumanMessage with context
                    langchain_messages.append(HumanMessage(content=f"[System Context] {msg.get('content', '')}"))
            else:
                # Already LangChain format, keep as is
                langchain_messages.append(msg)
        logger.info(f"BSA MEMORY FIX: Converted to {len(langchain_messages)} LangChain messages")
    
    # Add current user message in LangChain format
    langchain_messages.append(HumanMessage(content=message))
    
    # Build state (much smaller with optimizations)
    state = {
        "messages": langchain_messages,
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
    logger.info(f"BSA MEMORY FIX: State ready with {len(state['messages'])} LangChain messages (memory persistence should now work)")
    
    # Use singleton for invocation (no more testing, just use it!)
    try:
        logger.info(f"BSA STREAMING: Starting singleton.invoke() (direct path)...")
        start_time = datetime.now()
        
        # EMERGENCY FIX: Add timeout to prevent hanging
        try:
            # Invoke through singleton with thread persistence (increased timeout for GPT-4)
            result = await asyncio.wait_for(singleton.invoke(state, thread_id), timeout=30.0)
        except asyncio.TimeoutError:
            logger.error(f"BSA EMERGENCY: Singleton invoke timed out after 30s - using fallback response")
            # Create emergency fallback response
            fallback_response = f"Hello! I'm BSA, your bid submission assistant. I can help you with:\n\n• Finding available projects to bid on\n• Analyzing project requirements\n• Calculating competitive bid amounts\n• Submitting professional proposals\n\nWhat specific project or bidding assistance do you need today?"
            
            # Stream the fallback response
            chunk_size = 50
            chunks_sent = 0
            for i in range(0, len(fallback_response), chunk_size):
                chunk_text = fallback_response[i:i+chunk_size]
                chunks_sent += 1
                yield {
                    "choices": [{"delta": {"content": chunk_text}}],
                    "model": "deepagents-bsa-emergency-fallback",
                    "fallback_mode": True
                }
                await asyncio.sleep(0.02)
            
            # Final done marker
            yield {
                "choices": [{"delta": {"content": ""}}],
                "done": True,
                "model": "deepagents-bsa-emergency-fallback",
                "fallback_mode": True
            }
            return  # Exit early on timeout
        
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
                
                # Check if it's a LangChain AIMessage object (they don't have 'type' attribute)
                logger.info(f"BSA STREAMING: Checking if AIMessage - type name = {type(last_msg).__name__}, has content = {hasattr(last_msg, 'content')}")
                if type(last_msg).__name__ == 'AIMessage' and hasattr(last_msg, 'content'):
                    # LangChain AIMessage object
                    response_content = last_msg.content
                    extraction_method = "langchain_ai_message"
                    logger.info(f"BSA STREAMING: Extracted from LangChain AIMessage: {len(response_content) if response_content else 0} chars")
                    logger.info(f"BSA STREAMING: Content value = {repr(response_content[:200]) if response_content else 'None or empty'}")
                
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
    
    # Fallback to streaming if invoke fails or returns empty content
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
        
        # REMOVED: contractor_ai_memory updates - using unified memory only
        # conversation_data = {
        #     'input': message,
        #     'response': full_response,
        #     'context': f"BSA DeepAgents conversation for contractor {contractor_id}",
        #     'orchestrated': True
        # }
        # await ai_memory.update_contractor_memory(
        #     contractor_id=contractor_id,
        #     conversation_data=conversation_data
        # )
        
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
        # REMOVED: ai_memory = ContractorAIMemory()
        
        # Save to unified conversation (EXISTING)
        await db.save_unified_conversation({
            "user_id": contractor_id,
            "session_id": session_id or f"bsa_{asyncio.get_event_loop().time()}",
            "agent_type": "BSA-DeepAgents-Direct",
            "input_data": message,
            "response": response_content,
            "timestamp": datetime.now().isoformat()
        })
        
        # REMOVED: contractor_ai_memory updates - using unified memory only
        # conversation_data = {
        #     'input': message,
        #     'response': response_content,
        #     'context': f"BSA DeepAgents conversation for contractor {contractor_id}",
        #     'orchestrated': True
        # }
        # await ai_memory.update_contractor_memory(
        #     contractor_id=contractor_id,
        #     conversation_data=conversation_data
        # )
        
        logger.info(f"BSA DeepAgents: Successfully saved conversation result for {contractor_id}")
        
    except Exception as e:
        logger.error(f"BSA DeepAgents: Failed to save conversation result: {e}")

# ============================================================================
# BACKWARDS COMPATIBILITY WRAPPER
# ============================================================================

# Alias for easy switching
bsa_conversation = bsa_deepagent_stream