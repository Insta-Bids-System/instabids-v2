"""
Intelligent Contractor Type Analysis using GPT-4o
Analyzes contractor business profiles and suggests additional contractor types
NO HARDCODED RULES - Pure AI intelligence based on business data
"""

import json
import logging
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class IntelligentContractorAnalyzer:
    """
    Uses GPT-4o to analyze contractor business profiles and suggest additional contractor types
    """
    
    def __init__(self):
        # Use environment variable for API key
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=api_key)
        logger.info("Intelligent Contractor Analyzer initialized with GPT-4o")
    
    async def analyze_and_suggest_contractor_types(
        self,
        contractor_profile: Dict[str, Any],
        current_contractor_types: List[int],
        all_contractor_types: Dict[int, str]
    ) -> Dict[str, Any]:
        """
        Analyze contractor's complete business profile using GPT-4o and suggest additional contractor types
        
        Args:
            contractor_profile: Complete contractor business data
            current_contractor_types: List of current contractor type IDs
            all_contractor_types: Dict mapping ID -> contractor type name
            
        Returns:
            Dict with intelligent suggestions based on business analysis
        """
        try:
            logger.info(f"Starting GPT-4o analysis for contractor profile")
            
            # Get current type names
            current_type_names = [all_contractor_types.get(type_id, f"Type {type_id}") 
                                for type_id in current_contractor_types]
            
            # Build analysis prompt with complete business context
            analysis_prompt = self._build_analysis_prompt(
                contractor_profile, 
                current_type_names, 
                all_contractor_types
            )
            
            # Call GPT-4o for intelligent analysis
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": analysis_prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.3,  # Some creativity but mostly logical
                response_format={"type": "json_object"}
            )
            
            # Parse GPT-4o response
            analysis_result = json.loads(response.choices[0].message.content)
            
            # Convert suggested type names back to IDs
            suggestions = []
            for suggestion in analysis_result.get('suggested_types', []):
                type_name = suggestion.get('type_name')
                reasoning = suggestion.get('reasoning', 'AI analysis suggests this type')
                
                # Find the contractor type ID for this name
                type_id = self._find_contractor_type_id(type_name, all_contractor_types)
                if type_id and type_id not in current_contractor_types:
                    suggestions.append({
                        "contractor_type_id": type_id,
                        "contractor_type_name": type_name,
                        "reason": reasoning,
                        "confidence": suggestion.get('confidence', 'medium')
                    })
            
            return {
                "success": True,
                "analysis_method": "gpt-4o-intelligent",
                "current_contractor_types": current_contractor_types,
                "current_type_names": current_type_names,
                "suggestions": suggestions[:5],  # Top 5 suggestions
                "total_suggestions": len(suggestions),
                "business_analysis": analysis_result.get('business_analysis', ''),
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"GPT-4o returned invalid JSON: {e}")
            return {"success": False, "error": "gpt4o_json_parse_error", "suggestions": []}
        except Exception as e:
            logger.error(f"GPT-4o contractor analysis error: {e}")
            return {"success": False, "error": str(e), "suggestions": []}
    
    def _get_system_prompt(self) -> str:
        """System prompt defining GPT-4o's role as contractor business analyst"""
        return """You are an expert contractor business analyst with 25+ years of construction industry experience.

Your job is to analyze a contractor's complete business profile and intelligently suggest additional contractor types they might offer based on:
- Their business name and description
- Services they currently provide
- Their specialties and expertise
- Years in business and experience level
- Equipment and capabilities mentioned
- Business size and scope

ANALYSIS APPROACH:
1. Understand their core business from the profile data
2. Consider what related services businesses like theirs typically offer
3. Look for clues about additional capabilities (equipment, certifications, experience)
4. Think about natural business expansions and synergies
5. Consider seasonal vs year-round service patterns

IMPORTANT RULES:
- Base suggestions ONLY on evidence in their business profile
- Don't suggest unrelated types (don't suggest plumbing for a landscaper unless they mention it)
- Consider business size - small contractors might do multiple related services
- Think about logical business combinations (lighting + electrical, landscaping + irrigation)
- Prioritize suggestions with higher confidence based on business evidence

OUTPUT FORMAT: Return JSON with suggested contractor types and detailed reasoning.
"""
    
    def _build_analysis_prompt(
        self, 
        contractor_profile: Dict[str, Any],
        current_type_names: List[str],
        all_contractor_types: Dict[int, str]
    ) -> str:
        """Build the analysis prompt with complete contractor context"""
        
        # Get available contractor type names for context
        available_types = list(all_contractor_types.values())
        
        # Create focused list of relevant types based on current contractor profile
        relevant_keywords = []
        company_name = contractor_profile.get('company_name', '').lower()
        
        # Safely join list fields as strings
        services_list = contractor_profile.get('services', [])
        services = ' '.join([str(s) for s in services_list]).lower() if services_list else ''
        
        specialties_list = contractor_profile.get('specialties', [])
        specialties = ' '.join([str(s) for s in specialties_list]).lower() if specialties_list else ''
        
        business_text = f"{company_name} {services} {specialties}".lower()
        
        # Identify relevant keywords from business profile
        if 'lighting' in business_text:
            relevant_keywords.extend(['lighting', 'voltage', 'electrical', 'led'])
        if 'event' in business_text:
            relevant_keywords.extend(['event', 'audio', 'visual', 'equipment'])
        if 'landscape' in business_text or 'lawn' in business_text:
            relevant_keywords.extend(['landscape', 'lawn', 'turf', 'irrigation'])
        if 'holiday' in business_text:
            relevant_keywords.extend(['seasonal', 'decorat', 'display'])
        
        # No longer needed - we'll show ALL contractor types
        
        # Safely convert all list fields to strings
        services = contractor_profile.get('services', [])
        services_str = ', '.join([str(s) for s in services]) if services else 'None specified'
        
        specialties = contractor_profile.get('specialties', [])
        specialties_str = ', '.join([str(s) for s in specialties]) if specialties else 'None specified'
        
        certifications = contractor_profile.get('certifications', [])
        certifications_str = ', '.join([str(c) for c in certifications]) if certifications else 'None specified'
        
        competitive_advantages = contractor_profile.get('competitive_advantages', [])
        competitive_advantages_str = ', '.join([str(c) for c in competitive_advantages]) if competitive_advantages else 'None specified'
        
        prompt = f"""CONTRACTOR BUSINESS ANALYSIS REQUEST

CONTRACTOR PROFILE:
Company Name: {contractor_profile.get('company_name', 'Unknown')}
Business Description: {contractor_profile.get('ai_business_summary', contractor_profile.get('ai_capability_description', 'No description'))}
Services: {services_str}
Specialties: {specialties_str}
Years in Business: {contractor_profile.get('years_in_business', 'Unknown')}
Capabilities: {contractor_profile.get('capabilities', 'Unknown')}
Equipment/Capabilities: {competitive_advantages_str}

CURRENT CONTRACTOR TYPES:
{', '.join(current_type_names)}

ALL AVAILABLE CONTRACTOR TYPES ({len(all_contractor_types)} total):
{', '.join([f'{name}={str(id)}' for id, name in all_contractor_types.items()])}

TASK: Analyze this contractor's business profile and suggest additional contractor types they might realistically offer.

Look for evidence in their:
- Business name and description
- Listed services and specialties  
- Years of experience and business size
- Certifications and competitive advantages
- Natural business synergies and expansions

Return your analysis as JSON:
{{
  "business_analysis": "Brief analysis of their core business and capabilities",
  "suggested_types": [
    {{
      "type_name": "Exact contractor type name from available list",
      "reasoning": "Specific evidence from their profile supporting this suggestion",
      "confidence": "high/medium/low"
    }}
  ]
}}

Focus on types they could realistically add based on their existing business profile evidence."""
        
        return prompt
    
    def _find_contractor_type_id(self, type_name: str, all_contractor_types: Dict[int, str]) -> Optional[int]:
        """Find contractor type ID by name (case-insensitive)"""
        type_name_lower = type_name.lower().strip()
        
        for type_id, name in all_contractor_types.items():
            if name.lower().strip() == type_name_lower:
                return type_id
        
        # Try partial matching if exact match fails
        for type_id, name in all_contractor_types.items():
            if type_name_lower in name.lower() or name.lower() in type_name_lower:
                return type_id
                
        logger.warning(f"Could not find contractor type ID for: {type_name}")
        return None

# Async wrapper function for subagent compatibility
async def intelligent_contractor_type_analysis(
    contractor_profile: Dict[str, Any],
    current_contractor_types: List[int],
    all_contractor_types: Dict[int, str]
) -> Dict[str, Any]:
    """
    Async wrapper for intelligent contractor type analysis
    """
    try:
        analyzer = IntelligentContractorAnalyzer()
        return await analyzer.analyze_and_suggest_contractor_types(
            contractor_profile, 
            current_contractor_types, 
            all_contractor_types
        )
    except Exception as e:
        logger.error(f"Intelligent contractor analysis error: {e}")
        return {
            "success": False,
            "error": str(e),
            "suggestions": [],
            "analysis_method": "gpt-4o-failed"
        }