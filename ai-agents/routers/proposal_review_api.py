"""
Submitted Proposals Admin Review API
Integrates contractor bids with file review system for admin oversight
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import json

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from database_simple import db


router = APIRouter(tags=["proposal-review"])


class ProposalReviewDecision(BaseModel):
    decision: str  # "approved" or "rejected"
    admin_id: str
    notes: Optional[str] = None
    reason: Optional[str] = None


class ProposalReviewFilter(BaseModel):
    status: Optional[str] = None  # "pending", "approved", "rejected", "flagged"
    has_attachments: Optional[bool] = None
    has_contact_info: Optional[bool] = None
    project_type: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


async def analyze_proposal_for_contact_info(proposal_text: str, approach_text: str = None) -> Dict[str, Any]:
    """Analyze proposal text for contact information using GPT-4o"""
    try:
        # Import here to avoid circular imports
        from agents.intelligent_messaging_agent import IntelligentMessagingAgent
        
        # Initialize messaging agent
        messaging_agent = IntelligentMessagingAgent()
        
        # Combine proposal and approach text
        full_text = proposal_text
        if approach_text:
            full_text += f"\n\nApproach: {approach_text}"
        
        # Analyze text for contact info
        return await messaging_agent.analyzer.analyze_message_content(full_text)
        
    except Exception as e:
        print(f"Contact analysis error: {e}")
        # Conservative approach - flag for review if analysis fails
        return {
            "contact_info_detected": False,
            "confidence": 0.0,
            "explanation": f"Analysis failed: {str(e)}",
            "phones": [],
            "emails": [],
            "addresses": [],
            "social_handles": []
        }


def get_contact_flags(proposal: str, approach: str = None) -> Dict[str, Any]:
    """Quick contact detection for existing proposals"""
    import re
    
    text = (proposal + " " + (approach or "")).lower()
    
    # Simple regex patterns for contact info
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b|\b\(\d{3}\)\s?\d{3}[-.]?\d{4}\b'
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    phones = re.findall(phone_pattern, text)
    emails = re.findall(email_pattern, text, re.IGNORECASE)
    
    has_contact = len(phones) > 0 or len(emails) > 0 or "call" in text or "email" in text
    
    return {
        "contact_info_detected": has_contact,
        "confidence": 0.8 if has_contact else 0.1,
        "phones": phones,
        "emails": emails,
        "explanation": f"Found {len(phones)} phones, {len(emails)} emails" if has_contact else "No contact info detected"
    }


@router.get("/queue")
async def get_submitted_proposals(
    status: Optional[str] = Query(None, description="Filter by review status"),
    has_attachments: Optional[bool] = Query(None, description="Filter by attachment presence"),
    has_contact_info: Optional[bool] = Query(None, description="Filter by contact info presence"),
    project_type: Optional[str] = Query(None, description="Filter by project type"),
    limit: int = Query(50, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip")
):
    """Get all submitted proposals with comprehensive filtering"""
    try:
        supabase_client = db.client
        
        # Get contractor bids with basic filtering
        bids_query = supabase_client.table("contractor_bids").select("*")
        
        if status and status != "all" and status != "flagged":
            bids_query = bids_query.eq("status", status)
            
        bids_result = bids_query.order("submitted_at", desc=True).limit(limit).execute()
        raw_proposals = bids_result.data if bids_result.data else []
        
        # Now enhance each proposal with additional data
        enhanced_proposals = []
        for bid in raw_proposals:
            if not bid:
                continue
                
            # Get bid card info
            bid_card = {}
            if bid.get('bid_card_id'):
                bid_card_result = supabase_client.table("bid_cards").select("*").eq("id", bid['bid_card_id']).execute()
                if bid_card_result.data:
                    bid_card = bid_card_result.data[0]
            
            # Get contractor info
            contractor_name = "Unknown Contractor"
            contact_name = None
            if bid.get('contractor_id'):
                contractor_result = supabase_client.table("contractors").select("*").eq("id", bid['contractor_id']).execute()
                if contractor_result.data:
                    contractor = contractor_result.data[0]
                    contractor_name = contractor.get('company_name', 'Unknown Contractor')
                    contact_name = contractor.get('contact_name')
            
            # Get attachment count
            attachment_count = 0
            if bid.get('id'):
                attachments_result = supabase_client.table("contractor_proposal_attachments").select("id").eq("contractor_bid_id", bid['id']).execute()
                attachment_count = len(attachments_result.data) if attachments_result.data else 0
            
            # Create enhanced proposal object
            proposal = {
                "id": bid.get('id'),
                "bid_card_id": bid.get('bid_card_id'),
                "contractor_id": bid.get('contractor_id'),
                "amount": bid.get('amount', 0),
                "timeline_start": bid.get('timeline_start', ''),
                "timeline_end": bid.get('timeline_end', ''),
                "proposal": bid.get('proposal', ''),
                "approach": bid.get('approach', ''),
                "warranty_details": bid.get('warranty_details'),
                "bid_status": bid.get('status', 'submitted'),
                "submitted_at": bid.get('submitted_at', ''),
                "additional_data": bid.get('additional_data', {}),
                
                # Bid card information
                "bid_card_number": bid_card.get('bid_card_number', 'Unknown'),
                "project_type": bid_card.get('project_type', 'Unknown'),
                "urgency_level": bid_card.get('urgency_level', 'standard'),
                "project_status": bid_card.get('status', 'unknown'),
                "budget_min": bid_card.get('budget_min', 0),
                "budget_max": bid_card.get('budget_max', 0),
                "bid_document": bid_card.get('bid_document', {}),
                
                # Contractor information
                "contractor_name": contractor_name,
                "contact_name": contact_name,
                "attachment_count": attachment_count
            }
            
            enhanced_proposals.append(proposal)
        
        proposals = enhanced_proposals
        
        # Enhance each proposal with contact analysis
        enhanced_proposals = []
        for proposal in proposals:
            # Analyze for contact info
            contact_analysis = get_contact_flags(
                proposal.get('proposal', ''),
                proposal.get('approach', '')
            )
            
            # Determine review status
            review_status = "pending"
            if contact_analysis['contact_info_detected']:
                review_status = "flagged"
            elif proposal.get('bid_status') == 'approved':
                review_status = "approved"
            elif proposal.get('bid_status') == 'rejected':
                review_status = "rejected"
            
            enhanced_proposal = {
                **proposal,
                "contact_analysis": contact_analysis,
                "review_status": review_status,
                "flagged_reason": contact_analysis.get('explanation', ''),
                "requires_review": contact_analysis['contact_info_detected'],
                "attachment_count": proposal.get('attachment_count', 0)
            }
            
            # Apply contact info filter
            if has_contact_info is not None:
                if has_contact_info and not contact_analysis['contact_info_detected']:
                    continue
                if not has_contact_info and contact_analysis['contact_info_detected']:
                    continue
                    
            enhanced_proposals.append(enhanced_proposal)
        
        return enhanced_proposals
        
    except Exception as e:
        print(f"Error getting submitted proposals: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_proposal_review_stats():
    """Get statistics for proposal review dashboard"""
    try:
        supabase_client = db.client
        
        # Get all proposals
        proposals_result = supabase_client.table("contractor_bids").select("*").execute()
        proposals = proposals_result.data if proposals_result.data else []
        
        # Analyze each proposal for contact info
        total = len(proposals)
        flagged = 0
        approved = 0
        rejected = 0
        pending = 0
        
        for proposal in proposals:
            if not proposal:  # Skip None proposals
                continue
                
            contact_analysis = get_contact_flags(
                proposal.get('proposal', ''),
                proposal.get('approach', '')
            )
            
            status = proposal.get('status', 'submitted')
            
            if contact_analysis['contact_info_detected']:
                flagged += 1
            elif status == 'approved':
                approved += 1
            elif status == 'rejected':
                rejected += 1
            else:
                pending += 1
        
        # Get attachment stats
        attachments_result = supabase_client.table("contractor_proposal_attachments").select("id").execute()
        total_attachments = len(attachments_result.data) if attachments_result.data else 0
        
        # Calculate proposals with attachments
        with_attachments = 0
        for proposal in proposals:
            if not proposal:
                continue
            additional_data = proposal.get('additional_data') or {}
            if additional_data.get('has_attachments', False):
                with_attachments += 1
        
        return {
            "total": total,
            "pending": pending,
            "flagged": flagged,
            "approved": approved,
            "rejected": rejected,
            "total_attachments": total_attachments,
            "with_attachments": with_attachments
        }
        
    except Exception as e:
        print(f"Error getting proposal stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{proposal_id}")
async def get_proposal_details(proposal_id: str):
    """Get detailed information about a specific proposal"""
    try:
        supabase_client = db.client
        
        # Get proposal with full context
        proposal_result = supabase_client.table("contractor_bids").select("*").eq("id", proposal_id).execute()
        if not proposal_result.data:
            raise HTTPException(status_code=404, detail="Proposal not found")
            
        proposal = proposal_result.data[0]
        
        # Get bid card details
        bid_card_result = supabase_client.table("bid_cards").select("*").eq("id", proposal['bid_card_id']).execute()
        bid_card = bid_card_result.data[0] if bid_card_result.data else {}
        
        # Get contractor details
        contractor_result = supabase_client.table("contractors").select("*").eq("id", proposal['contractor_id']).execute()
        contractor = contractor_result.data[0] if contractor_result.data else {}
        
        # Get attachments
        attachments_result = supabase_client.table("contractor_proposal_attachments").select("*").eq("contractor_bid_id", proposal_id).execute()
        attachments = attachments_result.data if attachments_result.data else []
        
        # Analyze for contact info
        contact_analysis = get_contact_flags(
            proposal.get('proposal', ''),
            proposal.get('approach', '')
        )
        
        return {
            "proposal": proposal,
            "bid_card": bid_card,
            "contractor": contractor,
            "attachments": attachments,
            "contact_analysis": contact_analysis,
            "requires_review": contact_analysis['contact_info_detected']
        }
        
    except Exception as e:
        print(f"Error getting proposal details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{proposal_id}/attachments")
async def get_proposal_attachments(proposal_id: str):
    """Get all attachments for a specific proposal"""
    try:
        supabase_client = db.client
        
        attachments_result = supabase_client.table("contractor_proposal_attachments").select("*").eq("contractor_bid_id", proposal_id).execute()
        attachments = attachments_result.data if attachments_result.data else []
        
        return attachments
        
    except Exception as e:
        print(f"Error getting proposal attachments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{proposal_id}/decision")
async def make_proposal_decision(proposal_id: str, decision: ProposalReviewDecision):
    """Approve or reject a submitted proposal"""
    try:
        supabase_client = db.client
        
        # Validate proposal exists
        proposal_result = supabase_client.table("contractor_bids").select("*").eq("id", proposal_id).execute()
        if not proposal_result.data:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        # Update proposal status
        update_data = {
            "status": decision.decision,
            "updated_at": datetime.now().isoformat(),
            "additional_data": {
                **proposal_result.data[0].get("additional_data", {}),
                "admin_review": {
                    "reviewed_by": decision.admin_id,
                    "reviewed_at": datetime.now().isoformat(),
                    "decision": decision.decision,
                    "notes": decision.notes,
                    "reason": decision.reason
                }
            }
        }
        
        update_result = supabase_client.table("contractor_bids").update(update_data).eq("id", proposal_id).execute()
        
        # If rejecting, optionally add to review queue for future reference
        if decision.decision == "rejected" and decision.reason:
            queue_data = {
                "bid_card_id": proposal_result.data[0]["bid_card_id"],
                "contractor_id": proposal_result.data[0]["contractor_id"],
                "file_name": f"proposal_{proposal_id}.txt",
                "file_path": f"proposals/{proposal_id}",
                "file_type": "text/plain",
                "contact_analysis": {
                    "flagged_reason": decision.reason,
                    "admin_decision": decision.decision
                },
                "flagged_reason": decision.reason,
                "review_status": "rejected",
                "reviewed_by": decision.admin_id,
                "reviewed_at": datetime.now().isoformat(),
                "admin_decision_reason": decision.reason
            }
            
            supabase_client.table("file_review_queue").insert(queue_data).execute()
        
        return {
            "success": True,
            "proposal_id": proposal_id,
            "decision": decision.decision,
            "updated_proposal": update_result.data[0] if update_result.data else None
        }
        
    except Exception as e:
        print(f"Error making proposal decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{proposal_id}/download")
async def get_proposal_download_url(proposal_id: str, attachment_id: Optional[str] = None):
    """Get download URL for proposal attachment"""
    try:
        supabase_client = db.client
        
        if attachment_id:
            # Get specific attachment
            attachment_result = supabase_client.table("contractor_proposal_attachments").select("*").eq("id", attachment_id).execute()
            if not attachment_result.data:
                raise HTTPException(status_code=404, detail="Attachment not found")
                
            attachment = attachment_result.data[0]
            
            # Generate signed URL for download
            # Note: This would typically use Supabase storage signed URL generation
            download_url = attachment["url"]  # Placeholder - implement actual signed URL
            
            return {
                "download_url": download_url,
                "filename": attachment["name"],
                "mime_type": attachment.get("mime_type"),
                "expires_in": 3600
            }
        else:
            # Generate download for entire proposal as PDF/document
            proposal_result = supabase_client.table("contractor_bids").select("*").eq("id", proposal_id).execute()
            if not proposal_result.data:
                raise HTTPException(status_code=404, detail="Proposal not found")
                
            # This would generate a PDF of the proposal
            return {
                "download_url": f"/api/proposal-review/{proposal_id}/export",
                "filename": f"proposal_{proposal_id}.pdf",
                "mime_type": "application/pdf",
                "expires_in": 3600
            }
            
    except Exception as e:
        print(f"Error getting download URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{proposal_id}/attachments/{attachment_id}/view")
async def get_attachment_for_viewing(proposal_id: str, attachment_id: str):
    """Get attachment content for inline viewing"""
    try:
        supabase_client = db.client
        
        # Get attachment details
        attachment_result = supabase_client.table("contractor_proposal_attachments").select("*").eq("id", attachment_id).execute()
        if not attachment_result.data:
            raise HTTPException(status_code=404, detail="Attachment not found")
            
        attachment = attachment_result.data[0]
        
        # Verify it belongs to the proposal
        if attachment.get("contractor_bid_id") != proposal_id:
            raise HTTPException(status_code=403, detail="Attachment does not belong to this proposal")
        
        # For now, return the URL directly - in production, you might want to:
        # 1. Stream the file content directly
        # 2. Generate temporary signed URLs
        # 3. Add security checks and access controls
        
        return {
            "url": attachment["url"],
            "filename": attachment["name"], 
            "mime_type": attachment.get("mime_type"),
            "size": attachment.get("size", 0)
        }
        
    except Exception as e:
        print(f"Error getting attachment for viewing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{proposal_id}")
async def delete_proposal(proposal_id: str, admin_id: str):
    """Delete a proposal (admin only)"""
    try:
        supabase_client = db.client
        
        # First delete attachments
        supabase_client.table("contractor_proposal_attachments").delete().eq("contractor_bid_id", proposal_id).execute()
        
        # Then delete proposal
        delete_result = supabase_client.table("contractor_bids").delete().eq("id", proposal_id).execute()
        
        return {
            "success": True,
            "deleted_proposal_id": proposal_id,
            "deleted_by": admin_id
        }
        
    except Exception as e:
        print(f"Error deleting proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))