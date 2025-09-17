"""
REAL BSA Agent - No Templates, Pure Intelligence
Built to have genuine conversations and make real decisions
"""

import os
import json
import logging
from typing import Dict, Any, List
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

async def real_bsa_conversation(
    contractor_id: str,
    message: str,
    conversation_history: List[Dict] = None,
    bid_card_id: str = None
):
    """
    REAL intelligent BSA conversation - no templates, no fake responses
    Just pure AI intelligence with proper context and system prompts
    """
    
    # Get OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception("No OpenAI API key configured")
    
    client = AsyncOpenAI(api_key=api_key)
    
    # Load REAL contractor context from database
    try:
        from database_simple import get_client
        supabase = get_client()
    except ImportError:
        # Fallback to database module
        from database import SupabaseDB
        db = SupabaseDB()
        supabase = None
    
    # Get actual contractor profile
    contractor = supabase.table('contractors').select('*').eq('id', contractor_id).execute()
    contractor_lead = supabase.table('contractor_leads').select('*').eq('id', contractor_id).execute()
    
    contractor_context = "Unknown contractor"
    if contractor.data:
        profile = contractor.data[0]
        contractor_context = f"{profile.get('company_name', 'Contractor')} - Verified platform contractor with {profile.get('total_jobs', 0)} completed projects, {profile.get('rating', 0)}/5 rating"
    elif contractor_lead.data:
        profile = contractor_lead.data[0]
        specialties = profile.get('specialties', [])
        contractor_context = f"{profile.get('company_name', 'Contractor')} - {', '.join(specialties)} specialist with {profile.get('years_in_business', 'unknown')} years experience"
    
    # Get REAL AI memory if available
    ai_memory_context = ""
    try:
        from memory.contractor_ai_memory import ContractorAIMemory
        ai_memory = ContractorAIMemory()
        memory_prompt = await ai_memory.get_memory_for_system_prompt(contractor_id)
        if memory_prompt:
            ai_memory_context = f"\n\nContractor Memory Context:\n{memory_prompt}"
    except:
        pass
    
    # REAL system prompt - intelligent, contextual, honest
    system_prompt = f"""You are BSA (Bid Submission Agent) for InstaBids. You help contractors find projects and optimize their bidding.

CONTRACTOR CONTEXT:
{contractor_context}{ai_memory_context}

YOUR ROLE:
- Help contractors find relevant projects in their area
- Provide intelligent advice about bidding and pricing
- Answer questions about the InstaBids platform
- Have natural, helpful conversations

AVAILABLE ACTIONS:
- Search for bid cards/projects in specific locations and radius
- Analyze project requirements and contractor fit
- Provide market insights and bidding advice
- Track contractor interactions and preferences

CONVERSATION STYLE:
- Be direct, helpful, and intelligent
- Use the contractor's actual context and memory
- Make real decisions based on their needs
- Never give template or predetermined responses
- Ask clarifying questions when needed
- Provide specific, actionable advice

SEARCH CAPABILITIES:
When contractors ask for projects, you can:
- Search by location (ZIP code + radius)
- Filter by project type (kitchen, bathroom, landscaping, etc.)
- Consider their specialties and experience level
- Explain why projects are good matches

You are having a real conversation. Respond naturally and intelligently to: "{message}"
"""
    
    # Build conversation with history
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add recent conversation history for context
    if conversation_history:
        for msg in conversation_history[-8:]:  # Last 8 messages for context
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                messages.append(msg)
            elif hasattr(msg, 'type') and hasattr(msg, 'content'):
                role = "assistant" if msg.type == "ai" else "user"
                messages.append({"role": role, "content": msg.content})
    
    # Add current message
    messages.append({"role": "user", "content": message})
    
    logger.info(f"Real BSA: Having intelligent conversation with {contractor_id}")
    logger.info(f"Real BSA: Message: {message}")
    logger.info(f"Real BSA: Context loaded: {len(ai_memory_context) > 0}")
    
    # Stream intelligent response
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        stream=True,
        max_completion_tokens=800,
        temperature=0.8  # More creative and conversational
    )
    
    # Stream the real AI response
    async for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            yield {
                "choices": [{"delta": {"content": chunk.choices[0].delta.content}}],
                "model": "gpt-4o-intelligent",
                "real_ai": True
            }
    
    # End marker
    yield {"choices": [{"delta": {"content": ""}}], "done": True, "model": "gpt-4o-intelligent"}

async def search_projects_intelligently(
    contractor_id: str, 
    search_request: str,
    zip_code: str = None,
    radius: int = 30,
    project_type: str = None
):
    """
    Intelligent project search that actually uses the database
    """
    from database_simple import get_client
    supabase = get_client()
    
    # Search actual bid cards table
    query = supabase.table('bid_cards').select('*')
    
    # Apply filters based on search
    if project_type:
        query = query.ilike('project_type', f'%{project_type}%')
    
    # Execute search
    result = query.limit(10).execute()
    
    projects = []
    if result.data:
        for card in result.data:
            projects.append({
                "id": card["id"],
                "title": card.get("title", "Untitled Project"),
                "project_type": card.get("project_type"),
                "location": card.get("location_zip", "Unknown"),
                "budget_min": card.get("budget_min"),
                "budget_max": card.get("budget_max"),
                "status": card.get("status"),
                "description": card.get("description", "")[:200]
            })
    
    return {
        "success": True,
        "count": len(projects),
        "projects": projects,
        "search_params": {
            "zip_code": zip_code,
            "radius": radius,
            "project_type": project_type,
            "search_request": search_request
        }
    }