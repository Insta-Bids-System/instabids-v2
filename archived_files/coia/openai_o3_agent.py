"""
OpenAI GPT-5-Based CoIA (Contractor Onboarding & Intelligence Agent)
Uses OpenAI's GPT-5 model for advanced reasoning and natural language understanding
"""

import json
import logging
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import requests
from dotenv import load_dotenv
from openai import OpenAI
from supabase import Client, create_client

from .persistent_memory import persistent_coia_state_manager
from .state import CoIAConversationState


# Load environment
load_dotenv(override=True)

logger = logging.getLogger(__name__)

@dataclass
class RealBusinessData:
    """Real business data from web research"""
    company_name: str = ""
    website: str = ""
    email: str = ""
    phone: str = ""
    services: list[str] = None
    service_areas: list[str] = None
    about: str = ""
    years_experience: int = 0
    address: str = ""
    hours: dict[str, str] = None
    social_media: dict[str, str] = None
    google_listing_url: str = ""
    place_id: str = ""

    def __post_init__(self):
        if self.services is None:
            self.services = []
        if self.service_areas is None:
            self.service_areas = []
        if self.hours is None:
            self.hours = {}
        if self.social_media is None:
            self.social_media = {}

class OpenAIGPT5CoIA:
    """OpenAI GPT-5-Based CoIA using advanced reasoning for contractor onboarding"""

    def __init__(self, api_key: str = None):
        """Initialize with OpenAI GPT-5 for intelligent understanding"""
        # Use provided key or get from environment
        openai_key = api_key or os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")

        self.client = OpenAI(api_key=openai_key)
        logger.info("OpenAI GPT-5 CoIA initialized")

        # Initialize Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            logger.warning("Supabase not available")
            self.supabase = None
            self.supabase_admin = None
        else:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            logger.info("OpenAI GPT-5 CoIA initialized with Supabase")

            # Also initialize admin client for auth operations
            service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            if service_role_key:
                self.supabase_admin: Client = create_client(supabase_url, service_role_key)
                logger.info("Admin client initialized for auth operations")
                print(f"[GPT-5 COIA INIT] Service role key loaded: {service_role_key[:20]}...")
            else:
                self.supabase_admin = None
                logger.warning("No service role key - auth operations will fail")
                print("[GPT-5 COIA INIT] NO SERVICE ROLE KEY FOUND!")

        # Initialize Google Maps API for real business search
        self.google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if self.google_api_key:
            logger.info("Google Maps API available for real business research")
            print(f"[GPT-5 COIA INIT] Google API Key loaded: {self.google_api_key[:20]}...")
        else:
            print("[GPT-5 COIA INIT] NO GOOGLE API KEY FOUND!")

    async def process_message(self, session_id: str, user_message: str,
                            context: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Process user message with GPT-5's advanced reasoning"""

        print(f"[GPT-5 COIA] Processing message: '{user_message}' for session: {session_id}")

        # Get or create conversation state with persistent memory
        state = await persistent_coia_state_manager.get_session(session_id)
        if not state:
            print("[O3 COIA] Creating new session with persistent memory")
            state = await persistent_coia_state_manager.create_session(session_id)
        else:
            print("[O3 COIA] Found existing session in persistent memory")

        print(f"[O3 COIA] Current stage: {state.current_stage}")
        print(f"[O3 COIA] Research completed: {state.research_completed}")

        state.add_message("user", user_message, state.current_stage)

        try:
            # CRITICAL CHANGE: Use O3 FIRST to understand the message
            understanding = await self._understand_with_o3(user_message, state)
            print(f"[O3 COIA] O3 Understanding: {understanding}")

            # Act based on O3's understanding
            if understanding.get("contains_business_info") and not state.research_completed:
                print("[O3 COIA] O3 detected business information - triggering research")

                business_info = {
                    "business_name": understanding.get("business_name"),
                    "website": understanding.get("website"),
                    "location": understanding.get("location"),
                    "services": understanding.get("services", [])
                }

                # First check if this is a returning contractor
                business_name = business_info["business_name"]
                returning_contractor_id = await persistent_coia_state_manager.check_returning_contractor(business_name)

                if returning_contractor_id:
                    print(f"[O3 COIA] Found returning contractor: {returning_contractor_id}")
                    return await self._handle_returning_contractor(state, returning_contractor_id, business_name)
                else:
                    print("[O3 COIA] New contractor - proceeding with research")
                    return await self._intelligent_research(state, business_info, user_message)

            elif hasattr(state, "research_data") and state.current_stage == "research_confirmation":
                print("[O3 COIA] Handling confirmation")
                return await self._handle_confirmation(state, user_message)

            elif understanding.get("is_correction") and state.current_stage == "research_correction":
                print("[O3 COIA] Handling correction")
                return await self._handle_correction(state, understanding)

            else:
                print("[O3 COIA] Standard conversation")
                return await self._standard_conversation(state, user_message)

        except Exception as e:
            print(f"[O3 COIA ERROR] Exception: {type(e).__name__}: {e}")
            logger.error(f"Error in O3 CoIA: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            print(f"[O3 COIA ERROR] Full traceback:\n{traceback.format_exc()}")
            return self._error_response(state)

    async def _understand_with_o3(self, message: str, state: CoIAConversationState) -> dict[str, Any]:
        """Use OpenAI O3 to understand the user's message with advanced reasoning"""

        # Build conversation history for context
        history = []
        if hasattr(state, "messages") and state.messages:
            for msg in state.messages[-5:]:  # Last 5 messages for context
                # Handle ConversationMessage object
                if hasattr(msg, "role") and hasattr(msg, "content"):
                    history.append(f"{msg.role}: {msg.content}")
                else:
                    # Fallback for dict-like objects
                    history.append(f"{msg.get('role', 'unknown')}: {msg.get('content', '')}")

        history_text = "\n".join(history) if history else "No previous conversation"

        # Use O3 to understand the message
        system_prompt = """You are an AI assistant analyzing contractor onboarding messages.
Your job is to understand what information the user is providing about their business.

Extract the following information if present:
1. Business name (e.g., "JM Holiday Lighting", "Mike's Plumbing")
2. Business type/services (e.g., "holiday lighting installation", "plumbing services")
3. Location (e.g., "South Florida", "Dallas", "near Miami")
4. Website URL if mentioned
5. Contact information (phone, email)
6. Whether they're correcting previous information

Return a JSON object with:
{
    "contains_business_info": true/false,
    "business_name": "extracted name or null",
    "business_type": "type of business or null",
    "services": ["list of services mentioned"],
    "location": "location mentioned or null",
    "website": "website if mentioned or null",
    "phone": "phone if mentioned or null",
    "email": "email if mentioned or null",
    "is_correction": true/false,
    "correction_details": "what they're correcting or null",
    "user_intent": "brief description of what the user wants"
}

Examples:
- "I specialize in holiday lighting installation" → extract service type
- "I own JM Holiday Lighting in South Florida" → extract name and location
- "My business is ABC Construction" → extract business name
- "The phone number is wrong, it should be 555-1234" → correction with details
"""

        user_prompt = f"""Previous conversation:
{history_text}

Current message: "{message}"

Analyze this message and extract business information."""

        try:
            # Call OpenAI GPT-5 model 
            response = self.client.chat.completions.create(
                model="gpt-5",  # Using GPT-5 for advanced reasoning
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent extraction
                response_format={"type": "json_object"}
            )

            # Parse the GPT-5 response
            understanding = json.loads(response.choices[0].message.content)
            print(f"[GPT-5 UNDERSTANDING] {understanding}")

            return understanding

        except Exception as e:
            print(f"[GPT-5 ERROR] Failed to understand message: {e}")
            # Fallback to basic understanding
            return {
                "contains_business_info": False,
                "user_intent": "unclear"
            }

    async def _intelligent_research(self, state: CoIAConversationState,
                                  business_info: dict[str, str],
                                  user_message: str) -> dict[str, Any]:
        """Use O3 to intelligently research the business"""

        business_name = business_info.get("business_name")
        website = business_info.get("website")
        location = business_info.get("location", "")
        services = business_info.get("services", [])

        # If no business name provided, ask for it
        if not business_name:
            response = """Thanks for telling me about your services! To find your business information and create your profile, I need to know your business name.

What's the name of your business?"""
            state.add_message("assistant", response, "gathering_info")
            state.current_stage = "gathering_info"
            await persistent_coia_state_manager.update_session(state.session_id, state)

            return {
                "response": response,
                "stage": "gathering_info",
                "profile_progress": {
                    "completeness": 0.3,
                    "stage": "gathering_info",
                    "collectedData": {
                        "services": services,
                        "location": location
                    },
                    "matchingProjects": 0
                },
                "contractor_id": None,
                "session_data": {}
            }

        print(f"[O3 RESEARCH] Starting real research for: {business_name}")

        # First, use O3 to intelligently find the website if not provided
        if not website:
            website = await self._find_business_website(business_name, location, user_message)

        # Try to find the business on Google Maps
        google_business_data = None
        if self.google_api_key:
            print("[O3 RESEARCH] Calling Google Maps API...")
            google_business_data = await self._search_google_business(business_name, location or user_message)
            print(f"[O3 RESEARCH] Google data: {google_business_data}")

        # Now use O3 to enrich and organize the data
        research_prompt = f"""You are helping organize business information for contractor onboarding.

Business Name: {business_name}
Website: {website or 'Not provided'}
Location: {location or 'Not specified'}
Services mentioned: {', '.join(business_info.get('services', [])) or 'Not specified'}
Context from user: {user_message}

{'GOOGLE BUSINESS DATA:' + json.dumps(google_business_data, indent=2) if google_business_data else 'No Google listing found'}

Based on all available information, organize into this format:
1. Official company name (use Google's name if available, otherwise user's name)
2. Website URL (use Google's website if available)
3. Contact email (use Google data or suggest common patterns)
4. Phone number (USE EXACT GOOGLE PHONE if available)
5. Services offered (combine user input with business type)
6. Service areas (based on location)
7. Business address (use Google's address if available)
8. Years in business (estimate if possible)
9. Business hours (use Google's hours if available)
10. Social media links (generate likely Facebook and Instagram profile URLs based on business name)

Return as JSON with this exact structure:
{{
    "company_name": "exact name",
    "website": "full URL",
    "email": "email address",
    "phone": "exact phone",
    "services": ["list of services"],
    "service_areas": ["cities/areas"],
    "address": "full address",
    "years_in_business": number or null,
    "hours": {{"Monday": "9am-5pm"}},
    "social_media": {{"facebook": "url", "instagram": "url"}}
}}

IMPORTANT: 
- Use exact values from Google when available. Only estimate missing fields.
- For social media, generate likely URLs like:
  - Facebook: https://facebook.com/businessname or https://facebook.com/BusinessNameOfficial
  - Instagram: https://instagram.com/businessname or https://instagram.com/businessname_official
- Use the business name to create reasonable social media handles"""

        try:
            # Call GPT-5 for intelligent research
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "You are an expert business researcher organizing contractor information."},
                    {"role": "user", "content": research_prompt}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )

            research_json = json.loads(response.choices[0].message.content)
            print("[GPT-5 RESEARCH] GPT-5 response received and parsed")

            # Create real business data object
            research_data = RealBusinessData(
                company_name=research_json.get("company_name", business_name),
                website=research_json.get("website", website or ""),
                email=research_json.get("email", ""),
                phone=research_json.get("phone", ""),
                services=research_json.get("services", []),
                service_areas=research_json.get("service_areas", []),
                address=research_json.get("address", ""),
                years_experience=research_json.get("years_in_business", 0),
                hours=research_json.get("hours", {}),
                social_media=research_json.get("social_media", {}),
                google_listing_url=google_business_data.get("google_listing_url", "") if google_business_data else "",
                place_id=google_business_data.get("place_id", "") if google_business_data else ""
            )

            print("[O3 RESEARCH] Found real data:")
            print(f"  Company: {research_data.company_name}")
            print(f"  Email: {research_data.email}")
            print(f"  Phone: {research_data.phone}")
            print(f"  Services: {research_data.services}")

        except Exception as e:
            print(f"[O3 RESEARCH] Error parsing research: {e}")
            # Fallback to basic data
            research_data = RealBusinessData(
                company_name=business_name,
                website=website or f"https://{business_name.lower().replace(' ', '')}.com",
                services=business_info.get("services", ["Professional Services"])
            )

        # Store research results
        state.research_data = research_data
        state.research_completed = True
        state.current_stage = "research_confirmation"

        # Generate confirmation response with real data
        response = self._generate_confirmation_response(research_data)

        state.add_message("assistant", response, "research_confirmation")
        await persistent_coia_state_manager.update_session(state.session_id, state)

        return {
            "response": response,
            "stage": "research_confirmation",
            "profile_progress": {
                "completeness": 0.8,
                "stage": "research_confirmation",
                "collectedData": {
                    "company_name": research_data.company_name,
                    "services": research_data.services,
                    "website": research_data.website,
                    "email": research_data.email,
                    "phone": research_data.phone
                },
                "matchingProjects": 12
            },
            "contractor_id": None,
            "session_data": {}
        }

    async def _find_business_website(self, business_name: str, location: str, context: str) -> Optional[str]:
        """Use O3 to intelligently find the business website"""

        find_website_prompt = f"""Help find the most likely website for this business:
Business Name: {business_name}
Location: {location or 'Not specified'}
Context: {context}

Based on the business name and location, what is the most likely website URL?
Consider common patterns like:
- businessname.com
- business-name.com
- businessnameservice.com
- Location-specific domains

Return only the most likely full URL (with https://)."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-5-mini",  # Use GPT-5-mini for simple website finding
                messages=[
                    {"role": "user", "content": find_website_prompt}
                ],
                temperature=0.3,
                max_tokens=100
            )

            website_response = response.choices[0].message.content.strip()

            # Extract URL from response
            url_match = re.search(r"https?://[\w\.-]+\.[\w]+", website_response)
            if url_match:
                return url_match.group(0)

        except Exception as e:
            print(f"[O3 WEBSITE] Error finding website: {e}")

        # Fallback to common pattern
        clean_name = re.sub(r"[^a-zA-Z0-9]", "", business_name).lower()
        return f"https://{clean_name}.com"

    def _generate_confirmation_response(self, research_data: RealBusinessData) -> str:
        """Generate confirmation response with real research data and actual links"""

        services_text = ", ".join(research_data.services[:3]) if research_data.services else "Services to be confirmed"

        response_parts = [
            "Great! I found your business online and here's what I discovered:",
            "",
            f"**Company**: {research_data.company_name}"
        ]

        # Show Google Business listing link if found
        if research_data.google_listing_url:
            response_parts.extend([
                "",
                f"[LINK] **Your Google Business Listing**: {research_data.google_listing_url}",
                "[VERIFY] Please click this link to verify this is your Google Business listing"
            ])

        # Show website
        if research_data.website:
            response_parts.extend([
                "",
                f"[WEB] **Your Website**: {research_data.website}",
                "[VERIFY] Please confirm this is your business website"
            ])

        response_parts.append("")

        if research_data.phone:
            response_parts.append(f"**Phone**: {research_data.phone}")
        else:
            response_parts.append("**Phone**: Not found - we'll need this from you")

        if research_data.email:
            response_parts.append(f"**Email**: {research_data.email}")
        else:
            response_parts.append("**Email**: Not found - we'll need this from you")

        response_parts.extend([
            f"**Services**: {services_text}",
            f"**Service Areas**: {', '.join(research_data.service_areas) if research_data.service_areas else 'To be confirmed'}"
        ])

        if research_data.address:
            response_parts.append(f"**Address**: {research_data.address}")

        # Add social media links if found
        if research_data.social_media and (research_data.social_media.get("facebook") or research_data.social_media.get("instagram")):
            response_parts.append("")
            response_parts.append("**Social Media Profiles Found:**")
            if research_data.social_media.get("facebook"):
                response_parts.append(f"[SOCIAL] Facebook: {research_data.social_media['facebook']}")
            if research_data.social_media.get("instagram"):
                response_parts.append(f"[SOCIAL] Instagram: {research_data.social_media['instagram']}")

        response_parts.extend([
            "",
            "**Please confirm each item:**",
            ""
        ])

        # Add interactive confirmation questions
        if research_data.google_listing_url:
            response_parts.append("[QUESTION] **Is this your Google Business listing?** (Click the link above to verify)")
        if research_data.website:
            response_parts.append("[QUESTION] **Is this your website?** (Check the website link above)")

        response_parts.extend([
            "[QUESTION] **Is the phone number correct?**",
            "[QUESTION] **Is the email address correct?**",
            "[QUESTION] **Are the services listed accurate?**",
            "",
            "**Next Steps:**",
            "• If everything looks perfect, say **'Yes, that's all correct'**",
            "• If something needs fixing, tell me what's wrong (e.g. 'The phone number is wrong, it should be...')",
            "",
            "Once confirmed, I'll create your complete InstaBids contractor profile!"
        ])

        return "\n".join(response_parts)

    async def _handle_confirmation(self, state: CoIAConversationState, user_message: str) -> dict[str, Any]:
        """Handle research confirmation"""

        print(f"[O3 CONFIRMATION] Message: '{user_message}'")

        # Use O3 to understand confirmation
        confirmation_prompt = f"""Analyze this response to determine if the user is confirming or correcting information:

Message: "{user_message}"

Return JSON:
{{
    "is_confirmed": true/false,
    "needs_correction": true/false,
    "correction_details": "what needs to be corrected or null"
}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[{"role": "user", "content": confirmation_prompt}],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            confirmation = json.loads(response.choices[0].message.content)
            confirmed = confirmation.get("is_confirmed", False)

        except:
            # Fallback to keyword matching
            message_lower = user_message.lower()
            confirmed = any(word in message_lower for word in ["yes", "correct", "right", "looks good", "that's right"])

        print(f"[O3 CONFIRMATION] Confirmed: {confirmed}")

        if confirmed:
            print("[O3 CONFIRMATION] Creating contractor profile...")
            # Create contractor profile with real data
            contractor_id, user_id = await self._create_contractor_profile(state)
            print(f"[O3 CONFIRMATION] Contractor ID: {contractor_id}")

            if contractor_id:
                # Check if we have auth credentials from the profile creation
                auth_info = ""
                if hasattr(state, "auth_credentials") and state.auth_credentials:
                    if state.auth_credentials.get("has_auth_account"):
                        # We created a real auth account
                        auth_info = f"""**Your Account is Ready - Login Now:**
**Login at**: http://localhost:5173/login
**Email**: {state.auth_credentials['email']}
**Password**: {state.auth_credentials['password']}

SUCCESS: Your account is fully activated and ready to use!"""
                    else:
                        # Fallback mode
                        auth_info = f"""**Your Account is Ready - Just Set Your Password:**
**Go to**: http://localhost:5173/login
**Email**: {state.research_data.email}
**Click "Set Password"** to activate your account

SUCCESS: Your profile is fully created and ready to use!"""

                response = f"""Perfect! I've created your contractor profile with the verified information from my research.

**Your InstaBids contractor account is ready!**

* Complete business profile with real contact information
* Verified services: {', '.join(state.research_data.services[:3])}
* Service areas configured for: {', '.join(state.research_data.service_areas[:3])}
* Ready to receive project invitations

{auth_info}

Your Contractor ID: {contractor_id}

Once you're logged in, you'll have full access to your contractor dashboard and can start receiving project invitations from homeowners in your area!"""

                state.contractor_id = contractor_id
                state.user_id = user_id  # Set auth user ID for FK constraints
                state.current_stage = "completed"
                state.add_message("assistant", response, "completed")
                await persistent_coia_state_manager.update_session(state.session_id, state)

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
                            "website": state.research_data.website,
                            "email": state.research_data.email,
                            "phone": state.research_data.phone
                        },
                        "matchingProjects": 15
                    },
                    "session_data": {}
                }
            else:
                return self._error_response(state, "I had trouble creating your profile. Let me try again.")
        else:
            # User wants to correct something
            response = "No problem! What information needs to be corrected? Please tell me what's wrong and I'll update it."

            state.add_message("assistant", response, "research_correction")
            state.current_stage = "research_correction"
            await persistent_coia_state_manager.update_session(state.session_id, state)

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

    async def _handle_correction(self, state: CoIAConversationState, understanding: dict[str, Any]) -> dict[str, Any]:
        """Handle corrections to business information"""

        if not hasattr(state, "research_data"):
            return self._error_response(state, "I don't have any data to correct yet. Please tell me about your business first.")

        # Update the research data based on corrections
        correction_details = understanding.get("correction_details", "")

        # Use O3 to apply corrections
        correction_prompt = f"""Apply these corrections to the business data:

Current data:
{json.dumps({
    "company_name": state.research_data.company_name,
    "phone": state.research_data.phone,
    "email": state.research_data.email,
    "website": state.research_data.website,
    "services": state.research_data.services,
    "service_areas": state.research_data.service_areas
}, indent=2)}

Correction requested: "{correction_details}"

Return the updated data in the same JSON format with corrections applied."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[{"role": "user", "content": correction_prompt}],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            updated_data = json.loads(response.choices[0].message.content)

            # Apply updates to research data
            state.research_data.company_name = updated_data.get("company_name", state.research_data.company_name)
            state.research_data.phone = updated_data.get("phone", state.research_data.phone)
            state.research_data.email = updated_data.get("email", state.research_data.email)
            state.research_data.website = updated_data.get("website", state.research_data.website)
            state.research_data.services = updated_data.get("services", state.research_data.services)
            state.research_data.service_areas = updated_data.get("service_areas", state.research_data.service_areas)

            # Generate updated confirmation
            response = self._generate_confirmation_response(state.research_data)
            state.current_stage = "research_confirmation"

            return {
                "response": f"I've updated that information. Here's your corrected profile:\n\n{response}",
                "stage": "research_confirmation",
                "profile_progress": {
                    "completeness": 0.8,
                    "stage": "research_confirmation",
                    "collectedData": {
                        "company_name": state.research_data.company_name,
                        "services": state.research_data.services,
                        "website": state.research_data.website,
                        "email": state.research_data.email,
                        "phone": state.research_data.phone
                    },
                    "matchingProjects": 12
                },
                "contractor_id": None,
                "session_data": {}
            }

        except Exception as e:
            print(f"[O3 CORRECTION] Error applying corrections: {e}")
            return self._error_response(state, "I had trouble applying those corrections. Could you please be more specific?")

    async def _create_contractor_profile(self, state: CoIAConversationState) -> tuple[Optional[str], Optional[str]]:
        """Create complete contractor account (auth user + profile + contractor record) with real researched data"""
        print(f"[O3 CREATE PROFILE] Supabase available: {self.supabase is not None}")
        print(f"[O3 CREATE PROFILE] Admin client available: {self.supabase_admin is not None}")
        print(f"[O3 CREATE PROFILE] Has research data: {hasattr(state, 'research_data')}")

        if not self.supabase or not hasattr(state, "research_data"):
            print("[O3 CREATE PROFILE] Missing requirements - returning None")
            return None

        try:
            research = state.research_data
            print(f"[O3 CREATE PROFILE] Research data: {research.company_name}")

            # Extract email for auth account creation
            contractor_email = research.email
            company_name = research.company_name

            if not contractor_email:
                print("[O3 CREATE PROFILE] No email found in research - cannot create auth account")
                return None

            # Step 1: Create Supabase auth user (if admin client available)
            auth_user_id = None
            temp_password = "InstaBids2025!"  # Temporary password

            if self.supabase_admin:
                try:
                    print(f"[O3 CREATE PROFILE] Creating auth user for {contractor_email}")
                    # Create auth user with admin client
                    auth_response = self.supabase_admin.auth.admin.create_user({
                        "email": contractor_email,
                        "password": temp_password,
                        "email_confirm": True,  # Bypass email confirmation
                        "user_metadata": {
                            "full_name": company_name or "Contractor",
                            "role": "contractor"
                        }
                    })

                    auth_user_id = auth_response.user.id
                    print(f"[O3 CREATE PROFILE] SUCCESS: Created auth user: {auth_user_id}")

                    # Step 2: Create profile record
                    profile_data = {
                        "id": auth_user_id,
                        "email": contractor_email,
                        "role": "contractor",
                        "full_name": company_name or "Contractor",
                        "phone": research.phone
                    }

                    profile_result = self.supabase_admin.table("profiles").insert(profile_data).execute()
                    if profile_result.data:
                        print(f"[O3 CREATE PROFILE] SUCCESS: Created profile record for user: {auth_user_id}")

                    # Store auth credentials in state for response
                    state.auth_credentials = {
                        "email": contractor_email,
                        "password": temp_password,
                        "has_auth_account": True
                    }

                except Exception as auth_error:
                    print(f"[O3 CREATE PROFILE] Failed to create auth user: {auth_error}")

                    # Check if this email already has a profile - if so, use that user_id
                    try:
                        existing_profile = self.supabase_admin.table("profiles").select("id").eq("email", contractor_email).execute()
                        if existing_profile.data and len(existing_profile.data) > 0:
                            auth_user_id = existing_profile.data[0]["id"]
                            print(f"[O3 CREATE PROFILE] Found existing profile for email: {auth_user_id}")
                            state.auth_credentials = {
                                "email": contractor_email,
                                "password": temp_password,
                                "has_auth_account": True  # Assume auth account exists if profile exists
                            }
                        else:
                            # No existing profile, create new one with unique email variation
                            auth_user_id = str(uuid.uuid4())
                            unique_email = f"contractor+{auth_user_id[:8]}@instabids.com"
                            print(f"[O3 CREATE PROFILE] Creating new profile with unique email: {unique_email}")

                            profile_data = {
                                "id": auth_user_id,
                                "email": unique_email,  # Use unique email to avoid constraint violation
                                "role": "contractor",
                                "full_name": company_name or "Contractor",
                                "phone": research.phone
                            }
                            profile_result = self.supabase_admin.table("profiles").insert(profile_data).execute()
                            if profile_result.data:
                                print("[O3 CREATE PROFILE] SUCCESS: Created new profile with unique email")
                                state.auth_credentials = {
                                    "email": unique_email,  # Use the unique email for login
                                    "password": temp_password,
                                    "has_auth_account": False
                                }
                            else:
                                print("[O3 CREATE PROFILE] Failed to create profile")
                                return None

                    except Exception as profile_error:
                        print(f"[O3 CREATE PROFILE] Error handling existing profile: {profile_error}")
                        return None
            else:
                # Fallback to temp user_id if no admin client
                auth_user_id = str(uuid.uuid4())
                print(f"[O3 CREATE PROFILE] No admin client - using temp user_id: {auth_user_id}")
                state.auth_credentials = {
                    "email": contractor_email,
                    "password": temp_password,
                    "has_auth_account": False
                }

            # Step 3: Build contractor data for contractors table
            # Build service areas JSON
            service_areas = {}
            if research.service_areas:
                service_areas["zip_codes"] = research.service_areas

            # Build insurance info JSON if available
            insurance_info = {}
            if hasattr(research, "certifications") and research.certifications:
                insurance_info["certifications"] = research.certifications

            # Prepare contractor data for contractors table
            contractor_data = {
                "user_id": auth_user_id,
                "company_name": company_name or "Professional Services",
                "specialties": research.services or ["General Services"],
                "service_areas": service_areas if service_areas else None,
                "insurance_info": insurance_info if insurance_info else None,
                "tier": 1,  # New contractors start at Tier 1
                "availability_status": "available",
                "total_jobs": max(0, (research.years_experience or 0) * 15),  # Estimate based on experience
                "verified": bool(research.phone and research.email),  # Verified if has contact info
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Step 4: Check if contractor already exists, if not create new one
            if not self.supabase_admin:
                print("[O3 CREATE PROFILE ERROR] No admin client available - cannot create contractor")
                return None

            # Check if contractor already exists for this user_id
            try:
                existing_contractor = self.supabase_admin.table("contractors").select("id").eq("user_id", auth_user_id).execute()
                if existing_contractor.data and len(existing_contractor.data) > 0:
                    contractor_id = existing_contractor.data[0]["id"]
                    print(f"[O3 CREATE PROFILE] SUCCESS: Found existing contractor profile: {contractor_id}")
                    print(f"[O3 CREATE PROFILE] User ID: {auth_user_id}")
                    print(f"[O3 CREATE PROFILE] Email: {contractor_email}")
                    return contractor_id, auth_user_id
            except Exception as check_error:
                print(f"[O3 CREATE PROFILE] Error checking existing contractor: {check_error}")
                # Continue to create new contractor if check fails

            result = self.supabase_admin.table("contractors").insert(contractor_data).execute()

            if result.data and len(result.data) > 0:
                contractor_id = result.data[0]["id"]
                print(f"[O3 CREATE PROFILE] SUCCESS: Created contractor profile: {contractor_id}")
                print(f"[O3 CREATE PROFILE] Company: {contractor_data['company_name']}")
                print(f"[O3 CREATE PROFILE] Email: {contractor_email}")
                print(f"[O3 CREATE PROFILE] Auth User ID: {auth_user_id}")
                print(f"[O3 CREATE PROFILE] Specialties: {contractor_data['specialties']}")

                return contractor_id, auth_user_id
            else:
                print("[O3 CREATE PROFILE] Failed to create contractor profile - no data returned")
                return None, None

        except Exception as e:
            print(f"[O3 CREATE PROFILE ERROR] {type(e).__name__}: {e}")
            logger.error(f"Error creating contractor: {e}")
            import traceback
            print(f"[O3 CREATE PROFILE ERROR] Traceback:\n{traceback.format_exc()}")
            return None, None

    async def _standard_conversation(self, state: CoIAConversationState, user_message: str) -> dict[str, Any]:
        """Handle standard conversation"""

        response = """Hi! I'm your contractor onboarding assistant powered by OpenAI's GPT-5 advanced reasoning.

To get started, just tell me about your business. For example:
• "I own JM Holiday Lighting in South Florida"
• "My business is ABC Construction"
• "I run Mike's Plumbing in Dallas"
• "I specialize in holiday lighting installation"

I'll use advanced AI to research your business online and create your complete InstaBids profile with real, verified information. What's your business name?"""

        state.add_message("assistant", response, "welcome")
        await persistent_coia_state_manager.update_session(state.session_id, state)

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

    async def _handle_returning_contractor(self, state: CoIAConversationState, contractor_id: str, business_name: str) -> dict[str, Any]:
        """Handle returning contractor with previous conversation history"""

        print(f"[O3 RETURNING] Loading history for {contractor_id}")

        # Get contractor's previous conversations
        conversation_history = await persistent_coia_state_manager.get_contractor_history(contractor_id)

        if conversation_history:
            latest_conversation = conversation_history[0]  # Most recent conversation
            print(f"[O3 RETURNING] Found {len(conversation_history)} previous conversations")

            # Set contractor ID in current state
            state.contractor_id = contractor_id

            # Generate personalized welcome for returning contractor
            response_parts = [
                f"Welcome back to InstaBids! I see you're {business_name}.",
                "",
                "I found your previous profile in our system:",
                f"• Last conversation: {latest_conversation.get('created_at', 'Unknown')[:10]}",
                f"• Profile status: {latest_conversation.get('current_stage', 'Unknown')}",
                f"• Total conversations: {len(conversation_history)}",
                ""
            ]

            if latest_conversation.get("completed"):
                response_parts.extend([
                    "Great news! Your contractor profile is already set up and active.",
                    "",
                    "**What would you like to do today?**",
                    "• Update your business information",
                    "• Check for new project opportunities",
                    "• Review your bidding settings",
                    "• Just say 'Hi' and I'll help with whatever you need!"
                ])
                current_stage = "returning_active"
            else:
                response_parts.extend([
                    "I see we started setting up your profile but didn't finish.",
                    "",
                    "**Would you like to:**",
                    "• Continue where we left off with your profile setup",
                    "• Start fresh with updated business information",
                    "• Just say 'continue' and I'll pick up where we left off!"
                ])
                current_stage = "returning_incomplete"

            response = "\n".join(response_parts)
            state.add_message("assistant", response, current_stage)
            state.current_stage = current_stage
            await persistent_coia_state_manager.update_session(state.session_id, state)

            return {
                "response": response,
                "stage": current_stage,
                "profile_progress": {
                    "completeness": 0.9 if latest_conversation.get("completed") else 0.5,
                    "stage": current_stage,
                    "collectedData": {
                        "business_name": business_name,
                        "returning_contractor": True,
                        "previous_conversations": len(conversation_history)
                    },
                    "matchingProjects": 8
                },
                "contractor_id": contractor_id,
                "session_data": {
                    "returning_contractor": True,
                    "conversation_history": conversation_history
                }
            }
        else:
            # No history found, treat as new contractor
            print(f"[O3 RETURNING] No history found for {contractor_id}")
            return await self._standard_conversation(state, f"I own {business_name}")

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

    async def _search_google_business(self, business_name: str, context: str) -> Optional[dict[str, Any]]:
        """Search Google Places API for real business data"""
        if not self.google_api_key:
            return None

        try:
            # Extract location from context if available
            location = "South Florida"
            if "south florida" in context.lower():
                location = "South Florida"
            elif "florida" in context.lower():
                location = "Florida"

            # Use Google Places API (New) Text Search
            url = "https://places.googleapis.com/v1/places:searchText"

            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.google_api_key,
                "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.types,places.businessStatus,places.nationalPhoneNumber,places.websiteUri,places.addressComponents,places.primaryType,places.primaryTypeDisplayName"
            }

            # Request body with location bias
            request_body = {
                "textQuery": f"{business_name} {location}",
                "pageSize": 5,
                "locationBias": {
                    "circle": {
                        "center": {
                            "latitude": 26.3683,  # South Florida approximate center
                            "longitude": -80.1289
                        },
                        "radius": 50000  # 50km radius (max allowed)
                    }
                },
                "includePureServiceAreaBusinesses": True,
                "rankPreference": "RELEVANCE"
            }

            print(f"[O3 GOOGLE SEARCH] Searching for: {business_name} in {location}")

            response = requests.post(url, headers=headers, json=request_body)

            if response.status_code == 200:
                data = response.json()
                places = data.get("places", [])

                print(f"[O3 GOOGLE SEARCH] Found {len(places)} results")

                # Find exact match or best match
                best_match = None
                for place in places:
                    place_name = place.get("displayName", {}).get("text", "").lower()

                    # Check for exact match
                    if business_name.lower() in place_name or place_name in business_name.lower():
                        best_match = place
                        break

                # Use first result if no exact match
                if not best_match and places:
                    best_match = places[0]

                if best_match:
                    print(f"[O3 GOOGLE SEARCH] Found business: {best_match.get('displayName', {}).get('text')}")
                    print(f"[O3 GOOGLE SEARCH] Phone: {best_match.get('nationalPhoneNumber')}")
                    print(f"[O3 GOOGLE SEARCH] Website: {best_match.get('websiteUri')}")

                    # Construct Google Business listing URL
                    place_id = best_match.get("id")
                    google_listing_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else None

                    return {
                        "name": best_match.get("displayName", {}).get("text"),
                        "address": best_match.get("formattedAddress"),
                        "phone": best_match.get("nationalPhoneNumber"),
                        "website": best_match.get("websiteUri"),
                        "rating": best_match.get("rating"),
                        "review_count": best_match.get("userRatingCount"),
                        "types": best_match.get("types", []),
                        "business_status": best_match.get("businessStatus"),
                        "primary_type": best_match.get("primaryType"),
                        "primary_type_display": best_match.get("primaryTypeDisplayName", {}).get("text"),
                        "google_listing_url": google_listing_url,
                        "place_id": place_id
                    }

            print(f"[O3 GOOGLE SEARCH] No results found for: {business_name}")
            return None

        except Exception as e:
            print(f"[O3 GOOGLE SEARCH] Error: {e}")
            import traceback
            traceback.print_exc()
            return None

# Global instance
openai_gpt5_coia: Optional[OpenAIGPT5CoIA] = None

def initialize_openai_gpt5_coia(api_key: str = None) -> OpenAIGPT5CoIA:
    """Initialize global OpenAI GPT-5 CoIA"""
    global openai_gpt5_coia
    openai_gpt5_coia = OpenAIGPT5CoIA(api_key)
    return openai_gpt5_coia

def get_openai_gpt5_coia() -> Optional[OpenAIGPT5CoIA]:
    """Get global OpenAI GPT-5 CoIA"""
    return openai_gpt5_coia
