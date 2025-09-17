"""
Group Bidding Sub-Agent - DeepAgents Framework
Specialized sub-agent for identifying and managing group bidding opportunities
Analyzes multiple projects for bulk pricing advantages and strategic bundling
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging
import os
from dataclasses import dataclass
from collections import defaultdict
import asyncio

from database import SupabaseDB
from deepagents.sub_agent import SubAgent
from deepagents.state import DeepAgentState

# Import service complexity classifier for filtering group-eligible projects
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from agents.cia.service_complexity_classifier import ServiceComplexityClassifier

logger = logging.getLogger(__name__)

@dataclass
class GroupOpportunity:
    """Group bidding opportunity"""
    group_id: str
    project_count: int
    total_value: float
    potential_savings: float
    discount_percentage: float
    location_cluster: str
    timeline_overlap: int  # days of overlap
    projects: List[Dict[str, Any]]
    difficulty_score: float
    coordination_requirements: List[str]

@dataclass
class ProjectCluster:
    """Cluster of related projects"""
    cluster_id: str
    cluster_type: str  # geographic, temporal, specialty, homeowner
    projects: List[Dict[str, Any]]
    clustering_factors: List[str]
    synergy_score: float
    coordination_complexity: str

@dataclass
class BulkPricingStrategy:
    """Bulk pricing strategy recommendation"""
    base_pricing: Dict[str, float]
    bulk_discounts: Dict[int, float]  # project count -> discount percentage
    savings_breakdown: Dict[str, float]
    timeline_optimization: Dict[str, Any]
    resource_allocation: Dict[str, Any]
    risk_mitigation: List[str]

@dataclass
class GroupBidRecommendation:
    """Complete group bidding recommendation"""
    opportunity: GroupOpportunity
    pricing_strategy: BulkPricingStrategy
    implementation_plan: Dict[str, Any]
    success_probability: float
    competitive_advantages: List[str]
    potential_challenges: List[str]

class GroupBiddingAgent(SubAgent):
    """
    Group Bidding Sub-Agent specializing in multi-project opportunities
    
    Capabilities:
    1. Identify clustered project opportunities (geographic, temporal, specialty)
    2. Calculate bulk pricing advantages and cost savings
    3. Optimize resource allocation across multiple projects
    4. Assess coordination complexity and logistics
    5. Generate strategic group bidding recommendations
    6. Analyze homeowner relationship building opportunities
    """
    
    def __init__(self):
        super().__init__(
            name="group-bidding",
            description="Identifies and optimizes group bidding opportunities for maximum efficiency and profitability",
            version="1.0.0"
        )
        self.db = SupabaseDB()
        self.service_classifier = ServiceComplexityClassifier()
        
        # Group bidding parameters - now with service complexity awareness
        self.clustering_parameters = {
            "max_geographic_distance": 25,  # miles
            "max_timeline_gap": 30,  # days
            "min_group_size": 3,
            "max_group_size": 8,
            "min_savings_threshold": 0.10,  # 10% minimum savings
            "specialty_match_weight": 0.4,
            "geographic_weight": 0.3,
            "timeline_weight": 0.3,
            # Service complexity filtering for group eligibility
            "preferred_service_complexity": "single-trade",  # Focus on single-trade projects
            "allow_multi_trade": False,  # Initially exclude multi-trade projects
            "group_eligible_trades": [
                "lawn care", "landscaping", "turf installation", 
                "roofing", "pool maintenance", "window cleaning",
                "gutter cleaning", "pressure washing", "painting"
            ]
        }
        
    async def execute(self, state: DeepAgentState, task_description: str) -> Dict[str, Any]:
        """
        Execute group bidding opportunity analysis
        
        Args:
            state: DeepAgentState with conversation context
            task_description: Specific group bidding task from main agent
            
        Returns:
            Comprehensive group bidding analysis with strategic recommendations
        """
        try:
            # Extract group bidding parameters from task and state
            group_params = await self._extract_group_parameters(task_description, state)
            
            # Load available projects for grouping analysis
            available_projects = await self._load_available_projects(group_params)
            
            # Perform project clustering analysis
            project_clusters = await self._analyze_project_clusters(available_projects, group_params)
            
            # Identify group bidding opportunities
            group_opportunities = await self._identify_group_opportunities(project_clusters, group_params)
            
            # Develop bulk pricing strategies
            pricing_strategies = await self._develop_bulk_pricing_strategies(group_opportunities, group_params)
            
            # Generate implementation recommendations
            implementation_plans = await self._generate_implementation_plans(
                group_opportunities, pricing_strategies, group_params
            )
            
            # Create final recommendations
            recommendations = await self._create_group_recommendations(
                group_opportunities, pricing_strategies, implementation_plans
            )
            
            # Calculate success metrics
            success_metrics = await self._calculate_success_metrics(recommendations, group_params)
            
            # Format results for main agent
            results = {
                "sub_agent": "group-bidding",
                "group_params": group_params,
                "available_projects": len(available_projects),
                "project_clusters": self._format_project_clusters(project_clusters),
                "group_opportunities": self._format_group_opportunities(group_opportunities),
                "pricing_strategies": self._format_pricing_strategies(pricing_strategies),
                "recommendations": self._format_group_recommendations(recommendations),
                "success_metrics": success_metrics,
                "strategic_insights": await self._generate_strategic_insights(
                    group_opportunities, recommendations
                ),
                "group_metadata": {
                    "analysis_time": datetime.now().isoformat(),
                    "clustering_algorithm": "multi_factor_v2.1",
                    "opportunities_found": len(group_opportunities),
                    "max_potential_savings": max([opp.potential_savings for opp in group_opportunities], default=0),
                    "total_project_value": sum([opp.total_value for opp in group_opportunities], default=0)
                }
            }
            
            # Update state with group bidding context
            await self._update_group_context(state, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Group bidding agent error: {e}")
            return {
                "sub_agent": "group-bidding",
                "error": str(e),
                "fallback_recommendations": await self._get_fallback_group_recommendations()
            }
    
    async def _extract_group_parameters(self, task_description: str, state: DeepAgentState) -> Dict[str, Any]:
        """Extract and normalize group bidding parameters from task and conversation state"""
        
        params = {
            "task_description": task_description,
            "contractor_id": None,
            "current_project_id": None,
            "target_location": None,
            "specialties": [],
            "capacity_weeks": 12,  # Available capacity in weeks
            "preferred_group_size": 4,
            "max_travel_distance": 25,  # miles
            "timeline_flexibility": "moderate",  # strict, moderate, flexible
            "pricing_strategy": "competitive",  # aggressive, competitive, premium
            "risk_tolerance": "moderate",  # low, moderate, high
            "focus_area": "geographic"  # geographic, specialty, temporal, mixed
        }
        
        # Extract from conversation state
        if hasattr(state, 'conversation_memory') and state.conversation_memory:
            memory = state.conversation_memory
            params.update({
                "current_project_id": memory.get("bid_card_id"),
                "target_location": memory.get("location"),
                "project_type": memory.get("project_type"),
                "timeline": memory.get("timeline"),
                "budget_range": memory.get("budget_range")
            })
        
        # Extract contractor context
        if hasattr(state, 'contractor_id'):
            params["contractor_id"] = state.contractor_id
            
            # Load contractor specialties and preferences
            contractor_context = await self._load_contractor_context(state.contractor_id)
            if contractor_context:
                params["specialties"] = contractor_context.get("specialties", [])
                params["service_area"] = contractor_context.get("service_area", [])
                params["capacity_score"] = contractor_context.get("capacity_score", 0.5)
        
        # Parse task description for specific group bidding intent
        task_lower = task_description.lower()
        
        # Determine focus area
        if "geographic" in task_lower or "location" in task_lower or "area" in task_lower:
            params["focus_area"] = "geographic"
        elif "specialty" in task_lower or "similar" in task_lower:
            params["focus_area"] = "specialty"
        elif "timeline" in task_lower or "schedule" in task_lower:
            params["focus_area"] = "temporal"
        elif "package" in task_lower or "bundle" in task_lower:
            params["focus_area"] = "mixed"
        
        # Determine preferred group size
        if "small" in task_lower:
            params["preferred_group_size"] = 3
        elif "large" in task_lower:
            params["preferred_group_size"] = 6
        
        # Determine timeline flexibility
        if "urgent" in task_lower or "tight" in task_lower:
            params["timeline_flexibility"] = "strict"
        elif "flexible" in task_lower or "open" in task_lower:
            params["timeline_flexibility"] = "flexible"
        
        return params
    
    async def _load_available_projects(self, group_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Load available projects for group bidding analysis with service complexity filtering"""
        try:
            # Query for available bid cards that could be grouped
            # Exclude current project if specified
            current_project_id = group_params.get("current_project_id")
            exclude_clause = f"AND id != '{current_project_id}'" if current_project_id else ""
            
            query = f"""
            SELECT 
                bc.id,
                bc.bid_card_number,
                bc.project_type,
                bc.budget_min,
                bc.budget_max,
                bc.timeline,
                bc.location_city,
                bc.location_state,
                bc.location_zip,
                bc.urgency_level,
                bc.contractor_count_needed,
                bc.status,
                bc.created_at,
                bc.bid_document,
                -- Campaign information
                oc.contractors_targeted,
                oc.responses_received,
                -- Project complexity indicators
                CASE 
                    WHEN bc.budget_max - bc.budget_min > 30000 THEN 'high_flexibility'
                    WHEN bc.budget_max - bc.budget_min > 10000 THEN 'moderate_flexibility'
                    ELSE 'low_flexibility'
                END as budget_flexibility
            FROM bid_cards bc
            LEFT JOIN outreach_campaigns oc ON bc.id = oc.bid_card_id
            WHERE bc.status IN ('generated', 'collecting_bids')
            {exclude_clause}
            AND bc.created_at > NOW() - INTERVAL '30 days'
            ORDER BY bc.created_at DESC
            LIMIT 100
            """
            
            projects = await self.db.execute_query(query)
            
            # Filter by contractor specialties and service area
            specialties = group_params.get("specialties", [])
            target_location = group_params.get("target_location", "")
            
            filtered_projects = []
            for project in projects:
                # Check specialty match
                if specialties:
                    project_type = project.get("project_type", "").lower()
                    specialty_match = any(
                        specialty.lower() in project_type or project_type in specialty.lower()
                        for specialty in specialties
                    )
                    if not specialty_match:
                        continue
                
                # Check location proximity (simplified)
                if target_location:
                    project_location = f"{project.get('location_city', '')}, {project.get('location_state', '')}".lower()
                    if target_location.lower() not in project_location and project_location not in target_location.lower():
                        # In production, would use geographic distance calculation
                        continue
                
                # Filter by service complexity for group bidding eligibility
                if not await self._is_project_group_eligible(project):
                    continue
                
                # Add calculated fields
                project["estimated_value"] = (project.get("budget_min", 0) + project.get("budget_max", 0)) / 2 if project.get("budget_max") else project.get("budget_min", 0)
                project["timeline_weeks"] = await self._parse_timeline_weeks(project.get("timeline", ""))
                project["complexity_score"] = await self._calculate_project_complexity(project)
                
                filtered_projects.append(project)
            
            return filtered_projects[:50]  # Limit for performance
            
        except Exception as e:
            logger.error(f"Project loading error: {e}")
            return await self._get_sample_projects(group_params)
    
    async def _is_project_group_eligible(self, project: Dict[str, Any]) -> bool:
        """Determine if project is eligible for group bidding based on service complexity"""
        try:
            project_type = project.get("project_type", "")
            project_description = project.get("project_description", "")
            
            # Use service complexity classifier to analyze project
            classification = self.service_classifier.classify_project(
                project_type=project_type,
                description=project_description,
                recommended_trades=None
            )
            
            service_complexity = classification.get("service_complexity", "single-trade")
            primary_trade = classification.get("primary_trade", "").lower()
            
            print(f"[Group Bidding] Project '{project_type}' classified as {service_complexity}, trade: {primary_trade}")
            
            # Check if complexity matches group bidding preferences
            preferred_complexity = self.clustering_parameters["preferred_service_complexity"]
            allow_multi_trade = self.clustering_parameters["allow_multi_trade"]
            group_eligible_trades = self.clustering_parameters["group_eligible_trades"]
            
            # Primary filter: service complexity
            if service_complexity == "single-trade":
                # Check if the primary trade is in the group-eligible list
                trade_eligible = any(
                    eligible_trade.lower() in primary_trade or primary_trade in eligible_trade.lower()
                    for eligible_trade in group_eligible_trades
                )
                
                if trade_eligible:
                    print(f"[Group Bidding] Project APPROVED for group bidding: {primary_trade} single-trade")
                    return True
                else:
                    print(f"[Group Bidding] Project EXCLUDED: {primary_trade} not in group-eligible trades")
                    return False
            
            elif service_complexity == "multi-trade" and allow_multi_trade:
                print(f"[Group Bidding] Project CONDITIONALLY APPROVED: multi-trade allowed")
                return True
            
            else:  # complex-coordination or multi-trade when not allowed
                print(f"[Group Bidding] Project EXCLUDED: {service_complexity} not suitable for group bidding")
                return False
                
        except Exception as e:
            logger.error(f"Group eligibility check error: {e}")
            # Default to eligible if classification fails (conservative approach)
            return True
    
    async def _calculate_service_complexity_synergy(self, projects: List[Dict[str, Any]]) -> float:
        """Calculate synergy multiplier based on service complexity patterns within project group"""
        try:
            if not projects:
                return 1.0
            
            # Classify all projects in the group
            project_classifications = []
            for project in projects:
                classification = self.service_classifier.classify_project(
                    project_type=project.get("project_type", ""),
                    description=project.get("project_description", ""),
                    recommended_trades=None
                )
                project_classifications.append(classification)
            
            # Analyze complexity patterns
            complexities = [c.get("service_complexity", "single-trade") for c in project_classifications]
            primary_trades = [c.get("primary_trade", "general").lower() for c in project_classifications]
            
            synergy_multiplier = 1.0  # Base multiplier
            
            # Bonus for homogeneous service complexity
            if all(comp == complexities[0] for comp in complexities):
                if complexities[0] == "single-trade":
                    synergy_multiplier += 0.20  # 20% bonus for all single-trade
                    print(f"[Group Synergy] +20% bonus: All projects are single-trade")
                elif complexities[0] == "multi-trade":
                    synergy_multiplier += 0.10  # 10% bonus for all multi-trade (if allowed)
                    print(f"[Group Synergy] +10% bonus: All projects are multi-trade")
            
            # Bonus for trade specialization clustering
            unique_trades = set(primary_trades)
            if len(unique_trades) == 1:
                # All projects same trade type
                synergy_multiplier += 0.25  # 25% bonus for trade specialization
                print(f"[Group Synergy] +25% bonus: All projects are {primary_trades[0]} trade")
            elif len(unique_trades) <= len(projects) // 2:
                # High trade overlap
                synergy_multiplier += 0.15  # 15% bonus for high trade overlap
                print(f"[Group Synergy] +15% bonus: High trade overlap ({len(unique_trades)} trades)")
            
            # Bonus for complementary single-trade projects
            single_trade_count = complexities.count("single-trade")
            single_trade_ratio = single_trade_count / len(complexities)
            
            if single_trade_ratio >= 0.8:  # 80%+ single-trade
                synergy_multiplier += 0.15  # 15% bonus for single-trade dominance
                print(f"[Group Synergy] +15% bonus: {single_trade_ratio:.0%} single-trade projects")
            
            # Analyze trade complementarity for single-trade projects
            if single_trade_ratio >= 0.6:  # Majority single-trade
                complementary_bonus = await self._calculate_trade_complementarity_bonus(primary_trades)
                synergy_multiplier += complementary_bonus
                if complementary_bonus > 0:
                    print(f"[Group Synergy] +{complementary_bonus:.0%} bonus: Trade complementarity")
            
            # Penalty for mixed complexity (reduces efficiency)
            complexity_variety = len(set(complexities))
            if complexity_variety > 2:
                penalty = 0.10  # 10% penalty for high complexity variety
                synergy_multiplier -= penalty
                print(f"[Group Synergy] -{penalty:.0%} penalty: High complexity variety")
            
            # Cap synergy multiplier
            synergy_multiplier = max(0.5, min(1.5, synergy_multiplier))
            
            print(f"[Group Synergy] Final synergy multiplier: {synergy_multiplier:.2f}")
            return synergy_multiplier
            
        except Exception as e:
            logger.error(f"Service complexity synergy calculation error: {e}")
            return 1.0  # Default to no adjustment
    
    async def _calculate_trade_complementarity_bonus(self, primary_trades: List[str]) -> float:
        """Calculate bonus for complementary trade combinations"""
        # Define complementary trade groups that work well together
        complementary_groups = [
            {"landscaping", "lawn care", "turf installation"},
            {"roofing", "gutter cleaning", "pressure washing"},
            {"painting", "pressure washing", "window cleaning"},
            {"pool maintenance", "landscaping", "pressure washing"},
            {"flooring", "painting", "cleaning"}
        ]
        
        trades_set = set(primary_trades)
        
        for group in complementary_groups:
            # Check if current trades overlap with this complementary group
            overlap = trades_set.intersection(group)
            if len(overlap) >= 2:  # At least 2 trades from the same group
                overlap_ratio = len(overlap) / len(trades_set)
                if overlap_ratio >= 0.5:  # Majority of trades are complementary
                    return 0.12  # 12% bonus for strong complementarity
                else:
                    return 0.08  # 8% bonus for moderate complementarity
        
        return 0.0  # No complementarity bonus
    
    async def _parse_timeline_weeks(self, timeline_str: str) -> int:
        """Parse timeline string to extract weeks"""
        import re
        
        if not timeline_str:
            return 8  # Default
        
        # Extract numbers and look for time units
        numbers = re.findall(r'\d+', timeline_str.lower())
        if not numbers:
            return 8
        
        base_number = int(numbers[0])
        
        if "week" in timeline_str.lower():
            return base_number
        elif "month" in timeline_str.lower():
            return base_number * 4
        elif "day" in timeline_str.lower():
            return max(1, base_number // 7)
        else:
            # Assume weeks if no unit specified
            return base_number
    
    async def _calculate_project_complexity(self, project: Dict[str, Any]) -> float:
        """Calculate project complexity score (0.0 to 1.0)"""
        complexity = 0.3  # Base complexity
        
        # Budget complexity
        budget_max = project.get("budget_max", 0)
        if budget_max > 75000:
            complexity += 0.3
        elif budget_max > 40000:
            complexity += 0.2
        elif budget_max > 20000:
            complexity += 0.1
        
        # Timeline complexity
        timeline_weeks = project.get("timeline_weeks", 8)
        if timeline_weeks > 12:
            complexity += 0.2
        elif timeline_weeks < 4:
            complexity += 0.1  # Rush jobs are complex
        
        # Urgency complexity
        urgency = project.get("urgency_level", "standard")
        if urgency == "emergency":
            complexity += 0.3
        elif urgency == "urgent":
            complexity += 0.2
        
        # Project type complexity
        project_type = project.get("project_type", "").lower()
        complex_types = ["renovation", "remodel", "addition", "custom", "structural"]
        if any(complex_type in project_type for complex_type in complex_types):
            complexity += 0.2
        
        return min(1.0, complexity)
    
    async def _analyze_project_clusters(self, available_projects: List[Dict[str, Any]], 
                                      group_params: Dict[str, Any]) -> List[ProjectCluster]:
        """Analyze projects to identify potential clusters"""
        clusters = []
        
        try:
            # Geographic clustering
            geographic_clusters = await self._create_geographic_clusters(available_projects, group_params)
            clusters.extend(geographic_clusters)
            
            # Temporal clustering  
            temporal_clusters = await self._create_temporal_clusters(available_projects, group_params)
            clusters.extend(temporal_clusters)
            
            # Specialty clustering
            specialty_clusters = await self._create_specialty_clusters(available_projects, group_params)
            clusters.extend(specialty_clusters)
            
            # Homeowner clustering (multiple projects from same homeowner)
            homeowner_clusters = await self._create_homeowner_clusters(available_projects, group_params)
            clusters.extend(homeowner_clusters)
            
            # Remove overlapping clusters and rank by synergy score
            unique_clusters = await self._deduplicate_clusters(clusters)
            unique_clusters.sort(key=lambda x: x.synergy_score, reverse=True)
            
            return unique_clusters[:15]  # Return top 15 clusters
            
        except Exception as e:
            logger.error(f"Project clustering error: {e}")
            return []
    
    async def _create_geographic_clusters(self, projects: List[Dict[str, Any]], 
                                        group_params: Dict[str, Any]) -> List[ProjectCluster]:
        """Create clusters based on geographic proximity"""
        clusters = []
        
        try:
            # Group by city/zip code proximity
            location_groups = defaultdict(list)
            
            for project in projects:
                city = project.get("location_city", "unknown").lower()
                state = project.get("location_state", "unknown").lower()
                location_key = f"{city}, {state}"
                location_groups[location_key].append(project)
            
            # Create clusters for locations with multiple projects
            for location, location_projects in location_groups.items():
                if len(location_projects) >= self.clustering_parameters["min_group_size"]:
                    
                    # Calculate synergy score based on proximity and project compatibility
                    synergy_score = await self._calculate_geographic_synergy(location_projects)
                    
                    cluster = ProjectCluster(
                        cluster_id=f"geo_{location.replace(' ', '_').replace(',', '_')}",
                        cluster_type="geographic",
                        projects=location_projects,
                        clustering_factors=[
                            f"All projects in {location}",
                            f"Reduced travel costs",
                            f"Efficient resource deployment"
                        ],
                        synergy_score=synergy_score,
                        coordination_complexity="low"
                    )
                    clusters.append(cluster)
            
            return clusters
            
        except Exception as e:
            logger.error(f"Geographic clustering error: {e}")
            return []
    
    async def _create_temporal_clusters(self, projects: List[Dict[str, Any]], 
                                      group_params: Dict[str, Any]) -> List[ProjectCluster]:
        """Create clusters based on timeline overlap"""
        clusters = []
        
        try:
            # Group by timeline compatibility
            timeline_groups = []
            
            # Sort projects by timeline weeks
            sorted_projects = sorted(projects, key=lambda x: x.get("timeline_weeks", 8))
            
            current_group = []
            current_timeline = None
            
            for project in sorted_projects:
                project_timeline = project.get("timeline_weeks", 8)
                
                if current_timeline is None or abs(project_timeline - current_timeline) <= 4:
                    # Similar timeline (within 4 weeks)
                    current_group.append(project)
                    current_timeline = project_timeline
                else:
                    # Save current group if large enough
                    if len(current_group) >= self.clustering_parameters["min_group_size"]:
                        timeline_groups.append(current_group)
                    
                    # Start new group
                    current_group = [project]
                    current_timeline = project_timeline
            
            # Don't forget the last group
            if len(current_group) >= self.clustering_parameters["min_group_size"]:
                timeline_groups.append(current_group)
            
            # Create clusters from timeline groups
            for i, timeline_projects in enumerate(timeline_groups):
                avg_timeline = sum(p.get("timeline_weeks", 8) for p in timeline_projects) / len(timeline_projects)
                
                synergy_score = await self._calculate_temporal_synergy(timeline_projects)
                
                cluster = ProjectCluster(
                    cluster_id=f"temporal_{i}",
                    cluster_type="temporal",
                    projects=timeline_projects,
                    clustering_factors=[
                        f"Similar timeline: {avg_timeline:.1f} weeks average",
                        "Sequential project scheduling possible",
                        "Resource continuity advantages"
                    ],
                    synergy_score=synergy_score,
                    coordination_complexity="moderate"
                )
                clusters.append(cluster)
            
            return clusters
            
        except Exception as e:
            logger.error(f"Temporal clustering error: {e}")
            return []
    
    async def _create_specialty_clusters(self, projects: List[Dict[str, Any]], 
                                       group_params: Dict[str, Any]) -> List[ProjectCluster]:
        """Create clusters based on project type/specialty similarity"""
        clusters = []
        
        try:
            # Group by project type similarity
            specialty_groups = defaultdict(list)
            
            for project in projects:
                project_type = project.get("project_type", "general").lower()
                
                # Categorize by specialty
                specialty_category = await self._categorize_project_specialty(project_type)
                specialty_groups[specialty_category].append(project)
            
            # Create clusters for specialties with multiple projects
            for specialty, specialty_projects in specialty_groups.items():
                if len(specialty_projects) >= self.clustering_parameters["min_group_size"]:
                    
                    synergy_score = await self._calculate_specialty_synergy(specialty_projects, specialty)
                    
                    cluster = ProjectCluster(
                        cluster_id=f"specialty_{specialty}",
                        cluster_type="specialty",
                        projects=specialty_projects,
                        clustering_factors=[
                            f"All {specialty} projects",
                            "Specialized expertise application",
                            "Material purchasing advantages",
                            "Standardized processes"
                        ],
                        synergy_score=synergy_score,
                        coordination_complexity="low"
                    )
                    clusters.append(cluster)
            
            return clusters
            
        except Exception as e:
            logger.error(f"Specialty clustering error: {e}")
            return []
    
    async def _categorize_project_specialty(self, project_type: str) -> str:
        """Categorize project type into specialty groups"""
        specialty_keywords = {
            "kitchen": ["kitchen", "cabinet", "appliance", "countertop"],
            "bathroom": ["bathroom", "bath", "shower", "toilet", "vanity"],
            "landscaping": ["landscaping", "lawn", "garden", "outdoor", "yard", "patio"],
            "electrical": ["electrical", "wiring", "lighting", "power", "outlet"],
            "plumbing": ["plumbing", "pipe", "water", "drain", "fixture"],
            "flooring": ["flooring", "floor", "carpet", "tile", "hardwood"],
            "roofing": ["roofing", "roof", "shingle", "gutter"],
            "painting": ["painting", "paint", "color", "interior", "exterior"]
        }
        
        for specialty, keywords in specialty_keywords.items():
            if any(keyword in project_type for keyword in keywords):
                return specialty
        
        return "general"
    
    async def _create_homeowner_clusters(self, projects: List[Dict[str, Any]], 
                                       group_params: Dict[str, Any]) -> List[ProjectCluster]:
        """Create clusters for multiple projects from same homeowner"""
        # This would require homeowner_id field in bid_cards table
        # For now, return empty list as this feature requires database schema updates
        return []
    
    async def _calculate_geographic_synergy(self, projects: List[Dict[str, Any]]) -> float:
        """Calculate synergy score for geographic cluster"""
        base_score = 0.6  # Base score for geographic clustering
        
        # Boost for project value alignment
        values = [p.get("estimated_value", 0) for p in projects]
        if values:
            value_variance = max(values) - min(values)
            avg_value = sum(values) / len(values)
            if avg_value > 0:
                variance_ratio = value_variance / avg_value
                if variance_ratio < 0.5:  # Similar project values
                    base_score += 0.2
        
        # Boost for timeline alignment
        timelines = [p.get("timeline_weeks", 8) for p in projects]
        timeline_variance = max(timelines) - min(timelines)
        if timeline_variance <= 4:  # Within 4 weeks
            base_score += 0.15
        
        # Boost for project count
        project_bonus = min(0.1, len(projects) * 0.02)
        base_score += project_bonus
        
        return min(1.0, base_score)
    
    async def _calculate_temporal_synergy(self, projects: List[Dict[str, Any]]) -> float:
        """Calculate synergy score for temporal cluster"""
        base_score = 0.5  # Base score for temporal clustering
        
        # Timeline consistency bonus
        timelines = [p.get("timeline_weeks", 8) for p in projects]
        avg_timeline = sum(timelines) / len(timelines)
        timeline_std = (sum((t - avg_timeline) ** 2 for t in timelines) / len(timelines)) ** 0.5
        
        if timeline_std < 2:  # Very consistent timelines
            base_score += 0.3
        elif timeline_std < 4:  # Moderately consistent
            base_score += 0.15
        
        # Resource continuity bonus
        total_weeks = sum(timelines)
        if total_weeks <= 20:  # Can be completed in sequence within 20 weeks
            base_score += 0.2
        
        return min(1.0, base_score)
    
    async def _calculate_specialty_synergy(self, projects: List[Dict[str, Any]], specialty: str) -> float:
        """Calculate synergy score for specialty cluster"""
        base_score = 0.7  # Higher base score for specialty clustering
        
        # Specialization efficiency bonus
        if specialty in ["kitchen", "bathroom", "electrical", "plumbing"]:
            base_score += 0.2  # High specialization benefit
        elif specialty in ["landscaping", "flooring", "painting"]:
            base_score += 0.1  # Moderate specialization benefit
        
        # Project scale bonus
        total_value = sum(p.get("estimated_value", 0) for p in projects)
        if total_value > 200000:  # Large combined project
            base_score += 0.15
        
        return min(1.0, base_score)
    
    async def _deduplicate_clusters(self, clusters: List[ProjectCluster]) -> List[ProjectCluster]:
        """Remove overlapping clusters and keep the best ones"""
        unique_clusters = []
        used_project_ids = set()
        
        # Sort by synergy score (best first)
        sorted_clusters = sorted(clusters, key=lambda x: x.synergy_score, reverse=True)
        
        for cluster in sorted_clusters:
            cluster_project_ids = {p["id"] for p in cluster.projects}
            
            # Check for overlap with already selected clusters
            overlap = cluster_project_ids & used_project_ids
            overlap_ratio = len(overlap) / len(cluster_project_ids)
            
            # Keep cluster if overlap is minimal (< 50%)
            if overlap_ratio < 0.5:
                unique_clusters.append(cluster)
                used_project_ids.update(cluster_project_ids)
        
        return unique_clusters
    
    async def _identify_group_opportunities(self, project_clusters: List[ProjectCluster], 
                                          group_params: Dict[str, Any]) -> List[GroupOpportunity]:
        """Identify concrete group bidding opportunities from project clusters"""
        opportunities = []
        
        try:
            for cluster in project_clusters:
                if len(cluster.projects) < self.clustering_parameters["min_group_size"]:
                    continue
                
                # Calculate opportunity metrics
                total_value = sum(p.get("estimated_value", 0) for p in cluster.projects)
                
                # Calculate potential savings based on cluster type and size
                base_discount = await self._calculate_base_discount(cluster)
                
                # Analyze service complexity synergy for additional savings
                complexity_synergy = await self._calculate_service_complexity_synergy(cluster.projects)
                
                # Adjust discount based on project compatibility and service complexity
                compatibility_multiplier = cluster.synergy_score * complexity_synergy
                final_discount = base_discount * compatibility_multiplier
                
                potential_savings = total_value * final_discount
                
                # Calculate timeline overlap
                timeline_overlap = await self._calculate_timeline_overlap(cluster.projects)
                
                # Assess difficulty
                difficulty_score = await self._assess_coordination_difficulty(cluster, group_params)
                
                # Generate coordination requirements
                coordination_requirements = await self._generate_coordination_requirements(cluster)
                
                # Create group opportunity
                opportunity = GroupOpportunity(
                    group_id=f"group_{cluster.cluster_id}_{datetime.now().strftime('%Y%m%d')}",
                    project_count=len(cluster.projects),
                    total_value=total_value,
                    potential_savings=potential_savings,
                    discount_percentage=final_discount * 100,
                    location_cluster=await self._get_location_summary(cluster.projects),
                    timeline_overlap=timeline_overlap,
                    projects=cluster.projects,
                    difficulty_score=difficulty_score,
                    coordination_requirements=coordination_requirements
                )
                
                # Filter opportunities by minimum savings threshold
                if final_discount >= self.clustering_parameters["min_savings_threshold"]:
                    opportunities.append(opportunity)
            
            # Sort by potential savings
            opportunities.sort(key=lambda x: x.potential_savings, reverse=True)
            return opportunities[:10]  # Return top 10 opportunities
            
        except Exception as e:
            logger.error(f"Group opportunity identification error: {e}")
            return []
    
    async def _calculate_base_discount(self, cluster: ProjectCluster) -> float:
        """Calculate base discount percentage for cluster type"""
        base_discounts = {
            "specialty": 0.20,    # 20% for specialty clustering
            "geographic": 0.15,   # 15% for geographic clustering  
            "temporal": 0.12,     # 12% for temporal clustering
            "homeowner": 0.18     # 18% for same homeowner
        }
        
        base_discount = base_discounts.get(cluster.cluster_type, 0.10)
        
        # Scale discount based on project count
        project_count = len(cluster.projects)
        count_multiplier = min(1.5, 1.0 + (project_count - 3) * 0.1)  # 10% per additional project
        
        return min(0.35, base_discount * count_multiplier)  # Cap at 35% discount
    
    async def _calculate_timeline_overlap(self, projects: List[Dict[str, Any]]) -> int:
        """Calculate timeline overlap in days"""
        if len(projects) < 2:
            return 0
        
        # For now, simplified calculation based on average timeline
        timelines_weeks = [p.get("timeline_weeks", 8) for p in projects]
        avg_timeline = sum(timelines_weeks) / len(timelines_weeks)
        
        # Estimate overlap based on project scheduling efficiency
        total_sequential_weeks = sum(timelines_weeks)
        optimized_weeks = avg_timeline * (len(projects) ** 0.8)  # Economies of scale
        
        overlap_weeks = max(0, total_sequential_weeks - optimized_weeks)
        return int(overlap_weeks * 7)  # Convert to days
    
    async def _assess_coordination_difficulty(self, cluster: ProjectCluster, 
                                            group_params: Dict[str, Any]) -> float:
        """Assess coordination difficulty score (0.0 = easy, 1.0 = very difficult)"""
        difficulty = 0.3  # Base difficulty
        
        # Geographic difficulty
        if cluster.cluster_type == "geographic":
            difficulty += 0.1  # Geographic coordination is easier
        else:
            difficulty += 0.2  # Non-geographic requires more coordination
        
        # Project count difficulty
        project_count = len(cluster.projects)
        if project_count > 6:
            difficulty += 0.3  # Many projects are harder to coordinate
        elif project_count > 4:
            difficulty += 0.2
        
        # Complexity difficulty
        avg_complexity = sum(p.get("complexity_score", 0.5) for p in cluster.projects) / len(cluster.projects)
        difficulty += avg_complexity * 0.3
        
        # Timeline difficulty
        timelines = [p.get("timeline_weeks", 8) for p in cluster.projects]
        timeline_variance = max(timelines) - min(timelines)
        if timeline_variance > 8:  # Large timeline variance
            difficulty += 0.2
        
        return min(1.0, difficulty)
    
    async def _generate_coordination_requirements(self, cluster: ProjectCluster) -> List[str]:
        """Generate list of coordination requirements for the cluster"""
        requirements = []
        
        # Base requirements
        requirements.append("Detailed project scheduling and timeline coordination")
        requirements.append("Regular communication with all homeowners")
        requirements.append("Coordinated material ordering and delivery")
        
        # Cluster-specific requirements
        if cluster.cluster_type == "geographic":
            requirements.append("Optimize travel routes between project sites")
            requirements.append("Share equipment and tools across nearby projects")
        elif cluster.cluster_type == "specialty":
            requirements.append("Standardize materials and processes across projects")
            requirements.append("Leverage specialized team expertise efficiently")
        elif cluster.cluster_type == "temporal":
            requirements.append("Sequential project execution planning")
            requirements.append("Resource allocation across timeline")
        
        # Complexity-based requirements
        avg_complexity = sum(p.get("complexity_score", 0.5) for p in cluster.projects) / len(cluster.projects)
        if avg_complexity > 0.7:
            requirements.append("Enhanced project management for complex projects")
            requirements.append("Additional quality control measures")
        
        # Scale-based requirements
        if len(cluster.projects) > 5:
            requirements.append("Dedicated project manager for group coordination")
            requirements.append("Formal communication protocols")
        
        return requirements
    
    async def _get_location_summary(self, projects: List[Dict[str, Any]]) -> str:
        """Get summary of project locations"""
        locations = []
        for project in projects:
            city = project.get("location_city", "Unknown")
            state = project.get("location_state", "Unknown")
            locations.append(f"{city}, {state}")
        
        unique_locations = list(set(locations))
        
        if len(unique_locations) == 1:
            return unique_locations[0]
        elif len(unique_locations) <= 3:
            return "; ".join(unique_locations)
        else:
            return f"{unique_locations[0]} and {len(unique_locations)-1} other locations"
    
    async def _develop_bulk_pricing_strategies(self, group_opportunities: List[GroupOpportunity], 
                                             group_params: Dict[str, Any]) -> List[BulkPricingStrategy]:
        """Develop bulk pricing strategies for group opportunities"""
        strategies = []
        
        try:
            for opportunity in group_opportunities:
                # Calculate base pricing for each project
                base_pricing = {}
                for project in opportunity.projects:
                    project_id = project["id"]
                    base_pricing[project_id] = project.get("estimated_value", 0)
                
                # Calculate bulk discount tiers
                bulk_discounts = {
                    3: 0.10,  # 10% for 3 projects
                    4: 0.15,  # 15% for 4 projects
                    5: 0.20,  # 20% for 5 projects
                    6: 0.25,  # 25% for 6 projects
                    7: 0.30,  # 30% for 7+ projects
                }
                
                # Adjust discounts based on opportunity characteristics
                project_count = opportunity.project_count
                applicable_discount = bulk_discounts.get(project_count, bulk_discounts[7])
                
                # Calculate savings breakdown
                total_base_value = sum(base_pricing.values())
                total_savings = total_base_value * applicable_discount
                
                savings_breakdown = {
                    "material_savings": total_savings * 0.4,    # 40% from bulk materials
                    "labor_efficiency": total_savings * 0.35,   # 35% from labor efficiency
                    "travel_savings": total_savings * 0.15,     # 15% from reduced travel
                    "overhead_reduction": total_savings * 0.1   # 10% from shared overhead
                }
                
                # Timeline optimization
                sequential_weeks = sum(p.get("timeline_weeks", 8) for p in opportunity.projects)
                optimized_weeks = sequential_weeks * 0.75  # 25% time savings from coordination
                
                timeline_optimization = {
                    "sequential_timeline": f"{sequential_weeks} weeks",
                    "optimized_timeline": f"{optimized_weeks:.0f} weeks",
                    "time_savings": f"{sequential_weeks - optimized_weeks:.0f} weeks",
                    "scheduling_approach": await self._determine_scheduling_approach(opportunity)
                }
                
                # Resource allocation strategy
                resource_allocation = {
                    "crew_size": await self._calculate_optimal_crew_size(opportunity),
                    "equipment_sharing": await self._identify_shared_equipment(opportunity),
                    "material_coordination": await self._plan_material_coordination(opportunity),
                    "supervision_model": await self._determine_supervision_model(opportunity)
                }
                
                # Risk mitigation strategies
                risk_mitigation = await self._identify_risk_mitigation_strategies(opportunity)
                
                strategy = BulkPricingStrategy(
                    base_pricing=base_pricing,
                    bulk_discounts=bulk_discounts,
                    savings_breakdown=savings_breakdown,
                    timeline_optimization=timeline_optimization,
                    resource_allocation=resource_allocation,
                    risk_mitigation=risk_mitigation
                )
                
                strategies.append(strategy)
            
            return strategies
            
        except Exception as e:
            logger.error(f"Bulk pricing strategy development error: {e}")
            return []
    
    async def _determine_scheduling_approach(self, opportunity: GroupOpportunity) -> str:
        """Determine optimal scheduling approach for group opportunity"""
        if opportunity.timeline_overlap > 30:  # Significant overlap possible
            return "parallel_execution"
        elif len(opportunity.projects) <= 4:
            return "sequential_execution"
        else:
            return "hybrid_execution"
    
    async def _calculate_optimal_crew_size(self, opportunity: GroupOpportunity) -> Dict[str, int]:
        """Calculate optimal crew size for group opportunity"""
        total_value = opportunity.total_value
        project_count = opportunity.project_count
        
        # Base crew size calculation
        if total_value > 300000:
            return {"lead_crew": 6, "support_crews": 2, "total_workers": 10}
        elif total_value > 150000:
            return {"lead_crew": 4, "support_crews": 1, "total_workers": 6}
        else:
            return {"lead_crew": 3, "support_crews": 0, "total_workers": 3}
    
    async def _identify_shared_equipment(self, opportunity: GroupOpportunity) -> List[str]:
        """Identify equipment that can be shared across projects"""
        shared_equipment = [
            "Construction vehicles and transportation",
            "Power tools and specialized equipment",
            "Scaffolding and temporary structures",
            "Material handling equipment"
        ]
        
        # Add specialty-specific equipment
        project_types = [p.get("project_type", "").lower() for p in opportunity.projects]
        
        if any("kitchen" in pt for pt in project_types):
            shared_equipment.append("Cabinet installation tools")
        if any("bathroom" in pt for pt in project_types):
            shared_equipment.append("Plumbing and tile installation tools")
        if any("landscaping" in pt for pt in project_types):
            shared_equipment.append("Excavation and landscaping equipment")
        
        return shared_equipment
    
    async def _plan_material_coordination(self, opportunity: GroupOpportunity) -> Dict[str, Any]:
        """Plan material coordination strategy"""
        return {
            "bulk_ordering": "Coordinate material orders for volume discounts",
            "delivery_scheduling": "Optimize delivery timing across all projects",
            "waste_reduction": "Share excess materials between projects",
            "storage_strategy": "Centralized material storage where possible"
        }
    
    async def _determine_supervision_model(self, opportunity: GroupOpportunity) -> str:
        """Determine supervision model based on opportunity characteristics"""
        if opportunity.project_count > 5 or opportunity.difficulty_score > 0.7:
            return "dedicated_project_manager"
        elif opportunity.project_count > 3:
            return "rotating_supervision"
        else:
            return "lead_contractor_supervision"
    
    async def _identify_risk_mitigation_strategies(self, opportunity: GroupOpportunity) -> List[str]:
        """Identify risk mitigation strategies for group opportunity"""
        strategies = [
            "Comprehensive project insurance coverage",
            "Clear communication protocols with all homeowners",
            "Contingency planning for timeline delays",
            "Quality control checkpoints across all projects"
        ]
        
        # Add difficulty-specific strategies
        if opportunity.difficulty_score > 0.6:
            strategies.extend([
                "Enhanced project management oversight",
                "Regular progress review meetings",
                "Backup contractor arrangements"
            ])
        
        # Add value-specific strategies
        if opportunity.total_value > 200000:
            strategies.extend([
                "Performance bonds for large project groups",
                "Milestone-based payment structure",
                "Professional project documentation"
            ])
        
        return strategies
    
    async def _generate_implementation_plans(self, group_opportunities: List[GroupOpportunity],
                                           pricing_strategies: List[BulkPricingStrategy],
                                           group_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate implementation plans for group opportunities"""
        implementation_plans = []
        
        try:
            for i, (opportunity, strategy) in enumerate(zip(group_opportunities, pricing_strategies)):
                
                # Phase 1: Planning and Coordination (Week 1-2)
                planning_phase = {
                    "duration": "2 weeks",
                    "activities": [
                        "Contact all homeowners to discuss group opportunity",
                        "Conduct detailed site assessments for all projects",
                        "Finalize project specifications and requirements",
                        "Develop detailed project timeline and resource allocation",
                        "Secure permits and approvals for all projects",
                        "Order materials with bulk pricing arrangements"
                    ],
                    "deliverables": [
                        "Signed contracts for all projects",
                        "Detailed project schedules",
                        "Material delivery schedules",
                        "Team assignment plans"
                    ]
                }
                
                # Phase 2: Execution (Varies by project)
                execution_approach = strategy.timeline_optimization["scheduling_approach"]
                
                if execution_approach == "parallel_execution":
                    execution_phase = {
                        "approach": "Parallel Execution",
                        "description": "Execute multiple projects simultaneously with coordinated teams",
                        "duration": f"{max(p.get('timeline_weeks', 8) for p in opportunity.projects)} weeks",
                        "coordination_requirements": [
                            "Daily coordination meetings",
                            "Shared resource scheduling",
                            "Cross-project quality control"
                        ]
                    }
                elif execution_approach == "sequential_execution":
                    total_weeks = sum(p.get("timeline_weeks", 8) for p in opportunity.projects) * 0.8
                    execution_phase = {
                        "approach": "Sequential Execution", 
                        "description": "Execute projects one after another with optimized transitions",
                        "duration": f"{total_weeks:.0f} weeks",
                        "coordination_requirements": [
                            "Seamless project transitions",
                            "Material flow optimization",
                            "Team reallocation planning"
                        ]
                    }
                else:  # hybrid_execution
                    execution_phase = {
                        "approach": "Hybrid Execution",
                        "description": "Combination of parallel and sequential execution based on project compatibility",
                        "duration": f"{sum(p.get('timeline_weeks', 8) for p in opportunity.projects) * 0.7:.0f} weeks",
                        "coordination_requirements": [
                            "Flexible scheduling adaptation",
                            "Dynamic resource allocation",
                            "Multi-track project management"
                        ]
                    }
                
                # Phase 3: Completion and Follow-up (Week after execution)
                completion_phase = {
                    "duration": "1 week",
                    "activities": [
                        "Final quality inspections for all projects",
                        "Client walkthroughs and sign-offs",
                        "Warranty documentation delivery",
                        "Project performance review and lessons learned",
                        "Client satisfaction surveys",
                        "Final billing and payment processing"
                    ]
                }
                
                # Success factors
                success_factors = [
                    "Clear communication with all homeowners from start to finish",
                    "Effective resource coordination and scheduling",
                    "Quality control consistency across all projects",
                    "Proactive issue identification and resolution",
                    "Strong project management oversight"
                ]
                
                # Potential challenges
                potential_challenges = [
                    "Coordinating multiple homeowner schedules and preferences",
                    "Managing resource allocation across simultaneous projects",
                    "Maintaining quality standards with increased scope",
                    "Weather or other external delays affecting multiple projects",
                    "Potential scope changes impacting group dynamics"
                ]
                
                implementation_plan = {
                    "opportunity_id": opportunity.group_id,
                    "planning_phase": planning_phase,
                    "execution_phase": execution_phase,
                    "completion_phase": completion_phase,
                    "total_duration": await self._calculate_total_duration(
                        planning_phase, execution_phase, completion_phase
                    ),
                    "success_factors": success_factors,
                    "potential_challenges": potential_challenges,
                    "resource_requirements": strategy.resource_allocation,
                    "communication_plan": await self._create_communication_plan(opportunity),
                    "risk_management": strategy.risk_mitigation
                }
                
                implementation_plans.append(implementation_plan)
            
            return implementation_plans
            
        except Exception as e:
            logger.error(f"Implementation plan generation error: {e}")
            return []
    
    async def _calculate_total_duration(self, planning_phase: Dict, execution_phase: Dict, 
                                      completion_phase: Dict) -> str:
        """Calculate total project duration"""
        planning_weeks = 2
        execution_weeks = int(execution_phase["duration"].split()[0])
        completion_weeks = 1
        
        total_weeks = planning_weeks + execution_weeks + completion_weeks
        return f"{total_weeks} weeks"
    
    async def _create_communication_plan(self, opportunity: GroupOpportunity) -> Dict[str, Any]:
        """Create communication plan for group opportunity"""
        return {
            "kickoff_meeting": "Group meeting with all homeowners to align expectations",
            "regular_updates": "Weekly progress reports to all homeowners",
            "coordination_meetings": "Daily team coordination meetings",
            "issue_escalation": "24-hour response time for any concerns",
            "final_review": "Individual project walkthroughs and group feedback session"
        }
    
    async def _create_group_recommendations(self, group_opportunities: List[GroupOpportunity],
                                          pricing_strategies: List[BulkPricingStrategy],
                                          implementation_plans: List[Dict[str, Any]]) -> List[GroupBidRecommendation]:
        """Create final group bidding recommendations"""
        recommendations = []
        
        try:
            for opportunity, strategy, plan in zip(group_opportunities, pricing_strategies, implementation_plans):
                
                # Calculate success probability
                success_probability = await self._calculate_success_probability(opportunity, strategy)
                
                # Identify competitive advantages
                competitive_advantages = await self._identify_group_competitive_advantages(opportunity, strategy)
                
                # Identify potential challenges
                potential_challenges = await self._identify_group_challenges(opportunity, strategy)
                
                recommendation = GroupBidRecommendation(
                    opportunity=opportunity,
                    pricing_strategy=strategy,
                    implementation_plan=plan,
                    success_probability=success_probability,
                    competitive_advantages=competitive_advantages,
                    potential_challenges=potential_challenges
                )
                
                recommendations.append(recommendation)
            
            # Sort by success probability and potential savings
            recommendations.sort(
                key=lambda x: (x.success_probability, x.opportunity.potential_savings), 
                reverse=True
            )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Group recommendations creation error: {e}")
            return []
    
    async def _calculate_success_probability(self, opportunity: GroupOpportunity, 
                                           strategy: BulkPricingStrategy) -> float:
        """Calculate probability of success for group opportunity"""
        base_probability = 0.6  # Base probability
        
        # Adjust for difficulty
        difficulty_penalty = opportunity.difficulty_score * 0.3
        base_probability -= difficulty_penalty
        
        # Adjust for savings attractiveness
        if opportunity.discount_percentage > 20:
            base_probability += 0.2  # High savings are attractive
        elif opportunity.discount_percentage > 15:
            base_probability += 0.1
        
        # Adjust for project count
        if opportunity.project_count <= 4:
            base_probability += 0.1  # Easier to coordinate
        elif opportunity.project_count > 6:
            base_probability -= 0.1  # Harder to coordinate
        
        # Adjust for timeline optimization
        timeline_savings = opportunity.timeline_overlap
        if timeline_savings > 30:  # Significant time savings
            base_probability += 0.15
        
        return max(0.1, min(0.95, base_probability))
    
    async def _identify_group_competitive_advantages(self, opportunity: GroupOpportunity, 
                                                   strategy: BulkPricingStrategy) -> List[str]:
        """Identify competitive advantages for group opportunity"""
        advantages = [
            f"${opportunity.potential_savings:,.0f} in cost savings ({opportunity.discount_percentage:.1f}% discount)",
            f"Coordinated timeline reduces overall project duration by {opportunity.timeline_overlap} days",
            "Bulk material purchasing for better quality and pricing",
            "Dedicated project management for enhanced coordination",
            "Economies of scale in labor and equipment utilization"
        ]
        
        # Add opportunity-specific advantages
        if opportunity.project_count >= 5:
            advantages.append("Large-scale project expertise and efficiency")
        
        if opportunity.difficulty_score < 0.5:
            advantages.append("Low coordination complexity ensures smooth execution")
        
        # Add savings-specific advantages
        savings_breakdown = strategy.savings_breakdown
        material_savings = savings_breakdown.get("material_savings", 0)
        if material_savings > 5000:
            advantages.append(f"${material_savings:,.0f} in material cost savings through bulk purchasing")
        
        return advantages[:6]  # Limit to top 6 advantages
    
    async def _identify_group_challenges(self, opportunity: GroupOpportunity, 
                                       strategy: BulkPricingStrategy) -> List[str]:
        """Identify potential challenges for group opportunity"""
        challenges = []
        
        # Difficulty-based challenges
        if opportunity.difficulty_score > 0.6:
            challenges.append("High coordination complexity requires enhanced project management")
        
        # Scale-based challenges
        if opportunity.project_count > 5:
            challenges.append("Managing multiple homeowner relationships and expectations")
            challenges.append("Complex scheduling and resource allocation requirements")
        
        # Timeline challenges
        if opportunity.timeline_overlap < 14:
            challenges.append("Limited timeline flexibility may constrain scheduling options")
        
        # Value challenges
        if opportunity.total_value > 250000:
            challenges.append("Large financial commitment requires careful cash flow management")
        
        # Coordination challenges
        coordination_reqs = opportunity.coordination_requirements
        if len(coordination_reqs) > 5:
            challenges.append("Extensive coordination requirements increase operational complexity")
        
        # Add generic challenges if none identified
        if not challenges:
            challenges = [
                "Ensuring consistent quality across all projects",
                "Managing potential weather or external delays",
                "Coordinating material deliveries and storage"
            ]
        
        return challenges[:5]  # Limit to top 5 challenges
    
    async def _calculate_success_metrics(self, recommendations: List[GroupBidRecommendation], 
                                       group_params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall success metrics for group bidding analysis"""
        if not recommendations:
            return {"total_opportunities": 0, "total_savings": 0}
        
        total_opportunities = len(recommendations)
        total_savings = sum(rec.opportunity.potential_savings for rec in recommendations)
        total_value = sum(rec.opportunity.total_value for rec in recommendations)
        avg_success_probability = sum(rec.success_probability for rec in recommendations) / len(recommendations)
        
        # Best opportunity metrics
        best_opportunity = recommendations[0] if recommendations else None
        best_metrics = {}
        if best_opportunity:
            best_metrics = {
                "project_count": best_opportunity.opportunity.project_count,
                "potential_savings": best_opportunity.opportunity.potential_savings,
                "success_probability": best_opportunity.success_probability,
                "difficulty_score": best_opportunity.opportunity.difficulty_score
            }
        
        return {
            "total_opportunities": total_opportunities,
            "total_potential_savings": total_savings,
            "total_project_value": total_value,
            "average_success_probability": round(avg_success_probability, 2),
            "savings_rate": round(total_savings / total_value * 100, 1) if total_value > 0 else 0,
            "best_opportunity": best_metrics,
            "recommendation": await self._generate_overall_recommendation(recommendations)
        }
    
    async def _generate_overall_recommendation(self, recommendations: List[GroupBidRecommendation]) -> str:
        """Generate overall recommendation based on analysis"""
        if not recommendations:
            return "No viable group bidding opportunities identified with current parameters"
        
        best_rec = recommendations[0]
        
        if best_rec.success_probability > 0.7 and best_rec.opportunity.potential_savings > 10000:
            return f"Strongly recommend pursuing group opportunity: {best_rec.opportunity.project_count} projects with ${best_rec.opportunity.potential_savings:,.0f} savings"
        elif best_rec.success_probability > 0.5:
            return f"Consider group opportunity: {best_rec.opportunity.project_count} projects with moderate success probability"
        else:
            return "Group opportunities available but require careful evaluation of coordination complexity"
    
    async def _generate_strategic_insights(self, group_opportunities: List[GroupOpportunity], 
                                         recommendations: List[GroupBidRecommendation]) -> List[str]:
        """Generate strategic insights from group bidding analysis"""
        insights = []
        
        if not group_opportunities:
            return ["No group bidding opportunities found - focus on individual project optimization"]
        
        # Opportunity insights
        total_savings = sum(opp.potential_savings for opp in group_opportunities)
        avg_discount = sum(opp.discount_percentage for opp in group_opportunities) / len(group_opportunities)
        
        insights.append(f"Found {len(group_opportunities)} group opportunities with ${total_savings:,.0f} total potential savings")
        insights.append(f"Average group discount: {avg_discount:.1f}% across opportunities")
        
        # Best opportunity insights
        if recommendations:
            best_rec = recommendations[0]
            insights.append(f"Top opportunity: {best_rec.opportunity.project_count} projects with {best_rec.success_probability:.0%} success probability")
        
        # Strategic insights based on patterns
        cluster_types = [opp.location_cluster for opp in group_opportunities]
        if len(set(cluster_types)) < len(cluster_types) / 2:
            insights.append("Geographic clustering shows strong potential - consider focusing on specific areas")
        
        high_value_opps = [opp for opp in group_opportunities if opp.total_value > 150000]
        if high_value_opps:
            insights.append(f"{len(high_value_opps)} high-value opportunities (>$150k) identified")
        
        return insights[:6]  # Limit to top insights
    
    async def _update_group_context(self, state: DeepAgentState, results: Dict[str, Any]):
        """Update conversation state with group bidding context"""
        try:
            if not hasattr(state, 'group_bidding_history'):
                state.group_bidding_history = []
            
            group_entry = {
                "timestamp": datetime.now().isoformat(),
                "opportunities_found": results["group_metadata"]["opportunities_found"],
                "max_potential_savings": results["group_metadata"]["max_potential_savings"],
                "total_project_value": results["group_metadata"]["total_project_value"],
                "best_opportunity_id": results["recommendations"][0]["opportunity"]["group_id"] if results.get("recommendations") else None
            }
            
            state.group_bidding_history.append(group_entry)
            
            # Keep only last 3 group analyses
            if len(state.group_bidding_history) > 3:
                state.group_bidding_history = state.group_bidding_history[-3:]
                
        except Exception as e:
            logger.error(f"Group context update error: {e}")
    
    async def _load_contractor_context(self, contractor_id: str) -> Optional[Dict[str, Any]]:
        """Load contractor context for group bidding analysis"""
        try:
            # Load from unified contractor system (using both contractors and contractor_leads tables)
            contractor = await self.db.get_contractor_by_id(contractor_id)
            contractor_lead = await self.db.get_contractor_lead_by_id(contractor_id)
            
            context = {}
            
            if contractor:
                context.update({
                    "specialties": ["general"],  # Default
                    "service_area": ["local"],
                    "capacity_score": 0.5,
                    "total_jobs": contractor.get("total_jobs", 0),
                    "rating": contractor.get("rating", 0)
                })
            
            if contractor_lead:
                context.update({
                    "specialties": contractor_lead.get("specialties", ["general"]),
                    "service_area": [f"{contractor_lead.get('city', 'Local')}, {contractor_lead.get('state', '')}"],
                    "capacity_score": min(1.0, contractor_lead.get("employees", 3) / 10),
                    "years_experience": contractor_lead.get("years_in_business", 5)
                })
            
            return context if context else None
            
        except Exception as e:
            logger.error(f"Contractor context loading error: {e}")
            return None
    
    async def _get_sample_projects(self, group_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate sample projects for testing when database query fails"""
        location = group_params.get("target_location", "Local Area")
        
        sample_projects = []
        project_types = ["Kitchen Remodel", "Bathroom Update", "Landscaping", "Flooring", "Painting"]
        
        for i, project_type in enumerate(project_types):
            sample_project = {
                "id": f"sample_{i+1}",
                "bid_card_number": f"BC-SAMPLE-{i+1}",
                "project_type": project_type,
                "budget_min": 20000 + i * 5000,
                "budget_max": 35000 + i * 8000,
                "timeline": f"{6 + i} weeks",
                "location_city": location.split(",")[0] if "," in location else location,
                "location_state": location.split(",")[1].strip() if "," in location else "State",
                "urgency_level": "standard",
                "status": "generated",
                "estimated_value": 27500 + i * 6500,
                "timeline_weeks": 6 + i,
                "complexity_score": 0.3 + i * 0.1
            }
            sample_projects.append(sample_project)
        
        return sample_projects
    
    async def _get_fallback_group_recommendations(self) -> List[str]:
        """Provide fallback recommendations when group analysis fails"""
        return [
            "Group bidding analysis temporarily unavailable",
            "Consider searching for similar projects in your service area",
            "Look for opportunities to bundle complementary project types",
            "Geographic clustering can provide 10-15% cost savings",
            "Specialty clustering offers material and labor efficiencies",
            "Contact local contractors to discuss partnership opportunities"
        ]
    
    def _format_project_clusters(self, clusters: List[ProjectCluster]) -> List[Dict[str, Any]]:
        """Format project clusters for API response"""
        return [
            {
                "cluster_id": cluster.cluster_id,
                "cluster_type": cluster.cluster_type,
                "project_count": len(cluster.projects),
                "clustering_factors": cluster.clustering_factors,
                "synergy_score": cluster.synergy_score,
                "coordination_complexity": cluster.coordination_complexity
            }
            for cluster in clusters
        ]
    
    def _format_group_opportunities(self, opportunities: List[GroupOpportunity]) -> List[Dict[str, Any]]:
        """Format group opportunities for API response"""
        return [
            {
                "group_id": opp.group_id,
                "project_count": opp.project_count,
                "total_value": opp.total_value,
                "potential_savings": opp.potential_savings,
                "discount_percentage": opp.discount_percentage,
                "location_cluster": opp.location_cluster,
                "timeline_overlap": opp.timeline_overlap,
                "difficulty_score": opp.difficulty_score,
                "coordination_requirements": opp.coordination_requirements
            }
            for opp in opportunities
        ]
    
    def _format_pricing_strategies(self, strategies: List[BulkPricingStrategy]) -> List[Dict[str, Any]]:
        """Format pricing strategies for API response"""
        return [
            {
                "base_pricing": strategy.base_pricing,
                "bulk_discounts": strategy.bulk_discounts,
                "savings_breakdown": strategy.savings_breakdown,
                "timeline_optimization": strategy.timeline_optimization,
                "resource_allocation": strategy.resource_allocation,
                "risk_mitigation": strategy.risk_mitigation
            }
            for strategy in strategies
        ]
    
    def _format_group_recommendations(self, recommendations: List[GroupBidRecommendation]) -> List[Dict[str, Any]]:
        """Format group recommendations for API response"""
        return [
            {
                "opportunity": self._format_group_opportunities([rec.opportunity])[0],
                "pricing_strategy": self._format_pricing_strategies([rec.pricing_strategy])[0],
                "implementation_plan": rec.implementation_plan,
                "success_probability": rec.success_probability,
                "competitive_advantages": rec.competitive_advantages,
                "potential_challenges": rec.potential_challenges
            }
            for rec in recommendations
        ]