#!/usr/bin/env python3
"""
Debug: Test message filtering in detail
"""

import sys
import os

# Add parent directory to path
ai_agents_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai-agents')
sys.path.insert(0, ai_agents_path)

from adapters.messaging_context import MessagingContextAdapter

# Test message
test_message = {
    "content": "Hi, I'm John Smith at 123 Main St. My phone is 555-1234.",
    "sender_id": "test_user",
    "sender_type": "homeowner",
    "metadata": {
        "full_name": "John Smith",
        "phone": "555-1234",
        "address": "123 Main St"
    }
}

adapter = MessagingContextAdapter()

# Apply filtering
filtered = adapter.apply_message_filtering(
    message=test_message,
    sender_side="homeowner",
    recipient_side="contractor"
)

print("Original content:", test_message["content"])
print("Filtered content:", filtered.get("content"))
print("\nFull filtered message:")
import json
print(json.dumps(filtered, indent=2))