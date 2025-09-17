"""
LangGraph integration for multi-project memory system
Provides project-aware agent initialization and memory management
"""
import logging
import os
import sys
from datetime import datetime
from typing import Any, Optional


# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.multi_project_store import MultiProjectMemoryStore, memory_store


logger = logging.getLogger(__name__)

class ProjectAwareAgentConfig:
    """
    Configuration class for project-aware AI agents
    Provides cross-project memory context and project-specific state
    """

    def __init__(self, user_id: str, project_id: Optional[str] = None, session_id: Optional[str] = None):
        self.user_id = user_id
        self.project_id = project_id
        self.session_id = session_id
        self.memory_store = memory_store

    async def initialize_agent_context(self) -> dict[str, Any]:
        """
        Initialize comprehensive agent context with cross-project awareness
        This is called before agent processing to load all relevant context
        """
        try:
            context = {
                "user_id": self.user_id,
                "project_id": self.project_id,
                "session_id": self.session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "cross_project_enabled": True
            }

            # Load cross-project context if project is specified
            if self.project_id:
                cross_project_context = await self.memory_store.get_cross_project_context(
                    self.user_id, self.project_id
                )
                context.update(cross_project_context)

                # Analyze project relationships for intelligent questions
                if cross_project_context.get("current_project"):
                    relationships = await self.memory_store.analyze_project_relationships(
                        self.user_id, cross_project_context["current_project"]
                    )
                    context["project_relationships"] = relationships

            # Load user memories even if no specific project
            else:
                user_memories = await self.memory_store.get_user_memories(self.user_id)
                context["user_memories"] = user_memories

                # Get overview of all user projects
                project_summaries = await self.memory_store.get_user_projects_summary(self.user_id)
                context["user_projects_overview"] = {
                    "total_projects": len(project_summaries),
                    "recent_projects": project_summaries[:3]
                }

            logger.info(f"Initialized agent context for user {self.user_id}, project {self.project_id}")
            return context

        except Exception as e:
            logger.error(f"Error initializing agent context: {e}")
            return {
                "user_id": self.user_id,
                "project_id": self.project_id,
                "error": str(e),
                "cross_project_enabled": False
            }

    async def update_agent_memory(self, conversation_result: dict[str, Any]) -> bool:
        """
        Update memory stores based on agent conversation results
        Called after agent processing to save new insights and context
        """
        try:
            # Update user-level memories (preferences, patterns)
            await self._update_user_memories(conversation_result)

            # Update project-specific context if project is specified
            if self.project_id:
                await self._update_project_context(conversation_result)

                # Update project summary for cross-project awareness
                await self._update_project_summary(conversation_result)

            logger.info(f"Updated agent memory for user {self.user_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating agent memory: {e}")
            return False

    async def _update_user_memories(self, conversation_result: dict[str, Any]) -> None:
        """Update cross-project user memories"""

        # Extract user preferences from conversation
        state = conversation_result.get("state", {})
        collected_info = state.get("collected_info", {})

        # Budget preferences
        if collected_info.get("budget_min") or collected_info.get("budget_max"):
            budget_memory = {
                "recent_budget_ranges": [],
                "budget_preference_patterns": {}
            }

            # Get existing budget memory
            existing_memories = await self.memory_store.get_user_memories(self.user_id, "budget_preferences")
            if existing_memories:
                budget_memory.update(existing_memories.get("budget_preferences", budget_memory))

            # Add new budget info
            if collected_info.get("budget_min") and collected_info.get("budget_max"):
                budget_range = {
                    "min": collected_info["budget_min"],
                    "max": collected_info["budget_max"],
                    "project_type": collected_info.get("project_type"),
                    "timestamp": datetime.utcnow().isoformat()
                }
                budget_memory["recent_budget_ranges"].append(budget_range)
                budget_memory["recent_budget_ranges"] = budget_memory["recent_budget_ranges"][-5:]  # Keep last 5

            await self.memory_store.save_user_memory(self.user_id, "budget_preferences", budget_memory)

        # Communication preferences
        communication_memory = {
            "preferred_communication_style": state.get("communication_style", "detailed"),
            "response_length_preference": "detailed" if len(conversation_result.get("response", "")) > 200 else "concise",
            "last_updated": datetime.utcnow().isoformat()
        }

        await self.memory_store.save_user_memory(self.user_id, "communication_preferences", communication_memory)

        # Project type preferences
        if collected_info.get("project_type"):
            project_types_memory = {
                "project_types_discussed": [],
                "expertise_areas": []
            }

            existing_project_memory = await self.memory_store.get_user_memories(self.user_id, "project_preferences")
            if existing_project_memory:
                project_types_memory.update(existing_project_memory.get("project_preferences", project_types_memory))

            project_type = collected_info["project_type"]
            if project_type not in project_types_memory["project_types_discussed"]:
                project_types_memory["project_types_discussed"].append(project_type)

            await self.memory_store.save_user_memory(self.user_id, "project_preferences", project_types_memory)

    async def _update_project_context(self, conversation_result: dict[str, Any]) -> None:
        """Update project-specific context"""

        context_data = {
            "conversation_stage": conversation_result.get("current_phase", "discovery"),
            "collected_information": conversation_result.get("state", {}).get("collected_info", {}),
            "ready_for_next_stage": conversation_result.get("ready_for_jaa", False),
            "missing_information": conversation_result.get("missing_fields", []),
            "conversation_history_summary": {
                "total_messages": conversation_result.get("message_count", 1),
                "last_interaction": datetime.utcnow().isoformat(),
                "key_topics_discussed": self._extract_key_topics(conversation_result)
            },
            "agent_insights": {
                "user_engagement_level": self._assess_engagement(conversation_result),
                "information_completeness": 1.0 - (len(conversation_result.get("missing_fields", [])) / 10.0),
                "project_clarity": "high" if conversation_result.get("ready_for_jaa", False) else "developing"
            }
        }

        await self.memory_store.save_project_context(self.user_id, self.project_id, context_data)

    async def _update_project_summary(self, conversation_result: dict[str, Any]) -> None:
        """Update project summary for cross-project awareness"""

        state = conversation_result.get("state", {})
        collected_info = state.get("collected_info", {})

        # Generate title from project type and description
        project_type = collected_info.get("project_type", "unknown")
        collected_info.get("project_description", "")

        # Create a readable title
        if project_type != "unknown":
            project_title = project_type.replace("_", " ").title()
            if "kitchen" in project_type.lower():
                project_title = "Kitchen Renovation"
            elif "bathroom" in project_type.lower():
                project_title = "Bathroom Remodel"
            elif "lawn" in project_type.lower():
                project_title = "Lawn Care Service"
        else:
            project_title = "Home Improvement Project"

        summary_data = {
            "project_title": project_title,
            "project_type": project_type,
            "category": collected_info.get("category", "general"),
            "status": "planning",  # Default status
            "budget_range": f"${collected_info.get('budget_min', 0):,}-${collected_info.get('budget_max', 0):,}" if collected_info.get("budget_min") else "Not specified",
            "timeline": collected_info.get("timeline_start") or collected_info.get("timeline", "Not specified"),
            "urgency": collected_info.get("urgency", "medium"),
            "key_features": collected_info.get("materials_preferences", []) if isinstance(collected_info.get("materials_preferences"), list) else [collected_info.get("materials_preferences")] if collected_info.get("materials_preferences") else [],
            "key_requirements": collected_info.get("requirements", []),
            "location_context": collected_info.get("location") or collected_info.get("address"),
            "conversation_progress": {
                "stage": conversation_result.get("current_phase", "discovery"),
                "completeness": 1.0 - (len(conversation_result.get("missing_fields", [])) / 10.0),
                "ready_for_implementation": conversation_result.get("ready_for_jaa", False)
            },
            "ai_generated_summary": self._generate_project_summary(collected_info),
            "last_updated": datetime.utcnow().isoformat()
        }

        await self.memory_store.save_project_summary(self.user_id, self.project_id, summary_data)

    def _extract_key_topics(self, conversation_result: dict[str, Any]) -> list[str]:
        """Extract key topics from conversation for memory"""
        topics = []

        collected_info = conversation_result.get("state", {}).get("collected_info", {})

        # Add explicit topics
        if collected_info.get("project_type"):
            topics.append(collected_info["project_type"])

        if collected_info.get("materials"):
            topics.extend(collected_info["materials"])

        if collected_info.get("requirements"):
            topics.extend(collected_info["requirements"][:3])  # Top 3 requirements

        # Add inferred topics from response
        response = conversation_result.get("response", "").lower()
        if "budget" in response:
            topics.append("budget_discussion")
        if "timeline" in response:
            topics.append("timeline_planning")
        if "contractor" in response:
            topics.append("contractor_requirements")

        return topics[:5]  # Limit to 5 key topics

    def _assess_engagement(self, conversation_result: dict[str, Any]) -> str:
        """Assess user engagement level from conversation"""

        # Simple heuristics for engagement assessment
        response_length = len(conversation_result.get("response", ""))
        missing_fields_count = len(conversation_result.get("missing_fields", []))

        if missing_fields_count <= 2 and response_length > 100:
            return "high"
        elif missing_fields_count <= 5:
            return "medium"
        else:
            return "developing"

    def _generate_project_summary(self, collected_info: dict[str, Any]) -> str:
        """Generate AI-friendly project summary for cross-project context"""

        parts = []

        if collected_info.get("project_type"):
            parts.append(f"{collected_info['project_type']} project")

        if collected_info.get("budget_min") and collected_info.get("budget_max"):
            parts.append(f"budget ${collected_info['budget_min']:,}-${collected_info['budget_max']:,}")

        if collected_info.get("timeline"):
            parts.append(f"timeline: {collected_info['timeline']}")

        if collected_info.get("urgency"):
            parts.append(f"urgency: {collected_info['urgency']}")

        return ", ".join(parts) if parts else "Project details being gathered"

async def setup_project_aware_agent(user_id: str, project_id: Optional[str] = None, session_id: Optional[str] = None) -> dict[str, Any]:
    """
    Setup function for project-aware agents
    Returns configuration dict that can be passed to LangGraph agents
    """
    try:
        config = ProjectAwareAgentConfig(user_id, project_id, session_id)
        context = await config.initialize_agent_context()

        # Return LangGraph-compatible configuration
        return {
            "configurable": {
                "user_id": user_id,
                "project_id": project_id,
                "session_id": session_id,
                "cross_project_context": context,
                "memory_store": memory_store,
                "config_instance": config
            }
        }

    except Exception as e:
        logger.error(f"Error setting up project-aware agent: {e}")
        return {
            "configurable": {
                "user_id": user_id,
                "project_id": project_id,
                "session_id": session_id,
                "error": str(e)
            }
        }

async def update_agent_memory_after_conversation(
    user_id: str,
    project_id: str,
    session_id: str,
    conversation_summary: str,
    extracted_info: dict[str, Any],
    user_preferences_discovered: dict[str, Any],
    project_relationships: dict[str, Any]
) -> bool:
    """
    Update memory after agent conversation with discovered insights
    Call this after each agent interaction to maintain memory
    """
    try:
        # Initialize memory store
        memory_store = MultiProjectMemoryStore()

        # Update user preferences if discovered
        if user_preferences_discovered:
            # Budget preferences
            if user_preferences_discovered.get("budget_preference"):
                budget_data = await memory_store.get_user_memories(user_id)
                budget_memory = budget_data.get("budget_preferences", {
                    "recent_budget_ranges": [],
                    "last_updated": datetime.utcnow().isoformat()
                })

                budget_str = f"${user_preferences_discovered['budget_preference']}"
                if budget_str not in budget_memory["recent_budget_ranges"]:
                    budget_memory["recent_budget_ranges"].append(budget_str)
                    # Keep only last 5 budget ranges
                    budget_memory["recent_budget_ranges"] = budget_memory["recent_budget_ranges"][-5:]

                await memory_store.save_user_memory(user_id, "budget_preferences", budget_memory)

            # Communication style
            if user_preferences_discovered.get("communication_style"):
                comm_memory = {
                    "preferred_communication_style": user_preferences_discovered["communication_style"],
                    "last_updated": datetime.utcnow().isoformat()
                }
                await memory_store.save_user_memory(user_id, "communication_preferences", comm_memory)

        # Update project context
        project_context = {
            "last_conversation_summary": conversation_summary,
            "collected_info": extracted_info,
            "last_session_id": session_id,
            "last_updated": datetime.utcnow().isoformat()
        }

        # Add project relationships if discovered
        if project_relationships.get("mentioned_other_projects"):
            project_context["mentioned_other_projects"] = True
            project_context["project_type"] = project_relationships.get("project_type")

        await memory_store.save_project_context(user_id, project_id, project_context)

        # Update project summary
        project_summary = {
            "project_title": extracted_info.get("project_type", "Unknown Project"),
            "project_type": extracted_info.get("project_type"),
            "budget_range": f"${extracted_info.get('budget_min', 0)}-${extracted_info.get('budget_max', 0)}" if extracted_info.get("budget_min") else None,
            "timeline": extracted_info.get("urgency"),
            "last_updated": datetime.utcnow().isoformat()
        }

        await memory_store.save_project_summary(user_id, project_id, project_summary)

        logger.info(f"Successfully updated memory for user {user_id}, project {project_id}")
        return True

    except Exception as e:
        logger.error(f"Error updating memory after conversation: {e}")
        return False
