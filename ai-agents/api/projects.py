"""
Projects API endpoints for multi-project system
Works with existing InstaBids database schema
"""
import logging
import os
import sys
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_simple import db


logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for request/response
class CreateProjectRequest(BaseModel):
    user_id: str
    title: str
    category: str
    description: str
    urgency: Optional[str] = "flexible"
    budget_range: Optional[str] = None
    location: Optional[str] = None

class UpdateProjectRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    urgency: Optional[str] = None
    budget_range: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: str
    category: str
    urgency: str
    budget_range: Optional[str]
    location: Optional[str]
    status: str
    images: Optional[list[str]]
    documents: Optional[list[str]]
    cia_conversation_id: Optional[str]
    job_assessment: Optional[dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    conversation_count: Optional[int] = 0
    last_activity: Optional[datetime] = None

@router.post("/projects", response_model=ProjectResponse)
async def create_project(request: CreateProjectRequest):
    """Create a new project for a homeowner"""
    try:
        # Verify homeowner exists
        homeowner_check = db.client.table("homeowners").select("id").eq("id", request.user_id).execute()

        if not homeowner_check.data:
            raise HTTPException(status_code=404, detail="Homeowner not found")

        # Create project with required fields
        project_data = {
            "user_id": request.user_id,
            "title": request.title,
            "category": request.category,
            "description": request.description,
            "urgency": request.urgency,
            "budget_range": request.budget_range,
            "location": request.location,
            "status": "draft"  # Start as draft
        }

        result = db.client.table("projects").insert(project_data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create project")

        project = result.data[0]

        # Convert to response model
        return ProjectResponse(
            id=project["id"],
            user_id=project["user_id"],
            title=project["title"],
            description=project["description"],
            category=project["category"],
            urgency=project["urgency"],
            budget_range=project["budget_range"],
            location=project["location"],
            status=project["status"],
            images=project.get("images", []),
            documents=project.get("documents", []),
            cia_conversation_id=project.get("cia_conversation_id"),
            job_assessment=project.get("job_assessment"),
            created_at=project["created_at"],
            updated_at=project["updated_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/homeowners/{user_id}/projects", response_model=list[ProjectResponse])
async def get_homeowner_projects(user_id: str):
    """Get all projects for a specific homeowner"""
    try:
        # Get projects for homeowner
        projects_result = db.client.table("projects").select("*").eq(
            "user_id", user_id
        ).order("updated_at", desc=True).execute()

        if not projects_result.data:
            return []

        # Get conversation counts for each project
        projects_with_stats = []

        for project in projects_result.data:
            # Count conversations for this project (if cia_conversation_id exists)
            conversation_count = 0
            last_activity = project["updated_at"]

            if project.get("cia_conversation_id"):
                conversations = db.client.table("agent_conversations").select("updated_at").eq(
                    "thread_id", project["cia_conversation_id"]
                ).execute()

                if conversations.data:
                    conversation_count = len(conversations.data)
                    # Get most recent conversation activity
                    latest_conv = max(conversations.data, key=lambda x: x["updated_at"])
                    if latest_conv["updated_at"] > last_activity:
                        last_activity = latest_conv["updated_at"]

            projects_with_stats.append(ProjectResponse(
                id=project["id"],
                user_id=project["user_id"],
                title=project["title"],
                description=project["description"],
                category=project["category"],
                urgency=project["urgency"],
                budget_range=project["budget_range"],
                location=project["location"],
                status=project["status"],
                images=project.get("images", []),
                documents=project.get("documents", []),
                cia_conversation_id=project.get("cia_conversation_id"),
                job_assessment=project.get("job_assessment"),
                created_at=project["created_at"],
                updated_at=project["updated_at"],
                conversation_count=conversation_count,
                last_activity=last_activity
            ))

        return projects_with_stats

    except Exception as e:
        logger.error(f"Error getting homeowner projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get a specific project by ID"""
    try:
        result = db.client.table("projects").select("*").eq("id", project_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Project not found")

        project = result.data[0]

        return ProjectResponse(
            id=project["id"],
            user_id=project["user_id"],
            title=project["title"],
            description=project["description"],
            category=project["category"],
            urgency=project["urgency"],
            budget_range=project["budget_range"],
            location=project["location"],
            status=project["status"],
            images=project.get("images", []),
            documents=project.get("documents", []),
            cia_conversation_id=project.get("cia_conversation_id"),
            job_assessment=project.get("job_assessment"),
            created_at=project["created_at"],
            updated_at=project["updated_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, request: UpdateProjectRequest):
    """Update a project"""
    try:
        # Check if project exists
        existing = db.client.table("projects").select("*").eq("id", project_id).execute()

        if not existing.data:
            raise HTTPException(status_code=404, detail="Project not found")

        # Build update data from non-None fields
        update_data = {}
        for field, value in request.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value

        if not update_data:
            # No fields to update, return existing
            project = existing.data[0]
        else:
            # Update the project
            result = db.client.table("projects").update(update_data).eq("id", project_id).execute()

            if not result.data:
                raise HTTPException(status_code=500, detail="Failed to update project")

            project = result.data[0]

        return ProjectResponse(
            id=project["id"],
            user_id=project["user_id"],
            title=project["title"],
            description=project["description"],
            category=project["category"],
            urgency=project["urgency"],
            budget_range=project["budget_range"],
            location=project["location"],
            status=project["status"],
            images=project.get("images", []),
            documents=project.get("documents", []),
            cia_conversation_id=project.get("cia_conversation_id"),
            job_assessment=project.get("job_assessment"),
            created_at=project["created_at"],
            updated_at=project["updated_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    try:
        # Check if project exists
        existing = db.client.table("projects").select("id").eq("id", project_id).execute()

        if not existing.data:
            raise HTTPException(status_code=404, detail="Project not found")

        # Delete the project
        db.client.table("projects").delete().eq("id", project_id).execute()

        return {"message": "Project deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/link-conversation")
async def link_conversation_to_project(project_id: str, conversation_id: str):
    """Link a CIA conversation to a project"""
    try:
        # Verify project exists
        project_check = db.client.table("projects").select("id").eq("id", project_id).execute()

        if not project_check.data:
            raise HTTPException(status_code=404, detail="Project not found")

        # Verify conversation exists
        conversation_check = db.client.table("agent_conversations").select("thread_id").eq(
            "thread_id", conversation_id
        ).execute()

        if not conversation_check.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Link conversation to project
        update_result = db.client.table("projects").update({
            "cia_conversation_id": conversation_id
        }).eq("id", project_id).execute()

        if not update_result.data:
            raise HTTPException(status_code=500, detail="Failed to link conversation")

        return {"message": "Conversation linked to project successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking conversation to project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/conversations")
async def get_project_conversations(project_id: str):
    """Get all conversations associated with a project"""
    try:
        # Get project to find linked conversation
        project = db.client.table("projects").select("cia_conversation_id").eq("id", project_id).execute()

        if not project.data:
            raise HTTPException(status_code=404, detail="Project not found")

        conversations = []
        cia_conversation_id = project.data[0].get("cia_conversation_id")

        if cia_conversation_id:
            # Get the linked conversation
            conversation_result = db.client.table("agent_conversations").select("*").eq(
                "thread_id", cia_conversation_id
            ).execute()

            conversations = conversation_result.data or []

        return {
            "project_id": project_id,
            "conversations": conversations
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
