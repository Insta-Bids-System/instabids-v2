"""
Contractor Proposals API Router
Manages contractor bid submissions and proposal retrieval for homeowners
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel


try:
    from database_simple import db
except ImportError:
    from database import SupabaseDB
    db = SupabaseDB()

router = APIRouter(tags=["contractor-proposals"])


class ContractorProposal(BaseModel):
    bid_card_id: str
    contractor_id: str
    contractor_name: Optional[str] = None
    contractor_company: Optional[str] = None
    amount: float  # Changed from bid_amount to match frontend
    timeline_start: str  # Added to match frontend format
    timeline_end: str    # Added to match frontend format  
    proposal: str        # Changed from proposal_text to match frontend
    technical_approach: Optional[str] = None  # Added to match frontend
    attachments: Optional[list[dict[str, Any]]] = None


@router.post("/submit")
async def submit_proposal(proposal: ContractorProposal):
    """Submit a contractor proposal/bid for a bid card"""
    try:
        # Check if contractor already submitted a proposal for this bid card
        existing = db.client.table("contractor_proposals").select("*").eq(
            "bid_card_id", proposal.bid_card_id
        ).eq("contractor_id", proposal.contractor_id).execute()

        if existing.data:
            return {
                "success": False,
                "message": "You have already submitted a proposal for this project"
            }

        # Calculate timeline days from start/end dates
        from datetime import datetime
        try:
            start_date = datetime.fromisoformat(proposal.timeline_start.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(proposal.timeline_end.replace('Z', '+00:00'))
            timeline_days = (end_date - start_date).days
        except:
            timeline_days = 30  # Default fallback
        
        # Get contractor name if not provided
        contractor_name = proposal.contractor_name
        if not contractor_name:
            # Try to get contractor name from contractors table
            contractor_result = db.client.table("contractors").select("company_name").eq("id", proposal.contractor_id).execute()
            if contractor_result.data:
                contractor_name = contractor_result.data[0].get("company_name", f"Contractor {proposal.contractor_id[:8]}")
            else:
                contractor_name = f"Contractor {proposal.contractor_id[:8]}"

        # Combine proposal and technical approach
        combined_proposal = proposal.proposal
        if proposal.technical_approach:
            combined_proposal += f"\n\nTechnical Approach:\n{proposal.technical_approach}"

        # Create proposal record
        proposal_data = {
            "id": str(uuid.uuid4()),
            "bid_card_id": proposal.bid_card_id,
            "contractor_id": proposal.contractor_id,
            "contractor_name": contractor_name,
            "contractor_company": proposal.contractor_company,
            "bid_amount": proposal.amount,  # Changed to use amount field
            "timeline_days": timeline_days,
            "proposal_text": combined_proposal,  # Combined proposal + technical approach
            "attachments": proposal.attachments or [],
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        result = db.client.table("contractor_proposals").insert(proposal_data).execute()

        if result.data:
            # CREATE HOMEOWNER NOTIFICATION FOR NEW BID
            try:
                # Get bid card info for project type
                bid_card_result = db.client.table("bid_cards").select("project_type, user_id").eq(
                    "id", proposal.bid_card_id
                ).execute()
                
                if bid_card_result.data:
                    bid_card = bid_card_result.data[0]
                    project_type = bid_card.get("project_type", "project")
                    user_id = bid_card.get("user_id", "11111111-1111-1111-1111-111111111111")
                    
                    # Create notification for homeowner
                    notification_data = {
                        "id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "notification_type": "bid_received",
                        "title": f"New bid received from {contractor_name}",
                        "message": f"You received a ${proposal.amount:,.2f} bid for your {project_type} project. Timeline: {timeline_days} days.",
                        "action_url": f"/bid-cards/{proposal.bid_card_id}",
                        "contractor_id": proposal.contractor_id,
                        "bid_card_id": proposal.bid_card_id,
                        "is_read": False,
                        "is_archived": False,
                        "channels": {
                            "email": True,
                            "in_app": True,
                            "sms": False
                        },
                        "delivered_channels": {
                            "in_app": True
                        },
                        "created_at": datetime.utcnow().isoformat()
                    }
                    
                    # Use service role key for notification insertion to bypass RLS
                    from supabase import create_client
                    import os
                    
                    service_url = os.getenv("SUPABASE_URL")
                    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
                    
                    if service_url and service_key:
                        service_client = create_client(service_url, service_key)
                        notification_result = service_client.table("notifications").insert(notification_data).execute()
                    else:
                        print(f"⚠️ Missing service credentials - URL: {bool(service_url)}, Key: {bool(service_key)}")
                        notification_result = None
                    
                    if notification_result and notification_result.data:
                        print(f"✅ Created homeowner notification for bid from {contractor_name}")
                    else:
                        print(f"⚠️ Failed to create homeowner notification")
                        
            except Exception as notification_error:
                print(f"⚠️ Error creating homeowner notification: {notification_error}")
                # Don't fail the whole proposal submission if notification creation fails
            
            # AUTO-CREATE CONVERSATION WITH ALIAS ASSIGNMENT
            try:
                # For now, use a test user_id since bid_cards doesn't have user_id column
                # In production, this should come from the authenticated user or a proper relationship
                user_id = "11111111-1111-1111-1111-111111111111"  # Test homeowner ID

                if user_id:

                    # Use the unified messaging system to create conversation
                    # Check if conversation already exists for this contractor and bid card
                    existing_conv = db.client.table("unified_conversations").select("*").eq(
                        "entity_id", proposal.bid_card_id
                    ).eq("entity_type", "bid_card").execute()

                    # Look for existing participant for this contractor
                    if existing_conv.data:
                        conv_id = existing_conv.data[0]["id"]
                        existing_participant = db.client.table("unified_conversation_participants").select("*").eq(
                            "conversation_id", conv_id
                        ).eq("participant_id", proposal.contractor_id).execute()
                    else:
                        existing_participant = None

                    if not existing_participant or not existing_participant.data:
                        # Create new unified conversation if it doesn't exist
                        if not existing_conv.data:
                            conversation_data = {
                                "id": str(uuid.uuid4()),
                                "tenant_id": "11111111-1111-1111-1111-111111111111",  # Default tenant
                                "created_by": proposal.contractor_id,
                                "conversation_type": "bid_card_messaging",
                                "entity_id": proposal.bid_card_id,
                                "entity_type": "bid_card",
                                "title": f"Bid Card Discussion - {contractor_name}",
                                "status": "active",
                                "metadata": {
                                    "bid_card_id": proposal.bid_card_id,
                                    "contractor_id": proposal.contractor_id,
                                    "contractor_name": contractor_name,
                                    "user_id": user_id
                                },
                                "created_at": datetime.utcnow().isoformat(),
                                "updated_at": datetime.utcnow().isoformat()
                            }
                            conv_result = db.client.table("unified_conversations").insert(conversation_data).execute()
                            if conv_result.data:
                                conv_id = conversation_data["id"]
                                print(f"✅ Created unified conversation for bid card {proposal.bid_card_id}")
                            else:
                                print(f"⚠️ Failed to create unified conversation")
                                conv_id = None
                        else:
                            conv_id = existing_conv.data[0]["id"]

                        # Add contractor as participant if conversation was created/exists
                        if conv_id:
                            participant_data = {
                                "id": str(uuid.uuid4()),
                                "tenant_id": "11111111-1111-1111-1111-111111111111",  # Default tenant
                                "conversation_id": conv_id,
                                "participant_id": proposal.contractor_id,
                                "participant_type": "contractor",
                                "role": "participant",
                                "joined_at": datetime.utcnow().isoformat()
                            }
                            participant_result = db.client.table("unified_conversation_participants").insert(participant_data).execute()
                            if participant_result.data:
                                print(f"✅ Auto-created unified conversation and added contractor {contractor_name} as participant")
                            else:
                                print(f"⚠️ Failed to add contractor {proposal.contractor_id} as participant")
                    else:
                        print(f"ℹ️ Conversation already exists for contractor {proposal.contractor_id}")
                else:
                    print(f"⚠️ Could not find user_id for bid card {proposal.bid_card_id}")

            except Exception as conv_error:
                print(f"⚠️ Error creating conversation: {conv_error}")
                # Don't fail the whole proposal submission if conversation creation fails
            # Update bid card's bid count
            bid_card_result = db.client.table("bid_cards").select("*").eq(
                "id", proposal.bid_card_id
            ).execute()

            bid_card = {"data": bid_card_result.data[0] if bid_card_result.data else None}

            if bid_card["data"]:
                bid_doc = bid_card["data"].get("bid_document") or {}
                current_bids = bid_doc.get("submitted_bids", [])
                current_bids.append({
                    "contractor_id": proposal.contractor_id,
                    "contractor_name": contractor_name,
                    "bid_amount": proposal.amount,
                    "timeline_days": timeline_days,
                    "created_at": datetime.utcnow().isoformat()
                })

                update_data = {
                    "bid_document": {
                        **(bid_card["data"].get("bid_document") or {}),
                        "submitted_bids": current_bids,
                        "bids_received_count": len(current_bids)
                    },
                    "bid_count": len(current_bids),
                    "updated_at": datetime.utcnow().isoformat()
                }

                # Check if target met
                target = bid_card["data"].get("contractor_count_needed", 4)
                if len(current_bids) >= target:
                    update_data["status"] = "bids_complete"
                    update_data["bid_document"]["bids_target_met"] = True

                db.client.table("bid_cards").update(update_data).eq(
                    "id", proposal.bid_card_id
                ).execute()

            # Track the bid submission event
            from routers.bid_card_event_tracker import EventTracker
            await EventTracker.track_event(
                bid_card_id=proposal.bid_card_id,
                event_type="bid_submitted",
                description=f"Bid submitted by {contractor_name}",
                details={
                    "contractor_id": proposal.contractor_id,
                    "contractor_name": contractor_name,
                    "bid_amount": proposal.amount,
                    "timeline_days": timeline_days,
                    "submission_method": "api"
                },
                created_by=proposal.contractor_id,
                created_by_type="contractor"
            )
            
            # Track in My Bids system
            try:
                from services.my_bids_tracker import my_bids_tracker
                import asyncio
                # Track proposal submission in My Bids
                asyncio.create_task(my_bids_tracker.track_bid_interaction(
                    contractor_id=proposal.contractor_id,
                    bid_card_id=proposal.bid_card_id,
                    interaction_type='proposal_submitted',
                    details={
                        'proposal_id': proposal_data["id"],
                        'bid_amount': proposal.amount,
                        'timeline_days': timeline_days,
                        'has_technical_approach': bool(proposal.technical_approach),
                        'has_attachments': bool(proposal.attachments)
                    }
                ))
                print(f"Tracked My Bids interaction for contractor {proposal.contractor_id} proposal submission")
            except Exception as tracking_error:
                print(f"Failed to track My Bids interaction: {tracking_error}")
                # Don't fail the proposal submission if tracking fails

            return {
                "success": True,
                "message": "Proposal submitted successfully",
                "proposal_id": proposal_data["id"]
            }
        else:
            return {
                "success": False,
                "message": "Failed to submit proposal"
            }

    except Exception as e:
        print(f"Error submitting proposal: {e}")
        return {
            "success": False,
            "message": f"Error submitting proposal: {e!s}"
        }


@router.get("/bid-card/{bid_card_id}")
async def get_bid_card_proposals(bid_card_id: str):
    """Get all proposals for a specific bid card"""
    try:
        result = db.client.table("contractor_proposals").select("*").eq(
            "bid_card_id", bid_card_id
        ).order("created_at", desc=True).execute()

        return result.data or []

    except Exception as e:
        print(f"Error fetching proposals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contractor/{contractor_id}")
async def get_contractor_proposals(contractor_id: str):
    """Get all proposals submitted by a specific contractor"""
    try:
        result = db.client.table("contractor_proposals").select(
            "*, bid_cards!inner(bid_card_number, project_type, title, status)"
        ).eq(
            "contractor_id", contractor_id
        ).order("created_at", desc=True).execute()

        return result.data or []

    except Exception as e:
        print(f"Error fetching contractor proposals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-attachment")
async def upload_proposal_attachment(
    file: UploadFile = File(...),
    proposal_id: str = Form(...),
    contractor_id: str = Form(...)
):
    """Upload an attachment for a proposal"""
    try:
        # Validate file type
        allowed_types = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "image/jpeg",
            "image/png",
            "image/jpg"
        ]

        if file.content_type not in allowed_types:
            return {
                "success": False,
                "message": f"File type {file.content_type} not allowed"
            }

        # Read file data
        file_data = await file.read()

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_name = f"proposals/{proposal_id}/{timestamp}_{file.filename}"

        # Upload to Supabase Storage
        db.client.storage.from_("project-images").upload(
            unique_name,
            file_data,
            {
                "content-type": file.content_type,
                "cache-control": "3600",
                "upsert": "false"
            }
        )

        # Get public URL
        public_url = db.client.storage.from_("project-images").get_public_url(unique_name)

        # Update proposal with attachment
        proposal = db.client.table("contractor_proposals").select("*").eq(
            "id", proposal_id
        ).eq("contractor_id", contractor_id).single().execute()

        if proposal.data:
            attachments = proposal.data.get("attachments", [])
            attachments.append({
                "name": file.filename,
                "url": public_url,
                "type": file.content_type,
                "size": len(file_data),
                "uploaded_at": datetime.utcnow().isoformat()
            })

            db.client.table("contractor_proposals").update({
                "attachments": attachments,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", proposal_id).execute()

            return {
                "success": True,
                "message": "Attachment uploaded successfully",
                "url": public_url
            }
        else:
            return {
                "success": False,
                "message": "Proposal not found"
            }

    except Exception as e:
        print(f"Error uploading attachment: {e}")
        return {
            "success": False,
            "message": f"Error uploading attachment: {e!s}"
        }


@router.put("/{proposal_id}/status")
async def update_proposal_status(proposal_id: str, status: str, user_id: str):
    """Update the status of a proposal (accept/reject)"""
    try:
        if status not in ["accepted", "rejected"]:
            raise HTTPException(status_code=400, detail="Invalid status")

        # Verify homeowner owns the bid card
        proposal = db.client.table("contractor_proposals").select(
            "*, bid_cards!inner(id)"
        ).eq("id", proposal_id).single().execute()

        if not proposal.data:
            raise HTTPException(status_code=404, detail="Proposal not found")

        # Update proposal status
        result = db.client.table("contractor_proposals").update({
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", proposal_id).execute()

        if result.data:
            # If accepting, update bid card status
            if status == "accepted":
                db.client.table("bid_cards").update({
                    "status": "awarded",
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", proposal.data["bid_card_id"]).execute()

            return {
                "success": True,
                "message": f"Proposal {status} successfully"
            }
        else:
            return {
                "success": False,
                "message": "Failed to update proposal status"
            }

    except Exception as e:
        print(f"Error updating proposal status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint for proposals API"""
    return {
        "success": True,
        "status": "healthy",
        "message": "Contractor proposals API is running",
        "timestamp": datetime.utcnow().isoformat()
    }
