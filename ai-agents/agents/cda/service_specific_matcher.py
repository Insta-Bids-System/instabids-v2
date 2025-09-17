"""
Service-Specific Intelligent Matcher
Uses OpenAI GPT-4 to understand contractor specializations and service requirements
"""
import json
import os
from typing import Any

from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()


class ServiceSpecificMatcher:
    """Intelligent matcher that understands service-level contractor specializations"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.client = OpenAI(api_key=self.api_key)
        print("[ServiceMatcher] Initialized with OpenAI GPT-4")

    def analyze_project_requirements(self, bid_data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze project requirements to understand specific service needs
        
        Returns:
            Dict with project analysis including service type, specialization needs, etc.
        """
        try:
            # Extract project information
            project_type = bid_data.get("project_type", "")

            # Get project description from bid document
            description = ""
            bid_document = bid_data.get("bid_document", {})
            if isinstance(bid_document, dict):
                project_overview = bid_document.get("project_overview", {})
                if isinstance(project_overview, dict):
                    description = project_overview.get("description", "")

            # Also check other description fields
            description += " " + bid_data.get("description", "")
            description += " " + bid_data.get("project_description", "")

            prompt = f"""
Analyze this home improvement project to understand the specific contractor requirements:

PROJECT TYPE: {project_type}
PROJECT DESCRIPTION: {description}

Please analyze and return a JSON response with:
1. "service_category" - The main service category (roofing, plumbing, electrical, etc.)
2. "service_type" - The specific type of service needed (repair, installation, maintenance, etc.)
3. "specialization_required" - Any specific specializations needed
4. "urgency_indicators" - Any urgency signals in the description
5. "quality_preferences" - Any quality/budget preferences mentioned
6. "scope_complexity" - Simple, moderate, or complex based on description
7. "contractor_requirements" - List of specific contractor qualifications needed

Focus on understanding what TYPE of contractor specialization is needed, not just the general category.
"""

            # Call OpenAI GPT-4 API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert contractor matching system that analyzes project requirements and returns structured JSON responses."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1000,
                temperature=0.7
            )

            content = response.choices[0].message.content

            try:
                # Extract JSON from response
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_content = content[json_start:json_end].strip()
                else:
                    # Look for JSON-like content
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    json_content = content[start:end]

                analysis = json.loads(json_content)
                print(f"[ServiceMatcher] Project analysis complete: {analysis.get('service_category', 'Unknown')} - {analysis.get('service_type', 'Unknown')}")
                return analysis

            except json.JSONDecodeError as e:
                print(f"[ServiceMatcher] Could not parse JSON response: {e}")
                print(f"[ServiceMatcher] Raw response: {content}")
                # Return basic fallback analysis
                return {
                    "service_category": project_type,
                    "service_type": "general",
                    "specialization_required": [],
                    "urgency_indicators": [],
                    "quality_preferences": "balanced",
                    "scope_complexity": "moderate",
                    "contractor_requirements": []
                }

        except Exception as e:
            print(f"[ServiceMatcher] Error analyzing project: {e}")
            return self._fallback_analysis(bid_data)

    def score_contractor_match(self, contractor: dict[str, Any], project_analysis: dict[str, Any]) -> dict[str, Any]:
        """
        Score how well a contractor matches the specific project requirements
        
        Returns:
            Dict with match score, reasoning, and specific strengths/concerns
        """
        try:
            # Extract contractor information
            company_name = contractor.get("company_name", "Unknown")
            business_types = contractor.get("google_types", [])
            rating = contractor.get("google_rating", 0)
            review_count = contractor.get("google_review_count", 0)
            website = contractor.get("website", "")
            contractor_size = contractor.get("contractor_size", "unknown")
            contractor_type = contractor.get("contractor_type", "unknown")
            specialties = contractor.get("specialties", [])

            prompt = f"""
Evaluate how well this contractor matches the specific project requirements:

CONTRACTOR INFO:
- Company: {company_name}
- Business Types: {business_types}
- Specialties: {specialties}
- Google Rating: {rating}
- Review Count: {review_count}
- Website: {website}
- Contractor Size: {contractor_size} (solo_handyman, owner_operator, small_business, regional_company, or unknown)
- Contractor Type: {contractor_type}

PROJECT REQUIREMENTS:
- Service Category: {project_analysis.get('service_category', 'Unknown')}
- Service Type: {project_analysis.get('service_type', 'Unknown')}
- Specialization Required: {project_analysis.get('specialization_required', [])}
- Scope Complexity: {project_analysis.get('scope_complexity', 'moderate')}
- Contractor Requirements: {project_analysis.get('contractor_requirements', [])}

Please analyze and return a JSON response with:
1. "match_score" - Score from 0-100 based on specialization match AND contractor size appropriateness
2. "specialization_match" - How well their types match the required service
3. "size_match" - How well their size matches the project needs (solo for small jobs, regional for complex projects)
4. "experience_indicators" - Signs of relevant experience
5. "quality_indicators" - Rating, reviews, and other quality signals
6. "concerns" - Any potential concerns or mismatches (including size mismatches)
7. "key_strengths" - Top 3 reasons why they're a good match
8. "recommendation" - "excellent_match", "good_match", "possible_match", or "poor_match"
9. "reasoning" - Brief explanation of the score including size considerations

Focus on:
- SPECIALTIES MATCH: Compare contractor's specialties array against required service type and specializations
- SERVICE TYPE PRECISION: Match repair vs installation vs maintenance needs
- CONTRACTOR SIZE APPROPRIATENESS (solo handyman for small repairs, regional companies for complex projects)
- Match between project complexity and contractor scale
- Multiple specialties should be considered an advantage for diverse projects
"""

            # Call OpenAI GPT-4 API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert contractor matching system that evaluates contractor-project fit and returns structured JSON responses."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=800,
                temperature=0.7
            )

            content = response.choices[0].message.content

            try:
                # Extract JSON from response
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_content = content[json_start:json_end].strip()
                else:
                    # Look for JSON-like content
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    json_content = content[start:end]

                scoring = json.loads(json_content)
                print(f"[ServiceMatcher] Scored {company_name}: {scoring.get('match_score', 0)} - {scoring.get('recommendation', 'unknown')}")
                return scoring

            except json.JSONDecodeError as e:
                print(f"[ServiceMatcher] Could not parse scoring JSON: {e}")
                return self._fallback_scoring(contractor, project_analysis)

        except Exception as e:
            print(f"[ServiceMatcher] Error scoring contractor: {e}")
            return self._fallback_scoring(contractor, project_analysis)

    def _fallback_analysis(self, bid_data: dict[str, Any]) -> dict[str, Any]:
        """Fallback analysis when API fails"""
        project_type = bid_data.get("project_type", "general")
        return {
            "service_category": project_type,
            "service_type": "general",
            "specialization_required": [],
            "urgency_indicators": [],
            "quality_preferences": "balanced",
            "scope_complexity": "moderate",
            "contractor_requirements": []
        }

    def _fallback_scoring(self, contractor: dict[str, Any], project_analysis: dict[str, Any]) -> dict[str, Any]:
        """Fallback scoring when API fails"""
        # Simple scoring based on basic criteria
        score = 50  # Base score

        rating = contractor.get("google_rating", 0)
        if rating >= 4.5:
            score += 20
        elif rating >= 4.0:
            score += 15
        elif rating >= 3.5:
            score += 10

        review_count = contractor.get("google_review_count", 0)
        if review_count >= 100:
            score += 15
        elif review_count >= 50:
            score += 10
        elif review_count >= 20:
            score += 5

        if contractor.get("website"):
            score += 5

        # Add contractor size consideration in fallback
        contractor_size = contractor.get("contractor_size", "unknown")
        project_complexity = project_analysis.get("scope_complexity", "moderate")

        size_concerns = []
        if contractor_size == "solo_handyman" and project_complexity == "complex":
            score -= 10
            size_concerns.append("Solo contractor may be overwhelmed by complex project")
        elif contractor_size == "regional_company" and project_complexity == "simple":
            score -= 5
            size_concerns.append("Large company may be overkill for simple project")
        elif contractor_size in ["owner_operator", "small_business"]:
            score += 5  # Good middle ground for most projects

        return {
            "match_score": min(score, 100),
            "specialization_match": "moderate",
            "size_match": "moderate" if contractor_size != "unknown" else "unknown",
            "experience_indicators": ["established business"],
            "quality_indicators": [f"Rating: {rating}", f"Reviews: {review_count}"],
            "concerns": ["Limited specialization analysis available"] + size_concerns,
            "key_strengths": ["Local contractor", "Established business", "Customer reviews"],
            "recommendation": "possible_match" if score >= 70 else "poor_match",
            "reasoning": f"Basic scoring based on ratings and reviews (fallback mode). Contractor size: {contractor_size}"
        }


# Test the service-specific matcher
if __name__ == "__main__":
    print("TESTING SERVICE-SPECIFIC MATCHER")
    print("=" * 50)

    matcher = ServiceSpecificMatcher()

    # Test with roofing repair project
    test_bid_data = {
        "project_type": "roofing",
        "bid_document": {
            "project_overview": {
                "description": "I have a leak in my roof after the storm last week. Need emergency repair to fix the damaged shingles and prevent water damage. This is urgent."
            }
        }
    }

    print("Testing project analysis...")
    analysis = matcher.analyze_project_requirements(test_bid_data)
    print(f"Analysis result: {json.dumps(analysis, indent=2)}")

    # Test with mock contractor
    test_contractor = {
        "company_name": "Emergency Roof Repair Pro",
        "google_types": ["roofing_contractor", "general_contractor"],
        "google_rating": 4.7,
        "google_review_count": 156,
        "website": "https://roofrepairpro.com"
    }

    print("\nTesting contractor scoring...")
    scoring = matcher.score_contractor_match(test_contractor, analysis)
    print(f"Scoring result: {json.dumps(scoring, indent=2)}")
