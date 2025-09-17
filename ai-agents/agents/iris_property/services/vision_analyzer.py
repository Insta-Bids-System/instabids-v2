"""
IRIS Vision Analyzer Service
Uses OpenAI Vision API to detect maintenance issues in property photos
"""

import logging
import base64
from typing import List, Dict, Any, Optional
import openai
import os

logger = logging.getLogger(__name__)

class VisionAnalyzer:
    """Analyzes property photos to detect maintenance issues using OpenAI Vision API"""
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.warning("OPENAI_API_KEY not found, vision analysis will be limited")
            self.client = None
        else:
            self.client = openai.OpenAI(api_key=api_key)
            logger.info("VisionAnalyzer initialized with OpenAI Vision API")
    
    def analyze_property_photo(
        self,
        image_data: str,
        room_type: str,
        user_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a property photo for maintenance issues using OpenAI Vision
        
        Returns:
            Dict with detected issues, severity, and contractor recommendations
        """
        
        if not self.client:
            return self._get_fallback_analysis(room_type, user_message)
        
        try:
            # Prepare the prompt
            prompt = self._create_analysis_prompt(room_type, user_message)
            
            # Ensure image data is properly formatted for OpenAI
            if not image_data.startswith('data:image/'):
                image_data = f"data:image/jpeg;base64,{image_data}"
            
            # Call OpenAI Vision API using new client format
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use vision-capable model
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_data
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            # Parse the response
            analysis_text = response.choices[0].message.content
            return self._parse_analysis_response(analysis_text, room_type)
            
        except Exception as e:
            logger.error(f"OpenAI Vision API error: {e}")
            return self._get_fallback_analysis(room_type, user_message)
    
    def _create_analysis_prompt(self, room_type: str, user_message: Optional[str] = None) -> str:
        """Create analysis prompt for OpenAI Vision"""
        
        base_prompt = f"""
        Analyze this {room_type} photo for maintenance issues that would need contractor work.
        
        Look for:
        - Water damage or stains
        - Cracks in walls, ceiling, or fixtures
        - Damaged or worn flooring
        - Plumbing issues (leaks, rust, mineral buildup)
        - Electrical problems (exposed wires, damaged outlets)
        - Paint or finish problems
        - Structural issues
        - HVAC problems
        - Any safety hazards
        
        For each issue found, provide:
        1. Title (short description)
        2. Description (detailed explanation)
        3. Severity (low/medium/high/urgent)
        4. Contractor type needed (plumbing/electrical/general/painting/flooring/etc)
        5. Estimated urgency
        
        Return your analysis in this JSON format:
        {{
            "detected_issues": [
                {{
                    "title": "Issue Name",
                    "description": "Detailed description",
                    "severity": "medium",
                    "contractor_type": "plumbing",
                    "urgency": "can wait a few weeks"
                }}
            ],
            "contractor_types": ["plumbing", "electrical"],
            "overall_condition": "needs attention",
            "priority_level": "medium"
        }}
        
        If no significant issues are found, return:
        {{
            "detected_issues": [],
            "contractor_types": [],
            "overall_condition": "good",
            "priority_level": "none"
        }}
        """
        
        if user_message:
            base_prompt += f"\n\nUser context: {user_message}"
        
        return base_prompt
    
    def _parse_analysis_response(self, response_text: str, room_type: str) -> Dict[str, Any]:
        """Parse OpenAI response into structured format"""
        
        try:
            # Try to extract JSON from response
            import json
            import re
            
            # Find JSON in response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                analysis = json.loads(json_str)
                
                # Validate structure
                if 'detected_issues' in analysis:
                    return analysis
            
            # If no valid JSON, create fallback
            logger.warning("Could not parse OpenAI response as JSON, using fallback")
            return self._get_fallback_analysis(room_type, None)
            
        except Exception as e:
            logger.error(f"Error parsing OpenAI response: {e}")
            return self._get_fallback_analysis(room_type, None)
    
    def _get_fallback_analysis(self, room_type: str, user_message: Optional[str] = None) -> Dict[str, Any]:
        """Provide fallback analysis when OpenAI API is unavailable"""
        
        logger.info(f"Using fallback analysis for {room_type}")
        
        # Default issues based on room type and user message
        fallback_issues = []
        contractor_types = []
        
        if user_message:
            message_lower = user_message.lower()
            
            # Water-related keywords
            if any(word in message_lower for word in ['leak', 'water', 'drip', 'wet', 'stain']):
                fallback_issues.append({
                    "title": "Potential Water Issue",
                    "description": "Water-related problem mentioned - may need plumbing inspection",
                    "severity": "medium",
                    "contractor_type": "plumbing",
                    "urgency": "should be addressed soon"
                })
                contractor_types.append("plumbing")
            
            # Electrical keywords
            if any(word in message_lower for word in ['outlet', 'switch', 'electrical', 'wire', 'power']):
                fallback_issues.append({
                    "title": "Electrical Issue",
                    "description": "Electrical problem mentioned - may need electrician inspection",
                    "severity": "medium",
                    "contractor_type": "electrical",
                    "urgency": "should be addressed for safety"
                })
                contractor_types.append("electrical")
            
            # Damage keywords
            if any(word in message_lower for word in ['crack', 'damage', 'broken', 'repair', 'fix']):
                fallback_issues.append({
                    "title": "Repair Needed",
                    "description": "Damage or repair issue mentioned",
                    "severity": "medium",
                    "contractor_type": "general",
                    "urgency": "assess and repair as needed"
                })
                contractor_types.append("general")
        
        # If no specific issues, provide generic room-based suggestion
        if not fallback_issues:
            room_contractors = {
                'kitchen': 'general',
                'bathroom': 'plumbing',
                'bedroom': 'general',
                'living_room': 'general',
                'basement': 'general',
                'attic': 'general',
                'garage': 'general'
            }
            
            contractor = room_contractors.get(room_type, 'general')
            fallback_issues.append({
                "title": "General Maintenance Check",
                "description": f"Routine maintenance check recommended for {room_type.replace('_', ' ')}",
                "severity": "low",
                "contractor_type": contractor,
                "urgency": "routine maintenance"
            })
            contractor_types.append(contractor)
        
        return {
            "detected_issues": fallback_issues,
            "contractor_types": list(set(contractor_types)),
            "overall_condition": "needs inspection",
            "priority_level": "medium",
            "fallback_used": True
        }
    
    def get_severity_score(self, severity: str) -> float:
        """Convert severity string to numeric score"""
        severity_map = {
            'low': 0.25,
            'medium': 0.5,
            'high': 0.75,
            'urgent': 1.0
        }
        return severity_map.get(severity.lower(), 0.5)
    
    def group_issues_by_contractor(self, issues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group detected issues by contractor type"""
        
        grouped = {}
        for issue in issues:
            contractor_type = issue.get('contractor_type', 'general')
            if contractor_type not in grouped:
                grouped[contractor_type] = []
            grouped[contractor_type].append(issue)
        
        return grouped