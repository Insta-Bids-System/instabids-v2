#!/usr/bin/env python3
"""
Enhanced Iris Context - Add Cross-Agent Memory Access
This shows what needs to be added to make Iris truly intelligent across agents
"""

import requests
from datetime import datetime
from config.service_urls import get_backend_url

def get_enhanced_context_for_iris(user_id: str, current_conversation_id: str) -> dict:
    """
    Enhanced context that Iris should have but currently doesn't
    This would make Iris truly intelligent across all agent interactions
    """
    
    enhanced_context = {
        "homeowner_profile": {},
        "past_projects": [],
        "cia_conversations": [],
        "design_history": [],
        "budget_context": {},
        "timeline_preferences": {}
    }
    
    try:
        # Get ALL homeowner conversations across agents
        response = requests.get(f"{get_backend_url()}/api/conversations/user/{user_id}")
        
        if response.ok:
            conversations = response.json().get("conversations", [])
            
            for conv in conversations:
                # Get full conversation details
                detail_response = requests.get(f"{get_backend_url()}/api/conversations/{conv['id']}")
                
                if detail_response.ok:
                    conv_data = detail_response.json()
                    
                    # CIA conversations (project planning)
                    if conv_data.get("conversation", {}).get("conversation_type") == "project_setup":
                        cia_context = extract_cia_context(conv_data)
                        enhanced_context["cia_conversations"].append(cia_context)
                    
                    # Previous Iris conversations (design history)
                    elif conv_data.get("conversation", {}).get("conversation_type") == "design_inspiration":
                        if conv_data.get("conversation", {}).get("id") != current_conversation_id:
                            design_context = extract_design_context(conv_data)
                            enhanced_context["design_history"].append(design_context)
                    
                    # Extract cross-agent memory
                    memory_items = conv_data.get("memory", [])
                    for memory in memory_items:
                        if memory.get("memory_type") == "project_context":
                            enhanced_context["past_projects"].append(memory.get("memory_value"))
                        elif memory.get("memory_type") == "budget_preferences":
                            enhanced_context["budget_context"] = memory.get("memory_value")
                        elif memory.get("memory_type") == "timeline_preferences":
                            enhanced_context["timeline_preferences"] = memory.get("memory_value")
    
    except Exception as e:
        print(f"Error getting enhanced context: {e}")
    
    return enhanced_context

def extract_cia_context(conv_data: dict) -> dict:
    """Extract relevant context from CIA conversations"""
    messages = conv_data.get("messages", [])
    
    cia_context = {
        "project_type": None,
        "budget_mentioned": None,
        "timeline_mentioned": None,
        "specific_requirements": [],
        "conversation_date": conv_data.get("conversation", {}).get("created_at")
    }
    
    # Analyze messages for project context
    for message in messages:
        content = message.get("content", "").lower()
        
        # Extract project types
        if any(word in content for word in ["kitchen", "bathroom", "living room", "bedroom"]):
            project_types = [word for word in ["kitchen", "bathroom", "living room", "bedroom"] if word in content]
            cia_context["project_type"] = project_types
        
        # Extract budget mentions
        if any(word in content for word in ["budget", "cost", "price", "$", "thousand", "dollars"]):
            cia_context["budget_mentioned"] = content
        
        # Extract timeline mentions
        if any(word in content for word in ["week", "month", "soon", "urgent", "timeline"]):
            cia_context["timeline_mentioned"] = content
        
        # Extract specific requirements
        if any(word in content for word in ["want", "need", "prefer", "like", "must have"]):
            cia_context["specific_requirements"].append(content)
    
    return cia_context

def extract_design_context(conv_data: dict) -> dict:
    """Extract design preferences from previous Iris conversations"""
    design_context = {
        "style_preferences": [],
        "color_preferences": [],
        "material_preferences": [],
        "room_focus": None,
        "conversation_date": conv_data.get("conversation", {}).get("created_at")
    }
    
    # Extract from memory if available
    memory_items = conv_data.get("memory", [])
    for memory in memory_items:
        if memory.get("memory_type") == "design_preferences":
            preferences = memory.get("memory_value", {}).get("preferences", {})
            design_context.update(preferences)
    
    return design_context

def build_enhanced_iris_prompt(enhanced_context: dict, current_room_type: str, current_message: str) -> str:
    """Build an enhanced system prompt for Iris with full context"""
    
    prompt = f"""You are Iris, InstaBids' expert interior design assistant. You have access to this homeowner's complete project history and preferences.

HOMEOWNER'S COMPLETE CONTEXT:

PAST CIA CONVERSATIONS (Project Planning):"""
    
    for cia_conv in enhanced_context.get("cia_conversations", []):
        prompt += f"""
- Project Type: {cia_conv.get('project_type', 'Not specified')}
- Budget Context: {cia_conv.get('budget_mentioned', 'Not discussed')}
- Timeline: {cia_conv.get('timeline_mentioned', 'Not discussed')}
- Requirements: {'; '.join(cia_conv.get('specific_requirements', [])[:2])}"""

    prompt += f"""

PREVIOUS DESIGN CONVERSATIONS:"""
    
    for design_conv in enhanced_context.get("design_history", []):
        prompt += f"""
- Style Preferences: {design_conv.get('preferred_styles', [])}
- Color Preferences: {design_conv.get('color_preferences', [])}
- Materials: {design_conv.get('material_preferences', [])}"""

    prompt += f"""

CURRENT CONVERSATION:
- Room Type: {current_room_type}
- Current Message: {current_message}

YOUR ENHANCED CAPABILITIES:
- Reference past projects and show awareness of their journey
- Connect design choices to previously mentioned budgets/timelines
- Build on previous design conversations to show continuity
- Provide contextually aware suggestions based on their full history

Respond as Iris with full awareness of this homeowner's complete project and design journey."""
    
    return prompt

if __name__ == "__main__":
    # Example usage
    TEST_HOMEOWNER_ID = "bda3ab78-e034-4be7-8285-1b7be1bf1387"
    
    print("ENHANCED IRIS CONTEXT DEMONSTRATION")
    print("="*50)
    
    # Get enhanced context (this is what Iris SHOULD see but currently doesn't)
    context = get_enhanced_context_for_iris(TEST_HOMEOWNER_ID, "current_conv_id")
    
    print("Enhanced context Iris should have:")
    print(f"- CIA Conversations: {len(context['cia_conversations'])}")
    print(f"- Design History: {len(context['design_history'])}")
    print(f"- Past Projects: {len(context['past_projects'])}")
    
    # Show what an enhanced prompt would look like
    enhanced_prompt = build_enhanced_iris_prompt(
        context, 
        "kitchen", 
        "I want to update my kitchen to match the style we discussed before"
    )
    
    print(f"\nEnhanced prompt length: {len(enhanced_prompt)} characters")
    print("This would give Iris TRUE cross-agent intelligence!")