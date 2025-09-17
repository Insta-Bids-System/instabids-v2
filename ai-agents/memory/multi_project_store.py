"""
Multi-Project Memory Store using LangGraph Store interface
Implements cross-project memory management for AI agents
"""
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_simple import db


logger = logging.getLogger(__name__)

@dataclass
class MemoryItem:
    """Individual memory item with metadata"""
    key: str
    value: dict[str, Any]
    namespace: tuple[str, ...]
    created_at: datetime
    updated_at: datetime

class MultiProjectMemoryStore:
    """
    Multi-project memory store that implements cross-project awareness
    while maintaining project separation

    Memory Organization:
    - User-level memories: ("user_memories", user_id)
    - Project contexts: ("project_contexts", user_id, project_id)
    - Cross-project summaries: ("project_summaries", user_id)
    """

    def __init__(self):
        self.db = db

    # === USER-LEVEL CROSS-PROJECT MEMORIES ===

    async def save_user_memory(self, user_id: str, memory_type: str, data: dict[str, Any]) -> bool:
        """Save cross-project user memory (preferences, history, patterns)"""
        try:
            memory_data = {
                "user_id": user_id,
                "memory_type": memory_type,
                "memory_data": data,
                "updated_at": datetime.utcnow().isoformat()
            }

            # Try to update existing memory first
            existing = self.db.client.table("user_memories").select("id").eq(
                "user_id", user_id
            ).eq("memory_type", memory_type).execute()

            if existing.data:
                # Update existing
                self.db.client.table("user_memories").update(memory_data).eq(
                    "user_id", user_id
                ).eq("memory_type", memory_type).execute()
            else:
                # Create new
                memory_data["created_at"] = datetime.utcnow().isoformat()
                self.db.client.table("user_memories").insert(memory_data).execute()

            logger.info(f"Saved user memory {memory_type} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving user memory: {e}")
            return False

    async def get_user_memories(self, user_id: str, memory_type: Optional[str] = None) -> dict[str, Any]:
        """Get cross-project memories for a user"""
        try:
            query = self.db.client.table("user_memories").select("*").eq("user_id", user_id)

            if memory_type:
                query = query.eq("memory_type", memory_type)

            result = query.execute()

            memories = {}
            for item in result.data or []:
                memories[item["memory_type"]] = item["memory_data"]

            return memories

        except Exception as e:
            logger.error(f"Error getting user memories: {e}")
            return {}

    # === PROJECT-SPECIFIC CONTEXTS ===

    async def save_project_context(self, user_id: str, project_id: str, context: dict[str, Any]) -> bool:
        """Save project-specific AI context and state"""
        try:
            context_data = {
                "user_id": user_id,
                "project_id": project_id,
                "context_data": context,
                "last_accessed": datetime.utcnow().isoformat()
            }

            # Try to update existing context
            existing = self.db.client.table("project_contexts").select("id").eq(
                "user_id", user_id
            ).eq("project_id", project_id).execute()

            if existing.data:
                # Update existing
                self.db.client.table("project_contexts").update(context_data).eq(
                    "user_id", user_id
                ).eq("project_id", project_id).execute()
            else:
                # Create new
                self.db.client.table("project_contexts").insert(context_data).execute()

            logger.info(f"Saved project context for project {project_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving project context: {e}")
            return False

    async def get_project_context(self, user_id: str, project_id: str) -> dict[str, Any]:
        """Get context for specific project"""
        try:
            result = self.db.client.table("project_contexts").select("*").eq(
                "user_id", user_id
            ).eq("project_id", project_id).execute()

            if result.data:
                return result.data[0]["context_data"]
            return {}

        except Exception as e:
            logger.error(f"Error getting project context: {e}")
            return {}

    # === CROSS-PROJECT SUMMARIES ===

    async def save_project_summary(self, user_id: str, project_id: str, summary: dict[str, Any]) -> bool:
        """Save AI-generated project summary for cross-project awareness"""
        try:
            summary_data = {
                "user_id": user_id,
                "project_id": project_id,
                "summary_data": summary,
                "last_updated": datetime.utcnow().isoformat()
            }

            # Try to update existing summary
            existing = self.db.client.table("project_summaries").select("id").eq(
                "user_id", user_id
            ).eq("project_id", project_id).execute()

            if existing.data:
                # Update existing
                self.db.client.table("project_summaries").update(summary_data).eq(
                    "user_id", user_id
                ).eq("project_id", project_id).execute()
            else:
                # Create new
                self.db.client.table("project_summaries").insert(summary_data).execute()

            logger.info(f"Saved project summary for project {project_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving project summary: {e}")
            return False

    async def get_user_projects_summary(self, user_id: str) -> list[dict[str, Any]]:
        """Get summaries of all user's projects for AI context"""
        try:
            result = self.db.client.table("project_summaries").select("*").eq(
                "user_id", user_id
            ).order("last_updated", desc=True).execute()

            return result.data or []

        except Exception as e:
            logger.error(f"Error getting user projects summary: {e}")
            return []

    # === CROSS-PROJECT INTELLIGENCE ===

    async def get_cross_project_context(self, user_id: str, current_project_id: str) -> dict[str, Any]:
        """
        Get comprehensive cross-project context for AI agent
        Includes user memories, other project summaries, and current project context
        """
        try:
            # Get user-level memories
            user_memories = await self.get_user_memories(user_id)

            # Get current project context
            current_context = await self.get_project_context(user_id, current_project_id)

            # Get summaries of other projects
            all_summaries = await self.get_user_projects_summary(user_id)
            other_projects = [s for s in all_summaries if s["project_id"] != current_project_id]

            # Get current project details from main projects table
            current_project = None
            try:
                # Get user_id for user
                homeowner_result = self.db.client.table("homeowners").select("id").eq("user_id", user_id).execute()
                if homeowner_result.data:
                    user_id = homeowner_result.data[0]["id"]
                    project_result = self.db.client.table("projects").select("*").eq(
                        "id", current_project_id
                    ).eq("user_id", user_id).execute()
                    if project_result.data:
                        current_project = project_result.data[0]
            except Exception as e:
                logger.warning(f"Could not get current project details: {e}")

            return {
                "user_memories": user_memories,
                "current_project": current_project,
                "current_context": current_context,
                "other_projects_count": len(other_projects),
                "other_projects_summaries": other_projects[:5],  # Limit to 5 most recent
                "cross_project_context": True,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting cross-project context: {e}")
            return {}

    # === INTELLIGENT PROJECT ANALYSIS ===

    async def analyze_project_relationships(self, user_id: str, current_project_data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze relationships between current project and user's other projects
        This enables AI to ask questions like "Is this in addition to your lawn project?"
        """
        try:
            # Get all user's projects
            homeowner_result = self.db.client.table("homeowners").select("id").eq("user_id", user_id).execute()
            if not homeowner_result.data:
                return {"related_projects": [], "analysis": "No previous projects found"}

            user_id = homeowner_result.data[0]["id"]
            projects_result = self.db.client.table("projects").select("*").eq(
                "user_id", user_id
            ).execute()

            if not projects_result.data:
                return {"related_projects": [], "analysis": "No previous projects found"}

            # Analyze relationships
            all_projects = projects_result.data
            current_category = current_project_data.get("category", "").lower()
            current_title = current_project_data.get("title", "").lower()

            related_projects = []

            for project in all_projects:
                if project["id"] == current_project_data.get("id"):
                    continue  # Skip current project

                similarity_score = 0
                relationship_type = []

                # Category similarity
                if project["category"].lower() == current_category:
                    similarity_score += 3
                    relationship_type.append("same_category")

                # Title keyword similarity (simple approach)
                project_title = project["title"].lower()
                common_words = set(current_title.split()) & set(project_title.split())
                if common_words:
                    similarity_score += len(common_words)
                    relationship_type.append("similar_scope")

                # Location similarity (if available)
                if (project.get("location") and
                    current_project_data.get("location") and
                    project["location"].lower() == current_project_data.get("location", "").lower()):
                    similarity_score += 2
                    relationship_type.append("same_location")

                # Timeline proximity (active projects)
                if project["status"] in ["active", "in_progress", "draft"]:
                    similarity_score += 1
                    relationship_type.append("concurrent")

                if similarity_score > 0:
                    related_projects.append({
                        "project_id": project["id"],
                        "title": project["title"],
                        "category": project["category"],
                        "status": project["status"],
                        "similarity_score": similarity_score,
                        "relationship_types": relationship_type
                    })

            # Sort by similarity score
            related_projects.sort(key=lambda x: x["similarity_score"], reverse=True)

            # Generate analysis text
            analysis = self._generate_project_analysis(related_projects, current_project_data)

            return {
                "related_projects": related_projects[:3],  # Top 3 most related
                "analysis": analysis,
                "total_projects": len(all_projects),
                "active_projects": len([p for p in all_projects if p["status"] in ["active", "in_progress"]])
            }

        except Exception as e:
            logger.error(f"Error analyzing project relationships: {e}")
            return {"related_projects": [], "analysis": "Error analyzing project relationships"}

    def _generate_project_analysis(self, related_projects: list[dict], current_project: dict[str, Any]) -> str:
        """Generate human-readable analysis of project relationships"""
        if not related_projects:
            return "This appears to be your first project of this type."

        analysis_parts = []

        # Most similar project
        top_match = related_projects[0]
        if "same_category" in top_match["relationship_types"]:
            analysis_parts.append(f"You have a similar {top_match['category']} project: '{top_match['title']}'.")

        # Concurrent projects
        concurrent = [p for p in related_projects if "concurrent" in p["relationship_types"]]
        if concurrent:
            if len(concurrent) == 1:
                analysis_parts.append(f"You currently have another active project: '{concurrent[0]['title']}'.")
            else:
                analysis_parts.append(f"You have {len(concurrent)} other active projects.")

        # Same location
        same_location = [p for p in related_projects if "same_location" in p["relationship_types"]]
        if same_location:
            analysis_parts.append(f"This is at the same location as your '{same_location[0]['title']}' project.")

        return " ".join(analysis_parts) if analysis_parts else "This project appears to be independent of your other projects."

# Global instance
memory_store = MultiProjectMemoryStore()
