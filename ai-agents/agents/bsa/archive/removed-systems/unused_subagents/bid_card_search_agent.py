"""
Bid Card Search Sub-Agent - DeepAgents Framework
Specialized sub-agent for searching and analyzing existing bid cards to provide insights
Integrates with the complete 41-table bid card ecosystem for comprehensive analysis
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import logging
import os
from dataclasses import dataclass

from database import SupabaseDB
# Removed DeepAgents dependency - using standard Python class instead
# from deepagents.sub_agent import SubAgent  
# from deepagents.state import DeepAgentState
from openai import AsyncOpenAI
from utils.radius_search_fixed import get_zip_codes_in_radius, calculate_distance_miles

logger = logging.getLogger(__name__)

@dataclass
class BidCardMatch:
    """Structured bid card match result"""
    bid_card_id: str
    project_type: str
    similarity_score: float
    budget_range: Dict[str, int]
    timeline: str
    location: str
    contractor_count: int
    status: str
    success_rate: float
    insights: List[str]

@dataclass
class ContractorFitAnalysis:
    """Contractor fit analysis for specific project"""
    contractor_id: str
    fit_score: float
    specialty_match: float
    experience_match: float
    location_match: float
    capacity_score: float
    recommendations: List[str]

class BidCardSearchAgent:
    """
    Bid Card Search Sub-Agent specializing in finding similar projects and providing insights
    
    Capabilities:
    1. Semantic search through existing bid cards
    2. Contractor suitability analysis 
    3. Market trend identification
    4. Success rate prediction
    5. Competitive positioning analysis
    """
    
    def __init__(self):
        self.name = "bid-card-search"
        self.description = "Searches existing bid cards for similar projects and provides competitive insights with semantic matching"
        self.version = "2.0.0"
        self.db = SupabaseDB()
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    async def execute(self, state: Dict[str, Any], task_description: str) -> Dict[str, Any]:
        """
        Execute bid card search and analysis
        
        Args:
            state: State dictionary with conversation context
            task_description: Specific search task from main agent
            
        Returns:
            Comprehensive bid card analysis with recommendations
        """
        try:
            # Extract search parameters from task description and state
            search_params = await self._extract_search_parameters(task_description, state)
            
            # Perform multi-dimensional bid card search
            similar_cards = await self._search_similar_bid_cards(search_params)
            
            # Analyze contractor fit for found projects
            contractor_analysis = await self._analyze_contractor_fit(
                search_params.get("contractor_id"),
                similar_cards,
                search_params
            )
            
            # Generate market insights from search results
            market_insights = await self._generate_market_insights(similar_cards, search_params)
            
            # Create actionable recommendations
            recommendations = await self._create_recommendations(
                similar_cards,
                contractor_analysis,
                market_insights,
                search_params
            )
            
            # Format results for main agent
            results = {
                "sub_agent": "bid-card-search",
                "search_params": search_params,
                "similar_projects": [self._format_bid_card_match(card) for card in similar_cards],
                "contractor_fit_analysis": contractor_analysis,
                "market_insights": market_insights,
                "recommendations": recommendations,
                "confidence_score": await self._calculate_confidence_score(similar_cards),
                "search_metadata": {
                    "total_cards_analyzed": len(similar_cards),
                    "search_time": datetime.now().isoformat(),
                    "search_algorithm": "semantic_similarity_v2",
                    "data_sources": ["bid_cards", "contractor_leads", "campaign_history"]
                }
            }
            
            # Update state with search context for future use
            await self._update_search_context(state, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Bid card search agent error: {e}")
            return {
                "sub_agent": "bid-card-search",
                "error": str(e),
                "fallback_recommendations": await self._get_fallback_recommendations()
            }
    
    async def _extract_search_parameters(self, task_description: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize search parameters from task and conversation state"""
        
        # Start with task description analysis
        params = {
            "task_description": task_description,
            "project_type": None,
            "budget_range": None,
            "timeline": None,
            "location": None,
            "contractor_id": None,
            "urgency_level": "standard",
            "specific_requirements": []
        }
        
        # Extract from conversation state (CIA agent context)
        if hasattr(state, 'conversation_memory') and state.conversation_memory:
            memory = state.conversation_memory
            
            params.update({
                "project_type": memory.get("project_type"),
                "budget_range": memory.get("budget_range"),
                "timeline": memory.get("timeline"),
                "location": memory.get("location"),
                "urgency_level": memory.get("urgency_level", "standard"),
                "homeowner_preferences": memory.get("homeowner_preferences", {}),
                "specific_requirements": memory.get("specific_requirements", [])
            })
        
        # Extract contractor ID from current session
        if hasattr(state, 'contractor_id'):
            params["contractor_id"] = state.contractor_id
        
        # Parse task description for specific search intent
        task_lower = task_description.lower()
        
        # Identify search intent
        if "similar" in task_lower or "compare" in task_lower:
            params["search_intent"] = "similarity"
        elif "competitive" in task_lower or "pricing" in task_lower:
            params["search_intent"] = "competitive_analysis"
        elif "success" in task_lower or "rate" in task_lower:
            params["search_intent"] = "success_prediction"
        else:
            params["search_intent"] = "general_insights"
        
        return params
    
    async def _search_similar_bid_cards(self, search_params: Dict[str, Any]) -> List[BidCardMatch]:
        """
        Perform comprehensive bid card search - simplified for working implementation
        """
        try:
            similar_cards = []
            
            # Simple direct search for bid cards
            location = search_params.get("location", {})
            zip_code = location.get("zip", "33442")
            
            # Use the search method that actually works
            search_result = await self.search_bid_cards_in_radius(
                contractor_zip=zip_code,
                radius_miles=30,
                project_type=search_params.get("project_type"),
                use_semantic_matching=False  # Start simple
            )
            
            if not search_result.get("success"):
                return []
                
            raw_cards = search_result.get("bid_cards", [])
            
            # Use intelligent semantic matching instead of simple similarity
            semantic_results = await self._intelligent_semantic_matching(
                contractor_search=search_params.get("task_description", ""),
                bid_cards=raw_cards,
                contractor_specialties=search_params.get("contractor_specialties", [])
            )
            
            # Convert semantic results to BidCardMatch objects
            for card in semantic_results.get("matched_cards", []):
                match_info = card.get("match_info", {})
                similarity_score = match_info.get("relevance_score", 0) / 100.0  # Convert to 0-1 scale
                
                if similarity_score > 0.6:  # Higher threshold for semantic matching
                    bid_match = BidCardMatch(
                        bid_card_id=card["id"],
                        project_type=card["project_type"],
                        similarity_score=similarity_score,
                        budget_range={
                            "min": card["budget_min"] or 0,
                            "max": card["budget_max"] or 0
                        },
                        timeline=card["timeline"] or "Not specified",
                        location=f"{card['location_city']}, {card['location_state']}" if card["location_city"] else "Location not specified",
                        contractor_count=card["contractor_count_needed"] or 0,
                        status=card["status"],
                        success_rate=await self._calculate_project_success_rate(card),
                        insights=await self._generate_project_insights(card, search_params)
                    )
                    
                    similar_cards.append(bid_match)
            
            # Add borderline matches with lower confidence
            for card in semantic_results.get("borderline_cards", []):
                match_info = card.get("match_info", {})
                similarity_score = match_info.get("relevance_score", 0) / 100.0
                
                if similarity_score > 0.4:  # Borderline threshold
                    bid_match = BidCardMatch(
                        bid_card_id=card["id"],
                        project_type=card["project_type"],
                        similarity_score=similarity_score,
                        budget_range={
                            "min": card.get("budget_min", 0),
                            "max": card.get("budget_max", 0)
                        },
                        timeline=card.get("timeline", "TBD"),
                        location=f"{card.get('location_city', 'Unknown')}, {card.get('location_state', '')}",
                        contractor_count=card.get("contractor_count_needed", 1),
                        status=card.get("status", "unknown"),
                        success_rate=0.5,  # Default for borderline
                        insights=[
                            f"Borderline match: {match_info.get('match_reason', 'May be relevant')}",
                            f"Question: {match_info.get('clarifying_question', 'Consider if this fits your needs')}"
                        ]
                    )
                    similar_cards.append(bid_match)
            
            # Sort by similarity score and return top matches
            similar_cards.sort(key=lambda x: x.similarity_score, reverse=True)
            return similar_cards[:10]  # Return top 10 matches
            
        except Exception as e:
            logger.error(f"Bid card search error: {e}")
            return []
    
    async def _calculate_similarity_score(self, card: Dict, search_params: Dict) -> float:
        """Calculate similarity score between bid card and search parameters"""
        score = 0.0
        
        # Project type similarity (weight: 0.4)
        if search_params.get("project_type") and card.get("project_type"):
            project_similarity = await self._calculate_project_type_similarity(
                search_params["project_type"], 
                card["project_type"]
            )
            score += project_similarity * 0.4
        
        # Budget range similarity (weight: 0.3)
        if search_params.get("budget_range") and (card.get("budget_min") or card.get("budget_max")):
            budget_similarity = await self._calculate_budget_similarity(
                search_params["budget_range"],
                {"min": card.get("budget_min"), "max": card.get("budget_max")}
            )
            score += budget_similarity * 0.3
        
        # Location similarity (weight: 0.2)
        if search_params.get("location") and card.get("location_city"):
            location_similarity = await self._calculate_location_similarity(
                search_params["location"],
                f"{card.get('location_city')}, {card.get('location_state')}"
            )
            score += location_similarity * 0.2
        
        # Timeline similarity (weight: 0.1)
        if search_params.get("timeline") and card.get("timeline"):
            timeline_similarity = await self._calculate_timeline_similarity(
                search_params["timeline"],
                card["timeline"]
            )
            score += timeline_similarity * 0.1
        
        return min(1.0, score)
    
    async def _calculate_project_type_similarity(self, search_type: str, card_type: str) -> float:
        """Calculate semantic similarity between project types"""
        # Exact match
        if search_type.lower() == card_type.lower():
            return 1.0
        
        # Category-based similarity mapping
        similarity_map = {
            "kitchen": ["kitchen", "remodel", "renovation", "cabinet", "appliance"],
            "bathroom": ["bathroom", "bath", "shower", "toilet", "vanity"],
            "landscaping": ["landscaping", "lawn", "garden", "outdoor", "yard", "patio"],
            "electrical": ["electrical", "wiring", "lighting", "power", "outlet"],
            "plumbing": ["plumbing", "pipe", "water", "drain", "fixture"],
            "flooring": ["flooring", "floor", "carpet", "tile", "hardwood"],
            "roofing": ["roofing", "roof", "shingle", "gutter"],
            "painting": ["painting", "paint", "color", "interior", "exterior"]
        }
        
        search_lower = search_type.lower()
        card_lower = card_type.lower()
        
        for category, keywords in similarity_map.items():
            search_match = any(keyword in search_lower for keyword in keywords)
            card_match = any(keyword in card_lower for keyword in keywords)
            
            if search_match and card_match:
                return 0.8  # High similarity within same category
        
        # Partial text similarity
        common_words = set(search_lower.split()) & set(card_lower.split())
        if common_words:
            return len(common_words) / max(len(search_lower.split()), len(card_lower.split()))
        
        return 0.0
    
    async def _calculate_budget_similarity(self, search_budget: Dict, card_budget: Dict) -> float:
        """Calculate budget range similarity"""
        try:
            search_min = search_budget.get("min", 0)
            search_max = search_budget.get("max", 0)
            card_min = card_budget.get("min", 0) or 0
            card_max = card_budget.get("max", 0) or 0
            
            if not (search_min or search_max) or not (card_min or card_max):
                return 0.5  # Neutral if budget info missing
            
            # Calculate range overlap
            overlap_min = max(search_min, card_min)
            overlap_max = min(search_max or float('inf'), card_max or float('inf'))
            
            if overlap_min <= overlap_max:
                # Calculate percentage overlap
                search_range = search_max - search_min if search_max else search_min
                card_range = card_max - card_min if card_max else card_min
                overlap_range = overlap_max - overlap_min
                
                if search_range > 0 and card_range > 0:
                    overlap_ratio = overlap_range / min(search_range, card_range)
                    return min(1.0, overlap_ratio)
            
            # No overlap - calculate distance penalty
            if search_max and card_min and search_max < card_min:
                # Search budget below card budget
                distance = (card_min - search_max) / search_max
                return max(0.0, 1.0 - distance * 0.5)
            elif search_min and card_max and search_min > card_max:
                # Search budget above card budget  
                distance = (search_min - card_max) / card_max
                return max(0.0, 1.0 - distance * 0.5)
            
            return 0.3  # Default similarity if ranges don't overlap well
            
        except Exception as e:
            logger.error(f"Budget similarity calculation error: {e}")
            return 0.5
    
    async def _calculate_location_similarity(self, search_location: str, card_location: str) -> float:
        """Calculate location similarity (city/state/region matching)"""
        try:
            search_lower = search_location.lower()
            card_lower = card_location.lower()
            
            # Exact match
            if search_lower == card_lower:
                return 1.0
            
            # Same city match
            search_parts = [part.strip() for part in search_lower.split(",")]
            card_parts = [part.strip() for part in card_lower.split(",")]
            
            if len(search_parts) >= 1 and len(card_parts) >= 1:
                if search_parts[0] == card_parts[0]:  # Same city
                    return 0.9
            
            # Same state match
            if len(search_parts) >= 2 and len(card_parts) >= 2:
                if search_parts[1] == card_parts[1]:  # Same state
                    return 0.6
            
            # Partial text match
            common_words = set(search_lower.split()) & set(card_lower.split())
            if common_words:
                return 0.4
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Location similarity calculation error: {e}")
            return 0.5
    
    async def _calculate_timeline_similarity(self, search_timeline: str, card_timeline: str) -> float:
        """Calculate timeline similarity"""
        # Simple timeline matching for now
        if search_timeline.lower() == card_timeline.lower():
            return 1.0
        
        # Extract numeric values for comparison
        import re
        search_numbers = re.findall(r'\d+', search_timeline)
        card_numbers = re.findall(r'\d+', card_timeline)
        
        if search_numbers and card_numbers:
            search_val = int(search_numbers[0])
            card_val = int(card_numbers[0])
            
            # Calculate similarity based on numeric difference
            if abs(search_val - card_val) <= 1:
                return 0.8
            elif abs(search_val - card_val) <= 3:
                return 0.6
            elif abs(search_val - card_val) <= 7:
                return 0.4
        
        return 0.2  # Default low similarity
    
    async def _calculate_project_success_rate(self, card: Dict) -> float:
        """Calculate project success rate based on historical data"""
        try:
            # Factors for success rate calculation:
            # 1. Did it reach bid target?
            # 2. Response rate from contractors
            # 3. Timeline adherence
            # 4. Budget adherence
            
            success_score = 0.5  # Base score
            
            # Check if bids were completed
            if card.get("status") == "bids_complete":
                success_score += 0.3
            
            # Response rate factor
            targeted = card.get("contractors_targeted", 0)
            responses = card.get("responses_received", 0)
            
            if targeted > 0:
                response_rate = responses / targeted
                success_score += response_rate * 0.2
            
            return min(1.0, success_score)
            
        except Exception as e:
            logger.error(f"Success rate calculation error: {e}")
            return 0.5
    
    async def _generate_project_insights(self, card: Dict, search_params: Dict) -> List[str]:
        """Generate actionable insights for similar project"""
        insights = []
        
        try:
            # Budget insights
            if card.get("budget_min") and card.get("budget_max"):
                budget_range = card["budget_max"] - card["budget_min"]
                if budget_range > 20000:
                    insights.append(f"Wide budget range (${budget_range:,}) suggests flexible homeowner expectations")
                else:
                    insights.append(f"Tight budget range (${budget_range:,}) indicates specific financial constraints")
            
            # Timeline insights
            if card.get("urgency_level"):
                if card["urgency_level"] == "emergency":
                    insights.append("Emergency timeline commanded premium pricing in similar projects")
                elif card["urgency_level"] == "flexible":
                    insights.append("Flexible timeline allowed for competitive bidding and better rates")
            
            # Success pattern insights
            success_rate = await self._calculate_project_success_rate(card)
            if success_rate > 0.8:
                insights.append("High success rate indicates strong market demand for this project type")
            elif success_rate < 0.4:
                insights.append("Lower completion rate suggests potential challenges with this project type")
            
            # Contractor count insights
            if card.get("contractor_count_needed"):
                if card["contractor_count_needed"] > 6:
                    insights.append("High contractor target suggests competitive bidding environment")
                elif card["contractor_count_needed"] <= 3:
                    insights.append("Limited contractor target indicates selective bidding process")
            
            return insights
            
        except Exception as e:
            logger.error(f"Project insights generation error: {e}")
            return ["Unable to generate specific insights for this project"]
    
    async def _analyze_contractor_fit(self, contractor_id: str, similar_cards: List[BidCardMatch], search_params: Dict) -> ContractorFitAnalysis:
        """Analyze how well contractor fits the project based on similar projects"""
        try:
            if not contractor_id:
                return ContractorFitAnalysis(
                    contractor_id="unknown",
                    fit_score=0.5,
                    specialty_match=0.5,
                    experience_match=0.5,
                    location_match=0.5,
                    capacity_score=0.5,
                    recommendations=["Contractor profile needed for detailed analysis"]
                )
            
            # Load contractor context
            contractor = await self.db.get_contractor_by_id(contractor_id)
            contractor_lead = await self.db.get_contractor_lead_by_id(contractor_id)
            
            # Calculate fit scores
            specialty_match = await self._calculate_specialty_match(contractor, contractor_lead, search_params)
            experience_match = await self._calculate_experience_match(contractor, contractor_lead, similar_cards)
            location_match = await self._calculate_contractor_location_match(contractor, contractor_lead, search_params)
            capacity_score = await self._calculate_capacity_score(contractor, contractor_lead, search_params)
            
            # Overall fit score (weighted average)
            fit_score = (specialty_match * 0.4 + experience_match * 0.3 + location_match * 0.2 + capacity_score * 0.1)
            
            # Generate recommendations
            recommendations = await self._generate_contractor_recommendations(
                fit_score, specialty_match, experience_match, location_match, capacity_score
            )
            
            return ContractorFitAnalysis(
                contractor_id=contractor_id,
                fit_score=fit_score,
                specialty_match=specialty_match,
                experience_match=experience_match,
                location_match=location_match,
                capacity_score=capacity_score,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Contractor fit analysis error: {e}")
            return ContractorFitAnalysis(
                contractor_id=contractor_id or "unknown",
                fit_score=0.5,
                specialty_match=0.5,
                experience_match=0.5,
                location_match=0.5,
                capacity_score=0.5,
                recommendations=[f"Analysis error: {str(e)}"]
            )
    
    async def _calculate_specialty_match(self, contractor: Dict, contractor_lead: Dict, search_params: Dict) -> float:
        """Calculate how well contractor's specialties match project requirements"""
        project_type = search_params.get("project_type", "").lower()
        
        # Get specialties from contractor data
        specialties = []
        if contractor_lead and contractor_lead.get("specialties"):
            specialties.extend(contractor_lead["specialties"])
        
        if not specialties:
            return 0.5  # Neutral score if no specialty data
        
        # Check for direct matches
        for specialty in specialties:
            if project_type in specialty.lower() or specialty.lower() in project_type:
                return 1.0
        
        # Check for category matches
        category_matches = {
            "kitchen": ["kitchen", "cabinet", "remodel", "renovation"],
            "bathroom": ["bathroom", "bath", "plumbing"],
            "landscaping": ["landscaping", "lawn", "outdoor", "garden"],
            "electrical": ["electrical", "wiring", "lighting"],
            "flooring": ["flooring", "floor", "tile", "carpet"]
        }
        
        for category, keywords in category_matches.items():
            if any(keyword in project_type for keyword in keywords):
                if any(keyword in specialty.lower() for specialty in specialties for keyword in keywords):
                    return 0.8
        
        return 0.3  # Low match if no obvious connection
    
    async def _calculate_experience_match(self, contractor: Dict, contractor_lead: Dict, similar_cards: List[BidCardMatch]) -> float:
        """Calculate experience match based on years in business and project complexity"""
        years_experience = 0
        
        if contractor_lead and contractor_lead.get("years_in_business"):
            years_experience = contractor_lead["years_in_business"]
        elif contractor and contractor.get("total_jobs"):
            # Estimate years based on job count (rough approximation)
            years_experience = min(20, contractor["total_jobs"] / 50)
        
        # Score based on experience level
        if years_experience >= 10:
            return 0.9
        elif years_experience >= 5:
            return 0.7
        elif years_experience >= 2:
            return 0.5
        else:
            return 0.3
    
    async def _calculate_contractor_location_match(self, contractor: Dict, contractor_lead: Dict, search_params: Dict) -> float:
        """Calculate location match for contractor service area"""
        search_location = search_params.get("location", "").lower()
        
        # Get contractor location info
        contractor_location = ""
        if contractor_lead:
            city = contractor_lead.get("city", "")
            state = contractor_lead.get("state", "")
            contractor_location = f"{city}, {state}".lower()
        
        if not contractor_location or not search_location:
            return 0.5  # Neutral if location data missing
        
        # Use same location similarity algorithm
        return await self._calculate_location_similarity(search_location, contractor_location)
    
    async def _calculate_capacity_score(self, contractor: Dict, contractor_lead: Dict, search_params: Dict) -> float:
        """Calculate contractor capacity to handle the project"""
        # Factors: employee count, current workload, project size
        
        base_score = 0.5
        
        # Employee count factor
        if contractor_lead and contractor_lead.get("employees"):
            employee_count = contractor_lead["employees"]
            if employee_count >= 10:
                base_score += 0.3
            elif employee_count >= 5:
                base_score += 0.2
            elif employee_count >= 2:
                base_score += 0.1
        
        # Business maturity factor
        if contractor and contractor.get("total_jobs"):
            total_jobs = contractor["total_jobs"]
            if total_jobs >= 100:
                base_score += 0.2
            elif total_jobs >= 50:
                base_score += 0.1
        
        return min(1.0, base_score)
    
    async def _generate_contractor_recommendations(self, fit_score: float, specialty_match: float, 
                                                 experience_match: float, location_match: float, 
                                                 capacity_score: float) -> List[str]:
        """Generate actionable recommendations based on contractor fit analysis"""
        recommendations = []
        
        if fit_score >= 0.8:
            recommendations.append("Excellent fit - highly recommend pursuing this project")
        elif fit_score >= 0.6:
            recommendations.append("Good fit - project aligns well with contractor capabilities")
        elif fit_score >= 0.4:
            recommendations.append("Moderate fit - consider if workload allows")
        else:
            recommendations.append("Poor fit - may want to focus on better-matched opportunities")
        
        # Specific improvement suggestions
        if specialty_match < 0.5:
            recommendations.append("Consider highlighting transferable skills from related project types")
        
        if experience_match < 0.5:
            recommendations.append("Emphasize quality over quantity in project examples")
        
        if location_match < 0.5:
            recommendations.append("Factor in travel time and local permit requirements for pricing")
        
        if capacity_score < 0.5:
            recommendations.append("Ensure sufficient resources available before bidding")
        
        return recommendations
    
    async def _generate_market_insights(self, similar_cards: List[BidCardMatch], search_params: Dict) -> Dict[str, Any]:
        """Generate market insights from similar project analysis"""
        try:
            if not similar_cards:
                return {"error": "No similar projects found for market analysis"}
            
            # Budget analysis
            budgets = [card.budget_range for card in similar_cards if card.budget_range.get("min") or card.budget_range.get("max")]
            budget_insights = {}
            
            if budgets:
                min_budgets = [b["min"] for b in budgets if b.get("min")]
                max_budgets = [b["max"] for b in budgets if b.get("max")]
                
                if min_budgets and max_budgets:
                    budget_insights = {
                        "typical_range": {
                            "min": sum(min_budgets) // len(min_budgets),
                            "max": sum(max_budgets) // len(max_budgets)
                        },
                        "budget_variance": max(max_budgets) - min(min_budgets),
                        "sample_size": len(budgets)
                    }
            
            # Success rate analysis
            success_rates = [card.success_rate for card in similar_cards]
            avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0.5
            
            # Timeline analysis
            timelines = [card.timeline for card in similar_cards if card.timeline != "Not specified"]
            common_timelines = {}
            for timeline in timelines:
                common_timelines[timeline] = common_timelines.get(timeline, 0) + 1
            
            most_common_timeline = max(common_timelines.items(), key=lambda x: x[1])[0] if common_timelines else "6-8 weeks"
            
            # Competition analysis
            contractor_counts = [card.contractor_count for card in similar_cards if card.contractor_count > 0]
            avg_competition = sum(contractor_counts) / len(contractor_counts) if contractor_counts else 4
            
            return {
                "budget_insights": budget_insights,
                "market_success_rate": round(avg_success_rate, 2),
                "typical_timeline": most_common_timeline,
                "average_competition": round(avg_competition, 1),
                "market_trends": await self._analyze_market_trends(similar_cards),
                "competitive_positioning": await self._analyze_competitive_positioning(similar_cards, search_params)
            }
            
        except Exception as e:
            logger.error(f"Market insights generation error: {e}")
            return {"error": f"Market analysis failed: {str(e)}"}
    
    async def _analyze_market_trends(self, similar_cards: List[BidCardMatch]) -> List[str]:
        """Analyze trends from similar projects"""
        trends = []
        
        try:
            # Analyze by project status
            status_counts = {}
            for card in similar_cards:
                status_counts[card.status] = status_counts.get(card.status, 0) + 1
            
            completed_rate = status_counts.get("bids_complete", 0) / len(similar_cards)
            
            if completed_rate > 0.8:
                trends.append("High completion rate indicates strong contractor interest")
            elif completed_rate < 0.4:
                trends.append("Lower completion rate suggests challenging market conditions")
            
            # Analyze budget trends
            recent_cards = sorted(similar_cards, key=lambda x: x.bid_card_id, reverse=True)[:5]
            older_cards = similar_cards[5:]
            
            if recent_cards and older_cards:
                recent_avg = sum(c.budget_range.get("max", 0) for c in recent_cards) / len(recent_cards)
                older_avg = sum(c.budget_range.get("max", 0) for c in older_cards) / len(older_cards)
                
                if recent_avg > older_avg * 1.1:
                    trends.append("Budget expectations trending upward")
                elif recent_avg < older_avg * 0.9:
                    trends.append("Budget expectations trending downward")
            
            return trends
            
        except Exception as e:
            logger.error(f"Market trends analysis error: {e}")
            return ["Market trend analysis unavailable"]
    
    async def _analyze_competitive_positioning(self, similar_cards: List[BidCardMatch], search_params: Dict) -> Dict[str, Any]:
        """Analyze competitive positioning for contractor"""
        try:
            # Competition intensity
            avg_contractor_count = sum(c.contractor_count for c in similar_cards if c.contractor_count > 0) / len(similar_cards)
            
            if avg_contractor_count <= 3:
                competition_level = "low"
            elif avg_contractor_count <= 6:
                competition_level = "moderate"
            else:
                competition_level = "high"
            
            # Success factors from high-performing projects
            high_success_cards = [c for c in similar_cards if c.success_rate > 0.7]
            success_factors = []
            
            if high_success_cards:
                # Analyze what made these projects successful
                common_budgets = [c.budget_range for c in high_success_cards]
                common_timelines = [c.timeline for c in high_success_cards]
                
                if len(set(t for t in common_timelines if t)) <= 2:
                    success_factors.append("Consistent timeline expectations")
                
                if all(b.get("max", 0) > 25000 for b in common_budgets):
                    success_factors.append("Higher budget projects show better completion rates")
            
            return {
                "competition_level": competition_level,
                "average_competitors": round(avg_contractor_count, 1),
                "success_factors": success_factors,
                "recommended_strategy": await self._get_bidding_strategy(competition_level, search_params)
            }
            
        except Exception as e:
            logger.error(f"Competitive positioning analysis error: {e}")
            return {"error": "Competitive analysis unavailable"}
    
    async def _get_bidding_strategy(self, competition_level: str, search_params: Dict) -> str:
        """Recommend bidding strategy based on competition analysis"""
        if competition_level == "low":
            return "Focus on quality and unique value proposition - less price pressure"
        elif competition_level == "moderate":
            return "Balance competitive pricing with differentiating factors"
        else:
            return "Emphasize speed, reliability, and competitive pricing to stand out"
    
    async def _create_recommendations(self, similar_cards: List[BidCardMatch], 
                                   contractor_analysis: ContractorFitAnalysis,
                                   market_insights: Dict[str, Any], 
                                   search_params: Dict[str, Any]) -> List[str]:
        """Create actionable recommendations based on comprehensive analysis"""
        recommendations = []
        
        try:
            # Project viability recommendations
            if similar_cards:
                avg_success_rate = sum(c.success_rate for c in similar_cards) / len(similar_cards)
                
                if avg_success_rate > 0.7:
                    recommendations.append("High success rate for similar projects - good opportunity")
                elif avg_success_rate < 0.4:
                    recommendations.append("Lower success rate - investigate potential challenges")
            
            # Contractor fit recommendations
            if contractor_analysis.fit_score > 0.7:
                recommendations.append("Strong contractor-project fit - recommend pursuing")
            elif contractor_analysis.fit_score < 0.4:
                recommendations.append("Poor project fit - consider passing unless strategic value")
            
            # Market timing recommendations
            if market_insights.get("market_success_rate", 0) > 0.6:
                recommendations.append("Market conditions favorable for this project type")
            
            # Pricing recommendations
            budget_insights = market_insights.get("budget_insights", {})
            if budget_insights.get("typical_range"):
                typical_range = budget_insights["typical_range"]
                recommendations.append(f"Typical budget range: ${typical_range['min']:,} - ${typical_range['max']:,}")
            
            # Competition recommendations
            competition_level = market_insights.get("competitive_positioning", {}).get("competition_level")
            if competition_level:
                if competition_level == "high":
                    recommendations.append("High competition - focus on unique differentiators")
                elif competition_level == "low":
                    recommendations.append("Lower competition - opportunity for premium pricing")
            
            # Timeline recommendations
            typical_timeline = market_insights.get("typical_timeline")
            if typical_timeline:
                recommendations.append(f"Typical project timeline: {typical_timeline}")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Recommendations generation error: {e}")
            return ["Analysis complete - specific recommendations unavailable"]
    
    async def _calculate_confidence_score(self, similar_cards: List[BidCardMatch]) -> float:
        """Calculate confidence score for analysis results"""
        if not similar_cards:
            return 0.1
        
        # Base confidence on number of similar projects found
        base_confidence = min(0.5, len(similar_cards) * 0.05)
        
        # Boost confidence for high-similarity matches
        high_similarity_count = sum(1 for card in similar_cards if card.similarity_score > 0.7)
        similarity_boost = min(0.3, high_similarity_count * 0.1)
        
        # Boost confidence for recent projects
        recent_count = sum(1 for card in similar_cards if "2024" in card.bid_card_id or "2025" in card.bid_card_id)
        recency_boost = min(0.2, recent_count * 0.05)
        
        return min(1.0, base_confidence + similarity_boost + recency_boost)
    
    async def _update_search_context(self, state: Dict[str, Any], results: Dict[str, Any]):
        """Update conversation state with search context for future reference"""
        try:
            if 'search_history' not in state:
                state['search_history'] = []
            
            search_entry = {
                "timestamp": datetime.now().isoformat(),
                "search_params": results["search_params"],
                "results_count": len(results["similar_projects"]),
                "confidence_score": results["confidence_score"]
            }
            
            state['search_history'].append(search_entry)
            
            # Keep only last 5 searches
            if len(state['search_history']) > 5:
                state['search_history'] = state['search_history'][-5:]
                
        except Exception as e:
            logger.error(f"Search context update error: {e}")
    
    async def _format_bid_card_match(self, match: BidCardMatch) -> Dict[str, Any]:
        """Format bid card match for API response"""
        return {
            "bid_card_id": match.bid_card_id,
            "project_type": match.project_type,
            "similarity_score": round(match.similarity_score, 2),
            "budget_range": match.budget_range,
            "timeline": match.timeline,
            "location": match.location,
            "contractor_count": match.contractor_count,
            "status": match.status,
            "success_rate": round(match.success_rate, 2),
            "insights": match.insights
        }
    
    async def _get_fallback_recommendations(self) -> List[str]:
        """Provide fallback recommendations when search fails"""
        return [
            "Unable to find similar projects - rely on standard market rates",
            "Consider reaching out to local contractors for pricing guidance",
            "Review industry publications for current market trends",
            "Focus on contractor qualifications and experience over pricing comparisons"
        ]
    
    # ============================================================================
    # INTELLIGENT SEMANTIC MATCHING METHODS - Integrated from simple system
    # ============================================================================
    

    async def search_bid_cards_in_radius(
        self,
        contractor_zip: str, 
        radius_miles: int = 30, 
        project_type: Optional[str] = None,
        expanded_types: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        use_semantic_matching: bool = True
    ) -> Dict[str, Any]:
        """
        Search for bid cards within radius with intelligent semantic matching
        Now integrated into DeepAgents framework
        """
        try:
            # Get ZIP codes in radius using existing utility
            zip_codes = get_zip_codes_in_radius(contractor_zip, radius_miles)
            
            # Query database for bid cards in radius
            if use_semantic_matching and (expanded_types or keywords):
                # Use the actual Supabase client from database_simple
                from database_simple import get_client
                client = get_client()
                
                # Build Supabase query properly
                query = client.table("bid_cards").select("*")
                query = query.in_("status", ["active", "collecting_bids", "generated"])
                
                if zip_codes:
                    query = query.in_("location_zip", zip_codes[:50])
                else:
                    query = query.eq("location_zip", contractor_zip)
                
                # Execute and get results
                result = query.limit(100).execute()
                all_bid_cards = result.data if result.data else []
                
                # Add distance information
                for card in all_bid_cards:
                    if card.get("location_zip"):
                        card["distance_miles"] = calculate_distance_miles(
                            contractor_zip, 
                            str(card["location_zip"])
                        )
                
                # Use intelligent semantic matching
                search_terms = []
                if expanded_types:
                    search_terms.extend(expanded_types[:3])
                if keywords:
                    search_terms.extend(keywords[:3])
                
                search_string = " ".join(search_terms) if search_terms else project_type or "construction projects"
                
                # Perform semantic matching using OpenAI
                match_result = await self._intelligent_semantic_matching(
                    contractor_search=search_string,
                    bid_cards=all_bid_cards,
                    contractor_specialties=expanded_types
                )
                
                if match_result.get("success"):
                    matched_cards = match_result.get("matched_cards", [])
                    borderline_cards = match_result.get("borderline_cards", [])
                    
                    return {
                        "success": True,
                        "count": len(matched_cards),
                        "bid_cards": matched_cards[:10],
                        "borderline_cards": borderline_cards[:5],
                        "search_radius": radius_miles,
                        "contractor_zip": contractor_zip,
                        "semantic_matching": True,
                        "analysis_summary": match_result.get("analysis_summary", ""),
                        "suggested_questions": match_result.get("suggested_questions", []),
                        "total_analyzed": match_result.get("total_analyzed", 0)
                    }
                else:
                    logger.warning(f"Semantic matching failed: {match_result.get('error')}")
                    # Fall through to basic matching
                    bid_cards = all_bid_cards
            else:
                # Basic search without semantic matching
                from database_simple import get_client
                client = get_client()
                
                query = client.table("bid_cards").select("*")
                query = query.in_("status", ["active", "collecting_bids", "generated"])
                
                if zip_codes:
                    query = query.in_("location_zip", zip_codes[:50])
                else:
                    query = query.eq("location_zip", contractor_zip)
                
                result = query.limit(100).execute()
                bid_cards = result.data if result.data else []
                
                # Filter by project type if specified
                if project_type:
                    filtered = [card for card in bid_cards 
                              if project_type.lower() in card.get("project_type", "").lower()]
                    bid_cards = filtered
                
                # Add distance information and sort
                for card in bid_cards:
                    if card.get("location_zip"):
                        card["distance_miles"] = calculate_distance_miles(
                            contractor_zip, 
                            str(card["location_zip"])
                        )
                
                bid_cards.sort(key=lambda x: x.get("distance_miles", 999))
            
            return {
                "success": True,
                "count": len(bid_cards),
                "bid_cards": bid_cards[:10],
                "search_radius": radius_miles,
                "contractor_zip": contractor_zip,
                "project_type": project_type,
                "semantic_matching": False
            }
            
        except Exception as e:
            logger.error(f"Error searching bid cards in radius: {e}")
            return {
                "success": False,
                "error": str(e),
                "count": 0,
                "bid_cards": []
            }
    
    async def _intelligent_semantic_matching(
        self,
        contractor_search: str,
        bid_cards: List[Dict[str, Any]],
        contractor_specialties: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Use OpenAI GPT-4o-mini for intelligent semantic matching of bid cards
        Integrated from intelligent_matcher.py into DeepAgents framework
        """
        if not bid_cards:
            return {"success": True, "matched_cards": [], "borderline_cards": [], "total_analyzed": 0}
        
        if not self.openai_client:
            return {"success": False, "error": "OpenAI client not available"}
        
        try:
            # Build context about contractor specialties
            specialty_context = ""
            if contractor_specialties:
                specialty_context = f"Contractor specializes in: {', '.join(contractor_specialties)}"
            
            # Prepare bid card data for analysis (limit to avoid token overflow)
            simplified_cards = []
            for i, card in enumerate(bid_cards[:20]):  # Limit to 20 cards
                simplified_cards.append({
                    "index": i,
                    "id": card.get("id"),
                    "title": card.get("project_name", ""),
                    "type": card.get("project_type", ""),
                    "description": card.get("project_description", "")[:200],  # Truncate
                    "location": f"{card.get('location_city', '')}, {card.get('location_state', '')}",
                    "budget": card.get("budget_max", 0),
                    "timeline": card.get("timeline_weeks", "")
                })
            
            # Create prompt for semantic matching
            system_prompt = """You are an expert contractor matching system. Your job is to analyze bid cards and determine how well they match a contractor's search request.

For each bid card, provide:
1. relevance_score (0-100): How well does this project match the contractor's request?
2. reasoning: Brief explanation of why it matches or doesn't match
3. clarifying_question: If relevance is 40-60%, ask a question to clarify if the contractor would be interested

Scoring guidelines:
- 80-100: Perfect match (contractor definitely interested)
- 60-79: Good match (likely interested)
- 40-59: Borderline match (ask clarifying question)
- 20-39: Poor match (contractor might not be interested)
- 0-19: No match (contractor definitely not interested)

Return JSON format:
{
  "matches": [
    {
      "index": 0,
      "relevance_score": 85,
      "reasoning": "Perfect match - artificial turf installation aligns with landscaping expertise",
      "clarifying_question": null
    }
  ],
  "analysis_summary": "Found 5 landscaping projects that match your artificial turf expertise...",
  "suggested_questions": ["Do you also install drainage systems?", "Can you do hardscaping work?"]
}"""
            
            user_prompt = f"""Contractor search: "{contractor_search}"
{specialty_context}

Analyze these bid cards:
{json.dumps(simplified_cards, indent=2)}

Score each bid card's relevance to the contractor's search."""
            
            # Call OpenAI for semantic analysis
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse response
            analysis = json.loads(response.choices[0].message.content)
            matches = analysis.get("matches", [])
            
            # Separate into matched and borderline cards
            matched_cards = []
            borderline_cards = []
            
            for match in matches:
                index = match.get("index")
                score = match.get("relevance_score", 0)
                reasoning = match.get("reasoning", "")
                question = match.get("clarifying_question")
                
                if 0 <= index < len(bid_cards):
                    card = bid_cards[index].copy()
                    
                    # Add match metadata
                    card["match_info"] = {
                        "relevance_score": score,
                        "reasoning": reasoning,
                        "clarifying_question": question,
                        "match_type": "semantic"
                    }
                    
                    if score >= 60:
                        matched_cards.append(card)
                    elif score >= 40:
                        borderline_cards.append(card)
            
            # Sort by relevance score
            matched_cards.sort(key=lambda x: x["match_info"]["relevance_score"], reverse=True)
            borderline_cards.sort(key=lambda x: x["match_info"]["relevance_score"], reverse=True)
            
            return {
                "success": True,
                "matched_cards": matched_cards,
                "borderline_cards": borderline_cards,
                "analysis_summary": analysis.get("analysis_summary", ""),
                "suggested_questions": analysis.get("suggested_questions", []),
                "total_analyzed": len(simplified_cards)
            }
            
        except Exception as e:
            logger.error(f"Semantic matching error: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_confirmation_message(
        self,
        matched_cards: List[Dict[str, Any]],
        borderline_cards: List[Dict[str, Any]],
        contractor_search: str
    ) -> str:
        """
        Generate natural language confirmation message for search results
        Integrated from intelligent_matcher.py into DeepAgents framework
        """
        if not matched_cards and not borderline_cards:
            return ("I couldn't find any projects matching your criteria. "
                   "Would you like me to:\n"
                   "1. Expand the search radius?\n"
                   "2. Look for different types of projects?\n"
                   "3. Set up notifications for when matching projects are posted?")
        
        try:
            # Build context for GPT
            match_summary = []
            for card in matched_cards[:3]:  # Top 3 matches
                match_info = card.get("match_info", {})
                score = match_info.get("relevance_score", 0)
                project_name = card.get("project_name", "Project")
                project_type = card.get("project_type", "")
                location = f"{card.get('location_city', '')}, {card.get('location_state', '')}"
                budget = card.get("budget_max", 0)
                
                match_summary.append({
                    "name": project_name,
                    "type": project_type,
                    "location": location,
                    "budget": budget,
                    "score": score
                })
            
            borderline_summary = []
            for card in borderline_cards[:2]:  # Top 2 borderline
                match_info = card.get("match_info", {})
                project_name = card.get("project_name", "Project")
                question = match_info.get("clarifying_question", "")
                
                if question:
                    borderline_summary.append({
                        "name": project_name,
                        "question": question
                    })
            
            # Generate confirmation message using GPT
            if not self.openai_client:
                # Fallback without GPT
                message = f"I found {len(matched_cards)} projects matching '{contractor_search}'."
                if borderline_cards:
                    message += f" I also found {len(borderline_cards)} projects that might be relevant."
                message += " Do these look like projects you'd be interested in bidding on?"
                return message
            
            system_prompt = """You are a helpful assistant for contractors looking for bidding opportunities. 
            Generate a natural, conversational message confirming search results and asking for feedback.

            Your message should:
            1. Acknowledge what they searched for
            2. Summarize what you found (but don't list every detail)
            3. Ask if these are the types of projects they want
            4. If there are borderline matches, ask the clarifying questions
            5. Keep it conversational and helpful, not robotic

            Keep the message concise but friendly."""
            
            user_prompt = f"""Contractor searched for: "{contractor_search}"

            I found {len(matched_cards)} good matches:
            {json.dumps(match_summary, indent=2)}

            Borderline matches with questions:
            {json.dumps(borderline_summary, indent=2)}

            Generate a confirmation message asking if these are the types of projects they want."""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating confirmation message: {e}")
            # Fallback message
            message = f"I found {len(matched_cards)} projects that match your search for '{contractor_search}'."
            if borderline_cards:
                message += f" I also found {len(borderline_cards)} projects that might be relevant."
            message += " Do these look like the types of projects you're interested in?"
            return message