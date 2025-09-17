#!/usr/bin/env python3
"""
Admin Connection Fee Management Routes
Provides complete visibility into connection fee system for admin dashboard
"""

from datetime import datetime, timedelta
from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from database_simple import db

router = APIRouter(prefix="/api/admin", tags=["admin-connection-fees"])


class ConnectionFeeOverview(BaseModel):
    """Connection fee overview for admin dashboard"""
    fee_id: str
    bid_card_id: str
    bid_card_number: str
    contractor_id: str
    contractor_name: Optional[str]
    contractor_company: Optional[str]
    contractor_phone: Optional[str]
    contractor_email: Optional[str]
    contractor_license: Optional[str]
    contractor_rating: Optional[float]
    contractor_total_jobs: Optional[int]
    contractor_years_experience: Optional[int]
    contractor_specialties: Optional[List[str]]
    winning_bid_amount: float
    base_fee_amount: float
    final_fee_amount: float
    project_category: Optional[str]
    calculation_method: Optional[str]
    fee_status: str
    payment_processed_at: Optional[str]
    created_at: str
    days_since_selection: int
    project_title: str
    homeowner_name: Optional[str]


class ConnectionFeeStats(BaseModel):
    """Connection fee statistics"""
    total_fees_calculated: int
    total_fees_paid: int
    total_fees_pending: int
    total_revenue: float
    pending_revenue: float
    average_fee_amount: float
    payment_completion_rate: float
    overdue_payments: int


@router.get("/connection-fees", response_model=List[ConnectionFeeOverview])
async def get_all_connection_fees(
    status: Optional[str] = Query(None, description="Filter by fee status: calculated, paid, overdue"),
    limit: int = Query(50, description="Number of records to return")
):
    """Get all connection fees with bid card and contractor details"""
    try:
        # Build base query - simplified without joins first
        query = db.client.table("connection_fees").select(
            "id, bid_card_id, contractor_id, winning_bid_amount, base_fee_amount, final_fee_amount, fee_status, calculated_at, created_at"
        ).limit(limit)
        
        # Apply status filter if provided
        if status:
            if status == "overdue":
                # Consider fees overdue if pending for more than 7 days
                overdue_date = (datetime.now() - timedelta(days=7)).isoformat()
                query = query.eq("fee_status", "calculated").lt("created_at", overdue_date)
            else:
                query = query.eq("fee_status", status)
        
        result = query.order("created_at", desc=True).execute()
        
        # Transform data for admin view
        connection_fees = []
        for fee in result.data or []:
            # Calculate days since selection
            created_at = datetime.fromisoformat(fee["created_at"].replace("Z", "+00:00"))
            days_since = (datetime.now() - created_at).days
            
            # Get bid card details separately
            bid_card_result = db.client.table("bid_cards").select("bid_card_number, title, homeowner_name").eq("id", fee["bid_card_id"]).execute()
            bid_card = bid_card_result.data[0] if bid_card_result.data else {}
            
            # Get contractor details separately with full info
            contractor_result = db.client.table("contractors").select("company_name, contact_name, phone, email, license_number, rating, total_jobs, years_in_business, specialties").eq("id", fee["contractor_id"]).execute()
            contractor = contractor_result.data[0] if contractor_result.data else {}
            
            connection_fees.append(ConnectionFeeOverview(
                fee_id=fee["id"],
                bid_card_id=fee["bid_card_id"],
                bid_card_number=bid_card.get("bid_card_number", "Unknown"),
                contractor_id=fee["contractor_id"],
                contractor_name=contractor.get("contact_name"),
                contractor_company=contractor.get("company_name", "Unknown Company"),
                contractor_phone=contractor.get("phone"),
                contractor_email=contractor.get("email"),
                contractor_license=contractor.get("license_number"),
                contractor_rating=contractor.get("rating"),
                contractor_total_jobs=contractor.get("total_jobs"),
                contractor_years_experience=contractor.get("years_in_business"),
                contractor_specialties=contractor.get("specialties", []),
                winning_bid_amount=fee["winning_bid_amount"],
                base_fee_amount=fee.get("base_fee_amount", fee["final_fee_amount"]),
                final_fee_amount=fee["final_fee_amount"],
                project_category=fee.get("project_category"),
                calculation_method=fee.get("calculation_method"),
                fee_status=fee["fee_status"],
                payment_processed_at=fee.get("calculated_at"),
                created_at=fee["created_at"],
                days_since_selection=days_since,
                project_title=bid_card.get("title") or "Untitled Project",
                homeowner_name=bid_card.get("homeowner_name")
            ))
        
        return connection_fees
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving connection fees: {str(e)}")


@router.get("/connection-fees/stats", response_model=ConnectionFeeStats)
async def get_connection_fee_stats():
    """Get connection fee statistics for admin dashboard"""
    try:
        # Get all connection fees
        all_fees_result = db.client.table("connection_fees").select("*").execute()
        all_fees = all_fees_result.data or []
        
        # Calculate statistics
        total_calculated = len(all_fees)
        paid_fees = [f for f in all_fees if f["fee_status"] == "paid"]
        pending_fees = [f for f in all_fees if f["fee_status"] == "calculated"]
        
        total_paid = len(paid_fees)
        total_pending = len(pending_fees)
        
        # Revenue calculations
        total_revenue = sum(fee["final_fee_amount"] for fee in paid_fees)
        pending_revenue = sum(fee["final_fee_amount"] for fee in pending_fees)
        
        # Average fee calculation
        avg_fee = sum(fee["final_fee_amount"] for fee in all_fees) / total_calculated if total_calculated > 0 else 0
        
        # Payment completion rate
        completion_rate = (total_paid / total_calculated * 100) if total_calculated > 0 else 0
        
        # Overdue payments (pending for more than 7 days)
        overdue_date = datetime.now() - timedelta(days=7)
        overdue_count = 0
        for fee in pending_fees:
            created_at = datetime.fromisoformat(fee["created_at"].replace("Z", "+00:00"))
            if created_at < overdue_date:
                overdue_count += 1
        
        return ConnectionFeeStats(
            total_fees_calculated=total_calculated,
            total_fees_paid=total_paid,
            total_fees_pending=total_pending,
            total_revenue=round(total_revenue, 2),
            pending_revenue=round(pending_revenue, 2),
            average_fee_amount=round(avg_fee, 2),
            payment_completion_rate=round(completion_rate, 1),
            overdue_payments=overdue_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating connection fee stats: {str(e)}")


@router.get("/connection-fees/overdue")
async def get_overdue_connection_fees():
    """Get connection fees that are overdue for payment (pending > 7 days)"""
    try:
        # Calculate overdue threshold (7 days ago)
        overdue_date = (datetime.now() - timedelta(days=7)).isoformat()
        
        # Simplified query without complex joins
        result = db.client.table("connection_fees").select(
            "id, bid_card_id, contractor_id, final_fee_amount, created_at"
        ).eq("fee_status", "calculated").lt("created_at", overdue_date).execute()
        
        overdue_fees = []
        for fee in result.data or []:
            created_at = datetime.fromisoformat(fee["created_at"].replace("Z", "+00:00"))
            days_overdue = (datetime.now() - created_at).days - 7  # Days beyond the 7-day grace period
            
            # Get bid card details separately
            bid_card_result = db.client.table("bid_cards").select("bid_card_number, title").eq("id", fee["bid_card_id"]).execute()
            bid_card = bid_card_result.data[0] if bid_card_result.data else {}
            
            # Get contractor details separately
            contractor_result = db.client.table("contractors").select("company_name").eq("id", fee["contractor_id"]).execute()
            contractor = contractor_result.data[0] if contractor_result.data else {}
            
            overdue_fees.append({
                "fee_id": fee["id"],
                "bid_card_number": bid_card.get("bid_card_number", "Unknown"),
                "project_title": bid_card.get("title", "Unknown Project"),
                "contractor_company": contractor.get("company_name", "Unknown Company"),
                "fee_amount": fee["final_fee_amount"],
                "days_overdue": days_overdue,
                "created_at": fee["created_at"]
            })
        
        return {"overdue_fees": overdue_fees, "count": len(overdue_fees)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving overdue fees: {str(e)}")


@router.post("/connection-fees/{fee_id}/remind")
async def send_payment_reminder(fee_id: str):
    """Send payment reminder to contractor (placeholder for notification system)"""
    try:
        # Get connection fee details
        fee_result = db.client.table("connection_fees").select("*").eq("id", fee_id).execute()
        if not fee_result.data:
            raise HTTPException(status_code=404, detail="Connection fee not found")
        
        fee = fee_result.data[0]
        
        # For now, just log the reminder action
        # In production, this would integrate with the contractor notification service
        print(f"Payment reminder sent for connection fee {fee_id}")
        print(f"Contractor: {fee['contractor_id']}")
        print(f"Amount: ${fee['final_fee_amount']}")
        
        # Could create a notification record here
        notification_data = {
            "contractor_id": fee["contractor_id"],
            "notification_type": "payment_reminder",
            "message": f"Payment reminder for connection fee ${fee['final_fee_amount']}",
            "related_id": fee_id,
            "status": "sent",
            "created_at": datetime.now().isoformat()
        }
        
        # Insert notification (if notifications table exists)
        try:
            db.client.table("notifications").insert(notification_data).execute()
        except Exception:
            print("Notifications table not available, reminder logged only")
        
        return {
            "success": True,
            "message": f"Payment reminder sent for fee ${fee['final_fee_amount']}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending reminder: {str(e)}")