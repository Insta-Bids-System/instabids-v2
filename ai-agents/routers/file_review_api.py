"""
File Review API - Admin Panel Integration
Handles flagged files that contain potential contact information
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from database_simple import db


async def send_admin_decision_notification(review_data: dict, decision: str, reason: str):
    """Send notification to contractor about admin decision on their file"""
    try:
        from services.file_flagged_notification_service import FileFlaggedNotificationService
        
        service = FileFlaggedNotificationService()
        contractor_id = review_data.get("contractor_id")
        bid_card_id = review_data.get("bid_card_id")
        file_name = review_data.get("file_name")
        
        if not all([contractor_id, bid_card_id, file_name]):
            print(f"[WARNING] Missing data for admin decision notification: {review_data}")
            return
        
        # Get contractor info
        contractor = service._get_contractor_info(contractor_id)
        bid_card = service._get_bid_card_info(bid_card_id)
        
        if decision == "approved":
            notification_data = {
                "user_id": contractor_id,
                "contractor_id": contractor_id,
                "bid_card_id": bid_card_id,
                "notification_type": "file_approved",
                "title": "✅ File Approved",
                "message": f"Great news! Your file '{file_name}' has been approved and added to your bid for {bid_card.get('project_type', 'the project')}.",
                "action_url": f"/contractor/projects/{bid_card_id}",
                "is_read": False,
                "channels": {"in_app": True, "email": False}
            }
        else:  # rejected
            notification_data = {
                "user_id": contractor_id,
                "contractor_id": contractor_id,
                "bid_card_id": bid_card_id,
                "notification_type": "file_rejected",
                "title": "❌ File Rejected",
                "message": f"Your file '{file_name}' was rejected. Reason: {reason or 'Contains prohibited content'}. You can upload a corrected version.",
                "action_url": f"/contractor/projects/{bid_card_id}",
                "is_read": False,
                "channels": {"in_app": True, "email": True}
            }
        
        # Save notification
        db.table("notifications").insert(notification_data).execute()
        print(f"[NOTIFICATION] Admin decision notification sent: {decision} for {file_name}")
        
    except Exception as e:
        print(f"[ERROR] Failed to send admin decision notification: {e}")
        raise


router = APIRouter(prefix="/api/file-review", tags=["file-review"])


# Pydantic models
class FileReviewItem(BaseModel):
    id: str
    bid_card_id: str
    contractor_id: str
    file_name: str
    file_path: str
    file_type: str
    file_size: int
    flagged_reason: str
    confidence_score: float
    detected_contact_types: List[str]
    review_status: str
    created_at: str
    
    # Optional fields for reviewed items
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    review_notes: Optional[str] = None
    admin_decision_reason: Optional[str] = None


class ReviewDecision(BaseModel):
    decision: str  # 'approved' or 'rejected'
    admin_id: str
    notes: Optional[str] = None
    reason: Optional[str] = None


@router.get("/queue", response_model=List[FileReviewItem])
async def get_file_review_queue(
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
    limit: int = Query(50, description="Number of items to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """Get files in review queue for admin panel"""
    try:
        query = db.client.table("file_review_queue").select("*")
        
        if status:
            query = query.eq("review_status", status)
            
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        
        response = query.execute()
        
        return [FileReviewItem(**item) for item in response.data]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch review queue: {str(e)}")


@router.get("/stats")
async def get_review_queue_stats():
    """Get statistics for file review queue"""
    try:
        # Get counts by status
        pending_response = db.client.table("file_review_queue").select("id", count="exact").eq("review_status", "pending").execute()
        approved_response = db.client.table("file_review_queue").select("id", count="exact").eq("review_status", "approved").execute()
        rejected_response = db.client.table("file_review_queue").select("id", count="exact").eq("review_status", "rejected").execute()
        
        return {
            "pending": pending_response.count,
            "approved": approved_response.count,
            "rejected": rejected_response.count,
            "total": pending_response.count + approved_response.count + rejected_response.count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")


@router.get("/{review_id}")
async def get_file_review_details(review_id: str):
    """Get detailed information about a specific file review item"""
    try:
        # Get review item with bid card and contractor details
        response = db.client.table("file_review_queue").select("""
            *,
            bid_cards(bid_card_number, project_type, status),
            contractors(company_name, contact_name)
        """).eq("id", review_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Review item not found")
            
        return response.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch review details: {str(e)}")


@router.post("/{review_id}/decision")
async def make_review_decision(review_id: str, decision: ReviewDecision):
    """Admin makes decision on flagged file (approve/reject)"""
    try:
        if decision.decision not in ["approved", "rejected"]:
            raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'rejected'")
            
        # Update review record
        update_data = {
            "review_status": decision.decision,
            "reviewed_by": decision.admin_id,
            "reviewed_at": datetime.now().isoformat(),
            "review_notes": decision.notes,
            "admin_decision_reason": decision.reason
        }
        
        response = db.client.table("file_review_queue").update(update_data).eq("id", review_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Review item not found")
            
        # If approved, move file to main storage and create attachment record
        if decision.decision == "approved":
            await process_approved_file(review_id, response.data[0])
            
        # 🚨 NEW: Send notification to contractor about admin decision
        try:
            await send_admin_decision_notification(response.data[0], decision.decision, decision.reason)
        except Exception as e:
            print(f"[WARNING] Failed to send admin decision notification: {e}")
            
        return {
            "success": True,
            "message": f"File {decision.decision} successfully",
            "review_id": review_id,
            "decision": decision.decision
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process decision: {str(e)}")


async def process_approved_file(review_id: str, review_data: dict):
    """Process an approved file - move from quarantine to main storage"""
    try:
        # Get the quarantine file path
        quarantine_path = review_data["file_path"]
        
        # Generate new path in main storage
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        approved_path = f"bid_attachments/{review_data['bid_card_id']}/{timestamp}_{review_data['file_name']}"
        
        # Move file from quarantine to main storage
        # Note: Supabase doesn't have native move operation, so we copy and delete
        supabase_client = db.client
        
        # Download from quarantine
        file_response = supabase_client.storage.from_("project-images").download(quarantine_path)
        
        # Upload to main storage
        supabase_client.storage.from_("project-images").upload(
            approved_path,
            file_response,
            {
                "content-type": review_data["file_type"],
                "cache-control": "3600",
                "upsert": "false"
            }
        )
        
        # Get public URL
        file_url = supabase_client.storage.from_("project-images").get_public_url(approved_path)
        
        # Create attachment record in main table
        attachment_data = {
            "contractor_bid_id": review_data["original_upload_data"]["bid_id"],
            "name": review_data["file_name"],
            "type": review_data["file_type"].split("/")[0] if review_data["file_type"] else "document",
            "url": file_url,
            "size": review_data["file_size"],
            "mime_type": review_data["file_type"]
        }
        
        supabase_client.table("contractor_proposal_attachments").insert(attachment_data).execute()
        
        # Delete from quarantine
        supabase_client.storage.from_("project-images").remove([quarantine_path])
        
        print(f"[APPROVED FILE] Moved {review_data['file_name']} from quarantine to main storage")
        
    except Exception as e:
        print(f"Error processing approved file: {e}")
        # Don't fail the decision process if file moving fails
        pass


@router.get("/download/{review_id}")
async def download_file_for_review(review_id: str):
    """Get download URL for file under review"""
    try:
        # Get review item
        response = db.client.table("file_review_queue").select("file_path").eq("id", review_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Review item not found")
            
        file_path = response.data[0]["file_path"]
        
        # Generate signed URL for download (valid for 1 hour)
        signed_url = db.client.storage.from_("project-images").create_signed_url(file_path, 3600)
        
        return {
            "download_url": signed_url["signedURL"],
            "expires_in": 3600
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")


@router.delete("/{review_id}")
async def delete_review_item(review_id: str, admin_id: str):
    """Delete a review item and its associated file (admin only)"""
    try:
        # Get review item first
        response = db.client.table("file_review_queue").select("*").eq("id", review_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Review item not found")
            
        review_data = response.data[0]
        
        # Delete file from storage
        db.client.storage.from_("project-images").remove([review_data["file_path"]])
        
        # Delete record from database
        db.client.table("file_review_queue").delete().eq("id", review_id).execute()
        
        print(f"[DELETED] Admin {admin_id} deleted review item {review_id}: {review_data['file_name']}")
        
        return {
            "success": True,
            "message": "Review item and file deleted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete review item: {str(e)}")