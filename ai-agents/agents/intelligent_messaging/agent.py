"""
GPT-5 Intelligent Messaging Agent for InstaBids
BUSINESS CRITICAL: This agent is the linchpin preventing contact information sharing
Author: Agent 3 (Homeowner UX)  
Date: February 8, 2025
"""

import asyncio
import base64
import os
import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict, Union

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from openai import AsyncOpenAI
from supabase import Client, create_client

load_dotenv()

# Initialize clients - Force load from .env file to avoid truncated system env vars
from pathlib import Path
# Load from root .env file (moved from ai-agents/.env to root)
env_path = Path(__file__).parent.parent.parent / '.env'  # Go up to root directory
supabase_url = None
supabase_key = None

if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.startswith('SUPABASE_URL='):
                supabase_url = line.split('=', 1)[1].strip()
            elif line.startswith('SUPABASE_ANON_KEY='):
                supabase_key = line.split('=', 1)[1].strip()
                
if not supabase_url or not supabase_key:
    # Fallback to env vars if .env file not found
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(supabase_url, supabase_key)

# Force load the correct OpenAI key from .env file, not system env
from pathlib import Path
# Load from root .env file (moved from ai-agents/.env to root)
env_path = Path(__file__).parent.parent.parent / '.env'  # Go up to root directory
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.startswith('OPENAI_API_KEY='):
                correct_api_key = line.split('=', 1)[1].strip()
                break
else:
    correct_api_key = os.getenv("OPENAI_API_KEY")

openai_client = AsyncOpenAI(
    api_key=correct_api_key
)


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    SYSTEM = "system"
    AGENT_COMMENT = "agent_comment"
    BID_SUBMISSION = "bid_submission"  # 🆕 NEW: Route bid submissions through messaging agent


class SecurityThreat(str, Enum):
    CONTACT_INFO = "contact_info"
    SOCIAL_MEDIA = "social_media"
    EXTERNAL_MEETING = "external_meeting"
    PAYMENT_BYPASS = "payment_bypass"
    PLATFORM_BYPASS = "platform_bypass"


class ProjectScopeChange(str, Enum):
    MATERIAL_CHANGE = "material_change"     # "mulch instead of rocks"
    SIZE_CHANGE = "size_change"             # "actually make it bigger"
    FEATURE_ADDITION = "feature_addition"   # "also add a pergola"
    FEATURE_REMOVAL = "feature_removal"     # "skip the fence"
    TIMELINE_CHANGE = "timeline_change"     # "need it done sooner"
    BUDGET_CHANGE = "budget_change"         # "increase budget to $20k"


class AgentAction(str, Enum):
    BLOCK = "block"
    REDACT = "redact"
    WARN = "warn"
    COMMENT = "comment"
    ALLOW = "allow"


class IntelligentMessageState(TypedDict):
    """Enhanced state for intelligent message processing"""
    # Original message data
    original_content: str
    sender_type: str  # 'homeowner' or 'contractor'
    sender_id: str
    recipient_id: Optional[str]
    bid_card_id: str
    conversation_id: Optional[str]
    message_type: MessageType
    
    # Multimedia content
    attachments: List[Dict[str, Any]]
    image_data: Optional[str]  # Base64 encoded
    image_analysis: Optional[str]
    
    # GPT-5 Analysis Results
    security_analysis: Dict[str, Any]
    threats_detected: List[SecurityThreat]
    agent_decision: AgentAction
    confidence_score: float
    
    # Processed content
    filtered_content: str
    agent_comments: List[Dict[str, Any]]  # Private comments for parties
    homeowner_questions: List[str]
    suggested_actions: List[str]
    
    # Context and intelligence
    project_context: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    contractor_reputation: Optional[Dict[str, Any]]
    
    # 🆕 PROJECT SCOPE CHANGE DETECTION
    scope_changes_detected: List[ProjectScopeChange]
    scope_change_details: Dict[str, Any]
    requires_bid_update: bool
    other_contractors_to_notify: List[str]
    
    # 🆕 BID SUBMISSION PROCESSING
    bid_data: Optional[Dict[str, Any]]  # Original bid submission data
    bid_amount: Optional[float]
    bid_timeline_start: Optional[str]
    bid_timeline_end: Optional[str]
    bid_proposal: Optional[str]
    bid_approach: Optional[str]
    bid_warranty_details: Optional[str]
    bid_proposal_filtered: Optional[str]
    bid_approach_filtered: Optional[str]
    bid_warranty_filtered: Optional[str]
    bid_saved: bool
    bid_id: Optional[str]
    bid_amount: Optional[float]
    bid_timeline_start: Optional[str]
    bid_timeline_end: Optional[str]
    bid_proposal_filtered: Optional[str]  # GPT-4o filtered proposal
    bid_approach_filtered: Optional[str]  # GPT-4o filtered approach
    bid_warranty_filtered: Optional[str]  # GPT-4o filtered warranty
    bid_id: Optional[str]  # Generated after saving to contractor_bids table
    bid_conversation_message: Optional[str]  # Summary message for conversation
    
    # Final routing
    approved_for_delivery: bool
    delivery_instructions: Dict[str, Any]
    follow_up_required: bool


class GPT5SecurityAnalyzer:
    """GPT-5 powered security analysis for all message content"""
    
    def __init__(self):
        self.client = openai_client  # Use the correctly initialized client
    
    async def analyze_message_security(
        self, 
        content: str, 
        sender_type: str,
        project_context: Dict[str, Any],
        conversation_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive GPT-5 analysis of message security
        CRITICAL: This must catch ALL attempts to share contact information
        """
        
        system_prompt = """You are an AI security agent protecting a construction marketplace platform. Your job is CRITICAL to business success.

ABSOLUTE RULES:
1. NO contact information can EVER pass through (phone, email, address, social media)
2. NO external meeting arrangements (coffee, phone calls, site visits without platform)
3. NO payment discussions outside the platform
4. NO attempts to move conversation off-platform

🆕 PROJECT SCOPE CHANGE DETECTION:
You must ALSO detect when conversations indicate project scope changes that might require notifying other contractors:
- Material changes ("mulch instead of rocks", "granite countertops instead of laminate")
- Size changes ("make it bigger", "reduce the size by half")
- Feature additions ("also add a pergola", "include a fence around it")
- Feature removals ("skip the deck", "don't need the stairs")
- Timeline changes ("need it done by next week", "can wait until spring")
- Budget changes ("increase budget to $25k", "need to cut costs")

You must analyze EVERY message with extreme vigilance. Users will try creative methods to bypass filters:
- Spelling out numbers ("five-five-five-one-two-three")  
- Using symbols (5.5.5-1.2.3.4)
- Code words ("Call my office line")
- Embedded contact info in images or documents
- Subtle meeting suggestions ("Let's grab coffee to discuss")

CONTEXT: This is a construction project marketplace. Homeowners post projects, contractors bid. All communication MUST stay on platform for safety, legal protection, and business model.

Respond with detailed analysis including:
1. threats_detected: List of specific security issues found
2. confidence_score: 0-1 confidence in your analysis  
3. explanation: Detailed reasoning
4. recommended_action: BLOCK, REDACT, WARN, or ALLOW
5. suggested_response: What to tell the user if blocked/redacted
6. alternative_message: Safe version if content can be salvaged
7. scope_changes_detected: List of project scope changes identified
8. scope_change_details: Details about each scope change
9. requires_contractor_notification: Whether other contractors should be notified
"""

        user_prompt = f"""
ANALYZE THIS MESSAGE FOR SECURITY THREATS:

Original Message: "{content}"
Sender Type: {sender_type}
Project Context: {project_context.get('project_type', 'unknown')} - ${project_context.get('budget_min', 0)}-${project_context.get('budget_max', 0)}

Conversation History (last 3 messages):
{self._format_conversation_history(conversation_history or [])}

Provide your security analysis in JSON format.
"""

        try:
            # Use GPT-4o as primary model (GPT-5 not available yet)
            models_to_try = ["gpt-4o", "gpt-4o-2024-08-06", "gpt-4o-mini"]
            
            for model_name in models_to_try:
                try:
                    print(f"Attempting to use model: {model_name}")
                    response = await self.client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.1,  # Low temperature for consistency
                        timeout=30  # Add explicit timeout
                    )
                    print(f"✅ Successfully using model: {model_name}")
                    break
                except Exception as model_error:
                    error_msg = str(model_error)
                    print(f"❌ Model {model_name} failed: {error_msg[:100]}")
                    if "model" in error_msg.lower() and model_name != models_to_try[-1]:
                        print(f"Trying next model...")
                        continue
                    elif model_name == models_to_try[-1]:
                        print(f"All models failed. Last error: {error_msg}")
                        raise model_error
            
            result = response.choices[0].message.content
            import json
            return json.loads(result)  # Parse JSON response safely
            
        except Exception as e:
            print(f"GPT-5 Analysis Error: {e}")
            # Fallback to high-security mode if GPT-5 fails
            return self._fallback_analysis(content)
    
    async def analyze_image_content(self, image_data: str, image_format: str = "png") -> Dict[str, Any]:
        """
        Analyze images for embedded contact information using new OpenAI Structured Outputs
        CRITICAL: Uses JSON Schema to force consistent response format
        """
        
        # Define strict JSON schema for contact information detection
        contact_schema = {
            "type": "object",
            "properties": {
                "contact_info_detected": {
                    "type": "boolean",
                    "description": "True if any contact information was found in the image"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Confidence score from 0 to 1"
                },
                "explanation": {
                    "type": "string", 
                    "description": "Brief explanation of what was found or why blocked"
                },
                "phones": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of phone numbers found in image"
                },
                "emails": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "List of email addresses found in image"
                },
                "addresses": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of physical addresses found in image"  
                },
                "social_handles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of social media handles found in image"
                }
            },
            "required": ["contact_info_detected", "confidence", "explanation", "phones", "emails", "addresses", "social_handles"],
            "additionalProperties": False
        }

        try:
            # Try GPT models - prefer newer models that support structured outputs
            models_to_try = ["gpt-4o-2024-08-06", "gpt-4o-mini", "gpt-4o"]
            
            for model_name in models_to_try:
                try:
                    # Use chat completions API with structured outputs (JSON schema)
                    response = await self.client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": "You are analyzing images for contact information. Return your analysis in the exact JSON format specified."},
                            {"role": "user", "content": [
                                {"type": "text", "text": "Analyze this image for contact information like phone numbers, emails, addresses, social media handles. Look carefully at all text in the image. Return your analysis in JSON format with the exact structure: {\"contact_info_detected\": boolean, \"confidence\": number, \"explanation\": string, \"phones\": [strings], \"emails\": [strings], \"addresses\": [strings], \"social_handles\": [strings]}."},
                                {"type": "image_url", "image_url": {"url": f"data:image/{image_format};base64,{image_data}"}}
                            ]}
                        ],
                        response_format={
                            "type": "json_schema",
                            "json_schema": {
                                "name": "contact_analysis",
                                "description": "Analysis of contact information in image", 
                                "schema": contact_schema,
                                "strict": True
                            }
                        }
                    )
                    
                    print(f"Image analysis using model: {model_name}")
                    
                    # Parse structured response - guaranteed to match schema
                    import json
                    result = json.loads(response.choices[0].message.content)
                    
                    # Response is already in the correct format due to structured outputs
                    return result
                    
                except Exception as model_error:
                    if "model" in str(model_error).lower() and model_name != models_to_try[-1]:
                        print(f"Model {model_name} not available for image analysis, trying next...")
                        continue
                    elif model_name == models_to_try[-1]:
                        raise model_error
            
        except Exception as e:
            print(f"Image Analysis Error: {e}")
            return {
                "contact_info_detected": True,  # Conservative - block if unsure
                "confidence": 0.5,
                "explanation": "Image analysis failed - blocking for safety",
                "phones": [],
                "emails": [],
                "addresses": [],
                "social_handles": []
            }
    
    async def analyze_pdf_content(self, pdf_data: str, filename: str = "document.pdf") -> Dict[str, Any]:
        """
        Analyze PDF documents for embedded contact information
        CRITICAL: Extracts text and analyzes for security threats
        """
        
        try:
            import PyPDF2
            import base64
            import io
            
            # Decode base64 PDF data
            pdf_bytes = base64.b64decode(pdf_data)
            pdf_file = io.BytesIO(pdf_bytes)
            
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            extracted_text = ""
            
            for page in pdf_reader.pages:
                try:
                    page_text = page.extract_text()
                    extracted_text += page_text + "\n"
                except Exception as page_error:
                    print(f"Error extracting text from PDF page: {page_error}")
            
            if not extracted_text.strip():
                return {
                    "contact_info_detected": True,  # Conservative - block if can't read
                    "confidence": 0.3,
                    "explanation": "Could not extract text from PDF - blocking for safety",
                    "phones": [],
                    "emails": [],
                    "addresses": [],
                    "social_handles": [],
                    "extracted_text": ""
                }
            
            # Analyze extracted text using GPT-4o
            text_analysis_prompt = f"""
            Analyze this text extracted from a PDF document for contact information:

            FILENAME: {filename}
            EXTRACTED TEXT:
            {extracted_text[:2000]}  

            Look for:
            - Phone numbers (any format)
            - Email addresses
            - Physical addresses
            - Social media handles
            - Meeting requests or off-platform communication attempts

            Return analysis in JSON format with the exact structure:
            {{"contact_info_detected": boolean, "confidence": number, "explanation": string, "phones": [strings], "emails": [strings], "addresses": [strings], "social_handles": [strings]}}
            """
            
            # Use GPT-4o to analyze extracted text
            models_to_try = ["gpt-4o-2024-08-06", "gpt-4o-mini", "gpt-4o"]
            
            for model_name in models_to_try:
                try:
                    response = await self.client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": "You are analyzing PDF text for contact information. Return your analysis in the exact JSON format specified."},
                            {"role": "user", "content": text_analysis_prompt}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.1
                    )
                    
                    print(f"PDF analysis using model: {model_name}")
                    
                    import json
                    result = json.loads(response.choices[0].message.content)
                    result["extracted_text"] = extracted_text[:1000]  # Include sample of text
                    return result
                    
                except Exception as model_error:
                    if "model" in str(model_error).lower() and model_name != models_to_try[-1]:
                        print(f"Model {model_name} not available for PDF analysis, trying next...")
                        continue
                    elif model_name == models_to_try[-1]:
                        raise model_error
            
        except ImportError:
            print("PyPDF2 not installed - install with: pip install PyPDF2")
            return {
                "contact_info_detected": True,
                "confidence": 0.5,
                "explanation": "PDF processing library not available - blocking for safety",
                "phones": [],
                "emails": [],
                "addresses": [],
                "social_handles": [],
                "extracted_text": "PDF processing unavailable"
            }
            
        except Exception as e:
            print(f"PDF Analysis Error: {e}")
            return {
                "contact_info_detected": True,  # Conservative - block if unsure
                "confidence": 0.5,
                "explanation": f"PDF analysis failed: {str(e)} - blocking for safety",
                "phones": [],
                "emails": [],
                "addresses": [],
                "social_handles": [],
                "extracted_text": ""
            }
    
    def _format_conversation_history(self, history: List[Dict[str, Any]]) -> str:
        """Format recent conversation for context"""
        if not history:
            return "No previous messages"
        
        formatted = []
        for msg in history[-3:]:  # Last 3 messages
            sender = msg.get('sender_type', 'unknown')
            content = msg.get('content', '')[:100] + "..." if len(msg.get('content', '')) > 100 else msg.get('content', '')
            formatted.append(f"{sender}: {content}")
        
        return "\n".join(formatted)
    
    def _fallback_analysis(self, content: str) -> Dict[str, Any]:
        """High-security fallback if GPT-5 is unavailable"""
        # Ultra-conservative regex patterns
        contact_patterns = [
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # Phone numbers
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b(?:meet|call|text|email|phone|contact)\b',  # Meeting words
            r'\b\d{1,5}\s+\w+\s+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln)\b',  # Addresses
        ]
        
        threats = []
        for pattern in contact_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                threats.append("contact_info")
        
        return {
            "threats_detected": threats,
            "confidence_score": 0.8,
            "explanation": "Fallback analysis detected potential contact information",
            "recommended_action": "BLOCK" if threats else "ALLOW",
            "suggested_response": "Please keep all communication on the InstaBids platform for your protection.",
            "alternative_message": None
        }


class ProjectContextManager:
    """Loads and manages project context for intelligent decisions"""
    
    async def get_project_context(self, bid_card_id: str) -> Dict[str, Any]:
        """Load comprehensive project context"""
        try:
            # Get bid card details
            bid_card_response = supabase.table("bid_cards").select("*").eq("id", bid_card_id).execute()
            bid_card = bid_card_response.data[0] if bid_card_response.data else {}
            
            # Get contractor count and interactions from unified messaging system
            conversations_response = supabase.table("messages").select("*").eq("bid_card_id", bid_card_id).execute()
            conversations = conversations_response.data or []
            
            # 🆕 Get bid submissions for context
            bid_submissions = await self.get_bid_submissions_for_bid_card(bid_card_id)
            
            return {
                "project_type": bid_card.get("project_type", "unknown"),
                "budget_min": bid_card.get("budget_min", 0),
                "budget_max": bid_card.get("budget_max", 0),
                "urgency_level": bid_card.get("urgency_level", "standard"),
                "contractor_count": len(conversations),
                "project_status": bid_card.get("status", "active"),
                "created_at": bid_card.get("created_at"),
                "conversations": conversations,
                "bid_submissions": bid_submissions,  # 🆕 Add bid context
                "bids_received_count": len(bid_submissions),
                "highest_bid": max((bid["amount"] for bid in bid_submissions), default=0),
                "lowest_bid": min((bid["amount"] for bid in bid_submissions), default=0),
            }
            
        except Exception as e:
            print(f"Error loading project context: {e}")
            return {"error": str(e)}
    
    async def get_bid_submissions_for_bid_card(self, bid_card_id: str) -> List[Dict[str, Any]]:
        """Get all bid submissions for a bid card from contractor_bids table"""
        try:
            # Query contractor_bids table directly
            result = supabase.table("contractor_bids").select("*").eq("bid_card_id", bid_card_id).execute()
            
            bid_submissions = []
            for bid in result.data:
                bid_submissions.append({
                    "contractor_id": bid.get("contractor_id"),
                    "amount": bid.get("amount", 0),
                    "timeline": f"{bid.get('timeline_start', '')} to {bid.get('timeline_end', '')}",
                    "proposal": bid.get("proposal", ""),
                    "approach": bid.get("approach", ""),
                    "warranty": bid.get("warranty_details", ""),
                    "submitted_at": bid.get("submitted_at"),
                    "security_threats": bid.get("additional_data", {}).get("threats_detected", []),
                    "threat_level": "LOW",
                    "bid_id": bid.get("id")
                })
            
            return sorted(bid_submissions, key=lambda x: x.get("submitted_at", ""), reverse=True)
            
        except Exception as e:
            print(f"Error getting bid submissions: {e}")
            return []
    
    async def get_bid_comparison_context(self, bid_card_id: str) -> Dict[str, Any]:
        """Get bid comparison context for homeowner questions"""
        bid_submissions = await self.get_bid_submissions_for_bid_card(bid_card_id)
        
        if not bid_submissions:
            return {"has_bids": False, "message": "No bids received yet"}
        
        amounts = [bid["amount"] for bid in bid_submissions if bid["amount"]]
        
        return {
            "has_bids": True,
            "total_bids": len(bid_submissions),
            "bid_range": f"${min(amounts):,.2f} - ${max(amounts):,.2f}" if amounts else "No amounts",
            "average_bid": sum(amounts) / len(amounts) if amounts else 0,
            "latest_bid_amount": bid_submissions[0]["amount"] if bid_submissions else 0,
            "contractors_submitted": [bid["contractor_id"] for bid in bid_submissions]
        }


class IntelligentSecurityNode:
    """Main GPT-5 powered security analysis node"""
    
    def __init__(self):
        self.analyzer = GPT5SecurityAnalyzer()
        self.context_manager = ProjectContextManager()
    
    async def analyze_security(self, state: IntelligentMessageState) -> IntelligentMessageState:
        """Comprehensive security analysis using GPT-5"""
        
        # Load project context
        state["project_context"] = await self.context_manager.get_project_context(state["bid_card_id"])
        
        # For bid submissions, combine all text fields for analysis
        content_to_analyze = state["original_content"]
        if state["message_type"] == MessageType.BID_SUBMISSION and state.get("bid_data"):
            # Analyze all bid text fields together
            bid_fields = []
            if state.get("bid_proposal"):
                bid_fields.append(f"Proposal: {state['bid_proposal']}")
            if state.get("bid_approach"):
                bid_fields.append(f"Approach: {state['bid_approach']}")
            if state.get("bid_warranty_details"):
                bid_fields.append(f"Warranty: {state['bid_warranty_details']}")
            
            if bid_fields:
                content_to_analyze = state["original_content"] + "\n\n" + "\n".join(bid_fields)
        
        # Analyze text content (including bid fields if applicable)
        security_analysis = await self.analyzer.analyze_message_security(
            content=content_to_analyze,
            sender_type=state["sender_type"],
            project_context=state["project_context"],
            conversation_history=state.get("conversation_history", [])
        )
        
        state["security_analysis"] = security_analysis
        state["confidence_score"] = security_analysis.get("confidence_score", 0.0)
        
        # Analyze image content if present
        if state.get("image_data"):
            image_analysis = await self.analyzer.analyze_image_content(state["image_data"])
            state["image_analysis"] = image_analysis
            
            # Combine text and image threat analysis
            if image_analysis.get("contact_info_detected"):
                state["security_analysis"]["threats_detected"].append("contact_info")
        
        # 🆕 Analyze PDF attachments if present
        if state.get("attachments"):
            for attachment in state["attachments"]:
                if attachment.get("type") == "pdf" and attachment.get("data"):
                    filename = attachment.get("name", "document.pdf")
                    pdf_analysis = await self.analyzer.analyze_pdf_content(
                        attachment["data"], 
                        filename
                    )
                    state[f"pdf_analysis_{attachment.get('id', 'unknown')}"] = pdf_analysis
                    
                    # Combine PDF threat analysis
                    if pdf_analysis.get("contact_info_detected"):
                        state["security_analysis"]["threats_detected"].append("contact_info")
                        print(f"PDF {filename} contains contact info: {pdf_analysis.get('explanation')}")
        
        # Determine threats and action
        threats = security_analysis.get("threats_detected", [])
        
        # Map GPT natural language threats to SecurityThreat enums
        mapped_threats = []
        for threat in threats:
            threat_lower = threat.lower()
            if any(keyword in threat_lower for keyword in ["contact", "email", "phone", "social media", "instagram", "facebook"]):
                mapped_threats.append(SecurityThreat.CONTACT_INFO)
            elif any(keyword in threat_lower for keyword in ["off-platform", "platform", "external", "outside"]):
                mapped_threats.append(SecurityThreat.PLATFORM_BYPASS)
            elif any(keyword in threat_lower for keyword in ["meeting", "coffee", "lunch", "visit"]):
                mapped_threats.append(SecurityThreat.EXTERNAL_MEETING)
            elif any(keyword in threat_lower for keyword in ["payment", "cash", "venmo", "paypal"]):
                mapped_threats.append(SecurityThreat.PAYMENT_BYPASS)
        
        # Remove duplicates
        state["threats_detected"] = list(set(mapped_threats))
        
        # Determine agent action based on mapped threats
        if mapped_threats:
            # REDACT contact info instead of blocking - we want to filter but keep the message
            if SecurityThreat.CONTACT_INFO in mapped_threats:
                state["agent_decision"] = AgentAction.REDACT  # Filter out contact info
            elif SecurityThreat.PLATFORM_BYPASS in mapped_threats:
                state["agent_decision"] = AgentAction.REDACT  # Filter bypass attempts
            elif SecurityThreat.PAYMENT_BYPASS in mapped_threats:
                state["agent_decision"] = AgentAction.BLOCK  # Block payment bypass completely
            else:
                state["agent_decision"] = AgentAction.REDACT
        else:
            state["agent_decision"] = AgentAction.ALLOW
        
        return state


class ScopeChangeDetectionNode:
    """Detects project scope changes and creates homeowner questions"""
    
    async def analyze_scope_changes(self, state: IntelligentMessageState) -> IntelligentMessageState:
        """Analyze message for project scope changes using enhanced handler"""
        
        # Extract scope change data from GPT analysis
        security_analysis = state.get("security_analysis", {})
        scope_changes = security_analysis.get("scope_changes_detected", [])
        scope_details = security_analysis.get("scope_change_details", {})
        
        state["scope_changes_detected"] = scope_changes
        state["scope_change_details"] = scope_details
        state["requires_bid_update"] = len(scope_changes) > 0
        
        # If homeowner is making scope changes, use the enhanced scope change handler
        if (state["sender_type"] == "homeowner" and len(scope_changes) > 0):
            
            try:
                # Import and use the enhanced scope change handler
                from .scope_change_handler import handle_scope_changes
                
                scope_result = await handle_scope_changes(
                    scope_changes=scope_changes,
                    scope_details=scope_details,
                    bid_card_id=state["bid_card_id"],
                    sender_id=state["sender_id"],
                    message_content=state["original_content"]
                )
                
                # Update state with enhanced results
                state["other_contractors_to_notify"] = scope_result.get("other_contractors", [])
                state["scope_change_handler_result"] = scope_result
                
                # Add homeowner-only question if generated
                homeowner_question = scope_result.get("homeowner_question")
                if homeowner_question:
                    if "agent_comments" not in state:
                        state["agent_comments"] = []
                    
                    state["agent_comments"].append({
                        "visible_to": "homeowner",
                        "user_id": state["sender_id"],
                        "content": homeowner_question,
                        "type": "scope_change_question",
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {
                            "scope_changes": scope_changes,
                            "other_contractors": scope_result.get("other_contractors", []),
                            "requires_response": True,
                            "action_type": "confirm_scope_changes"
                        }
                    })
                
            except Exception as e:
                print(f"Error in enhanced scope change handling: {e}")
                # Fallback to basic scope change detection
                state["other_contractors_to_notify"] = []
        
        return state
    
    async def _get_other_contractors(self, bid_card_id: str, current_conversation_id: Optional[str]) -> List[str]:
        """Get list of other contractors involved in this bid card"""
        try:
            # Get all contractor interactions for this bid card from messages table
            conversations = supabase.table("messages").select("sender_id").eq(
                "bid_card_id", bid_card_id
            ).eq("sender_type", "contractor").execute()
            
            other_contractors = []
            unique_contractors = set()
            for conv in conversations.data or []:
                contractor_id = conv.get("sender_id")
                if contractor_id and contractor_id not in unique_contractors:
                    unique_contractors.add(contractor_id)
                    other_contractors.append({
                        "contractor_id": contractor_id,
                        "contractor_alias": f"Contractor {contractor_id[:8]}"
                    })
            
            return other_contractors
            
        except Exception as e:
            print(f"Error getting other contractors: {e}")
            return []
    
    def _create_scope_change_question(self, scope_changes: List[str], scope_details: Dict[str, Any], other_contractors: List[Dict[str, str]]) -> str:
        """Create intelligent question for homeowner about scope changes"""
        
        if not scope_changes or not other_contractors:
            return ""
        
        # Count other contractors
        contractor_count = len(other_contractors)
        contractor_names = [c.get("contractor_alias", "Contractor") for c in other_contractors]
        
        # Create context-aware question based on scope change type
        change_descriptions = []
        for change in scope_changes:
            if change == "material_change":
                change_descriptions.append("material preference changes")
            elif change == "size_change":
                change_descriptions.append("size modifications")
            elif change == "feature_addition":
                change_descriptions.append("additional features")
            elif change == "feature_removal":
                change_descriptions.append("removed features")
            elif change == "timeline_change":
                change_descriptions.append("timeline adjustments")
            elif change == "budget_change":
                change_descriptions.append("budget changes")
        
        changes_text = " and ".join(change_descriptions)
        
        # Create personalized question
        if contractor_count == 1:
            contractor_text = f"{contractor_names[0]}"
        elif contractor_count == 2:
            contractor_text = f"{contractor_names[0]} and {contractor_names[1]}"
        else:
            contractor_text = f"{', '.join(contractor_names[:-1])}, and {contractor_names[-1]}"
        
        question = f"💡 I noticed you mentioned {changes_text} in your conversation. "
        question += f"You have {contractor_count} other contractor{'s' if contractor_count > 1 else ''} "
        question += f"({contractor_text}) who might need to know about these changes to provide accurate bids. "
        question += f"Would you like me to notify them about the updated project scope?"
        
        return question


class AgentCommentNode:
    """Creates private agent comments for specific parties"""
    
    async def create_agent_comments(self, state: IntelligentMessageState) -> IntelligentMessageState:
        """Generate intelligent agent comments based on situation"""
        
        comments = []
        
        if state["agent_decision"] == AgentAction.BLOCK:
            # Comment for the sender
            sender_comment = {
                "visible_to": state["sender_type"],
                "user_id": state["sender_id"],
                "content": f"🤖 Your message was blocked for containing contact information. Please keep all communication on InstaBids for your protection and to ensure the best service.",
                "type": "warning",
                "timestamp": datetime.now().isoformat()
            }
            comments.append(sender_comment)
            
            # Comment for the recipient
            recipient_type = "homeowner" if state["sender_type"] == "contractor" else "contractor"
            recipient_comment = {
                "visible_to": recipient_type,
                "user_id": state.get("recipient_id", "system"),
                "content": f"🤖 The {state['sender_type']} attempted to share contact information. I've redirected them to continue the conversation here on the platform.",
                "type": "info",
                "timestamp": datetime.now().isoformat()
            }
            comments.append(recipient_comment)
        
        elif state["agent_decision"] == AgentAction.REDACT:
            # Explain what was redacted
            redacted_comment = {
                "visible_to": state["sender_type"],
                "user_id": state["sender_id"],
                "content": f"🤖 I've removed some content from your message for safety. The rest of your message has been delivered.",
                "type": "info", 
                "timestamp": datetime.now().isoformat()
            }
            comments.append(redacted_comment)
        
        # Add intelligent project suggestions if appropriate
        if state["sender_type"] == "homeowner" and len(comments) == 0:
            # Check if homeowner could benefit from suggestions
            project_context = state.get("project_context", {})
            if project_context.get("contractor_count", 0) > 3:
                suggestion_comment = {
                    "visible_to": "homeowner",
                    "user_id": state["sender_id"],
                    "content": f"💡 You have {project_context.get('contractor_count')} contractors interested. Would you like me to help you compare their bids or ask them specific questions?",
                    "type": "suggestion",
                    "timestamp": datetime.now().isoformat()
                }
                comments.append(suggestion_comment)
        
        state["agent_comments"] = comments
        return state


class ContentProcessingNode:
    """Process and filter content based on agent decision"""
    
    async def process_content(self, state: IntelligentMessageState) -> IntelligentMessageState:
        """Process content based on security analysis"""
        
        if state["agent_decision"] == AgentAction.BLOCK:
            state["filtered_content"] = ""
            state["approved_for_delivery"] = False
            
            # For bid submissions, block the entire bid
            if state["message_type"] == MessageType.BID_SUBMISSION:
                state["bid_proposal_filtered"] = "[BLOCKED - Contact information detected]"
                state["bid_approach_filtered"] = "[BLOCKED - Contact information detected]"
                state["bid_warranty_filtered"] = "[BLOCKED - Contact information detected]"
            
        elif state["agent_decision"] == AgentAction.REDACT:
            # Use GPT-5 suggested alternative or fall back to regex
            alt_message = state["security_analysis"].get("alternative_message")
            if alt_message:
                state["filtered_content"] = alt_message
            else:
                state["filtered_content"] = self._regex_redact(state["original_content"])
            state["approved_for_delivery"] = True
            
            # For bid submissions, redact individual fields
            if state["message_type"] == MessageType.BID_SUBMISSION:
                if state.get("bid_proposal"):
                    state["bid_proposal_filtered"] = self._regex_redact(state["bid_proposal"])
                if state.get("bid_approach"):
                    state["bid_approach_filtered"] = self._regex_redact(state["bid_approach"])
                if state.get("bid_warranty_details"):
                    state["bid_warranty_filtered"] = self._regex_redact(state["bid_warranty_details"])
            
        else:  # ALLOW
            state["filtered_content"] = state["original_content"]
            state["approved_for_delivery"] = True
            
            # For bid submissions, pass through original content
            if state["message_type"] == MessageType.BID_SUBMISSION:
                state["bid_proposal_filtered"] = state.get("bid_proposal", "")
                state["bid_approach_filtered"] = state.get("bid_approach", "")
                state["bid_warranty_filtered"] = state.get("bid_warranty_details", "")
        
        return state
    
    def _regex_redact(self, content: str) -> str:
        """Fallback regex redaction"""
        patterns = [
            (r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE REMOVED]'),
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL REMOVED]'),
        ]
        
        filtered = content
        for pattern, replacement in patterns:
            filtered = re.sub(pattern, replacement, filtered, flags=re.IGNORECASE)
        
        return filtered


class MessagePersistenceNode:
    """Enhanced message persistence with agent comments"""
    
    async def save_message_and_comments(self, state: IntelligentMessageState) -> IntelligentMessageState:
        """Save message and agent comments to database"""
        
        if not state.get("approved_for_delivery"):
            # Still log blocked messages for analysis
            await self._log_blocked_message(state)
            return state
        
        try:
            # 🆕 Handle bid submission processing
            if state["message_type"] == MessageType.BID_SUBMISSION:
                await self._save_bid_submission(state)
                # Create conversation message about the bid
                state["filtered_content"] = state.get("bid_conversation_message", 
                    f"Contractor submitted bid: ${state.get('bid_amount', 0):,.2f}")
            
            # Save message directly to messages table (unified messaging system)
            print("IntelligentAgent: Saving message to unified messaging system")
            
            message_data = {
                "sender_type": state["sender_type"],
                "sender_id": state["sender_id"],
                "content": state["filtered_content"],
                "content_type": "text",
                "bid_card_id": state["bid_card_id"],
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "original_content": state["original_content"],
                    "content_filtered": len(state.get("threats_detected", [])) > 0,
                    "filter_reasons": [t.value for t in state.get("threats_detected", [])],
                    "message_type": state["message_type"].value,
                    "security_analysis": state.get("security_analysis", {}),
                    "agent_decision": state.get("agent_decision", AgentAction.ALLOW).value,
                    "confidence_score": state.get("confidence_score", 0.0),
                    "messaging_source": "intelligent_messaging_agent"
                }
            }
            
            message_result = supabase.table("messages").insert(message_data).execute()
            message_id = message_result.data[0]["id"] if message_result.data else None
            
            # Save agent comments
            for comment in state.get("agent_comments", []):
                comment_data = {
                    "message_id": message_id,
                    "visible_to_type": comment["visible_to"],
                    "visible_to_id": comment["user_id"],
                    "content": comment["content"],
                    "comment_type": comment["type"],
                    "created_at": comment["timestamp"]
                }
                
                supabase.table("agent_comments").insert(comment_data).execute()
            
            state["message_id"] = message_id
            
        except Exception as e:
            print(f"Error saving message: {e}")
            state["message_id"] = None
        
        return state
    
    async def _log_blocked_message(self, state: IntelligentMessageState):
        """Log blocked messages for security analysis"""
        try:
            log_data = {
                "bid_card_id": state["bid_card_id"],
                "sender_type": state["sender_type"],
                "sender_id": state["sender_id"],
                "original_content": state["original_content"],
                "threats_detected": [t.value for t in state.get("threats_detected", [])],
                "confidence_score": state.get("confidence_score", 0.0),
                "blocked_at": datetime.now().isoformat()
            }
            
            supabase.table("blocked_messages_log").insert(log_data).execute()
            
        except Exception as e:
            print(f"Error logging blocked message: {e}")
    
    async def _save_bid_submission(self, state: IntelligentMessageState):
        """Save filtered bid submission to contractor_bids table"""
        try:
            if not state.get("bid_data"):
                return
                
            # Create bid record with FILTERED content (using GPT-4o intelligent analysis)
            bid_data = {
                "bid_card_id": state["bid_card_id"],
                "contractor_id": state["sender_id"],
                "amount": state.get("bid_amount"),
                "timeline_start": state.get("bid_timeline_start"),
                "timeline_end": state.get("bid_timeline_end"),
                "proposal": state.get("bid_proposal_filtered", state["bid_data"].get("proposal", "")),
                "approach": state.get("bid_approach_filtered", state["bid_data"].get("approach", "")),
                "warranty_details": state.get("bid_warranty_filtered", state["bid_data"].get("warranty_details")),
                "materials_included": state["bid_data"].get("materials_included", False),
                "status": "submitted",
                "allows_messages": True,
                "submitted_at": datetime.now().isoformat(),
                "additional_data": {
                    "filtered_by_intelligent_agent": True,
                    "used_gpt4o": True,
                    "security_analysis": state.get("security_analysis", {}),
                    "threats_detected": [t.value for t in state.get("threats_detected", [])],
                    "agent_decision": state.get("agent_decision", AgentAction.ALLOW).value
                }
            }
            
            bid_result = supabase.table("contractor_bids").insert(bid_data).execute()
            if bid_result.data:
                state["bid_id"] = bid_result.data[0]["id"]
                state["bid_saved"] = True  # Mark bid as successfully saved
                
                # Create conversation message
                timeline_text = ""
                if state.get("bid_timeline_start") and state.get("bid_timeline_end"):
                    timeline_text = f" with timeline {state['bid_timeline_start']} to {state['bid_timeline_end']}"
                    
                state["bid_conversation_message"] = f"💰 Bid Submitted: ${state.get('bid_amount', 0):,.2f}{timeline_text}"
                
        except Exception as e:
            print(f"Error saving bid submission: {e}")


def create_intelligent_messaging_graph() -> StateGraph:
    """Create the enhanced LangGraph workflow"""
    
    # Initialize nodes
    security_node = IntelligentSecurityNode()
    scope_node = ScopeChangeDetectionNode()
    comment_node = AgentCommentNode()
    content_node = ContentProcessingNode()
    persistence_node = MessagePersistenceNode()
    
    # Create workflow
    workflow = StateGraph(IntelligentMessageState)
    
    # Add nodes
    workflow.add_node("analyze_security", security_node.analyze_security)
    workflow.add_node("detect_scope_changes", scope_node.analyze_scope_changes)  # 🆕 NEW NODE
    workflow.add_node("create_comments", comment_node.create_agent_comments)  
    workflow.add_node("process_content", content_node.process_content)
    workflow.add_node("save_message", persistence_node.save_message_and_comments)
    
    # Define enhanced flow with scope change detection
    workflow.add_edge("analyze_security", "detect_scope_changes")
    workflow.add_edge("detect_scope_changes", "create_comments")
    workflow.add_edge("create_comments", "process_content")
    workflow.add_edge("process_content", "save_message")
    workflow.add_edge("save_message", END)
    
    # Set entry point
    workflow.set_entry_point("analyze_security")
    
    return workflow.compile()


# Create the intelligent messaging agent
intelligent_messaging_agent = create_intelligent_messaging_graph()


async def process_intelligent_message(
    content: str,
    sender_type: str,
    sender_id: str,
    bid_card_id: str,
    recipient_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    attachments: List[Dict[str, Any]] = None,
    image_data: Optional[str] = None,
    message_type: MessageType = MessageType.TEXT,
    # 🆕 BID SUBMISSION FIELDS
    bid_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main entry point for intelligent message processing
    BUSINESS CRITICAL: This prevents contact information sharing
    """
    
    initial_state = IntelligentMessageState(
        original_content=content,
        sender_type=sender_type,
        sender_id=sender_id,
        recipient_id=recipient_id,
        bid_card_id=bid_card_id,
        conversation_id=conversation_id,
        message_type=message_type,
        attachments=attachments or [],
        image_data=image_data,
        image_analysis=None,
        security_analysis={},
        threats_detected=[],
        agent_decision=AgentAction.ALLOW,
        confidence_score=0.0,
        filtered_content=content,
        agent_comments=[],
        homeowner_questions=[],
        suggested_actions=[],
        project_context={},
        conversation_history=[],
        contractor_reputation=None,
        # 🆕 NEW SCOPE CHANGE FIELDS
        scope_changes_detected=[],
        scope_change_details={},
        requires_bid_update=False,
        other_contractors_to_notify=[],
        # 🆕 BID SUBMISSION FIELDS
        bid_data=bid_data,
        bid_amount=bid_data.get("amount") if bid_data else None,
        bid_timeline_start=bid_data.get("timeline", "").split(" to ")[0] if bid_data and bid_data.get("timeline") else None,
        bid_timeline_end=bid_data.get("timeline", "").split(" to ")[1] if bid_data and bid_data.get("timeline") and " to " in bid_data.get("timeline", "") else None,
        bid_proposal=bid_data.get("proposal") if bid_data else None,
        bid_approach=bid_data.get("approach") if bid_data else None,
        bid_warranty_details=bid_data.get("warranty_details") if bid_data else None,
        bid_proposal_filtered=None,
        bid_approach_filtered=None,
        bid_warranty_filtered=None,
        bid_saved=False,
        bid_id=None,
        bid_conversation_message=None,
        approved_for_delivery=True,
        delivery_instructions={},
        follow_up_required=False
    )
    
    # Run through the intelligent workflow
    final_state = await intelligent_messaging_agent.ainvoke(initial_state)
    
    return {
        "message_id": final_state.get("message_id"),
        "approved": final_state.get("approved_for_delivery", False),
        "filtered_content": final_state.get("filtered_content", ""),
        "agent_decision": final_state.get("agent_decision", AgentAction.ALLOW).value,
        "threats_detected": [t.value for t in final_state.get("threats_detected", [])],
        "agent_comments": final_state.get("agent_comments", []),
        "confidence_score": final_state.get("confidence_score", 0.0),
        "security_analysis": final_state.get("security_analysis", {}),
        # 🆕 NEW SCOPE CHANGE INFORMATION
        "scope_changes_detected": final_state.get("scope_changes_detected", []),
        "scope_change_details": final_state.get("scope_change_details", {}),
        "requires_bid_update": final_state.get("requires_bid_update", False),
        "other_contractors_to_notify": final_state.get("other_contractors_to_notify", []),
        # 🆕 BID SUBMISSION FIELDS
        "bid_saved": final_state.get("bid_saved", False),
        "bid_id": final_state.get("bid_id"),
        "bid_conversation_message": final_state.get("bid_conversation_message")
    }


# Example usage and testing
if __name__ == "__main__":
    async def test_intelligent_messaging():
        """Test the intelligent messaging agent"""
        
        # Test 1: Contact info sharing attempt
        print("Test 1: Contact info sharing...")
        result1 = await process_intelligent_message(
            content="Hi! I love your project. Can you call me at 555-123-4567 to discuss details?",
            sender_type="contractor",
            sender_id="test-contractor-123",
            bid_card_id="test-bid-card-123"
        )
        
        print(f"Approved: {result1['approved']}")
        print(f"Decision: {result1['agent_decision']}")
        print(f"Threats: {result1['threats_detected']}")
        print(f"Comments: {len(result1['agent_comments'])}")
        print()
        
        # Test 2: Legitimate project discussion
        print("Test 2: Legitimate discussion...")
        result2 = await process_intelligent_message(
            content="I can install the kitchen cabinets for $15,000. The timeline would be 2 weeks. Do you have specific color preferences?",
            sender_type="contractor", 
            sender_id="test-contractor-456",
            bid_card_id="test-bid-card-123"
        )
        
        print(f"Approved: {result2['approved']}")
        print(f"Decision: {result2['agent_decision']}")
        print(f"Filtered content: {result2['filtered_content']}")
        
    # Run tests
    asyncio.run(test_intelligent_messaging())