"""
LLM-Powered Bid Extraction Tools for BSA API
Intelligent document analysis using OpenAI GPT-4o for accurate quote parsing
"""

import json
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from openai import AsyncOpenAI
import os
from dataclasses import dataclass

@dataclass
class ExtractionResult:
    """Structured result from LLM extraction"""
    bid_amount: Optional[float]
    timeline_days: Optional[int]
    start_date: Optional[str]
    materials_included: bool
    warranty_details: Optional[str]
    payment_schedule: Optional[str]
    proposal: str
    confidence_score: float
    extraction_reasoning: str

# Configure OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def extract_quote_from_document_llm(document_text: str, bid_card_context: dict) -> dict:
    """
    Extract bid details from document text using OpenAI GPT-4o intelligent analysis.
    
    This replaces regex patterns with contextual understanding of contractor quotes.
    """
    
    # Construct intelligent prompt for GPT-4o
    extraction_prompt = f"""
You are an expert construction project analyst. Analyze the following contractor quote document and extract key bid information with high accuracy.

DOCUMENT TO ANALYZE:
{document_text}

PROJECT CONTEXT:
{json.dumps(bid_card_context, indent=2)}

EXTRACTION REQUIREMENTS:
1. Find the TOTAL PROJECT COST (not individual line items)
2. Determine project timeline in days
3. Identify if materials are included in the price
4. Extract warranty information
5. Find payment schedule/terms
6. Create a professional project proposal summary

OUTPUT FORMAT (JSON):
{{
    "bid_amount": <float or null>,
    "timeline_days": <integer or null>,
    "start_date": <"YYYY-MM-DD" or null>,
    "materials_included": <boolean>,
    "warranty_details": <string or null>,
    "payment_schedule": <string or null>,
    "proposal": <string>,
    "confidence_score": <float 0.0-1.0>,
    "extraction_reasoning": <string explaining your analysis>
}}

CRITICAL INSTRUCTIONS:
- For bid_amount: Look for "TOTAL", "TOTAL PROJECT COST", final sum amounts, not individual line items
- For timeline_days: Convert weeks to days (multiply by 7), look for "timeline", "duration", "completion"
- For materials_included: Look for phrases like "materials included", "all materials", "material costs included"
- For warranty_details: Extract complete warranty information, not just "warranty"
- For payment_schedule: Find payment terms, deposit requirements, milestone payments
- For proposal: Summarize the scope of work professionally
- For confidence_score: Rate your confidence in the extraction accuracy (0.0-1.0)
- For extraction_reasoning: Explain how you determined each value

ACCURACY IS CRITICAL: This data will be used for real bid submissions. Ensure TOTAL amounts are correct.
"""

    try:
        # Call OpenAI GPT-4o for intelligent extraction
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert construction document analyzer. Provide accurate, structured extraction of bid information from contractor quotes. Always return valid JSON."
                },
                {"role": "user", "content": extraction_prompt}
            ],
            temperature=0.1,  # Low temperature for accuracy
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        # Parse LLM response
        llm_result = json.loads(response.choices[0].message.content)
        
        # Validate and clean extracted data
        extracted = {
            "bid_amount": _safe_float(llm_result.get("bid_amount")),
            "timeline_days": _safe_int(llm_result.get("timeline_days")),
            "start_date": llm_result.get("start_date"),
            "materials_included": bool(llm_result.get("materials_included", False)),
            "warranty_details": _clean_text(llm_result.get("warranty_details")),
            "payment_schedule": _clean_text(llm_result.get("payment_schedule")),
            "proposal": _clean_text(llm_result.get("proposal", "")),
            "confidence_scores": {
                "overall": float(llm_result.get("confidence_score", 0.0)),
                "bid_amount": 0.9 if llm_result.get("bid_amount") else 0.0,
                "timeline_days": 0.9 if llm_result.get("timeline_days") else 0.0,
                "materials_included": 0.8,
                "warranty_details": 0.8 if llm_result.get("warranty_details") else 0.0,
                "payment_schedule": 0.8 if llm_result.get("payment_schedule") else 0.0,
                "proposal": 0.9 if llm_result.get("proposal") else 0.0
            },
            "extraction_method": "llm_gpt4o",
            "extraction_reasoning": llm_result.get("extraction_reasoning", "LLM-powered extraction completed")
        }
        
        return extracted
        
    except Exception as e:
        print(f"LLM extraction failed: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to basic document analysis if LLM fails
        fallback_result = await _fallback_extraction(document_text)
        fallback_result["llm_error"] = str(e)
        return fallback_result

async def extract_quote_with_context_awareness(document_text: str, bid_card_context: dict) -> dict:
    """
    Enhanced extraction with project context awareness.
    
    Uses bid card context to improve extraction accuracy.
    """
    
    project_type = bid_card_context.get("project_type", "general renovation")
    budget_range = f"${bid_card_context.get('budget_min', 0):,} - ${bid_card_context.get('budget_max', 100000):,}"
    timeline_hint = bid_card_context.get("timeline_days", "flexible")
    
    context_prompt = f"""
You are analyzing a contractor quote for a {project_type} project.

EXPECTED PROJECT DETAILS:
- Project Type: {project_type}
- Expected Budget Range: {budget_range}
- Expected Timeline: {timeline_hint} days
- Project Requirements: {json.dumps(bid_card_context.get('requirements', []), indent=2)}

DOCUMENT TO ANALYZE:
{document_text}

Use this context to improve extraction accuracy. If the extracted bid amount seems reasonable for a {project_type} project in the {budget_range} range, increase confidence scores.

Focus on finding:
1. TOTAL PROJECT COST (should align with {budget_range})
2. Project timeline for {project_type}
3. Materials inclusion for {project_type} work
4. Warranty appropriate for {project_type}
5. Payment terms suitable for {budget_range} project

Return the same JSON format as before, but with context-aware confidence scores.
"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a construction project analyst with deep knowledge of project types, typical costs, and industry standards. Use project context to improve extraction accuracy."
                },
                {"role": "user", "content": context_prompt}
            ],
            temperature=0.1,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        llm_result = json.loads(response.choices[0].message.content)
        
        # Enhanced validation with context
        extracted = {
            "bid_amount": _safe_float(llm_result.get("bid_amount")),
            "timeline_days": _safe_int(llm_result.get("timeline_days")),
            "start_date": llm_result.get("start_date"),
            "materials_included": bool(llm_result.get("materials_included", False)),
            "warranty_details": _clean_text(llm_result.get("warranty_details")),
            "payment_schedule": _clean_text(llm_result.get("payment_schedule")),
            "proposal": _clean_text(llm_result.get("proposal", "")),
            "confidence_scores": {
                "overall": float(llm_result.get("confidence_score", 0.0)),
                "bid_amount": _validate_amount_confidence(llm_result.get("bid_amount"), bid_card_context),
                "timeline_days": _validate_timeline_confidence(llm_result.get("timeline_days"), bid_card_context),
                "materials_included": 0.9,
                "warranty_details": 0.8 if llm_result.get("warranty_details") else 0.0,
                "payment_schedule": 0.8 if llm_result.get("payment_schedule") else 0.0,
                "proposal": 0.9 if llm_result.get("proposal") else 0.0
            },
            "extraction_method": "llm_context_aware",
            "extraction_reasoning": llm_result.get("extraction_reasoning", "Context-aware LLM extraction completed"),
            "context_validation": _validate_against_context(llm_result, bid_card_context)
        }
        
        return extracted
        
    except Exception as e:
        print(f"Context-aware extraction failed: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to basic LLM extraction
        fallback_result = await extract_quote_from_document_llm(document_text, bid_card_context)
        fallback_result["context_aware_error"] = str(e)
        return fallback_result

async def parse_verbal_bid_llm(conversation: str, bid_card_id: str, contractor_context: dict) -> dict:
    """
    Parse bid details from verbal conversation using LLM intelligence.
    """
    
    conversation_prompt = f"""
Analyze this contractor conversation and extract bid information:

CONVERSATION:
{conversation}

CONTRACTOR CONTEXT:
{json.dumps(contractor_context, indent=2)}

Extract bid details from this conversation. Look for:
- Quoted prices or cost estimates
- Timeline mentions
- Material inclusion discussions
- Warranty offers
- Payment terms discussed

Return the standard JSON extraction format.
"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are analyzing contractor conversations to extract bid information. Focus on stated prices, timelines, and commitments made in the conversation."
                },
                {"role": "user", "content": conversation_prompt}
            ],
            temperature=0.1,
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        
        llm_result = json.loads(response.choices[0].message.content)
        
        parsed = {
            "bid_card_id": bid_card_id,
            "contractor_id": contractor_context.get("contractor_id"),
            "contractor_name": contractor_context.get("company_name", "Contractor"),
            "bid_amount": _safe_float(llm_result.get("bid_amount")),
            "timeline_days": _safe_int(llm_result.get("timeline_days")),
            "start_date": llm_result.get("start_date"),
            "materials_included": bool(llm_result.get("materials_included", False)),
            "warranty_details": _clean_text(llm_result.get("warranty_details")),
            "payment_schedule": _clean_text(llm_result.get("payment_schedule")),
            "proposal": _clean_text(llm_result.get("proposal", conversation[:500])),
            "submission_method": "bsa_verbal_llm",
            "confidence_scores": {
                "overall": float(llm_result.get("confidence_score", 0.0))
            },
            "extraction_reasoning": llm_result.get("extraction_reasoning", "Verbal conversation analysis")
        }
        
        return parsed
        
    except Exception as e:
        print(f"Verbal bid parsing failed: {e}")
        return {
            "bid_card_id": bid_card_id,
            "contractor_id": contractor_context.get("contractor_id"),
            "contractor_name": contractor_context.get("company_name", "Contractor"),
            "bid_amount": None,
            "timeline_days": None,
            "materials_included": False,
            "proposal": conversation[:500],
            "submission_method": "bsa_verbal_fallback",
            "error": str(e)
        }

# Helper functions for data validation and cleaning

def _safe_float(value: Any) -> Optional[float]:
    """Safely convert value to float"""
    if value is None:
        return None
    try:
        if isinstance(value, str):
            # Remove currency symbols and commas
            cleaned = value.replace('$', '').replace(',', '').strip()
            return float(cleaned)
        return float(value)
    except (ValueError, TypeError):
        return None

def _safe_int(value: Any) -> Optional[int]:
    """Safely convert value to int"""
    if value is None:
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None

def _clean_text(value: Any) -> Optional[str]:
    """Clean and validate text values"""
    if not value or value in ['null', 'None', '']:
        return None
    return str(value).strip()

def _validate_amount_confidence(amount: Any, context: dict) -> float:
    """Validate bid amount against project context"""
    if not amount:
        return 0.0
    
    try:
        amount_val = float(amount)
        budget_min = context.get("budget_min", 0)
        budget_max = context.get("budget_max", float('inf'))
        
        if budget_min <= amount_val <= budget_max:
            return 0.95  # High confidence for amounts in range
        elif budget_min * 0.5 <= amount_val <= budget_max * 1.5:
            return 0.8   # Good confidence for reasonable amounts
        else:
            return 0.6   # Lower confidence for outlier amounts
    except:
        return 0.5

def _validate_timeline_confidence(timeline: Any, context: dict) -> float:
    """Validate timeline against project context"""
    if not timeline:
        return 0.0
        
    try:
        days = int(timeline)
        expected_days = context.get("timeline_days", 30)
        
        if 0.5 <= days / expected_days <= 2.0:
            return 0.9   # High confidence for reasonable timelines
        else:
            return 0.7   # Lower confidence for outlier timelines
    except:
        return 0.5

def _validate_against_context(extraction: dict, context: dict) -> dict:
    """Validate extraction results against project context"""
    validation = {
        "amount_reasonable": False,
        "timeline_reasonable": False,
        "materials_match": False,
        "overall_match": False
    }
    
    # Validate amount
    if extraction.get("bid_amount"):
        budget_min = context.get("budget_min", 0)
        budget_max = context.get("budget_max", float('inf'))
        amount = float(extraction["bid_amount"])
        validation["amount_reasonable"] = budget_min * 0.5 <= amount <= budget_max * 1.5
    
    # Validate timeline
    if extraction.get("timeline_days"):
        expected = context.get("timeline_days", 30)
        actual = int(extraction["timeline_days"])
        validation["timeline_reasonable"] = 0.3 <= actual / expected <= 3.0
    
    # Overall validation
    validation["overall_match"] = (
        validation["amount_reasonable"] and 
        validation["timeline_reasonable"]
    )
    
    return validation

async def _fallback_extraction(document_text: str) -> dict:
    """Fallback extraction if LLM fails"""
    return {
        "bid_amount": None,
        "timeline_days": None,
        "start_date": None,
        "materials_included": False,
        "warranty_details": None,
        "payment_schedule": None,
        "proposal": document_text[:500] if document_text else "",
        "confidence_scores": {"overall": 0.1},
        "extraction_method": "fallback",
        "extraction_reasoning": "LLM extraction failed, using fallback",
        "error": "LLM extraction unavailable"
    }

# Maintain compatibility with existing API
async def extract_quote_from_document(document_text: str, bid_card_context: dict) -> dict:
    """
    Main extraction function - now uses LLM intelligence instead of regex.
    
    This maintains API compatibility while providing intelligent extraction.
    """
    return await extract_quote_with_context_awareness(document_text, bid_card_context)