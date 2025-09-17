"""
Streaming Handler for COIA Agent
Provides real-time streaming of responses with thinking indicators
"""
import asyncio
import json
import logging
from typing import Any, AsyncIterator, Optional

from langchain_core.messages import AIMessage, HumanMessage
from langchain.callbacks.base import AsyncCallbackHandler

logger = logging.getLogger(__name__)


class COIAStreamingHandler(AsyncCallbackHandler):
    """
    Custom callback handler for streaming COIA responses
    Provides real-time updates for thinking, typing, and tool usage
    """
    
    def __init__(self):
        self.current_thought = ""
        self.current_response = ""
        self.is_thinking = False
        self.is_using_tool = False
        self.tool_name = None
        self.stream_queue = asyncio.Queue()
    
    async def on_llm_start(self, serialized: dict, prompts: list[str], **kwargs) -> None:
        """Called when LLM starts generating"""
        self.is_thinking = True
        await self.stream_queue.put({
            "type": "thinking_start",
            "message": "Thinking..."
        })
    
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Called when LLM generates a new token"""
        self.current_response += token
        
        # Stream the token to frontend
        await self.stream_queue.put({
            "type": "token",
            "content": token
        })
    
    async def on_llm_end(self, response: Any, **kwargs) -> None:
        """Called when LLM finishes generating"""
        self.is_thinking = False
        await self.stream_queue.put({
            "type": "thinking_end",
            "message": "Done thinking"
        })
    
    async def on_tool_start(self, serialized: dict, input_str: str, **kwargs) -> None:
        """Called when a tool starts executing"""
        self.is_using_tool = True
        self.tool_name = serialized.get("name", "tool")
        
        await self.stream_queue.put({
            "type": "tool_start",
            "tool": self.tool_name,
            "message": f"Using {self.tool_name}..."
        })
    
    async def on_tool_end(self, output: str, **kwargs) -> None:
        """Called when a tool finishes executing"""
        self.is_using_tool = False
        
        await self.stream_queue.put({
            "type": "tool_end",
            "tool": self.tool_name,
            "result": output[:100]  # Truncate for UI
        })
        
        self.tool_name = None
    
    async def on_tool_error(self, error: Exception, **kwargs) -> None:
        """Called when a tool encounters an error"""
        await self.stream_queue.put({
            "type": "tool_error",
            "tool": self.tool_name,
            "error": str(error)
        })
    
    async def get_stream(self) -> AsyncIterator[dict]:
        """Get the stream of events"""
        while True:
            event = await self.stream_queue.get()
            yield event
            
            # Check for completion
            if event.get("type") == "complete":
                break


async def stream_coia_response(
    app: Any,
    state: dict,
    config: dict,
    websocket: Optional[Any] = None
) -> AsyncIterator[dict]:
    """
    Stream COIA responses with real-time updates
    Can be used with WebSocket or Server-Sent Events (SSE)
    """
    
    # Create streaming handler
    handler = COIAStreamingHandler()
    
    # Add handler to config
    if "callbacks" not in config:
        config["callbacks"] = []
    config["callbacks"].append(handler)
    
    # Stream events using astream_events
    try:
        async for event in app.astream_events(state, config, version="v2"):
            
            # Process different event types
            if event["event"] == "on_chat_model_start":
                # Model started thinking
                yield {
                    "type": "status",
                    "status": "thinking",
                    "message": "COIA is thinking..."
                }
            
            elif event["event"] == "on_chat_model_stream":
                # Stream tokens as they're generated
                token = event["data"]["chunk"].content
                yield {
                    "type": "token",
                    "content": token
                }
            
            elif event["event"] == "on_chat_model_end":
                # Model finished generating
                yield {
                    "type": "status",
                    "status": "complete",
                    "message": "Response complete"
                }
            
            elif event["event"] == "on_tool_start":
                # Tool execution started
                tool_name = event.get("name", "tool")
                yield {
                    "type": "tool",
                    "status": "start",
                    "tool": tool_name,
                    "message": f"Searching {tool_name}..."
                }
            
            elif event["event"] == "on_tool_end":
                # Tool execution completed
                yield {
                    "type": "tool",
                    "status": "end",
                    "tool": event.get("name", "tool")
                }
            
            # Send to WebSocket if provided
            if websocket:
                await websocket.send_json(event)
    
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield {
            "type": "error",
            "error": str(e)
        }


async def stream_with_ui_updates(
    app: Any,
    user_message: str,
    session_id: str,
    contractor_lead_id: Optional[str] = None
) -> AsyncIterator[dict]:
    """
    Enhanced streaming with UI state updates
    Provides rich feedback for frontend components
    """
    
    # Prepare initial state
    from .unified_state import create_initial_state
    from langchain_core.messages import HumanMessage
    
    initial_state = create_initial_state(
        session_id=session_id,
        interface="chat",
        contractor_lead_id=contractor_lead_id
    ).to_langgraph_state()
    
    initial_state["messages"] = [HumanMessage(content=user_message)]
    
    # Configure with streaming
    config = {
        "configurable": {
            "thread_id": session_id,
            "checkpoint_id": f"stream_{session_id}",
            "checkpoint_ns": "coia_streaming"
        },
        "recursion_limit": 25,
        "stream_mode": "values"  # Stream intermediate values
    }
    
    # UI state indicators
    ui_states = {
        "greeting": "[HELLO] Let me help you...",
        "researching": "[RESEARCH] Researching your company...",
        "searching": "[SEARCH] Searching for bid opportunities...",
        "analyzing": "[ANALYZE] Analyzing project requirements...",
        "writing": "[WRITE] Preparing response...",
        "complete": "[READY] Ready to help!"
    }
    
    current_state = "greeting"
    
    try:
        # Stream the conversation
        async for chunk in app.astream(initial_state, config):
            
            # Detect mode changes for UI updates
            if "current_mode" in chunk:
                mode = chunk["current_mode"]
                
                if mode == "research":
                    current_state = "researching"
                    yield {
                        "type": "ui_state",
                        "state": current_state,
                        "message": ui_states[current_state]
                    }
                
                elif mode == "bid_card_search":
                    current_state = "searching"
                    yield {
                        "type": "ui_state",
                        "state": current_state,
                        "message": ui_states[current_state]
                    }
                
                elif mode == "intelligence":
                    current_state = "analyzing"
                    yield {
                        "type": "ui_state",
                        "state": current_state,
                        "message": ui_states[current_state]
                    }
            
            # Stream message content
            if "messages" in chunk and chunk["messages"]:
                last_message = chunk["messages"][-1]
                
                if isinstance(last_message, AIMessage):
                    # Stream the AI response
                    content = last_message.content
                    
                    # Break into chunks for typing effect
                    words = content.split()
                    for i in range(0, len(words), 3):  # Stream 3 words at a time
                        word_chunk = " ".join(words[i:i+3])
                        yield {
                            "type": "content",
                            "content": word_chunk + " ",
                            "ui_state": "writing"
                        }
                        await asyncio.sleep(0.05)  # Typing delay
            
            # Stream tool results
            if "tool_results" in chunk and chunk["tool_results"]:
                for tool, result in chunk["tool_results"].items():
                    yield {
                        "type": "tool_result",
                        "tool": tool,
                        "result": result,
                        "ui_state": f"Used {tool}"
                    }
            
            # Stream bid cards if found
            if "bid_cards_attached" in chunk and chunk["bid_cards_attached"]:
                yield {
                    "type": "bid_cards",
                    "cards": chunk["bid_cards_attached"],
                    "count": len(chunk["bid_cards_attached"]),
                    "ui_state": "Found opportunities!"
                }
        
        # Final state
        yield {
            "type": "ui_state",
            "state": "complete",
            "message": ui_states["complete"]
        }
    
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield {
            "type": "error",
            "error": str(e),
            "ui_state": "error"
        }


class ThinkingIndicator:
    """
    Animated thinking indicator for UI
    Shows different states of AI processing
    """
    
    def __init__(self):
        self.states = [
            "[THINK] Thinking",
            "[THINK] Thinking.",
            "[THINK] Thinking..",
            "[THINK] Thinking...",
            "[PROCESS] Processing",
            "[PROCESS] Processing.",
            "[PROCESS] Processing..",
            "[PROCESS] Processing...",
            "[ANALYZE] Analyzing",
            "[ANALYZE] Analyzing.",
            "[ANALYZE] Analyzing..",
            "[ANALYZE] Analyzing..."
        ]
        self.current_index = 0
    
    def get_next_state(self) -> str:
        """Get next thinking state for animation"""
        state = self.states[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.states)
        return state
    
    async def animate(self, duration: float = 3.0) -> AsyncIterator[str]:
        """Animate thinking indicator for specified duration"""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < duration:
            yield self.get_next_state()
            await asyncio.sleep(0.3)  # Animation speed
        
        yield "[COMPLETE] Done!"


# Export main streaming functions
__all__ = [
    "COIAStreamingHandler",
    "stream_coia_response",
    "stream_with_ui_updates",
    "ThinkingIndicator"
]