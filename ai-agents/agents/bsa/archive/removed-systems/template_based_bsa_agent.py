"""
BSA (Bid Submission Agent) - Built on DeepAgents Framework
Converts contractor natural input into standardized InstaBids proposals
"""

from typing import Dict, Any, List
from deepagents import create_deep_agent
from langchain_core.tools import tool
import os
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Import service complexity classifier for trade-specific routing
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from agents.cia.service_complexity_classifier import ServiceComplexityClassifier

# Import DeepAgents sub-agents (real system)
from .sub_agents.bid_card_search_agent import BidCardSearchAgent
from .sub_agents.market_research_agent import MarketResearchAgent
from .sub_agents.bid_submission_agent import BidSubmissionAgent
from .sub_agents.group_bidding_agent import GroupBiddingAgent

# ============================================================================
# CORE BSA TOOLS - These integrate with your existing systems
# ============================================================================

@tool
def fetch_bid_card(bid_card_id: str) -> Dict:
    """Fetch bid card details from database"""
    # This would use your Supabase MCP in production
    # For now, returning mock data to demonstrate
    return {
        "id": bid_card_id,
        "title": "Kitchen Remodel - Modern Update",
        "budget_range": {"min": 40000, "max": 60000},
        "timeline": "8-10 weeks",
        "requirements": [
            "Full cabinet replacement",
            "Granite countertops",
            "New appliances",
            "Tile backsplash"
        ],
        "sqft": 250
    }

@tool  
def get_contractor_profile(contractor_id: str) -> Dict:
    """Get contractor capabilities and pricing patterns from COIA"""
    # In production, this calls COIA agent
    return {
        "id": contractor_id,
        "specialties": ["kitchen", "bathroom"],
        "typical_pricing": {
            "kitchen_sqft": 240,
            "labor_rate": 85,
            "markup": 1.15
        },
        "crew_size": 4,
        "completed_projects": 127,
        "avg_timeline_weeks": 8
    }

@tool
def extract_pricing_from_text(text: str) -> Dict:
    """Parse natural language pricing into structured format"""
    import re
    
    # Extract dollar amounts
    price_pattern = r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)[kK]?'
    prices = re.findall(price_pattern, text)
    
    # Extract timeline
    timeline_pattern = r'(\d+)\s*(?:weeks?|days?|months?)'
    timelines = re.findall(timeline_pattern, text.lower())
    
    return {
        "extracted_prices": [p.replace(',', '') for p in prices],
        "extracted_timelines": timelines,
        "raw_text": text
    }

@tool
def calculate_trade_pricing(
    trade: str,
    sqft: float,
    materials: List[str],
    location: str = "default"
) -> Dict:
    """Calculate pricing based on trade-specific formulas"""
    
    base_rates = {
        "kitchen": {"labor": 85, "sqft": 240, "materials_multiplier": 1.4},
        "bathroom": {"labor": 95, "sqft": 350, "materials_multiplier": 1.5},
        "landscaping": {"labor": 65, "sqft": 15, "materials_multiplier": 1.2},
        "electrical": {"labor": 110, "per_outlet": 150, "per_fixture": 250},
        "plumbing": {"labor": 105, "per_fixture": 450, "rough_in": 2500}
    }
    
    if trade not in base_rates:
        trade = "kitchen"  # Default
        
    rates = base_rates[trade]
    
    # Calculate base cost
    if trade in ["kitchen", "bathroom", "landscaping"]:
        labor_cost = sqft * rates["sqft"] * 0.4  # 40% labor
        materials_cost = sqft * rates["sqft"] * 0.6  # 60% materials
    else:
        labor_cost = rates["labor"] * 40  # Assume 40 hours base
        materials_cost = 5000  # Base materials
    
    total = (labor_cost + materials_cost) * rates["materials_multiplier"]
    
    return {
        "trade": trade,
        "labor_cost": round(labor_cost),
        "materials_cost": round(materials_cost),
        "total_estimate": round(total),
        "breakdown": {
            "sqft_rate": rates.get("sqft", 0),
            "labor_rate": rates["labor"],
            "markup": rates["materials_multiplier"]
        }
    }

@tool
def generate_professional_proposal(
    contractor_name: str,
    project_type: str,
    amount: float,
    timeline_weeks: int,
    approach: str,
    materials: List[str]
) -> str:
    """Generate a professional proposal from extracted information"""
    
    timeline_start = datetime.now() + timedelta(days=14)  # 2 weeks out
    timeline_end = timeline_start + timedelta(weeks=timeline_weeks)
    
    proposal = f"""
## Project Proposal: {project_type}
**Submitted by:** {contractor_name}

### Project Overview
{approach}

### Scope of Work
Our comprehensive {project_type.lower()} service includes:
- Professional project management throughout
- All necessary permits and inspections
- High-quality materials from trusted suppliers
- Expert installation by certified professionals
- Complete cleanup and debris removal
- Full warranty on all work performed

### Materials & Specifications
{chr(10).join([f'- {material}' for material in materials])}

### Investment
**Total Project Investment:** ${amount:,.2f}
- Includes all labor, materials, and permits
- Payment schedule available upon request
- All pricing includes applicable warranties

### Timeline
**Project Start:** {timeline_start.strftime('%B %d, %Y')}
**Estimated Completion:** {timeline_end.strftime('%B %d, %Y')}
**Duration:** {timeline_weeks} weeks

### Why Choose Us
- {contractor_name} brings proven expertise to your project
- Fully licensed, bonded, and insured
- Commitment to quality and customer satisfaction
- Clear communication throughout the project

### Next Steps
Upon acceptance of this proposal, we will:
1. Schedule a detailed planning meeting
2. Finalize material selections
3. Obtain necessary permits
4. Begin work on scheduled start date

We look forward to transforming your space!
"""
    return proposal.strip()

# ============================================================================
# SERVICE COMPLEXITY ROUTING
# ============================================================================

class BSAServiceComplexityRouter:
    """Routes BSA requests based on project service complexity"""
    
    def __init__(self):
        self.service_classifier = ServiceComplexityClassifier()
        
    def classify_project_complexity(self, project_type: str, description: str = "", trade_count: int = None) -> Dict[str, Any]:
        """Classify project complexity for BSA routing decisions"""
        try:
            classification = self.service_classifier.classify_project(
                project_type=project_type,
                description=description,
                recommended_trades=None
            )
            
            print(f"[BSA Router] Project '{project_type}' classified as: {classification['service_complexity']}")
            print(f"[BSA Router] Trade count: {classification['trade_count']}, Primary: {classification['primary_trade']}")
            
            return classification
            
        except Exception as e:
            print(f"[BSA Router] Classification error: {e}")
            # Return safe defaults
            return {
                "service_complexity": "single-trade",
                "trade_count": 1,
                "primary_trade": project_type or "general",
                "secondary_trades": []
            }
    
    def route_to_subagent(self, project_classification: Dict[str, Any], request_type: str = "bid_search") -> str:
        """Route request to appropriate sub-agent based on complexity"""
        complexity = project_classification.get("service_complexity", "single-trade")
        trade_count = project_classification.get("trade_count", 1)
        
        # Route based on request type and complexity
        if request_type == "bid_search":
            if complexity == "single-trade":
                print(f"[BSA Router] Routing single-trade project to specialized bid_card_search")
                return "bid_card_search"
            elif complexity == "multi-trade" and trade_count <= 3:
                print(f"[BSA Router] Routing multi-trade project to market_research for coordination analysis")
                return "market_research"
            else:  # complex-coordination
                print(f"[BSA Router] Routing complex project to group_bidding for advanced coordination")
                return "group_bidding"
                
        elif request_type == "group_bidding":
            # Only route simple projects to group bidding initially
            if complexity == "single-trade":
                print(f"[BSA Router] Single-trade project approved for group bidding")
                return "group_bidding"
            else:
                print(f"[BSA Router] Multi-trade project requires individual handling first")
                return "market_research"
                
        elif request_type == "bid_submission":
            # All complexities can use bid submission optimization
            return "bid_submission"
            
        else:
            # Default routing
            return "bid_card_search"
    
    def get_complexity_specific_instructions(self, project_classification: Dict[str, Any]) -> str:
        """Generate complexity-specific instructions for sub-agents"""
        complexity = project_classification.get("service_complexity", "single-trade")
        primary_trade = project_classification.get("primary_trade", "general")
        secondary_trades = project_classification.get("secondary_trades", [])
        
        if complexity == "single-trade":
            return f"""
Focus on {primary_trade} projects. Key considerations:
- Single trade specialization
- Standard scheduling and pricing
- Individual contractor capability matching
- No trade coordination required
"""
        elif complexity == "multi-trade":
            trades_list = [primary_trade] + secondary_trades
            return f"""
Multi-trade project requiring: {', '.join(trades_list)}
Key considerations:
- Coordination between {len(trades_list)} trades
- Sequential scheduling requirements
- Material and timeline dependencies
- Contractor capability in multiple trades OR coordination ability
"""
        else:  # complex-coordination
            return f"""
Complex coordination project with {primary_trade} as primary trade
Key considerations:
- Advanced project management required
- Multiple trade coordination and scheduling
- Potential permit and regulatory complexity
- Experienced general contractors or coordination specialists needed
"""

# ============================================================================
# BSA MAIN INSTRUCTIONS
# ============================================================================

# ============================================================================
# BSA DEEPAGENTS SUBAGENT CONFIGURATION
# ============================================================================

from deepagents import create_deep_agent, SubAgent

# Import BSA tools for sub-agents
try:
    from agents.bsa.enhanced_tools import (
        search_available_bid_cards,
        research_contractor_company,
        find_similar_contractors,
        analyze_market_rates
    )
    BSA_TOOLS_AVAILABLE = True
    BSA_TOOLS = [
        search_available_bid_cards,
        research_contractor_company,
        find_similar_contractors, 
        analyze_market_rates
    ]
except ImportError as e:
    print(f"Warning: Could not import BSA tools: {e}")
    BSA_TOOLS_AVAILABLE = False
    BSA_TOOLS = []

# Properly define BSA sub-agents for DeepAgents framework
BSA_SUBAGENTS = [
    SubAgent(
        name="bid_card_search",
        description="Find and analyze relevant bid cards and projects for contractors based on their specialties, location, and preferences",
        prompt="""You are a bid card search specialist for InstaBids. Your role is to:
1. Search for relevant bid cards matching contractor criteria
2. Analyze project requirements and contractor capabilities
3. Provide insights on project suitability and competition
4. Suggest optimal bidding strategies

Focus on helping contractors find the best project opportunities.""",
        tools=["search_available_bid_cards", "find_similar_contractors"]
    ),
    SubAgent(
        name="market_research", 
        description="Research market pricing, trends, and competitive landscape for construction projects",
        prompt="""You are a market research analyst for the construction industry. Your role is to:
1. Research current market pricing for different project types
2. Analyze competitive landscape and pricing trends
3. Provide insights on market opportunities and threats
4. Help contractors understand fair market pricing

Focus on providing data-driven market intelligence to help contractors make informed bidding decisions.""",
        tools=["analyze_market_rates", "research_contractor_company"]
    ),
    SubAgent(
        name="bid_submission",
        description="Optimize bid proposals and manage submission strategy for maximum success rate", 
        prompt="""You are a bid submission optimizer for contractors. Your role is to:
1. Review and optimize bid proposals for clarity and competitiveness
2. Suggest pricing strategies based on project requirements
3. Help with proposal writing and presentation
4. Provide submission timing and strategy advice

Focus on maximizing contractor success rates through optimized bid submissions."""
    ),
    SubAgent(
        name="group_bidding",
        description="Handle multiple project bids and coordinate group submissions for efficiency",
        prompt="""You are a group bidding coordinator for contractors. Your role is to:
1. Identify opportunities for bulk or group project bidding
2. Coordinate multiple project submissions for efficiency
3. Analyze resource allocation across multiple projects
4. Suggest project bundling strategies for cost savings

Focus on helping contractors manage multiple opportunities effectively."""
    )
]

# ============================================================================
# BSA DEEPAGENTS IMPLEMENTATION
# ============================================================================

def create_bsa_agent():
    """
    Create BSA agent using DeepAgents framework with service complexity-aware routing
    
    The main agent uses ServiceComplexityClassifier to route requests to appropriate sub-agents
    based on project complexity (single-trade, multi-trade, complex-coordination).
    
    Returns:
        DeepAgents agent with BSA instructions and service complexity routing
    """
    
    # Initialize service complexity router
    complexity_router = BSAServiceComplexityRouter()
    
    bsa_instructions = f"""You are the BSA (Bid Submission Agent) for InstaBids, with advanced service complexity awareness.

Your primary role is to help contractors with complexity-appropriate routing:
1. Find relevant bid cards using service complexity classification 
2. Research market conditions with trade-specific analysis
3. Optimize bid submissions based on project complexity
4. Manage projects efficiently based on coordination requirements

SERVICE COMPLEXITY ROUTING:
- SINGLE-TRADE projects (lawn care, roofing, single-room): Route to bid_card_search for specialized matching
- MULTI-TRADE projects (kitchen remodel, bathroom): Route to market_research for coordination analysis  
- COMPLEX-COORDINATION projects (whole house, additions): Route to group_bidding for advanced planning

DELEGATION PATTERN with Complexity Awareness:
1. When contractors request projects, first classify the request complexity
2. Route to appropriate sub-agent based on classification
3. Provide complexity-specific context to the sub-agent

Example for single-trade:
"Let me search for lawn care projects using our single-trade specialization system."
→ Route to bid_card_search with single-trade context

Example for multi-trade:
"Let me analyze market conditions for this kitchen remodel requiring multiple trades."  
→ Route to market_research with multi-trade coordination context

CRITICAL: When sub-agents return results, YOU MUST:
1. Parse the actual results returned by the sub-agent
2. Present them with complexity-appropriate context
3. Explain why projects match the contractor's complexity capability
4. Never ignore sub-agent results

Always explain your routing decisions to help contractors understand the complexity-based approach."""

    # Create the DeepAgents-powered BSA agent with complexity routing
    return create_deep_agent(
        tools=BSA_TOOLS if BSA_TOOLS_AVAILABLE else [],
        instructions=bsa_instructions,
        subagents=BSA_SUBAGENTS
    )

# ============================================================================
# BSA INTERFACE FUNCTIONS
# ============================================================================

async def process_contractor_input_streaming(
    bid_card_id: str,
    contractor_id: str,
    input_type: str,
    input_data: str,
    session_id: str = None,
    conversation_history: List[Dict] = None
):
    """
    Stream BSA processing using OpenAI GPT-5/GPT-4o directly
    Returns an async generator for real-time streaming responses
    WITH MEMORY: Now includes conversation history for context
    """
    import os
    from openai import AsyncOpenAI
    
    # Get OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("No OpenAI API key configured")
        raise Exception("No OpenAI API key configured")
    
    logger.info(f"BSA: Creating OpenAI client for contractor {contractor_id}")
    client = AsyncOpenAI(api_key=api_key)
    
    logger.info(f"BSA: Processing message: {input_data[:100]}...")
    logger.info(f"BSA: Conversation history has {len(conversation_history) if conversation_history else 0} messages")
    
    # Check if this is a bid card search request
    def detect_bid_card_request(message: str) -> bool:
        # Keywords that indicate a conversational question, not a bid search
        conversational_keywords = [
            'context', 'prove', 'about me', 'my business', 'know about',
            'remember', 'who am i', 'what do you know', 'can you tell me',
            'my profile', 'my information', 'what is in your'
        ]
        
        search_keywords = [
            'find projects', 'show me projects', 'search projects', 'bid cards',
            'opportunities', 'jobs available', 'work available', 'available projects',
            'kitchen projects', 'bathroom projects', 'plumbing jobs',
            'turf projects', 'lawn projects', 'landscaping projects',
            'near me', 'in my area', 'within'  # Removed generic 'projects' and 'miles'
        ]
        message_lower = message.lower()
        
        # If it's a conversational question, definitely not a bid search
        if any(keyword in message_lower for keyword in conversational_keywords):
            return False
            
        return any(keyword in message_lower for keyword in search_keywords)
    
    # If this is a bid card search request, use direct search (API endpoint doesn't exist)
    if input_type == "text" and detect_bid_card_request(input_data):
        # ALWAYS use direct search since the API endpoint doesn't exist
        api_available = False  # Force direct search
        
        if True:  # Always take this path
            # Skip API and go straight to fallback
            yield {
                "type": "sub_agent_status",
                "message": "[DIRECT] Using direct bid card search...",
                "sub_agent": "bid-card-finder",
                "status": "searching"
            }
            
            # Extract ZIP code from input if available
            import re
            zip_match = re.search(r'\b(\d{5})\b', input_data)
            contractor_zip = zip_match.group(1) if zip_match else "33442"
            
            # Determine project type from input
            project_type = None
            if "kitchen" in input_data.lower():
                project_type = "kitchen"
            elif "bathroom" in input_data.lower():
                project_type = "bathroom"
            elif "landscaping" in input_data.lower() or "lawn" in input_data.lower() or "turf" in input_data.lower():
                project_type = "landscaping"
            
            # Use BSA tools directly
            from agents.bsa.sub_agents.bid_card_search_agent import BidCardSearchAgent
            search_agent = BidCardSearchAgent()
            
            # Send radius info
            yield {
                "type": "radius_info",
                "message": f"Searching within 30 miles of ZIP {contractor_zip}",
                "current_radius": 30,
                "current_zip": contractor_zip
            }
            
            # Search for bid cards
            try:
                bid_cards_result = await search_agent.search_bid_cards_in_radius(
                    contractor_zip=contractor_zip,
                    radius_miles=30,
                    project_type=project_type,
                    use_semantic_matching=True
                )
            except Exception as e:
                print(f"[BSA] Error in bid card search: {e}")
                # Use the enhanced tools directly as fallback
                from agents.bsa.enhanced_tools import search_available_bid_cards
                bid_cards_result = search_available_bid_cards.invoke({
                    "contractor_zip": contractor_zip,
                    "radius_miles": 30,
                    "project_keywords": project_type or "turf lawn"
                })
            
            if bid_cards_result.get('success') and bid_cards_result.get('bid_cards'):
                count = bid_cards_result.get('count', 0)
                bid_cards = bid_cards_result.get('bid_cards', [])
                
                yield {
                    "type": "sub_agent_status",
                    "message": f"[SUCCESS] Found {count} projects!",
                    "sub_agent": "bid-card-finder",
                    "status": "completed"
                }
                
                yield {
                    "type": "bid_cards_found",
                    "bid_cards": bid_cards,
                    "search_metadata": {
                        "count": count,
                        "radius": 30,
                        "contractor_zip": contractor_zip,
                        "project_type": project_type
                    }
                }
                
                # Generate confirmation message
                confirmation_msg = await search_agent.generate_confirmation_message(
                    matched_cards=bid_cards[:5],
                    borderline_cards=[],
                    contractor_search=input_data
                )
                
                yield {
                    "type": "match_confirmation",
                    "message": confirmation_msg,
                    "has_matches": True,
                    "match_count": count
                }
            else:
                yield {
                    "type": "sub_agent_status",
                    "message": "[INFO] No matching projects found.",
                    "sub_agent": "bid-card-finder",
                    "status": "no_results"
                }
            
            # Exit early - we've handled the request
            return
        
        # If API is available, try to use it
        try:
            # Send sub-agent status message
            yield {
                "type": "sub_agent_status",
                "message": "[BOT] Analyzing your search request with AI...",
                "sub_agent": "intelligent-search",
                "status": "starting"
            }
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        intelligent_search_url,
                        json={
                            "message": input_data,
                            "contractor_id": contractor_id,
                            "session_id": session_id
                        },
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as resp:
                        if resp.status == 200:
                            search_result = await resp.json()
                            
                            if search_result.get("success"):
                                # Extract search understanding
                                understanding = search_result.get("search_understanding", {})
                                bid_cards = search_result.get("bid_cards", [])
                                suggestions = search_result.get("suggestions", {})
                                
                                # Show what we're searching for
                                search_explanation = understanding.get("search_explanation", "Searching for relevant projects...")
                                
                                # Extract location info for radius confirmation
                                location = understanding.get("location", {})
                                search_zip = location.get("zip", "your location")
                                search_radius = location.get("radius_miles", 30)
                                
                                yield {
                                    "type": "sub_agent_status",
                                    "message": f"[SEARCH] {search_explanation}",
                                    "sub_agent": "intelligent-search", 
                                    "status": "searching"
                                }
                                
                                # Add radius confirmation
                                yield {
                                    "type": "radius_info",
                                    "message": f"📍 Searching within {search_radius} miles of ZIP {search_zip}. Would you like to adjust the search distance?",
                                    "current_radius": search_radius,
                                    "current_zip": search_zip
                                }
                                
                                # Show expanded search terms
                                project_types = understanding.get("project_types", [])
                                if project_types:
                                    yield {
                                        "type": "sub_agent_status",
                                        "message": f"[EXPAND] Searching for: {', '.join(project_types[:3])}...",
                                        "sub_agent": "intelligent-search",
                                        "status": "expanding"
                                    }
                                
                                # If we found bid cards, return them
                                if bid_cards:
                                    yield {
                                        "type": "sub_agent_status",
                                        "message": f"[SUCCESS] Found {len(bid_cards)} relevant projects!",
                                        "sub_agent": "intelligent-search",
                                        "status": "completed"
                                    }
                                    
                                    # Check if we have semantic match info
                                    has_semantic = any(card.get("match_info") for card in bid_cards)
                                    
                                    yield {
                                        "type": "bid_cards_found",
                                        "bid_cards": bid_cards,
                                        "search_metadata": {
                                            "count": len(bid_cards),
                                            "searched_types": project_types,
                                            "keywords": understanding.get("keywords", []),
                                            "semantic_matching": has_semantic
                                        }
                                    }
                                    
                                    # Generate and send confirmation message using DeepAgents
                                    from agents.bsa.sub_agents.bid_card_search_agent import BidCardSearchAgent
                                    
                                    # Get borderline cards if any
                                    borderline_cards = search_result.get("borderline_cards", [])
                                    
                                    # Initialize DeepAgents sub-agent for confirmation message
                                    search_agent = BidCardSearchAgent()
                                    confirmation_msg = await search_agent.generate_confirmation_message(
                                        matched_cards=bid_cards[:5],
                                        borderline_cards=borderline_cards[:3],
                                        contractor_search=input_data
                                    )
                                    
                                    yield {
                                        "type": "match_confirmation",
                                        "message": confirmation_msg,
                                        "has_matches": True,
                                        "match_count": len(bid_cards),
                                        "borderline_count": len(borderline_cards)
                                    }
                                    
                                    # Send borderline questions separately if they exist
                                    if borderline_cards:
                                        borderline_questions = []
                                        for card in borderline_cards[:3]:
                                            match_info = card.get("match_info", {})
                                            question = match_info.get("clarifying_question")
                                            if question:
                                                borderline_questions.append({
                                                    "card_title": card.get("title", "Project"),
                                                    "question": question,
                                                    "relevance": match_info.get("relevance_score", 50)
                                                })
                                        
                                        if borderline_questions:
                                            yield {
                                                "type": "borderline_questions",
                                                "questions": borderline_questions,
                                                "message": "I also found some projects that might be relevant:"
                                            }
                                    
                                    # Include additional clarifying questions if available
                                    clarifying_questions = suggestions.get("clarifying_questions", [])
                                    if clarifying_questions:
                                        yield {
                                            "type": "clarifying_questions",
                                            "questions": clarifying_questions,
                                            "message": "To help refine future searches:"
                                        }
                                else:
                                    # No results found, suggest alternatives
                                    yield {
                                        "type": "sub_agent_status",
                                        "message": "[INFO] No exact matches found. Let me suggest alternatives...",
                                        "sub_agent": "intelligent-search",
                                        "status": "no_results"
                                    }
                                    
                                    # Suggest related services
                                    related_services = suggestions.get("related_services", [])
                                    if related_services:
                                        yield {
                                            "type": "related_services",
                                            "services": related_services,
                                            "message": f"You might also be interested in: {', '.join(related_services[:3])}"
                                        }
                        else:
                            # Fall back to basic search if intelligent search fails
                            logger.warning(f"Intelligent search returned status {resp.status}")
                            # Fall back to hardcoded search  
                            contractor_zip = "78701"
                            project_type = None
                            if "kitchen" in input_data.lower():
                                project_type = "kitchen"
                            elif "bathroom" in input_data.lower():
                                project_type = "bathroom"
                            elif "landscaping" in input_data.lower() or "lawn" in input_data.lower() or "turf" in input_data.lower():
                                project_type = "landscaping"
                            
                            yield {
                                "type": "sub_agent_status",
                                "message": f"[FALLBACK] Using basic search for {project_type or 'all'} projects...",
                                "sub_agent": "bid-card-finder",
                                "status": "searching"
                            }
                            
                            # Fall back to basic search using DeepAgents
                            search_agent = BidCardSearchAgent()
                            
                            # First send radius info for fallback search
                            yield {
                                "type": "radius_info",
                                "message": f"📍 Searching within 30 miles of ZIP {contractor_zip}. Would you like to adjust the search distance?",
                                "current_radius": 30,
                                "current_zip": contractor_zip
                            }
                            
                            bid_cards_result = await search_agent.search_bid_cards_in_radius(
                                contractor_zip=contractor_zip,
                                radius_miles=30,
                                project_type=project_type,
                                use_semantic_matching=True  # Still try semantic matching
                            )
                            
                            if bid_cards_result.get('success') and bid_cards_result.get('bid_cards'):
                                count = bid_cards_result.get('count', 0)
                                bid_cards = bid_cards_result.get('bid_cards', [])
                                borderline = bid_cards_result.get('borderline_cards', [])
                            
                                yield {
                                    "type": "sub_agent_status",
                                    "message": f"[SUCCESS] Found {count} projects!",
                                    "sub_agent": "bid-card-finder",
                                    "status": "completed"
                                }
                                
                                yield {
                                    "type": "bid_cards_found",
                                    "bid_cards": bid_cards,
                                    "search_metadata": {
                                        "count": count,
                                        "radius": 30,
                                        "contractor_zip": contractor_zip,
                                        "project_type": project_type,
                                        "semantic_matching": bid_cards_result.get('semantic_matching', False)
                                    }
                                }
                                
                                # Generate confirmation for fallback results too using DeepAgents
                                search_agent = BidCardSearchAgent() 
                                
                                confirmation_msg = await search_agent.generate_confirmation_message(
                                    matched_cards=bid_cards[:5],
                                    borderline_cards=borderline[:3],
                                    contractor_search=input_data
                                )
                                
                                yield {
                                    "type": "match_confirmation",
                                    "message": confirmation_msg,
                                    "has_matches": True,
                                    "match_count": count,
                                    "borderline_count": len(borderline)
                                }
                            else:
                                yield {
                                    "type": "sub_agent_status",
                                    "message": "[INFO] No matching projects found in your area.",
                                    "sub_agent": "bid-card-finder",
                                    "status": "no_results"
                                }
                                
                                yield {
                                    "type": "match_confirmation",
                                    "message": "I couldn't find any projects matching your criteria within 30 miles. Would you like to:\n1. Expand the search radius to 50 miles?\n2. Try different search terms?\n3. Get notified when new matching projects are posted?",
                                    "has_matches": False,
                                    "match_count": 0,
                                    "borderline_count": 0
                                }
                            
                except aiohttp.ClientError as e:
                    # Network error - fall back to basic search
                    logger.error(f"Intelligent search API error: {e}")
                    yield {
                        "type": "sub_agent_status",
                        "message": "[FALLBACK] API unavailable, using direct search...",
                        "sub_agent": "bid-card-finder",
                        "status": "fallback"
                    }
                    
                    # Extract ZIP code from input if available
                    import re
                    zip_match = re.search(r'\b(\d{5})\b', input_data)
                    contractor_zip = zip_match.group(1) if zip_match else "33442"
                    
                    # Determine project type from input
                    project_type = None
                    if "kitchen" in input_data.lower():
                        project_type = "kitchen"
                    elif "bathroom" in input_data.lower():
                        project_type = "bathroom"
                    elif "landscaping" in input_data.lower() or "lawn" in input_data.lower() or "turf" in input_data.lower():
                        project_type = "landscaping"
                    
                    # Fall back to basic search using BSA tools
                    from agents.bsa.sub_agents.bid_card_search_agent import BidCardSearchAgent
                    search_agent = BidCardSearchAgent()
                    
                    # Send radius info
                    yield {
                        "type": "radius_info",
                        "message": f"Searching within 30 miles of ZIP {contractor_zip}",
                        "current_radius": 30,
                        "current_zip": contractor_zip
                    }
                    
                    # Search for bid cards
                    bid_cards_result = await search_agent.search_bid_cards_in_radius(
                        contractor_zip=contractor_zip,
                        radius_miles=30,
                        project_type=project_type,
                        use_semantic_matching=True
                    )
                    
                    if bid_cards_result.get('success') and bid_cards_result.get('bid_cards'):
                        count = bid_cards_result.get('count', 0)
                        bid_cards = bid_cards_result.get('bid_cards', [])
                        
                        yield {
                            "type": "sub_agent_status",
                            "message": f"[SUCCESS] Found {count} projects!",
                            "sub_agent": "bid-card-finder",
                            "status": "completed"
                        }
                        
                        yield {
                            "type": "bid_cards_found",
                            "bid_cards": bid_cards,
                            "search_metadata": {
                                "count": count,
                                "radius": 30,
                                "contractor_zip": contractor_zip,
                                "project_type": project_type
                            }
                        }
                        
                        # Generate confirmation message
                        confirmation_msg = await search_agent.generate_confirmation_message(
                            matched_cards=bid_cards[:5],
                            borderline_cards=[],
                            contractor_search=input_data
                        )
                        
                        yield {
                            "type": "match_confirmation",
                            "message": confirmation_msg,
                            "has_matches": True,
                            "match_count": count
                        }
                    else:
                        yield {
                            "type": "sub_agent_status",
                            "message": "[INFO] No matching projects found.",
                            "sub_agent": "bid-card-finder",
                            "status": "no_results"
                        }
                
        except Exception as e:
            # Send error status
            yield {
                "type": "sub_agent_status",
                "message": f"[ERROR] Sub-agent error: {str(e)}",
                "sub_agent": "bid-card-finder",
                "status": "error"
            }
            
            # Log error but continue with normal conversation
            import logging
            logging.error(f"Sub-agent bid card search failed: {e}")
    
    # Construct specialized BSA prompt based on input type
    if input_type == "voice":
        user_prompt = f"""
A contractor provided voice input for bid card {bid_card_id}:

Voice transcript: "{input_data}"
Contractor ID: {contractor_id}

As the BSA (Bid Submission Agent), please:
1. Extract pricing and timeline from their natural speech
2. Identify the trade type (kitchen, landscaping, electrical, general)
3. Generate a professional proposal based on their input
4. Provide structured bid data

Trade expertise: Apply specialized knowledge for the detected trade type.
"""
    
    elif input_type == "text":
        user_prompt = f"""
A contractor submitted text input for bid card {bid_card_id}:

Their input: "{input_data}"
Contractor ID: {contractor_id}

As the BSA (Bid Submission Agent), please:
1. Parse their text for pricing and timeline details
2. Identify the trade specialization needed
3. Generate a professional, detailed proposal
4. Structure the response for bid submission

Apply trade-specific expertise to enhance their input into a professional bid.
"""
    
    elif input_type == "pdf" or input_type == "document":
        user_prompt = f"""
A contractor uploaded an estimate/document for bid card {bid_card_id}:

Document content: "{input_data}"
Contractor ID: {contractor_id}

As the BSA (Bid Submission Agent), please:
1. Extract all pricing, timeline, and scope details from the document
2. Identify the trade type and apply specialized knowledge
3. Reformat into a professional InstaBids proposal
4. Ensure all key information is preserved and enhanced

Transform their document into a polished, professional bid proposal.
"""
    
    else:
        user_prompt = f"""
Contractor input for bid card {bid_card_id}:
Input: {input_data}
Contractor ID: {contractor_id}

As the BSA, process this into a professional bid proposal with pricing and timeline.
"""
    
    # BSA System Prompt with trade expertise
    system_prompt = f"""You are the Bid Submission Agent (BSA) for InstaBids. You help contractors transform their casual input into professional, structured bid proposals.

## Your Role:
Transform contractor natural language input (voice, text, documents) into polished bid proposals that homeowners can easily evaluate.

## Trade Expertise:
- **Kitchen Remodeling**: Cabinet pricing ($150-300/linear ft), appliance packages, countertop materials, layout considerations
- **Landscaping**: Zone-based pricing, plant materials, hardscaping, irrigation, seasonal factors  
- **Electrical**: Service upgrades, fixture counts, permit costs, code compliance
- **General Construction**: Additions, remodels, repairs, material calculations

## Your Process:
1. **Extract Information**: Pull pricing, timeline, materials, approach from contractor input
2. **Apply Trade Knowledge**: Use specialized expertise for the detected trade type
3. **Generate Professional Proposal**: Create polished, detailed proposal text
4. **Structure Output**: Format for InstaBids platform

## Output Format:
Provide a professional proposal including:
- Clear project overview and approach
- Detailed scope of work
- Materials and specifications
- Investment breakdown (labor + materials)
- Timeline with start/end dates
- Contractor qualifications and next steps

Be conversational yet professional. Enhance their input while maintaining their intended pricing and approach.
"""
    
    # Build messages array with conversation history
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history if available
    if conversation_history:
        print(f"BSA Agent: Received {len(conversation_history)} messages in conversation history")
        # Add previous messages for context (limit to last 10 for token management)
        for msg in conversation_history[-10:]:
            if isinstance(msg, dict):
                messages.append(msg)
            elif hasattr(msg, 'type') and hasattr(msg, 'content'):
                # Handle LangChain message format
                role = "assistant" if msg.type == "ai" else "user"
                messages.append({"role": role, "content": msg.content})
    
    # Add current user message
    messages.append({"role": "user", "content": user_prompt})
    
    logger.info(f"BSA: Sending {len(messages)} messages to OpenAI API")
    logger.info(f"BSA: System prompt length: {len(messages[0]['content']) if messages else 0}")
    logger.info(f"BSA: User prompt: {user_prompt[:200]}...")
    
    # Use GPT-4o (GPT-5 doesn't exist yet)
    try:
        logger.info("BSA: Using GPT-4o for completion...")
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            stream=True,
            max_completion_tokens=1500,
            temperature=0.7
        )
        model_used = "gpt-4o"
        logger.info("BSA: GPT-4o stream created successfully")
    except Exception as e:
        logger.error(f"BSA: GPT-4o failed: {e}")
        print(f"GPT-4o failed: {e}")
        # Try fallback model
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            stream=True,
            max_tokens=1500,
            temperature=0.7  # GPT-4o uses standard temperature
        )
        model_used = "gpt-4o"
        logger.info("BSA: GPT-4o stream created successfully")
    
    # Stream the response
    async for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            yield {
                "choices": [{"delta": {"content": chunk.choices[0].delta.content}}],
                "model": model_used
            }
    
    # End of stream marker
    yield {"choices": [{"delta": {"content": ""}}], "done": True, "model": model_used}

def process_contractor_input(
    bid_card_id: str,
    contractor_id: str,
    input_type: str,
    input_data: str,
    session_id: str = None
) -> Dict[str, Any]:
    """
    Main entry point for processing contractor bid submissions
    
    Args:
        bid_card_id: ID of the bid card being responded to
        contractor_id: ID of the contractor submitting
        input_type: "text", "voice", "pdf", "image"
        input_data: The actual input (text, transcript, file path, etc.)
        session_id: Optional session for multi-turn conversations
        
    Returns:
        Structured bid ready for submission to InstaBids API
    """
    
    # Create BSA agent
    agent = create_bsa_agent()
    
    # Construct the prompt based on input type
    if input_type == "voice":
        prompt = f"""A contractor just provided voice input for bid card {bid_card_id}.
        
Voice transcript: "{input_data}"

Contractor ID: {contractor_id}

Please:
1. Extract the pricing and timeline from their natural speech
2. Get the bid card details to understand requirements  
3. Get contractor profile for context
4. Generate a professional proposal
5. Return structured bid data ready for API submission"""
    
    elif input_type == "text":
        prompt = f"""A contractor submitted text input for bid card {bid_card_id}.
        
Their input: "{input_data}"

Contractor ID: {contractor_id}

Please:
1. Parse their text for pricing and timeline
2. Get bid card requirements
3. Use contractor profile for missing details
4. Generate professional proposal
5. Return structured bid for API submission"""
    
    elif input_type == "pdf":
        prompt = f"""A contractor uploaded their estimate/template for bid card {bid_card_id}.

File content is available as 'estimate.pdf' in the file system.

Contractor ID: {contractor_id}

Please:
1. Read the uploaded file
2. Extract pricing, timeline, and scope
3. Get bid card requirements to ensure alignment
4. Reformat into professional InstaBids proposal
5. Return structured bid for API submission"""
    
    else:  # General fallback
        prompt = f"""Process contractor input for bid card {bid_card_id}.
        
Input: {input_data}
Contractor ID: {contractor_id}

Generate a complete bid proposal."""
    
    # Prepare state with files if needed
    state = {
        "messages": [{"role": "user", "content": prompt}]
    }
    
    if input_type == "pdf":
        # In production, would extract PDF content first
        state["files"] = {"estimate.pdf": input_data}
    
    # Run the agent
    result = agent.invoke(state)
    
    # Extract the final structured bid from agent output
    # In production, would parse agent's response for the structured data
    
    return {
        "bid_card_id": bid_card_id,
        "contractor_id": contractor_id,
        "amount": 45000,  # Would be extracted from agent response
        "timeline_start": datetime.now() + timedelta(days=14),
        "timeline_end": datetime.now() + timedelta(weeks=8),
        "proposal": result["messages"][-1].content,
        "confidence_score": 0.85,
        "session_id": session_id
    }

# ============================================================================
# GROUP BIDDING COORDINATOR  
# ============================================================================

def process_group_bid(
    bid_card_ids: List[str],
    contractor_id: str,
    bulk_input: str
) -> List[Dict[str, Any]]:
    """
    Process contractor input for multiple related projects
    
    Args:
        bid_card_ids: List of bid cards to submit together
        contractor_id: Contractor submitting the group bid
        bulk_input: Contractor's input about the group
        
    Returns:
        List of structured bids, one per bid card
    """
    
    agent = create_bsa_agent()
    
    prompt = f"""A contractor wants to bid on {len(bid_card_ids)} related projects as a group.

Bid Cards: {', '.join(bid_card_ids)}
Contractor ID: {contractor_id}

Contractor's Input: "{bulk_input}"

Please:
1. Fetch details for all bid cards
2. Calculate bulk pricing with appropriate discounts
3. Optimize timeline by scheduling projects efficiently  
4. Generate coordinated proposals mentioning the group discount
5. Return structured bids for each project

Important: 
- Apply 10-15% bulk discount for 3+ projects
- Schedule projects to minimize mobilization costs
- Reference other projects in each proposal
"""
    
    result = agent.invoke({
        "messages": [{"role": "user", "content": prompt}]
    })
    
    # Parse and return list of bids
    # In production, would extract structured data from agent response
    
    return [
        {
            "bid_card_id": bid_id,
            "contractor_id": contractor_id,
            "amount": 40000,  # Would vary per project
            "proposal": f"Part of {len(bid_card_ids)}-project package...",
            "group_bid_id": f"group_{contractor_id}_{datetime.now().timestamp()}"
        }
        for bid_id in bid_card_ids
    ]

# ============================================================================
# TESTING & VALIDATION
# ============================================================================

if __name__ == "__main__":
    # Quick test of BSA agent
    print("Testing BSA Agent...")
    
    # Test text input
    test_result = process_contractor_input(
        bid_card_id="test-123",
        contractor_id="contractor-456",
        input_type="text",
        input_data="I can do this kitchen remodel for about 45k, should take me 8 weeks"
    )
    
    print("Test Result:", json.dumps(test_result, indent=2, default=str))