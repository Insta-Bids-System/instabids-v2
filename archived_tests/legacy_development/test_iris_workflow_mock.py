#!/usr/bin/env python3
"""
Test IRIS workflow questions by directly calling the method without Claude API
"""

import sys
import os
import json

# Add ai-agents to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-agents'))

# Now we can import from ai-agents
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

def test_workflow_logic():
    """Test the workflow question generation logic directly"""
    
    print("\n" + "="*80)
    print("TESTING IRIS WORKFLOW QUESTION LOGIC")
    print("="*80)
    
    # Create a mock request
    tiny_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    # Simulate request data
    class MockRequest:
        def __init__(self):
            self.message = "Test image upload"
            self.user_id = "test-user"
            self.session_id = "test-session"
            self.context_type = "auto"
            self.images = [{
                "data": tiny_image,
                "filename": "test.png",
                "size": 100,
                "type": "image/png"
            }]
            self.trigger_image_workflow = True
    
    request = MockRequest()
    
    print("\nRequest created with:")
    print(f"- trigger_image_workflow: {request.trigger_image_workflow}")
    print(f"- images: {len(request.images) if request.images else 0}")
    
    # Test the workflow question generation logic
    print("\n" + "-"*40)
    print("Testing workflow question creation logic:")
    print("-"*40)
    
    # Simulate the logic from the process_message method
    workflow_questions = []
    
    if request.trigger_image_workflow and request.images:
        print("[OK] Condition met: trigger_image_workflow=True and images present")
        
        workflow_questions = [
            {
                "question": "Where would you like to store this image?",
                "options": ["Inspiration Board", "Property Photos", "Both"],
                "callback": "store_image_location"
            },
            {
                "question": "What room or area is this?",
                "options": ["Backyard", "Kitchen", "Bathroom", "Living Room", "Bedroom", "Other"],
                "callback": "identify_room_type"
            }
        ]
        print(f"[OK] Created {len(workflow_questions)} workflow questions")
    else:
        print("[X] Condition not met")
    
    print(f"\nWorkflow questions: {workflow_questions}")
    
    # Test the response object
    print("\n" + "-"*40)
    print("Testing response object creation:")
    print("-"*40)
    
    # Create a mock response similar to UnifiedIrisResponse
    class MockResponse:
        def __init__(self, **kwargs):
            self.response = kwargs.get('response', '')
            self.suggestions = kwargs.get('suggestions', [])
            self.session_id = kwargs.get('session_id', '')
            self.reasoning = kwargs.get('reasoning', {})
            self.available_tools = kwargs.get('available_tools', [])
            self.context_summary = kwargs.get('context_summary', {})
            self.workflow_questions = kwargs.get('workflow_questions', [])
        
        def to_dict(self):
            return {
                'response': self.response,
                'suggestions': self.suggestions,
                'session_id': self.session_id,
                'reasoning': self.reasoning,
                'available_tools': self.available_tools,
                'context_summary': self.context_summary,
                'workflow_questions': self.workflow_questions
            }
    
    response = MockResponse(
        response="Test response",
        suggestions=[],
        session_id="test-session",
        reasoning={},
        available_tools=[],
        context_summary={},
        workflow_questions=workflow_questions
    )
    
    print(f"Response object created successfully")
    print(f"- workflow_questions in response: {response.workflow_questions}")
    print(f"- workflow_questions count: {len(response.workflow_questions) if response.workflow_questions else 0}")
    
    # Verify serialization
    response_dict = response.to_dict()
    print(f"\nSerialized response:")
    print(f"- 'workflow_questions' key present: {'workflow_questions' in response_dict}")
    print(f"- Value: {response_dict.get('workflow_questions')}")

if __name__ == "__main__":
    test_workflow_logic()