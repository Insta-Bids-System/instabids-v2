"""
Unified COIA State Schema for LangGraph - FIXED VERSION
All fields properly annotated to handle concurrent updates
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated, Any, Literal, Optional, TypedDict

from langgraph.graph.message import AnyMessage, add_messages

from .state import ContractorProfile, ConversationMessage


# Helper reducers for concurrent updates
def last_write_wins(x, y):
    """Always take the latest value"""
    return y

def merge_dicts(x, y):
    """Merge two dictionaries, with y values overwriting x"""
    if not x:
        return y
    if not y:
        return x
    return {**x, **y}

def max_value(x, y):
    """Take the maximum value"""
    if x is None:
        return y
    if y is None:
        return x
    return max(x, y)

def logical_or(x, y):
    """Logical OR for booleans"""
    return x or y

def append_lists(x, y):
    """Append lists together"""
    if not x:
        return y
    if not y:
        return x
    return x + y

# New reducers: append + unique + cap (to prevent unbounded growth and dupes)
def _append_unique_capped(x, y, cap: int):
    base = (x or []) + (y or [])
    # stable unique (preserve order)
    seen = set()
    unique = []
    for item in base:
        key = repr(item)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    # cap length
    if len(unique) > cap:
        unique = unique[-cap:]
    return unique

def append_unique_capped_50(x, y):
    return _append_unique_capped(x, y, 50)

def append_unique_capped_100(x, y):
    return _append_unique_capped(x, y, 100)

def append_unique_capped_200(x, y):
    return _append_unique_capped(x, y, 200)


class UnifiedCoIAState(TypedDict):
    """
    Unified state schema for multi-mode COIA agent
    All fields properly annotated for concurrent updates
    """

    # Core conversation tracking
    messages: Annotated[list[AnyMessage], add_messages]
    session_id: str
    user_id: Optional[str]
    contractor_lead_id: Optional[str]
    contractor_id: Optional[str]
    
    # Bid card link tracking
    verification_token: Annotated[Optional[str], last_write_wins]
    source_channel: Annotated[Optional[str], last_write_wins]

    # Interface and mode management - ALL ANNOTATED
    interface: Annotated[Optional[str], last_write_wins]
    current_mode: Annotated[Literal["conversation", "research", "intelligence", "bid_card_search"], last_write_wins]
    previous_mode: Annotated[Optional[str], last_write_wins]
    mode_confidence: Annotated[float, last_write_wins]
    transition_reason: Annotated[Optional[str], last_write_wins]
    last_updated: Annotated[str, last_write_wins]

    # Contractor profile data - PROPERLY MERGED
    contractor_profile: Annotated[dict[str, Any], merge_dicts]
    profile_completeness: Annotated[float, max_value]

    # Business information detection - ANNOTATED
    company_name: Annotated[Optional[str], last_write_wins]
    company_website: Annotated[Optional[str], last_write_wins]
    business_info: Annotated[Optional[dict[str, str]], merge_dicts]

    # Research mode data - ANNOTATED
    research_completed: Annotated[bool, logical_or]
    research_confirmed: Annotated[bool, logical_or]
    research_findings: Annotated[Optional[dict[str, Any]], merge_dicts]
    website_research_status: Annotated[Optional[str], last_write_wins]

    # Intelligence mode data - ANNOTATED
    intelligence_data: Annotated[Optional[dict[str, Any]], merge_dicts]
    google_places_data: Annotated[Optional[dict[str, Any]], merge_dicts]
    returning_contractor_id: Annotated[Optional[str], last_write_wins]
    persistent_memory_loaded: Annotated[bool, logical_or]

    # Tool management and capabilities - ANNOTATED
    available_capabilities: Annotated[list[str], append_unique_capped_50]
    active_tools: Annotated[list[str], append_unique_capped_50]
    tool_results: Annotated[Optional[dict[str, Any]], merge_dicts]

    # Control flow and completion - ANNOTATED
    next_action: Annotated[Optional[str], last_write_wins]
    completion_ready: Annotated[bool, logical_or]
    contractor_created: Annotated[bool, logical_or]
    conversion_successful: Annotated[bool, logical_or]
    error_state: Annotated[Optional[str], last_write_wins]
    mode_detector_visits: Annotated[int, max_value]  # Track visits to prevent loops

    # Context from original project - ANNOTATED
    original_project_id: Annotated[Optional[str], last_write_wins]
    source_channel: Annotated[Optional[str], last_write_wins]
    matching_projects_count: Annotated[int, max_value]

    # Bid card search fields - ANNOTATED
    bid_cards_attached: Annotated[list[dict[str, Any]], append_unique_capped_50]
    marketplace_links: Annotated[list[str], append_unique_capped_200]
    bid_search_criteria: Annotated[Optional[dict[str, Any]], merge_dicts]
    last_bid_search: Annotated[Optional[str], last_write_wins]


@dataclass
class UnifiedCoIAConversationState:
    """
    Extended conversation state that includes all mode capabilities
    This is the dataclass version for easier manipulation
    """

    # Core identification
    session_id: str
    user_id: Optional[str] = None
    contractor_lead_id: Optional[str] = None
    contractor_id: Optional[str] = None

    # Conversation history
    messages: list[ConversationMessage] = field(default_factory=list)

    # Mode management
    interface: Optional[str] = None
    current_mode: Literal["conversation", "research", "intelligence", "bid_card_search"] = "conversation"
    previous_mode: Optional[str] = None
    mode_confidence: float = 0.0
    transition_reason: Optional[str] = None
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Profile data
    contractor_profile: ContractorProfile = field(default_factory=ContractorProfile)
    profile_completeness: float = 0.0

    # Business information
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    business_info: Optional[dict[str, str]] = None

    # Research data
    research_completed: bool = False
    research_confirmed: bool = False
    research_findings: Optional[dict[str, Any]] = None
    website_research_status: Optional[str] = None

    # Intelligence data
    intelligence_data: Optional[dict[str, Any]] = None
    google_places_data: Optional[dict[str, Any]] = None
    returning_contractor_id: Optional[str] = None
    persistent_memory_loaded: bool = False

    # Tool management
    available_capabilities: list[str] = field(default_factory=lambda: ["web_research", "google_places", "memory"])
    active_tools: list[str] = field(default_factory=list)
    tool_results: Optional[dict[str, Any]] = None

    # Control flow
    next_action: Optional[str] = None
    completion_ready: bool = False
    contractor_created: bool = False
    conversion_successful: bool = False
    error_state: Optional[str] = None

    # Context
    original_project_id: Optional[str] = None
    source_channel: Optional[str] = None
    matching_projects_count: int = 0

    # Bid card search fields
    bid_cards_attached: list[dict[str, Any]] = field(default_factory=list)
    marketplace_links: list[str] = field(default_factory=list)
    bid_search_criteria: Optional[dict[str, Any]] = None
    last_bid_search: Optional[str] = None

    def to_langgraph_state(self) -> UnifiedCoIAState:
        """Convert to LangGraph TypedDict format"""
        from langchain_core.messages import AIMessage, HumanMessage

        # Convert messages to LangChain format
        lc_messages = []
        for msg in self.messages:
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            else:
                lc_messages.append(AIMessage(content=msg.content))

        return UnifiedCoIAState(
            messages=lc_messages,
            session_id=self.session_id,
            user_id=self.user_id,
            contractor_lead_id=self.contractor_lead_id,
            contractor_id=self.contractor_id,
            interface=self.interface,
            current_mode=self.current_mode,
            previous_mode=self.previous_mode,
            mode_confidence=self.mode_confidence,
            transition_reason=self.transition_reason,
            last_updated=self.last_updated,
            contractor_profile=self.contractor_profile.to_dict() if self.contractor_profile and hasattr(self.contractor_profile, 'to_dict') else (self.contractor_profile.__dict__ if self.contractor_profile else None),
            profile_completeness=self.profile_completeness,
            company_name=self.company_name,
            company_website=self.company_website,
            business_info=self.business_info,
            research_completed=self.research_completed,
            research_confirmed=self.research_confirmed,
            research_findings=self.research_findings,
            website_research_status=self.website_research_status,
            intelligence_data=self.intelligence_data,
            google_places_data=self.google_places_data,
            returning_contractor_id=self.returning_contractor_id,
            persistent_memory_loaded=self.persistent_memory_loaded,
            available_capabilities=self.available_capabilities,
            active_tools=self.active_tools,
            tool_results=self.tool_results,
            next_action=self.next_action,
            completion_ready=self.completion_ready,
            contractor_created=self.contractor_created,
            conversion_successful=self.conversion_successful,
            error_state=self.error_state,
            original_project_id=self.original_project_id,
            source_channel=self.source_channel,
            matching_projects_count=self.matching_projects_count,
            bid_cards_attached=self.bid_cards_attached,
            marketplace_links=self.marketplace_links,
            bid_search_criteria=self.bid_search_criteria,
            last_bid_search=self.last_bid_search
        )

    @classmethod
    def from_langgraph_state(cls, state: UnifiedCoIAState) -> "UnifiedCoIAConversationState":
        """Create from LangGraph state"""
        # Convert messages
        conv_messages = []
        for msg in state.get("messages", []):
            if hasattr(msg, "content"):
                role = "user" if msg.__class__.__name__ == "HumanMessage" else "assistant"
                conv_messages.append(ConversationMessage(
                    role=role,
                    content=msg.content,
                    timestamp=datetime.utcnow().isoformat()
                ))

        # Create profile from dict
        profile_dict = state.get("contractor_profile", {})
        profile = ContractorProfile(**profile_dict) if profile_dict else ContractorProfile()

        return cls(
            session_id=state.get("session_id", ""),
            user_id=state.get("user_id"),
            contractor_lead_id=state.get("contractor_lead_id"),
            contractor_id=state.get("contractor_id"),
            messages=conv_messages,
            interface=state.get("interface"),
            current_mode=state.get("current_mode", "conversation"),
            previous_mode=state.get("previous_mode"),
            mode_confidence=state.get("mode_confidence", 0.0),
            transition_reason=state.get("transition_reason"),
            last_updated=state.get("last_updated", datetime.utcnow().isoformat()),
            contractor_profile=profile,
            profile_completeness=state.get("profile_completeness", 0.0),
            company_name=state.get("company_name"),
            company_website=state.get("company_website"),
            business_info=state.get("business_info"),
            research_completed=state.get("research_completed", False),
            research_confirmed=state.get("research_confirmed", False),
            research_findings=state.get("research_findings"),
            website_research_status=state.get("website_research_status"),
            intelligence_data=state.get("intelligence_data"),
            google_places_data=state.get("google_places_data"),
            returning_contractor_id=state.get("returning_contractor_id"),
            persistent_memory_loaded=state.get("persistent_memory_loaded", False),
            available_capabilities=state.get("available_capabilities", ["web_research", "google_places", "memory"]),
            active_tools=state.get("active_tools", []),
            tool_results=state.get("tool_results"),
            next_action=state.get("next_action"),
            completion_ready=state.get("completion_ready", False),
            contractor_created=state.get("contractor_created", False),
            conversion_successful=state.get("conversion_successful", False),
            error_state=state.get("error_state"),
            original_project_id=state.get("original_project_id"),
            source_channel=state.get("source_channel"),
            matching_projects_count=state.get("matching_projects_count", 0),
            bid_cards_attached=state.get("bid_cards_attached", []),
            marketplace_links=state.get("marketplace_links", []),
            bid_search_criteria=state.get("bid_search_criteria"),
            last_bid_search=state.get("last_bid_search")
        )


def create_initial_state(
    session_id: str,
    interface: str = "chat",
    contractor_lead_id: Optional[str] = None,
    original_project_id: Optional[str] = None
) -> UnifiedCoIAConversationState:
    """Create a new initial state for COIA"""
    return UnifiedCoIAConversationState(
        session_id=session_id,
        interface=interface,
        contractor_lead_id=contractor_lead_id,
        original_project_id=original_project_id,
        current_mode="conversation",
        available_capabilities=["web_research", "google_places", "memory"]
    )
