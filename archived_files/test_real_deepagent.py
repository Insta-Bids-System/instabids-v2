"""
Test REAL deepagents framework with o3
"""
import os
from dotenv import load_dotenv
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI

# Load environment
load_dotenv()

# Create o3 model
o3_model = ChatOpenAI(
    model="o3-mini",  # Using o3-mini which is available
    api_key=os.environ.get("OPENAI_API_KEY"),
    temperature=0.1
)

# Simple test function
def test_function(query: str) -> str:
    """Test function for the agent"""
    return f"Processed: {query}"

# Create a simple subagent
test_subagent = {
    "name": "test-expert",
    "description": "Test expert for demo",
    "prompt": "You are a test expert. Help with testing.",
    "tools": ["test_function"]
}

# Create the agent
agent = create_deep_agent(
    tools=[test_function],
    instructions="You are a test agent using the REAL deepagents framework with o3.",
    model=o3_model,
    subagents=[test_subagent]
)

print("Agent created successfully!")
print(f"Agent type: {type(agent)}")
print(f"Agent config: {agent.config}")

# Test it
response = agent.invoke({
    "messages": [{"role": "user", "content": "Hello, test the system"}]
})

print(f"Response: {response}")