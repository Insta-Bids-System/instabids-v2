"""
Unified COIA LangGraph Implementation
Creates a single agent with multiple modes and conditional entry points
"""

import logging
from typing import Any, Optional

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .langgraph_nodes import conversation_node, intelligence_node, mode_detector_node, research_node
from .mcp_supabase_checkpointer import create_mcp_supabase_checkpointer
from .unified_state import UnifiedCoIAState, create_initial_state


logger = logging.getLogger(__name__)


class UnifiedCoIAGraph:
    """
    Unified COIA agent implemented as a LangGraph workflow
    Supports multiple entry points and dynamic mode switching
    """

    def __init__(self, checkpointer: Optional[BaseCheckpointSaver] = None):
        """Initialize the unified COIA graph"""
        self.checkpointer = checkpointer
        self.graph = None
        self.app = None

    async def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        if self.graph is not None:
            return self.graph

        logger.info("Building unified COIA graph...")

        # Create the state graph
        graph = StateGraph(UnifiedCoIAState)

        # Add nodes
        from .extraction_node import extraction_node
        graph.add_node("extraction", extraction_node)
        graph.add_node("mode_detector", mode_detector_node)
        graph.add_node("conversation", conversation_node)
        graph.add_node("research", research_node)
        graph.add_node("intelligence", intelligence_node)

        # Add bid card search node - FIXED VERSION with ZIP radius expansion
        from .bid_card_search_node_fixed import bid_card_search_node
        graph.add_node("bid_card_search", bid_card_search_node)
        
        # Add bid submission and account creation nodes with interrupts
        from .bid_submission_node import bid_submission_node, account_creation_node
        graph.add_node("bid_submission", bid_submission_node)
        graph.add_node("account_creation", account_creation_node)

        # Set conditional entry point based on interface and state
        graph.set_conditional_entry_point(
            self._determine_entry_point,
            {
                "extraction": "extraction",
                "conversation": "conversation",
                "research": "research",
                "intelligence": "intelligence",
                "mode_detector": "mode_detector",
                "bid_card_search": "bid_card_search"
            }
        )

        # Add edges from extraction node - always go to mode_detector after extraction
        graph.add_edge("extraction", "mode_detector")

        # Add conditional edges from mode_detector
        graph.add_conditional_edges(
            "mode_detector",
            self._route_from_mode_detector,
            {
                "conversation": "conversation",
                "research": "research",
                "intelligence": "intelligence",
                "bid_card_search": "bid_card_search",
                "end": END
            }
        )

        # Add conditional edges from conversation node
        graph.add_conditional_edges(
            "conversation",
            self._route_from_conversation,
            {
                "continue": "conversation",
                "research": "research",
                "intelligence": "intelligence",
                "bid_card_search": "bid_card_search",
                "mode_detector": "mode_detector",
                "account_creation": "account_creation",
                "end": END
            }
        )

        # Add conditional edges from research node
        graph.add_conditional_edges(
            "research",
            self._route_from_research,
            {
                "conversation": "conversation",
                "intelligence": "intelligence",
                "mode_detector": "mode_detector",
                "end": END
            }
        )

        # Add conditional edges from intelligence node
        graph.add_conditional_edges(
            "intelligence",
            self._route_from_intelligence,
            {
                "conversation": "conversation",
                "mode_detector": "mode_detector",
                "end": END
            }
        )

        # Add conditional edges from bid card search node
        graph.add_conditional_edges(
            "bid_card_search",
            self._route_from_bid_card_search,
            {
                "conversation": "conversation",
                "bid_card_search": "bid_card_search",
                "mode_detector": "mode_detector",
                "end": END
            }
        )

        self.graph = graph
        logger.info("Unified COIA graph built successfully")
        return graph

    async def compile(self) -> Any:
        """Compile the graph into an executable application"""
        if self.app is not None:
            return self.app

        if self.graph is None:
            await self.build_graph()

        # Use provided checkpointer or create fallback
        checkpointer = self.checkpointer
        if checkpointer is None:
            try:
                # Try to create REST-based Supabase checkpointer
                checkpointer = await create_mcp_supabase_checkpointer()
                logger.info("Using Supabase REST checkpointer for state persistence")
            except Exception as e:
                logger.warning(f"Failed to initialize Supabase REST checkpointer: {e}")
                logger.info("Falling back to in-memory checkpointer")
                checkpointer = MemorySaver()

        # Compile the graph with interrupt points for human review
        self.app = self.graph.compile(
            checkpointer=checkpointer,
            interrupt_before=["bid_submission", "account_creation"],  # Human review points
            debug=True  # Enable debug mode for better visibility
        )
        logger.info("Unified COIA graph compiled successfully with interrupt points")
        return self.app

    def _determine_entry_point(self, state: UnifiedCoIAState) -> str:
        """
        Determine entry point based on interface and current state
        This enables different interfaces to start in different modes
        """
        try:
            interface = state.get("interface", "chat")
            current_mode = state.get("current_mode", "conversation")
            company_name = state.get("company_name", "")
            extraction_completed = state.get("extraction_completed", False)

            logger.info(f"Determining entry point - Interface: {interface}, Mode: {current_mode}")
            logger.info(f"Company name: '{company_name}', Extraction completed: {extraction_completed}")

            # PRIORITY 1: Check if we need to run extraction first
            # For any new messages without company name, always start with extraction
            messages = state.get("messages", [])
            if messages and not company_name and not extraction_completed:
                logger.info("🧠 New message without company name - routing to extraction node first")
                return "extraction"

            # PRIORITY 2: Interface-based entry points
            if interface == "landing_page":
                # Landing page: Check if we have company name and should research
                if company_name:
                    logger.info(f"Landing page with company name '{company_name}' - enabling mode detector for research")
                    return "mode_detector"  # Let mode detector decide research vs conversation
                else:
                    # No company name yet - start with extraction to collect info
                    logger.info("Landing page without company name - routing to extraction first")
                    return "extraction"
                
            elif interface == "research_portal":
                # Research portal should start in research mode if company name available
                if company_name:
                    return "research"
                else:
                    return "extraction"  # Need to extract company info first

            elif interface == "intelligence_dashboard":
                # Intelligence dashboard should start in intelligence mode if data available
                if company_name and (state.get("business_info") or state.get("research_completed")):
                    return "intelligence"
                else:
                    return "mode_detector"  # Let mode detector decide next step

            elif interface == "chat":
                # Chat interface: Check if extraction needed first, otherwise use mode detector
                if messages and not company_name and not extraction_completed:
                    logger.info("Chat interface new message - routing to extraction first")
                    return "extraction"
                else:
                    # Already extracted or continuing conversation - use mode detector for smart routing
                    return "mode_detector"

            # Default: If we have messages but no extraction, do extraction first
            if messages and not extraction_completed:
                logger.info("Default case with messages - routing to extraction first")
                return "extraction"
            
            # Final fallback
            return "conversation"

        except Exception as e:
            logger.error(f"Error in entry point determination: {e}")
            return "conversation"  # Safe fallback

    def _route_from_mode_detector(self, state: UnifiedCoIAState) -> str:
        """Route from mode detector to appropriate node"""
        try:
            # Check the mode detector's decision first
            mode_decision = state.get("mode_detector_decision", state.get("current_mode", "conversation"))

            logger.info(f"Routing from mode detector: decision = {mode_decision}")

            # Check for completion
            if state.get("completion_ready") or state.get("contractor_created"):
                return "end"

            # Route to appropriate mode based on mode detector decision
            if mode_decision == "research":
                return "research"
            elif mode_decision == "intelligence":
                return "intelligence"
            elif mode_decision == "bid_card_search":
                return "bid_card_search"
            else:
                return "conversation"

        except Exception as e:
            logger.error(f"Error routing from mode detector: {e}")
            return "conversation"

    def _route_from_conversation(self, state: UnifiedCoIAState) -> str:
        """Route from conversation node based on response"""
        try:
            # LANDING PAGE: Check if company name was extracted and we should trigger research FIRST
            interface = state.get("interface", "chat")
            if interface == "landing_page":
                company_name = state.get("company_name")
                research_completed = state.get("research_completed", False)
                contractor_created = state.get("contractor_created", False)
                account_creation_confirmed = state.get("account_creation_confirmed", False)
                mode_detector_visits = state.get("mode_detector_visits", 0)
                
                # Priority 0: Check if user confirmed account creation
                if account_creation_confirmed and research_completed and not contractor_created:
                    logger.info(f"✅ LANDING PAGE: Account creation confirmed - routing to account_creation")
                    return "account_creation"
                
                # Priority 1: Check if user is asking for bid cards BEFORE defaulting to research
                messages = state.get("messages", [])
                if messages:
                    last_message = messages[-1].content.lower() if hasattr(messages[-1], "content") else str(messages[-1]).lower()
                    # Check for bid card search triggers (removed "work" to allow research flow)
                    bid_triggers = ["show me", "projects", "available", "bid", "opportunities", "jobs"]
                    if any(trigger in last_message for trigger in bid_triggers):
                        logger.info(f"🔍 LANDING PAGE: Bid card search requested - routing to mode_detector")
                        return "mode_detector"  # Let mode detector route to bid_card_search
                
                # Priority 2: Research if company name extracted and not done yet
                # BUT prevent infinite loops by limiting mode_detector visits
                if company_name and not research_completed and not contractor_created and mode_detector_visits < 3:
                    logger.info(f"🎯 LANDING PAGE: Company '{company_name}' extracted - triggering research")
                    return "research"  # Go directly to research, don't route through mode_detector
                
                # Priority 2: Extract company name first if not available
                if not company_name and not research_completed and mode_detector_visits < 3:
                    logger.info(f"🎯 LANDING PAGE: No company name yet - staying in conversation to extract")
                    return "end"  # Stay in conversation mode
                
                # Priority 3: End if contractor already created
                if contractor_created:
                    logger.info(f"✅ LANDING PAGE: Contractor created - ending conversation")
                    return "end"

            # Check for completion FIRST to prevent loops
            if state.get("completion_ready") or state.get("contractor_created"):
                logger.info("Conversation complete - ending")
                return "end"

            # Check for mode transitions - but limit to prevent loops
            current_mode = state.get("current_mode", "conversation")
            mode_detector_visits = state.get("mode_detector_visits", 0)

            # If mode changed to specific modes, route directly
            if current_mode == "research":
                return "research"
            elif current_mode == "intelligence":
                return "intelligence"
            elif current_mode == "bid_card_search":
                return "bid_card_search"

            # Check for error state
            if state.get("error_state"):
                logger.warning(f"Error state detected: {state.get('error_state')}")
                return "end"

            # Allow conversation to continue even with high mode_detector_visits 
            # since conversation node handles Stage 2 detection
            if current_mode == "conversation":
                logger.info("Conversation mode detected - allowing conversation to continue")
                return "continue"

            # Prevent infinite loops by limiting mode transitions
            if mode_detector_visits >= 8:  # Increased limit to allow more conversation turns
                logger.warning(f"Too many mode_detector visits ({mode_detector_visits}) - ending conversation to prevent infinite loop")
                return "end"

            # Default: Allow conversation to continue
            logger.info("Routing: defaulting to continue conversation")
            return "continue"

        except Exception as e:
            logger.error(f"Error routing from conversation: {e}")
            return "end"

    def _route_from_research(self, state: UnifiedCoIAState) -> str:
        """Route from research node based on results"""
        try:
            # Check for completion
            if state.get("completion_ready") or state.get("contractor_created"):
                return "end"

            # Check current mode after research
            current_mode = state.get("current_mode", "conversation")

            if current_mode == "intelligence":
                return "intelligence"
            elif current_mode == "conversation":
                return "conversation"
            else:
                return "mode_detector"

        except Exception as e:
            logger.error(f"Error routing from research: {e}")
            return "conversation"

    def _route_from_bid_card_search(self, state: UnifiedCoIAState) -> str:
        """Route from bid card search node based on user interaction"""
        try:
            # Check if user wants to continue searching
            messages = state.get("messages", [])
            if messages and len(messages) > 2:  # Only check for continuation if there are multiple messages
                last_message = messages[-1].content.lower() if hasattr(messages[-1], "content") else str(messages[-1]).lower()

                # User wants more results or different search (but only for follow-up messages)
                if any(keyword in last_message for keyword in ["more", "filter", "different", "other"]):
                    return "bid_card_search"

                # User wants to bid or get details
                if any(keyword in last_message for keyword in ["bid", "details", "tell me about"]):
                    return "end"  # End to prevent loops, user can start new conversation

                # User switching topics
                if any(keyword in last_message for keyword in ["profile", "website", "business"]):
                    return "end"  # End to prevent loops

            # Check completion status
            if state.get("completion_ready"):
                return "end"

            # Default to end for bid card search completion
            return "end"

        except Exception as e:
            logger.error(f"Error routing from bid card search: {e}")
            return "end"

    def _route_from_intelligence(self, state: UnifiedCoIAState) -> str:
        """Route from intelligence node based on results"""
        try:
            # Check for completion
            if state.get("completion_ready") or state.get("contractor_created"):
                return "end"

            # Intelligence typically returns to conversation
            current_mode = state.get("current_mode", "conversation")

            if current_mode == "conversation":
                return "conversation"
            else:
                return "mode_detector"

        except Exception as e:
            logger.error(f"Error routing from intelligence: {e}")
            return "conversation"


# Factory functions for different interface types
async def create_landing_page_interface_graph(checkpointer: Optional[BaseCheckpointSaver] = None) -> Any:
    """Create COIA graph optimized for landing page onboarding (unauthenticated)"""
    graph = UnifiedCoIAGraph(checkpointer)
    return await graph.compile()


async def create_chat_interface_graph(checkpointer: Optional[BaseCheckpointSaver] = None) -> Any:
    """Create COIA graph optimized for chat interface (authenticated)"""
    graph = UnifiedCoIAGraph(checkpointer)
    return await graph.compile()


async def create_research_interface_graph(checkpointer: Optional[BaseCheckpointSaver] = None) -> Any:
    """Create COIA graph optimized for research portal interface"""
    graph = UnifiedCoIAGraph(checkpointer)
    return await graph.compile()


async def create_intelligence_interface_graph(checkpointer: Optional[BaseCheckpointSaver] = None) -> Any:
    """Create COIA graph optimized for intelligence dashboard interface"""
    graph = UnifiedCoIAGraph(checkpointer)
    return await graph.compile()


# Main interface for creating the unified COIA system
async def create_unified_coia_system(checkpointer: Optional[BaseCheckpointSaver] = None) -> Any:
    """
    Create the unified COIA system that can handle all interfaces
    This is the main entry point for the consolidated agent
    """
    logger.info("Creating unified COIA system...")

    try:
        graph = UnifiedCoIAGraph(checkpointer)
        app = await graph.compile()

        logger.info("Unified COIA system created successfully")
        return app

    except Exception as e:
        logger.error(f"Failed to create unified COIA system: {e}")
        raise


# Helper functions for invoking the unified system
async def invoke_coia_chat(
    app: Any,
    user_message: str,
    session_id: str,
    contractor_lead_id: Optional[str] = None,
    project_id: Optional[str] = None
) -> dict[str, Any]:
    """Invoke COIA for chat interface"""

    # Use contractor_lead_id for persistent memory across sessions
    # Fall back to session_id if contractor_lead_id not available
    thread_id = contractor_lead_id if contractor_lead_id else session_id

    config = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_id": f"chat_{thread_id}",  # Proper checkpoint ID
            "checkpoint_ns": "coia_chat"
        },
        "recursion_limit": 50,  # Prevent infinite loops
        "max_concurrency": 10   # Limit parallel execution
    }

    # Create user message
    from langchain_core.messages import HumanMessage

    # Try to get existing state first, or create initial state if new session
    try:
        # Check if there's existing state by getting the current checkpoint
        existing_state = await app.aget_state(config)

        if existing_state and existing_state.values:
            # Session exists - add the new message to existing state
            logger.info(f"Continuing existing session for {thread_id}")
            # Get the complete existing state and add new message
            input_data = existing_state.values.copy()
            existing_messages = input_data.get("messages", [])
            input_data["messages"] = existing_messages + [HumanMessage(content=user_message)]
        else:
            # New session - create initial state
            logger.info(f"Creating new session for {thread_id}")
            initial_state = create_initial_state(
                session_id=session_id,
                interface="chat",
                contractor_lead_id=contractor_lead_id,
                original_project_id=project_id
            ).to_langgraph_state()

            # Add the user message to initial state
            initial_state["messages"] = [HumanMessage(content=user_message)]
            input_data = initial_state

    except Exception as e:
        # Fallback to creating new session if state retrieval fails
        logger.warning(f"Could not retrieve existing state for {thread_id}: {e}")
        logger.info(f"Creating new session for {thread_id}")
        initial_state = create_initial_state(
            session_id=session_id,
            interface="chat",
            contractor_lead_id=contractor_lead_id,
            original_project_id=project_id
        ).to_langgraph_state()

        # Add the user message to initial state
        initial_state["messages"] = [HumanMessage(content=user_message)]
        input_data = initial_state

    result = await app.ainvoke(input_data, config)
    return result


async def invoke_coia_research(
    app: Any,
    company_data: dict[str, Any],
    session_id: str
) -> dict[str, Any]:
    """Invoke COIA for research portal interface"""

    config = {
        "configurable": {
            "thread_id": session_id,
            "checkpoint_id": f"research_{session_id}",
            "checkpoint_ns": "coia_research"
        },
        "recursion_limit": 50,
        "max_concurrency": 10
    }

    initial_state = create_initial_state(
        session_id=session_id,
        interface="research_portal"
    ).to_langgraph_state()

    # Set company data for research
    initial_state["company_name"] = company_data.get("name")
    initial_state["company_website"] = company_data.get("website")
    initial_state["business_info"] = company_data

    from langchain_core.messages import HumanMessage
    initial_state["messages"] = [HumanMessage(content=f"Research company: {company_data.get('name')}")]

    result = await app.ainvoke(initial_state, config)
    return result


async def invoke_coia_intelligence(
    app: Any,
    contractor_data: dict[str, Any],
    session_id: str
) -> dict[str, Any]:
    """Invoke COIA for intelligence dashboard interface"""

    config = {
        "configurable": {
            "thread_id": session_id,
            "checkpoint_id": f"intelligence_{session_id}",
            "checkpoint_ns": "coia_intelligence"
        },
        "recursion_limit": 50,
        "max_concurrency": 10
    }

    initial_state = create_initial_state(
        session_id=session_id,
        interface="intelligence_dashboard"
    ).to_langgraph_state()

    # Set contractor data for intelligence processing
    initial_state["company_name"] = contractor_data.get("company_name")
    initial_state["contractor_profile"] = contractor_data
    initial_state["business_info"] = contractor_data.get("business_info", {})
    initial_state["research_completed"] = bool(contractor_data.get("research_data"))

    from langchain_core.messages import HumanMessage
    initial_state["messages"] = [HumanMessage(content=f"Enhance intelligence for: {contractor_data.get('company_name')}")]

    result = await app.ainvoke(initial_state, config)
    return result


async def invoke_coia_landing_page(
    app: Any,
    user_message: str,
    session_id: str,
    contractor_lead_id: Optional[str] = None
) -> dict[str, Any]:
    """Invoke COIA for landing page interface (unauthenticated onboarding)"""
    
    # Import state manager for persistence
    from agents.coia.state_management.state_manager import get_state_manager
    
    # Generate contractor_lead_id if not provided
    if not contractor_lead_id:
        import uuid
        contractor_lead_id = f"landing-{uuid.uuid4().hex[:12]}"
    
    # Always use contractor_lead_id as thread for persistent memory
    thread_id = contractor_lead_id
    
    # Get state manager and restore saved state
    state_manager = await get_state_manager()
    saved_state = await state_manager.restore_state(contractor_lead_id)
    
    config = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_ns": "coia_landing"
        },
        "recursion_limit": 50,
        "max_concurrency": 10
    }
    
    # Create user message
    from langchain_core.messages import HumanMessage
    
    # Try to get existing state first
    try:
        existing_state = await app.aget_state(config)
        
        if existing_state and existing_state.values:
            # Continuing existing onboarding session
            logger.info(f"Continuing landing page session for {thread_id}")
            input_data = existing_state.values.copy()
            existing_messages = input_data.get("messages", [])
            input_data["messages"] = existing_messages + [HumanMessage(content=user_message)]
            # Ensure interface stays as landing_page
            input_data["interface"] = "landing_page"
            
            # MERGE RESTORED STATE FROM UNIFIED MEMORY
            if saved_state:
                logger.info(f"✅ Merging {len(saved_state)} restored state fields")
                for key, value in saved_state.items():
                    if key not in input_data or not input_data[key]:
                        input_data[key] = value
        else:
            # New onboarding session
            logger.info(f"Creating new landing page session for {thread_id}")
            initial_state = create_initial_state(
                session_id=session_id,
                interface="landing_page",  # Critical: Set to landing_page
                contractor_lead_id=contractor_lead_id
            ).to_langgraph_state()
            
            # INJECT RESTORED STATE INTO INITIAL STATE
            if saved_state:
                logger.info(f"✅ Injecting {len(saved_state)} restored state fields into new session")
                logger.info(f"   Restored company: {saved_state.get('company_name')}")
                for key, value in saved_state.items():
                    initial_state[key] = value
            
            initial_state["messages"] = [HumanMessage(content=user_message)]
            input_data = initial_state
            
    except Exception as e:
        logger.warning(f"Could not retrieve existing state for {thread_id}: {e}")
        logger.info(f"Creating new landing page session for {thread_id}")
        initial_state = create_initial_state(
            session_id=session_id,
            interface="landing_page",  # Critical: Set to landing_page
            contractor_lead_id=contractor_lead_id
        ).to_langgraph_state()
        
        initial_state["messages"] = [HumanMessage(content=user_message)]
        input_data = initial_state
    
    result = await app.ainvoke(input_data, config)
    return result


async def invoke_coia_bid_card_link(
    app: Any,
    user_message: str,
    session_id: str,
    contractor_lead_id: Optional[str] = None,
    verification_token: Optional[str] = None,
    source_channel: Optional[str] = None
) -> dict[str, Any]:
    """Invoke COIA for bid card link interface (direct bid card access)"""
    
    logger.info(f"🎯 Bid card link invoked - Contractor: {contractor_lead_id}")
    
    # Generate contractor_lead_id if not provided
    if not contractor_lead_id:
        import uuid
        contractor_lead_id = f"bidcard-{uuid.uuid4().hex[:12]}"
        logger.warning(f"No contractor_lead_id provided, generated: {contractor_lead_id}")
    
    # Always use contractor_lead_id as thread for persistent memory
    thread_id = contractor_lead_id
    
    config = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_id": f"bidcard_{thread_id}",
            "checkpoint_ns": "coia_bidcard"
        },
        "recursion_limit": 50,
        "max_concurrency": 10
    }
    
    # CRITICAL: Load contractor's full context when they click the bid card link!
    contractor_context = {}
    company_name = ""
    
    if contractor_lead_id and not contractor_lead_id.startswith("bidcard-"):
        try:
            from adapters.contractor_context import ContractorContextAdapter
            adapter = ContractorContextAdapter()
            contractor_context = adapter.get_contractor_context(contractor_lead_id, session_id)
            
            logger.info(f"✅ Loaded contractor context for {contractor_lead_id}")
            company_name = contractor_context.get("contractor_profile", {}).get("company_name", "")
            logger.info(f"  - Company: {company_name}")
            logger.info(f"  - Profile loaded: {bool(contractor_context.get('contractor_profile'))}")
            logger.info(f"  - Bid history: {len(contractor_context.get('bid_history', []))} bids")
        except Exception as e:
            logger.error(f"Error loading contractor context: {e}")
    
    # Create user message
    from langchain_core.messages import HumanMessage
    
    # Try to get existing state first
    try:
        existing_state = await app.aget_state(config)
        
        if existing_state and existing_state.values:
            # Continuing existing bid card session
            logger.info(f"Continuing bid card session for {thread_id}")
            input_data = existing_state.values.copy()
            existing_messages = input_data.get("messages", [])
            input_data["messages"] = existing_messages + [HumanMessage(content=user_message)]
        else:
            # New bid card session - PRELOAD CONTRACTOR CONTEXT!
            logger.info(f"Creating new bid card session for {thread_id} with PRELOADED CONTEXT")
            initial_state = create_initial_state(
                session_id=session_id,
                interface="bid_card_link",  # CRITICAL: Use bid_card_link interface for proper prompt
                contractor_lead_id=contractor_lead_id
            ).to_langgraph_state()
            
            # PRELOAD ALL CONTRACTOR CONTEXT INTO STATE FOR FIRST TURN
            if contractor_context:
                initial_state["contractor_profile"] = contractor_context.get("contractor_profile", {})
                initial_state["company_name"] = company_name
                initial_state["bid_history"] = contractor_context.get("bid_history", [])
                initial_state["submitted_bids"] = contractor_context.get("submitted_bids", [])
                initial_state["conversation_history"] = contractor_context.get("conversation_history", [])
                initial_state["available_projects"] = contractor_context.get("available_projects", [])
                initial_state["persistent_memory_loaded"] = True
                logger.info(f"✅ Preloaded full contractor context into state")
            
            # Set bid card specific data
            initial_state["verification_token"] = verification_token
            initial_state["source_channel"] = source_channel
            initial_state["messages"] = [HumanMessage(content=user_message)]
            input_data = initial_state
            
    except Exception as e:
        logger.warning(f"Could not retrieve existing state for {thread_id}: {e}")
        logger.info(f"Creating new bid card session for {thread_id} with PRELOADED CONTEXT")
        initial_state = create_initial_state(
            session_id=session_id,
            interface="bid_card_link",  # CRITICAL: Use bid_card_link interface for proper prompt
            contractor_lead_id=contractor_lead_id
        ).to_langgraph_state()
        
        # PRELOAD ALL CONTRACTOR CONTEXT INTO STATE FOR FIRST TURN
        if contractor_context:
            initial_state["contractor_profile"] = contractor_context.get("contractor_profile", {})
            initial_state["company_name"] = company_name
            initial_state["bid_history"] = contractor_context.get("bid_history", [])
            initial_state["submitted_bids"] = contractor_context.get("submitted_bids", [])
            initial_state["conversation_history"] = contractor_context.get("conversation_history", [])
            initial_state["available_projects"] = contractor_context.get("available_projects", [])
            initial_state["persistent_memory_loaded"] = True
            logger.info(f"✅ Preloaded full contractor context into state")
        
        # Set bid card specific data
        initial_state["verification_token"] = verification_token
        initial_state["source_channel"] = source_channel
        initial_state["messages"] = [HumanMessage(content=user_message)]
        input_data = initial_state
    
    result = await app.ainvoke(input_data, config)
    return result


# Export main functions
__all__ = [
    "UnifiedCoIAGraph",
    "create_landing_page_interface_graph",
    "create_chat_interface_graph",
    "create_intelligence_interface_graph",
    "create_research_interface_graph",
    "create_unified_coia_system",
    "invoke_coia_landing_page",
    "invoke_coia_chat",
    "invoke_coia_intelligence",
    "invoke_coia_research",
    "invoke_coia_bid_card_link"
]
