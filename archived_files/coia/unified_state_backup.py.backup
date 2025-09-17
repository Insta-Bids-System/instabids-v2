"""
Unified COIA State Schema for LangGraph
Combines all three agent capabilities into a single state machine
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated, Any, Literal, Optional, TypedDict

from langgraph.graph.message import AnyMessage, add_messages

from .state import ContractorProfile, ConversationMessage


class UnifiedCoIAState(TypedDict):
    """
    Unified state schema for multi-mode COIA agent
    Supports conversation, research, and intelligence modes
    """

    # Core conversation tracking
    messages: Annotated[list[AnyMessage], add_messages]
    session_id: str
    user_id: Optional[str]
    contractor_lead_id: Optional[str]
    contractor_id: Optional[str]

    # Interface and mode management
    interface: Optional[str]  # "chat", "research_portal", "intelligence_dashboard"
    current_mode: Annotated[Literal["conversation", "research", "intelligence"], lambda x, y: y]  # Allow last-write-wins
    previous_mode: Annotated[Optional[str], lambda x, y: y]  # Allow last-write-wins
    mode_confidence: Annotated[float, lambda x, y: y]  # Allow last-write-wins
    transition_reason: Annotated[Optional[str], lambda x, y: y]  # Allow last-write-wins
    last_updated: Annotated[str, lambda x, y: y]  # Allow last-write-wins

    # Contractor profile data (unified from all modes)
    contractor_profile: Annotated[dict[str, Any], lambda x, y: {**x, **y} if x else y]  # Merge dicts
    profile_completeness: Annotated[float, lambda x, y: max(x, y) if x else y]  # Take higher completeness

    # Business information detection (from conversation)
    company_name: Optional[str]
    company_website: Optional[str]
    business_info: Optional[dict[str, str]]  # Raw extracted business info

    # Research mode data (from PlaywrightWebsiteEnricher)
    research_completed: bool
    research_confirmed: bool
    research_findings: Optional[dict[str, Any]]  # EnrichedContractorData
    website_research_status: Optional[str]  # "pending", "completed", "failed"

    # Intelligence mode data (from Google Places + advanced processing)
    intelligence_data: Optional[dict[str, Any]]  # RealBusinessData
    google_places_data: Optional[dict[str, Any]]
    returning_contractor_id: Optional[str]
    persistent_memory_loaded: bool

    # Tool management and capabilities
    available_capabilities: list[str]  # ["web_research", "google_places", "memory"]
    active_tools: list[str]
    tool_results: Optional[dict[str, Any]]

    # Control flow and completion
    next_action: Optional[str]
    completion_ready: bool
    contractor_created: bool
    conversion_successful: bool
    error_state: Optional[str]

    # Context from original project (if applicable)
    original_project_id: Optional[str]
    source_channel: Optional[str]
    matching_projects_count: int


@dataclass
class UnifiedCoIAConversationState:
    """
    Extended conversation state that includes all mode capabilities
    Used for serialization and more complex state operations
    """

    # Core identifiers
    session_id: str
    contractor_lead_id: Optional[str] = None
    contractor_id: Optional[str] = None
    user_id: Optional[str] = None

    # Mode management
    current_mode: str = "conversation"
    previous_mode: Optional[str] = None
    mode_confidence: float = 1.0
    interface: Optional[str] = None
    transition_reason: Optional[str] = None

    # Conversation tracking
    messages: list[ConversationMessage] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)

    # Unified contractor profile
    profile: ContractorProfile = field(default_factory=ContractorProfile)

    # Business research data (from all modes)
    business_research: Optional[dict[str, str]] = None  # Initial business detection
    research_completed: bool = False
    research_confirmed: bool = False
    research_data: Optional[Any] = None  # EnrichedContractorData from research mode

    # Intelligence data (from advanced mode)
    intelligence_data: Optional[Any] = None  # RealBusinessData from intelligence mode
    google_places_data: Optional[dict[str, Any]] = None
    returning_contractor_id: Optional[str] = None
    persistent_memory_loaded: bool = False

    # Capabilities and tools
    available_capabilities: list[str] = field(default_factory=list)
    active_capabilities: list[str] = field(default_factory=list)

    # Context and completion
    original_project_id: Optional[str] = None
    source_channel: Optional[str] = None
    matching_projects_count: int = 0
    completed: bool = False
    completed_at: Optional[datetime] = None
    conversion_successful: bool = False

    # Auth credentials (for login info)
    auth_credentials: Optional[dict[str, Any]] = None

    def add_message(self, role: str, content: str, stage: Optional[str] = None,
                   profile_updates: Optional[dict[str, Any]] = None):
        """Add a message to the conversation history"""
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            stage=stage,
            profile_updates=profile_updates
        )
        self.messages.append(message)
        self.last_updated = datetime.now()

        if stage:
            # Update mode based on stage if applicable
            stage_to_mode_map = {
                "welcome": "conversation",
                "experience": "conversation",
                "service_area": "conversation",
                "differentiators": "conversation",
                "research_confirmation": "research",
                "website_research": "research",
                "intelligence_enhancement": "intelligence",
                "completed": "conversation"
            }
            if stage in stage_to_mode_map:
                new_mode = stage_to_mode_map[stage]
                if new_mode != self.current_mode:
                    self.previous_mode = self.current_mode
                    self.current_mode = new_mode
                    self.transition_reason = f"Stage progression: {stage}"

    def update_profile(self, updates: dict[str, Any]):
        """Update profile with new data"""
        for key, value in updates.items():
            if hasattr(self.profile, key):
                if key in ["service_areas", "specializations", "preferred_project_types", "certifications"]:
                    # Handle list fields
                    if isinstance(value, list):
                        setattr(self.profile, key, value)
                    else:
                        current_list = getattr(self.profile, key)
                        if value not in current_list:
                            current_list.append(value)
                else:
                    setattr(self.profile, key, value)

        self.last_updated = datetime.now()

    def transition_mode(self, new_mode: str, reason: str):
        """Transition to a new operational mode"""
        if new_mode != self.current_mode:
            self.previous_mode = self.current_mode
            self.current_mode = new_mode
            self.transition_reason = reason
            self.mode_confidence = 0.8  # Start with moderate confidence
            self.last_updated = datetime.now()

    def mark_completed(self, contractor_id: str):
        """Mark conversation as completed with contractor creation"""
        self.completed = True
        self.completed_at = datetime.now()
        self.contractor_id = contractor_id
        self.conversion_successful = True
        self.current_mode = "conversation"  # Return to conversation for completion message

    def to_langgraph_state(self) -> UnifiedCoIAState:
        """Convert to LangGraph state format"""
        return {
            "messages": [],  # Will be populated with AnyMessage objects
            "session_id": self.session_id,
            "user_id": self.user_id,
            "contractor_lead_id": self.contractor_lead_id,
            "contractor_id": self.contractor_id,
            "interface": self.interface,
            "current_mode": self.current_mode,
            "previous_mode": self.previous_mode,
            "mode_confidence": self.mode_confidence,
            "transition_reason": self.transition_reason,
            "last_updated": self.last_updated.isoformat(),
            "contractor_profile": self.profile.to_dict(),
            "profile_completeness": self.profile.calculate_completeness(),
            "company_name": getattr(self.profile, "company_name", None),
            "company_website": getattr(self.profile, "website", None),
            "business_info": self.business_research,
            "research_completed": self.research_completed,
            "research_confirmed": self.research_confirmed,
            "research_findings": self.research_data.to_dict() if self.research_data else None,
            "website_research_status": "completed" if self.research_completed else "pending",
            "intelligence_data": self.intelligence_data.to_dict() if self.intelligence_data else None,
            "google_places_data": self.google_places_data,
            "returning_contractor_id": self.returning_contractor_id,
            "persistent_memory_loaded": self.persistent_memory_loaded,
            "available_capabilities": self.available_capabilities,
            "active_tools": self.active_capabilities,
            "tool_results": None,
            "next_action": None,
            "completion_ready": self.completed,
            "contractor_created": bool(self.contractor_id),
            "conversion_successful": self.conversion_successful,
            "error_state": None,
            "original_project_id": self.original_project_id,
            "source_channel": self.source_channel,
            "matching_projects_count": self.matching_projects_count
        }

    def get_stage_progress(self) -> dict[str, Any]:
        """Get current stage and progress information"""
        stages = ["welcome", "experience", "service_area", "differentiators", "completed"]

        # Determine current stage based on mode and completion
        if self.completed:
            current_stage = "completed"
        elif self.current_mode == "research":
            current_stage = "research_confirmation"
        elif self.current_mode == "intelligence":
            current_stage = "intelligence_enhancement"
        else:
            # Default conversation stages
            if not self.profile.primary_trade:
                current_stage = "welcome"
            elif self.profile.years_in_business is None:
                current_stage = "experience"
            elif not self.profile.service_areas:
                current_stage = "service_area"
            elif not self.profile.differentiators:
                current_stage = "differentiators"
            else:
                current_stage = "completed"

        current_index = stages.index(current_stage) if current_stage in stages else 0

        return {
            "current_stage": current_stage,
            "current_mode": self.current_mode,
            "stage_index": current_index,
            "total_stages": len(stages),
            "progress_percentage": (current_index / (len(stages) - 1)) * 100,
            "profile_completeness": self.profile.calculate_completeness(),
            "matching_projects": self.matching_projects_count,
            "research_completed": self.research_completed,
            "intelligence_data_available": bool(self.intelligence_data)
        }


def create_initial_state(session_id: str, interface: str = "chat",
                        contractor_lead_id: Optional[str] = None,
                        original_project_id: Optional[str] = None) -> UnifiedCoIAConversationState:
    """Create initial unified conversation state"""

    # Determine initial mode based on interface
    mode_map = {
        "chat": "conversation",
        "research_portal": "research",
        "intelligence_dashboard": "intelligence"
    }
    initial_mode = mode_map.get(interface, "conversation")

    state = UnifiedCoIAConversationState(
        session_id=session_id,
        contractor_lead_id=contractor_lead_id,
        original_project_id=original_project_id,
        interface=interface,
        current_mode=initial_mode,
        mode_confidence=1.0
    )

    # Set available capabilities based on environment
    capabilities = ["conversation"]  # Always available

    # Check for research capabilities
    try:
        import playwright
        capabilities.append("web_research")
    except ImportError:
        pass

    # Check for Google Places capability
    import os
    if os.getenv("GOOGLE_PLACES_API_KEY"):
        capabilities.append("google_places")

    # Check for persistent memory
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
        capabilities.append("memory")

    state.available_capabilities = capabilities

    return state
