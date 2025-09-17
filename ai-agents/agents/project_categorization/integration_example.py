"""
Example integration showing how CIA and IRIS agents use the categorization tool
"""

import openai
from typing import Dict, Any
from .tool_handler import CATEGORIZATION_TOOL, handle_categorize_project_tool, create_categorization_prompt_context

class CategorizedAgent:
    """Example of how to integrate categorization tool into an agent"""
    
    def __init__(self, openai_api_key: str):
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.tools = [CATEGORIZATION_TOOL]  # Add to agent's tools
    
    async def process_project_with_categorization(
        self, 
        user_message: str,
        project_data: Dict[str, Any],
        bid_card_id: str
    ) -> str:
        """
        Process user message and automatically categorize if needed
        
        Args:
            user_message: User's message about their project
            project_data: Current project information
            bid_card_id: Bid card being worked on
            
        Returns:
            Agent response
        """
        
        # Create system message with categorization instructions
        system_message = {
            "role": "system",
            "content": """
You are a helpful home improvement assistant with access to a categorize_project tool.

WHEN TO USE CATEGORIZATION TOOL:
- When user provides new project details (title, description, type)
- When project information has changed
- When you need to standardize project language

CONFIDENCE RULES:
- If confidence_score ≥ 0.7: Use the tool to save categorization
- If confidence_score < 0.7: Ask ONE clarifying question instead

CONVERSATIONAL STYLE:
- After successful categorization: "Tagged as [category], [scope] ([confidence]). [natural follow-up]"
- When unsure: Ask specific question to clarify

You categorize home improvement projects into:
- service_category: Installation, Repair, Replacement, Renovation, Maintenance, Ongoing, Emergency, Labor Only, Consultation, Events, Rentals, Lifestyle & Wellness, Professional/Digital, AI Solutions
- project_scope: single_trade, multi_trade, full_renovation
- required_capabilities: Array of needed trades/skills
- normalized_project_type: Consistent snake_case naming

Handle synonyms intelligently (artificial turf = synthetic grass = fake grass).
"""
        }
        
        # Create context message with project data
        context_message = {
            "role": "user", 
            "content": f"""
{create_categorization_prompt_context(project_data)}

User message: {user_message}
"""
        }
        
        # Call OpenAI with tools
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[system_message, context_message],
            tools=self.tools,
            tool_choice="auto"
        )
        
        # Handle tool calls
        if response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                if tool_call.function.name == "categorize_project":
                    # Parse tool arguments
                    tool_args = eval(tool_call.function.arguments)  # In production, use json.loads
                    
                    # Handle the categorization
                    result = await handle_categorize_project_tool(
                        bid_card_id=bid_card_id,
                        project_data=project_data,
                        tool_call_args=tool_args
                    )
                    
                    if result["success"]:
                        # Successful categorization
                        return f"{response.choices[0].message.content}\n\n{result['message']}"
                    else:
                        # Low confidence - agent should ask clarifying question
                        return response.choices[0].message.content
        
        # No tool call needed
        return response.choices[0].message.content

# Example usage in CIA Agent
async def example_cia_integration():
    """Example of how CIA agent would use categorization"""
    
    agent = CategorizedAgent("your-openai-key")
    
    # Scenario 1: Clear project
    project_data = {
        "project_type": "kitchen remodel",
        "title": "Kitchen Renovation", 
        "description": "Complete kitchen makeover with new cabinets, countertops, and appliances"
    }
    
    response1 = await agent.process_project_with_categorization(
        user_message="I want to renovate my kitchen completely",
        project_data=project_data,
        bid_card_id="test-bid-card-1"
    )
    # Expected: "Tagged as Renovation, multi_trade (0.89). Do you need permits for this work?"
    
    # Scenario 2: Ambiguous project  
    project_data_vague = {
        "project_type": "general",
        "title": "Home Project",
        "description": "Need some work done"
    }
    
    response2 = await agent.process_project_with_categorization(
        user_message="I need some work done on my house",
        project_data=project_data_vague,
        bid_card_id="test-bid-card-2"  
    )
    # Expected: "Could you be more specific? Are you looking to install something new, repair existing features, or renovate a room?"
    
    return response1, response2

if __name__ == "__main__":
    import asyncio
    asyncio.run(example_cia_integration())