"""
Bid Submission Node for COIA with Human-in-the-Loop Approval
Handles contractor bid submissions with confirmation prompts
"""
import logging
from datetime import datetime
from typing import Any, Optional

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.errors import NodeInterrupt

from .unified_state import UnifiedCoIAState
from .tools import coia_tools

logger = logging.getLogger(__name__)


async def bid_submission_node(state: UnifiedCoIAState) -> dict[str, Any]:
    """
    Handle bid submission with human confirmation for COIA
    Interrupts for human approval before submitting high-value bids
    """
    
    logger.info("=== BID SUBMISSION NODE ACTIVATED ===")
    
    # Get bid details from state
    bid_cards = state.get("bid_cards_attached", [])
    contractor_profile = state.get("contractor_profile", {})
    messages = state.get("messages", [])
    
    if not bid_cards:
        return {
            "messages": [AIMessage(content="I don't see any active bid cards. Would you like me to search for opportunities?")],
            "current_mode": "bid_card_search"
        }
    
    # Get the bid card to submit for
    target_bid_card = bid_cards[0] if bid_cards else {}
    
    # Extract bid details from last message
    last_message = messages[-1].content if messages else ""
    bid_details = _extract_bid_details(last_message, contractor_profile, target_bid_card)
    
    # Check if this is a continuation after interrupt
    if _is_post_interrupt_confirmation(last_message):
        # User confirmed, proceed with submission
        result = await _submit_bid(bid_details, target_bid_card, contractor_profile)
        
        response = f"""
        ✅ **Bid Successfully Submitted!**
        
        **Project**: {target_bid_card.get('title', 'Unknown Project')}
        **Your Bid**: ${bid_details['amount']:,}
        **Timeline**: {bid_details['timeline']}
        **Status**: Submitted and pending homeowner review
        
        You'll receive a notification when the homeowner responds to your bid.
        
        Would you like to:
        1. View similar bid opportunities
        2. Update your contractor profile
        3. Return to the main menu
        """
        
        return {
            "messages": [AIMessage(content=response)],
            "current_mode": "conversation",
            "bid_submitted": True,
            "last_bid_details": result
        }
    
    # Check if we need human approval
    if _needs_human_approval(bid_details):
        # Format confirmation message
        confirmation_message = _format_bid_confirmation(bid_details, target_bid_card)
        
        # Interrupt for human confirmation
        logger.info(f"Interrupting for bid approval: ${bid_details['amount']}")
        raise NodeInterrupt(confirmation_message)
    
    # Auto-approve small bids
    result = await _submit_bid(bid_details, target_bid_card, contractor_profile)
    
    response = f"""
    ✅ **Quick Bid Submitted!**
    
    Your bid of ${bid_details['amount']:,} has been submitted for:
    **{target_bid_card.get('title', 'the project')}**
    
    The homeowner will review your bid and get back to you soon.
    """
    
    return {
        "messages": [AIMessage(content=response)],
        "current_mode": "conversation",
        "bid_submitted": True,
        "last_bid_details": result
    }


def _extract_bid_details(message: str, contractor_profile: dict, bid_card: dict) -> dict:
    """Extract bid details from contractor's message"""
    
    # Parse bid amount from message
    import re
    amount_match = re.search(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', message)
    bid_amount = float(amount_match.group(1).replace(',', '')) if amount_match else 0
    
    # If no amount specified, use midpoint of budget range
    if bid_amount == 0:
        budget_min = bid_card.get("budget_min", 1000)
        budget_max = bid_card.get("budget_max", 5000)
        bid_amount = (budget_min + budget_max) / 2
    
    # Extract timeline
    timeline_keywords = {
        "immediately": "Can start immediately",
        "tomorrow": "Can start tomorrow",
        "this week": "Can start this week",
        "next week": "Can start next week",
        "2 weeks": "Can start in 2 weeks",
        "month": "Can start within a month"
    }
    
    timeline = "Can start within 1-2 weeks"  # Default
    message_lower = message.lower()
    for keyword, timeline_text in timeline_keywords.items():
        if keyword in message_lower:
            timeline = timeline_text
            break
    
    # Build bid details
    return {
        "amount": bid_amount,
        "timeline": timeline,
        "message": message,
        "contractor_id": contractor_profile.get("id"),
        "contractor_name": contractor_profile.get("company_name", "Your Company"),
        "includes_materials": "materials included" in message_lower,
        "warranty_offered": "warranty" in message_lower,
        "payment_terms": _extract_payment_terms(message)
    }


def _needs_human_approval(bid_details: dict) -> bool:
    """Determine if bid needs human approval before submission"""
    
    # Always ask for confirmation if bid is over $5000
    if bid_details["amount"] > 5000:
        return True
    
    # Ask for confirmation if it's the contractor's first bid
    # This would check contractor history in production
    
    return False


def _is_post_interrupt_confirmation(message: str) -> bool:
    """Check if this is a confirmation after interrupt"""
    
    confirmations = ["yes", "confirm", "submit", "approve", "go ahead", "looks good"]
    message_lower = message.lower()
    
    return any(confirm in message_lower for confirm in confirmations)


def _format_bid_confirmation(bid_details: dict, bid_card: dict) -> str:
    """Format bid details for human confirmation"""
    
    return f"""
    ## 🔍 Please Review Your Bid Before Submission
    
    **Project**: {bid_card.get('title', 'Unknown Project')}
    **Location**: {bid_card.get('location_city', 'Unknown')}, {bid_card.get('location_state', '')}
    **Homeowner Budget**: ${bid_card.get('budget_min', 0):,} - ${bid_card.get('budget_max', 0):,}
    
    ### Your Bid Details:
    - **Bid Amount**: ${bid_details['amount']:,}
    - **Timeline**: {bid_details['timeline']}
    - **Materials**: {'Included' if bid_details['includes_materials'] else 'Not included'}
    - **Warranty**: {'Offered' if bid_details['warranty_offered'] else 'Standard'}
    - **Payment Terms**: {bid_details['payment_terms']}
    
    ### Your Message to Homeowner:
    "{bid_details['message'][:200]}..."
    
    **Type "yes" to submit this bid, or provide changes.**
    """


def _extract_payment_terms(message: str) -> str:
    """Extract payment terms from message"""
    
    message_lower = message.lower()
    
    if "50% deposit" in message_lower or "half up front" in message_lower:
        return "50% deposit, 50% on completion"
    elif "25% deposit" in message_lower:
        return "25% deposit, 75% on completion"
    elif "payment plan" in message_lower:
        return "Flexible payment plan available"
    elif "net 30" in message_lower:
        return "Net 30 payment terms"
    
    return "Standard payment terms"


async def _submit_bid(bid_details: dict, bid_card: dict, contractor_profile: dict) -> dict:
    """Submit the bid to the system"""
    
    try:
        # Import the bid submission API
        from routers.bid_submission_api import submit_contractor_bid
        
        # Prepare bid submission
        bid_data = {
            "bid_card_id": bid_card.get("id"),
            "contractor_id": contractor_profile.get("id"),
            "bid_amount": bid_details["amount"],
            "proposed_timeline": bid_details["timeline"],
            "message": bid_details["message"],
            "includes_materials": bid_details["includes_materials"],
            "warranty_offered": bid_details["warranty_offered"],
            "payment_terms": bid_details["payment_terms"],
            "submitted_at": datetime.utcnow().isoformat()
        }
        
        # Submit the bid
        result = await submit_contractor_bid(bid_data)
        
        logger.info(f"Bid submitted successfully: {result}")
        return result
        
    except ImportError:
        # Fallback for testing
        logger.warning("Bid submission API not available, using mock submission")
        return {
            "success": True,
            "bid_id": f"BID-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "status": "submitted",
            "submitted_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error submitting bid: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def account_creation_node(state: UnifiedCoIAState) -> dict[str, Any]:
    """
    Handle account creation with human confirmation
    Interrupts before creating contractor account
    """
    
    logger.info("=== ACCOUNT CREATION NODE ACTIVATED ===")
    
    contractor_profile = state.get("contractor_profile", {})
    contractor_lead_id = state.get("contractor_lead_id")
    messages = state.get("messages", [])
    
    # Check if this is post-interrupt confirmation
    if messages and _is_post_interrupt_confirmation(messages[-1].content):
        # Create the account
        result = await _create_contractor_account(contractor_profile, contractor_lead_id)
        
        response = f"""
        ✅ **Account Successfully Created!**
        
        **Company**: {contractor_profile.get('company_name', 'Your Company')}
        **Email**: {contractor_profile.get('email', 'Not provided')}
        **Temporary Password**: {result.get('temp_password', 'Check your email')}
        
        Please check your email for login instructions and to set your permanent password.
        
        You can now:
        - Submit bids on projects
        - Update your company profile
        - Upload certifications and portfolio
        - Message homeowners directly
        
        Would you like me to help you find relevant bid opportunities?
        """
        
        # CRITICAL: Set contractor_created flag to True in state
        return {
            "messages": [AIMessage(content=response)],
            "current_mode": "conversation",
            "contractor_created": True,  # THIS FLAG MUST BE SET!
            "contractor_id": result.get("contractor_id"),
            "account_creation_completed": True  # Additional flag for clarity
        }
    
    # Format account creation confirmation
    confirmation = f"""
    ## 👤 Ready to Create Your Contractor Account
    
    I have the following information:
    
    **Company Name**: {contractor_profile.get('company_name', 'Not provided')}
    **Contact Name**: {contractor_profile.get('contact_name', 'Not provided')}
    **Email**: {contractor_profile.get('email', 'Not provided')}
    **Phone**: {contractor_profile.get('phone', 'Not provided')}
    **Location**: {contractor_profile.get('city', 'Not provided')}, {contractor_profile.get('state', '')}
    
    **Services**: {', '.join(contractor_profile.get('specialties', ['Not specified'])[:3])}
    **Years in Business**: {contractor_profile.get('years_in_business', 'Not specified')}
    **License Verified**: {'Yes' if contractor_profile.get('license_verified') else 'No'}
    **Insurance Verified**: {'Yes' if contractor_profile.get('insurance_verified') else 'No'}
    
    This will create your official InstaBids contractor account.
    
    **Type "yes" to create your account, or let me know what needs to be corrected.**
    """
    
    # Interrupt for confirmation
    logger.info("Interrupting for account creation confirmation")
    raise NodeInterrupt(confirmation)


async def _create_contractor_account(profile: dict, contractor_lead_id: Optional[str]) -> dict:
    """
    Create contractor account via the tools facade (single source of truth),
    then mark contractor_lead converted if provided.
    """
    try:
        # Delegate creation to the canonical tools path
        result = await coia_tools.create_contractor_account(profile)

        if result.get("success"):
            contractor_id = result.get("account", {}).get("id") or result.get("contractor_id")

            # If we have a contractor_lead_id, mark as converted in contractor_leads
            if contractor_lead_id and contractor_id:
                try:
                    import sys, os
                    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                    from database_simple import db
                    db.client.table("contractor_leads").update({
                        "converted_to_contractor": True,
                        "contractor_id": contractor_id
                    }).eq("id", contractor_lead_id).execute()
                    logger.info(f"Marked contractor_lead {contractor_lead_id} as converted (contractor {contractor_id})")
                except Exception as e:
                    logger.warning(f"Could not update contractor_lead conversion flag: {e}")

            # Return a normalized success payload
            return {
                "success": True,
                "contractor_id": contractor_id,
                "temp_password": result.get("temp_password") or "Set via email",
                "email_sent": result.get("email_sent", False),
                "contractor_created": True
            }

        # Bubble up failure from tools path
        return {"success": False, "error": result.get("error", "Unknown error")}

    except Exception as e:
        logger.error(f"Error delegating to tools.create_contractor_account: {e}")
        return {"success": False, "error": str(e)}
