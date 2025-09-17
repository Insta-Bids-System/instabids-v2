"""
Bid Card Generation for JAA
Creates professional contractor bid cards from project information
"""
import json
from datetime import datetime
from typing import Any, Optional
import os

from openai import OpenAI


class BidCardGenerator:
    """Generates professional bid cards for contractors"""

    def __init__(self, openai_client: Optional[OpenAI] = None):
        # If no client is passed, try to create one with the API key
        if openai_client:
            self.client = openai_client
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = OpenAI(api_key=api_key)
                print("[BidCardGenerator] Initialized with OpenAI GPT-4")
            else:
                self.client = None
                print("[BidCardGenerator] No OpenAI API key found, using basic generation")

    async def generate_document(self,
                              project_info: dict[str, Any],
                              urgency_level: str,
                              contractor_count: int,
                              conversation_data: dict[str, Any]) -> dict[str, Any]:
        """Generate complete professional bid card document"""

        print("[BidCardGenerator] Generating professional bid card document")

        # If no API client, generate basic bid card
        if not self.client:
            return self._generate_basic_bid_card(project_info, urgency_level, contractor_count)

        # Generate AI-enhanced bid card with GPT-4
        return await self._generate_ai_bid_card(project_info, urgency_level, contractor_count, conversation_data)

    def _generate_basic_bid_card(self, project_info: dict[str, Any], urgency_level: str, contractor_count: int) -> dict[str, Any]:
        """Generate basic bid card without AI enhancement"""

        return {
            "project_overview": {
                "title": f"{project_info.get('project_type', 'Home Improvement Project')}",
                "description": "Project details extracted from homeowner conversation",
                "location": project_info.get("address", "Location provided by homeowner"),
                "urgency": urgency_level,
                "contractors_needed": contractor_count
            },
            "budget_information": {
                "budget_min": project_info.get("budget_min", 0),
                "budget_max": project_info.get("budget_max", 0),
                "budget_range": f"${project_info.get('budget_min', 0):,} - ${project_info.get('budget_max', 0):,}"
            },
            "timeline": {
                "preferred_start": project_info.get("timeline_start", "To be discussed"),
                "completion_target": project_info.get("timeline_end", "To be discussed"),
                "urgency_level": urgency_level
            },
            "requirements": project_info.get("requirements", {}),
            "specifications": project_info.get("specifications", {}),
            "concerns": project_info.get("concerns", []),
            "homeowner_preferences": project_info.get("preferences", {}),
            "images": len(project_info.get("images", [])),
            "generated_at": datetime.now().isoformat(),
            "format": "basic"
        }

    async def _generate_ai_bid_card(self,
                                  project_info: dict[str, Any],
                                  urgency_level: str,
                                  contractor_count: int,
                                  conversation_data: dict[str, Any]) -> dict[str, Any]:
        """Generate AI-enhanced professional bid card using GPT-4"""

        # Create prompt for GPT-4
        prompt = self._create_bid_card_prompt(project_info, urgency_level, contractor_count, conversation_data)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                max_tokens=2000,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional bid card generator for contractors. Create detailed, professional bid cards from homeowner project information."
                    },
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse GPT-4's response into structured bid card
            bid_card_content = response.choices[0].message.content

            # Enhance basic bid card with AI-generated content
            basic_card = self._generate_basic_bid_card(project_info, urgency_level, contractor_count)

            # Add AI-enhanced sections
            basic_card.update({
                "professional_summary": self._extract_summary_from_ai(bid_card_content),
                "detailed_scope": self._extract_scope_from_ai(bid_card_content),
                "contractor_guidance": self._extract_guidance_from_ai(bid_card_content),
                "ai_enhanced": True,
                "format": "professional"
            })

            return basic_card

        except Exception as e:
            print(f"[BidCardGenerator ERROR] AI generation failed: {e}")
            # Fallback to basic bid card
            return self._generate_basic_bid_card(project_info, urgency_level, contractor_count)

    def _create_bid_card_prompt(self,
                              project_info: dict[str, Any],
                              urgency_level: str,
                              contractor_count: int,
                              conversation_data: dict[str, Any]) -> str:
        """Create prompt for GPT-4 to generate professional bid card"""

        return f"""
Please create a professional contractor bid card based on this homeowner project information:

PROJECT TYPE: {project_info.get('project_type', 'Unknown')}
BUDGET RANGE: ${project_info.get('budget_min', 0):,} - ${project_info.get('budget_max', 0):,}
URGENCY: {urgency_level}
CONTRACTORS NEEDED: {contractor_count}

REQUIREMENTS:
{json.dumps(project_info.get('requirements', {}), indent=2)}

SPECIFICATIONS:
{json.dumps(project_info.get('specifications', {}), indent=2)}

CONCERNS/ISSUES:
{', '.join(project_info.get('concerns', []))}

HOMEOWNER PREFERENCES:
{json.dumps(project_info.get('preferences', {}), indent=2)}

TIMELINE:
Start: {project_info.get('timeline_start', 'Flexible')}
End: {project_info.get('timeline_end', 'Flexible')}

Please provide:
1. PROFESSIONAL SUMMARY: 2-3 sentence overview for contractors
2. DETAILED SCOPE: Comprehensive work description broken into phases
3. CONTRACTOR GUIDANCE: Specific recommendations for bidding on this project

Format as clear, professional content that contractors can use to submit accurate bids.
"""

    def _extract_summary_from_ai(self, ai_content: str) -> str:
        """Extract professional summary from AI response"""
        lines = ai_content.split("\n")
        summary_section = []
        in_summary = False

        for line in lines:
            if "PROFESSIONAL SUMMARY" in line.upper():
                in_summary = True
                continue
            elif line.strip().startswith("2.") or "DETAILED SCOPE" in line.upper():
                break
            elif in_summary and line.strip():
                summary_section.append(line.strip())

        return " ".join(summary_section) if summary_section else "Professional summary generated from homeowner conversation."

    def _extract_scope_from_ai(self, ai_content: str) -> str:
        """Extract detailed scope from AI response"""
        lines = ai_content.split("\n")
        scope_section = []
        in_scope = False

        for line in lines:
            if "DETAILED SCOPE" in line.upper():
                in_scope = True
                continue
            elif line.strip().startswith("3.") or "CONTRACTOR GUIDANCE" in line.upper():
                break
            elif in_scope and line.strip():
                scope_section.append(line.strip())

        return "\n".join(scope_section) if scope_section else "Detailed scope to be discussed with contractor."

    def _extract_guidance_from_ai(self, ai_content: str) -> str:
        """Extract contractor guidance from AI response"""
        lines = ai_content.split("\n")
        guidance_section = []
        in_guidance = False

        for line in lines:
            if "CONTRACTOR GUIDANCE" in line.upper():
                in_guidance = True
                continue
            elif in_guidance and line.strip():
                guidance_section.append(line.strip())

        return "\n".join(guidance_section) if guidance_section else "Standard contractor guidelines apply."
