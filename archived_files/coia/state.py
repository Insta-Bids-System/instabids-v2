"""
CoIA (Contractor Interface Agent) State Management
Purpose: Track conversation state and profile building progress
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class ContractorProfile:
    """Contractor profile data collected through conversation"""
    primary_trade: Optional[str] = None
    years_in_business: Optional[int] = None
    business_name: Optional[str] = None
    company_name: Optional[str] = None  # From AI research
    email: Optional[str] = None  # From AI research
    phone: Optional[str] = None  # From AI research
    website: Optional[str] = None  # From AI research
    service_areas: list[str] = field(default_factory=list)
    service_radius_miles: Optional[int] = None
    specializations: list[str] = field(default_factory=list)
    differentiators: Optional[str] = None
    license_info: Optional[str] = None
    insurance_verified: bool = False
    team_size: Optional[str] = None
    minimum_project_size: Optional[int] = None
    preferred_project_types: list[str] = field(default_factory=list)
    availability: Optional[str] = None
    response_time: Optional[str] = None
    warranty_offered: bool = False
    certifications: list[str] = field(default_factory=list)

    def calculate_completeness(self) -> float:
        """Calculate profile completeness percentage"""
        required_fields = [
            self.primary_trade,
            self.years_in_business,
            len(self.service_areas) > 0,
            self.differentiators
        ]

        optional_fields = [
            self.business_name,
            self.service_radius_miles,
            len(self.specializations) > 0,
            self.license_info,
            self.team_size,
            len(self.certifications) > 0
        ]

        required_complete = sum(1 for field in required_fields if field)
        optional_complete = sum(1 for field in optional_fields if field)

        # Required fields worth 80%, optional worth 20%
        completeness = (required_complete / len(required_fields)) * 0.8 + \
                      (optional_complete / len(optional_fields)) * 0.2

        return min(completeness, 1.0)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "primary_trade": self.primary_trade,
            "years_in_business": self.years_in_business,
            "business_name": self.business_name,
            "company_name": self.company_name,
            "email": self.email,
            "phone": self.phone,
            "website": self.website,
            "service_areas": self.service_areas,
            "service_radius_miles": self.service_radius_miles,
            "specializations": self.specializations,
            "differentiators": self.differentiators,
            "license_info": self.license_info,
            "insurance_verified": self.insurance_verified,
            "team_size": self.team_size,
            "minimum_project_size": self.minimum_project_size,
            "preferred_project_types": self.preferred_project_types,
            "availability": self.availability,
            "response_time": self.response_time,
            "warranty_offered": self.warranty_offered,
            "certifications": self.certifications,
            "completeness": self.calculate_completeness()
        }

@dataclass
class ConversationMessage:
    """Individual message in the conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    stage: Optional[str] = None
    profile_updates: Optional[dict[str, Any]] = None

@dataclass
class CoIAConversationState:
    """Complete conversation state for a contractor onboarding session"""
    session_id: str
    contractor_lead_id: Optional[str] = None
    contractor_id: Optional[str] = None
    user_id: Optional[str] = None  # Auth user ID for FK constraints

    # Conversation tracking
    current_stage: str = "welcome"
    messages: list[ConversationMessage] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)

    # Profile building
    profile: ContractorProfile = field(default_factory=ContractorProfile)

    # Research tracking (NEW)
    business_research: Optional[dict[str, str]] = None  # Business name, website
    research_completed: bool = False
    research_confirmed: bool = False
    research_data: Optional[Any] = None  # EnrichedContractorData

    # Context
    original_project_id: Optional[str] = None
    source_channel: Optional[str] = None
    matching_projects_count: int = 0

    # Completion tracking
    completed: bool = False
    completed_at: Optional[datetime] = None
    conversion_successful: bool = False

    # Auth credentials (for providing login info)
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
            self.current_stage = stage

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

    def get_conversation_history(self, limit: Optional[int] = None) -> list[dict[str, Any]]:
        """Get conversation history in API format"""
        messages = self.messages[-limit:] if limit else self.messages
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "stage": msg.stage
            }
            for msg in messages
        ]

    def mark_completed(self, contractor_id: str):
        """Mark conversation as completed"""
        self.completed = True
        self.completed_at = datetime.now()
        self.contractor_id = contractor_id
        self.conversion_successful = True
        self.current_stage = "completed"

    def get_stage_progress(self) -> dict[str, Any]:
        """Get current stage and progress information"""
        stages = ["welcome", "experience", "service_area", "differentiators", "completed"]
        current_index = stages.index(self.current_stage) if self.current_stage in stages else 0

        return {
            "current_stage": self.current_stage,
            "stage_index": current_index,
            "total_stages": len(stages),
            "progress_percentage": (current_index / (len(stages) - 1)) * 100,
            "profile_completeness": self.profile.calculate_completeness(),
            "matching_projects": self.matching_projects_count
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "session_id": self.session_id,
            "contractor_lead_id": self.contractor_lead_id,
            "contractor_id": self.contractor_id,
            "current_stage": self.current_stage,
            "profile": self.profile.to_dict(),
            "stage_progress": self.get_stage_progress(),
            "completed": self.completed,
            "conversion_successful": self.conversion_successful,
            "last_updated": self.last_updated.isoformat(),
            "message_count": len(self.messages)
        }

class CoIAStateManager:
    """Manages CoIA conversation states"""

    def __init__(self):
        self._states: dict[str, CoIAConversationState] = {}

    def create_session(self, session_id: str, contractor_lead_id: Optional[str] = None,
                      original_project_id: Optional[str] = None) -> CoIAConversationState:
        """Create a new conversation session"""
        state = CoIAConversationState(
            session_id=session_id,
            contractor_lead_id=contractor_lead_id,
            original_project_id=original_project_id
        )
        self._states[session_id] = state
        return state

    def get_session(self, session_id: str) -> Optional[CoIAConversationState]:
        """Get existing conversation session"""
        return self._states.get(session_id)

    def update_session(self, session_id: str, state: CoIAConversationState):
        """Update conversation session"""
        self._states[session_id] = state

    def delete_session(self, session_id: str):
        """Delete conversation session"""
        if session_id in self._states:
            del self._states[session_id]

    def get_active_sessions(self) -> list[str]:
        """Get list of active session IDs"""
        return list(self._states.keys())

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old sessions"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        old_sessions = [
            session_id for session_id, state in self._states.items()
            if state.last_updated < cutoff_time
        ]

        for session_id in old_sessions:
            del self._states[session_id]

        return len(old_sessions)

# Global state manager instance
coia_state_manager = CoIAStateManager()
