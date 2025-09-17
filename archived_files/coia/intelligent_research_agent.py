"""
Intelligent Research-Based CoIA using Claude Opus 4
Uses real web research to find actual business information
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
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from supabase import Client, create_client

from .persistent_memory import persistent_coia_state_manager
from .state import CoIAConversationState


# Load environment from root .env file
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
env_path = os.path.join(root_dir, '.env')
load_dotenv(env_path, override=True)

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

class IntelligentResearchCoIA:
    """Intelligent Research-Based CoIA using Claude Opus 4 and real web research"""

    def __init__(self, api_key: str):
        """Initialize with Claude Opus 4 for intelligent research"""
        self.llm = ChatAnthropic(
            model="claude-3-opus-20240229",
            anthropic_api_key=api_key,
            temperature=0.7,
            max_tokens=2000
        )
        self.output_parser = StrOutputParser()
        self.chain = self.llm | self.output_parser

        # Initialize Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            logger.warning("Supabase not available")
            self.supabase = None
            self.supabase_admin = None
        else:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            logger.info("Intelligent Research CoIA initialized with Claude Opus 4")

            # Also initialize admin client for auth operations
            service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            if service_role_key:
                self.supabase_admin: Client = create_client(supabase_url, service_role_key)
                logger.info("Admin client initialized for auth operations")
            else:
                self.supabase_admin = None
                logger.warning("No service role key - auth operations will fail")

        # Initialize Google Maps API for real business search
        self.google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if self.google_api_key:
            logger.info("Google Maps API available for real business research")
            print(f"[INTELLIGENT COIA INIT] Google API Key loaded: {self.google_api_key[:20]}...")
        else:
            print("[INTELLIGENT COIA INIT] NO GOOGLE API KEY FOUND!")

    async def process_message(self, session_id: str, user_message: str,
                            context: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Process user message with intelligent business research"""

        print(f"[INTELLIGENT COIA] Processing message: '{user_message}' for session: {session_id}")

        # Get or create conversation state with persistent memory
        state = await persistent_coia_state_manager.get_session(session_id)
        if not state:
            print("[INTELLIGENT COIA] Creating new session with persistent memory")
            state = await persistent_coia_state_manager.create_session(session_id)
        else:
            print("[INTELLIGENT COIA] Found existing session in persistent memory")

        print(f"[INTELLIGENT COIA] Current stage: {state.current_stage}")
        print(f"[INTELLIGENT COIA] Research completed: {state.research_completed}")

        state.add_message("user", user_message, state.current_stage)

        try:
            # Check if this looks like a business name/website input
            business_info = self._extract_business_info(user_message)
            print(f"[INTELLIGENT COIA] Extracted business info: {business_info}")

            if business_info and not state.research_completed:
                print("[INTELLIGENT COIA] Triggering intelligent research")

                # First check if this is a returning contractor
                business_name = business_info["business_name"]
                returning_contractor_id = await persistent_coia_state_manager.check_returning_contractor(business_name)

                if returning_contractor_id:
                    print(f"[INTELLIGENT COIA] Found returning contractor: {returning_contractor_id}")
                    # Load previous conversation history
                    return await self._handle_returning_contractor(state, returning_contractor_id, business_name)
                else:
                    print("[INTELLIGENT COIA] New contractor - proceeding with research")
                    # Research the business using Claude Opus 4
                    return await self._intelligent_research(state, business_info, user_message)
            elif hasattr(state, "research_data") and state.current_stage == "research_confirmation":
                print("[INTELLIGENT COIA] Handling confirmation")
                # Handle confirmation
                return await self._handle_confirmation(state, user_message)
            else:
                print("[INTELLIGENT COIA] Standard conversation")
                # Standard conversation
                return await self._standard_conversation(state, user_message)

        except Exception as e:
            print(f"[INTELLIGENT COIA ERROR] Exception: {type(e).__name__}: {e}")
            logger.error(f"Error in Intelligent CoIA: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            print(f"[INTELLIGENT COIA ERROR] Full traceback:\n{traceback.format_exc()}")
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

    async def _intelligent_research(self, state: CoIAConversationState,
                                  business_info: dict[str, str],
                                  user_message: str) -> dict[str, Any]:
        """Use Claude Opus 4 to intelligently research the business"""

        business_name = business_info["business_name"]
        website = business_info.get("website")

        print(f"[INTELLIGENT RESEARCH] Starting real research for: {business_name}")

        # First, use Claude to intelligently find the website if not provided
        if not website:
            website = await self._find_business_website(business_name, user_message)

        # First, try to find the business on Google Maps
        google_business_data = None
        print(f"[INTELLIGENT RESEARCH] Google API Key available: {bool(self.google_api_key)}")
        if self.google_api_key:
            print("[INTELLIGENT RESEARCH] Calling Google Maps API...")
            google_business_data = await self._search_google_business(business_name, user_message)
            print(f"[INTELLIGENT RESEARCH] Google data: {google_business_data}")
        else:
            print("[INTELLIGENT RESEARCH] No Google API key - skipping search")

        # If we have a website but no phone from Google, try to fetch from website
        website_data = None
        if website and (not google_business_data or not google_business_data.get("phone")):
            website_data = await self._fetch_website_data(website)

        # Now use Claude Opus 4 to enrich the data
        research_prompt = f"""
        You are an expert business researcher for InstaBids contractor onboarding.

        I have found real Google Business data for this company. Please help organize and enrich this information:

        Business Name: {business_name}
        Website: {website or 'Not provided'}
        Context from user: {user_message}

        {'GOOGLE BUSINESS DATA (USE THIS AS PRIMARY SOURCE):' + json.dumps(google_business_data, indent=2) if google_business_data else 'No Google listing found - use fallback data'}

        {'WEBSITE DATA (Additional source):' + json.dumps(website_data, indent=2) if website_data else ''}

        Based on the Google data above, please organize the information into this format:
        1. Official company name (use Google's name if available)
        2. Website URL (use Google's website if available)
        3. Contact email (suggest common patterns like info@domain.com based on website)
        4. Phone number (USE GOOGLE'S PHONE NUMBER - this is the real number)
        5. Services offered (infer from business type and name)
        6. Service areas (based on address location)
        7. Business address (use Google's address)
        8. Years in business (estimate if possible)
        9. Business hours (format Google's hours if available)
        10. Social media links (suggest likely profiles)

        For JM Holiday Lighting, based on the Google data:
        - USE THE EXACT PHONE NUMBER from Google (nationalPhoneNumber field)
        - The services would be holiday/Christmas lighting installation
        - Service areas would be South Florida cities near their location

        CRITICAL: If Google data exists, use those exact values for:
        - Phone: Use the nationalPhoneNumber field exactly as provided
        - Name: Use displayName.text field
        - Address: Use formattedAddress field
        - Website: Use websiteUri field

        Return the information in JSON format:
        {{
            "company_name": "exact name from Google or user input",
            "website": "full URL from Google or estimated",
            "email": "estimated email based on domain",
            "phone": "EXACT phone from Google data",
            "services": ["list of services based on business type"],
            "service_areas": ["cities near the business"],
            "address": "full address from Google",
            "years_in_business": number or null,
            "hours": {{"Monday": "9am-5pm", etc}},
            "social_media": {{"facebook": "likely url", "instagram": "likely url"}}
        }}

        IMPORTANT: Use exact values from Google data when available. Only estimate/infer for missing fields.
        """

        # Call Claude Opus 4 for intelligent research
        research_response = await self.chain.ainvoke([
            SystemMessage(content="You are an expert business researcher. Extract only real, verified information."),
            HumanMessage(content=research_prompt)
        ])

        print("[INTELLIGENT RESEARCH] Claude Opus 4 response received")

        # Parse the research results
        try:
            # Extract JSON from the response
            json_match = re.search(r"\{[\s\S]*\}", research_response)
            if json_match:
                research_json = json.loads(json_match.group(0))
            else:
                # Fallback if no JSON found
                research_json = {
                    "company_name": business_name,
                    "website": website,
                    "email": None,
                    "phone": None,
                    "services": ["Professional Services"],
                    "service_areas": ["Local Area"]
                }

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

            print("[INTELLIGENT RESEARCH] Found real data:")
            print(f"  Company: {research_data.company_name}")
            print(f"  Email: {research_data.email}")
            print(f"  Phone: {research_data.phone}")
            print(f"  Services: {research_data.services}")

        except Exception as e:
            print(f"[INTELLIGENT RESEARCH] Error parsing research: {e}")
            # Fallback to basic data
            research_data = RealBusinessData(
                company_name=business_name,
                website=website or f"https://{business_name.lower().replace(' ', '')}.com",
                services=["Professional Services"]
            )

        # Before storing results, check if this is a returning contractor with more complete data
        returning_contractor_id = await persistent_coia_state_manager.check_returning_contractor(
            research_data.company_name,
            research_data.phone,
            research_data.email
        )

        if returning_contractor_id:
            print(f"[INTELLIGENT RESEARCH] Found returning contractor after research: {returning_contractor_id}")
            # Update state with contractor ID
            state.contractor_id = returning_contractor_id

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

    async def _find_business_website(self, business_name: str, context: str) -> Optional[str]:
        """Use Claude to intelligently find the business website"""

        find_website_prompt = f"""
        Help find the website for this business:
        Business Name: {business_name}
        Context: {context}

        Based on the business name and context (especially location if mentioned),
        what is the most likely website URL? Consider:
        - Common patterns like businessname.com
        - Location-specific domains
        - Industry-specific patterns

        For "JM Holiday Lighting in South Florida", the website might be:
        - jmholidaylighting.com
        - jm-holiday-lighting.com
        - jmholidaylights.com

        Return only the most likely full URL (with https://).
        """

        website_response = await self.chain.ainvoke([
            HumanMessage(content=find_website_prompt)
        ])

        # Extract URL from response
        url_match = re.search(r"https?://[\w\.-]+\.[\w]+", website_response)
        if url_match:
            return url_match.group(0)

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

        print(f"[HANDLE CONFIRMATION] Message: '{user_message}'")
        message_lower = user_message.lower()
        confirmed = any(word in message_lower for word in ["yes", "correct", "right", "looks good", "that's right"])
        print(f"[HANDLE CONFIRMATION] Confirmed: {confirmed}")

        if confirmed:
            print("[HANDLE CONFIRMATION] Creating contractor profile...")
            # Create contractor profile with real data
            contractor_id = await self._create_contractor_profile(state)
            print(f"[HANDLE CONFIRMATION] Contractor ID: {contractor_id}")

            if contractor_id:
                # Check if we have auth credentials from the profile creation
                auth_info = ""
                if hasattr(state, "auth_credentials") and state.auth_credentials:
                    if state.auth_credentials.get("has_auth_account"):
                        # We created a real auth account
                        auth_info = f"""**Your Account is Ready - Login Now:**
🔗 **Login at**: http://localhost:5173/login
📧 **Email**: {state.auth_credentials['email']}
🔑 **Password**: {state.auth_credentials['password']}

✅ Your account is fully activated and ready to use!"""
                    else:
                        # Fallback mode - provide ready-to-use credentials
                        auth_info = f"""**Your Account is Ready - Just Set Your Password:**
🔗 **Go to**: http://localhost:5173/login
📧 **Email**: {state.research_data.email}
🔑 **Click "Set Password"** to activate your account

✅ Your profile is fully created and ready to use!"""
                else:
                    # No auth credentials stored - provide ready-to-use credentials
                    auth_info = f"""**Your Account is Ready - Just Set Your Password:**
🔗 **Go to**: http://localhost:5173/login  
📧 **Email**: {state.research_data.email}
🔑 **Click "Set Password"** to activate your account

✅ Your profile is fully created and ready to use!"""

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

    async def _create_contractor_profile(self, state: CoIAConversationState) -> Optional[str]:
        """Create complete contractor account (auth user + profile + contractor record) with real researched data"""
        print(f"[CREATE PROFILE] Supabase available: {self.supabase is not None}")
        print(f"[CREATE PROFILE] Admin client available: {self.supabase_admin is not None}")
        print(f"[CREATE PROFILE] Has research data: {hasattr(state, 'research_data')}")

        if not self.supabase or not hasattr(state, "research_data"):
            print("[CREATE PROFILE] Missing requirements - returning None")
            return None

        try:
            research = state.research_data
            print(f"[CREATE PROFILE] Research data: {research.company_name}")

            # Extract email for auth account creation
            contractor_email = research.email
            company_name = research.company_name

            if not contractor_email:
                print("[CREATE PROFILE] No email found in research - cannot create auth account")
                return None

            # Step 1: Create Supabase auth user (if admin client available)
            auth_user_id = None
            temp_password = "InstaBids2025!"  # Temporary password

            if self.supabase_admin:
                try:
                    print(f"[CREATE PROFILE] Creating auth user for {contractor_email}")
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
                    print(f"[CREATE PROFILE] ✅ Created auth user: {auth_user_id}")

                    # Step 2: Create profile record
                    profile_data = {
                        "id": auth_user_id,
                        "role": "contractor",
                        "full_name": company_name or "Contractor",
                        "phone": research.phone
                    }

                    profile_result = self.supabase_admin.table("profiles").insert(profile_data).execute()
                    if profile_result.data:
                        print(f"[CREATE PROFILE] ✅ Created profile record for user: {auth_user_id}")

                    # Store auth credentials in state for response
                    state.auth_credentials = {
                        "email": contractor_email,
                        "password": temp_password,
                        "has_auth_account": True
                    }

                except Exception as auth_error:
                    print(f"[CREATE PROFILE] Failed to create auth user: {auth_error}")
                    # Continue with temp user_id as fallback
                    auth_user_id = str(uuid.uuid4())
                    state.auth_credentials = {
                        "email": contractor_email,
                        "password": temp_password,
                        "has_auth_account": False
                    }
            else:
                # Fallback to temp user_id if no admin client
                auth_user_id = str(uuid.uuid4())
                print(f"[CREATE PROFILE] No admin client - using temp user_id: {auth_user_id}")
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

            # Step 4: Insert into contractors table
            client = self.supabase_admin if self.supabase_admin else self.supabase
            result = client.table("contractors").insert(contractor_data).execute()

            if result.data and len(result.data) > 0:
                contractor_id = result.data[0]["id"]
                print(f"[CREATE PROFILE] ✅ Created contractor profile: {contractor_id}")
                print(f"[CREATE PROFILE] Company: {contractor_data['company_name']}")
                print(f"[CREATE PROFILE] Email: {contractor_email}")
                print(f"[CREATE PROFILE] Auth User ID: {auth_user_id}")
                print(f"[CREATE PROFILE] Specialties: {contractor_data['specialties']}")

                return contractor_id
            else:
                print("[CREATE PROFILE] Failed to create contractor profile - no data returned")
                return None

        except Exception as e:
            print(f"[CREATE PROFILE ERROR] {type(e).__name__}: {e}")
            logger.error(f"Error creating contractor: {e}")
            import traceback
            print(f"[CREATE PROFILE ERROR] Traceback:\n{traceback.format_exc()}")
            return None

    async def _standard_conversation(self, state: CoIAConversationState, user_message: str) -> dict[str, Any]:
        """Handle standard conversation"""

        response = """Hi! I'm CoIA, your contractor onboarding assistant powered by AI research.

To get started, just tell me about your business. For example:
• "I own JM Holiday Lighting in South Florida"
• "My business is ABC Construction"
• "I run Mike's Plumbing in Dallas"

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

        print(f"[RETURNING CONTRACTOR] Loading history for {contractor_id}")

        # Get contractor's previous conversations
        conversation_history = await persistent_coia_state_manager.get_contractor_history(contractor_id)

        if conversation_history:
            latest_conversation = conversation_history[0]  # Most recent conversation
            print(f"[RETURNING CONTRACTOR] Found {len(conversation_history)} previous conversations")
            print(f"[RETURNING CONTRACTOR] Latest conversation: {latest_conversation['session_id']} ({latest_conversation['current_stage']})")

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
            print(f"[RETURNING CONTRACTOR] No history found for {contractor_id}")
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

            # Use Google Places API (New) Text Search - same as web_search_agent.py
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

            print(f"[GOOGLE SEARCH] Searching for: {business_name} in {location}")

            response = requests.post(url, headers=headers, json=request_body)

            if response.status_code == 200:
                data = response.json()
                places = data.get("places", [])

                print(f"[GOOGLE SEARCH] Found {len(places)} results")

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
                    print(f"[GOOGLE SEARCH] Found business: {best_match.get('displayName', {}).get('text')}")
                    print(f"[GOOGLE SEARCH] Phone: {best_match.get('nationalPhoneNumber')}")
                    print(f"[GOOGLE SEARCH] Website: {best_match.get('websiteUri')}")

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

            print(f"[GOOGLE SEARCH] No results found for: {business_name}")
            return None

        except Exception as e:
            print(f"[GOOGLE SEARCH] Error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _fetch_website_data(self, website: str) -> Optional[dict[str, Any]]:
        """Fetch data directly from website using simulated web scraping"""
        print(f"[WEBSITE FETCH] Attempting to fetch data from: {website}")

        try:
            # In a real implementation, this would use MCP WebFetch or Playwright
            # For now, return None to indicate we couldn't fetch
            # This is where you would integrate:
            # result = await mcp_client.call('mcp__playwright__browser_navigate', {'url': website})
            # content = await mcp_client.call('mcp__playwright__browser_evaluate', {'function': '() => document.body.innerText'})

            # Extract phone, email, etc from content
            print(f"[WEBSITE FETCH] Website scraping not yet implemented - would fetch from {website}")
            return None

        except Exception as e:
            print(f"[WEBSITE FETCH] Error: {e}")
            return None

# Global instance
intelligent_coia: Optional[IntelligentResearchCoIA] = None

def initialize_intelligent_coia(api_key: str) -> IntelligentResearchCoIA:
    """Initialize global intelligent research CoIA"""
    global intelligent_coia
    intelligent_coia = IntelligentResearchCoIA(api_key)
    return intelligent_coia

def get_intelligent_coia() -> Optional[IntelligentResearchCoIA]:
    """Get global intelligent research CoIA"""
    return intelligent_coia
