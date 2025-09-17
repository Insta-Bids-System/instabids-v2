#!/usr/bin/env python3
"""
COIA Company Extraction Node - Dedicated extraction step
This node ONLY extracts company information from messages
"""

import asyncio
import logging
import os
from typing import Any, Dict

from openai import AsyncOpenAI
from dotenv import load_dotenv

from .unified_state import UnifiedCoIAState

# Load environment
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
env_path = os.path.join(root_dir, '.env')
load_dotenv(env_path, override=True)

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
AI_MODEL = "gpt-4o"


async def extraction_node(state: UnifiedCoIAState) -> Dict[str, Any]:
    """
    Dedicated extraction node - extracts company name from any user message
    This runs BEFORE conversation/research and ALWAYS updates state
    """
    try:
        logger.info("🧠 EXTRACTION NODE: Starting company name extraction")
        
        messages = state.get("messages", [])
        company_name = state.get("company_name", "")
        
        # Skip if company already found
        if company_name:
            logger.info(f"Company already extracted: {company_name}")
            return {"company_name": company_name}
        
        # Find the most recent user message
        user_message = None
        for msg in reversed(messages):
            if hasattr(msg, "content") and hasattr(msg, "__class__"):
                if "Human" in msg.__class__.__name__ or getattr(msg, "type", None) == "human":
                    user_message = msg.content
                    break
        
        if not user_message:
            logger.info("No user message found for extraction")
            return {"company_name": ""}
        
        logger.info(f"Extracting from: {user_message[:100]}...")
        
        # DEDICATED EXTRACTION PROMPT - ONLY JOB IS TO FIND COMPANY NAMES
        extraction_prompt = f"""You are a company name extraction specialist. Your ONLY job is to find company names.

Analyze this message and extract the company name if mentioned:

Message: "{user_message}"

EXTRACTION RULES:
1. Look for phrases like "our company is", "we are", "I run", "my business", company introductions
2. Return ONLY the company name (e.g., "Tropical Turf", "ABC Construction", "Smith Landscaping")  
3. Clean up the name (remove "called", "named", etc.)
4. If no company name found, return "NONE"
5. Do not return personal names, only business names

Company name (or NONE):"""

        # Call OpenAI for extraction
        try:
            response = await openai_client.chat.completions.create(
                model=AI_MODEL,
                messages=[{"role": "user", "content": extraction_prompt}],
                max_tokens=50,
                temperature=0.1
            )
            
            extracted_name = response.choices[0].message.content.strip()
            logger.info(f"OpenAI extraction result: '{extracted_name}'")
            
            if extracted_name and extracted_name != "NONE":
                company_name = extracted_name
                logger.info(f"🎯 EXTRACTION SUCCESS: Company name = '{company_name}'")
                
                # Update contractor profile immediately
                contractor_profile = state.get("contractor_profile", {})
                updated_profile = contractor_profile.copy()
                updated_profile["company_name"] = company_name
                
                return {
                    "company_name": company_name,
                    "contractor_profile": updated_profile,
                    "extraction_completed": True
                }
            else:
                logger.info("No company name found in message")
                return {"company_name": "", "extraction_completed": True}
                
        except Exception as e:
            logger.error(f"OpenAI extraction failed: {e}")
            return {"company_name": "", "extraction_completed": False}
            
    except Exception as e:
        logger.error(f"Extraction node error: {e}")
        return {"company_name": "", "extraction_completed": False}