"""
BSA Bid Submission Tools
Handles quote extraction, parsing, and bid submission for contractors
"""

import json
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from langchain.tools import tool
import asyncio

# Import document processing capabilities
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    import io
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


@tool
async def extract_quote_from_document(
    document_text: str,
    bid_card_context: dict
) -> dict:
    """
    Extract bid details from uploaded document text.
    Intelligently parses various CRM formats and contractor quotes.
    
    Args:
        document_text: Extracted text from PDF/image
        bid_card_context: Context about the bid card project
        
    Returns:
        Extracted bid data with confidence scores
    """
    
    extracted = {
        "bid_amount": None,
        "timeline_days": None,
        "start_date": None,
        "materials_included": False,
        "warranty_terms": None,
        "payment_schedule": None,
        "confidence_scores": {}
    }
    
    # Extract bid amount
    amount_patterns = [
        r"\$[\d,]+(?:\.\d{2})?",  # $45,000.00
        r"(?:total|quote|bid|price)[\s:]+\$?([\d,]+)",  # Total: 45000
        r"(?:amount|cost)[\s:]+\$?([\d,]+)",  # Amount: 45000
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, document_text, re.IGNORECASE)
        if match:
            amount_str = match.group(1) if match.groups() else match.group(0)
            amount_str = re.sub(r"[$,]", "", amount_str)
            try:
                extracted["bid_amount"] = float(amount_str)
                extracted["confidence_scores"]["bid_amount"] = 0.9
                break
            except ValueError:
                pass
    
    # Extract timeline
    timeline_patterns = [
        r"(\d+)\s*(?:weeks?|wks?)",
        r"(\d+)\s*(?:days?)",
        r"(?:timeline|duration|schedule)[\s:]+(\d+)",
        r"(?:completion|complete)[\s:]+(\d+)\s*(?:weeks?|days?)",
    ]
    
    for pattern in timeline_patterns:
        match = re.search(pattern, document_text, re.IGNORECASE)
        if match:
            timeline_value = int(match.group(1))
            if "week" in match.group(0).lower():
                timeline_value *= 7  # Convert weeks to days
            extracted["timeline_days"] = timeline_value
            extracted["confidence_scores"]["timeline_days"] = 0.85
            break
    
    # Extract start date
    date_patterns = [
        r"(?:start|begin|commence)[\s:]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"(?:available|availability)[\s:]+(\w+\s+\d{1,2})",
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, document_text, re.IGNORECASE)
        if match:
            extracted["start_date"] = match.group(1)
            extracted["confidence_scores"]["start_date"] = 0.7
            break
    
    # Check for materials inclusion
    if re.search(r"materials?\s+included|including\s+materials?|all\s+inclusive", 
                 document_text, re.IGNORECASE):
        extracted["materials_included"] = True
        extracted["confidence_scores"]["materials_included"] = 0.9
    
    # Extract warranty
    warranty_match = re.search(r"(\d+)\s*(?:year|yr|month|mo)?\s*warranty", 
                              document_text, re.IGNORECASE)
    if warranty_match:
        extracted["warranty_terms"] = warranty_match.group(0)
        extracted["confidence_scores"]["warranty_terms"] = 0.85
    
    # Extract payment terms
    if "deposit" in document_text.lower() or "payment" in document_text.lower():
        payment_patterns = [
            r"(\d+)%?\s*(?:deposit|down|upfront)",
            r"(?:payment|terms)[\s:]+([^\n]+)",
        ]
        for pattern in payment_patterns:
            match = re.search(pattern, document_text, re.IGNORECASE)
            if match:
                extracted["payment_schedule"] = match.group(0)
                extracted["confidence_scores"]["payment_schedule"] = 0.75
                break
    
    # Extract approach/methodology
    approach_keywords = ["approach", "methodology", "process", "scope", "includes"]
    for keyword in approach_keywords:
        pattern = f"{keyword}[:\\s]+([^\\n]+(?:\\n[^\\n]+){{0,3}})"
        match = re.search(pattern, document_text, re.IGNORECASE)
        if match:
            extracted["technical_approach"] = match.group(1).strip()
            extracted["confidence_scores"]["technical_approach"] = 0.7
            break
    
    # Calculate overall confidence
    if extracted["confidence_scores"]:
        extracted["overall_confidence"] = sum(extracted["confidence_scores"].values()) / len(extracted["confidence_scores"])
    else:
        extracted["overall_confidence"] = 0.0
    
    return extracted


@tool
async def parse_verbal_bid(
    conversation: str,
    bid_card_id: str,
    contractor_context: dict
) -> dict:
    """
    Parse bid details from conversational input.
    
    Args:
        conversation: The conversation text about the bid
        bid_card_id: ID of the bid card being quoted
        contractor_context: Context about the contractor
        
    Returns:
        Structured bid data from conversation
    """
    
    bid_data = {
        "bid_card_id": bid_card_id,
        "contractor_id": contractor_context.get("contractor_id"),
        "contractor_name": contractor_context.get("company_name"),
        "bid_amount": None,
        "timeline_days": None,
        "proposal": "",
        "materials_included": False,
        "warranty_details": None,
        "approach": "",
        "milestones": []
    }
    
    # Parse amount from conversation
    amount_phrases = [
        r"(?:do it for|quote|bid|price is|charge|cost)\s*\$?([\d,]+)",
        r"\$?([\d,]+)(?:\s*(?:dollars?|k|thousand))",
        r"(?:my price|total)\s*(?:is|would be)?\s*\$?([\d,]+)",
    ]
    
    for pattern in amount_phrases:
        match = re.search(pattern, conversation, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(",", "")
            if "k" in match.group(0).lower() or "thousand" in match.group(0).lower():
                bid_data["bid_amount"] = float(amount_str) * 1000
            else:
                bid_data["bid_amount"] = float(amount_str)
            break
    
    # Parse timeline
    timeline_phrases = [
        r"(?:take|complete|finish|done in|need)\s*(?:about|approximately|around)?\s*(\d+)\s*(?:weeks?|days?)",
        r"(\d+)\s*(?:week|day)\s*(?:timeline|schedule|project)",
    ]
    
    for pattern in timeline_phrases:
        match = re.search(pattern, conversation, re.IGNORECASE)
        if match:
            timeline_value = int(match.group(1))
            if "week" in match.group(0).lower():
                timeline_value *= 7
            bid_data["timeline_days"] = timeline_value
            break
    
    # Check for materials
    if re.search(r"(?:materials?|supplies)\s*(?:included|covered|in price)", 
                 conversation, re.IGNORECASE):
        bid_data["materials_included"] = True
    elif re.search(r"(?:plus|additional|separate)\s*materials?", 
                   conversation, re.IGNORECASE):
        bid_data["materials_included"] = False
    
    # Extract warranty
    warranty_match = re.search(r"(\d+)\s*(?:year|month)\s*warranty", 
                              conversation, re.IGNORECASE)
    if warranty_match:
        bid_data["warranty_details"] = warranty_match.group(0)
    
    # Build proposal text from key points
    proposal_parts = []
    if bid_data["bid_amount"]:
        proposal_parts.append(f"Total bid amount: ${bid_data['bid_amount']:,.2f}")
    if bid_data["timeline_days"]:
        proposal_parts.append(f"Timeline: {bid_data['timeline_days']} days")
    if bid_data["materials_included"]:
        proposal_parts.append("All materials included in price")
    if bid_data["warranty_details"]:
        proposal_parts.append(f"Warranty: {bid_data['warranty_details']}")
    
    bid_data["proposal"] = "\n".join(proposal_parts)
    
    return bid_data


@tool
async def validate_bid_completeness(
    bid_data: dict,
    bid_card_requirements: dict
) -> Tuple[bool, List[str]]:
    """
    Validate that bid has all required fields and meets requirements.
    
    Args:
        bid_data: The bid data to validate
        bid_card_requirements: Requirements from the bid card
        
    Returns:
        Tuple of (is_valid, list_of_missing_or_invalid_fields)
    """
    
    issues = []
    
    # Check required fields
    required_fields = ["bid_amount", "timeline_days", "proposal"]
    for field in required_fields:
        if not bid_data.get(field):
            issues.append(f"Missing required field: {field}")
    
    # Validate bid amount is within reasonable range
    if bid_data.get("bid_amount"):
        min_budget = bid_card_requirements.get("budget_min", 0)
        max_budget = bid_card_requirements.get("budget_max", float('inf'))
        
        if bid_data["bid_amount"] < min_budget * 0.7:  # Allow 30% under minimum
            issues.append(f"Bid amount significantly below budget range (${min_budget:,.0f}-${max_budget:,.0f})")
        elif bid_data["bid_amount"] > max_budget * 1.5:  # Allow 50% over maximum
            issues.append(f"Bid amount significantly above budget range (${min_budget:,.0f}-${max_budget:,.0f})")
    
    # Validate timeline
    if bid_data.get("timeline_days"):
        urgency = bid_card_requirements.get("urgency_level", "standard")
        if urgency == "emergency" and bid_data["timeline_days"] > 7:
            issues.append("Timeline too long for emergency project (max 7 days)")
        elif urgency == "urgent" and bid_data["timeline_days"] > 14:
            issues.append("Timeline too long for urgent project (max 14 days)")
    
    # Check proposal length
    if bid_data.get("proposal") and len(bid_data["proposal"]) < 50:
        issues.append("Proposal description too brief (minimum 50 characters)")
    
    is_valid = len(issues) == 0
    return is_valid, issues


@tool
async def submit_contractor_bid(
    bid_data: dict,
    attachments: Optional[List[str]] = None,
    chat_session_id: Optional[str] = None
) -> dict:
    """
    Submit bid to database with all required tracking.
    
    Args:
        bid_data: Complete bid data to submit
        attachments: List of attachment URLs
        chat_session_id: BSA chat session ID for tracking
        
    Returns:
        Submission result with bid ID
    """
    
    try:
        from database_simple import db
    except ImportError:
        from database import SupabaseDB
        db = SupabaseDB()
    
    import uuid
    
    try:
        # Generate unique IDs
        bid_id = str(uuid.uuid4())
        proposal_id = str(uuid.uuid4())
        
        # Calculate timeline dates
        start_date = datetime.now() + timedelta(days=7)  # Default start in 1 week
        if bid_data.get("start_date"):
            # Parse custom start date if provided
            try:
                start_date = datetime.strptime(bid_data["start_date"], "%Y-%m-%d")
            except:
                pass
        
        end_date = start_date + timedelta(days=bid_data.get("timeline_days", 30))
        
        # Create bid record in contractor_bids table
        bid_record = {
            "id": bid_id,
            "bid_card_id": bid_data["bid_card_id"],
            "contractor_id": bid_data["contractor_id"],
            "bid_amount": bid_data["bid_amount"],
            "timeline_days": bid_data["timeline_days"],
            "timeline_start": start_date.isoformat(),
            "timeline_end": end_date.isoformat(),
            "proposal": bid_data.get("proposal", ""),
            "approach": bid_data.get("approach", ""),
            "materials_included": bid_data.get("materials_included", False),
            "warranty_details": bid_data.get("warranty_details"),
            "submission_method": "bsa_chat" if chat_session_id else "bsa_upload",
            "chat_session_id": chat_session_id,
            "extracted_from_upload": bool(attachments),
            "status": "submitted",
            "created_at": datetime.now().isoformat(),
        }
        
        result = db.client.table("contractor_bids").insert(bid_record).execute()
        
        if not result.data:
            return {"success": False, "error": "Failed to create bid record"}
        
        # Also create contractor_proposals record for compatibility
        proposal_record = {
            "id": proposal_id,
            "bid_card_id": bid_data["bid_card_id"],
            "contractor_id": bid_data["contractor_id"],
            "contractor_name": bid_data.get("contractor_name"),
            "bid_amount": bid_data["bid_amount"],
            "timeline_days": bid_data["timeline_days"],
            "proposal_text": bid_data.get("proposal", ""),
            "attachments": [{"url": url, "type": "quote"} for url in (attachments or [])],
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
        
        db.client.table("contractor_proposals").insert(proposal_record).execute()
        
        # Update bid card with new submission
        bid_card = db.client.table("bid_cards").select("*").eq(
            "id", bid_data["bid_card_id"]
        ).single().execute()
        
        if bid_card.data:
            bid_document = bid_card.data.get("bid_document", {})
            submitted_bids = bid_document.get("submitted_bids", [])
            
            submitted_bids.append({
                "bid_id": bid_id,
                "contractor_id": bid_data["contractor_id"],
                "contractor_name": bid_data.get("contractor_name"),
                "bid_amount": bid_data["bid_amount"],
                "timeline_days": bid_data["timeline_days"],
                "submitted_at": datetime.now().isoformat(),
                "submission_method": "bsa_chat" if chat_session_id else "bsa_upload"
            })
            
            bid_document["submitted_bids"] = submitted_bids
            bid_document["bids_received_count"] = len(submitted_bids)
            
            # Check if target met
            target = bid_card.data.get("contractor_count_needed", 4)
            if len(submitted_bids) >= target:
                bid_document["bids_target_met"] = True
                update_status = "bids_complete"
            else:
                update_status = bid_card.data.get("status")
            
            db.client.table("bid_cards").update({
                "bid_document": bid_document,
                "bid_count": len(submitted_bids),
                "status": update_status,
                "updated_at": datetime.now().isoformat()
            }).eq("id", bid_data["bid_card_id"]).execute()
        
        # Track in My Bids system
        try:
            from services.my_bids_tracker import my_bids_tracker
            await my_bids_tracker.track_bid_interaction(
                contractor_id=bid_data["contractor_id"],
                bid_card_id=bid_data["bid_card_id"],
                interaction_type='bsa_bid_submitted',
                details={
                    'bid_id': bid_id,
                    'proposal_id': proposal_id,
                    'bid_amount': bid_data["bid_amount"],
                    'submission_method': 'bsa_chat' if chat_session_id else 'bsa_upload',
                    'has_attachments': bool(attachments)
                }
            )
        except Exception as e:
            print(f"Failed to track in My Bids: {e}")
        
        return {
            "success": True,
            "bid_id": bid_id,
            "proposal_id": proposal_id,
            "message": "Bid submitted successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tool 
async def get_bid_card_requirements(bid_card_id: str) -> dict:
    """
    Get bid card requirements for validation and context.
    
    Args:
        bid_card_id: ID of the bid card
        
    Returns:
        Bid card requirements and context
    """
    
    try:
        from database_simple import db
    except ImportError:
        from database import SupabaseDB
        db = SupabaseDB()
    
    try:
        result = db.client.table("bid_cards").select("*").eq(
            "id", bid_card_id
        ).single().execute()
        
        if result.data:
            return {
                "bid_card_id": bid_card_id,
                "project_type": result.data.get("project_type"),
                "budget_min": result.data.get("budget_min", 0),
                "budget_max": result.data.get("budget_max", 999999),
                "urgency_level": result.data.get("urgency_level", "standard"),
                "timeline_flexibility": result.data.get("timeline_flexibility"),
                "materials_preference": result.data.get("materials_preference"),
                "special_requirements": result.data.get("special_requirements", []),
                "contractor_count_needed": result.data.get("contractor_count_needed", 4),
                "location": result.data.get("location"),
                "description": result.data.get("description", "")
            }
        else:
            return {"error": "Bid card not found"}
            
    except Exception as e:
        return {"error": str(e)}


@tool
async def format_bid_proposal(
    bid_data: dict,
    contractor_context: dict
) -> str:
    """
    Format a professional bid proposal from extracted data.
    
    Args:
        bid_data: Extracted or parsed bid data
        contractor_context: Contractor information
        
    Returns:
        Formatted proposal text
    """
    
    proposal_lines = []
    
    # Header
    company_name = contractor_context.get("company_name", "Contractor")
    proposal_lines.append(f"BID PROPOSAL FROM {company_name.upper()}")
    proposal_lines.append("=" * 50)
    proposal_lines.append("")
    
    # Project details
    if bid_data.get("project_type"):
        proposal_lines.append(f"Project Type: {bid_data['project_type']}")
    
    # Pricing
    proposal_lines.append("")
    proposal_lines.append("PRICING")
    proposal_lines.append("-" * 20)
    if bid_data.get("bid_amount"):
        proposal_lines.append(f"Total Bid Amount: ${bid_data['bid_amount']:,.2f}")
    if bid_data.get("materials_included"):
        proposal_lines.append("✓ All materials included")
    else:
        proposal_lines.append("Note: Materials to be purchased separately")
    
    # Timeline
    proposal_lines.append("")
    proposal_lines.append("TIMELINE")
    proposal_lines.append("-" * 20)
    if bid_data.get("timeline_days"):
        weeks = bid_data["timeline_days"] // 7
        days = bid_data["timeline_days"] % 7
        if weeks > 0:
            timeline_str = f"{weeks} week{'s' if weeks > 1 else ''}"
            if days > 0:
                timeline_str += f" and {days} day{'s' if days > 1 else ''}"
        else:
            timeline_str = f"{days} day{'s' if days > 1 else ''}"
        proposal_lines.append(f"Project Duration: {timeline_str}")
    
    if bid_data.get("start_date"):
        proposal_lines.append(f"Available to Start: {bid_data['start_date']}")
    
    # Approach
    if bid_data.get("approach") or bid_data.get("technical_approach"):
        proposal_lines.append("")
        proposal_lines.append("APPROACH")
        proposal_lines.append("-" * 20)
        approach_text = bid_data.get("approach") or bid_data.get("technical_approach")
        proposal_lines.append(approach_text)
    
    # Warranty
    if bid_data.get("warranty_details") or bid_data.get("warranty_terms"):
        proposal_lines.append("")
        proposal_lines.append("WARRANTY")
        proposal_lines.append("-" * 20)
        warranty_text = bid_data.get("warranty_details") or bid_data.get("warranty_terms")
        proposal_lines.append(warranty_text)
    
    # Payment terms
    if bid_data.get("payment_schedule"):
        proposal_lines.append("")
        proposal_lines.append("PAYMENT TERMS")
        proposal_lines.append("-" * 20)
        proposal_lines.append(bid_data["payment_schedule"])
    
    # Company info
    proposal_lines.append("")
    proposal_lines.append("ABOUT US")
    proposal_lines.append("-" * 20)
    if contractor_context.get("years_in_business"):
        proposal_lines.append(f"• {contractor_context['years_in_business']} years in business")
    if contractor_context.get("license_number"):
        proposal_lines.append(f"• Licensed & Insured (#{contractor_context['license_number']})")
    if contractor_context.get("specialties"):
        specialties = ", ".join(contractor_context["specialties"][:3])
        proposal_lines.append(f"• Specializing in: {specialties}")
    
    # Footer
    proposal_lines.append("")
    proposal_lines.append("=" * 50)
    proposal_lines.append("This proposal is valid for 30 days from submission date")
    
    return "\n".join(proposal_lines)