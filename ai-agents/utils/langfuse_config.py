"""
Langfuse Configuration and Tracing Utilities for InstaBids CDA System
"""
import os
import logging
from typing import Dict, Any, Optional, List
from functools import wraps
from datetime import datetime
import asyncio
import json

try:
    from langfuse import get_client, observe
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    logging.warning("Langfuse not installed. Tracing will be disabled.")

logger = logging.getLogger(__name__)

class InstaBidsTracing:
    """InstaBids-specific Langfuse tracing wrapper"""
    
    def __init__(self):
        self.enabled = False
        self.langfuse = None
        
        if LANGFUSE_AVAILABLE:
            self._initialize_langfuse()
    
    def _initialize_langfuse(self):
        """Initialize Langfuse with environment variables"""
        try:
            secret_key = os.getenv("LANGFUSE_SECRET_KEY")
            public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
            host = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
            
            if secret_key and public_key:
                # Set environment variables for Langfuse v3 SDK
                os.environ["LANGFUSE_SECRET_KEY"] = secret_key
                os.environ["LANGFUSE_PUBLIC_KEY"] = public_key
                os.environ["LANGFUSE_HOST"] = host
                
                self.langfuse = get_client()
                self.enabled = True
                logger.info(f"[Tracing] Langfuse initialized with host: {host}")
            else:
                logger.warning("[Tracing] Langfuse credentials not found in environment")
                
        except Exception as e:
            logger.error(f"[Tracing] Failed to initialize Langfuse: {e}")
    
    def create_trace(self, name: str, user_id: str = None, session_id: str = None, 
                    metadata: Dict[str, Any] = None) -> Optional[Any]:
        """Create a new trace for tracking a complete workflow"""
        if not self.enabled:
            return None
            
        try:
            # Use modern Langfuse v3 API - create a span as the root trace
            span = self.langfuse.start_span(name=name)
            if metadata:
                span.update(metadata=metadata)
            logger.debug(f"[Tracing] Created trace: {name}")
            return span
        except Exception as e:
            logger.error(f"[Tracing] Failed to create trace: {e}")
            return None
    
    def create_span(self, parent, name: str, input_data: Any = None, 
                   metadata: Dict[str, Any] = None) -> Optional[Any]:
        """Create a span within a parent observation"""
        if not self.enabled or not parent:
            return None
            
        try:
            # Use modern Langfuse API - create child span from parent observation
            span = parent.start_span(
                name=name,
                input=input_data,
                metadata=metadata or {}
            )
            logger.debug(f"[Tracing] Created span: {name}")
            return span
        except Exception as e:
            logger.error(f"[Tracing] Failed to create span: {e}")
            return None
    
    def end_span(self, span, output_data: Any = None, level: str = "DEFAULT",
                status_message: str = None):
        """End a span with output data"""
        if not self.enabled or not span:
            return
            
        try:
            # Update span with output data before ending
            if output_data:
                span.update(output=output_data)
            if status_message:
                span.update(status_message=status_message)
            
            span.end()
            logger.debug(f"[Tracing] Ended span with level: {level}")
        except Exception as e:
            logger.error(f"[Tracing] Failed to end span: {e}")
    
    def log_event(self, parent, name: str, input_data: Any = None, 
                 output_data: Any = None, level: str = "DEFAULT"):
        """Log a simple event within a parent observation"""
        if not self.enabled or not parent:
            return
            
        try:
            # Use modern Langfuse v3 API - create event as a nested span
            event_span = parent.start_span(name=name)
            if input_data:
                event_span.update(input=input_data)
            if output_data:
                event_span.update(output=output_data)
            event_span.end()
            logger.debug(f"[Tracing] Logged event: {name}")
            return event_span
        except Exception as e:
            logger.error(f"[Tracing] Failed to log event: {e}")
    
    def track_llm_call(self, parent, model: str, input_messages: List[Dict], 
                      response: str, usage: Dict[str, int] = None,
                      metadata: Dict[str, Any] = None) -> Optional[Any]:
        """Track an LLM API call"""
        if not self.enabled or not parent:
            return None
            
        try:
            # Use modern Langfuse v3 API - use context manager for generation
            with self.langfuse.start_as_current_generation(
                name=f"LLM Call - {model}",
                model=model
            ) as generation:
                generation.update(
                    input=input_messages,
                    output=response,
                    usage=usage,
                    metadata=metadata or {}
                )
                logger.debug(f"[Tracing] Tracked LLM call: {model}")
                return generation
        except Exception as e:
            logger.error(f"[Tracing] Failed to track LLM call: {e}")
            return None
    
    def flush(self):
        """Flush any pending traces"""
        if self.enabled and self.langfuse:
            try:
                self.langfuse.flush()
                logger.debug("[Tracing] Flushed pending traces")
            except Exception as e:
                logger.error(f"[Tracing] Failed to flush traces: {e}")

# Global tracing instance
tracing = InstaBidsTracing()

def trace_cda_operation(operation_name: str, include_input: bool = True, 
                       include_output: bool = True):
    """Decorator to trace CDA operations"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not tracing.enabled:
                return await func(*args, **kwargs)
            
            # Create trace for this operation
            trace = tracing.create_trace(
                name=f"CDA - {operation_name}",
                metadata={
                    "component": "CDA",
                    "operation": operation_name,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Prepare input data
            input_data = None
            if include_input:
                input_data = {
                    "args": [str(arg)[:200] for arg in args],  # Limit length
                    "kwargs": {k: str(v)[:200] for k, v in kwargs.items()}
                }
            
            # Create span for the operation
            span = tracing.create_span(
                trace, 
                operation_name,
                input_data=input_data,
                metadata={"function": func.__name__}
            )
            
            try:
                result = await func(*args, **kwargs)
                
                # End span with success
                output_data = None
                if include_output and result:
                    if isinstance(result, dict):
                        output_data = {k: str(v)[:200] for k, v in result.items()}
                    else:
                        output_data = str(result)[:500]
                
                tracing.end_span(span, output_data, "DEFAULT", "Success")
                
                return result
                
            except Exception as e:
                # End span with error
                tracing.end_span(span, {"error": str(e)}, "ERROR", f"Failed: {str(e)}")
                raise
            
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not tracing.enabled:
                return func(*args, **kwargs)
            
            # Similar logic for sync functions
            trace = tracing.create_trace(
                name=f"CDA - {operation_name}",
                metadata={
                    "component": "CDA",
                    "operation": operation_name,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            input_data = None
            if include_input:
                input_data = {
                    "args": [str(arg)[:200] for arg in args],
                    "kwargs": {k: str(v)[:200] for k, v in kwargs.items()}
                }
            
            span = tracing.create_span(
                trace, 
                operation_name,
                input_data=input_data,
                metadata={"function": func.__name__}
            )
            
            try:
                result = func(*args, **kwargs)
                
                output_data = None
                if include_output and result:
                    if isinstance(result, dict):
                        output_data = {k: str(v)[:200] for k, v in result.items()}
                    else:
                        output_data = str(result)[:500]
                
                tracing.end_span(span, output_data, "DEFAULT", "Success")
                return result
                
            except Exception as e:
                tracing.end_span(span, {"error": str(e)}, "ERROR", f"Failed: {str(e)}")
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def track_contractor_discovery(bid_card_id: str, project_type: str, location: Dict[str, Any]):
    """Create a trace specifically for contractor discovery workflow"""
    if not tracing.enabled:
        return None
    
    return tracing.create_trace(
        name="Contractor Discovery Workflow",
        session_id=bid_card_id,
        metadata={
            "bid_card_id": bid_card_id,
            "project_type": project_type,
            "location": location,
            "workflow_type": "contractor_discovery",
            "component": "CDA",
            "timestamp": datetime.now().isoformat()
        }
    )

def track_profile_building(contractor_name: str, data_sources: List[str]):
    """Create a trace for profile building workflow"""
    if not tracing.enabled:
        return None
    
    return tracing.create_trace(
        name="Contractor Profile Building",
        metadata={
            "contractor_name": contractor_name,
            "data_sources": data_sources,
            "workflow_type": "profile_building",
            "component": "CDA",
            "timestamp": datetime.now().isoformat()
        }
    )

# Convenience functions for common CDA operations
def log_geocoding_result(trace, zip_code: str, coordinates: tuple, duration: float):
    """Log geocoding operation result"""
    tracing.log_event(
        trace,
        "Geocoding Complete",
        input_data={"zip_code": zip_code},
        output_data={
            "coordinates": coordinates,
            "duration_seconds": duration,
            "success": coordinates is not None
        }
    )

def log_contractor_search(trace, search_criteria: Dict, results_count: int, 
                         search_method: str, duration: float):
    """Log contractor search operation"""
    tracing.log_event(
        trace,
        f"Contractor Search - {search_method}",
        input_data=search_criteria,
        output_data={
            "results_count": results_count,
            "search_method": search_method,
            "duration_seconds": duration,
            "success": results_count > 0
        }
    )

def log_profile_enrichment(trace, contractor_id: str, enrichment_source: str,
                          fields_added: int, duration: float):
    """Log profile enrichment operation"""
    tracing.log_event(
        trace,
        f"Profile Enrichment - {enrichment_source}",
        input_data={"contractor_id": contractor_id},
        output_data={
            "enrichment_source": enrichment_source,
            "fields_added": fields_added,
            "duration_seconds": duration,
            "success": fields_added > 0
        }
    )

# Export commonly used items
__all__ = [
    'tracing',
    'trace_cda_operation',
    'track_contractor_discovery',
    'track_profile_building',
    'log_geocoding_result',
    'log_contractor_search',
    'log_profile_enrichment'
]