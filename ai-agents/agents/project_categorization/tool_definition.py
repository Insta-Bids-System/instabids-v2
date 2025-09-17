"""
SHARED CATEGORIZATION TOOL DEFINITION
Used by both CIA and IRIS agents for project categorization
"""

CATEGORIZATION_TOOL = {
    "type": "function",
    "function": {
        "name": "categorize_project",
        "description": "Intelligently categorize a home improvement project with 4-tier classification system. Only call when you need to categorize project details from homeowner conversation.",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Full project description from homeowner conversation, including all details mentioned"
                },
                "bid_card_id": {
                    "type": "string", 
                    "description": "ID of bid card to categorize and update"
                },
                "context": {
                    "type": "string",
                    "description": "Additional context like urgency indicators, photo analysis results, or conversation hints",
                    "default": ""
                }
            },
            "required": ["description", "bid_card_id"]
        }
    }
}

# System prompt addition for agents
CATEGORIZATION_SYSTEM_PROMPT = """
CATEGORIZATION TOOL USAGE:

You have access to a categorize_project tool for standardizing home improvement projects into a 4-tier system:
- Service Category: What type of service (installation, repair, renovation, etc.)
- Project Type: Specific project (toilet_repair, turf_installation, etc.) 
- Trade Category: Auto-assigned primary trade (plumbing, landscaping, etc.)
- Contractor Types: Eligible contractor types for this project

WHEN TO USE THIS TOOL:
- After extracting project details from homeowner conversation
- When you have enough information to categorize the project  
- When bid card ID is available for updating

HOW TO USE:
1. Extract the complete project description from conversation
2. Include any urgency, timeline, or scope indicators as context
3. Call categorize_project with description and bid_card_id

TOOL BEHAVIOR:
- High confidence (≥0.7): Tool saves categorization and confirms success
- Low confidence (<0.7): Tool asks ONE clarifying question instead of saving
- Error handling: Tool provides fallback categorization or error message

CONVERSATIONAL RESPONSE:
- Success: "Tagged this as [Trade] → [Project Type] work with [confidence]% confidence. [follow-up question]"
- Clarification needed: Pass through the clarifying question from tool
- Error: "I need a bit more detail to properly categorize this project. Could you tell me..."

Example usage:
User: "I need to fix my leaking toilet that keeps running"
→ Call categorize_project(description="fix leaking toilet that keeps running", bid_card_id="abc123", context="urgency: standard")
→ Response: "Tagged this as Plumbing → Toilet Repair work with 92% confidence. Do you want me to find contractors right away?"
"""