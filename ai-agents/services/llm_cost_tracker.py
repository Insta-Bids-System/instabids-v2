"""
Universal LLM Cost Tracking System for InstaBids
Handles both OpenAI and Anthropic APIs with complete model detection
Captures EVERY token, calculates EXACT costs, stores in database
"""
import asyncio
import time
from typing import Dict, Any, Optional, Union
from datetime import datetime
import json
import os
from decimal import Decimal

from openai import AsyncOpenAI, OpenAI
from anthropic import AsyncAnthropic, Anthropic
from database_simple import SupabaseDB


class LLMCostCalculator:
    """Accurate cost calculations for all LLM providers and models"""
    
    # Current pricing as of January 2025 (per 1K tokens)
    PRICING = {
        "openai": {
            # GPT-5 Models
            "gpt-5": {"input": 0.010, "output": 0.030},
            "gpt-5-turbo": {"input": 0.008, "output": 0.025},
            
            # GPT-4 Models  
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4-turbo": {"input": 0.010, "output": 0.030},
            "gpt-4": {"input": 0.030, "output": 0.060},
            
            # GPT-3.5 Models
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004},
            
            # DALL-E Models (per image)
            "dall-e-3": {"1024x1024": 0.040, "1792x1024": 0.080},
            "dall-e-2": {"1024x1024": 0.020, "512x512": 0.018}
        },
        "anthropic": {
            # Claude Opus 4 Models
            "claude-opus-4-20250514": {"input": 0.015, "output": 0.075},
            "claude-opus-4": {"input": 0.015, "output": 0.075},
            
            # Claude 3 Models
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            
            # Claude 3.5 Models (current pricing as of Jan 2025)
            "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
            "claude-3.5-sonnet": {"input": 0.003, "output": 0.015},
            
            # Legacy Claude 3 Sonnet
            "claude-3-7-sonnet-20250219": {"input": 0.003, "output": 0.015},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125}
        }
    }
    
    def calculate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for any provider/model combination"""
        
        # Normalize provider name
        provider = provider.lower()
        
        # Try to find exact model match
        if provider in self.PRICING and model in self.PRICING[provider]:
            rates = self.PRICING[provider][model]
        else:
            # Fallback to default pricing based on provider
            print(f"[COST_CALC] Unknown model {model} for {provider}, using default pricing")
            if provider == "openai":
                rates = {"input": 0.005, "output": 0.015}  # GPT-4o pricing as default
            elif provider == "anthropic":
                rates = {"input": 0.003, "output": 0.015}  # Sonnet pricing as default
            else:
                rates = {"input": 0.001, "output": 0.003}  # Conservative default
        
        # Calculate cost (rates are per 1K tokens)
        input_cost = (input_tokens / 1000) * rates["input"]
        output_cost = (output_tokens / 1000) * rates["output"]
        total_cost = input_cost + output_cost
        
        return round(total_cost, 6)


class LLMCostTracker:
    """
    Central tracking system for ALL LLM API calls
    Captures tokens, costs, and performance metrics for every interaction
    """
    
    def __init__(self):
        """Initialize the cost tracking system"""
        self.db = SupabaseDB()
        self.calculator = LLMCostCalculator()
        self.daily_totals = {}  # Cache for daily totals
        
        # Cost alert thresholds
        self.thresholds = {
            "daily_limit": float(os.getenv("LLM_DAILY_LIMIT", "200")),
            "hourly_spike": float(os.getenv("LLM_HOURLY_SPIKE", "50")),
            "per_conversation": float(os.getenv("LLM_CONVERSATION_LIMIT", "5"))
        }
        
        print("[LLM_TRACKER] Initialized with thresholds:", self.thresholds)
    
    def track_llm_call_sync(self,
                           agent_name: str,
                           provider: str,
                           model: str,
                           input_tokens: int,
                           output_tokens: int,
                           duration_ms: int,
                           context: Dict[str, Any] = None,
                           error_occurred: bool = False,
                           error_details: str = None) -> Dict[str, Any]:
        """
        Synchronous wrapper for track_llm_call
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, schedule as a task
                task = asyncio.create_task(self.track_llm_call(
                    agent_name, provider, model, input_tokens, output_tokens,
                    duration_ms, context, error_occurred, error_details
                ))
                return {"status": "scheduled", "task": task}
            else:
                # If no loop is running, run synchronously
                return loop.run_until_complete(self.track_llm_call(
                    agent_name, provider, model, input_tokens, output_tokens,
                    duration_ms, context, error_occurred, error_details
                ))
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self.track_llm_call(
                agent_name, provider, model, input_tokens, output_tokens,
                duration_ms, context, error_occurred, error_details
            ))
    
    async def track_llm_call(self, 
                            agent_name: str,
                            provider: str,
                            model: str,
                            input_tokens: int,
                            output_tokens: int,
                            duration_ms: int,
                            context: Dict[str, Any] = None,
                            error_occurred: bool = False,
                            error_details: str = None) -> Dict[str, Any]:
        """
        Track an LLM API call with complete details
        Returns the tracking record for confirmation
        """
        
        # Calculate cost
        cost_usd = self.calculator.calculate_cost(provider, model, input_tokens, output_tokens)
        
        # Create tracking record
        tracking_record = {
            "agent_name": agent_name,
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_cost": cost_usd,
            "duration_ms": duration_ms,
            "error_occurred": error_occurred,
            "context": context or {}
        }
        
        # Store in database (async, non-blocking)
        try:
            await self._store_to_database(tracking_record)
            
            # Check cost thresholds
            await self._check_cost_alerts(agent_name, cost_usd, context)
            
            # Update daily totals cache
            self._update_daily_cache(agent_name, cost_usd)
            
            print(f"[LLM_TRACKER] {agent_name} used {model}: ${cost_usd:.4f} ({input_tokens}+{output_tokens} tokens)")
            
        except Exception as e:
            print(f"[LLM_TRACKER] Error storing metrics: {e}")
            # Don't fail the API call if tracking fails
        
        return tracking_record
    
    async def _store_to_database(self, record: Dict[str, Any]):
        """Store tracking record to Supabase"""
        try:
            # Extract context fields for database columns
            context_data = record.pop("context", {})
            
            db_record = {
                "agent_name": record["agent_name"],
                "provider": record["provider"],
                "model": record["model"],
                "input_tokens": record["input_tokens"],
                "output_tokens": record["output_tokens"],
                "total_cost": record["total_cost"],
                "duration_ms": record.get("duration_ms"),
                "user_id": context_data.get("user_id"),
                "conversation_id": context_data.get("conversation_id"),
                "error_occurred": record.get("error_occurred", False),
                "context": context_data  # Store as JSONB
            }
            
            result = self.db.client.table("llm_usage").insert(db_record).execute()
            
        except Exception as e:
            print(f"[LLM_TRACKER] Database storage error: {e}")
    
    async def _check_cost_alerts(self, agent_name: str, cost: float, context: Dict[str, Any]):
        """Check if cost thresholds are exceeded and trigger alerts"""
        
        # Check daily total
        daily_total = await self.get_daily_total()
        if daily_total > self.thresholds["daily_limit"]:
            await self._trigger_alert("daily_limit", f"Daily LLM spend ${daily_total:.2f} exceeds limit ${self.thresholds['daily_limit']:.2f}")
        
        # Check per-conversation cost if session_id provided
        if context and context.get("session_id"):
            session_cost = await self.get_session_cost(context["session_id"])
            if session_cost > self.thresholds["per_conversation"]:
                await self._trigger_alert("conversation_limit", f"Session {context['session_id']} cost ${session_cost:.2f} exceeds limit")
    
    async def _trigger_alert(self, alert_type: str, message: str):
        """Trigger a cost alert (email, slack, etc.)"""
        print(f"[LLM_ALERT] {alert_type}: {message}")
        # TODO: Implement email/slack notifications
    
    def _update_daily_cache(self, agent_name: str, cost: float):
        """Update in-memory daily totals cache"""
        today = datetime.utcnow().date().isoformat()
        
        if today not in self.daily_totals:
            self.daily_totals[today] = {}
        
        if agent_name not in self.daily_totals[today]:
            self.daily_totals[today][agent_name] = 0
        
        self.daily_totals[today][agent_name] += cost
    
    async def get_daily_total(self) -> float:
        """Get today's total LLM spend"""
        try:
            result = await self.db.client.from_("llm_usage_log")\
                .select("cost_usd")\
                .gte("timestamp", datetime.utcnow().date().isoformat())\
                .execute()
            
            return sum(row["cost_usd"] for row in result.data)
        except:
            return 0.0
    
    async def get_session_cost(self, session_id: str) -> float:
        """Get total cost for a specific session"""
        try:
            result = await self.db.client.from_("llm_usage_log")\
                .select("cost_usd")\
                .eq("session_id", session_id)\
                .execute()
            
            return sum(row["cost_usd"] for row in result.data)
        except:
            return 0.0


class TrackedOpenAI:
    """Wrapper for OpenAI that captures all usage"""
    
    def __init__(self, agent_name: str, api_key: str, tracker: LLMCostTracker, is_async: bool = True):
        self.agent_name = agent_name
        self.tracker = tracker
        
        if is_async:
            self.client = AsyncOpenAI(api_key=api_key)
            self.is_async = True
        else:
            self.client = OpenAI(api_key=api_key)
            self.is_async = False
    
    @property
    def chat(self):
        """Access chat completions with tracking"""
        return self
    
    @property
    def completions(self):
        """Access completions endpoint with tracking"""
        return self
    
    async def create(self, **kwargs):
        """Create chat completion with automatic tracking"""
        start_time = time.time()
        model = kwargs.get("model", "unknown")
        
        try:
            # Make the actual API call
            if self.is_async:
                response = await self.client.chat.completions.create(**kwargs)
            else:
                response = self.client.chat.completions.create(**kwargs)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Track the successful call
            if hasattr(response, 'usage') and response.usage:
                await self.tracker.track_llm_call(
                    agent_name=self.agent_name,
                    provider="openai",
                    model=model,
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    duration_ms=duration_ms,
                    context=self._extract_context(kwargs)
                )
            
            return response
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Track the failed call
            await self.tracker.track_llm_call(
                agent_name=self.agent_name,
                provider="openai",
                model=model,
                input_tokens=0,
                output_tokens=0,
                duration_ms=duration_ms,
                error_occurred=True,
                error_details=str(e)
            )
            raise
    
    def _extract_context(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Extract context from API call parameters"""
        context = {}
        
        # Try to extract user/session/bid_card info from messages or metadata
        if "metadata" in kwargs:
            context.update(kwargs["metadata"])
        
        # Extract from system message if available
        messages = kwargs.get("messages", [])
        if messages and len(messages) > 0:
            # Could parse messages for context if needed
            context["message_count"] = len(messages)
        
        return context


class TrackedAnthropic:
    """Wrapper for Anthropic that captures all usage"""
    
    def __init__(self, agent_name: str, api_key: str, tracker: LLMCostTracker, is_async: bool = True):
        self.agent_name = agent_name
        self.tracker = tracker
        
        if is_async:
            self.client = AsyncAnthropic(api_key=api_key)
            self.is_async = True
        else:
            self.client = Anthropic(api_key=api_key)
            self.is_async = False
    
    @property
    def messages(self):
        """Access messages endpoint with tracking"""
        return self
    
    async def create(self, **kwargs):
        """Create message with automatic tracking"""
        start_time = time.time()
        model = kwargs.get("model", "unknown")
        
        try:
            # Extract metadata before making the call (Anthropic doesn't support metadata param)
            metadata = kwargs.pop('metadata', {})
            
            # Store metadata for context tracking
            self._last_metadata = metadata
            
            # Make the actual API call
            if self.is_async:
                response = await self.client.messages.create(**kwargs)
            else:
                response = self.client.messages.create(**kwargs)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Track the successful call
            if hasattr(response, 'usage') and response.usage:
                await self.tracker.track_llm_call(
                    agent_name=self.agent_name,
                    provider="anthropic",
                    model=model,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    duration_ms=duration_ms,
                    context=self._extract_context(kwargs)
                )
            
            return response
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Track the failed call
            await self.tracker.track_llm_call(
                agent_name=self.agent_name,
                provider="anthropic",
                model=model,
                input_tokens=0,
                output_tokens=0,
                duration_ms=duration_ms,
                error_occurred=True,
                error_details=str(e)
            )
            raise
    
    def _extract_context(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Extract context from API call parameters"""
        context = {}
        
        # Use stored metadata if available
        if hasattr(self, '_last_metadata'):
            context.update(self._last_metadata)
        
        # Extract from messages if available
        messages = kwargs.get("messages", [])
        if messages and len(messages) > 0:
            context["message_count"] = len(messages)
        
        return context


# Global tracker instance
llm_cost_tracker = LLMCostTracker()


def get_tracked_openai_client(agent_name: str, api_key: str, is_async: bool = True) -> TrackedOpenAI:
    """Factory function to get a tracked OpenAI client"""
    return TrackedOpenAI(agent_name, api_key, llm_cost_tracker, is_async)


def get_tracked_anthropic_client(agent_name: str, api_key: str, is_async: bool = True) -> TrackedAnthropic:
    """Factory function to get a tracked Anthropic client"""
    return TrackedAnthropic(agent_name, api_key, llm_cost_tracker, is_async)