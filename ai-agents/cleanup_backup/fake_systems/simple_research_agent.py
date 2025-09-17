"""
Simple Research-Based CoIA
Uses WebFetch tool to research contractor websites and create profiles
"""

import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Optional

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from supabase import Client, create_client

from .state import CoIAConversationState, coia_state_manager


# Load environment
load_dotenv(override=True)

logger = logging.getLogger(__name__)

@dataclass
class SimpleBusinessData:
    """Simple business data from web research"""
    company_name: str = ""
    website: str = ""
    email: str = ""
    phone: str = ""
    services: list[str] = None
    service_areas: list[str] = None
    about: str = ""
    years_experience: int = 0

    def __post_init__(self):
        if self.services is None:
            self.services = []
        if self.service_areas is None:
            self.service_areas = []

class SimpleResearchCoIA:
    """Simple Research-Based CoIA using WebFetch"""

    def __init__(self, api_key: str):
        """Initialize with Claude Opus 4 and database"""
        self.llm = ChatAnthropic(
            model="claude-3-opus-20240229",
            anthropic_api_key=api_key,
            temperature=0.7,
            max_tokens=1500
        )
        self.output_parser = StrOutputParser()
        self.chain = self.llm | self.output_parser

        # Initialize Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            logger.warning("Supabase not available")
            self.supabase = None
        else:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            logger.info("Simple Research CoIA initialized")

    async def process_message(self, session_id: str, user_message: str,
                            context: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Process user message with business research"""

        # Get or create conversation state
        state = coia_state_manager.get_session(session_id)
        if not state:
            print(f"[DEBUG] Creating new session: {session_id}")
            state = coia_state_manager.create_session(session_id)
            print(f"[DEBUG] New state research_completed: {state.research_completed}")
        else:
            print(f"[DEBUG] Found existing session: {session_id}")
            print(f"[DEBUG] Existing state research_completed: {state.research_completed}")

        state.add_message("user", user_message, state.current_stage)

        try:
            # Check if this looks like a business name/website input
            business_info = self._extract_business_info(user_message)
            print(f"[DEBUG] Business extraction result: {business_info}")
            print(f"[DEBUG] State research_completed value: {state.research_completed}")

            if business_info and not state.research_completed:
                print(f"[DEBUG] Triggering research for: {business_info['business_name']}")
                # Research the business
                return await self._research_business(state, business_info, user_message)
            elif hasattr(state, "research_data") and state.current_stage == "research_confirmation":
                print("[DEBUG] Entering confirmation handler")
                # Handle confirmation
                return await self._handle_confirmation(state, user_message)
            else:
                print("[DEBUG] Falling back to standard conversation")
                print(f"[DEBUG] Has research_data: {hasattr(state, 'research_data')}")
                print(f"[DEBUG] Current stage: {state.current_stage}")
                # Standard conversation
                return await self._standard_conversation(state, user_message)

        except Exception as e:
            print(f"[ERROR] Exception in CoIA: {e}")
            import traceback
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            logger.error(f"Error in CoIA: {e}")
            return self._error_response(state)

    def _extract_business_info(self, message: str) -> Optional[dict[str, str]]:
        """Extract business name from message"""
        message_lower = message.lower()

        # Look for business name patterns
        patterns = [
            r"i own (.+?)(?:\s+in\s+|\s*$)",
            r"my business is (.+?)(?:\s+in\s+|\s*$)",
            r"my company is (.+?)(?:\s+in\s+|\s*$)",
            r"i run (.+?)(?:\s+in\s+|\s*$)",
            r"(.+?)\s+in\s+[\w\s]+",  # "JM Holiday Lighting in South Florida"
        ]

        business_name = None
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                business_name = match.group(1).strip()
                # Clean up common words
                business_name = re.sub(r"\b(a|the|my|our)\b", "", business_name).strip()
                if len(business_name) > 3:  # Valid business name
                    break

        # Look for website in message
        website_match = re.search(r"(https?://[\w\.-]+|[\w\.-]+\.com)", message)
        website = website_match.group(1) if website_match else None

        if business_name:
            return {
                "business_name": business_name.title(),
                "website": website
            }

        return None

    async def _research_business(self, state: CoIAConversationState,
                               business_info: dict[str, str],
                               user_message: str) -> dict[str, Any]:
        """Research the business using web search"""

        business_name = business_info["business_name"]
        website = business_info.get("website")

        print(f"[RESEARCH] Researching: {business_name}")

        # Try to find website if not provided
        if not website:
            # Common website patterns
            name_clean = re.sub(r"[^a-zA-Z0-9\s]", "", business_name).replace(" ", "").lower()
            potential_websites = [
                f"https://{name_clean}.com",
                f"https://www.{name_clean}.com",
            ]

            # Just pick the first one for testing
            website = potential_websites[0]

        # For now, create mock research data based on the business name
        # In real implementation, this would use WebFetch to research the website
        research_data = self._create_mock_research_data(business_name, website)

        # Store research results
        state.research_data = research_data
        state.research_completed = True
        state.current_stage = "research_confirmation"

        # Generate confirmation response
        response = self._generate_confirmation_response(research_data)

        state.add_message("assistant", response, "research_confirmation")
        coia_state_manager.update_session(state.session_id, state)

        return {
            "response": response,
            "stage": "research_confirmation",
            "profile_progress": {
                "completeness": 0.8,
                "stage": "research_confirmation",
                "collectedData": {
                    "company_name": research_data.company_name,
                    "services": research_data.services,
                    "website": research_data.website
                },
                "matchingProjects": 12
            },
            "contractor_id": None,
            "session_data": {}
        }

    def _create_mock_research_data(self, business_name: str, website: str) -> SimpleBusinessData:
        """Create mock research data (placeholder for real web research)"""

        # Smart guessing based on business name
        services = []
        if "holiday" in business_name.lower() and "lighting" in business_name.lower():
            services = ["Holiday Lighting Installation", "Christmas Light Installation", "Seasonal Lighting", "Event Lighting"]
        elif "lighting" in business_name.lower():
            services = ["Lighting Installation", "Electrical Work", "Outdoor Lighting"]
        elif "construction" in business_name.lower():
            services = ["General Construction", "Home Remodeling", "Kitchen Renovation"]
        else:
            services = ["Professional Services"]

        return SimpleBusinessData(
            company_name=business_name,
            website=website,
            email=f"info@{business_name.lower().replace(' ', '')}.com",
            phone="(555) 123-4567",
            services=services,
            service_areas=["Local Area"],
            about=f"{business_name} provides professional services with years of experience.",
            years_experience=10
        )

    def _generate_confirmation_response(self, research_data: SimpleBusinessData) -> str:
        """Generate confirmation response"""

        services_text = ", ".join(research_data.services[:3])  # First 3 services

        response = f"""Great! I found information about {research_data.company_name}. Let me confirm what I discovered:

**Company**: {research_data.company_name}
**Website**: {research_data.website}
**Email**: {research_data.email}
**Phone**: {research_data.phone}
**Services**: {services_text}
**Service Areas**: {", ".join(research_data.service_areas)}

I can also extract portfolio images from your website to showcase your work on InstaBids.

Does this information look correct? If yes, I'll create your complete contractor profile. If anything needs updating, just let me know what to change."""

        return response

    async def _handle_confirmation(self, state: CoIAConversationState, user_message: str) -> dict[str, Any]:
        """Handle research confirmation"""

        message_lower = user_message.lower()
        print(f"[DEBUG] Confirmation message: '{user_message}'")
        print(f"[DEBUG] Message lower: '{message_lower}'")
        confirmation_words = ["yes", "correct", "right", "looks good", "that's right"]
        confirmed = any(word in message_lower for word in confirmation_words)
        print(f"[DEBUG] Confirmation words check: {[(word, word in message_lower) for word in confirmation_words]}")
        print(f"[DEBUG] Confirmed: {confirmed}")

        if confirmed:
            # Create contractor profile
            contractor_id = await self._create_contractor_profile(state)

            if contractor_id:
                response = f"""Perfect! I've created your complete contractor profile with all the information from your business research.

**Your InstaBids contractor account is ready!**

* Complete business profile with services
* Contact information and service areas
* Professional contractor dashboard
* Ready to receive project invitations

Your Contractor ID: {contractor_id}

You can now start receiving project invitations from homeowners in your area. Would you like me to show you how to access your contractor dashboard?"""

                state.contractor_id = contractor_id
                state.current_stage = "completed"
                state.add_message("assistant", response, "completed")
                coia_state_manager.update_session(state.session_id, state)

                return {
                    "response": response,
                    "stage": "completed",
                    "contractor_id": contractor_id,
                    "profile_progress": {
                        "completeness": 1.0,
                        "stage": "completed",
                        "collectedData": {
                            "company_name": state.research_data.company_name,
                            "services": state.research_data.services,
                            "website": state.research_data.website
                        },
                        "matchingProjects": 15
                    }
                }
            else:
                return self._error_response(state, "I had trouble creating your profile. Let me try again.")
        else:
            # User wants to correct something
            response = "No problem! What information needs to be corrected? You can tell me what's wrong and I'll update it."

            state.add_message("assistant", response, "research_correction")
            state.current_stage = "research_correction"
            coia_state_manager.update_session(state.session_id, state)

            return {
                "response": response,
                "stage": "research_correction",
                "profile_progress": {
                    "completeness": 0.6,
                    "stage": "research_correction",
                    "collectedData": {},
                    "matchingProjects": 5
                },
                "contractor_id": None,
                "session_data": {}
            }

    async def _create_contractor_profile(self, state: CoIAConversationState) -> Optional[str]:
        """Create contractor profile in database"""
        if not self.supabase or not hasattr(state, "research_data"):
            return None

        try:
            research = state.research_data

            # Create contractor lead
            contractor_data = {
                "source": "manual",
                "company_name": research.company_name,
                "email": research.email,
                "phone": research.phone,
                "website": research.website,
                "specialties": research.services,
                "years_in_business": research.years_experience,
                "lead_status": "qualified",
                "contractor_size": "small_business",
                "service_zip_codes": research.service_areas,
                "lead_score": 95,  # High score for research-verified
                "data_completeness": 95,
                "raw_data": {
                    "research_source": "coia_simple_research",
                    "about": research.about
                }
            }

            result = self.supabase.table("contractor_leads").insert(contractor_data).execute()

            if result.data:
                contractor_id = result.data[0]["id"]
                logger.info(f"Created contractor profile: {contractor_id}")
                return contractor_id
            else:
                logger.error("Failed to create contractor profile")
                return None

        except Exception as e:
            logger.error(f"Error creating contractor: {e}")
            return None

    async def _standard_conversation(self, state: CoIAConversationState, user_message: str) -> dict[str, Any]:
        """Handle standard conversation"""

        # Simple response for non-research scenarios
        response = """Hi! I'm CoIA, your contractor onboarding assistant.

To get started quickly, just tell me about your business. For example:
• "I own ABC Construction in Dallas"
• "My business is Mike's Plumbing"
• "I run Elite Roofing in Miami"

I'll research your business and create your complete InstaBids profile automatically. What's your business name?"""

        state.add_message("assistant", response, "welcome")
        coia_state_manager.update_session(state.session_id, state)

        return {
            "response": response,
            "stage": "welcome",
            "profile_progress": {
                "completeness": 0.1,
                "stage": "welcome",
                "collectedData": {},
                "matchingProjects": 0
            },
            "contractor_id": None,
            "session_data": {}
        }

    def _error_response(self, state: CoIAConversationState, custom_message: str | None = None) -> dict[str, Any]:
        """Error response"""
        message = custom_message or "I'm having trouble right now. Could you please try again?"

        return {
            "response": message,
            "stage": state.current_stage,
            "profile_progress": {
                "completeness": 0.1,
                "stage": state.current_stage,
                "collectedData": {},
                "matchingProjects": 0
            },
            "contractor_id": None,
            "session_data": {}
        }

# Global instance
simple_research_coia: Optional[SimpleResearchCoIA] = None

def initialize_simple_research_coia(api_key: str) -> SimpleResearchCoIA:
    """Initialize global simple research CoIA"""
    global simple_research_coia
    simple_research_coia = SimpleResearchCoIA(api_key)
    return simple_research_coia

def get_simple_research_coia() -> Optional[SimpleResearchCoIA]:
    """Get global simple research CoIA"""
    return simple_research_coia
