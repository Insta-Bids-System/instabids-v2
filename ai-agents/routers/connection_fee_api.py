"""
Connection Fee Payment API
Handles connection fee payment processing and status updates
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime
from database_simple import db

router = APIRouter()


# For now, create a simple auth dependency that returns a test user
# This should be replaced with the actual auth system
def get_current_user():
    return {
        "id": "test-user-id",
        "email": "test@instabids.com",
        "role": "contractor"
    }


@router.post("/api/connection-fees/{fee_id}/pay")
async def process_connection_fee_payment(
    fee_id: str,
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Process connection fee payment for a contractor
    
    Args:
        fee_id: ID of the connection fee to pay
        request: Payment details including contractor_id and payment_method
        current_user: Authenticated user (contractor)
        
    Returns:
        Payment processing result
    """
    try:
        contractor_id = request.get("contractor_id")
        payment_method = request.get("payment_method", "card")
        
        if not contractor_id:
            raise HTTPException(status_code=400, detail="contractor_id is required")
        
        # 1. Verify connection fee exists and belongs to contractor
        fee_result = db.table("connection_fees").select("*").eq("id", fee_id).single().execute()
        if not fee_result.data:
            raise HTTPException(status_code=404, detail="Connection fee not found")
            
        connection_fee = fee_result.data
        
        # Verify contractor matches
        if connection_fee.get("contractor_id") != contractor_id:
            raise HTTPException(status_code=403, detail="Not authorized to pay this connection fee")
        
        # Check if already paid
        if connection_fee.get("fee_status") == "paid":
            raise HTTPException(status_code=400, detail="Connection fee already paid")
        
        # 2. Get bid card information for context
        bid_card_result = db.table("bid_cards").select("*").eq("id", connection_fee.get("bid_card_id")).single().execute()
        if not bid_card_result.data:
            raise HTTPException(status_code=404, detail="Associated bid card not found")
            
        bid_card = bid_card_result.data
        
        # 3. Process payment (In production, this would integrate with Stripe)
        # For now, we'll simulate successful payment processing
        payment_result = await simulate_payment_processing(
            amount=connection_fee.get("final_fee_amount", 0),
            contractor_id=contractor_id,
            payment_method=payment_method
        )
        
        if not payment_result["success"]:
            raise HTTPException(status_code=400, detail=f"Payment failed: {payment_result['error']}")
        
        # 4. Update connection fee status
        fee_update_data = {
            "fee_status": "paid",
            "payment_processed_at": datetime.utcnow().isoformat(),
            "payment_method": payment_method,
            "payment_transaction_id": payment_result["transaction_id"],
            "payment_details": {
                "processed_at": datetime.utcnow().isoformat(),
                "method": payment_method,
                "amount": connection_fee.get("final_fee_amount"),
                "currency": "USD"
            }
        }
        
        update_result = db.table("connection_fees").update(fee_update_data).eq("id", fee_id).execute()
        if not update_result.data:
            raise HTTPException(status_code=500, detail="Failed to update connection fee status")
        
        # 5. Update bid card status to active (contractor can now proceed)
        bid_card_update = {
            "status": "active",
            "contractor_started_at": datetime.utcnow().isoformat()
        }
        
        db.table("bid_cards").update(bid_card_update).eq("id", connection_fee.get("bid_card_id")).execute()
        
        # 6. Create notification for homeowner (project is now active)
        homeowner_notification = {
            "user_id": bid_card.get("user_id"),
            "bid_card_id": connection_fee.get("bid_card_id"),
            "contractor_id": contractor_id,
            "notification_type": "project_activated",
            "title": "Project Activated - Contractor Payment Confirmed",
            "message": f"Great news! Your contractor has confirmed the project and paid the connection fee. Your {bid_card.get('project_type', 'project').replace('_', ' ')} project is now active.",
            "action_url": f"/homeowner/projects/{connection_fee.get('bid_card_id')}",
            "is_read": False,
            "channels": {"email": True, "in_app": True},
            "created_at": datetime.utcnow().isoformat()
        }
        
        db.table("notifications").insert(homeowner_notification).execute()
        
        # 7. Process referral payout if applicable
        if connection_fee.get("referrer_portion", 0) > 0:
            await process_referral_payout(connection_fee)
        
        return {
            "success": True,
            "transaction_id": payment_result["transaction_id"],
            "amount_paid": connection_fee.get("final_fee_amount"),
            "contractor_receives": connection_fee.get("winning_bid_amount", 0) - connection_fee.get("final_fee_amount", 0),
            "project_status": "active",
            "message": f"Payment successful! Connection fee of ${connection_fee.get('final_fee_amount')} has been processed.",
            "next_steps": [
                "Contact the homeowner to schedule the work",
                "Review project details and requirements", 
                "Begin work according to your timeline"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment processing failed: {str(e)}")


@router.get("/api/connection-fees/contractor/{contractor_id}")
async def get_contractor_connection_fees(
    contractor_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all connection fees for a contractor
    """
    try:
        # Verify user is the contractor or admin
        if current_user["id"] != contractor_id and current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to view these connection fees")
        
        # Get connection fees with bid card details
        fees_result = db.table("connection_fees").select("""
            id, bid_card_id, contractor_id, winning_bid_amount, final_fee_amount, 
            fee_status, payment_processed_at, payment_method, created_at
        """).eq("contractor_id", contractor_id).order("created_at", desc=True).execute()
        
        connection_fees = fees_result.data or []
        
        # Enrich with bid card details
        enriched_fees = []
        for fee in connection_fees:
            bid_card = db.table("bid_cards").select("""
                bid_card_number, project_type, status, user_id
            """).eq("id", fee["bid_card_id"]).single().execute()
            
            if bid_card.data:
                fee["bid_card_details"] = bid_card.data
                enriched_fees.append(fee)
        
        return {
            "success": True,
            "connection_fees": enriched_fees,
            "total_fees": len(enriched_fees),
            "total_amount": sum(fee.get("final_fee_amount", 0) for fee in enriched_fees),
            "paid_amount": sum(fee.get("final_fee_amount", 0) for fee in enriched_fees if fee.get("fee_status") == "paid"),
            "pending_amount": sum(fee.get("final_fee_amount", 0) for fee in enriched_fees if fee.get("fee_status") != "paid")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def simulate_payment_processing(
    amount: float,
    contractor_id: str,
    payment_method: str = "card"
) -> Dict[str, Any]:
    """
    Simulate payment processing
    In production, this would integrate with Stripe, Square, or similar payment processor
    """
    import uuid
    import asyncio
    
    # Simulate processing delay (non-blocking)
    await asyncio.sleep(0.5)
    
    # Simulate success (98% success rate)
    import random
    if random.random() < 0.98:
        return {
            "success": True,
            "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
            "amount": amount,
            "currency": "USD",
            "method": payment_method,
            "processor": "InstaBids_Payment_Simulator"
        }
    else:
        return {
            "success": False,
            "error": "Payment declined by processor",
            "error_code": "CARD_DECLINED"
        }


async def process_referral_payout(connection_fee: Dict[str, Any]) -> None:
    """
    Process referral payout when connection fee is paid
    """
    try:
        referral_amount = connection_fee.get("referrer_portion", 0)
        if referral_amount <= 0:
            return
            
        # Update referral tracking status
        db.table("referral_tracking").update({
            "payout_status": "processed",
            "payout_processed_at": datetime.utcnow().isoformat(),
            "payout_amount": referral_amount
        }).eq("connection_fee_id", connection_fee["id"]).execute()
        
        print(f"[ReferralPayout] Processed ${referral_amount} payout for connection fee {connection_fee['id']}")
        
    except Exception as e:
        print(f"[ReferralPayout] Failed to process payout: {str(e)}")
        # Don't raise exception - referral payout failure shouldn't block main payment