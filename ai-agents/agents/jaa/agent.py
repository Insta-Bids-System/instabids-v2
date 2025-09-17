"""
Intelligent Job Assessment Agent - LangGraph + GPT-4 Implementation
Replaces regex-based extraction with real AI intelligence
"""
import json
import os
import sys
from datetime import datetime
from typing import Annotated, Any
import time

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from supabase import create_client


# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from typing_extensions import TypedDict

from bid_card_utils import create_bid_card_with_defaults
from database_simple import SupabaseDB
from services.llm_cost_tracker import LLMCostTracker
from utils.date_parser import SimpleDateParser


class IntelligentJAAState(TypedDict):
    """State for the Intelligent JAA Agent"""
    messages: Annotated[list[BaseMessage], add_messages]
    conversation_data: dict[str, Any]
    extracted_data: dict[str, Any]
    bid_card_data: dict[str, Any]
    thread_id: str
    stage: str  # 'analysis', 'extraction', 'validation', 'generation'
    errors: list[str]

class JobAssessmentAgent:
    """
    Intelligent Job Assessment Agent using GPT-4 + LangGraph
    Replaces simple regex patterns with real AI understanding
    """

    def __init__(self):
        """Initialize Intelligent JAA with GPT-4 and LangGraph"""
        load_dotenv(override=True)

        # Initialize OpenAI client
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        self.llm = ChatOpenAI(
            model="gpt-4",  # GPT-4 - most powerful model for complex reasoning
            api_key=self.openai_key,
            temperature=0.1,
            max_tokens=4000
        )

        # Initialize Supabase
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        self.db = SupabaseDB()
        
        # Initialize cost tracker
        self.cost_tracker = LLMCostTracker()
        
        # Initialize date parser
        self.date_parser = SimpleDateParser()

        # Build the LangGraph workflow
        self.workflow = self._build_workflow()

        print("[INTELLIGENT JAA] Initialized with GPT-4 + LangGraph + Date Parsing")
    
    def _tracked_llm_invoke(self, messages: list, context: dict = None):
        """Wrapper for LLM calls with cost tracking"""
        start_time = time.time()
        
        # Make the LLM call
        response = self.llm.invoke(messages)
        
        # Calculate approximate tokens (Claude doesn't always return usage)
        # Using rough estimate: 1 token ≈ 4 characters
        input_text = " ".join([msg.content for msg in messages])
        output_text = response.content if hasattr(response, 'content') else str(response)
        
        input_tokens = len(input_text) // 4
        output_tokens = len(output_text) // 4
        
        # Track the cost (using sync version)
        duration_ms = int((time.time() - start_time) * 1000)
        self.cost_tracker.track_llm_call_sync(
            agent_name="JAA",
            provider="openai",
            model="gpt-4",  # Using actual model name
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
            context=context or {}
        )
        
        return response

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for intelligent bid card generation"""

        workflow = StateGraph(IntelligentJAAState)

        # Add nodes
        workflow.add_node("analyze_conversation", self._analyze_conversation)
        workflow.add_node("extract_project_data", self._extract_project_data)
        workflow.add_node("extract_dates", self._extract_dates)
        workflow.add_node("validate_extraction", self._validate_extraction)
        workflow.add_node("generate_bid_card", self._generate_bid_card)

        # Add edges
        workflow.add_edge(START, "analyze_conversation")
        workflow.add_edge("analyze_conversation", "extract_project_data")
        workflow.add_edge("extract_project_data", "extract_dates")
        workflow.add_edge("extract_dates", "validate_extraction")
        workflow.add_edge("validate_extraction", "generate_bid_card")
        workflow.add_edge("generate_bid_card", END)

        return workflow.compile()

    async def process_conversation(self, thread_id: str) -> dict[str, Any]:
        """
        Main entry point: Process CIA conversation with full AI intelligence

        Args:
            thread_id: The conversation thread ID from CIA

        Returns:
            Dict with success status and bid card data
        """
        print(f"\n[INTELLIGENT JAA] Processing conversation: {thread_id}")

        try:
            # Step 1: Load conversation from unified conversation system
            print("[INTELLIGENT JAA] Loading conversation from unified system...")
            conversation_data = await self.db.load_conversation_state(thread_id)

            if not conversation_data:
                return {
                    "success": False,
                    "error": f"No conversation found for thread_id: {thread_id}"
                }

            # Extract state from unified conversation system
            state = conversation_data.get("state", {})
            if isinstance(state, str):
                state = json.loads(state)
                conversation_data["state"] = state

            print(f"[INTELLIGENT JAA] Loaded unified conversation with {len(state.get('messages', []))} messages")

            # Step 2: Initialize state and run LangGraph workflow
            initial_state = {
                "messages": [],
                "conversation_data": conversation_data,
                "extracted_data": {},
                "bid_card_data": {},
                "thread_id": thread_id,
                "stage": "analysis",
                "errors": []
            }

            # Run the intelligent workflow
            final_state = self.workflow.invoke(initial_state)

            if final_state["errors"]:
                return {
                    "success": False,
                    "error": f'Processing errors: {"; ".join(final_state["errors"])}'
                }

            # Step 3: Save to database using new utility
            print("[INTELLIGENT JAA] Creating bid card with fixed database schema...")

            # Prepare project data for the new utility
            project_data = {
                "project_type": final_state["bid_card_data"].get("project_type", "general_renovation"),
                "title": final_state["bid_card_data"].get("title", "New Project"),
                "description": final_state["bid_card_data"].get("description", ""),
                "urgency_level": final_state["bid_card_data"].get("urgency_level", "week"),
                "complexity_score": final_state["bid_card_data"].get("complexity_score", 3),
                "contractor_count_needed": final_state["bid_card_data"].get("contractor_count_needed", 3),
                "budget_min": final_state["bid_card_data"].get("budget_min"),
                "budget_max": final_state["bid_card_data"].get("budget_max"),
                "requirements": final_state["bid_card_data"].get("requirements", []),
                "location_city": final_state["bid_card_data"].get("location_city"),
                "location_state": final_state["bid_card_data"].get("location_state"),
                "location_zip": final_state["bid_card_data"].get("location_zip"),
                "cia_thread_id": thread_id[-20:],  # Truncate to fit VARCHAR(20)
                "timeline_start": final_state["bid_card_data"].get("timeline_start"),
                "timeline_end": final_state["bid_card_data"].get("timeline_end"),
                # NEW: Add exact date fields
                "bid_collection_deadline": final_state["extracted_data"].get("bid_collection_deadline"),
                "project_completion_deadline": final_state["extracted_data"].get("project_completion_deadline"),
                "deadline_hard": final_state["extracted_data"].get("deadline_hard", False),
                "deadline_context": final_state["extracted_data"].get("deadline_context")
            }

            # Create bid card using the new utility
            create_result = create_bid_card_with_defaults(project_data)

            if create_result["success"]:
                bid_card_data = create_result["bid_card"]
                bid_card_number = create_result["bid_card_number"]

                # Update the bid_document with AI analysis
                bid_document = {
                    "bid_card_number": bid_card_number,
                    "full_cia_thread_id": thread_id,
                    "all_extracted_data": final_state["extracted_data"],
                    "ai_analysis": final_state["bid_card_data"],
                    "generated_at": datetime.now().isoformat(),
                    "extraction_method": "IntelligentJAA_ClaudeOpus4",
                    "instabids_version": "3.0"
                }

                # Update the bid_document field
                update_result = self.supabase.table("bid_cards").update({
                    "bid_document": bid_document
                }).eq("id", bid_card_data["id"]).execute()

                print(f"[INTELLIGENT JAA] SUCCESS: Created bid card {bid_card_number}")
                print(f"[INTELLIGENT JAA] Project: {final_state['bid_card_data'].get('project_type')}")
                print(f"[INTELLIGENT JAA] Budget: ${final_state['bid_card_data'].get('budget_min')}-${final_state['bid_card_data'].get('budget_max')}")

                return {
                    "success": True,
                    "bid_card_number": bid_card_number,
                    "bid_card_data": final_state["bid_card_data"],
                    "cia_thread_id": thread_id,
                    "database_id": bid_card_data["id"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create bid card: {create_result['error']}"
                }

        except Exception as e:
            print(f"[INTELLIGENT JAA ERROR] {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }

    def _analyze_conversation(self, state: IntelligentJAAState) -> IntelligentJAAState:
        """Step 1: Analyze conversation with AI to understand project scope"""
        print("[INTELLIGENT JAA] Stage 1: Analyzing conversation with GPT-4...")

        # Extract conversation messages
        conversation_state = state["conversation_data"].get("state", {})
        messages = conversation_state.get("messages", [])
        collected_info = conversation_state.get("collected_info", {})

        # Combine all user messages
        user_messages = []
        for msg in messages:
            if msg.get("role") == "user":
                user_messages.append(msg.get("content", ""))

        full_conversation = "\n".join(user_messages)

        # Create analysis prompt
        analysis_prompt = f"""
You are an expert project analyst for InstaBids, a contractor marketplace.

Analyze this homeowner conversation and provide a detailed understanding of their project:

CONVERSATION:
{full_conversation}

COLLECTED INFO FROM CIA:
{json.dumps(collected_info, indent=2)}

Please analyze and provide:

1. PROJECT UNDERSTANDING:
   - What type of project is this?
   - What is the homeowner's primary goal?
   - What specific work needs to be done?

2. URGENCY & TIMELINE:
   - How urgent is this project?
   - When do they want to start?
   - Any time constraints or deadlines?

3. BUDGET ANALYSIS:
   - What budget range did they mention?
   - Do they seem price-sensitive or quality-focused?
   - Are there any budget constraints?

4. COMPLEXITY ASSESSMENT:
   - Is this a simple or complex project?
   - What challenges might contractors face?
   - Any special requirements or permits needed?

5. HOMEOWNER PROFILE:
   - How serious are they about proceeding?
   - Do they seem well-informed about the project?
   - Any specific preferences or concerns?

Provide your analysis in clear, structured format.
"""

        try:
            response = self._tracked_llm_invoke([
                SystemMessage(content="You are an expert project analyst for InstaBids contractor marketplace."),
                HumanMessage(content=analysis_prompt)
            ], context={"thread_id": state.get("thread_id"), "stage": "analysis"})

            # Store analysis
            state["extracted_data"]["ai_analysis"] = response.content
            state["stage"] = "extraction"

            print("[INTELLIGENT JAA] Conversation analysis complete")
            return state

        except Exception as e:
            state["errors"].append(f"Analysis failed: {e!s}")
            return state

    def _extract_project_data(self, state: IntelligentJAAState) -> IntelligentJAAState:
        """Step 2: Extract structured data points using AI intelligence"""
        print("[INTELLIGENT JAA] Stage 2: Extracting structured data with AI...")

        # Get conversation data
        conversation_state = state["conversation_data"].get("state", {})
        messages = conversation_state.get("messages", [])
        collected_info = conversation_state.get("collected_info", {})

        user_messages = []
        for msg in messages:
            if msg.get("role") == "user":
                user_messages.append(msg.get("content", ""))

        full_conversation = "\n".join(user_messages)

        # Create extraction prompt
        extraction_prompt = f"""
You are a data extraction specialist for InstaBids contractor marketplace.

Extract structured data from this homeowner conversation:

CONVERSATION:
{full_conversation}

COLLECTED INFO:
{json.dumps(collected_info, indent=2)}

PREVIOUS ANALYSIS:
{state["extracted_data"].get('ai_analysis', 'No previous analysis')}

Extract the following data points in JSON format:

{{
  "project_type": "kitchen|bathroom|roofing|flooring|plumbing|electrical|hvac|painting|landscaping|general",
  "service_type": "installation|repair|maintenance|renovation|new_construction",
  "project_description": "Detailed description of work needed",
  "budget_min": integer (minimum budget in dollars),
  "budget_max": integer (maximum budget in dollars),
  "budget_confidence": "high|medium|low",
  "urgency_level": "emergency|urgent|week|month|flexible",
  "timeline_start": "when they want to start",
  "timeline_duration": "expected project duration",
  "location": {{
    "address": "full address if provided",
    "city": "city name",
    "state": "state name",
    "zip_code": "zip code",
    "property_type": "house|condo|apartment|commercial"
  }},
  "materials_specified": ["list of materials mentioned"],
  "special_requirements": ["list of special needs"],
  "homeowner_info": {{
    "name": "homeowner name if provided",
    "email": "email if provided",
    "phone": "phone if provided",
    "communication_preference": "email|phone|text"
  }},
  "contractor_requirements": {{
    "count_needed": integer (3-6 contractors),
    "specialties_required": ["list of required specialties"],
    "license_requirements": ["list of required licenses"]
  }},
  "complexity_factors": ["list of complexity factors"],
  "quality_expectations": "basic|standard|premium",
  "intention_score": integer (1-10, how serious are they)
}}

IMPORTANT:
- Only extract data that is clearly mentioned or strongly implied
- Use null for unknown values
- Be conservative with budget estimates
- Consider urgency carefully based on language used
- Assess intention score based on specificity and commitment level

Return ONLY the JSON, no additional text.
"""

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a data extraction specialist. Return only valid JSON."),
                HumanMessage(content=extraction_prompt)
            ])

            # Clean the response - remove markdown code blocks if present
            response_content = response.content.strip()
            if response_content.startswith("```json"):
                response_content = response_content[7:]  # Remove ```json
            if response_content.endswith("```"):
                response_content = response_content[:-3]  # Remove ```
            response_content = response_content.strip()

            # Parse the JSON response
            extracted_data = json.loads(response_content)
            state["extracted_data"].update(extracted_data)
            state["stage"] = "validation"

            print("[INTELLIGENT JAA] Data extraction complete")
            return state

        except json.JSONDecodeError as e:
            state["errors"].append(f"JSON parsing failed: {e!s}")
            return state
        except Exception as e:
            state["errors"].append(f"Extraction failed: {e!s}")
            return state

    async def _validate_extraction(self, state: IntelligentJAAState) -> IntelligentJAAState:
        """Step 3: Validate extracted data and fill in missing pieces"""
        print("[INTELLIGENT JAA] Stage 3: Validating and enriching data...")

        # Basic validation and defaults
        extracted = state["extracted_data"]

        # Ensure required fields have sensible defaults
        if not extracted.get("project_type"):
            extracted["project_type"] = "general"

        if not extracted.get("budget_min") or extracted["budget_min"] < 100:
            extracted["budget_min"] = 5000

        if not extracted.get("budget_max") or extracted["budget_max"] < extracted["budget_min"]:
            extracted["budget_max"] = max(extracted["budget_min"] * 2, 15000)

        if not extracted.get("urgency_level"):
            extracted["urgency_level"] = "flexible"

        if not extracted.get("contractor_requirements"):
            extracted["contractor_requirements"] = {
                "count_needed": 4,
                "specialties_required": [],
                "license_requirements": []
            }

        # CRITICAL: Categorize project and get contractor_type_ids for BSA matching
        project_description = extracted.get("project_description", "")
        project_type = extracted.get("project_type", "general")
        
        contractor_type_ids = await self._categorize_project_and_populate_contractor_types(
            project_description, project_type
        )
        extracted["contractor_type_ids"] = contractor_type_ids

        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(extracted)
        extracted["complexity_score"] = complexity_score

        state["stage"] = "generation"
        print("[INTELLIGENT JAA] Data validation complete")
        return state

    def _generate_bid_card(self, state: IntelligentJAAState) -> IntelligentJAAState:
        """Step 4: Generate final bid card with all InstaBids-specific data"""
        print("[INTELLIGENT JAA] Stage 4: Generating professional bid card...")

        extracted = state["extracted_data"]

        # Generate final bid card data
        bid_card_data = {
            # Core project info
            "project_type": extracted.get("project_type", "general"),
            "service_type": extracted.get("service_type", "installation"),
            "project_description": extracted.get("project_description", "Project details to be discussed"),

            # Budget and timeline
            "budget_min": extracted.get("budget_min", 5000),
            "budget_max": extracted.get("budget_max", 15000),
            "budget_confidence": extracted.get("budget_confidence", "medium"),
            "urgency_level": extracted.get("urgency_level", "flexible"),
            "timeline_start": extracted.get("timeline_start"),
            "timeline_duration": extracted.get("timeline_duration"),

            # Location
            "location": extracted.get("location", {}),

            # Requirements
            "materials_specified": extracted.get("materials_specified", []),
            "special_requirements": extracted.get("special_requirements", []),

            # Contractor needs
            "contractor_count_needed": extracted.get("contractor_requirements", {}).get("count_needed", 4),
            "specialties_required": extracted.get("contractor_requirements", {}).get("specialties_required", []),
            "license_requirements": extracted.get("contractor_requirements", {}).get("license_requirements", []),
            
            # CRITICAL: contractor_type_ids for BSA matching - populated by GPT-4o categorization
            "contractor_type_ids": extracted.get("contractor_type_ids", []),

            # InstaBids metrics
            "complexity_score": extracted.get("complexity_score", 5),
            "intention_score": extracted.get("intention_score", 7),
            "quality_expectations": extracted.get("quality_expectations", "standard"),

            # Homeowner info
            "homeowner_info": extracted.get("homeowner_info", {}),

            # AI generated insights
            "ai_insights": {
                "project_analysis": state["extracted_data"].get("ai_analysis"),
                "complexity_factors": extracted.get("complexity_factors", []),
                "generated_by": "IntelligentJAA_ClaudeOpus4",
                "generated_at": datetime.now().isoformat()
            }
        }

        state["bid_card_data"] = bid_card_data
        print("[INTELLIGENT JAA] Bid card generation complete")
        return state

    def _calculate_complexity_score(self, extracted_data: dict[str, Any]) -> int:
        """Calculate project complexity score (1-10) using AI-extracted data"""
        score = 5  # Base score

        # Budget impact
        budget_max = extracted_data.get("budget_max", 0)
        if budget_max > 100000:
            score += 4
        elif budget_max > 50000:
            score += 3
        elif budget_max > 25000:
            score += 2
        elif budget_max > 10000:
            score += 1
        elif budget_max < 2000:
            score -= 2

        # Urgency impact
        urgency = extracted_data.get("urgency_level", "flexible")
        if urgency == "emergency":
            score += 3
        elif urgency == "urgent":
            score += 2

        # Special requirements
        special_reqs = extracted_data.get("special_requirements", [])
        score += len(special_reqs)

        # Complexity factors
        complexity_factors = extracted_data.get("complexity_factors", [])
        score += len(complexity_factors) * 0.5

        # License requirements indicate complexity
        license_reqs = extracted_data.get("contractor_requirements", {}).get("license_requirements", [])
        score += len(license_reqs)

        return max(1, min(10, int(score)))

    def _generate_bid_card_number(self) -> str:
        """Generate unique bid card number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"IBC-{timestamp}"  # Intelligent Bid Card prefix

    async def _categorize_project_and_populate_contractor_types(self, project_description: str, project_type: str) -> list[int]:
        """
        Use GPT-4o to categorize project and return contractor_type_ids
        
        Args:
            project_description: Full project description
            project_type: Extracted project type
            
        Returns:
            List of contractor_type_ids for BSA matching
        """
        try:
            categorization_prompt = f"""
You are a project categorization expert for a contractor matching platform.

PROJECT INFO:
- Type: {project_type}
- Description: {project_description}

Your job is to determine which contractor types are needed for this project.

Common contractor type mappings:
- Plumbing work: [33, 207] (plumbing, plumber)
- Electrical work: [48, 208] (electrical, electrician)  
- General construction: [127, 219] (handyman, general contractor)
- HVAC work: [156, 234] (hvac, hvac contractor)
- Roofing: [89, 223] (roofing, roofer)
- Flooring: [67, 198] (flooring, flooring installer)
- Kitchen remodel: [33, 48, 127, 207, 208, 219] (plumbing, electrical, general)
- Bathroom remodel: [33, 48, 127, 207, 208, 219] (plumbing, electrical, general)

Analyze the project and return ONLY a JSON array of contractor type IDs:
[33, 207, 127]

Return ONLY the JSON array, no other text.
"""

            response = self._tracked_llm_invoke([
                SystemMessage(content="You are a contractor categorization specialist. Return only JSON."),
                HumanMessage(content=categorization_prompt)
            ])

            # Clean and parse response
            response_content = response.content.strip()
            if response_content.startswith("```"):
                # Remove code blocks
                lines = response_content.split('\n')
                for line in lines:
                    if line.strip().startswith('['):
                        response_content = line.strip()
                        break

            contractor_type_ids = json.loads(response_content)
            
            if isinstance(contractor_type_ids, list) and all(isinstance(x, int) for x in contractor_type_ids):
                print(f"[JAA CATEGORIZATION] Project categorized with contractor_type_ids: {contractor_type_ids}")
                return contractor_type_ids
            else:
                print("[JAA CATEGORIZATION] Invalid categorization result, using default")
                return [127, 219]  # Default to general contractors
                
        except Exception as e:
            print(f"[JAA CATEGORIZATION] Error in categorization: {e}")
            return [127, 219]  # Default fallback

    async def update_existing_bid_card(self, bid_card_id: str, update_request: dict[str, Any]) -> dict[str, Any]:
        """
        Update existing bid card with intelligent analysis and contractor notifications
        
        Args:
            bid_card_id: The bid card ID to update
            update_request: Update request with conversation context
            
        Returns:
            Complete update result with contractor notification data
        """
        print(f"\n[JAA UPDATE] Processing bid card update: {bid_card_id}")
        
        try:
            # Step 1: Load existing bid card
            try:
                existing_card = self.supabase.table("bid_cards").select("*").eq("id", bid_card_id).execute()
                if not existing_card.data:
                    return {
                        "success": False,
                        "error": f"Bid card {bid_card_id} not found"
                    }
            except Exception as db_error:
                return {
                    "success": False,
                    "error": f"Bid card {bid_card_id} not found"
                }
            
            current_bid_card = existing_card.data[0]
            print(f"[JAA UPDATE] Loaded existing bid card: {current_bid_card.get('project_type', 'unknown')}")
            
            # Step 2: Analyze what needs to be updated using GPT-4
            update_analysis = await self._analyze_bid_card_update(current_bid_card, update_request)
            
            if update_analysis.get("errors"):
                return {
                    "success": False,
                    "error": f"Update analysis failed: {'; '.join(update_analysis['errors'])}"
                }
            
            # Step 3: Apply updates to bid card
            updated_data = update_analysis["updated_bid_card_data"]
            update_result = self.supabase.table("bid_cards").update(updated_data).eq("id", bid_card_id).execute()
            
            if not update_result.data:
                return {
                    "success": False,
                    "error": "Failed to update bid card in database"
                }
            
            # Step 4: Find all affected contractors
            affected_contractors = await self._find_affected_contractors(bid_card_id)
            
            # Step 5: Log the change to audit trail
            await self._log_bid_card_change(
                bid_card_id,
                current_bid_card,
                updated_data,
                update_analysis,
                update_request,
                len(affected_contractors)
            )
            
            # Step 6: Generate notification content using AI
            notification_content = await self._generate_update_notification_content(
                current_bid_card, 
                updated_data, 
                update_analysis["changes_made"],
                update_request
            )
            
            # Step 7: Return complete update package
            result = {
                "success": True,
                "bid_card_id": bid_card_id,
                "update_summary": {
                    "changes_made": update_analysis["changes_made"],
                    "change_summary": update_analysis["change_summary"],
                    "significance_level": update_analysis["significance_level"]
                },
                "affected_contractors": affected_contractors,
                "notification_content": notification_content,
                "next_actions": self._determine_next_actions(update_analysis, affected_contractors),
                "updated_at": datetime.now().isoformat(),
                "updated_by": update_request.get("update_context", {}).get("source_agent", "unknown")
            }
            
            print(f"[JAA UPDATE SUCCESS] Updated bid card with {len(affected_contractors)} contractors to notify")
            return result
            
        except Exception as e:
            print(f"[JAA UPDATE ERROR] {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }

    async def _analyze_bid_card_update(self, current_bid_card: dict[str, Any], update_request: dict[str, Any]) -> dict[str, Any]:
        """Analyze what needs to be updated using GPT-4"""
        print("[JAA UPDATE] Analyzing update requirements with GPT-4...")
        
        update_context = update_request.get("update_context", {})
        conversation_snippet = update_context.get("conversation_snippet", "")
        
        analysis_prompt = f"""
You are analyzing a bid card update for InstaBids contractor marketplace.

CURRENT BID CARD DATA:
Project Type: {current_bid_card.get('project_type', 'unknown')}
Budget: ${current_bid_card.get('budget_min', 0)}-${current_bid_card.get('budget_max', 0)}
Timeline: {current_bid_card.get('urgency_level', 'unknown')}
Location: {current_bid_card.get('location_city', '')}, {current_bid_card.get('location_state', '')}
Requirements: {current_bid_card.get('requirements', [])}

UPDATE REQUEST:
Source Agent: {update_context.get('source_agent', 'unknown')}
User Said: "{conversation_snippet}"
Detected Hints: {update_context.get('detected_change_hints', [])}

TASK: Analyze what specifically changed and provide structured update data.

Return ONLY valid JSON in this exact format:
{{
  "changes_made": [
    {{
      "field": "budget_range|urgency_level|requirements|location|project_type",
      "old_value": "current value",
      "new_value": "new value", 
      "change_type": "increased|decreased|modified|added|removed",
      "change_significance": "major|moderate|minor"
    }}
  ],
  "updated_bid_card_data": {{
    "budget_min": number,
    "budget_max": number,
    "urgency_level": "emergency|urgent|week|month|flexible",
    "requirements": ["array of requirements"],
    "location_city": "string",
    "location_state": "string"
  }},
  "change_summary": "Brief description of what changed",
  "significance_level": "major|moderate|minor",
  "contractors_need_notification": true/false
}}

RULES:
- Only extract changes clearly mentioned or strongly implied
- Be conservative with budget changes
- Map timeline language to urgency levels appropriately
- Include only fields that actually changed in updated_bid_card_data
"""

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are an expert bid card analyst. Return only valid JSON."),
                HumanMessage(content=analysis_prompt)
            ])
            
            # Clean and parse JSON response
            response_content = response.content.strip()
            if response_content.startswith("```json"):
                response_content = response_content[7:-3]
            response_content = response_content.strip()
            
            analysis_result = json.loads(response_content)
            print(f"[JAA UPDATE] Analysis complete: {len(analysis_result.get('changes_made', []))} changes detected")
            
            return analysis_result
            
        except json.JSONDecodeError as e:
            return {"errors": [f"JSON parsing failed: {str(e)}"]}
        except Exception as e:
            return {"errors": [f"Analysis failed: {str(e)}"]}

    async def _find_affected_contractors(self, bid_card_id: str) -> list[dict[str, Any]]:
        """Find all contractors who need notification about this bid card update"""
        print("[JAA UPDATE] Finding affected contractors...")
        
        affected_contractors = []
        
        try:
            # Find contractors via outreach attempts (contractor_leads)
            outreach_attempts = self.supabase.table("contractor_outreach_attempts")\
                .select("contractor_lead_id, channel, status")\
                .eq("bid_card_id", bid_card_id)\
                .execute()
            
            contractor_lead_ids = list(set([attempt["contractor_lead_id"] for attempt in outreach_attempts.data if attempt["contractor_lead_id"]]))
            
            if contractor_lead_ids:
                contractor_leads = self.supabase.table("contractor_leads")\
                    .select("id, company_name, contact_name, email, phone")\
                    .in_("id", contractor_lead_ids)\
                    .execute()
                
                for lead in contractor_leads.data:
                    # Determine engagement status
                    lead_attempts = [a for a in outreach_attempts.data if a["contractor_lead_id"] == lead["id"]]
                    channels = [a["channel"] for a in lead_attempts]
                    
                    affected_contractors.append({
                        "contractor_id": lead["id"],
                        "contractor_type": "contractor_lead",
                        "company_name": lead["company_name"] or "Unknown Company",
                        "contact_name": lead["contact_name"],
                        "email": lead["email"],
                        "phone": lead["phone"],
                        "engagement_status": self._determine_engagement_status(bid_card_id, lead["id"], channels),
                        "channels_used": channels,
                        "requires_notification": True
                    })
            
            # Find contractors via direct bids (contractors table)
            contractor_bids = self.supabase.table("contractor_bids")\
                .select("contractor_id")\
                .eq("bid_card_id", bid_card_id)\
                .execute()
            
            contractor_ids = list(set([bid["contractor_id"] for bid in contractor_bids.data]))
            
            if contractor_ids:
                contractors = self.supabase.table("contractors")\
                    .select("id, company_name, user_id")\
                    .in_("id", contractor_ids)\
                    .execute()
                
                for contractor in contractors.data:
                    affected_contractors.append({
                        "contractor_id": contractor["id"],
                        "contractor_type": "contractor",
                        "company_name": contractor["company_name"] or "Contractor",
                        "contact_name": None,
                        "email": None,  # Would need to get from user profile
                        "phone": None,  # Would need to get from user profile
                        "engagement_status": "has_bid",
                        "channels_used": ["platform"],
                        "requires_notification": True
                    })
            
            print(f"[JAA UPDATE] Found {len(affected_contractors)} affected contractors")
            return affected_contractors
            
        except Exception as e:
            print(f"[JAA UPDATE ERROR] Failed to find contractors: {e}")
            return []

    def _determine_engagement_status(self, bid_card_id: str, contractor_lead_id: str, channels_used: list[str]) -> str:
        """Determine contractor engagement status based on interactions"""
        try:
            # Check if contractor has submitted a bid
            bid_check = self.supabase.table("contractor_bids")\
                .select("id")\
                .eq("bid_card_id", bid_card_id)\
                .eq("contractor_id", contractor_lead_id)\
                .execute()
            
            if bid_check.data:
                return "has_bid"
            
            # Check if contractor has sent messages
            message_check = self.supabase.table("bid_card_messages")\
                .select("id")\
                .eq("bid_card_id", bid_card_id)\
                .eq("sender_type", "contractor")\
                .execute()
            
            # Note: This is a simplified check - in production would need sender_id matching
            if message_check.data:
                return "messaging_only"
            
            # Default to email/form only
            return "email_only" if "email" in channels_used else "form_only"
            
        except Exception:
            return "email_only"

    async def _generate_update_notification_content(
        self, 
        current_bid_card: dict[str, Any], 
        updated_data: dict[str, Any],
        changes_made: list[dict[str, Any]],
        update_request: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate professional notification content using GPT-4"""
        print("[JAA UPDATE] Generating notification content...")
        
        # Create change description
        change_descriptions = []
        for change in changes_made:
            if change["field"] == "budget_range":
                change_descriptions.append(f"Budget {change['change_type']} to ${updated_data.get('budget_min', 0)}-${updated_data.get('budget_max', 0)}")
            elif change["field"] == "urgency_level":
                change_descriptions.append(f"Timeline is now {updated_data.get('urgency_level', 'standard').upper()}")
            elif change["field"] == "requirements":
                change_descriptions.append("Project requirements updated")
            else:
                change_descriptions.append(f"{change['field'].replace('_', ' ').title()} {change['change_type']}")
        
        changes_text = ". ".join(change_descriptions)
        project_type = current_bid_card.get('project_type', 'project').replace('_', ' ').title()
        
        notification_prompt = f"""
Generate a professional contractor notification email for a bid card update.

PROJECT: {project_type}
CHANGES: {changes_text}
CONTEXT: {update_request.get('update_context', {}).get('conversation_snippet', '')}

Create professional notification content in JSON format:
{{
  "subject": "Brief, clear subject line about the update",
  "message_template": "Professional message explaining changes and next steps",
  "urgency_level": "low|medium|high",
  "call_to_action": "Clear action contractor should take"
}}

REQUIREMENTS:
- Professional InstaBids tone
- Clear explanation of changes
- Actionable next steps
- Appropriate urgency level
"""

        try:
            response = self.llm.invoke([
                SystemMessage(content="Generate professional contractor communications."),
                HumanMessage(content=notification_prompt)
            ])
            
            response_content = response.content.strip()
            if response_content.startswith("```json"):
                response_content = response_content[7:-3]
            
            notification_content = json.loads(response_content)
            
            # Add InstaBids branding
            notification_content["sender"] = "InstaBids Project Team"
            notification_content["footer"] = "View updated project details at InstaBids.com"
            
            return notification_content
            
        except Exception as e:
            print(f"[JAA UPDATE] Notification generation failed: {e}")
            # Fallback notification content
            return {
                "subject": f"Project Update: {project_type}",
                "message_template": f"The homeowner has updated their {project_type.lower()} project. {changes_text}. Please review the updated project details.",
                "urgency_level": "medium",
                "call_to_action": "Review Updated Project",
                "sender": "InstaBids Project Team",
                "footer": "View updated project details at InstaBids.com"
            }

    async def _log_bid_card_change(
        self,
        bid_card_id: str,
        current_bid_card: dict[str, Any],
        updated_data: dict[str, Any],
        update_analysis: dict[str, Any],
        update_request: dict[str, Any],
        contractors_affected: int
    ) -> None:
        """Log bid card changes to the audit trail for admin panel tracking"""
        print("[JAA UPDATE] Logging change to audit trail...")
        
        try:
            # Extract update context
            update_context = update_request.get("update_context", {})
            
            # Create before and after state comparison
            before_state = {}
            after_state = {}
            changed_fields = []
            
            # Check for changed fields and capture before/after values
            for change in update_analysis.get("changes_made", []):
                field = change.get("field")
                if field and field in updated_data:
                    changed_fields.append(field)
                    before_state[field] = change.get("old_value")
                    after_state[field] = change.get("new_value")
            
            # Determine change type based on what changed
            change_type = "update"
            if "urgency_level" in changed_fields:
                change_type = "urgency_change"
            elif "budget_min" in changed_fields or "budget_max" in changed_fields:
                change_type = "budget_change"
            elif "status" in changed_fields:
                change_type = "status_change"
            elif len(changed_fields) > 2:
                change_type = "major_update"
            
            # Create the change log entry
            change_log_entry = {
                "bid_card_id": bid_card_id,
                "bid_card_number": current_bid_card.get("bid_card_number", "unknown"),
                "change_type": change_type,
                "changed_fields": changed_fields,
                "before_state": before_state,
                "after_state": after_state,
                "change_summary": update_analysis.get("change_summary", "Bid card updated"),
                "significance_level": update_analysis.get("significance_level", "moderate"),
                "source_agent": update_context.get("source_agent", "unknown"),
                "source_context": update_context,
                "conversation_snippet": update_context.get("conversation_snippet", ""),
                "detected_change_hints": update_context.get("detected_change_hints", []),
                "approval_status": "auto_applied",  # Changes are auto-applied for now
                "contractors_notified": contractors_affected,
                "created_by": f"JAA_Agent_v2.0",
                "session_id": update_context.get("session_id"),
                "request_id": update_context.get("request_id")
            }
            
            # Log to database
            log_result = self.supabase.table("bid_card_change_logs").insert(change_log_entry).execute()
            
            if log_result.data:
                print(f"[JAA UPDATE] Change logged successfully: {change_log_entry['change_type']}")
            else:
                print("[JAA UPDATE] Failed to log change - no data returned")
                
        except Exception as e:
            print(f"[JAA UPDATE ERROR] Failed to log change: {e}")
            # Don't fail the entire update if logging fails
            import traceback
            traceback.print_exc()

    def _determine_next_actions(self, update_analysis: dict[str, Any], affected_contractors: list[dict[str, Any]]) -> list[str]:
        """Determine recommended next actions based on update analysis"""
        actions = ["notify_contractors"]
        
        if update_analysis.get("significance_level") == "major":
            actions.append("update_campaign_priority")
        
        if any(change.get("field") == "urgency_level" for change in update_analysis.get("changes_made", [])):
            actions.append("adjust_contractor_outreach_timing")
        
        if len(affected_contractors) > 5:
            actions.append("batch_notification_processing")
        
        return actions

    def _extract_dates(self, state: IntelligentJAAState) -> IntelligentJAAState:
        """NEW: Extract exact dates from conversation"""
        print("[INTELLIGENT JAA] Stage 2.5: Extracting exact dates with SimpleDateParser...")
        
        try:
            # Get conversation text
            conversation_data = state["conversation_data"]
            conversation_state = conversation_data.get("state", {})
            messages = conversation_state.get("messages", [])
            
            # Combine all conversation text for date extraction
            conversation_text = ""
            for msg in messages:
                if isinstance(msg, dict) and msg.get("content"):
                    conversation_text += f" {msg['content']}"
                elif hasattr(msg, 'content'):
                    conversation_text += f" {msg.content}"
            
            print(f"[INTELLIGENT JAA] Analyzing {len(conversation_text)} characters for date mentions...")
            
            # Use Claude to identify date-related text first
            date_extraction_prompt = SystemMessage(content="""
            You are a date extraction specialist. Find any mentions of deadlines, timelines, or specific dates in this conversation.
            
            Look for patterns like:
            - "by Friday", "before Christmas", "need it done by [date]"
            - "wedding June 15th", "graduation May 20", "party on [date]"
            - Specific dates: "6/15", "June 15", "2025-06-15"
            - Urgency indicators: "ASAP", "urgent", "rush job"
            
            Extract the exact phrases that mention timing or deadlines. Return as JSON:
            {
                "date_phrases": ["exact phrase 1", "exact phrase 2"],
                "urgency_indicators": ["urgent", "ASAP"],
                "context": "brief summary of timeline requirements"
            }
            """)
            
            user_message = HumanMessage(content=f"Conversation text: {conversation_text}")
            
            # Call Claude for initial date phrase extraction
            llm_response = self._tracked_llm_invoke(
                [date_extraction_prompt, user_message],
                context={"stage": "date_extraction", "thread_id": state["thread_id"]}
            )
            
            # Parse Claude's response
            try:
                import json
                date_analysis = json.loads(llm_response.content)
            except:
                date_analysis = {
                    "date_phrases": [conversation_text[:200]],  # Fallback
                    "urgency_indicators": [],
                    "context": "Could not parse AI response"
                }
            
            # Now use SimpleDateParser on each identified phrase
            extracted_dates = {}
            best_confidence = 0.0
            
            for phrase in date_analysis.get("date_phrases", []):
                result = self.date_parser.parse_natural_language_date(phrase)
                
                if result["parsed_date"] and result["confidence"] > best_confidence:
                    extracted_dates = {
                        "project_completion_deadline": result["parsed_date"].date() if result["parsed_date"] else None,
                        "deadline_hard": result["deadline_hard"],
                        "deadline_context": result["deadline_context"],
                        "confidence": result["confidence"]
                    }
                    best_confidence = result["confidence"]
            
            # Calculate bid collection deadline if we have a project deadline
            if extracted_dates.get("project_completion_deadline"):
                urgency = state["extracted_data"].get("urgency_level", "week")
                bid_deadline = self.date_parser.calculate_bid_collection_deadline(
                    datetime.combine(extracted_dates["project_completion_deadline"], datetime.min.time()),
                    urgency
                )
                extracted_dates["bid_collection_deadline"] = bid_deadline.date()
                
                # Override urgency based on deadline proximity
                calculated_urgency = self.date_parser.determine_campaign_duration(
                    datetime.combine(extracted_dates["project_completion_deadline"], datetime.min.time())
                )
                if calculated_urgency != urgency:
                    print(f"[INTELLIGENT JAA] Overriding urgency: {urgency} → {calculated_urgency} (based on deadline)")
                    state["extracted_data"]["urgency_level"] = calculated_urgency
            
            # Add to extracted data
            state["extracted_data"].update(extracted_dates)
            
            if extracted_dates:
                print(f"[INTELLIGENT JAA] Date extraction successful:")
                print(f"  Project deadline: {extracted_dates.get('project_completion_deadline')}")
                print(f"  Bid deadline: {extracted_dates.get('bid_collection_deadline')}")
                print(f"  Hard deadline: {extracted_dates.get('deadline_hard')}")
                print(f"  Context: {extracted_dates.get('deadline_context', 'N/A')[:100]}...")
                print(f"  Confidence: {extracted_dates.get('confidence', 0):.1%}")
            else:
                print("[INTELLIGENT JAA] No specific dates found in conversation")
                
        except Exception as e:
            print(f"[INTELLIGENT JAA] Date extraction error: {e}")
            state["errors"].append(f"Date extraction failed: {e}")
        
        return state


# Test the intelligent agent
if __name__ == "__main__":

    async def test_intelligent_jaa():
        """Test the intelligent JAA with a real conversation"""
        jaa = JobAssessmentAgent()

        # Use a real thread ID from your testing
        test_thread_id = "session_1727644456_test_bathroom_renovation"

        result = await jaa.process_conversation(test_thread_id)

        if result.get("success"):
            print("\nINTELLIGENT JAA Test Passed!")
            print(f"Created bid card: {result['bid_card_number']}")
            print(f"Project type: {result['bid_card_data']['project_type']}")
            print(f"Budget: ${result['bid_card_data']['budget_min']}-${result['bid_card_data']['budget_max']}")
        else:
            print(f"\nINTELLIGENT JAA Test Failed: {result.get('error')}")

    import asyncio
    asyncio.run(test_intelligent_jaa())
