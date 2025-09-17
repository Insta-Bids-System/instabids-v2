"""
BSA Singleton Implementation with LangGraph Checkpointing
Implements proper graph compilation and state persistence for 2-5 second responses
"""

import os
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import logging

# Checkpointer handling for Docker environment
try:
    from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver
    CHECKPOINTER_AVAILABLE = True
except ImportError:
    try:
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        CHECKPOINTER_AVAILABLE = True
    except ImportError:
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver as AsyncSqliteSaver
            CHECKPOINTER_AVAILABLE = True
        except ImportError:
            # No persistent checkpointer available in Docker - use in-memory
            AsyncSqliteSaver = None
            CHECKPOINTER_AVAILABLE = False
            logger = logging.getLogger(__name__)
            logger.warning("No persistent checkpointer available - using in-memory mode")
from deepagents import create_deep_agent
from agents.bsa.bsa_deepagents import BSA_MAIN_INSTRUCTIONS, BSADeepAgentState
from agents.bsa.bsa_deepagents import (
    bid_search_subagent,
    market_research_subagent,
    bid_submission_subagent,
    group_bidding_subagent,
    # Import tool functions
    search_bid_cards_original,
    search_projects_for_contractor,
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
    # Import bid submission tools
    extract_quote_from_document,
    parse_verbal_bid,
    validate_bid_completeness,
    submit_contractor_bid,
    get_bid_card_requirements
)

logger = logging.getLogger(__name__)


class BSASingleton:
    """Singleton BSA graph with persistent checkpointing"""
    
    _instance = None
    _graph = None
    _checkpointer = None
    _initialized = False
    
    @classmethod
    async def get_instance(cls):
        """Get or create the singleton BSA graph"""
        if cls._instance is None:
            await cls._initialize()
        return cls._instance
    
    @classmethod
    async def _initialize(cls):
        """Initialize the singleton graph with checkpointer"""
        if cls._initialized:
            return
            
        logger.info("BSA Singleton: Initializing graph and checkpointer...")
        
        try:
            # Create checkpointer for state persistence if available
            if CHECKPOINTER_AVAILABLE and AsyncSqliteSaver is not None:
                db_path = os.path.join(
                    os.path.dirname(__file__), 
                    "bsa_state.db"
                )
                cls._checkpointer = AsyncSqliteSaver.from_conn_string(db_path)
                logger.info(f"BSA Singleton: Persistent checkpointer created at {db_path}")
            else:
                # Use in-memory checkpointer or none for Docker compatibility
                cls._checkpointer = None
                logger.info("BSA Singleton: Running without persistent checkpointer (in-memory mode)")
            
            # Create the deep agent (same as before but only ONCE)
            tools = [
                search_bid_cards_original,
                search_projects_for_contractor,
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
            
            # Create deep agent with BSA instructions using OpenAI GPT-4
            from langchain_openai import ChatOpenAI
            
            # CRITICAL FIX (Sept 3, 2025): Changed from gpt-4 to gpt-4o
            # The OpenAI API key returns 401 error with gpt-4 but works with gpt-4o
            # This was causing BSA to return empty responses for 3 months
            # CIA uses gpt-4o successfully, so BSA now matches that configuration
            openai_model = ChatOpenAI(
                model="gpt-4o",  # Changed from "gpt-4" - fixes 401 API key error
                temperature=0.3,  # Lowered from 0.7 for more consistent tool selection
                api_key=os.getenv("OPENAI_API_KEY")
            )
            
            agent = create_deep_agent(
                tools=tools,
                instructions=BSA_MAIN_INSTRUCTIONS,
                model=openai_model,  # Explicitly use OpenAI model
                subagents=[
                    bid_search_subagent,
                    market_research_subagent,
                    bid_submission_subagent,
                    group_bidding_subagent
                ],
                state_schema=BSADeepAgentState
            )
            
            # Check if agent is already compiled or needs compilation
            if hasattr(agent, 'compile') and callable(getattr(agent, 'compile')):
                # Compile graph with checkpointer for persistence (if available)
                if cls._checkpointer is not None:
                    cls._graph = agent.compile(checkpointer=cls._checkpointer)
                    logger.info("BSA Singleton: Graph compiled with persistent checkpointer")
                else:
                    cls._graph = agent.compile()
                    logger.info("BSA Singleton: Graph compiled without checkpointer (faster startup)")
            else:
                # Agent is already compiled, use directly
                cls._graph = agent
                logger.info("BSA Singleton: Using pre-compiled DeepAgent graph")
            cls._instance = cls
            cls._initialized = True
            
            logger.info("BSA Singleton: Graph compiled and ready")
            
        except Exception as e:
            logger.error(f"BSA Singleton: Failed to initialize - {e}")
            raise
    
    @classmethod
    async def invoke(cls, state: Dict[str, Any], thread_id: str) -> Dict[str, Any]:
        """Invoke the singleton graph with thread-based persistence"""
        if not cls._initialized:
            await cls._initialize()
        
        # Configure with thread_id for session persistence if checkpointer available
        if cls._checkpointer is not None:
            config = {"configurable": {"thread_id": thread_id}}
            logger.info(f"BSA Singleton: Invoking with persistent thread_id={thread_id}")
        else:
            config = None
            logger.info(f"BSA Singleton: Invoking in stateless mode (still fast due to singleton)")
        
        start_time = datetime.now()
        
        try:
            # Invoke the compiled graph (reuses existing state via checkpointer if available)
            logger.info(f"BSA Singleton: About to invoke with state keys: {list(state.keys())}")
            logger.info(f"BSA Singleton: Number of messages: {len(state.get('messages', []))}")
            
            # DEBUG: Log the exact state being passed to DeepAgents
            for i, msg in enumerate(state.get('messages', [])):
                logger.info(f"BSA Singleton: Message {i}: type={type(msg)}, content preview={str(msg)[:100]}...")
            
            logger.info(f"BSA Singleton: Graph type: {type(cls._graph)}")
            logger.info(f"BSA Singleton: Graph methods: {[m for m in dir(cls._graph) if not m.startswith('_')]}")
            
            if config:
                logger.info(f"BSA Singleton: Invoking with config: {config}")
                result = await cls._graph.ainvoke(state, config=config)
            else:
                logger.info(f"BSA Singleton: Invoking without config")
                result = await cls._graph.ainvoke(state)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"BSA Singleton: Response in {elapsed:.2f} seconds")
            
            # DEBUG: Log raw result before any processing
            logger.info(f"BSA Singleton: Raw result from ainvoke: {type(result)}")
            logger.info(f"BSA Singleton: Raw result str: {str(result)[:200]}...")
            logger.info(f"BSA Singleton: Raw result repr: {repr(result)[:300]}...")
            
            # DEBUG: Log the result structure in detail  
            logger.info(f"BSA SINGLETON DEBUG: Result type: {type(result)}")
            logger.info(f"BSA SINGLETON DEBUG: Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            logger.info(f"BSA SINGLETON DEBUG: Full result = {result}")
            
            if isinstance(result, dict) and 'messages' in result:
                logger.info(f"BSA SINGLETON DEBUG: Messages in result: {len(result['messages'])}")
                logger.info(f"BSA SINGLETON DEBUG: All messages = {result['messages']}")
                if result['messages']:
                    last_msg = result['messages'][-1]
                    logger.info(f"BSA SINGLETON DEBUG: Last message type: {type(last_msg)}")
                    logger.info(f"BSA SINGLETON DEBUG: Full last message = {last_msg}")
                    if isinstance(last_msg, dict):
                        logger.info(f"BSA SINGLETON DEBUG: Last message keys: {list(last_msg.keys())}")
                        logger.info(f"BSA SINGLETON DEBUG: Last message role: {last_msg.get('role')}")
                        content = last_msg.get('content', '')
                        logger.info(f"BSA SINGLETON DEBUG: Raw content = {repr(content)}")
                        logger.info(f"BSA SINGLETON DEBUG: Content length: {len(content) if content else 0}")
                        if content:
                            logger.info(f"BSA SINGLETON DEBUG: Content preview: {content[:200]}...")
                        else:
                            logger.info(f"BSA SINGLETON DEBUG: ❌ NO CONTENT - GPT-4 returned empty response!")
            
            return result
            
        except Exception as e:
            logger.error(f"BSA Singleton: Invocation failed - {e}")
            raise
    
    @classmethod
    async def stream(cls, state: Dict[str, Any], thread_id: str):
        """Stream responses from the singleton graph"""
        if not cls._initialized:
            await cls._initialize()
        
        # Configure with thread_id for session persistence if checkpointer available 
        if cls._checkpointer is not None:
            config = {"configurable": {"thread_id": thread_id}}
            logger.info(f"BSA Singleton: Streaming with persistent thread_id={thread_id}")
        else:
            config = None
            logger.info(f"BSA Singleton: Streaming in stateless mode (still fast due to singleton)")
        
        start_time = datetime.now()
        
        try:
            # Stream from the compiled graph
            if config:
                async for chunk in cls._graph.astream(state, config=config, stream_mode="values"):
                    yield chunk
            else:
                async for chunk in cls._graph.astream(state, stream_mode="values"):
                    yield chunk
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"BSA Singleton: Stream completed in {elapsed:.2f} seconds")
            
        except Exception as e:
            logger.error(f"BSA Singleton: Streaming failed - {e}")
            raise
    
    @classmethod
    async def get_state(cls, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get the current state for a thread"""
        if not cls._initialized:
            await cls._initialize()
        
        # Only get state if checkpointer is available
        if cls._checkpointer is None:
            logger.info("BSA Singleton: No persistent state available without checkpointer")
            return None
        
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # Get state from checkpointer
            state = await cls._graph.aget_state(config)
            return state.values if state else None
        except Exception as e:
            logger.error(f"BSA Singleton: Failed to get state - {e}")
            return None
    
    @classmethod
    async def update_state(cls, thread_id: str, state_updates: Dict[str, Any]):
        """Update the state for a thread"""
        if not cls._initialized:
            await cls._initialize()
        
        # Only update state if checkpointer is available
        if cls._checkpointer is None:
            logger.info("BSA Singleton: No persistent state updates without checkpointer")
            return
        
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # Update state in checkpointer
            await cls._graph.aupdate_state(config, state_updates)
            logger.info(f"BSA Singleton: State updated for thread {thread_id}")
        except Exception as e:
            logger.error(f"BSA Singleton: Failed to update state - {e}")
    
    @classmethod
    def get_thread_id(cls, contractor_id: str, session_id: Optional[str] = None) -> str:
        """Generate a consistent thread_id for a contractor session"""
        # Use contractor_id + session_id for unique thread identification
        if session_id:
            return f"bsa_{contractor_id}_{session_id}"
        else:
            return f"bsa_{contractor_id}_default"