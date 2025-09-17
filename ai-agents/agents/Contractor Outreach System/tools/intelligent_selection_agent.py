"""
Intelligent Contractor Selection Agent
Uses Claude/GPT to make smart decisions about which contractors to enrich and select
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import openai
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class IntelligentSelectionAgent:
    """
    AI-powered agent that makes intelligent decisions about contractor selection
    No rigid rules - uses context and patterns to decide
    """
    
    def __init__(self):
        """Initialize with AI clients"""
        # For now, force heuristic selection since API keys are invalid
        self.openai_key = None  # os.getenv("OPENAI_API_KEY")
        self.anthropic_key = None  # os.getenv("ANTHROPIC_API_KEY")
        
        if self.anthropic_key:
            self.claude = Anthropic(api_key=self.anthropic_key)
            self.use_claude = True
            logger.info("Using Claude for intelligent selection")
        elif self.openai_key:
            openai.api_key = self.openai_key
            self.use_claude = False
            logger.info("Using GPT-4 for intelligent selection")
        else:
            logger.warning("Using intelligent heuristic selection")
            self.use_claude = False
    
    async def select_contractors_for_enrichment(self,
                                               google_contractors: List[Dict[str, Any]],
                                               project_context: Dict[str, Any],
                                               target_count: int = 10) -> Dict[str, Any]:
        """
        Intelligently select which contractors to enrich based on Google data
        
        Args:
            google_contractors: List of contractors from Google Places API
            project_context: Project type, urgency, location, size preference
            target_count: How many contractors we need for the campaign
        
        Returns:
            Dict with selected contractors and reasoning
        """
        logger.info(f"[INTELLIGENT SELECTION] Analyzing {len(google_contractors)} contractors")
        
        # Build context for AI
        context = self._build_selection_context(google_contractors, project_context, target_count)
        
        # Get AI decision - try GPT-4 first, then Claude, then heuristics
        decision = None
        if self.openai_key:
            decision = await self._gpt_selection(context)
            if decision.get("error"):
                print(f"GPT-4 selection failed: {decision['error']}, trying Claude...")
                decision = None
        
        if not decision and self.use_claude:
            decision = await self._claude_selection(context)
            if decision.get("error"):
                print(f"Claude selection failed: {decision['error']}, using heuristics...")
                decision = None
        
        if not decision:
            decision = self._heuristic_selection(google_contractors, target_count)
        
        return decision
    
    def _build_selection_context(self, contractors: List[Dict], project: Dict, target: int) -> str:
        """Build context prompt for AI decision"""
        
        # Format contractor list for AI
        contractor_summary = []
        for i, c in enumerate(contractors, 1):
            summary = f"{i}. {c.get('name', 'Unknown')}"
            summary += f"\n   Rating: {c.get('rating', 'N/A')} ({c.get('reviews', 0)} reviews)"
            summary += f"\n   Phone: {c.get('phone', 'N/A')}"
            summary += f"\n   Website: {'Yes' if c.get('website') else 'No'}"
            summary += f"\n   Types: {', '.join(c.get('types', [])[:3])}"
            summary += f"\n   Service Area Business: {c.get('is_service_area_business', False)}"
            contractor_summary.append(summary)
        
        prompt = f"""You are an intelligent contractor selection agent for a home services platform.
        
PROJECT CONTEXT:
- Service Type: {project.get('service_type', 'plumbing')}
- Location: {project.get('location', {}).get('city', '')}, {project.get('location', {}).get('state', '')} {project.get('location', {}).get('zip', '')}
- Urgency: {project.get('urgency', 'standard')}
- Size Preference: {project.get('size_preference', 'any')}
- Target Count: We need {target} contractors for the campaign

CONTRACTOR SIZE CATEGORIES:
- solo_handyman: 1-2 people, <50 reviews typically
- owner_operator: 3-15 people, 50-500 reviews typically, owner's name often in business name
- small_business: 15-50 people, 200-1000 reviews typically, established local presence
- regional_company: 50+ people, 1000+ reviews, multiple locations, corporate structure

YOUR TASK:
Analyze these {len(contractors)} contractors from Google Places and decide:
1. Which ones to investigate further with website enrichment (aim for {int(target * 1.5)} contractors)
2. Initial size category guess based on the Google data
3. Reasoning for each selection

Look for patterns like:
- Owner names in business names (e.g., "Joe's Plumbing") = likely owner_operator
- "Emergency" or "24/7" in name = good for urgent projects
- Review count as size indicator
- Service area businesses might be smaller operations
- Corporate words like "Corp", "LLC", "Group" might indicate larger size

CONTRACTORS TO ANALYZE:
{chr(10).join(contractor_summary)}

Please respond with a JSON structure:
{{
    "selected_for_enrichment": [
        {{
            "index": 1,
            "name": "contractor name",
            "estimated_size": "owner_operator",
            "reason": "45 reviews suggests established owner-operator, name includes owner"
        }}
    ],
    "skipped": [
        {{
            "index": 5,
            "name": "contractor name", 
            "reason": "3000+ reviews indicates corporate chain, too large"
        }}
    ],
    "summary": "Selected X contractors that appear to match project needs..."
}}"""
        
        return prompt
    
    async def _claude_selection(self, context: str) -> Dict[str, Any]:
        """Use Claude for selection"""
        try:
            response = self.claude.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": context
                }]
            )
            
            # Parse Claude's response
            text = response.content[0].text
            
            # Try to extract JSON
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                logger.info(f"[CLAUDE] Selected {len(result.get('selected_for_enrichment', []))} contractors")
                return result
            else:
                logger.error("Could not parse Claude response as JSON")
                return self._parse_text_response(text)
                
        except Exception as e:
            logger.error(f"Claude selection error: {e}")
            return {"error": str(e)}
    
    async def _gpt_selection(self, context: str) -> Dict[str, Any]:
        """Use GPT-4 for selection"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_key)
            response = client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o which is available
                messages=[
                    {"role": "system", "content": "You are an expert contractor selection agent. Respond with valid JSON only."},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            text = response.choices[0].message.content
            # Try to extract JSON
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(text)
            logger.info(f"[GPT-4] Selected {len(result.get('selected_for_enrichment', []))} contractors")
            return result
            
        except Exception as e:
            logger.error(f"GPT selection error: {e}")
            return {"error": str(e)}
    
    def _heuristic_selection(self, contractors: List[Dict], target: int) -> Dict[str, Any]:
        """Fallback heuristic selection if no AI available"""
        logger.info("[HEURISTIC] Using intelligent rule-based selection")
        
        selected = []
        skipped = []
        
        for i, c in enumerate(contractors, 1):
            rating = c.get('rating', 0)
            reviews = c.get('reviews', c.get('userRatingCount', 0))  # Handle both field names
            name = c.get('name', '')
            website = c.get('website', c.get('websiteUri', ''))
            is_sab = c.get('is_service_area_business', c.get('pureServiceAreaBusiness', False))
            
            # Intelligent size estimation based on patterns
            if reviews < 30:
                size = "solo_handyman"
                size_reason = "very few reviews suggests solo operation"
            elif reviews < 150:
                size = "owner_operator"
                size_reason = "moderate reviews, likely owner-operated"
            elif reviews < 500:
                size = "small_business"
                size_reason = "substantial reviews, established small business"
            elif reviews < 1500:
                size = "small_business"
                size_reason = "many reviews but not corporate scale"
            else:
                size = "regional_company"
                size_reason = "massive review count indicates corporate/franchise"
            
            # Check for owner names in business name (owner-operator signal)
            owner_signals = ["Joe", "Mike", "Bob", "John", "Jim", "Tom", "Dave", "Ron", "Bill"]
            has_owner_name = any(signal in name for signal in owner_signals)
            if has_owner_name and reviews < 500:
                size = "owner_operator"
                size_reason = "owner's name in business name"
            
            # Check for corporate signals
            corp_signals = ["Corp", "LLC", "Inc.", "Group", "Services", "Rooter", "Mr."]
            has_corp_signal = any(signal in name for signal in corp_signals)
            if has_corp_signal and reviews > 500:
                size = "regional_company"
                size_reason = "corporate naming with high reviews"
            
            # Selection logic - be more inclusive
            if rating >= 4.5 and reviews >= 25 and reviews <= 1200:
                selected.append({
                    "index": i,
                    "name": name,
                    "estimated_size": size,
                    "reason": f"Rating {rating}, {reviews} reviews - {size_reason}"
                })
            elif rating >= 4.8 and reviews < 25:
                # High rating but new - worth considering
                selected.append({
                    "index": i,
                    "name": name,
                    "estimated_size": "solo_handyman",
                    "reason": f"Excellent rating {rating} but new ({reviews} reviews)"
                })
            else:
                reason = ""
                if rating < 4.5:
                    reason = f"Rating {rating} below 4.5 threshold"
                elif reviews < 25:
                    reason = f"Only {reviews} reviews - too new/unproven"
                elif reviews > 1200:
                    reason = f"{reviews} reviews - likely too large/corporate"
                    
                skipped.append({
                    "index": i,
                    "name": name,
                    "reason": reason
                })
        
        # Sort selected by score (rating * log(reviews))
        import math
        for s in selected:
            idx = s['index'] - 1
            if idx < len(contractors):
                c = contractors[idx]
                rating = c.get('rating', 0)
                reviews = c.get('reviews', c.get('userRatingCount', 1))
                s['score'] = rating * math.log(max(reviews, 1))
        
        selected.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Limit to target * 1.5
        selected = selected[:int(target * 1.5)]
        
        # Remove score from output
        for s in selected:
            s.pop('score', None)
        
        return {
            "selected_for_enrichment": selected,
            "skipped": skipped,
            "summary": f"Intelligent heuristic selection: {len(selected)} contractors selected based on rating, reviews, and name patterns"
        }
    
    async def make_final_selection(self,
                                  enriched_profiles: List[Dict[str, Any]],
                                  project_context: Dict[str, Any],
                                  target_count: int = 10) -> Dict[str, Any]:
        """
        Make final selection from enriched profiles
        
        Args:
            enriched_profiles: Contractors with full 66-field profiles
            project_context: Project requirements
            target_count: How many to select for campaign
        
        Returns:
            Final selected contractors with size labels
        """
        logger.info(f"[FINAL SELECTION] Choosing {target_count} from {len(enriched_profiles)} enriched profiles")
        
        # Build context for final decision
        prompt = self._build_final_selection_prompt(enriched_profiles, project_context, target_count)
        
        # Get AI decision
        if self.use_claude:
            decision = await self._claude_final_selection(prompt)
        elif self.openai_key:
            decision = await self._gpt_final_selection(prompt)
        else:
            decision = self._heuristic_final_selection(enriched_profiles, target_count)
        
        return decision
    
    def _build_final_selection_prompt(self, profiles: List[Dict], project: Dict, target: int) -> str:
        """Build prompt for final selection with enriched data"""
        
        profile_summary = []
        for i, p in enumerate(profiles, 1):
            summary = f"{i}. {p.get('company_name', 'Unknown')}"
            summary += f"\n   Google Rating: {p.get('google_rating', 'N/A')} ({p.get('google_review_count', 0)} reviews)"
            summary += f"\n   Years in Business: {p.get('years_in_business', 'Unknown')}"
            summary += f"\n   Employees: {p.get('employees', 'Unknown')}"
            summary += f"\n   Specialties: {', '.join(p.get('specialties', [])[:3])}"
            summary += f"\n   Certifications: {', '.join(p.get('certifications', [])[:2])}"
            summary += f"\n   Has Contact Form: {p.get('has_contact_form', False)}"
            summary += f"\n   Email: {'Yes' if p.get('email') else 'No'}"
            summary += f"\n   Phone: {'Yes' if p.get('phone') else 'No'}"
            summary += f"\n   AI Summary: {p.get('ai_business_summary', '')[:100]}..."
            profile_summary.append(summary)
        
        prompt = f"""You are making the final contractor selection for a campaign.

PROJECT REQUIREMENTS:
- Service Type: {project.get('service_type', 'plumbing')}
- Location: {project.get('location', {}).get('zip', '')}
- Urgency: {project.get('urgency', 'standard')}
- Size Preference: {project.get('size_preference', 'any')}
- Need: {target} contractors for the campaign

You have {len(profiles)} fully enriched contractor profiles with website data.

FINAL TASK:
1. Select the {target} BEST contractors for this project
2. Assign final size category based on ALL data
3. Provide match score (1-100) for each

ENRICHED PROFILES:
{chr(10).join(profile_summary)}

Respond with JSON:
{{
    "selected_contractors": [
        {{
            "index": 1,
            "name": "contractor name",
            "final_size": "owner_operator",
            "match_score": 85,
            "reason": "15 employees, 10 years in business, perfect size match"
        }}
    ],
    "campaign_ready": true,
    "summary": "Selected {target} contractors..."
}}"""
        
        return prompt
    
    async def _claude_final_selection(self, prompt: str) -> Dict[str, Any]:
        """Claude makes final selection"""
        try:
            response = self.claude.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                temperature=0.2,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            text = response.content[0].text
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"error": "Could not parse response"}
            
        except Exception as e:
            logger.error(f"Claude final selection error: {e}")
            return {"error": str(e)}
    
    async def _gpt_final_selection(self, prompt: str) -> Dict[str, Any]:
        """GPT makes final selection"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_key)
            response = client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o which is available
                messages=[
                    {"role": "system", "content": "You are making final contractor selections. Respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            text = response.choices[0].message.content
            # Try to extract JSON
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return json.loads(text)
            
        except Exception as e:
            logger.error(f"GPT final selection error: {e}")
            return {"error": str(e)}
    
    def _heuristic_final_selection(self, profiles: List[Dict], target: int) -> Dict[str, Any]:
        """Fallback final selection"""
        # Sort by completeness and rating
        scored = []
        for i, p in enumerate(profiles, 1):
            score = 0
            score += min(p.get('google_rating', 0) * 20, 100)
            score += min(p.get('data_completeness', 0), 100)
            if p.get('has_contact_form'):
                score += 10
            if p.get('email'):
                score += 10
                
            scored.append({
                "index": i,
                "name": p.get('company_name'),
                "final_size": self._estimate_size(p),
                "match_score": int(score / 2),
                "reason": "Heuristic scoring"
            })
        
        scored.sort(key=lambda x: x['match_score'], reverse=True)
        
        return {
            "selected_contractors": scored[:target],
            "campaign_ready": True,
            "summary": f"Heuristic selection of top {target} contractors"
        }
    
    def _estimate_size(self, profile: Dict) -> str:
        """Estimate contractor size from profile data"""
        employees = profile.get('employees', 0)
        reviews = profile.get('google_review_count', 0)
        
        if employees:
            if employees <= 2:
                return "solo_handyman"
            elif employees <= 15:
                return "owner_operator"
            elif employees <= 50:
                return "small_business"
            else:
                return "regional_company"
        elif reviews:
            if reviews < 50:
                return "solo_handyman"
            elif reviews < 500:
                return "owner_operator"
            elif reviews < 1000:
                return "small_business"
            else:
                return "regional_company"
        else:
            return "owner_operator"  # Default guess