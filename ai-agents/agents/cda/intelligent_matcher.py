"""
Intelligent Contractor Matcher using OpenAI GPT-4
Uses GPT-4 to make nuanced matching decisions
"""
import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


class IntelligentContractorMatcher:
    """LLM-powered contractor matching with real intelligence"""

    def __init__(self, llm_provider: str = "openai"):
        """Initialize with OpenAI only"""
        load_dotenv(override=True)

        self.llm_provider = llm_provider
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = "gpt-4-turbo-preview"
        print("[IntelligentMatcher] Using GPT-4 for matching decisions")

    def analyze_bid_requirements(self, bid_card: dict[str, Any]) -> dict[str, Any]:
        """
        Use LLM to deeply understand what the customer really wants
        """
        bid_document = bid_card.get("bid_document", {})

        prompt = f"""
        Analyze this home improvement project request and extract the TRUE contractor preferences.
        Go beyond keywords - understand what the customer really wants.

        Project Details:
        {json.dumps(bid_document, indent=2)}

        Extract and infer:
        1. Contractor Size Preference:
           - Do they want a small local business (mom & pop)?
           - Are they looking for established medium companies?
           - Do they need large corporate contractors?
           - What clues indicate their preference?

        2. Quality vs Price Balance:
           - Are they price-sensitive or quality-focused?
           - What's their real budget comfort zone?
           - Do they mention "best value" or "cheapest" or "highest quality"?

        3. Communication Style:
           - Do they want personal, friendly service?
           - Are they looking for professional/corporate communication?
           - How important is responsiveness?

        4. Trust Factors:
           - What makes them trust a contractor?
           - Do they value reviews, years in business, certifications?
           - Are they worried about scams?

        5. Hidden Requirements:
           - What are they NOT saying but implying?
           - Any cultural or demographic preferences?
           - Scheduling flexibility needs?

        Return a JSON with your analysis and specific matching criteria.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        analysis = response.choices[0].message.content

        # Parse the LLM's analysis
        try:
            return json.loads(analysis)
        except:
            # If not valid JSON, return the text analysis
            return {"analysis": analysis}

    def score_contractor_match(self,
                              contractor: dict[str, Any],
                              bid_analysis: dict[str, Any],
                              bid_card: dict[str, Any]) -> dict[str, Any]:
        """
        Use LLM to score how well a contractor matches the analyzed requirements
        """
        prompt = f"""
        Score how well this contractor matches the customer's requirements.

        CUSTOMER REQUIREMENTS ANALYSIS:
        {json.dumps(bid_analysis, indent=2)}

        CONTRACTOR DETAILS:
        Company: {contractor.get('company_name')}
        Rating: {contractor.get('google_rating', 'N/A')} ({contractor.get('google_review_count', 0)} reviews)
        Phone: {contractor.get('phone', 'No phone')}
        Website: {contractor.get('website', 'No website')}
        Email: {contractor.get('email', 'No email')}
        Location: {contractor.get('city', '')}, {contractor.get('state', '')} {contractor.get('zip_code', '')}
        Business Types: {contractor.get('google_types', [])}

        PROJECT TYPE: {bid_card.get('project_type', 'Unknown')}
        LOCATION: {bid_card.get('location', {}).get('city', 'Unknown')}

        Consider:
        1. Size Match: Does this contractor's size match what customer wants?
        2. Quality Indicators: Do ratings/reviews match quality expectations?
        3. Professionalism: Does their online presence match communication style preference?
        4. Trust Factors: Do they have the trust indicators customer values?
        5. Specialization: Do they specialize in this type of project?
        6. Red Flags: Any concerns about this contractor?

        Provide:
        - match_score: 0-100 (be thoughtful, not everyone gets 90+)
        - size_assessment: your assessment of contractor size
        - key_strengths: what makes them a good match
        - concerns: any red flags or mismatches
        - recommendation: "perfect_match", "strong_match", "possible_match", "poor_match"
        - reasoning: explain your scoring in human terms

        Return as JSON.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        score_analysis = response.choices[0].message.content

        try:
            score_data = json.loads(score_analysis)
            # Add contractor info to result
            score_data["contractor_id"] = contractor.get("id")
            score_data["contractor_name"] = contractor.get("company_name")
            return score_data
        except:
            return {
                "match_score": 50,
                "error": "Failed to parse LLM response",
                "raw_response": score_analysis
            }

    def rank_and_select_contractors(self,
                                  contractors: list[dict[str, Any]],
                                  bid_card: dict[str, Any],
                                  contractors_needed: int = 5) -> dict[str, Any]:
        """
        Complete intelligent matching process
        """
        print("[IntelligentMatcher] Analyzing bid card requirements...")

        # Step 1: Deeply understand what customer wants
        bid_analysis = self.analyze_bid_requirements(bid_card)
        print(f"[IntelligentMatcher] Customer wants: {bid_analysis.get('contractor_size_preference', 'Unknown')}")

        # Step 2: Score each contractor intelligently
        scored_contractors = []
        for contractor in contractors:
            print(f"[IntelligentMatcher] Scoring {contractor.get('company_name')}...")
            score_result = self.score_contractor_match(contractor, bid_analysis, bid_card)

            # Merge contractor data with scoring
            scored_contractor = {**contractor, **score_result}
            scored_contractors.append(scored_contractor)

        # Step 3: Sort by match score
        scored_contractors.sort(key=lambda x: x.get("match_score", 0), reverse=True)

        # Step 4: Select top matches
        selected = scored_contractors[:contractors_needed]

        return {
            "success": True,
            "bid_analysis": bid_analysis,
            "total_scored": len(scored_contractors),
            "selected_count": len(selected),
            "selected_contractors": selected,
            "all_scores": [
                {
                    "name": c.get("contractor_name"),
                    "score": c.get("match_score"),
                    "recommendation": c.get("recommendation")
                }
                for c in scored_contractors
            ]
        }

    def explain_selection(self, selection_result: dict[str, Any]) -> str:
        """
        Generate human-readable explanation of contractor selection
        """
        selected = selection_result.get("selected_contractors", [])
        bid_analysis = selection_result.get("bid_analysis", {})

        prompt = f"""
        Write a brief explanation for why these contractors were selected for the customer.

        Customer Wanted: {json.dumps(bid_analysis, indent=2)}

        Selected Contractors:
        {json.dumps([{
            'name': c.get('contractor_name'),
            'score': c.get('match_score'),
            'reasoning': c.get('reasoning')
        } for c in selected], indent=2)}

        Write a 2-3 sentence explanation the customer would appreciate.
        Focus on how these contractors match what they're looking for.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content


# Example usage
if __name__ == "__main__":
    # Example bid card
    bid_card = {
        "id": "test-123",
        "project_type": "kitchen remodel",
        "bid_document": {
            "project_overview": {
                "description": "We want to update our kitchen but keep the family feel. Looking for someone we can trust, not a big corporation. Our last contractor was terrible - took forever and overcharged us."
            },
            "budget_information": {
                "budget_min": 8000,
                "budget_max": 12000,
                "notes": "We have some flexibility but want good value"
            }
        },
        "location": {
            "city": "Coconut Creek",
            "state": "FL",
            "zip_code": "33442"
        }
    }

    # Example contractors
    contractors = [
        {
            "id": "1",
            "company_name": "Family Kitchen Specialists",
            "google_rating": 4.7,
            "google_review_count": 34,
            "phone": "(555) 123-4567"
        },
        {
            "id": "2",
            "company_name": "MegaCorp Home Services",
            "google_rating": 4.2,
            "google_review_count": 487,
            "phone": "1-800-KITCHEN"
        }
    ]

    # Test intelligent matching
    matcher = IntelligentContractorMatcher()
    result = matcher.rank_and_select_contractors(contractors, bid_card, contractors_needed=2)

    print("\nINTELLIGENT MATCHING RESULTS:")
    print(json.dumps(result, indent=2))

    # Get explanation
    explanation = matcher.explain_selection(result)
    print(f"\nEXPLANATION FOR CUSTOMER:\n{explanation}")
