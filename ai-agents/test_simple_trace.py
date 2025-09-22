#!/usr/bin/env python3
"""
Simple test to verify Langfuse tracing is working
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.langfuse_config import tracing

def test_simple_trace():
    """Test basic trace creation"""
    
    print("=== Simple Langfuse Trace Test ===")
    print(f"Tracing enabled: {tracing.enabled}")
    
    if not tracing.enabled:
        print("Langfuse not available - skipping test")
        return
    
    try:
        # Create a simple trace
        trace = tracing.create_trace(
            name="Test Trace",
            user_id="test-user",
            session_id="test-session",
            metadata={"test": "simple_trace"}
        )
        
        if trace:
            print("✅ Trace created successfully")
            
            # Create a span
            span = tracing.create_span(
                trace, 
                "Test Operation",
                input_data={"input": "test"},
                metadata={"operation": "test"}
            )
            
            if span:
                print("✅ Span created successfully")
                
                # End the span
                tracing.end_span(span, {"output": "success"}, "DEFAULT", "Test completed")
                print("✅ Span ended successfully")
            
            # Log an event
            tracing.log_event(
                trace,
                "Test Event",
                input_data={"event": "test"},
                output_data={"result": "success"}
            )
            print("✅ Event logged successfully")
            
        # Flush to Langfuse
        tracing.flush()
        print("✅ Traces flushed to Langfuse")
        print("   -> Check https://us.cloud.langfuse.com for traces")
        
    except Exception as e:
        print(f"❌ Trace test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_trace()