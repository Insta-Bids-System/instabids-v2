"""
Simple bid extraction functions for BSA API
Direct async functions without LangChain tool decorators
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

async def extract_quote_from_document(document_text: str, bid_card_context: dict) -> dict:
    """
    Extract bid details from document text using regex and pattern matching.
    """
    
    extracted = {
        "bid_amount": None,
        "timeline_days": None,
        "start_date": None,
        "materials_included": False,
        "warranty_details": None,
        "payment_schedule": None,
        "proposal": "",
        "confidence_scores": {}
    }
    
    # Extract bid amount
    money_patterns = [
        r'\$\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)',  # $52,500 or $52,500.00 (proper comma grouping)
        r'total[:\s]+\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)',  # Total: $52,500
        r'amount[:\s]+\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)',  # Amount: $52,500
        r'price[:\s]+\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)',  # Price: $52,500
        r'cost[:\s]+\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)',   # Cost: $52,500
        r'\$\s*([0-9]+\.?[0-9]*)',  # Fallback for amounts without commas
    ]
    
    for pattern in money_patterns:
        match = re.search(pattern, document_text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                extracted["bid_amount"] = float(amount_str)
                extracted["confidence_scores"]["bid_amount"] = 0.9
                break
            except ValueError:
                continue
    
    # Extract timeline
    timeline_patterns = [
        r'(\d+)\s*-?\s*(\d+)?\s*weeks?',  # 5-6 weeks or 5 weeks
        r'timeline[:\s]+(\d+)\s*weeks?',   # Timeline: 5 weeks
        r'duration[:\s]+(\d+)\s*weeks?',   # Duration: 5 weeks
        r'(\d+)\s*days?',                  # 30 days
    ]
    
    for pattern in timeline_patterns:
        match = re.search(pattern, document_text, re.IGNORECASE)
        if match:
            if 'week' in pattern:
                weeks = int(match.group(1))
                extracted["timeline_days"] = weeks * 7
                extracted["confidence_scores"]["timeline_days"] = 0.8
            elif 'day' in pattern:
                extracted["timeline_days"] = int(match.group(1))
                extracted["confidence_scores"]["timeline_days"] = 0.9
            break
    
    # Check for materials included
    materials_keywords = ['materials included', 'materials: included', 'all materials', 'material costs']
    if any(keyword in document_text.lower() for keyword in materials_keywords):
        extracted["materials_included"] = True
        extracted["confidence_scores"]["materials_included"] = 0.7
    
    # Extract warranty information
    warranty_patterns = [
        r'warranty[:\s]+([^.\n]+)',
        r'guaranteed?[:\s]+([^.\n]+)',
        r'(\d+)\s*years?\s*warranty',
    ]
    
    for pattern in warranty_patterns:
        match = re.search(pattern, document_text, re.IGNORECASE)
        if match:
            extracted["warranty_details"] = match.group(0).strip()
            extracted["confidence_scores"]["warranty_details"] = 0.6
            break
    
    # Extract payment schedule
    payment_patterns = [
        r'payment[:\s]+([^.\n]+)',
        r'(\d+%[^.\n]+)',
        r'deposit[:\s]+([^.\n]+)',
    ]
    
    for pattern in payment_patterns:
        match = re.search(pattern, document_text, re.IGNORECASE)
        if match:
            extracted["payment_schedule"] = match.group(0).strip()
            extracted["confidence_scores"]["payment_schedule"] = 0.6
            break
    
    # Create basic proposal from document
    lines = document_text.strip().split('\n')
    proposal_lines = []
    
    for line in lines[:10]:  # First 10 lines
        line = line.strip()
        if line and len(line) > 10 and not any(skip in line.lower() for skip in ['phone', 'email', 'contact']):
            proposal_lines.append(line)
    
    if proposal_lines:
        extracted["proposal"] = ' '.join(proposal_lines)
        extracted["confidence_scores"]["proposal"] = 0.5
    
    return extracted

async def parse_verbal_bid(conversation: str, bid_card_id: str, contractor_context: dict) -> dict:
    """
    Parse bid details from verbal conversation.
    """
    
    parsed = {
        "bid_card_id": bid_card_id,
        "contractor_id": contractor_context.get("contractor_id"),
        "contractor_name": contractor_context.get("company_name", "Contractor"),
        "bid_amount": None,
        "timeline_days": None,
        "start_date": None,
        "materials_included": False,
        "warranty_details": None,
        "payment_schedule": None,
        "proposal": conversation[:500],  # First 500 chars as proposal
        "submission_method": "bsa_verbal"
    }
    
    # Use same extraction logic as document processing
    extracted = await extract_quote_from_document(conversation, {})
    parsed.update(extracted)
    
    return parsed

async def validate_bid_completeness(bid_data: dict, requirements: dict) -> Tuple[bool, List[str]]:
    """
    Validate that bid has all required fields.
    """
    
    issues = []
    
    # Required fields
    required_fields = ["bid_amount", "timeline_days", "proposal"]
    
    for field in required_fields:
        if not bid_data.get(field):
            issues.append(f"Missing required field: {field}")
    
    # Validate bid amount is reasonable
    if bid_data.get("bid_amount"):
        amount = float(bid_data["bid_amount"])
        budget_min = requirements.get("budget_min", 0)
        budget_max = requirements.get("budget_max", float('inf'))
        
        if budget_min > 0 and amount < budget_min * 0.5:
            issues.append(f"Bid amount ${amount:,} seems unusually low for this project")
        elif budget_max < float('inf') and amount > budget_max * 2:
            issues.append(f"Bid amount ${amount:,} seems unusually high for this project")
    
    # Validate timeline
    if bid_data.get("timeline_days"):
        days = int(bid_data["timeline_days"])
        if days < 1:
            issues.append("Timeline must be at least 1 day")
        elif days > 365:
            issues.append("Timeline seems unreasonably long (over 1 year)")
    
    is_valid = len(issues) == 0
    return is_valid, issues

async def submit_contractor_bid(bid_data: dict, attachments: Optional[List[str]] = None, chat_session_id: Optional[str] = None) -> dict:
    """
    Submit bid to database (simplified version).
    """
    
    try:
        # Import database
        from database_simple import db
        
        # Create bid record
        bid_record = {
            "id": f"bid-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "bid_card_id": bid_data.get("bid_card_id"),
            "contractor_id": bid_data.get("contractor_id"),
            "bid_amount": bid_data.get("bid_amount"),
            "timeline_days": bid_data.get("timeline_days"),
            "proposal": bid_data.get("proposal", ""),
            "materials_included": bid_data.get("materials_included", False),
            "warranty_details": bid_data.get("warranty_details"),
            "payment_schedule": bid_data.get("payment_schedule"),
            "submission_method": bid_data.get("submission_method", "bsa_chat"),
            "chat_session_id": chat_session_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": "submitted"
        }
        
        # For now, just return success (would normally save to database)
        return {
            "success": True,
            "bid_id": bid_record["id"],
            "message": "Bid submitted successfully",
            "bid_data": bid_record
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to submit bid"
        }

async def get_bid_card_requirements(bid_card_id: str) -> dict:
    """
    Get bid card requirements and context.
    """
    
    # Simplified version - would normally fetch from database
    return {
        "id": bid_card_id,
        "project_type": "kitchen_remodel",
        "budget_min": 40000,
        "budget_max": 70000,
        "timeline_days": 42,
        "requirements": [
            "Licensed and insured contractor",
            "Experience with kitchen renovations",
            "Detailed proposal with timeline",
            "Material specifications"
        ]
    }

async def format_bid_proposal(bid_data: dict, contractor_context: dict) -> str:
    """
    Format a professional bid proposal.
    """
    
    company_name = contractor_context.get("company_name", "Contractor")
    bid_amount = bid_data.get("bid_amount", 0)
    timeline_days = bid_data.get("timeline_days", 0)
    timeline_weeks = timeline_days // 7 if timeline_days else 0
    
    proposal = f"""
PROPOSAL FROM {company_name.upper()}

Project: Kitchen Renovation
Total Investment: ${bid_amount:,.2f}
Timeline: {timeline_weeks} weeks ({timeline_days} days)

SCOPE OF WORK:
{bid_data.get('proposal', 'Complete kitchen renovation as specified')}

MATERIALS: {'Included' if bid_data.get('materials_included') else 'Client responsibility'}

WARRANTY: {bid_data.get('warranty_details', 'Standard 1-year warranty on workmanship')}

PAYMENT TERMS: {bid_data.get('payment_schedule', 'Standard payment schedule')}

We look forward to working with you on this project.
    """
    
    return proposal.strip()